# ruff: noqa: T201
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from enum import Enum, auto
from pathlib import Path

import typer
from barks_fantagraphics.comic_book_info import BARKS_TITLE_DICT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.panel_boxes import PagePanelBoxes, TitlePagesPanelBoxes, TitlePanelBoxes
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups, SpeechPageGroup
from comic_utils.common_typer_options import TitleArg, VolumesArg
from intspan import intspan
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from barks_ocr.utils.geometry import Rect
from barks_ocr.utils.ocr_box import OcrBox, PointList

# ── Text-fit constants ────────────────────────────────────────────────────────

FIT_FONT_PATH = Path("/home/greg/Prj/fonts/verdana.ttf")
FIT_WIDTH_TOLERANCE = 1.1  # allow 10% overflow (Verdana is not the comic's font)
FIT_HEIGHT_FRACTION = 0.75  # derived font size ≈ box line height * this
FIT_MIN_FONT_SIZE = 8
MIN_MATCH_RATIO = 0.7  # SequenceMatcher threshold for cross-engine pairing

_FIT_FONT_MISSING_WARNED: list[bool] = [False]
_FIT_MEASURE_DRAW = ImageDraw.Draw(Image.new("RGB", (1, 1)))

# ── Issue data ────────────────────────────────────────────────────────────────


@dataclass
class IssueFound:
    volume: int
    fanta_page: str
    engine: str
    group_id: str
    issue_type: str
    panel_num: int
    text: str
    notes: str


def _rect_from_points(points: PointList) -> Rect:
    bottom_left, top_right = points[0], points[1]
    return Rect(
        bottom_left[0],
        bottom_left[1],
        top_right[0] - bottom_left[0],
        top_right[1] - bottom_left[1],
    )


def _box_wh(text_box: PointList) -> tuple[int, int]:
    """Return (width, height) in pixels from the text_box's min rotated rect."""
    bottom_left, top_right = OcrBox(text_box, "", 0, "").min_rotated_rectangle
    return int(top_right[0] - bottom_left[0]), int(top_right[1] - bottom_left[1])


def _text_fits_in_box(ai_text: str, text_box: PointList) -> bool:
    """Render ai_text at a box-calibrated font size; check it fits text_box width.

    Derives the font size from the box height divided by the number of lines so
    that fewer lines means a larger font — which is exactly the Gemini failure
    mode (multiple lines collapsed into one). The widest rendered line must fit
    within box width * FIT_WIDTH_TOLERANCE.
    """
    if not ai_text.strip() or not text_box:
        return True

    box_w, box_h = _box_wh(text_box)
    if box_w <= 0 or box_h <= 0:
        return True

    lines = ai_text.split("\n")
    n_lines = max(1, len(lines))
    font_size = max(FIT_MIN_FONT_SIZE, int(box_h / n_lines * FIT_HEIGHT_FRACTION))

    try:
        font = ImageFont.truetype(str(FIT_FONT_PATH), font_size)
    except OSError:
        if not _FIT_FONT_MISSING_WARNED[0]:
            logger.warning(f'Fit-check font not found: "{FIT_FONT_PATH}". Skipping fit checks.')
            _FIT_FONT_MISSING_WARNED[0] = True
        return True

    max_line_w = 0
    for line in lines:
        if not line:
            continue
        left, _top, right, _bottom = _FIT_MEASURE_DRAW.textbbox((0, 0), line, font=font)
        max_line_w = max(max_line_w, right - left)

    return max_line_w <= box_w * FIT_WIDTH_TOLERANCE


def _apply_line_pattern(source_text: str, pattern_text: str) -> str:
    """Re-wrap source_text so each line holds the same word count as pattern_text.

    Duplicated from EditorApp._apply_line_pattern in kivy_editor.py — inlined
    here to avoid importing Kivy just for a 15-line text helper.
    """
    pattern_lines = pattern_text.rstrip("\n").split("\n")
    line_counts = [len(ln.split()) for ln in pattern_lines]
    if not line_counts:
        return source_text

    words = source_text.split()
    if not words:
        return ""

    out: list[str] = []
    i = 0
    last_idx = len(line_counts) - 1
    for idx, count in enumerate(line_counts):
        if idx == last_idx:
            out.append(" ".join(words[i:]))
            break
        if i >= len(words):
            break
        out.append(" ".join(words[i : i + count]))
        i += count
    return "\n".join(out)


def _find_matching_group(
    group: dict,
    other_page_group: SpeechPageGroup | None,
    min_ratio: float = MIN_MATCH_RATIO,
) -> dict | None:
    """Best-matching group in the other engine, restricted to same panel_num.

    Returns the other engine's json_group dict, or None if no candidate clears
    min_ratio. Matches the pairing approach used in compare.py.
    """
    if other_page_group is None:
        return None

    panel_num = int(group.get("panel_num", -1))
    ai_text = (group.get("ai_text") or "").strip()
    if not ai_text:
        return None

    other_groups = other_page_group.speech_page_json.get("groups", {})

    best_ratio = 0.0
    best_group: dict | None = None
    for other in other_groups.values():
        if int(other.get("panel_num", -1)) != panel_num:
            continue
        other_text = (other.get("ai_text") or "").strip()
        if not other_text:
            continue
        ratio = SequenceMatcher(None, ai_text, other_text).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_group = other

    return best_group if best_ratio >= min_ratio else None


def _other_ocr_type(ocr_type: OcrTypes) -> OcrTypes:
    return OcrTypes.PADDLEOCR if ocr_type == OcrTypes.EASYOCR else OcrTypes.EASYOCR


class PanelNumState(Enum):
    PANEL_NUM_SET = auto()
    PANEL_NUM_NOT_SET_FIXABLE = auto()
    PANEL_NUM_NOT_SET_UNFIXABLE = auto()


# ── Checker ───────────────────────────────────────────────────────────────────


class OcrChecker:
    """Checks prelim OCR JSON files for issues and writes a kivy-editor queue file."""

    def __init__(
        self,
        comics_database: ComicsDatabase,
        fix_panel_nums: bool,
        fix_groups_order: bool,
        fix_newlines: bool,
    ) -> None:
        self._comics_database = comics_database
        self._fix_panel_nums = fix_panel_nums
        self._fix_groups_order = fix_groups_order
        self._fix_newlines = fix_newlines
        self._speech_groups = SpeechGroups(comics_database)
        self._title_panel_boxes = TitlePanelBoxes(self._comics_database)

    # ── Public API ────────────────────────────────────────────────────────────

    def check_titles(
        self,
        title_list: list[str],
        output_file: Path,
    ) -> None:
        """Check all pages of each title; print issues and write a queue file."""
        all_issues: list[IssueFound] = []

        for title_str in title_list:
            print("-" * 80)
            title = BARKS_TITLE_DICT[title_str]
            volume = self._comics_database.get_fanta_volume_int(title_str)
            page_groups = self._speech_groups.get_speech_page_groups(title)
            page_panel_boxes = self._title_panel_boxes.get_page_panel_boxes(title)

            pages: dict[str, dict[OcrTypes, SpeechPageGroup]] = defaultdict(dict)
            for pg in page_groups:
                pages[pg.fanta_page][pg.ocr_index] = pg

            title_issues: list[IssueFound] = []
            for fanta_page in sorted(pages):
                variants = pages[fanta_page]
                for ocr_index, page_group in variants.items():
                    other = variants.get(_other_ocr_type(ocr_index))
                    title_issues.extend(self._check_page_group(page_group, page_panel_boxes, other))

            if title_issues:
                print(f'Issues in "{title_str}" (Vol. {volume}):')
                for issue in title_issues:
                    self._print_issue(issue)
            else:
                print(f'  No issues in "{title_str}" (Vol. {volume}).')

            all_issues.extend(title_issues)

        self._print_issues_summary(all_issues)
        self._write_queue_file(all_issues, output_file)

    # ── Per-page / per-group checks ───────────────────────────────────────────

    def _check_page_group(
        self,
        page_group: SpeechPageGroup,
        page_panel_boxes: TitlePagesPanelBoxes,
        other_page_group: SpeechPageGroup | None = None,
    ) -> list[IssueFound]:
        volume = page_group.fanta_vol
        fanta_page = page_group.fanta_page
        engine = str(page_group.ocr_index)
        json_groups = page_group.speech_page_json.get("groups", {})
        per_page_boxes = page_panel_boxes.pages[fanta_page]

        issues: list[IssueFound] = []
        there_were_fixes = False

        for group_id, group in json_groups.items():
            group_issues, there_were_group_fixes = self._check_group(
                volume, fanta_page, engine, group_id, group, per_page_boxes, other_page_group
            )
            issues.extend(group_issues)
            if there_were_group_fixes:
                there_were_fixes = True

        if self._fix_groups_order and page_group.renumber_groups():
            there_were_fixes = True

        if there_were_fixes:
            page_group.save_json()

        return issues

    def _check_group(  # noqa: C901, PLR0913
        self,
        volume: int,
        fanta_page: str,
        engine: str,
        group_id: str,
        group: dict,
        page_panel_boxes: PagePanelBoxes,
        other_page_group: SpeechPageGroup | None = None,
    ) -> tuple[list[IssueFound], bool]:
        ai_text = (group.get("ai_text") or "").strip()
        notes = (group.get("notes") or "").strip()
        panel_num_state, panel_num = self._get_panel_num_state(group, page_panel_boxes)

        issues: list[IssueFound] = []
        there_were_fixes = False

        def add(issue_type: str) -> None:
            issues.append(
                IssueFound(
                    volume=volume,
                    fanta_page=fanta_page,
                    engine=engine,
                    group_id=group_id,
                    issue_type=issue_type,
                    panel_num=panel_num,
                    text=ai_text,
                    notes=notes,
                )
            )

        if panel_num_state == PanelNumState.PANEL_NUM_NOT_SET_UNFIXABLE:
            add("panel_unassigned")
        elif panel_num_state == PanelNumState.PANEL_NUM_NOT_SET_FIXABLE:
            there_were_fixes = self._deal_with_fixable_panel_num(group, group_id, panel_num)

        if ai_text == "":
            add("empty_text")
        elif self._is_short_text(group):
            add("short_text")
        if self._is_ai_detected_error(group):
            add("error_notes")
        if "page number" in notes.lower():
            add("page_number_notes")

        if ai_text:
            fit_fixed, fit_issue = self._check_text_fits(group, group_id, other_page_group)
            if fit_fixed:
                there_were_fixes = True
            if fit_issue:
                add(fit_issue)

        return issues, there_were_fixes

    # ── Text-fit check + optional fix ─────────────────────────────────────────

    def _check_text_fits(
        self,
        group: dict,
        group_id: str,
        other_page_group: SpeechPageGroup | None,
    ) -> tuple[bool, str | None]:
        """Return (fix_applied, issue_type_to_add).

        - fits already → (False, None).
        - doesn't fit, no fix flag → (False, "text_does_not_fit").
        - doesn't fit, flag set, match found → rewrap in place → (True, None).
        - doesn't fit, flag set, no match → warn → (False, "text_does_not_fit").
        """
        ai_text = (group.get("ai_text") or "").strip()
        text_box = group.get("text_box") or []
        if not ai_text or not text_box:
            return False, None

        if _text_fits_in_box(ai_text, text_box):
            return False, None

        if not self._fix_newlines:
            return False, "text_does_not_fit"

        match = _find_matching_group(group, other_page_group)
        if match is None:
            logger.warning(
                f"Group {group_id}: text does not fit text_box and no matching"
                f" group found in the other engine to transplant newlines from."
            )
            return False, "text_does_not_fit"

        pattern_text = (match.get("ai_text") or "").strip()
        new_text = _apply_line_pattern(ai_text, pattern_text)
        if new_text == ai_text:
            logger.warning(
                f"Group {group_id}: text does not fit but line-pattern transplant"
                f" produced no change."
            )
            return False, "text_does_not_fit"

        group["ai_text"] = new_text
        logger.info(f"Group {group_id}: rewrapped ai_text using other-engine pattern.")
        return True, None

    # ── Predicates ────────────────────────────────────────────────────────────

    @staticmethod
    def _is_ai_detected_error(group: dict) -> bool:
        notes = (group.get("notes") or "").strip().lower()
        return "error" in notes and "art" in notes and "background" in notes

    @staticmethod
    def _is_short_text(group: dict) -> bool:
        ai_text = (group.get("ai_text") or "").strip().lower()
        return (len(ai_text) == 1) and (ai_text not in ("?", "!"))

    def _get_panel_num_state(
        self, group: dict, page_panel_boxes: PagePanelBoxes
    ) -> tuple[PanelNumState, int]:
        panel_num = int(group.get("panel_num", -1))
        if panel_num != -1:
            return PanelNumState.PANEL_NUM_SET, panel_num
        return self._can_replace_missing_panel_num(group, page_panel_boxes)

    def _deal_with_fixable_panel_num(self, group: dict, group_id: str, panel_num: int) -> bool:
        if self._fix_panel_nums:
            group["panel_num"] = panel_num
            logger.warning(f"For group {group_id}, fixed panel_num = {panel_num}.")
            return True

        logger.warning(
            f"For group {group_id}, panel_num is not set"
            f" (and should be {panel_num})"
            f" but fix panel nums = {self._fix_panel_nums}."
        )
        return False

    # ── Panel-num fix helpers ─────────────────────────────────────────────────
    # TODO: Duplicated code from string_replacers
    def _can_replace_missing_panel_num(
        self, group: dict, page_panel_boxes: PagePanelBoxes
    ) -> tuple[PanelNumState, int]:
        panel_num = int(group["panel_num"])
        assert panel_num == -1

        text_box = group["text_box"]
        for reduce_by in [20, 40, 60]:
            can_do, reduced_box = self._get_reduced_text_box(text_box, reduce_by)
            if not can_do:
                logger.warning(f"Could not reduce text box: {text_box}")
                break
            assert reduced_box
            new_panel_num = self._get_enclosing_panel_num(reduced_box, page_panel_boxes)
            if new_panel_num != -1:
                return PanelNumState.PANEL_NUM_NOT_SET_FIXABLE, new_panel_num

        logger.warning(f"Could not find enclosing panel for box: {text_box}")

        return PanelNumState.PANEL_NUM_NOT_SET_UNFIXABLE, -1

    @staticmethod
    def _get_reduced_text_box(text_box: PointList, reduce_by: int) -> tuple[bool, PointList | None]:
        p0_x = text_box[0][0] + reduce_by
        p0_y = text_box[0][1] + reduce_by
        p1_x = text_box[1][0] - reduce_by
        p1_y = text_box[1][1] + reduce_by
        p2_x = text_box[2][0] - reduce_by
        p2_y = text_box[2][1] - reduce_by
        p3_x = text_box[3][0] + reduce_by
        p3_y = text_box[3][1] - reduce_by

        if p1_x <= p0_x or p2_y <= p0_y:
            return False, None

        return True, [(p0_x, p0_y), (p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)]

    @staticmethod
    def _get_enclosing_panel_num(box: PointList, page_panel_boxes: PagePanelBoxes) -> int:
        box_rect = _rect_from_points(OcrBox(box, "", 0, "").min_rotated_rectangle)

        for i, panel_box in enumerate(page_panel_boxes.panel_boxes):
            panel_rect = Rect(panel_box.x0, panel_box.y0, panel_box.w, panel_box.h)
            if panel_rect.is_rect_inside_rect(box_rect):
                return i + 1

        return -1

    # ── Output helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _write_queue_file(all_issues: list[IssueFound], output_file: Path) -> None:
        """Write de-duplicated queue file: one entry per unique (vol, page, engine, group_id)."""
        seen: set[tuple[int, str, str, str]] = set()
        queue_lines: list[str] = []
        for issue in all_issues:
            key = (issue.volume, issue.fanta_page, issue.engine, issue.group_id)
            if key not in seen:
                seen.add(key)
                queue_lines.append(
                    f"{issue.volume}"
                    f" {int(issue.fanta_page)}"
                    f" {issue.engine}"
                    f" {issue.group_id}"
                    f" {issue.issue_type}"
                )
        output_file.write_text("\n".join(queue_lines) + ("\n" if queue_lines else ""))
        print(f'\nQueue file: "{output_file}" ({len(queue_lines)} entries).')

    @staticmethod
    def _print_issues_summary(all_issues: list[IssueFound]) -> None:
        print()
        print("=" * 80)
        counts: Counter[str] = Counter(issue.issue_type for issue in all_issues)
        print(f"Total issues: {len(all_issues)}")
        for issue_type, count in sorted(counts.items()):
            print(f"  {issue_type}: {count}")

    @staticmethod
    def _print_issue(issue: IssueFound) -> None:
        text_preview = issue.text.replace("\n", "\\n")[:60]
        notes_str = f", notes={issue.notes!r}" if issue.notes else ""
        print(
            f"  [{issue.issue_type}]"
            f" page={issue.fanta_page} {issue.engine} group={issue.group_id}"
            f" panel={issue.panel_num}"
            f" text={text_preview!r}{notes_str}"
        )


# ── CLI ───────────────────────────────────────────────────────────────────────

app = typer.Typer()


def _default_output_file(volumes_str: str) -> Path:
    today = datetime.now(tz=UTC).date().isoformat()
    if volumes_str:
        safe = volumes_str.replace(",", "_").replace(" ", "")
        return Path(f"ocr-check-vol-{safe}-{today}.txt")
    return Path(f"ocr-check-{today}.txt")


@app.command(help="Check prelim OCR JSON files for issues and write a kivy-editor queue file.")
def main(  # noqa: PLR0913
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    output: Path = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Queue file path (default: auto-named ocr-check-vol-N-DATE.txt in CWD)",
    ),
    fix_panel_nums: bool = False,
    fix_groups_order: bool = False,
    fix_newlines: bool = False,
) -> None:
    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    comics_database = ComicsDatabase()
    volumes = list(intspan(volumes_str)) if volumes_str else []
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    output_file = output or _default_output_file(volumes_str)
    OcrChecker(comics_database, fix_panel_nums, fix_groups_order, fix_newlines).check_titles(
        title_list, output_file
    )


if __name__ == "__main__":
    app()

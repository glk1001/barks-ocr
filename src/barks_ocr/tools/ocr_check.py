# ruff: noqa: T201
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from enum import Enum, auto
from pathlib import Path
from statistics import median

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.panel_boxes import PagePanelBoxes, TitlePagesPanelBoxes, TitlePanelBoxes
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups, SpeechPageGroup
from comic_utils.common_typer_options import TitleArg, VolumesArg
from intspan import intspan
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from barks_ocr.utils.geometry import Rect
from barks_ocr.utils.group_checks import (
    has_dash_no_spaces,
    has_dash_wrong_space,
    has_dot_at_end_of_sentence,
    has_page_number_notes,
    is_acknowledged,
    is_ai_detected_error,
    is_short_text,
)
from barks_ocr.utils.ocr_box import OcrBox, PointList

# ── Text-fit constants ────────────────────────────────────────────────────────

FIT_FONT_PATH = Path("/home/greg/Prj/fonts/verdana.ttf")
FIT_WIDTH_TOLERANCE = 1.5  # allow 50% overflow (Verdana is not the comic's font)
FIT_WIDTH_TOLERANCE_SFX = 4.0  # allow 300% overflow: sound-effect lettering is stylized
FIT_HEIGHT_FRACTION = 0.75  # derived font size ≈ box line height * this
FIT_MIN_FONT_SIZE = 8
MIN_MATCH_RATIO = 0.7  # SequenceMatcher threshold for cross-engine pairing
MAX_FIX_PASSES = 5  # one fix can enable another; cap the re-check loop
# Lettering that is deliberately unlike the surrounding dialogue, so neither its
# width nor its line height says anything about the page. "title" is the
# splash-page logo: hand-drawn, one huge word per line, and nothing Verdana can
# model — measured strictly it produced 18 bogus text_does_not_fit flags.
STYLIZED_TYPES = ("sound_effect", "background", "title")

# ── Line-height constants ─────────────────────────────────────────────────────
# The fit check derives font size from box height / line count, so extra line
# breaks only ever make text easier to pass. These catch that inverse failure by
# comparing a group's line packing against the rest of its page.
# Real lettering is very consistent within a page, so correct groups cluster
# tightly around the median.
#
# Two bands, because one threshold cannot serve both needs. Below the outlier
# fraction the packing is unambiguous and always reported. Between the two lies
# a band that is mostly noise — on the cleaned vol 1, 66 of 72 flags sat there,
# while the uncleaned vols 19/21 barely change across it (5.1% -> 4.6%) — so it
# is reported only on request, as "too_many_lines_marginal".
LINE_HEIGHT_OUTLIER_FRACTION = 0.85  # below this * page median => surplus line breaks
LINE_HEIGHT_MARGINAL_FRACTION = 0.9  # ...and below this => marginal, opt-in
MIN_GROUPS_FOR_LINE_HEIGHT = 5  # too few groups for a trustworthy page median
MIN_LINES_FOR_LINE_HEIGHT = 2  # one-line boxes measure high; see _implied_line_height

_FIT_FONT_MISSING_WARNED: list[bool] = [False]
_FIT_MEASURE_DRAW = ImageDraw.Draw(Image.new("RGB", (1, 1)))

# ── Issue data ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PageLineHeights:
    """Median implied line height for a page, in this engine and the other one."""

    own: float | None
    other: float | None


@dataclass(frozen=True)
class MissingPrelim:
    """A title's pages that have no prelim OCR file — a gap in the OCR data."""

    volume: int
    title_str: str
    fanta_pages: list[str]


@dataclass(frozen=True)
class LineHeightLimits:
    """The two line-height bands, and whether the marginal one is reported."""

    outlier: float = LINE_HEIGHT_OUTLIER_FRACTION
    marginal: float = LINE_HEIGHT_MARGINAL_FRACTION
    include_marginal: bool = False


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
    ratio: float | None = None


def _format_page_ranges(fanta_pages: list[str]) -> str:
    """Collapse sorted page numbers into ranges, keeping their zero padding.

    ``intspan`` would do the collapsing but returns bare ints, and these pages
    are named after zero-padded files ("096-easyocr-...json"), so the padding
    has to survive.
    """
    if not fanta_pages:
        return ""

    runs: list[list[str]] = [[fanta_pages[0]]]
    for page in fanta_pages[1:]:
        if int(page) == int(runs[-1][-1]) + 1:
            runs[-1].append(page)
        else:
            runs.append([page])

    return ", ".join(run[0] if len(run) == 1 else f"{run[0]}-{run[-1]}" for run in runs)


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


def _text_fits_in_box(  # noqa: C901
    ai_text: str,
    text_box: PointList,
    fanta_page: str = "",
    *,
    strict: bool = True,
    width_tolerance: float = FIT_WIDTH_TOLERANCE,
) -> bool:
    """Render ai_text at a box-calibrated font size; check it fits text_box width.

    Derives the font size from the box height divided by the number of lines so
    that fewer lines means a larger font — which is exactly the Gemini failure
    mode (multiple lines collapsed into one). The widest rendered line must fit
    within box width * FIT_WIDTH_TOLERANCE.

    When ``strict`` is False the check is run twice — once in each orientation
    (swapping w and h) — and the text is considered to fit if either passes.
    This avoids false positives for groups whose text may be rotated (e.g.
    sound effects), since ``text_box`` itself is always axis-aligned and
    carries no rotation information.
    """
    if not ai_text.strip() or not text_box:
        return True

    box_w, box_h = _box_wh(text_box)
    if box_w <= 0 or box_h <= 0:
        return True

    lines = ai_text.split("\n")
    n_lines = max(1, len(lines))

    def _fits_one_orientation(w: int, h: int) -> tuple[bool, str]:
        """Return (fits, debug_msg). Font derives from h; widest line compared to w."""
        font_size = max(FIT_MIN_FONT_SIZE, int(h / n_lines * FIT_HEIGHT_FRACTION))
        try:
            font = ImageFont.truetype(str(FIT_FONT_PATH), font_size)
        except OSError:
            if not _FIT_FONT_MISSING_WARNED[0]:
                logger.warning(f'Fit-check font not found: "{FIT_FONT_PATH}". Skipping fit checks.')
                _FIT_FONT_MISSING_WARNED[0] = True
            return True, ""

        max_line_w = 0
        widest_line = ""
        for line in lines:
            if not line:
                continue
            left, _top, right, _bottom = _FIT_MEASURE_DRAW.textbbox((0, 0), line, font=font)
            line_w = right - left
            if line_w > max_line_w:
                max_line_w = line_w
                widest_line = line

        allowed_w = w * width_tolerance
        msg = (
            f"w={w}px h={h}px n_lines={n_lines} font_size={font_size}"
            f" widest_line_w={max_line_w}px allowed={allowed_w:.1f}px"
            f" (tolerance={width_tolerance}) widest_line={widest_line!r}"
        )
        return max_line_w <= allowed_w, msg

    page_prefix = f"page={fanta_page}: " if fanta_page else ""

    ok_h, msg_h = _fits_one_orientation(box_w, box_h)
    if ok_h:
        return True
    if strict:
        logger.debug(f"{page_prefix}Text does not fit (strict): {msg_h}")
        return False

    ok_v, msg_v = _fits_one_orientation(box_h, box_w)
    if ok_v:
        return True

    logger.debug(
        f"{page_prefix}Text does not fit (lenient, neither orientation):"
        f" horizontal=[{msg_h}] vertical=[{msg_v}]"
    )
    return False


def _is_stylized(group: dict) -> bool:
    """Whether the group's lettering is stylized, so its metrics are unreliable."""
    return (group.get("type") or "").strip().lower() in STYLIZED_TYPES


def _fit_params(group: dict) -> tuple[bool, float]:
    """Return the (strict, width_tolerance) fit parameters for a group.

    Keyed off the group's ``type``: only unknown types get the strict
    single-orientation check; the stylized types also get a wider tolerance.
    """
    group_type = (group.get("type") or "").strip().lower()
    stylized_types = STYLIZED_TYPES
    strict = group_type not in ("dialogue", "narration", *stylized_types)
    width_tolerance = (
        FIT_WIDTH_TOLERANCE_SFX if group_type in stylized_types else FIT_WIDTH_TOLERANCE
    )
    return strict, width_tolerance


def _group_text_fits(group: dict, fanta_page: str = "") -> bool:
    """Return whether the group's own ai_text fits its own text_box."""
    strict, width_tolerance = _fit_params(group)
    return _text_fits_in_box(
        (group.get("ai_text") or "").strip(),
        group.get("text_box") or [],
        fanta_page,
        strict=strict,
        width_tolerance=width_tolerance,
    )


def _implied_line_height(group: dict) -> float | None:
    """Box height per text line, or None when the group cannot be measured.

    Stylized groups are excluded: their lettering size is deliberately unlike
    the surrounding dialogue, so they are neither judged nor used as evidence.

    Single-line groups are excluded for a separate reason. ``box_h / n_lines``
    is not the line height — it is the line height plus the balloon's vertical
    padding divided by the line count. A one-line box charges the whole padding
    to its only line, so it measures about 19% high corpus-wide (median ratio
    to the page median: 1.19 at one line against 1.00 at three). Left in, they
    inflate the median and push correctly wrapped multi-line groups under the
    threshold. They are not worth judging either: one line cannot be too many.
    """
    ai_text = (group.get("ai_text") or "").strip()
    text_box = group.get("text_box") or []
    if not ai_text or not text_box or _is_stylized(group):
        return None

    n_lines = len(ai_text.split("\n"))
    if n_lines < MIN_LINES_FOR_LINE_HEIGHT:
        return None

    _box_w, box_h = _box_wh(text_box)
    if box_h <= 0:
        return None

    return box_h / n_lines


def _page_median_line_height(json_groups: dict) -> float | None:
    """Median implied line height for a page, or None if too few groups to judge."""
    heights = [h for g in json_groups.values() if (h := _implied_line_height(g)) is not None]
    if len(heights) < MIN_GROUPS_FOR_LINE_HEIGHT:
        return None
    return median(heights)


def _line_height_ratio(group: dict, page_median: float | None) -> float | None:
    """Return the group's implied line height as a fraction of its page's median.

    This is the inverse of the fit check. ``_text_fits_in_box`` derives the font
    size from box height / line count, so surplus line breaks shrink the font
    and always pass — only too *few* lines can ever fail it. A group whose
    implied line height sits well below the rest of the page is the signature of
    a spurious line break, and how far below is how confident that reading is.

    Returns None when the group cannot be judged: single-line and stylized
    groups, and pages with too few groups to hold a trustworthy median.
    """
    if page_median is None or page_median <= 0:
        return None

    line_height = _implied_line_height(group)
    if line_height is None:
        return None

    return line_height / page_median


def _is_line_height_outlier(
    group: dict, page_median: float | None, fraction: float = LINE_HEIGHT_OUTLIER_FRACTION
) -> bool:
    """Whether the group's lines are packed far tighter than the page norm."""
    ratio = _line_height_ratio(group, page_median)
    return ratio is not None and ratio < fraction


def _layout_ok(
    group: dict,
    fanta_page: str,
    page_median: float | None,
    fraction: float = LINE_HEIGHT_OUTLIER_FRACTION,
) -> bool:
    """Whether a group's text both fits its box and is wrapped like the page norm."""
    return _group_text_fits(group, fanta_page) and not _is_line_height_outlier(
        group, page_median, fraction
    )


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
        line_height_limits: LineHeightLimits | None = None,
    ) -> None:
        self._comics_database = comics_database
        self._limits = line_height_limits or LineHeightLimits()
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
        all_missing: list[MissingPrelim] = []

        for title_str in title_list:
            print("-" * 80)
            title = STR_TITLE_TO_ENUM[title_str]
            volume = self._comics_database.get_fanta_volume_int(title_str)
            page_groups = self._speech_groups.get_speech_page_groups(title, skip_missing=True)
            page_panel_boxes = self._title_panel_boxes.get_page_panel_boxes(title)

            missing_pages = sorted(
                {m.fanta_page for m in self._speech_groups.get_missing_prelim_pages(title)}
            )
            if missing_pages:
                all_missing.append(MissingPrelim(volume, title_str, missing_pages))

            pages: dict[str, dict[OcrTypes, SpeechPageGroup]] = defaultdict(dict)
            for pg in page_groups:
                pages[pg.fanta_page][pg.ocr_index] = pg

            title_issues, passes = self._check_title_to_convergence(
                title_str, pages, page_panel_boxes
            )
            if passes > 1:
                logger.info(f'"{title_str}": converged after {passes} passes.')

            if title_issues:
                print(f'Issues in "{title_str}" (Vol. {volume}):')
                for issue in title_issues:
                    self._print_issue(issue)
            else:
                print(f'  No issues in "{title_str}" (Vol. {volume}).')

            all_issues.extend(title_issues)

        self._print_issues_summary(all_issues)
        self._print_missing_prelims(all_missing)
        self._write_queue_file(all_issues, output_file)

    # ── Per-title passes ──────────────────────────────────────────────────────

    def _check_title_to_convergence(
        self,
        title_str: str,
        pages: dict[str, dict[OcrTypes, SpeechPageGroup]],
        page_panel_boxes: TitlePagesPanelBoxes,
    ) -> tuple[list[IssueFound], int]:
        """Re-run the check pass until one applies no fixes. Returns (issues, passes).

        A fix can supply exactly the donor another group was waiting on — pages
        are checked and saved in order, so a group never sees a donor repaired
        later in the same pass. Repeating until nothing changes lets those
        knock-on fixes land in one invocation. Only the final pass's issues are
        returned; earlier passes list issues that were then fixed.
        """
        title_issues, there_were_fixes = self._check_title_pages(pages, page_panel_boxes)
        passes = 1
        while there_were_fixes and passes < MAX_FIX_PASSES:
            passes += 1
            title_issues, there_were_fixes = self._check_title_pages(pages, page_panel_boxes)

        if there_were_fixes:
            logger.warning(
                f'"{title_str}": still applying fixes after {MAX_FIX_PASSES} passes.'
                f" Giving up — re-run to continue."
            )

        return title_issues, passes

    def _check_title_pages(
        self,
        pages: dict[str, dict[OcrTypes, SpeechPageGroup]],
        page_panel_boxes: TitlePagesPanelBoxes,
    ) -> tuple[list[IssueFound], bool]:
        """One full pass over a title's pages. Returns (issues, any_fixes_applied)."""
        issues: list[IssueFound] = []
        any_fixes = False

        for fanta_page in sorted(pages):
            variants = pages[fanta_page]
            for ocr_index, page_group in variants.items():
                other = variants.get(_other_ocr_type(ocr_index))
                page_issues, there_were_fixes = self._check_page_group(
                    page_group, page_panel_boxes, other
                )
                issues.extend(page_issues)
                if there_were_fixes:
                    any_fixes = True

        return issues, any_fixes

    # ── Per-page / per-group checks ───────────────────────────────────────────

    def _check_page_group(
        self,
        page_group: SpeechPageGroup,
        page_panel_boxes: TitlePagesPanelBoxes,
        other_page_group: SpeechPageGroup | None = None,
    ) -> tuple[list[IssueFound], bool]:
        """Check one page/engine, applying any enabled fixes.

        Returns (issues, there_were_fixes).
        """
        volume = page_group.fanta_vol
        fanta_page = page_group.fanta_page
        engine = str(page_group.ocr_index)
        per_page_boxes = page_panel_boxes.pages[fanta_page]

        issues: list[IssueFound] = []
        there_were_fixes = False

        if self._fix_groups_order and page_group.renumber_groups():
            there_were_fixes = True

        # Read the groups only after any renumbering: renumber_groups() rebinds
        # speech_page_json["groups"] to a freshly keyed dict, and the checks must
        # report the new group ids or the queue file would point at the old ones.
        json_groups = page_group.speech_page_json.get("groups", {})

        line_heights = PageLineHeights(
            own=_page_median_line_height(json_groups),
            other=_page_median_line_height(
                other_page_group.speech_page_json.get("groups", {})
                if other_page_group is not None
                else {}
            ),
        )

        for group_id, group in json_groups.items():
            group_issues, there_were_group_fixes = self._check_group(
                volume,
                fanta_page,
                engine,
                group_id,
                group,
                per_page_boxes,
                other_page_group,
                line_heights,
            )
            issues.extend(group_issues)
            if there_were_group_fixes:
                there_were_fixes = True

        if there_were_fixes:
            page_group.save_json()

        return issues, there_were_fixes

    def _check_group(  # noqa: C901, PLR0913
        self,
        volume: int,
        fanta_page: str,
        engine: str,
        group_id: str,
        group: dict,
        page_panel_boxes: PagePanelBoxes,
        other_page_group: SpeechPageGroup | None = None,
        line_heights: PageLineHeights = PageLineHeights(None, None),  # noqa: B008
    ) -> tuple[list[IssueFound], bool]:
        ai_text = (group.get("ai_text") or "").strip()
        notes = (group.get("notes") or "").strip()
        panel_num_state, panel_num = self._get_panel_num_state(group, page_panel_boxes)

        issues: list[IssueFound] = []
        there_were_fixes = False

        def add(issue_type: str, ratio: float | None = None) -> None:
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
                    ratio=ratio,
                )
            )

        if panel_num_state == PanelNumState.PANEL_NUM_NOT_SET_UNFIXABLE:
            add("panel_unassigned")
        elif panel_num_state == PanelNumState.PANEL_NUM_NOT_SET_FIXABLE:
            there_were_fixes = self._deal_with_fixable_panel_num(group, group_id, panel_num)

        if ai_text == "":
            add("empty_text")
        elif is_short_text(group) and not is_acknowledged(group, "short_text"):
            add("short_text")
        if is_ai_detected_error(group) and not is_acknowledged(group, "error_notes"):
            add("error_notes")
        if has_page_number_notes(group) and not is_acknowledged(group, "page_number_notes"):
            add("page_number_notes")
        if has_dot_at_end_of_sentence(group) and not is_acknowledged(
            group, "dot_at_end_of_sentence"
        ):
            add("dot_at_end_of_sentence")
        if has_dash_wrong_space(group) and not is_acknowledged(group, "dash_wrong_space"):
            add("dash_wrong_space")
        if has_dash_no_spaces(group) and not is_acknowledged(group, "dash_no_spaces"):
            add("dash_no_spaces")

        if ai_text:
            layout_fixed, layout_issue, layout_ratio = self._check_text_layout(
                group, group_id, fanta_page, other_page_group, line_heights
            )
            if layout_fixed:
                there_were_fixes = True
            if layout_issue:
                add(layout_issue, layout_ratio)

        return issues, there_were_fixes

    # ── Text-layout check + optional fix ──────────────────────────────────────

    def _check_text_layout(
        self,
        group: dict,
        group_id: str,
        fanta_page: str,
        other_page_group: SpeechPageGroup | None,
        line_heights: PageLineHeights,
    ) -> tuple[bool, str | None, float | None]:
        """Return (fix_applied, issue_type_to_add, line_height_ratio).

        Two opposite wrapping failures are checked, both repaired the same way —
        by transplanting the other engine's line pattern:

        - too few lines: the text overflows its box → "text_does_not_fit".
        - too many lines: the lines are packed far tighter than the rest of the
          page, which the fit check cannot see → "too_many_lines", or
          "too_many_lines_marginal" in the noisier band just above it.

        Well-formed → (False, None, ratio). Ill-formed with no fix flag, or with
        the transplant rejected → (False, issue_type, ratio). Transplant applied
        → (True, None, ratio).
        """
        ai_text = (group.get("ai_text") or "").strip()
        text_box = group.get("text_box") or []
        if not ai_text or not text_box:
            return False, None, None

        ratio = _line_height_ratio(group, line_heights.own)

        if not _group_text_fits(group, fanta_page):
            issue = "text_does_not_fit"
        elif ratio is not None and ratio < self._limits.outlier:
            issue = "too_many_lines"
        elif self._limits.include_marginal and ratio is not None and ratio < self._limits.marginal:
            issue = "too_many_lines_marginal"
        else:
            return False, None, ratio

        if not self._fix_newlines:
            return False, issue, ratio

        if not self._transplant_line_pattern(
            group, group_id, fanta_page, other_page_group, line_heights
        ):
            return False, issue, ratio

        return True, None, ratio

    def _transplant_line_pattern(
        self,
        group: dict,
        group_id: str,
        fanta_page: str,
        other_page_group: SpeechPageGroup | None,
        line_heights: PageLineHeights,
    ) -> bool:
        """Rewrap group's ai_text to the other engine's line pattern, if that helps.

        Returns whether ai_text was changed. This is the non-interactive
        equivalent of the kivy editor's "Copy Fmt" button. The donor must itself
        be well laid out, and the rewrapped result must be too, or nothing is
        written.
        """
        ai_text = (group.get("ai_text") or "").strip()

        match = _find_matching_group(group, other_page_group)
        if match is None:
            logger.warning(
                f"Group {group_id}: badly wrapped text and no matching"
                f" group found in the other engine to transplant newlines from."
            )
            return False

        if not _layout_ok(match, fanta_page, line_heights.other, self._limits.outlier):
            logger.warning(
                f"Group {group_id}: badly wrapped text but the matching group"
                f" in the other engine is not well laid out either,"
                f" so its line pattern is not worth transplanting."
            )
            return False

        pattern_text = (match.get("ai_text") or "").strip()
        new_text = _apply_line_pattern(ai_text, pattern_text)
        if new_text == ai_text:
            logger.warning(
                f"Group {group_id}: badly wrapped text but line-pattern transplant"
                f" produced no change."
            )
            return False

        if not _layout_ok(
            {**group, "ai_text": new_text}, fanta_page, line_heights.own, self._limits.outlier
        ):
            logger.warning(
                f"Group {group_id}: line-pattern transplant did not produce a well"
                f" laid out result, so ai_text was left unchanged."
            )
            return False

        group["ai_text"] = new_text
        logger.info(f"Group {group_id}: rewrapped ai_text using other-engine pattern.")
        return True

    # ── Predicates ────────────────────────────────────────────────────────────

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
        """Write de-duplicated queue file: one entry per unique (vol, page, engine, group_id).

        A line-height issue carries its ratio as a sixth field, so a queue can be
        triaged before it is worked. ``load_queue_file`` reads only the first
        five fields, so the extra one costs the editor nothing.
        """
        seen: set[tuple[int, str, str, str]] = set()
        queue_lines: list[str] = []
        for issue in all_issues:
            key = (issue.volume, issue.fanta_page, issue.engine, issue.group_id)
            if key not in seen:
                seen.add(key)
                ratio_str = "" if issue.ratio is None else f" {issue.ratio:.2f}"
                queue_lines.append(
                    f"{issue.volume}"
                    f" {int(issue.fanta_page)}"
                    f" {issue.engine}"
                    f" {issue.group_id}"
                    f" {issue.issue_type}"
                    f"{ratio_str}"
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
    def _print_missing_prelims(all_missing: list[MissingPrelim]) -> None:
        """List the pages that were skipped for want of a prelim OCR file.

        These are not editor work, so they are kept out of the queue file. They
        are OCR that never ran, and the only place they surface otherwise is a
        warning buried in the log.
        """
        if not all_missing:
            return

        total = sum(len(m.fanta_pages) for m in all_missing)
        print()
        print(f"Missing prelim OCR — {total} page(s), OCR never ran on these:")
        for missing in sorted(all_missing, key=lambda m: (m.volume, m.title_str)):
            print(
                f"  Vol {missing.volume:>2}  {missing.title_str}:"
                f" {_format_page_ranges(missing.fanta_pages)}"
            )

    @staticmethod
    def _print_issue(issue: IssueFound) -> None:
        text_preview = issue.text.replace("\n", "\\n")[:60]
        notes_str = f", notes={issue.notes!r}" if issue.notes else ""
        ratio_str = "" if issue.ratio is None else f" ratio={issue.ratio:.2f}"
        print(
            f"  [{issue.issue_type}]"
            f" page={issue.fanta_page} {issue.engine} group={issue.group_id}"
            f" panel={issue.panel_num}{ratio_str}"
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
    include_marginal: bool = typer.Option(
        default=False,
        help="Also report the noisier line-height band as 'too_many_lines_marginal'.",
    ),
    line_height_threshold: float = typer.Option(
        LINE_HEIGHT_OUTLIER_FRACTION,
        help="Flag as 'too_many_lines' below this fraction of the page median line height.",
    ),
    line_height_marginal: float = typer.Option(
        LINE_HEIGHT_MARGINAL_FRACTION,
        help="Upper edge of the marginal band; only used with --include-marginal.",
    ),
) -> None:
    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)
    if line_height_marginal < line_height_threshold:
        err_msg = (
            f"--line-height-marginal ({line_height_marginal}) must not be below"
            f" --line-height-threshold ({line_height_threshold})."
        )
        raise typer.BadParameter(err_msg)

    comics_database = ComicsDatabase()
    volumes = list(intspan(volumes_str)) if volumes_str else []
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    limits = LineHeightLimits(
        outlier=line_height_threshold,
        marginal=line_height_marginal,
        include_marginal=include_marginal,
    )
    output_file = output or _default_output_file(volumes_str)
    OcrChecker(
        comics_database, fix_panel_nums, fix_groups_order, fix_newlines, limits
    ).check_titles(title_list, output_file)


if __name__ == "__main__":
    app()

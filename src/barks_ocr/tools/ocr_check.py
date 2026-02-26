# ruff: noqa: T201
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.panel_boxes import PagePanelBoxes, TitlePagesPanelBoxes, TitlePanelBoxes
from barks_fantagraphics.speech_groupers import SpeechGroups, SpeechPageGroup
from comic_utils.common_typer_options import TitleArg, VolumesArg
from intspan import intspan
from loguru import logger

from barks_ocr.utils.geometry import Rect
from barks_ocr.utils.ocr_box import OcrBox, PointList

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


# ── Checker ───────────────────────────────────────────────────────────────────


class OcrChecker:
    """Checks prelim OCR JSON files for issues and writes a kivy-editor queue file."""

    def __init__(self, comics_database: ComicsDatabase) -> None:
        self._comics_database = comics_database
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

            title_issues: list[IssueFound] = []
            for page_group in page_groups:
                title_issues.extend(self._check_page_group(page_group, page_panel_boxes))

            if title_issues:
                print(f'Issues in "{title_str}" (Vol. {volume}):')
                for issue in title_issues:
                    self._print_issue(issue)
            else:
                print(f'  No issues in "{title_str}" (Vol. {volume}).')

            all_issues.extend(title_issues)

        print()
        print("=" * 80)
        counts: Counter[str] = Counter(issue.issue_type for issue in all_issues)
        print(f"Total issues: {len(all_issues)}")
        for issue_type, count in sorted(counts.items()):
            print(f"  {issue_type}: {count}")

        self._write_queue_file(all_issues, output_file)

    # ── Per-page / per-group checks ───────────────────────────────────────────

    def _check_page_group(
        self, page_group: SpeechPageGroup, page_panel_boxes: TitlePagesPanelBoxes
    ) -> list[IssueFound]:
        volume = page_group.fanta_vol
        fanta_page = page_group.fanta_page
        engine = str(page_group.ocr_index)
        json_groups = page_group.speech_page_json.get("groups", {})
        page_panel_boxes = page_panel_boxes.pages[fanta_page]
        issues: list[IssueFound] = []
        for group_id, group in json_groups.items():
            issues.extend(
                self._check_group(volume, fanta_page, engine, group_id, group, page_panel_boxes)
            )
        return issues

    def _check_group(  # noqa: PLR0913
        self,
        volume: int,
        fanta_page: str,
        engine: str,
        group_id: str,
        group: dict,
        page_panel_boxes: PagePanelBoxes,
    ) -> list[IssueFound]:
        panel_num = int(group.get("panel_num", -1))
        ai_text = group.get("ai_text", "") or ""
        notes = group.get("notes", "") or ""
        issues: list[IssueFound] = []

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

        if self._is_unfixable_panel_num(group, page_panel_boxes):
            add("panel_unassigned")
        if ai_text.strip() == "":
            add("empty_text")
        elif self._is_short_text(group):
            add("short_text")
        if self._is_ai_detected_error(group):
            add("error_notes")
        if "page number" in notes.lower():
            add("page_number_notes")

        return issues

    # ── Predicates ────────────────────────────────────────────────────────────

    @staticmethod
    def _is_ai_detected_error(group: dict) -> bool:
        notes = group.get("notes", "").strip().lower() or ""
        return "error" in notes and "art" in notes and "background" in notes

    @staticmethod
    def _is_short_text(group: dict) -> bool:
        ai_text = group.get("ai_text", "").strip().lower() or ""
        return len(ai_text) == 1 and "?" not in ai_text

    def _is_unfixable_panel_num(self, group: dict, page_panel_boxes: PagePanelBoxes) -> bool:
        panel_num = int(group.get("panel_num", -1))
        if panel_num != -1:
            return False
        can_fix, _new_panel_num = self._can_replace_missing_panel_num(group, page_panel_boxes)
        return not can_fix

    # ── Panel-num fix helpers ─────────────────────────────────────────────────
    # TODO: Duplicated code from string_replacers
    def _can_replace_missing_panel_num(
        self, group: dict, page_panel_boxes: PagePanelBoxes
    ) -> tuple[bool, int]:
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
                return True, new_panel_num

        logger.warning(f"Could not find enclosing panel for box: {text_box}")

        return False, -1

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
        ocr_box = OcrBox(box, "", 0, "")
        box = ocr_box.min_rotated_rectangle
        bottom_left = box[0]
        top_right = box[1]
        box_rect = Rect(
            bottom_left[0],
            bottom_left[1],
            top_right[0] - bottom_left[0],
            top_right[1] - bottom_left[1],
        )

        for i, panel_box in enumerate(page_panel_boxes.panel_boxes):  # type: ignore[union-attr]
            top_left_x = panel_box.x0
            top_left_y = panel_box.y0
            w = panel_box.w
            h = panel_box.h
            panel_rect = Rect(top_left_x, top_left_y, w, h)
            if panel_rect.is_rect_inside_rect(box_rect):
                return i + 1

        return -1

    # ── Output helpers ────────────────────────────────────────────────────────

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


# ── CLI ───────────────────────────────────────────────────────────────────────

app = typer.Typer()


def _default_output_file(volumes_str: str) -> Path:
    today = datetime.now(tz=UTC).date().isoformat()
    if volumes_str:
        safe = volumes_str.replace(",", "_").replace(" ", "")
        return Path(f"ocr-check-vol-{safe}-{today}.txt")
    return Path(f"ocr-check-{today}.txt")


@app.command(help="Check prelim OCR JSON files for issues and write a kivy-editor queue file.")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    output: Path = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Queue file path (default: auto-named ocr-check-vol-N-DATE.txt in CWD)",
    ),
) -> None:
    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    comics_database = ComicsDatabase()
    volumes = list(intspan(volumes_str)) if volumes_str else []
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    output_file = output or _default_output_file(volumes_str)
    OcrChecker(comics_database).check_titles(title_list, output_file)


if __name__ == "__main__":
    app()

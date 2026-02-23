# ruff: noqa: T201

import codecs
import re
import textwrap

import typer
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.panel_boxes import PagePanelBoxes, TitlePagesPanelBoxes, TitlePanelBoxes
from barks_fantagraphics.speech_groupers import SpeechGroups, SpeechPageGroup
from comic_utils.common_typer_options import TitleArg, VolumesArg
from intspan import intspan

from barks_ocr.utils.geometry import Rect
from barks_ocr.utils.ocr_box import OcrBox, PointList

SKIP_PREFIXES = {
    (" - ", 12): [105],
    (" -- ", 7): [135],
}


class PageCleaner:
    def __init__(
        self,
        dry_run: bool,
        speech_page_group: SpeechPageGroup,
        page_panel_boxes: PagePanelBoxes,
        skip_pages: list[int],
        target_regex: re.Pattern[str] | None,
        replacement_string: str,
    ) -> None:
        self._dry_run = dry_run
        self._speech_page_group = speech_page_group
        self._page_panel_boxes = page_panel_boxes
        self._skip_pages = skip_pages
        self._target_regex = target_regex
        self._replacement_string = replacement_string

        self.lines_changed_count = 0
        self.file_modified = False

    def clean(self) -> None:
        fanta_page = self._speech_page_group.fanta_page
        file_path = self._speech_page_group.ocr_prelim_groups_json_file
        prelim_ocr_json = self._speech_page_group.speech_page_json

        try:
            dirty_content = False
            remove_groups = []
            for group_id, group in prelim_ocr_json["groups"].items():
                if self._remove_group(group_id, group):
                    dirty_content = True
                    print(f"For file {file_path.name}, remove group {group_id}.")
                    remove_groups.append(group_id)
                    continue

                replace_panel_num, new_panel_num = self._replace_missing_panel_num(group_id, group)
                if replace_panel_num:
                    dirty_content = True
                    group["panel_num"] = new_panel_num
                    self.lines_changed_count += 1

                if int(fanta_page) in self._skip_pages:
                    print(f'PAGE IN SKIP LIST. SKIPPING "{file_path.name}".')
                elif self._target_regex:
                    replace_text, new_ai_text = self._get_replace_text(group_id, group)
                    if replace_text:
                        dirty_content = True
                        group["ai_text"] = new_ai_text
                        self.lines_changed_count += 1

            if dirty_content:
                self._replace_json(remove_groups)
                self.file_modified = True
        except Exception as e:  # noqa: BLE001
            print(f'**** ERROR processing "{file_path}": {e}')

    def _remove_group(self, group_id: str, group: dict) -> bool:
        if self._is_page_number_or_dodgy_char(group):
            print(
                f"Group ID: {group_id}, panel num: {group['panel_num']}"
                f' (Panel id: {group["panel_id"]}): {group["ai_text"]!r}, notes: "{group["notes"]}"'
            )
            return True

        return False

    def _is_page_number_or_dodgy_char(self, group: dict) -> bool:
        # panel_id = group["panel_id"]
        # if panel_id in ["title", "header"]:
        #     return True
        # if "the comic title" in group["notes"]:
        #     return True

        return False

        panel_num = int(group["panel_num"])

        if panel_num == -1:
            if group["notes"] and "error" in group["notes"].lower():
                return True
            if group["notes"] and "page number" in group["notes"].lower():
                return True
            return (
                (group["ai_text"].strip() == "")
                or len(group["ai_text"]) == 1
                or (group["ai_text"].upper() in ["W", " "])
            )

        return False

    def _replace_missing_panel_num(self, _group_id: str, group: dict) -> tuple[bool, int]:
        panel_num = int(group["panel_num"])

        if panel_num != -1:
            return False, -1

        # Look for a containing panel by trying successively smaller text boxes.
        text_box = group["text_box"]
        reduce_by_amounts = [20, 40, 60]

        for reduce_by in reduce_by_amounts:
            can_do, reduced_box = self._get_reduced_text_box(text_box, reduce_by)
            if not can_do:
                break

            assert reduced_box
            new_panel_num = self._get_enclosing_panel_num(reduced_box)

            if new_panel_num != -1:
                print(
                    f'For file "{self._speech_page_group.ocr_prelim_groups_json_file.name}"'
                    f" and text {group['ai_text']!r},"
                    f" fix panel_num with new value {new_panel_num}."
                )
                return True, new_panel_num

        print(
            f'*** ERROR: For file "{self._speech_page_group.ocr_prelim_groups_json_file.name}",'
            f" could not fix panel num for text {group['ai_text']!r}."
        )
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

    def _get_enclosing_panel_num(self, box: PointList) -> int:
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
        # print("box_rect", "XX", box_rect, "XX")

        for i, panel_box in enumerate(self._page_panel_boxes.panel_boxes):
            top_left_x = panel_box.x0
            top_left_y = panel_box.y0
            w = panel_box.w
            h = panel_box.h
            panel_rect = Rect(top_left_x, top_left_y, w, h)
            # print("panel_rect", i, "YY", panel_rect, "YY")
            if panel_rect.is_rect_inside_rect(box_rect):
                # print(f"Is inside: {i+1}.")
                return i + 1

        return -1

    def _get_replace_text(self, _group_id: str, group: dict) -> tuple[bool, str]:
        ai_text = group["ai_text"]
        assert self._target_regex is not None
        new_ai_text = self._target_regex.sub(self._replacement_string, ai_text)
        if new_ai_text != ai_text:
            print(
                f"Modified ai_text:\n"
                f"{textwrap.indent(ai_text, ' ' * 4)} ->\n"
                f"====\n"
                f"{textwrap.indent(group['ai_text'], ' ' * 4)}\n"
            )
            return True, new_ai_text

        return False, ""

    def _replace_json(
        self,
        remove_groups: list[str],
    ) -> None:
        if self._dry_run:
            print(
                f"DRY RUN: Would have modified {self.lines_changed_count}"
                f' lines in "{self._speech_page_group.ocr_prelim_groups_json_file.name}".'
            )
            print(
                f"DRY RUN: Would have removed {len(remove_groups)}"
                f' groups in "{self._speech_page_group.ocr_prelim_groups_json_file.name}".'
            )
        else:
            for group_id in remove_groups:
                del self._speech_page_group.speech_page_json["groups"][group_id]
            self._speech_page_group.save_json()
            print(
                f'Modified "{self._speech_page_group.ocr_prelim_groups_json_file.name}",'
                f" wrote new json to file."
            )


class PrelimOCRCleaner:
    def __init__(self, dry_run: bool, comics_database: ComicsDatabase) -> None:
        self._comics_database = comics_database
        self._dry_run = dry_run
        self._speech_groups = SpeechGroups(self._comics_database)
        self._title_panel_boxes = TitlePanelBoxes(self._comics_database)

        self._files_checked_count = 0
        self._files_processed_count = 0
        self._lines_process_count = 0

    def clean_titles(
        self,
        title_list: list[str],
        target_string: str,
        replacement_string: str,
    ) -> None:
        self._files_checked_count = 0
        self._files_processed_count = 0
        self._lines_process_count = 0

        for title_str in title_list:
            print("-" * 80)

            title = BARKS_TITLE_DICT[title_str]
            volume = self._comics_database.get_fanta_volume_int(title_str)
            skip_pages = SKIP_PREFIXES.get((target_string, volume), [])
            speech_page_groups = self._speech_groups.get_speech_page_groups(title)
            page_panel_boxes = self._title_panel_boxes.get_page_panel_boxes(title)

            self._replace_string_in_title(
                title_str,
                speech_page_groups,
                page_panel_boxes,
                skip_pages,
                target_string,
                replacement_string,
            )

            print()

        print()
        print("-" * 80)
        print(
            f"\nReplacement complete. Total files checked: {self._files_checked_count};"
            f" files modified: {self._files_processed_count};"
            f" lines modified: {self._lines_process_count}.\n"
        )

    def _replace_string_in_title(
        self,
        title_str: str,
        speech_page_groups: list[SpeechPageGroup],
        page_panel_boxes: TitlePagesPanelBoxes,
        skip_pages: list[int],
        target_string: str,
        replacement_string: str,
    ) -> None:
        print(f'Starting replacement process for "{title_str}"...')
        print(f"Target: '{target_string}', Replacement: '{replacement_string}'\n")

        if not target_string:
            print("NO TARGET STRING SPECIFIED. SKIPPING STRING REPLACEMENT.\n")
            target_regex = None
        else:
            try:
                target_regex = re.compile(target_string)
            except re.error as e:
                print(f"Error: Invalid regex pattern '{target_string}': {e}")
                return

        for speech_page_group in speech_page_groups:
            fanta_page = speech_page_group.fanta_page

            page_cleaner = PageCleaner(
                self._dry_run,
                speech_page_group,
                page_panel_boxes.pages[fanta_page],
                skip_pages,
                target_regex,
                replacement_string,
            )
            page_cleaner.clean()

            self._files_checked_count += 1
            if page_cleaner.file_modified:
                self._files_processed_count += 1
            self._lines_process_count += page_cleaner.lines_changed_count


app = typer.Typer()


@app.command(help="Replace string in JSON files")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    target: str = "",
    replace: str = "",
    dry_run: bool = False,
) -> None:
    # Decode escape sequences (like \n or \u2014) in the input strings.
    target_str = codecs.decode(target, "unicode_escape")
    replacement_str = codecs.decode(replace, "unicode_escape")

    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    prelim_ocr_cleaner = PrelimOCRCleaner(dry_run, comics_database)
    prelim_ocr_cleaner.clean_titles(title_list, target_str, replacement_str)


if __name__ == "__main__":
    app()

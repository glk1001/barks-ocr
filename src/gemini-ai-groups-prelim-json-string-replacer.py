# ruff: noqa: T201
import codecs
import json
import re
import textwrap
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT, is_non_comic_title
from barks_fantagraphics.comics_consts import BARKS_ROOT_DIR
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.panel_boxes import PagePanelBoxes, TitlePagesPanelBoxes, TitlePanelBoxes
from barks_fantagraphics.speech_groupers import SpeechGroups, SpeechPageGroup
from comic_utils.common_typer_options import TitleArg, VolumesArg
from intspan import intspan
from loguru import logger

from utils.geometry import Rect
from utils.ocr_box import OcrBox, PointList

PANEL_SEGMENTS_ROOT_DIR = BARKS_ROOT_DIR / "Fantagraphics-restored-panel-segments"

SKIP_PREFIXES = {
    (" - ", 12): [105],
    (" -- ", 7): [135],
}


def replace_string_in_titles(
    comics_database: ComicsDatabase,
    titles: list[str],
    target_string: str,
    replacement_string: str,
    dry_run: bool = False,
) -> None:
    for title_str in titles:
        if is_non_comic_title(title_str):
            logger.warning(f'Not a comic title "{title_str}" - skipping.')
            continue

        title = BARKS_TITLE_DICT[title_str]
        volume = comics_database.get_fanta_volume_int(title_str)
        skip_pages = SKIP_PREFIXES.get((target_string, volume), [])
        speech_groups = SpeechGroups(comics_database)
        title_panel_boxes = TitlePanelBoxes(comics_database)
        speech_page_groups = speech_groups.get_speech_page_groups(title)
        page_panel_boxes = title_panel_boxes.get_page_panel_boxes(title)

        replace_string_in_title(
            title_str,
            speech_page_groups,
            page_panel_boxes,
            skip_pages,
            target_string,
            replacement_string,
            dry_run,
        )


def replace_string_in_title(
    title_str: str,
    speech_page_groups: list[SpeechPageGroup],
    page_panel_boxes: TitlePagesPanelBoxes,
    skip_pages: list[int],
    target_string: str,
    replacement_string: str,
    dry_run: bool = False,
) -> None:
    print("-" * 80)
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

    files_checked_count = 0
    files_processed_count = 0
    lines_process_count = 0

    for speech_page_group in speech_page_groups:
        fanta_page = speech_page_group.fanta_page
        file_path = speech_page_group.ocr_prelim_groups_json_file
        json_ocr = speech_page_group.speech_page_json

        files_checked_count += 1
        try:
            dirty_content = False
            lines_changed_in_file = 0
            remove_groups = []
            for group_id, group in json_ocr["groups"].items():
                if remove_group(group_id, group):
                    dirty_content = True
                    print(f"For page {file_path}, remove group {group_id}.")
                    remove_groups.append(group_id)
                    continue

                replace_panel_num, new_panel_num = replace_missing_panel_num(
                    group_id, group, page_panel_boxes.pages[fanta_page]
                )
                if replace_panel_num:
                    if new_panel_num == -1:
                        print(
                            f"For page {file_path.name},"
                            f" could not fix panel num for text {group['ai_text']!r}."
                        )
                    else:
                        dirty_content = True
                        print(
                            f"For page {file_path.name} and text {group['ai_text']!r},"
                            f" fix panel_num with new value {new_panel_num}."
                        )
                        group["panel_num"] = new_panel_num
                        lines_process_count += 1
                        lines_changed_in_file += 1

                if int(fanta_page) in skip_pages:
                    print(f'PAGE IN SKIP LIST. SKIPPING "{file_path.name}".')
                elif target_string:
                    replace_text, new_ai_text = get_replace_text(
                        group_id, group, target_regex, replacement_string
                    )
                    if replace_text:
                        dirty_content = True
                        group["ai_text"] = new_ai_text
                        lines_process_count += 1
                        lines_changed_in_file += 1

            if dirty_content:
                replace_json(dry_run, file_path, lines_changed_in_file, remove_groups, json_ocr)
                files_processed_count += 1
        except Exception as e:  # noqa: BLE001
            print(f"Error processing {file_path}: '{e}'")

    print(
        f"\nReplacement complete. Total files checked: {files_checked_count};"
        f" files modified: {files_processed_count};"
        f" lines modified: {lines_process_count}.\n"
    )


def remove_group(group_id: int, group: dict) -> bool:
    if _is_page_number_or_dodgy_char(group):
        print(
            f"Group ID: {group_id}, panel num: {group['panel_num']}"
            f' (Panel id: {group["panel_id"]}): {group["ai_text"]!r}, notes: "{group["notes"]}"'
        )
        return True

    return False


def _is_page_number_or_dodgy_char(group: dict) -> bool:
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


def replace_missing_panel_num(
    _group_id: str, group: dict, page_panel_boxes: PagePanelBoxes
) -> tuple[bool, int]:
    panel_num = int(group["panel_num"])

    if panel_num != -1:
        return False, -1

    # print(
    #     f'Panel num: {panel_num} (Panel id: {group["panel_id"]}): "{group["ai_text"]!r}"'
    # )

    # Look for a containing panel.
    text_box = group["text_box"]
    reduce_by_amounts = [20, 40, 60]

    for reduce_by in reduce_by_amounts:
        can_do, reduced_box = get_reduced_text_box(text_box, reduce_by)
        if not can_do:
            return True, -1

        new_panel_num = _get_enclosing_panel_num(reduced_box, page_panel_boxes)

        # print(
        #     f'New panel num: {new_panel_num} (Panel id: {group["panel_id"]}): "{group["ai_text"]!r}"'
        # )

        if new_panel_num != -1:
            return True, new_panel_num

    return True, -1


def get_reduced_text_box(text_box: PointList, reduce_by: int) -> tuple[bool, PointList | None]:
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
    # print("box_rect", "XX", box_rect, "XX")

    for i, panel_box in enumerate(page_panel_boxes.panel_boxes):
        top_left_x = panel_box.x0
        top_left_y = panel_box.y1
        w = panel_box.w
        h = panel_box.h
        panel_rect = Rect(top_left_x, top_left_y, w, h)
        # print("panel_rect", i, "YY", panel_rect, "YY")
        if panel_rect.is_rect_inside_rect(box_rect):
            # print(f"Is inside: {i+1}.")
            return i + 1

    return -1


def get_replace_text(
    _group_id: int,
    group: dict,
    target_regex: re.Pattern[str],
    replacement_string: str,
) -> tuple[bool, str]:
    ai_text = group["ai_text"]
    new_ai_text = target_regex.sub(replacement_string, ai_text)
    if new_ai_text != ai_text:
        print(
            f"Modified ai_text:\n"
            f"{textwrap.indent(ai_text, ' ' * 4)} ->\n"
            f"====\n"
            f"{textwrap.indent(group['ai_text'], ' ' * 4)}\n"
        )
        return True, new_ai_text

    return False, ""


def replace_json(
    dry_run: bool,
    file_path: Path,
    lines_changed_in_file: int,
    remove_groups: list[str],
    json_ocr: dict,
) -> None:
    if dry_run:
        print(f'DRY RUN: Would have modified {lines_changed_in_file} lines in "{file_path.name}".')
        print(f'DRY RUN: Would have removed {len(remove_groups)} groups in "{file_path.name}".\n')
    else:
        for group_id in remove_groups:
            del json_ocr["groups"][group_id]
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(json_ocr, f, indent=4)
        print(f'Modified "{file_path.name}", wrote new json to file.')


app = typer.Typer()


@app.command(help="Replace string in JSON files")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    target: str = "",
    replace: str = "",
    dry_run: bool = False,
) -> None:
    # Decode escape sequences (like \n or \u2014) in the input strings
    target_str = codecs.decode(target, "unicode_escape")
    replacement_str = codecs.decode(replace, "unicode_escape")

    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()
    titles = get_titles(comics_database, volumes, title_str)

    replace_string_in_titles(
        comics_database,
        titles,
        target_str,
        replacement_str,
        dry_run,
    )


if __name__ == "__main__":
    app()

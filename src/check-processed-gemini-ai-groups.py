import json
import sys
from pathlib import Path

from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_ocr_type
from loguru import logger
from loguru_config import LoguruConfig
from thefuzz import fuzz, process

from ocr_file_paths import (
    BATCH_JOBS_OUTPUT_DIR,
    OCR_ANNOTATIONS_DIR,
    OCR_FIXES_DIR,
    OCR_RESULTS_DIR,
    get_ocr_boxes_annotated_filename,
    get_ocr_final_groups_json_filename,
    get_ocr_final_text_annotated_filename,
    get_ocr_predicted_groups_filename,
)

APP_LOGGING_NAME = "chkr"


def get_fix_command(
    volume_dirname: str,
    ocr_type_file: tuple[Path, Path],
    group_id: int,
    other_group_id: int,
    ai_text: str,
    other_ai_text: str,
) -> dict:
    ocr_type1 = get_ocr_type(ocr_type_file[0])
    ocr_type2 = get_ocr_type(ocr_type_file[1])
    svg_stem = ocr_type_file[0].stem[:3]

    file1_to_edit = (
        BATCH_JOBS_OUTPUT_DIR
        / volume_dirname
        / get_ocr_predicted_groups_filename(svg_stem, ocr_type1)
    )
    file2_to_edit = (
        BATCH_JOBS_OUTPUT_DIR
        / volume_dirname
        / get_ocr_predicted_groups_filename(svg_stem, ocr_type2)
    )

    file1_image = (
        OCR_ANNOTATIONS_DIR / volume_dirname / get_ocr_boxes_annotated_filename(svg_stem, ocr_type1)
    )

    target_key = "cleaned_text"
    file1_line = -1
    file2_line = -1
    if file1_to_edit.is_file():
        file1_line = find_line_number_in_json_string(file1_to_edit, group_id + 1, target_key)
    if (other_group_id != -1) and file2_to_edit.is_file():
        file2_line = find_line_number_in_json_string(file2_to_edit, other_group_id + 1, target_key)

    logger.info(
        f'Setting up fix command. Page {svg_stem},'
        f' group {group_id} in "{file1_to_edit}", line {file1_line}.'
    )
    logger.info(
        f'Setting up fix command. Page {svg_stem},'
        f' group {other_group_id} in "{file2_to_edit}", line {file2_line}.'
    )
    logger.info(f'Setting up fix command. Image to view: "{file1_image}".')

    return {
        "group_id": group_id,
        "other_group_id": other_group_id,
        "file1": str(file1_to_edit),
        "file2": str(file2_to_edit),
        "line1": file1_line,
        "line2": file2_line,
        "cleaned_text1": ai_text,
        "cleaned_text2": other_ai_text,
        "image_file": str(file1_image),
    }


def find_line_number_in_json_string(json_file: Path, n: int, target_key: str) -> int:
    # Find the line number of the nth target_key.
    assert target_key
    assert n > 0

    lines = json_file.read_text().splitlines()

    count = 0
    for i, line in enumerate(lines):
        line_number = i + 1  # 1-based line number

        if f'"{target_key}":' in line:
            count += 1
            if count == n:
                return line_number

    return -1


def check_gemini_ai_groups_for_titles(
    titles: list[str], compare_text: bool, show_close: bool
) -> None:
    total_errors = 0

    for title in titles:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        total_errors += check_gemini_ai_groups_for_title(title, compare_text, show_close)

    if total_errors == 0:
        logger.success("All comic titles checked - no errors found.")
    else:
        logger.error(f"There were {total_errors} errors found.")


def check_gemini_ai_groups_for_title(title: str, compare_text: bool, show_close: bool) -> int:
    volume_dirname = comics_database.get_fantagraphics_volume_title(
        comics_database.get_fanta_volume_int(title)
    )
    title_results_dir = OCR_RESULTS_DIR / volume_dirname
    title_annotated_images_dir = OCR_ANNOTATIONS_DIR / volume_dirname

    logger.info(
        f'Checking processed OCR groups for all pages in "{title}".'
        f' Looking in directory "{title_results_dir}"...'
    )

    comic = comics_database.get_comic_book(title)
    ocr_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)

    fix_objects = {}
    num_errors = 0
    for ocr_file in ocr_files:
        missing_ocr_file = False
        svg_stem = ocr_file[0].stem[:3]
        for ocr_type_file in ocr_file:
            ocr_type = get_ocr_type(ocr_type_file)

            ocr_final_groups_json_file = title_results_dir / get_ocr_final_groups_json_filename(
                svg_stem, ocr_type
            )
            if not ocr_final_groups_json_file.is_file():
                logger.error(f'Missing final groups json file: "{ocr_final_groups_json_file}".')
                num_errors += 1
                missing_ocr_file = True
            else:
                ocr_final_groups_annotated_file = (
                    title_annotated_images_dir
                    / get_ocr_final_text_annotated_filename(svg_stem, ocr_type)
                )
                if not ocr_final_groups_annotated_file.is_file():
                    logger.error(
                        f'Missing final groups annotated file: "{ocr_final_groups_json_file}".'
                    )
                    num_errors += 1

        if compare_text and not missing_ocr_file:
            fix_objects[svg_stem] = compare_ai_texts(
                volume_dirname, title_results_dir, ocr_file, show_close
            )

    if num_errors > 0:
        logger.error(f'There were {num_errors} errors for title "{title}".')

    if fix_objects:
        OCR_FIXES_DIR.mkdir(parents=True, exist_ok=True)
        fixes_file = OCR_FIXES_DIR / (title + ".json")
        with fixes_file.open("w") as f:
            json.dump(fix_objects, f, indent=4)

        logger.info(f'Fixes file saved to "{fixes_file}".')

    return num_errors


def compare_ai_texts(
    volume_dirname: str,
    title_results_dir: Path,
    ocr_type_file: tuple[Path, Path],
    show_close: bool,
) -> dict:
    ocr_type1 = get_ocr_type(ocr_type_file[0])
    ocr_type2 = get_ocr_type(ocr_type_file[1])
    svg_stem = ocr_type_file[0].stem[:3]

    ocr_final_groups_json_file1 = title_results_dir / get_ocr_final_groups_json_filename(
        svg_stem, ocr_type1
    )
    ocr_final_groups_json_file2 = title_results_dir / get_ocr_final_groups_json_filename(
        svg_stem, ocr_type2
    )

    ocr_group_data1 = json.loads(ocr_final_groups_json_file1.read_text())
    ocr_group_data2 = json.loads(ocr_final_groups_json_file2.read_text())

    ocr_group_2_ai_texts = [group["ai_text"] for group in ocr_group_data2.values()]

    logger.info(f'Checking ai_text in "{ocr_final_groups_json_file1}"...')

    fix_objects = {}
    for group_id, group in ocr_group_data1.items():
        ai_text = group["ai_text"]
        if ai_text in ocr_group_2_ai_texts:
            continue

        close = False
        other_group_id = -1
        other_ai_text = ""
        required_score = 95
        for index, ai_text2 in enumerate(ocr_group_2_ai_texts):
            if fuzz.partial_ratio(ai_text, ai_text2) > required_score:
                if show_close:
                    other_group_id = index
                    other_ai_text = ai_text2
                    logger.warning(
                        f'Group {group_id}: Could not find this ai_text in other:\n\n"{ai_text}"'
                        f'\n\nBUT from OTHER group {other_group_id},'
                        f'\n\n"{other_ai_text}"\n\nis close'
                        f" (partial ratio > {required_score})."
                    )
                close = True
                break

        if not close:
            required_score = 80
            other_ai_texts = {str(index): text for index, text in enumerate(ocr_group_2_ai_texts)}
            similarity_scores = process.extract(ai_text, other_ai_texts, scorer=fuzz.ratio)
            for (value,score,other_group_id) in similarity_scores:
                if score > required_score:
                    if show_close:
                        other_ai_text = value
                        logger.warning(
                            f"Group {group_id}: Could not find this ai_text in other:"
                            f'\n\n"{ai_text}"'
                            f'\n\nBUT from OTHER group {other_group_id}'
                            f'\n\n"{other_ai_text}"\n\nis close'
                            f" (similarity > {required_score})."
                        )
                    close = True
                    break

        if not close:
            logger.error(
                f'Group {group_id}: Could not find ai_text:\n\n"{ai_text}"'
                f"\n\nin other:\n\n{ocr_group_2_ai_texts}."
            )

        logger.debug(f"Appending fixes info for group {group_id}")
        fix_objects[int(group_id)] = get_fix_command(
            volume_dirname,
            ocr_type_file,
            int(group_id),
            int(other_group_id),
            ai_text,
            other_ai_text,
        )

    return fix_objects


if __name__ == "__main__":
    extra_args: list[ExtraArg] = [
        ExtraArg("--compare-text", action="store_true", type=None, default=None),
        ExtraArg("--show-close", action="store_true", type=None, default=None),
    ]

    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title", CmdArgNames.VOLUME | CmdArgNames.TITLE, extra_args
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = "make-gemini-ai-groups-batch-job.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    check_gemini_ai_groups_for_titles(
        cmd_args.get_titles(),
        compare_text=cmd_args.get_extra_arg("--compare_text"),
        show_close=cmd_args.get_extra_arg("--show_close"),
    )

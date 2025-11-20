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
    OCR_RESULTS_DIR,
    get_ocr_final_groups_json_filename,
    get_ocr_final_text_annotated_filename,
)

APP_LOGGING_NAME = "chkr"


def check_gemini_ai_groups_for_titles(titles: list[str], compare_text: bool, show_close: bool) -> None:
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

    logger.info(
        f'Checking processed OCR groups for all pages in "{title}".'
        f' Looking in directory "{title_results_dir}"...'
    )

    comic = comics_database.get_comic_book(title)
    ocr_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)

    num_errors = 0
    for ocr_file in ocr_files:
        missing_ocr_file = False
        for ocr_type_file in ocr_file:
            svg_stem = ocr_type_file.stem[:3]
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
                    title_results_dir / get_ocr_final_text_annotated_filename(svg_stem, ocr_type)
                )
                if not ocr_final_groups_annotated_file.is_file():
                    logger.error(
                        f'Missing final groups annotated file: "{ocr_final_groups_json_file}".'
                    )
                    num_errors += 1

        if compare_text and not missing_ocr_file:
            compare_ai_texts(title_results_dir, ocr_file, show_close)

    if num_errors > 0:
        logger.error(f'There were {num_errors} errors for title "{title}".')

    return num_errors


def compare_ai_texts(
    title_results_dir: Path, ocr_type_file: tuple[Path, Path], show_close: bool
) -> None:
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

    for group_id, group in ocr_group_data1.items():
        ai_text = group["ai_text"]
        if ai_text in ocr_group_2_ai_texts:
            continue

        close = False
        required_score = 95
        for other_ai_text in ocr_group_2_ai_texts:
            if fuzz.partial_ratio(ai_text, other_ai_text) > required_score:
                if show_close:
                    logger.warning(
                        f'Group {group_id}: Could not find this ai_text in other:\n\n"{ai_text}"'
                        f'\n\nBUT from OTHER\n\n"{other_ai_text}"\n\nis close'
                        f" (partial ratio > {required_score})."
                    )
                close = True
                break

        if not close:
            required_score = 80
            similarity_scores = process.extract(ai_text, ocr_group_2_ai_texts, scorer=fuzz.ratio)
            for score in similarity_scores:
                if score[1] > required_score:
                    if show_close:
                        logger.warning(
                            f"Group {group_id}: Could not find this ai_text in other:"
                            f'\n\n"{ai_text}"'
                            f'\n\nBUT from OTHER\n\n"{score[0]}"\n\nis close'
                            f" (similarity > {required_score})."
                        )
                    close = True
                    break

        if not close:
            logger.error(
                f'Group {group_id}: Could not find ai_text:\n\n"{ai_text}"'
                f'\n\nin other:\n\n{ocr_group_2_ai_texts}.'
            )


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
        cmd_args.get_titles(), compare_text=cmd_args.get_extra_arg("--compare_text"), show_close=cmd_args.get_extra_arg("--show_close")
    )

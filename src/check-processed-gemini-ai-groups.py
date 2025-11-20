import sys
from pathlib import Path

from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_ocr_type
from loguru import logger
from loguru_config import LoguruConfig

from ocr_file_paths import (
    OCR_RESULTS_DIR,
    get_ocr_final_groups_json_filename,
)

APP_LOGGING_NAME = "chkr"


def check_gemini_ai_groups_for_titles(titles: list[str]) -> None:
    for title in titles:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        check_gemini_ai_groups_for_title(title)


def check_gemini_ai_groups_for_title(title: str) -> None:
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
        for ocr_type_file in ocr_file:
            svg_stem = ocr_type_file.stem[:3]
            ocr_type = get_ocr_type(ocr_type_file)
            ocr_final_groups_json_file = title_results_dir / get_ocr_final_groups_json_filename(
                svg_stem, ocr_type
            )
            if not ocr_final_groups_json_file.is_file():
                logger.error(f'Missing final groups file: "{ocr_final_groups_json_file}".')
                num_errors += 1

    if num_errors > 0:
        logger.error(f'There were {num_errors} errors for title "{title}".')


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title",
        CmdArgNames.VOLUME | CmdArgNames.TITLE,
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

    check_gemini_ai_groups_for_titles(cmd_args.get_titles())

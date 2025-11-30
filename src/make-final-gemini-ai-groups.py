import json
import sys
from pathlib import Path

from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from loguru import logger
from loguru_config import LoguruConfig

from ocr_json_files import JsonFiles

APP_LOGGING_NAME = "gemf"


def make_final_gemini_ai_groups_for_titles(titles: list[str]) -> None:
    for title in titles:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        make_final_gemini_ai_groups_for_title(title)


def make_final_gemini_ai_groups_for_title(title: str) -> None:
    json_files = JsonFiles(comics_database, title)
    json_files.title_final_results_dir.mkdir(parents=True, exist_ok=True)

    comic = comics_database.get_comic_book(title)
    ocr_files = comic.get_srce_restored_raw_ocr_story_files(RESTORABLE_PAGE_TYPES)

    for ocr_file in ocr_files:
        json_files.set_ocr_file(ocr_file)

        ocr_prelim_group1 = json.loads(json_files.ocr_prelim_groups_json_file[0].read_text())
        ocr_prelim_group2 = json.loads(json_files.ocr_prelim_groups_json_file[1].read_text())
        assert (not ocr_prelim_group1["use_as_final"]) or (not ocr_prelim_group2["use_as_final"])
        if ocr_prelim_group1["use_as_final"]:
            with json_files.ocr_final_groups_json_file[0].open("w") as f:
                json.dump(ocr_prelim_group1["groups"], f, indent=4)
        elif ocr_prelim_group2["use_as_final"]:
            with json_files.ocr_final_groups_json_file[1].open("w") as f:
                json.dump(ocr_prelim_group2["groups"], f, indent=4)
        else:
            logger.warning(f'"{title}, {json_files.page}": Not ready for final yet.')


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title", CmdArgNames.VOLUME | CmdArgNames.TITLE
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

    make_final_gemini_ai_groups_for_titles(cmd_args.get_titles())

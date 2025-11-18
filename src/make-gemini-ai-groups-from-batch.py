import json
import sys
from pathlib import Path
from typing import Any

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from loguru import logger
from loguru_config import LoguruConfig

from gemini_ai_ocr_grouper import GeminiAiGrouper

APP_LOGGING_NAME = "gemg"


def get_ai_predicted_groups(
    ocr_name: str, prelim_dir: Path, _ocr_bound_ids: list[dict[str, Any]], _png_file: Path
) -> Any:  # noqa: ANN401
    temp_ai_predicted_groups_file = prelim_dir / f"{ocr_name}-ocr-ai-predicted-groups.json"

    logger.info(f'Reading gemini ai predicted groups from "{temp_ai_predicted_groups_file}".')

    with temp_ai_predicted_groups_file.open("r") as f:
        return json.load(f)


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title",
        CmdArgNames.VOLUME | CmdArgNames.TITLE | CmdArgNames.WORK_DIR,
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = "make-gemini-ai-groups-from-batch.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    output_dir = cmd_args.get_work_dir()
    prelim_results_dir = output_dir / "prelim"
    gemini_ai_grouper = GeminiAiGrouper(
        comics_database, prelim_results_dir, output_dir, get_ai_predicted_groups
    )
    gemini_ai_grouper.make_groups_for_titles(cmd_args.get_titles())

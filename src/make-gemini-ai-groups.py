import json
import sys
from pathlib import Path
from typing import Any

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from loguru import logger
from loguru_config import LoguruConfig
from PIL import Image

from gemini_ai_ocr_grouper import GeminiAiGrouper
from ocr_file_paths import get_ocr_predicted_groups_filename
from utils.gemini_ai_for_grouping import get_ai_predicted_groups
from utils.preprocessing import preprocess_image

APP_LOGGING_NAME = "gemg"


def get_predicted_groups_from_ai(
    svg_stem: str,
    ocr_type: str,
    prelim_dir: Path,
    ocr_bound_ids: list[dict[str, Any]],
    png_file: Path,
) -> list[Any]:
    bw_image = get_bw_image_from_alpha(png_file)
    bw_image = preprocess_image(bw_image)

    ai_predicted_groups = get_ai_predicted_groups(
        svg_stem, ocr_type, Image.fromarray(bw_image), ocr_bound_ids
    )
    temp_ai_predicted_groups_file = prelim_dir / get_ocr_predicted_groups_filename(
        svg_stem, ocr_type
    )

    logger.info(f'Writing gemini ai predicted groups to "{temp_ai_predicted_groups_file}".')

    with temp_ai_predicted_groups_file.open("w") as f:
        json.dump(ai_predicted_groups, f, indent=4)

    return ai_predicted_groups


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
    log_filename = "make-gemini-ai-groups.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    output_dir = cmd_args.get_work_dir()
    prelim_results_dir = output_dir / "prelim"
    gemini_ai_grouper = GeminiAiGrouper(
        comics_database, prelim_results_dir, output_dir, get_predicted_groups_from_ai
    )
    gemini_ai_grouper.make_groups_for_titles(cmd_args.get_titles())

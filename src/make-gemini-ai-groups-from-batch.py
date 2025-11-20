import json
import sys
from pathlib import Path
from typing import Any

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from loguru import logger
from loguru_config import LoguruConfig

from gemini_ai_ocr_grouper import GeminiAiGrouper
from ocr_file_paths import BATCH_JOBS_OUTPUT_DIR, OCR_RESULTS_DIR, get_ocr_predicted_groups_filename
from utils.gemini_ai_for_grouping import get_cleaned_text

APP_LOGGING_NAME = "gemg"


def get_ai_predicted_groups(
    svg_stem: str,
    ocr_type: str,
    prelim_dir: Path,
    _ocr_bound_ids: list[dict[str, Any]],
    _png_file: Path,
) -> Any:  # noqa: ANN401
    ai_predicted_groups_file = prelim_dir / get_ocr_predicted_groups_filename(
        svg_stem, ocr_type
    )

    logger.info(f'Reading gemini ai predicted groups from "{ai_predicted_groups_file}".')

    with ai_predicted_groups_file.open("r") as f:
        predicted_groups = f.read()

        predicted_groups, reason_changed = get_cleaned_text(predicted_groups)
        if reason_changed:
            logger.warning(f'Fixed json in "{ai_predicted_groups_file}": {reason_changed}.')

        return json.loads(predicted_groups)


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
    log_filename = "make-gemini-ai-groups-from-batch.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    assert (cmd_args.get_num_volumes() <= 1) or (len(cmd_args.get_titles()) <= 1)
    if cmd_args.one_or_more_volumes():
        volume = int(cmd_args.get_volume())
    else:
        assert len(cmd_args.get_titles()) == 1
        volume = comics_database.get_fanta_volume_int(cmd_args.get_title())

    volume_dirname = comics_database.get_fantagraphics_volume_title(volume)

    prelim_results_dir = BATCH_JOBS_OUTPUT_DIR / volume_dirname
    logger.info(
        f'Looking for preliminary predicted group data in directory "{prelim_results_dir}"...'
    )
    assert prelim_results_dir.is_dir()

    output_dir = OCR_RESULTS_DIR / volume_dirname
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f'Writing final ai group data to volume directory "{output_dir}"...')

    gemini_ai_grouper = GeminiAiGrouper(
        comics_database, prelim_results_dir, output_dir, get_ai_predicted_groups
    )
    gemini_ai_grouper.make_groups_for_titles(cmd_args.get_titles())

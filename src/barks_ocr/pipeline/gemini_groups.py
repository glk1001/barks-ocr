import json
from pathlib import Path
from typing import Any

import typer
from barks_fantagraphics.ocr_file_paths import get_ocr_predicted_groups_filename
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from loguru import logger

from barks_ocr.cli_setup import get_comic_titles, init_logging
from barks_ocr.pipeline.gemini_grouper import GeminiAiGrouper
from barks_ocr.utils.gemini_ai_for_grouping import get_cleaned_text

APP_LOGGING_NAME = "gemg"


def get_ai_predicted_groups(
    fanta_page: str,
    ocr_type: str,
    batch_results_dir: Path,
    _ocr_bound_ids: list[dict[str, Any]],
    _png_file: Path,
) -> Any:  # noqa: ANN401
    ai_predicted_groups_file = batch_results_dir / get_ocr_predicted_groups_filename(
        fanta_page, ocr_type
    )

    logger.info(f'Reading gemini ai predicted groups from "{ai_predicted_groups_file}".')

    with ai_predicted_groups_file.open("r") as f:
        predicted_groups = f.read()

        predicted_groups, reason_changed = get_cleaned_text(predicted_groups)
        if reason_changed:
            logger.warning(f'Fixed json in "{ai_predicted_groups_file}": {reason_changed}.')

        return json.loads(predicted_groups)


app = typer.Typer()


@app.command(help="Make gemini ai groups from batch job results")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    init_logging(APP_LOGGING_NAME, "make-gemini-ai-groups-from-batch.log", log_level_str)

    comics_database, titles = get_comic_titles(volumes_str, title_str)

    gemini_ai_grouper = GeminiAiGrouper(comics_database, get_ai_predicted_groups)
    gemini_ai_grouper.make_groups_for_titles(titles)


if __name__ == "__main__":
    app()

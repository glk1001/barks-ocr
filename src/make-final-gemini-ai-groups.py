import json
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.ocr_json_files import JsonFiles
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from intspan import intspan
from loguru import logger
from loguru_config import LoguruConfig

APP_LOGGING_NAME = "gemf"


def make_final_gemini_ai_groups_for_titles(
    comics_database: ComicsDatabase, titles: list[str]
) -> None:
    for title in titles:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        make_final_gemini_ai_groups_for_title(comics_database, title)


def make_final_gemini_ai_groups_for_title(comics_database: ComicsDatabase, title: str) -> None:
    json_files = JsonFiles(comics_database, title)
    json_files.title_final_results_dir.mkdir(parents=True, exist_ok=True)

    comic = comics_database.get_comic_book(title)
    ocr_files = comic.get_srce_restored_ocr_raw_story_files(RESTORABLE_PAGE_TYPES)

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


app = typer.Typer()
log_level = ""
log_filename = "make-final-gemini-ai-groups.log"


@app.command(help="Make final ai groups")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    # Global variable accessed by loguru-config.
    global log_level  # noqa: PLW0603
    log_level = log_level_str
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()

    make_final_gemini_ai_groups_for_titles(
        comics_database, get_titles(comics_database, volumes, title_str)
    )


if __name__ == "__main__":
    app()

# ruff: noqa: T201

import subprocess
from pathlib import Path

import typer
from barks_fantagraphics.comic_book import get_page_str
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.ocr_file_paths import (
    OCR_PRELIM_DIR,
    get_ocr_prelim_groups_json_filename,
)
from comic_utils.common_typer_options import LogLevelArg, PagesArg, VolumesArg
from intspan import intspan
from loguru import logger
import barks_ocr.log_setup as _log_setup
from loguru_config import LoguruConfig

_RESOURCES = Path(__file__).parent.parent / "resources"

APP_LOGGING_NAME = "opno"

EDITOR_EXE = ["vscodium"]
# TODO: duplicated in show-title-images
VIEWER_EXE = ["/usr/bin/eog"]


def open_viewer(image_file: Path) -> None:
    command = [*VIEWER_EXE, str(image_file)]

    _proc = subprocess.Popen(command)  # noqa: S603

    logger.debug(f'Image Viewer should now be showing image "{image_file}".')


def edit_file(file: Path, line: int) -> None:
    file_arg = f"{file}:{line}" if line > 0 else file
    command = [*EDITOR_EXE, "--goto", f"{file_arg}"]
    logger.debug(f"Running command: {command}.")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)  # noqa: S603
    _output = process.stdout.readline()  # ty:ignore[unresolved-attribute]

    logger.debug(f'Editor should now have opened "{file}" at line {line}.')


def open_prelim_files(comics_database: ComicsDatabase, volume: int, page: str) -> None:
    volume_dirname = comics_database.get_fantagraphics_volume_title(volume)

    prelim_dir = OCR_PRELIM_DIR / volume_dirname

    easy_ocr = prelim_dir / get_ocr_prelim_groups_json_filename(page, "easyocr")
    paddle_ocr = prelim_dir / get_ocr_prelim_groups_json_filename(page, "paddleocr")

    print(easy_ocr)
    assert easy_ocr.is_file()
    assert paddle_ocr.is_file()

    edit_file(easy_ocr, 1)
    edit_file(paddle_ocr, 1)


app = typer.Typer()


@app.command(help="Make final ai groups")
def main(
    volumes_str: VolumesArg = "",
    pages: PagesArg = "",
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    _log_setup.log_level = log_level_str
    _log_setup.log_filename = "open-prelim-ocr.log"
    _log_setup.APP_LOGGING_NAME = APP_LOGGING_NAME
    LoguruConfig.load(_RESOURCES / "log-config.yaml")

    volumes = list(intspan(volumes_str))
    assert len(volumes) == 1
    comics_database = ComicsDatabase()

    vol = volumes[0]
    pg = get_page_str(int(pages))

    open_prelim_files(comics_database, vol, pg)


if __name__ == "__main__":
    app()

import subprocess
import sys
from pathlib import Path

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from barks_fantagraphics.ocr_file_paths import (
    OCR_PRELIM_DIR,
    get_ocr_prelim_groups_json_filename,
)
from loguru import logger
from loguru_config import LoguruConfig

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
    _output = process.stdout.readline()  # ty:ignore[possibly-missing-attribute]

    logger.debug(f'Editor should now have opened "{file}" at line {line}.')


def open_prelim_files(volume: int, page: str) -> None:
    volume_dirname = comics_database.get_fantagraphics_volume_title(volume)

    prelim_dir = OCR_PRELIM_DIR / volume_dirname

    easy_ocr = prelim_dir / get_ocr_prelim_groups_json_filename(page, "easyocr")
    paddle_ocr = prelim_dir / get_ocr_prelim_groups_json_filename(page, "paddleocr")

    print(easy_ocr)
    assert easy_ocr.is_file()
    assert paddle_ocr.is_file()

    edit_file(easy_ocr, 1)
    edit_file(paddle_ocr, 1)


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs("Edit page and group for title", CmdArgNames.VOLUME | CmdArgNames.PAGE)
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = Path(__file__).stem + ".log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    vol = cmd_args.get_volume()
    pg = f"{cmd_args.get_pages()[0]:03d}"

    open_prelim_files(vol, pg)

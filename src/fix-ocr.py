import json
import subprocess
import sys
from pathlib import Path

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from loguru import logger
from loguru_config import LoguruConfig

from ocr_file_paths import (
    OCR_FIXES_DIR,
)

APP_LOGGING_NAME = "chkr"


# TODO: duplicated in show-title-images
VIEWER_EXE = ["/usr/bin/eog"]


def open_viewer(image_file: Path) -> None:
    command = [*VIEWER_EXE, str(image_file)]

    _proc = subprocess.Popen(command)  # noqa: S603

    print(f'Image Viewer should now be showing image "{image_file}".')


def edit_title_for_fixing(title: str, page: str, group_id: str) -> None:
    fixes_file = OCR_FIXES_DIR / (title + ".json")
    logger.info(f'Loading fix info from "{fixes_file}".')

    fix_objects = json.loads(fixes_file.read_text())

    file1_image = fix_objects[page][group_id]["image_file"]
    other_group_id = fix_objects[page][group_id]["other_group_id"]

    file1_to_edit = fix_objects[page][group_id]["file1"]
    file2_to_edit = fix_objects[page][group_id]["file2"]
    line1 = fix_objects[page][group_id]["line1"]
    line2 = fix_objects[page][group_id]["line2"]

    logger.info(f'Setting up fix command. Group {group_id} in "{file1_to_edit}", line {line1}.')
    logger.info(
        f'Setting up fix command. Group {other_group_id} in "{file2_to_edit}", line {line2}.'
    )
    logger.info(f'Setting up fix command. Image to view: "{file1_image}".')


if __name__ == "__main__":
    # extra_args: list[ExtraArg] = [
    #     ExtraArg("--page", action="store", type=str, default=""),
    #     ExtraArg("--group", action="store", type=str, default=""),
    # ]

    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs("Edit page and group for title", CmdArgNames.TITLE)
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = "make-gemini-ai-groups-batch-job.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    # (cmd_args.get_extra_arg("--page"),)
    # (int(cmd_args.get_extra_arg("--group")),)
    pg= "132"
    grp = "8"
    edit_title_for_fixing(
        cmd_args.get_title(), pg, grp
    )

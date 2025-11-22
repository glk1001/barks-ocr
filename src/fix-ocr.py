import json
import shutil
import subprocess
import sys
from pathlib import Path

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from barks_fantagraphics.comics_utils import get_timestamp_str
from loguru import logger
from loguru_config import LoguruConfig

from ocr_file_paths import (
    OCR_FIXES_BACKUP_DIR,
    OCR_FIXES_DIR,
)

APP_LOGGING_NAME = "chkr"


EDITOR_EXE = ["codium"]
# TODO: duplicated in show-title-images
VIEWER_EXE = ["/usr/bin/eog"]


def open_viewer(image_file: Path) -> None:
    command = [*VIEWER_EXE, str(image_file)]

    _proc = subprocess.Popen(command)  # noqa: S603

    logger.debug(f'Image Viewer should now be showing image "{image_file}".')


def edit_file(file: Path, line: int) -> None:
    command = [*EDITOR_EXE, "--goto", f"{file}:{line}"]

    _proc = subprocess.Popen(command)  # noqa: S603

    logger.debug(f'Editor should now have opened "{file}".')


def edit_title_for_fixing(title: str, page: str, group_id: str) -> None:
    fixes_file = OCR_FIXES_DIR / (title + ".json")
    logger.info(f'Loading fix info from "{fixes_file}".')

    fix_objects = json.loads(fixes_file.read_text())

    file1_image = Path(fix_objects[page][group_id]["image_file"])
    other_group_id = fix_objects[page][group_id]["other_group_id"]

    file1_to_edit = Path(fix_objects[page][group_id]["file1"])
    file2_to_edit = Path(fix_objects[page][group_id]["file2"])
    line1 = fix_objects[page][group_id]["line1"]
    line2 = fix_objects[page][group_id]["line2"]

    volume_dirname = comics_database.get_fantagraphics_volume_title(
        comics_database.get_fanta_volume_int(title)
    )
    ocr_backup_dir_for_title = OCR_FIXES_BACKUP_DIR / volume_dirname
    ocr_backup_dir_for_title.mkdir(parents=True, exist_ok=True)
    file1_backup = ocr_backup_dir_for_title / (
        file1_to_edit.name + "_" + get_timestamp_str(file1_to_edit)
    )
    file2_backup = ocr_backup_dir_for_title / (
        file2_to_edit.name + "_" + get_timestamp_str(file2_to_edit)
    )

    logger.info(f'Setting up fix command. Group {group_id} in "{file1_to_edit}", line {line1}.')
    logger.info(f'Copying file1 to "{file1_backup}".')
    logger.info(
        f'Setting up fix command. Group {other_group_id} in "{file2_to_edit}", line {line2}.'
    )
    logger.info(f'Copying file2 to "{file2_backup}".')
    logger.info(f'Setting up fix command. Image to view: "{file1_image}".')

    shutil.copy(file1_to_edit, file1_backup)
    shutil.copy(file2_to_edit, file2_backup)

    open_viewer(file1_image)
    edit_file(file1_to_edit, line1)
    edit_file(file2_to_edit, line2)


if __name__ == "__main__":
    extra_args: list[ExtraArg] = [
        ExtraArg("--group", action="store", type=str, default=""),
    ]

    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Edit page and group for title", CmdArgNames.TITLE | CmdArgNames.PAGE, extra_args
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

    pg = str(cmd_args.get_pages()[0])
    grp = cmd_args.get_extra_arg("--group")
    edit_title_for_fixing(cmd_args.get_title(), pg, grp)

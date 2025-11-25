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
    file_arg = f"{file}:{line}" if line > 0 else file
    command = [*EDITOR_EXE, "--goto", f"{file}:{line}"]
    logger.debug(f"Running command: {command}.")

    _proc = subprocess.Popen(command, shell=False)  # noqa: S603

    logger.debug(f'Editor should now have opened "{file}" at line {line}.')


def just_show(title: str, page: str, group_id: str) -> None:
    fixes_file = OCR_FIXES_DIR / (title + ".json")
    fix_objects = json.loads(fixes_file.read_text())
    file1_image = Path(fix_objects[page][group_id]["image_file"])
    open_viewer(file1_image)


def replace_left_text(title: str, page: str, group_id: str, rep_text: list[str]) -> None:
    replace_text(title, page, group_id, "file1", use_other_group=False, rep_text=rep_text)


def replace_right_text(title: str, page: str, group_id: str, rep_text: list[str]) -> None:
    replace_text(title, page, group_id, "file2", use_other_group=True, rep_text=rep_text)


def replace_text(
    title: str, page: str, group_id: str, file_key: str, use_other_group: bool, rep_text: list[str]
) -> None:
    assert len(rep_text) == 2  # noqa: PLR2004

    fixes_file = OCR_FIXES_DIR / (title + ".json")
    logger.info(f'Loading fix info from "{fixes_file}".')

    fix_objects = json.loads(fixes_file.read_text())

    group_id_to_use = (
        group_id if not use_other_group else fix_objects[page][group_id]["other_group_id"]
    )

    file_to_edit = Path(fix_objects[page][group_id][file_key])

    logger.info(f"Replacing text for page {page}, group {group_id_to_use}: {rep_text}.")

    backup_file(title, file_to_edit)

    file_objects = json.loads(file_to_edit.read_text())
    text_to_replace = file_objects[int(group_id_to_use)]["cleaned_text"]
    replaced_text = text_to_replace.replace(rep_text[0], rep_text[1])
    file_objects[int(group_id_to_use)]["cleaned_text"] = replaced_text
    logger.info(f"Replaced\n\n{text_to_replace}\n\nwith\n\n{replaced_text}\n\n")
    with file_to_edit.open(mode="w", encoding="utf-8") as f:
        json.dump(file_objects, f, ensure_ascii=False, indent=4)


def backup_file(title: str, file: Path) -> None:
    volume_dirname = comics_database.get_fantagraphics_volume_title(
        comics_database.get_fanta_volume_int(title)
    )
    ocr_backup_dir_for_title = OCR_FIXES_BACKUP_DIR / volume_dirname
    ocr_backup_dir_for_title.mkdir(parents=True, exist_ok=True)
    file_backup = ocr_backup_dir_for_title / (file.name + "_" + get_timestamp_str(file))
    logger.info(f'Backing up file "{file}" to "{file_backup}".')
    shutil.copy(file, file_backup)


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

    backup_file(title, file1_to_edit)
    backup_file(title, file2_to_edit)

    logger.info(f'Setting up fix command. Group {group_id} in "{file1_to_edit}", line {line1}.')
    logger.info(
        f'Setting up fix command. Group {other_group_id} in "{file2_to_edit}", line {line2}.'
    )
    logger.info(f'Setting up fix command. Image to view: "{file1_image}".')

    open_viewer(file1_image)
    edit_file(file1_to_edit, line1)
    edit_file(file2_to_edit, line2)


if __name__ == "__main__":
    extra_args: list[ExtraArg] = [
        ExtraArg("--group", action="store", type=str, default=""),
        ExtraArg("--rep-left", action="store", type=str, default="", nargs="+"),
        ExtraArg("--rep-right", action="store", type=str, default="", nargs="+"),
        ExtraArg("--show", action="store_true", type=None, default=None),
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
    show = cmd_args.get_extra_arg("--show")
    rep_left = cmd_args.get_extra_arg("--rep_left")
    rep_right = cmd_args.get_extra_arg("--rep_right")

    if rep_left:
        replace_left_text(cmd_args.get_title(), pg, grp, rep_left)
    elif rep_right:
        replace_right_text(cmd_args.get_title(), pg, grp, rep_right)
    elif show:
        just_show(cmd_args.get_title(), pg, grp)
    else:
        edit_title_for_fixing(cmd_args.get_title(), pg, grp)

import json
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_utils import get_timestamp_str
from barks_fantagraphics.ocr_file_paths import OCR_FIXES_BACKUP_DIR, OCR_FIXES_DIR
from comic_utils.common_typer_options import LogLevelArg, PagesArg, TitleArg
from loguru import logger
from loguru_config import LoguruConfig

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
    command = [*EDITOR_EXE, "--goto", f"{file_arg}"]
    logger.debug(f"Running command: {command}.")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)  # noqa: S603
    _output = process.stdout.readline()

    logger.debug(f'Editor should now have opened "{file}" at line {line}.')


def just_show(title: str, ocr_index: int, page: str) -> None:
    fixes_file = OCR_FIXES_DIR / (title + ".json")
    fix_objects = json.loads(fixes_file.read_text())
    file1_image = Path(fix_objects[str(ocr_index)]["errors"][page]["image1"])
    open_viewer(file1_image)


def replace_left_text(
    comics_database: ComicsDatabase, title: str, page: str, group_id: str, rep_text: list[str]
) -> None:
    replace_text(comics_database, title, 0, page, group_id, rep_text=rep_text)


def replace_right_text(
    comics_database: ComicsDatabase, title: str, page: str, group_id: str, rep_text: list[str]
) -> None:
    replace_text(comics_database, title, 1, page, group_id, rep_text=rep_text)


def replace_text(
    comics_database: ComicsDatabase,
    title: str,
    ocr_index: int,
    page: str,
    group_id: str,
    rep_text: list[str],
) -> None:
    assert len(rep_text) == 2  # noqa: PLR2004

    ocr_index = str(ocr_index)

    fixes_file = OCR_FIXES_DIR / (title + ".json")
    logger.info(f'Loading fix info from "{fixes_file}".')

    fix_objects = json.loads(fixes_file.read_text())

    file_to_edit = Path(fix_objects[ocr_index]["errors"][page]["file1"])

    logger.info(f"Replacing text for ocr {ocr_index}, page {page}, group {group_id}: {rep_text}.")

    backup_file(comics_database, title, file_to_edit)

    file_objects = json.loads(file_to_edit.read_text())
    text_to_replace = file_objects[int(group_id)]["cleaned_text"]
    replaced_text = text_to_replace.replace(rep_text[0], rep_text[1])
    file_objects[int(group_id)]["cleaned_text"] = replaced_text
    logger.info(f"Replaced\n\n{text_to_replace}\n\nwith\n\n{replaced_text}\n\n")
    with file_to_edit.open(mode="w", encoding="utf-8") as f:
        json.dump(file_objects, f, ensure_ascii=False, indent=4)


def backup_file(comics_database: ComicsDatabase, title: str, file: Path) -> None:
    volume_dirname = comics_database.get_fantagraphics_volume_title(
        comics_database.get_fanta_volume_int(title)
    )
    ocr_backup_dir_for_title = OCR_FIXES_BACKUP_DIR / volume_dirname
    ocr_backup_dir_for_title.mkdir(parents=True, exist_ok=True)
    file_backup = ocr_backup_dir_for_title / (file.name + "_" + get_timestamp_str(file))
    logger.info(f'Backing up file "{file}" to "{file_backup}".')
    shutil.copy(file, file_backup)


def edit_title_for_fixing(
    comics_database: ComicsDatabase, title: str, ocr_index: int, page: str, group_id: str
) -> None:
    ocr_index = str(ocr_index)

    fixes_file = OCR_FIXES_DIR / (title + ".json")
    logger.info(f'Loading fix info from "{fixes_file}".')

    fix_objects = json.loads(fixes_file.read_text())

    file1_image = Path(fix_objects[ocr_index]["errors"][page]["image1"])
    other_group_id = fix_objects[ocr_index]["errors"][page][group_id]["other_group_id"]

    file1_to_edit = Path(fix_objects[ocr_index]["errors"][page]["file1"])
    file2_to_edit = Path(fix_objects[ocr_index]["errors"][page]["file2"])
    line1 = fix_objects[ocr_index]["errors"][page][group_id]["line1"]
    line2 = fix_objects[ocr_index]["errors"][page][group_id]["line2"]

    backup_file(comics_database, title, file1_to_edit)
    backup_file(comics_database, title, file2_to_edit)

    logger.info(f'Setting up fix command. Group {group_id} in "{file1_to_edit}", line {line1}.')
    logger.info(
        f'Setting up fix command. Group {other_group_id} in "{file2_to_edit}", line {line2}.'
    )
    logger.info(f'Setting up fix command. Image to view: "{file1_image}".')

    open_viewer(file1_image)
    edit_file(file1_to_edit, line1)
    edit_file(file2_to_edit, line2)


app = typer.Typer()
log_level = ""
log_filename = "fix-ocr.log"


@app.command(help="Run easyocr and paddleocr on restored titles")
def main(
    title_str: TitleArg = "",
    page: PagesArg = "",
    group: str = "",
    rep_left: list[str] | None = None,
    rep_right: list[str] | None = None,
    show_left: bool = False,
    show_right: bool = False,
    edit_left: bool = False,
    edit_right: bool = False,
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    # Global variable accessed by loguru-config.
    global log_level  # noqa: PLW0603
    log_level = log_level_str
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = ComicsDatabase()

    pg = str(page[0])

    if rep_left is None:
        rep_left = []
    if rep_right is None:
        rep_right = []

    if rep_left:
        replace_left_text(comics_database, title_str, pg, group, rep_left)
    elif rep_right:
        replace_right_text(comics_database, title_str, pg, group, rep_right)
    elif show_left:
        just_show(title_str, 0, pg)
    elif show_right:
        just_show(title_str, 1, pg)
    elif edit_left:
        edit_title_for_fixing(comics_database, title_str, 0, pg, group)
    elif edit_right:
        edit_title_for_fixing(comics_database, title_str, 1, pg, group)
    else:
        logger.error("No arguments given.")
        sys.exit(1)


if __name__ == "__main__":
    app()

import json
import re
import sys
from pathlib import Path

from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs, ExtraArg
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_ocr_type
from loguru import logger
from loguru_config import LoguruConfig
from thefuzz import fuzz, process

from ocr_file_paths import (
    BATCH_JOBS_OUTPUT_DIR,
    OCR_ANNOTATIONS_DIR,
    OCR_FIXES_DIR,
    OCR_PRELIM_DIR,
    get_ocr_boxes_annotated_filename,
    get_ocr_predicted_groups_filename,
    get_ocr_prelim_groups_json_filename,
    get_ocr_prelim_text_annotated_filename,
)

APP_LOGGING_NAME = "chkr"

BAD_PATTERNS = [
    r"--",
    r" +\-[^ \n!]",
    r"[^ ]\- +",
    r" +—[^ \n!]",
    r"[^ ]— +",
]


class JsonFiles:
    def __init__(
        self,
        title: str,
    ) -> None:
        self.title = title
        self.volume_dirname = comics_database.get_fantagraphics_volume_title(
            comics_database.get_fanta_volume_int(title)
        )
        self.title_prelim_results_dir = OCR_PRELIM_DIR / self.volume_dirname
        self.title_annotated_images_dir = OCR_ANNOTATIONS_DIR / self.volume_dirname

        self.page: str = ""
        self.ocr_file: tuple[Path, Path] | None = None
        self.ocr_type: list[str] = []
        self.ocr_prelim_groups_json_file: list[Path] = []
        self.ocr_prelim_groups_annotated_file: list[Path] = []
        self.ocr_predicted_groups_file: list[Path] = []
        self.ocr_boxes_annotated_file: list[Path] = []

    def set_ocr_file(self, ocr_file: tuple[Path, Path]) -> None:
        self.page = ocr_file[0].stem[:3]
        self.ocr_file = ocr_file

        self.ocr_type = []
        self.ocr_prelim_groups_json_file = []
        self.ocr_prelim_groups_annotated_file = []
        self.ocr_predicted_groups_file = []
        self.ocr_boxes_annotated_file = []

        for ocr_type_file in ocr_file:
            ocr_type = get_ocr_type(ocr_type_file)
            self.ocr_type.append(ocr_type)

            self.ocr_prelim_groups_json_file.append(
                self.title_prelim_results_dir
                / get_ocr_prelim_groups_json_filename(self.page, ocr_type)
            )
            self.ocr_prelim_groups_annotated_file.append(
                self.title_annotated_images_dir
                / get_ocr_prelim_text_annotated_filename(self.page, ocr_type)
            )
            self.ocr_predicted_groups_file.append(
                BATCH_JOBS_OUTPUT_DIR
                / self.volume_dirname
                / get_ocr_predicted_groups_filename(self.page, ocr_type)
            )
            self.ocr_boxes_annotated_file.append(
                OCR_ANNOTATIONS_DIR
                / self.volume_dirname
                / get_ocr_boxes_annotated_filename(self.page, ocr_type)
            )


def check_gemini_ai_groups_for_titles(
    titles: list[str], compare_text: bool, show_close: bool
) -> None:
    total_errors = 0

    for title in titles:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        total_errors += check_gemini_ai_groups_for_title(title, compare_text, show_close)

    if total_errors == 0:
        logger.success("All comic titles checked - no errors found.")
    else:
        logger.error(f"There were {total_errors} errors found.")


def check_gemini_ai_groups_for_title(title: str, compare_text: bool, show_close: bool) -> int:
    json_files = JsonFiles(title)

    logger.info(
        f'Checking processed OCR groups for all pages in "{title}".'
        f' Looking in directory "{json_files.title_prelim_results_dir}"...'
    )

    comic = comics_database.get_comic_book(title)
    ocr_files = comic.get_srce_restored_raw_ocr_story_files(RESTORABLE_PAGE_TYPES)

    fix_objects = {
        0: {
            "bad-pats": {},
            "errors": {},
        },
        1: {
            "bad-pats": {},
            "errors": {},
        },
    }

    num_errors = 0
    for ocr_file in ocr_files:
        json_files.set_ocr_file(ocr_file)

        missing_ocr_file = False
        for index in range(len(ocr_file)):
            if not json_files.ocr_prelim_groups_json_file[index].is_file():
                logger.error(
                    f"Missing prelim groups json file:"
                    f' "{json_files.ocr_prelim_groups_json_file[index]}".'
                )
                num_errors += 1
                missing_ocr_file = True
            elif not json_files.ocr_prelim_groups_annotated_file[index].is_file():
                logger.error(
                    f"Missing prelim groups annotated file:"
                    f' "{json_files.ocr_prelim_groups_annotated_file[index]}".'
                )
                num_errors += 1

        if not missing_ocr_file:
            fix_objs = check_ocr_for_bad_patterns(json_files)
            if fix_objs:
                for index, fix_obj in enumerate(fix_objs):
                    if not fix_obj:
                        continue
                    fix_objects[index]["bad-pats"][json_files.page] = fix_obj

        if compare_text and not missing_ocr_file:
            fix_objs = compare_ocr_ai_texts(json_files, show_close)
            for index, fix_obj in enumerate(fix_objs):
                if not fix_obj:
                    continue
                fix_objects[index]["errors"][json_files.page] = fix_obj

    if num_errors > 0:
        logger.error(f'There were {num_errors} errors for title "{title}".')

    if fix_objects:
        OCR_FIXES_DIR.mkdir(parents=True, exist_ok=True)
        fixes_file = OCR_FIXES_DIR / (title + ".json")
        with fixes_file.open("w") as f:
            json.dump(fix_objects, f, indent=4)

        logger.info(f'Fixes file saved to "{fixes_file}".')

    return num_errors


def check_ocr_for_bad_patterns(json_files: JsonFiles) -> tuple[dict, dict]:
    return check_for_bad_patterns(json_files, 0, 1), check_for_bad_patterns(json_files, 1, 0)


def check_for_bad_patterns(json_files: JsonFiles, index1: int, index2: int) -> dict:
    ocr_prelim_groups_json_file1 = json_files.ocr_prelim_groups_json_file[index1]
    ocr_group_data1 = json.loads(ocr_prelim_groups_json_file1.read_text())

    fix_objects1 = {}
    for group_id, group in ocr_group_data1.items():
        ai_text = group["ai_text"]
        for pat in BAD_PATTERNS:
            if re.search(pat, ai_text):
                logger.error(
                    f"Page {json_files.page}, group: {group_id};"
                    f' bad pattern "{pat}" found in "{ai_text}".'
                )

                logger.debug(f"Appending fixes info for group {group_id}")
                fix_objects1[int(group_id)] = get_fix_command(
                    json_files,
                    index1,
                    index2,
                    int(group_id),
                    -1,
                    ai_text,
                    "",
                )

    return fix_objects1


def compare_ocr_ai_texts(
    json_files: JsonFiles,
    show_close: bool,
) -> tuple[dict, dict]:
    fix_objects1 = compare_ai_texts(json_files, 0, 1, show_close)
    fix_objects2 = compare_ai_texts(json_files, 1, 0, show_close)

    return fix_objects1, fix_objects2


def compare_ai_texts(
    json_files: JsonFiles,
    index1: int,
    index2: int,
    show_close: bool,
) -> dict:
    ocr_group_data1 = json.loads(json_files.ocr_prelim_groups_json_file[index1].read_text())
    ocr_group_data2 = json.loads(json_files.ocr_prelim_groups_json_file[index2].read_text())

    ocr_group_2_ai_texts = [group["ai_text"] for group in ocr_group_data2.values()]

    logger.info(f'Checking ai_text in "{json_files.ocr_prelim_groups_json_file[index1]}"...')

    fix_objects = {
        "file1": str(json_files.ocr_predicted_groups_file[index1]),
        "file2": str(json_files.ocr_predicted_groups_file[index2]),
        "image1": str(json_files.ocr_boxes_annotated_file[index1]),
    }
    zero_groups_len = len(fix_objects)

    for group_id, group in ocr_group_data1.items():
        ai_text = group["ai_text"]
        if ai_text in ocr_group_2_ai_texts:
            continue

        close = False
        other_group_id = -1
        other_ai_text = ""
        required_score = 95
        best_score = 0
        closest_group = -1
        closest_ai_text = ""
        for index, ai_text2 in enumerate(ocr_group_2_ai_texts):
            score = fuzz.partial_ratio(ai_text, ai_text2)
            if score > best_score:
                best_score = score
                closest_group = index
                closest_ai_text = ai_text2

        if best_score > required_score:
            other_group_id = closest_group
            other_ai_text = closest_ai_text
            if show_close:
                logger.warning(
                    f'Group {group_id}: Could not find this ai_text in other:\n\n"{ai_text}"'
                    f"\n\nBUT from OTHER group {other_group_id},"
                    f'\n\n"{other_ai_text}"\n\nis close'
                    f" (partial ratio > {required_score})."
                )
            close = True

        if not close:
            best_score = 0
            closest_group = -1
            closest_ai_text = ""
            required_score = 80
            other_ai_texts = {str(index): text for index, text in enumerate(ocr_group_2_ai_texts)}
            similarity_scores = process.extract(ai_text, other_ai_texts, scorer=fuzz.ratio)
            for value, score, other_group_id in similarity_scores:
                if score > best_score:
                    best_score = score
                    closest_group = other_group_id
                    closest_ai_text = value

            if best_score > required_score:
                other_group_id = closest_group
                other_ai_text = closest_ai_text
                if show_close:
                    logger.warning(
                        f"Group {group_id}: Could not find this ai_text in other:"
                        f'\n\n"{ai_text}"'
                        f"\n\nBUT from OTHER group {other_group_id}"
                        f'\n\n"{other_ai_text}"\n\nis close'
                        f" (similarity > {required_score})."
                    )
                close = True

        if not close:
            logger.error(f'Group {group_id}: Could not find ai_text:\n\n"{ai_text}"\n\nin other.')

        logger.debug(f"Appending fixes info for group {group_id}")
        fix_objects[int(group_id)] = get_fix_command(
            json_files,
            index1,
            index2,
            int(group_id),
            int(other_group_id),
            ai_text,
            other_ai_text,
        )

    return fix_objects if len(fix_objects) > zero_groups_len else {}


def get_fix_command(
    json_files: JsonFiles,
    index1: int,
    index2: int,
    group_id: int,
    other_group_id: int,
    ai_text: str,
    other_ai_text: str,
) -> dict:
    file1_to_edit = json_files.ocr_predicted_groups_file[index1]
    file2_to_edit = json_files.ocr_predicted_groups_file[index2]

    target_key = "cleaned_text"
    file1_line = -1
    file2_line = -1
    if (group_id != -1) and file1_to_edit.is_file():
        file1_line = find_line_number_in_json_string(file1_to_edit, group_id + 1, target_key)
    if (other_group_id != -1) and file2_to_edit.is_file():
        file2_line = find_line_number_in_json_string(file2_to_edit, other_group_id + 1, target_key)

    logger.info(
        f"Setting up fix command for {json_files.ocr_type[index1]}:"
        f" page {json_files.page}, group {group_id}, line {file1_line}."
    )
    logger.info(
        f"Setting up fix command for {json_files.ocr_type[index2]}:"
        f" page {json_files.page}, group {other_group_id}, line {file2_line}."
    )

    return {
        "group_id": group_id,
        "other_group_id": other_group_id,
        "line1": file1_line,
        "line2": file2_line,
        "cleaned_text1": ai_text,
        "cleaned_text2": other_ai_text,
    }


def find_line_number_in_json_string(json_file: Path, n: int, target_key: str) -> int:
    # Find the line number of the nth target_key.
    assert target_key
    assert n > 0

    lines = json_file.read_text().splitlines()

    count = 0
    for i, line in enumerate(lines):
        line_number = i + 1  # 1-based line number

        if f'"{target_key}":' in line:
            count += 1
            if count == n:
                return line_number

    return -1


if __name__ == "__main__":
    extra_args: list[ExtraArg] = [
        ExtraArg("--compare-text", action="store_true", type=None, default=None),
        ExtraArg("--show-close", action="store_true", type=None, default=None),
    ]

    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make Gemini AI OCR groups for title", CmdArgNames.VOLUME | CmdArgNames.TITLE, extra_args
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

    check_gemini_ai_groups_for_titles(
        cmd_args.get_titles(),
        compare_text=cmd_args.get_extra_arg("--compare_text"),
        show_close=cmd_args.get_extra_arg("--show_close"),
    )

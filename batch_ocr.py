import json
import logging
import os.path
import sys
import time
from pathlib import Path
from typing import Tuple, List

import autocorrect
import cv2 as cv
import easyocr
import enchant
import numpy as np

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_relpath


def setup_logging(log_level) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


REJECTED_WORDS = ["F", "H", "M", "W", "OO", "VV", "|", "L", "\\", "IY"]
AUTO_CORRECTIONS = {
    "AOINT MARROW": "POINT MARROW",
    "FIZZLEBUDEET": "FIZZLEBUDGET",
    "G0": "GO",
}

spell_dict = enchant.DictWithPWL("en_US", "mywords.txt")
spell_correct = autocorrect.Speller()


def words_are_ok(words_str: str) -> Tuple[bool, List[str]]:
    words_str = words_str.strip(" ")

    auto_ok, corrected_words_str = can_auto_correct(words_str)
    if auto_ok:
        return True, [corrected_words_str]

    words = words_str.split(" ")

    accepted_words = []
    for word in words:
        word_ok, accepted_word = word_is_ok(word)
        if not word_ok:
            return False, []
        accepted_words.append(accepted_word)

    return True, accepted_words


def can_auto_correct(words_str: str) -> Tuple[bool, str]:
    if words_str in AUTO_CORRECTIONS:
        return True, AUTO_CORRECTIONS[words_str]

    if words_str[-1] in ").!;?,":
        if words_str[:-1] in AUTO_CORRECTIONS:
            return True, AUTO_CORRECTIONS[words_str[:-1]] + words_str[-1]

    return False, ""


def word_is_ok(word: str) -> Tuple[bool, str]:
    word = word.upper().strip()

    if not word:
        return False, ""

    if word in REJECTED_WORDS:
        return False, ""

    if spell_dict.check(word):
        return True, word

    if word[-1] in ").!;?,":
        if spell_dict.check(word[:-1]):
            return True, word

    possible_words = spell_dict.suggest(word)
    possible_words = [f'"{word}"' for word in possible_words]
    # print(f"  possible_words = {possible_words}.")
    if possible_words:
        return True, possible_words[0]

    word = spell_correct.autocorrect_word(word)
    print(f"AUTO corrected word: '{word}'")
    if not spell_dict.check(word):
        return False, ""
    return True, word


def get_easyocr_text_box_data(image_file: str) -> List[Tuple[List[int], str, str, float]]:
    reader = easyocr.Reader(["en"])
    result = reader.readtext(image_file)

    text_list = []
    for bbox, text, prob in result:
        (tl, tr, br, bl) = bbox

        text_str = text.strip()
        if prob < 0.1 or not text_str:
            continue

        words_ok, accepted_words = words_are_ok(text_str)
        if not words_ok:
            continue
        accepted_words_str = " ".join(accepted_words)

        x0 = int(round(tl[0]))
        y0 = int(round(tl[1]))
        x1 = int(round(tr[0]))
        y1 = int(round(tr[1]))
        x2 = int(round(br[0]))
        y2 = int(round(br[1]))
        x3 = int(round(bl[0]))
        y3 = int(round(bl[1]))
        bbox = [x0, y0, x1, y1, x2, y2, x3, y3]

        text_list.append((bbox, text_str, accepted_words_str, prob))

    return text_list


def get_box_str(box: List[int]) -> str:
    assert len(box) == 8
    return (
        f"{box[0]:04},{box[1]:04}, {box[2]:04},{box[3]:04}, "
        f"{box[4]:04},{box[5]:04}, {box[6]:04},{box[7]:04}"
    )


def get_bw_image(file: str) -> cv.typing.MatLike:
    black_mask = cv.imread(file, -1)

    scale = 4
    black_mask = cv.resize(
        black_mask, (0, 0), fx=1.0 / scale, fy=1.0 / scale, interpolation=cv.INTER_AREA
    )

    _, _, _, binary = cv.split(black_mask)
    binary = np.uint8(255 - binary)

    return binary


def ocr_titles(title_list: List[str]) -> None:
    start = time.time()

    num_png_files = 0
    for title in title_list:
        logging.info(f'OCRing all pages in "{title}"...')

        comic = comics_database.get_comic_book(title)

        srce_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
        dest_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)

        for srce_file, dest_file in zip(srce_files, dest_files):
            if not ocr_comic_page(srce_file, dest_file):
                # raise Exception("There were process errors.")
                pass

        num_png_files += len(srce_files)

    logging.info(f"\nTime taken to OCR all {num_png_files} files: {int(time.time() - start)}s.")


def ocr_comic_page(svg_file: str, ocr_json_file: str) -> bool:
    png_file = svg_file + ".png"
    logging.info(f'OCRing png file "{get_relpath(png_file)}" to "{get_relpath(ocr_json_file)}"...')

    if not os.path.isfile(png_file):
        logging.error(f'Could not find png file "{png_file}".')
        return False

    if os.path.isfile(ocr_json_file):
        logging.info(f'OCR file "{get_relpath(png_file)}" exists - skipping..')
        return True

    bw_image = get_bw_image(png_file)
    # TODO: need work_dir
    grey_image_file = os.path.join("/tmp", Path(png_file).stem + "-grey.png")
    cv.imwrite(grey_image_file, bw_image)

    text_data_boxes = get_easyocr_text_box_data(grey_image_file)

    with open(os.path.join(ocr_json_file), "w") as f:
        json.dump(text_data_boxes, f, indent=4)

    return True


if __name__ == "__main__":

    setup_logging(logging.INFO)

    cmd_args = CmdArgs("Ocr titles", CmdArgNames.TITLE | CmdArgNames.VOLUME)
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logging.error(error_msg)
        sys.exit(1)

    comics_database = cmd_args.get_comics_database()

    ocr_titles(cmd_args.get_titles())
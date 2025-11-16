import json
import logging
import os.path
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Tuple

import cv2 as cv
import easyocr
import enchant
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_abbrev_path, get_ocr_no_json_suffix
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from loguru import logger
from loguru_config import LoguruConfig

from utils.common import ProcessResult
from utils.preprocessing import preprocess_image

APP_LOGGING_NAME = "bocr"

REJECTED_WORDS = ["F", "H", "M", "W", "OO", "VV", "|", "L", "\\", "IY"]
# noinspection SpellCheckingInspection
AUTO_CORRECTIONS = {
    "AOINT MARROW": "POINT MARROW",
    "FIZZLEBUDEET": "FIZZLEBUDGET",
    "G0": "GO",
}

BARKS_OCR_SPELL_DICT = Path(__file__).parent.parent / "barks_words.txt"
if not os.path.isfile(BARKS_OCR_SPELL_DICT):
    raise Exception(f'Could not find Barks spelling dict: "{BARKS_OCR_SPELL_DICT}".')

spell_dict = enchant.DictWithPWL("en_US", str(BARKS_OCR_SPELL_DICT))


def ocr_titles(title_list: List[str]) -> None:
    start = time.time()

    num_files_processed = 0
    for title in title_list:
        logging.info(f'OCRing all pages in "{title}"...')

        comic = comics_database.get_comic_book(title)

        srce_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
        dest_file_groups = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)

        for srce_file, dest_files in zip(srce_files, dest_file_groups):
            result = ocr_comic_page(srce_file, dest_files)
            if result == ProcessResult.FAILURE:
                raise Exception("There were process errors.")
                # pass
            if result == ProcessResult.SUCCESS:
                num_files_processed += 1

    logging.info(f"Time taken to OCR all {num_files_processed} files: {int(time.time() - start)}s.")


def ocr_comic_page(svg_file: Path, ocr_json_files: Tuple[Path, Path]) -> ProcessResult:
    png_file = Path(str(svg_file) + ".png")

    if not os.path.isfile(png_file):
        logging.error(f'Could not find png file "{png_file}".')
        return ProcessResult.FAILURE

    if all([os.path.isfile(f) for f in ocr_json_files]):
        for ocr_json_file in ocr_json_files:
            logging.info(f'OCR file exists - skipping: "{get_abbrev_path(ocr_json_file)}".')
        return ProcessResult.SKIPPED

    svg_stem = Path(svg_file).stem
    grey_image_file = work_dir / (svg_stem + "-grey.png")
    make_grey_image(png_file, grey_image_file)

    for ocr_json_file in ocr_json_files:
        if os.path.isfile(ocr_json_file):
            logging.info(f'OCR file exists - skipping: "{get_abbrev_path(ocr_json_file)}".')
            continue

        logging.info(
            f'OCRing png file "{get_abbrev_path(png_file)}"'
            f' to "{get_abbrev_path(ocr_json_file)}"...'
        )

        ocr_suffix = get_ocr_no_json_suffix(ocr_json_file)
        if ocr_suffix == ".easyocr":
            text_data_boxes = get_easyocr_text_box_data(grey_image_file)
        else:
            assert ocr_suffix == ".paddleocr"
            text_data_boxes = get_paddleocr_text_box_data(grey_image_file)

        with open(os.path.join(ocr_json_file), "w") as f:
            json.dump(text_data_boxes, f, indent=4)

    return ProcessResult.SUCCESS


def make_grey_image(png_file: Path, out_grey_file: Path) -> None:
    bw_image = get_bw_image_from_alpha(Path(png_file))
    bw_image = preprocess_image(bw_image)
    cv.imwrite(str(out_grey_file), bw_image)


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

    # word = spell_correct.autocorrect_word(word)
    # print(f"AUTO corrected word: '{word}'")
    # if not spell_dict.check(word):
    #     return False, ""
    return True, word


def get_easyocr_text_box_data(image_file: Path) -> List[Tuple[List[int], str, str, float]]:
    reader = easyocr.Reader(["en"])
    result = reader.readtext(
        str(image_file),
        paragraph=False,
        decoder="beamsearch",
        beamWidth=5,
        batch_size=8,
        contrast_ths=0.1,
        adjust_contrast=0.5,
        text_threshold=0.7,
        low_text=0.4,
        link_threshold=0.6,
        mag_ratio=2.0,
    )

    text_list = []
    for bbox, text, prob in result:
        text_str = text.strip()
        if prob < 0.1 or not text_str:
            continue

        words_ok, accepted_words = words_are_ok(text_str)
        if not words_ok:
            continue
        accepted_words_str = " ".join(accepted_words)

        (bl, br, tr, tl) = bbox
        x0 = int(round(bl[0]))
        y0 = int(round(bl[1]))
        x1 = int(round(br[0]))
        y1 = int(round(br[1]))
        x2 = int(round(tr[0]))
        y2 = int(round(tr[1]))
        x3 = int(round(tl[0]))
        y3 = int(round(tl[1]))
        bbox = [x0, y0, x1, y1, x2, y2, x3, y3]

        text_list.append((bbox, text_str, accepted_words_str, prob))

    return text_list


def get_paddleocr_text_box_data(image_file: Path) -> List[Tuple[List[int], str, str, float]]:
    # Import PaddleOCR here where it can't screw up 'logging'.
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        #use_angle_cls=True,
        lang="en",
        det_limit_side_len=2560,
        det_db_thresh=0.1,
        det_db_box_thresh=0.2,
        enable_mkldnn=True,
    )

    result = ocr.predict(str(image_file))

    for res in result:
        print(res['input_path'])
        print(res['model_settings'])
        print(res['text_det_params'])
        res.save_to_img("output")
        res.save_to_json("output")

    text_list = []
    for res in result:
        rec_texts = res["rec_texts"]
        rec_scores = res["rec_scores"]
        rec_polys = res["rec_polys"]
        for i, rec in enumerate(rec_texts):
            text = rec_texts[i]
            prob = rec_scores[i]
            text_str = text.strip()
            bbox = [(int(rec_polys[i][j][0]), int(rec_polys[i][j][1])) for j in range(4)]
            if prob < 0.1 or not text_str:
                continue

            words_ok, accepted_words = words_are_ok(text_str)
            if not words_ok:
                continue
            accepted_words_str = " ".join(accepted_words)

            (bl, br, tr, tl) = bbox
            x0 = int(round(bl[0]))
            y0 = int(round(bl[1]))
            x1 = int(round(br[0]))
            y1 = int(round(br[1]))
            x2 = int(round(tr[0]))
            y2 = int(round(tr[1]))
            x3 = int(round(tl[0]))
            y3 = int(round(tl[1]))
            bbox = [x0, y0, x1, y1, x2, y2, x3, y3]

            text_list.append((bbox, text_str, accepted_words_str, prob))

    return text_list


def get_box_str(box: List[int]) -> str:
    assert len(box) == 8
    return (
        f"{box[0]:04},{box[1]:04}, {box[2]:04},{box[3]:04}, "
        f"{box[4]:04},{box[5]:04}, {box[6]:04},{box[7]:04}"
    )


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs("Ocr titles", CmdArgNames.TITLE | CmdArgNames.VOLUME)
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = "batch-ocr.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    work_dir = Path(tempfile.gettempdir())

    comics_database = cmd_args.get_comics_database()

    ocr_titles(cmd_args.get_titles())

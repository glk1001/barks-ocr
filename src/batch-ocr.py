# ruff: noqa: ERA001

import concurrent.futures
import json
import sys
import tempfile
from pathlib import Path

import cv2 as cv
import easyocr
import enchant
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_abbrev_path, get_ocr_type
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from comic_utils.timing import Timing
from loguru import logger
from loguru_config import LoguruConfig
from paddleocr import PaddleOCR

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
if not BARKS_OCR_SPELL_DICT.is_file():
    msg = f'Could not find Barks spelling dict: "{BARKS_OCR_SPELL_DICT}".'
    raise FileNotFoundError(msg)

spell_dict = enchant.DictWithPWL("en_US", str(BARKS_OCR_SPELL_DICT))

num_files_processed = 0


def ocr_titles(title_list: list[str]) -> None:
    timing = Timing()

    global num_files_processed
    num_files_processed = 0

    for title in title_list:
        logger.info(f'OCRing all pages in "{title}"...')

        comic = comics_database.get_comic_book(title)

        srce_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
        dest_file_groups = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)

        with concurrent.futures.ProcessPoolExecutor(10) as executor:
            for srce_file, dest_files in zip(srce_files, dest_file_groups, strict=True):
                executor.submit(ocr_page, srce_file, dest_files)

    logger.info(
        f"Time taken to OCR all {num_files_processed} files: {timing.get_elapsed_time_with_unit()}."
    )

def ocr_page(srce_file: Path, dest_files: tuple[Path, Path]) -> None:
    result = ocr_comic_page(srce_file, dest_files)
    if result == ProcessResult.FAILURE:
        logger.error(f'"{srce_file}": There were process errors.')
    if result == ProcessResult.SUCCESS:
        global num_files_processed
        num_files_processed += 1


def ocr_comic_page(svg_file: Path, ocr_json_files: tuple[Path, Path]) -> ProcessResult:
    png_file = Path(str(svg_file) + ".png")

    if not png_file.is_file():
        logger.error(f'Could not find png file "{png_file}".')
        return ProcessResult.FAILURE

    if all(f.is_file() for f in ocr_json_files):
        for ocr_json_file in ocr_json_files:
            logger.info(f'OCR file exists - skipping: "{get_abbrev_path(ocr_json_file)}".')
        return ProcessResult.SKIPPED

    svg_stem = Path(svg_file).stem
    grey_image_file = work_dir / (svg_stem + "-grey.png")
    make_grey_image(png_file, grey_image_file)

    for ocr_json_file in ocr_json_files:
        if ocr_json_file.is_file():
            logger.info(f'OCR file exists - skipping: "{get_abbrev_path(ocr_json_file)}".')
            continue

        logger.info(
            f'OCRing png file "{get_abbrev_path(png_file)}"'
            f' to "{get_abbrev_path(ocr_json_file)}"...'
        )

        ocr_type = get_ocr_type(ocr_json_file)
        if ocr_type == "easyocr":
            text_data_boxes = get_easyocr_text_box_data(grey_image_file)
        else:
            assert ocr_type == "paddleocr"
            text_data_boxes = get_paddleocr_text_box_data(grey_image_file)

        with ocr_json_file.open("w") as f:
            json.dump(text_data_boxes, f, indent=4)

    return ProcessResult.SUCCESS


def make_grey_image(png_file: Path, out_grey_file: Path) -> None:
    bw_image = get_bw_image_from_alpha(Path(png_file))
    bw_image = preprocess_image(bw_image)
    cv.imwrite(str(out_grey_file), bw_image)


def words_are_ok(words_str: str) -> tuple[bool, list[str]]:
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


def can_auto_correct(words_str: str) -> tuple[bool, str]:
    if words_str in AUTO_CORRECTIONS:
        return True, AUTO_CORRECTIONS[words_str]

    if words_str[-1] in ").!;?," and words_str[:-1] in AUTO_CORRECTIONS:
        return True, AUTO_CORRECTIONS[words_str[:-1]] + words_str[-1]

    return False, ""


def word_is_ok(word: str) -> tuple[bool, str]:
    word = word.upper().strip()

    if not word:
        return False, ""

    if word in REJECTED_WORDS:
        return False, ""

    if spell_dict.check(word):
        return True, word

    if word[-1] in ").!;?," and spell_dict.check(word[:-1]):
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


def get_easyocr_text_box_data(
    image_file: Path,
) -> list[tuple[list[int], str, str, float]]:
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
        if prob < 0.1 or not text_str:  # noqa: PLR2004
            continue

        words_ok, accepted_words = words_are_ok(text_str)
        if not words_ok:
            continue
        accepted_words_str = " ".join(accepted_words)

        (bl, br, tr, tl) = bbox
        x0 = round(bl[0])
        y0 = round(bl[1])
        x1 = round(br[0])
        y1 = round(br[1])
        x2 = round(tr[0])
        y2 = round(tr[1])
        x3 = round(tl[0])
        y3 = round(tl[1])
        bnd_box = [x0, y0, x1, y1, x2, y2, x3, y3]

        text_list.append((bnd_box, text_str, accepted_words_str, prob))

    return text_list


def get_paddleocr_text_box_data(
    image_file: Path,
) -> list[tuple[list[int], str, str, float]]:
    # Import PaddleOCR here where it can't screw up 'logger'.
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        # use_angle_cls=True,
        lang="en",
        det_limit_side_len=2560,
        det_db_thresh=0.1,
        det_db_box_thresh=0.2,
        enable_mkldnn=True,
    )

    result = ocr.predict(str(image_file))

    text_list = []
    for res in result:
        rec_texts = res["rec_texts"]
        rec_scores = res["rec_scores"]
        rec_polys = res["rec_polys"]
        for i, rec in enumerate(rec_texts):
            text = rec
            prob = rec_scores[i]
            text_str = text.strip()
            bbox = [(int(rec_polys[i][j][0]), int(rec_polys[i][j][1])) for j in range(4)]
            if prob < 0.1 or not text_str:  # noqa: PLR2004
                continue

            words_ok, accepted_words = words_are_ok(text_str)
            if not words_ok:
                continue
            accepted_words_str = " ".join(accepted_words)

            (bl, br, tr, tl) = bbox
            x0 = round(bl[0])
            y0 = round(bl[1])
            x1 = round(br[0])
            y1 = round(br[1])
            x2 = round(tr[0])
            y2 = round(tr[1])
            x3 = round(tl[0])
            y3 = round(tl[1])
            bbox = [x0, y0, x1, y1, x2, y2, x3, y3]

            text_list.append((bbox, text_str, accepted_words_str, prob))

    return text_list


def get_box_str(box: list[int]) -> str:
    assert len(box) == 8  # noqa: PLR2004
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

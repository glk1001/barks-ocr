import json
import logging
import os.path
import sys
from pathlib import Path
from typing import List

import cv2 as cv
import numpy as np
from PIL import Image, ImageDraw

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_info import PNG_FILE_EXT
from barks_fantagraphics.comics_utils import get_relpath


# TODO: Duplicated
def setup_logging(log_level) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


# TODO: Duplicated - comics utils??
def get_bw_image(file: str) -> cv.typing.MatLike:
    black_mask = cv.imread(file, -1)

    scale = 4
    black_mask = cv.resize(
        black_mask, (0, 0), fx=1.0 / scale, fy=1.0 / scale, interpolation=cv.INTER_AREA
    )

    _, _, _, binary = cv.split(black_mask)
    binary = np.uint8(255 - binary)

    return binary


# TODO: Duplicated
def get_box_str(box: List[int]) -> str:
    assert len(box) == 8
    return (
        f"{box[0]:04},{box[1]:04}, {box[2]:04},{box[3]:04}, "
        f"{box[4]:04},{box[5]:04}, {box[6]:04},{box[7]:04}"
    )


def ocr_annotate_title(title: str, out_dir: str) -> None:
    out_dir = os.path.join(out_dir, title)

    logging.info(f'OCR annotating all pages in "{title}" to directory "{out_dir}"...')

    os.makedirs(out_dir, exist_ok=True)
    comic = comics_database.get_comic_book(title)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    ocr_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)

    for svg_file, ocr_file in zip(svg_files, ocr_files):
        png_file = svg_file + PNG_FILE_EXT
        annotated_img_file = os.path.join(out_dir, Path(svg_file).stem + "-ocr-annotated.png")
        text_and_boxes_file = os.path.join(out_dir, Path(svg_file).stem + "-ocr-text-boxes.txt")
        if not ocr_annotate_file(png_file, ocr_file, annotated_img_file, text_and_boxes_file):
            # raise Exception("There were process errors.")
            pass


def ocr_annotate_file(
    png_file: str, ocr_file: str, annotated_img_file: str, text_and_boxes_file: str
) -> bool:
    logging.info(f'OCR annotating image "{get_relpath(png_file)}"...')

    if not os.path.isfile(png_file):
        logging.error(f'Could not find image file "{png_file}".')
        return False
    if not os.path.isfile(ocr_file):
        logging.error(f'Could not find ocr file "{ocr_file}".')
        return False
    if os.path.isfile(annotated_img_file):
        logging.info(f'Found annotation file "{annotated_img_file}" -- skipping.')
        return True

    with open(ocr_file, "r") as f:
        jsn_text_data_boxes = json.load(f)

    bw_image = get_bw_image(png_file)

    pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image]))
    img_rects = ImageDraw.Draw(pil_image)
    for box, _, _, _ in jsn_text_data_boxes:
        img_rects.polygon(box, outline="green", width=5)
    img_rects._image.save(annotated_img_file)

    max_test_len = max([len(t[1]) for t in jsn_text_data_boxes])
    max_acc_test_len = max([len(t[2]) for t in jsn_text_data_boxes])
    with open(text_and_boxes_file, "w") as f:
        for box, text, accepted_text, prob in jsn_text_data_boxes:
            f.write(
                f"text: '{text:<{max_test_len}}', acc: '{accepted_text:<{max_acc_test_len}}'"
                f" P: {prob:4.2f}, box: {get_box_str(box)}\n"
            )

    return True


if __name__ == "__main__":

    setup_logging(logging.INFO)

    cmd_args = CmdArgs("OCR annotate title", CmdArgNames.TITLE | CmdArgNames.WORK_DIR)
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logging.error(error_msg)
        sys.exit(1)

    comics_database = cmd_args.get_comics_database()

    ocr_annotate_title(cmd_args.get_title(), cmd_args.get_work_dir())

import json
import logging
import math
import os.path
import sys
from pathlib import Path
from typing import List

import cv2 as cv
from PIL import Image, ImageDraw
from shapely.geometry import Polygon

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_image_io import get_bw_image_from_alpha
from barks_fantagraphics.comics_info import PNG_FILE_EXT
from barks_fantagraphics.comics_utils import get_abbrev_path, setup_logging
from ocr_box import OcrBox


def ocr_annotate_titles(titles: List[str], out_dir: str) -> None:
    for title in titles:
        ocr_annotate_title(title, out_dir)


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
        if not ocr_annotate_file(png_file, ocr_file, annotated_img_file):
            raise Exception("There were process errors.")


def ocr_annotate_file(
    png_file: str,
    ocr_file: str,
    annotated_img_file: str,
) -> bool:
    logging.info(f'OCR annotating image "{get_abbrev_path(png_file)}"...')

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

    bw_image = get_bw_image_from_alpha(png_file)

    text_data_polygons: List[OcrBox] = []
    pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image]))
    img_rects = ImageDraw.Draw(pil_image)

    for box, ocr_text, accepted_text, ocr_prob in jsn_text_data_boxes:
        p1 = (box[0], box[1])
        p2 = (box[2], box[3])
        p3 = (box[4], box[5])
        p4 = (box[6], box[7])
        poly_points = [p1, p2, p3, p4]
        poly = Polygon(poly_points)

        is_rect = math.isclose(poly.minimum_rotated_rectangle.area, poly.area)
        is_rect = is_rect and p1[0] < p3[0] and p1[1] < p3[1]

        if is_rect:
            img_rects.rectangle([p1, p3], outline="green", width=5)
        else:
            img_rects.polygon(box, outline="red", width=3)

        text_data_polygons.append(OcrBox(poly_points, is_rect, ocr_text, ocr_prob, accepted_text))

    img_rects._image.save(annotated_img_file)

    return True


if __name__ == "__main__":

    setup_logging(logging.INFO)

    cmd_args = CmdArgs(
        "OCR annotate titles", CmdArgNames.VOLUME | CmdArgNames.TITLE | CmdArgNames.WORK_DIR
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logging.error(error_msg)
        sys.exit(1)

    comics_database = cmd_args.get_comics_database()

    ocr_annotate_titles(cmd_args.get_titles(), cmd_args.get_work_dir())

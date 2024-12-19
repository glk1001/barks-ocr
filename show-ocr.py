import json
import logging
import math
import os.path
import sys
from pathlib import Path
from typing import List, Tuple, Dict

import cv2 as cv
from PIL import Image, ImageDraw
from shapely.geometry import Polygon

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_image_io import get_bw_image_from_alpha
from barks_fantagraphics.comics_info import PNG_FILE_EXT
from barks_fantagraphics.comics_utils import get_relpath, setup_logging
from geometry import Rect
from ocr_box import OcrBox, save_groups_as_json, load_groups_from_json, get_box_str


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
        text_and_boxes_json_file = os.path.join(
            out_dir, Path(svg_file).stem + "-ocr-text-boxes.json"
        )
        if not ocr_annotate_file(
            png_file, ocr_file, annotated_img_file, text_and_boxes_file, text_and_boxes_json_file
        ):
            raise Exception("There were process errors.")


def ocr_annotate_file(
    png_file: str,
    ocr_file: str,
    annotated_img_file: str,
    text_and_boxes_file: str,
    text_and_boxes_json_file: str,
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

    bw_image = get_bw_image_from_alpha(png_file)
    max_test_len = max([len(t[1]) for t in jsn_text_data_boxes])
    max_acc_test_len = max([len(t[2]) for t in jsn_text_data_boxes])

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
            print(p1, p3)
            img_rects.rectangle([p1, p3], outline="green", width=5)
        else:
            img_rects.polygon(box, outline="red", width=3)

        text_data_polygons.append(OcrBox(poly_points, is_rect, ocr_text, ocr_prob, accepted_text))

    img_rects._image.save(annotated_img_file)

    groups = make_box_groups(text_data_polygons)

    save_groups_as_json(groups, text_and_boxes_json_file)
    groups = load_groups_from_json(text_and_boxes_json_file)

    with open(text_and_boxes_file, "w") as f:
        for group in groups:
            for ocr_box, dist in groups[group]:
                f.write(
                    f"Group: {group:03d}, "
                    f"text: '{ocr_box.ocr_text:<{max_test_len}}', "
                    f"acc: '{ocr_box.accepted_text:<{max_acc_test_len}}', "
                    f"P: {ocr_box.ocr_prob:4.2f}, "
                    f"box: {get_box_str(ocr_box.box_points)}, rect: {ocr_box.is_rect}\n"
                )

    return True


def make_box_groups(text_data_polygons: List[OcrBox]) -> Dict[int, List[Tuple[OcrBox, float]]]:
    print(text_data_polygons)
    groups: Dict[int, List[Tuple[OcrBox, float]]] = dict()
    num_groups = 0
    for ocr_box in text_data_polygons:
        print()
        print(
            f"CHECK TEXT '{ocr_box.ocr_text}': box {ocr_box.box_points}: {ocr_box.ocr_text},"
            f" {ocr_box.accepted_text}, {ocr_box.ocr_prob}"
        )
        in_group = False
        for group in groups:
            for grp_ocr_box, _ in groups[group]:
                if ocr_box.is_rect and grp_ocr_box.is_rect:
                    dist = get_rect_dist(ocr_box.box_points, grp_ocr_box.box_points)
                else:
                    dist = get_dist(ocr_box.box_points, grp_ocr_box.box_points)
                print(
                    f"gbox: {grp_ocr_box.box_points}, gtext: {grp_ocr_box.ocr_text}, dist: {dist},"
                    f" box: {ocr_box.box_points}, text: {ocr_box.ocr_text}"
                )
                if dist < 15:
                    groups[group].append((ocr_box, dist))
                    in_group = True
                    print(
                        f"Added to group {group}: {ocr_box.box_points}, {dist}, {ocr_box.ocr_text}"
                    )
                    break
            if in_group:
                break
        if not in_group:
            print(f"Starting group {num_groups} with {ocr_box.box_points}, {ocr_box.ocr_text}")
            groups[num_groups] = [(ocr_box, 0.0)]
            num_groups += 1

    return groups


def get_rect_dist(poly1: List[Tuple[float, float]], poly2: List[Tuple[float, float]]) -> float:
    p1 = poly1[0]
    p3 = poly1[2]
    rect1 = Rect(p1[0], p1[1], p3[0] - p1[0], p3[1] - p1[1])

    p1 = poly2[0]
    p3 = poly2[2]
    rect2 = Rect(p1[0], p1[1], p3[0] - p1[0], p3[1] - p1[1])

    # print(f"rect1: {rect1.x}, {rect1.y}, {rect1.w}, {rect1.h}")
    # print(f"rect2: {rect2.x}, {rect2.y}, {rect2.w}, {rect2.h}")

    return rect1.distance_to_rect(rect2)


def get_dist(poly1: List[Tuple[float, float]], poly2: List[Tuple[float, float]]) -> float:
    return Polygon(poly1).distance(Polygon(poly2))


if __name__ == "__main__":

    setup_logging(logging.INFO)

    cmd_args = CmdArgs("OCR annotate title", CmdArgNames.TITLE | CmdArgNames.WORK_DIR)
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logging.error(error_msg)
        sys.exit(1)

    comics_database = cmd_args.get_comics_database()

    ocr_annotate_title(cmd_args.get_title(), cmd_args.get_work_dir())

import json
import logging
import math
import os.path
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict

import cv2 as cv
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_info import PNG_FILE_EXT
from barks_fantagraphics.comics_utils import get_relpath, setup_logging
from geometry import Rect


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
def get_box_str(box: Polygon) -> str:
    pts = box.exterior.coords
    assert len(pts) == 5
    return (
        f"{round(pts[0][0]):04},{round(pts[0][1]):04}, {round(pts[1][0]):04},{round(pts[1][1]):04}, "
        f"{round(pts[2][0]):04},{round(pts[2][1]):04}, {round(pts[3][0]):04},{round(pts[3][1]):04}"
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
        text_and_boxes_json_file = os.path.join(
            out_dir, Path(svg_file).stem + "-ocr-text-boxes.json"
        )
        if not ocr_annotate_file(
            png_file, ocr_file, annotated_img_file, text_and_boxes_file, text_and_boxes_json_file
        ):
            # raise Exception("There were process errors.")
            pass


@dataclass
class OcrBox:
    box: Polygon
    is_rect: bool
    ocr_text: str
    ocr_prob: float
    accepted_text: str

def save_groups_as_json(groups:Dict[int, List[Tuple[OcrBox, float]]], file: str) -> None:

    def custom_ocr_box(obj):
        if isinstance(obj, OcrBox):
            poly_xy = [(xy[0],xy[1]) for xy in obj.box.exterior.coords]
            print(f"poly_xy = {poly_xy}")
            return poly_xy, obj.is_rect, obj.ocr_text, obj.ocr_prob, obj.accepted_text
        return obj

    with open(file, "w") as f:
        json.dump(groups, f, indent=4, default=custom_ocr_box)


def load_groups_from_json(file: str)->Dict[int, List[Tuple[OcrBox, float]]]:
    with open(file, "r") as f:
        json_groups = json.load(f)

    groups:Dict[int, List[Tuple[OcrBox, float]]] = dict()
    for json_group in json_groups:
        for json_ocr_box in json_group[0]:
            pass

    return groups


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

    bw_image = get_bw_image(png_file)
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
        poly = Polygon([p1, p2, p3, p4])

        is_rect = math.isclose(poly.minimum_rotated_rectangle.area, poly.area)
        is_rect = is_rect and p1[0] < p3[0] and p1[1] < p3[1]

        if is_rect:
            print(p1, p3)
            img_rects.rectangle([p1, p3], outline="green", width=5)
        else:
            img_rects.polygon(box, outline="red", width=3)

        text_data_polygons.append(OcrBox(poly, is_rect, ocr_text, ocr_prob, accepted_text))

    img_rects._image.save(annotated_img_file)

    groups = make_box_groups(text_data_polygons)

    def custom_ocr_box(obj):
        if isinstance(obj, OcrBox):
            poly_xy = [(xy[0],xy[1]) for xy in obj.box.exterior.coords]
            print(f"poly_xy = {poly_xy}")
            return poly_xy, obj.is_rect, obj.ocr_text, obj.ocr_prob, obj.accepted_text
        return obj

    with open(text_and_boxes_json_file, "w") as f:
        json.dump(groups, f, indent=4, default=custom_ocr_box)

    with open(text_and_boxes_file, "w") as f:
        for group in groups:
            for ocr_box, dist in groups[group]:
                f.write(
                    f"Group: {group:03d}, "
                    f"text: '{ocr_box.ocr_text:<{max_test_len}}', "
                    f"acc: '{ocr_box.accepted_text:<{max_acc_test_len}}', "
                    f"P: {ocr_box.ocr_prob:4.2f}, "
                    f"box: {get_box_str(ocr_box.box)}, rect: {ocr_box.is_rect}\n"
                )

    return True


def make_box_groups(text_data_polygons: List[OcrBox]) -> Dict[int, List[Tuple[OcrBox, float]]]:
    print(text_data_polygons)
    groups: Dict[int, List[Tuple[OcrBox, float]]] = dict()
    num_groups = 0
    for ocr_box in text_data_polygons:
        print()
        print(
            f"CHECK TEXT '{ocr_box.ocr_text}': box {ocr_box.box}: {ocr_box.ocr_text}, {ocr_box.accepted_text}, {ocr_box.ocr_prob}"
        )
        in_group = False
        for group in groups:
            for grp_ocr_box, _ in groups[group]:
                if ocr_box.is_rect and grp_ocr_box.is_rect:
                    dist = get_rect_dist(ocr_box.box, grp_ocr_box.box)
                else:
                    dist = get_dist(ocr_box.box, grp_ocr_box.box)
                print(
                    f"gbox: {grp_ocr_box.box}, gtext: {grp_ocr_box.ocr_text}, dist: {dist}, box: {ocr_box.box}, text: {ocr_box.ocr_text}"
                )
                if dist < 15:
                    groups[group].append((ocr_box, dist))
                    in_group = True
                    print(f"Added to group {group}: {ocr_box.box}, {dist}, {ocr_box.ocr_text}")
                    break
            if in_group:
                break
        if not in_group:
            print(f"Starting group {num_groups} with {ocr_box.box}, {ocr_box.ocr_text}")
            groups[num_groups] = [(ocr_box, 0.0)]
            num_groups += 1

    return groups


#
#
# class Rect:
#     def __init__(self,cpt,w,h):
#         self.x = cpt[0]
#         self.y = cpt[1]
#         self.w = w
#         self.h = h
#
#     def dist(self,other):
#         #overlaps in x or y:
#         if abs(self.x - other.x) <= (self.w + other.w):
#             dx = 0
#         else:
#             dx = abs(self.x - other.x) - (self.w + other.w)
#         #
#         if abs(self.y - other.y) <= (self.h + other.h):
#             dy = 0
#         else:
#             dy = abs(self.y - other.y) - (self.h + other.h)
#         return dx + dy


def get_rect_dist(poly1: Polygon, poly2: Polygon) -> float:
    p1 = poly1.exterior.coords[0]
    p3 = poly1.exterior.coords[2]
    rect1 = Rect(p1[0], p1[1], p3[0] - p1[0], p3[1] - p1[1])

    p1 = poly2.exterior.coords[0]
    p3 = poly2.exterior.coords[2]
    rect2 = Rect(p1[0], p1[1], p3[0] - p1[0], p3[1] - p1[1])

    # print(f"rect1: {rect1.x}, {rect1.y}, {rect1.w}, {rect1.h}")
    # print(f"rect2: {rect2.x}, {rect2.y}, {rect2.w}, {rect2.h}")

    return rect1.distance_to_rect(rect2)


def get_dist(poly1: Polygon, poly2: Polygon) -> float:
    return poly1.distance(poly2)


if __name__ == "__main__":

    setup_logging(logging.INFO)

    cmd_args = CmdArgs("OCR annotate title", CmdArgNames.TITLE | CmdArgNames.WORK_DIR)
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logging.error(error_msg)
        sys.exit(1)

    comics_database = cmd_args.get_comics_database()

    ocr_annotate_title(cmd_args.get_title(), cmd_args.get_work_dir())

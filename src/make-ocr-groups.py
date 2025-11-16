import json
import os.path
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_ocr_no_json_suffix
from loguru import logger
from shapely.geometry import Polygon

from utils.geometry import Rect
from utils.ocr_box import (
    OcrBox,
    get_box_str,
    load_groups_from_json,
    save_groups_as_json,
)


def make_ocr_groups_for_titles(title_list: List[str], out_dir: Path) -> None:
    for title in title_list:
        make_ocr_groups_for_title(title, out_dir)


def make_ocr_groups_for_title(title: str, out_dir: Path) -> None:
    out_dir /= title

    logger.info(f'Making OCR groups for all pages in "{title}". To directory "{out_dir}"...')

    os.makedirs(out_dir, exist_ok=True)
    comic = comics_database.get_comic_book(title)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    ocr_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)

    for svg_file, ocr_file in zip(svg_files, ocr_files):
        svg_stem = Path(svg_file).stem

        for ocr_type_file in ocr_file:
            ocr_suffix = get_ocr_no_json_suffix(ocr_type_file)

            ocr_groups_json_file = get_ocr_groups_json_filename(svg_stem, ocr_suffix, out_dir)
            ocr_groups_txt_file = get_ocr_groups_txt_filename(svg_stem, ocr_suffix, out_dir)
            # # ocr_final_data_groups_json_file = get_ocr_final_data_groups_json_filename(
            # #     svg_stem, ocr_suffix, out_dir
            # )

            if not make_ocr_groups(ocr_type_file, ocr_groups_json_file, ocr_groups_txt_file):
                raise Exception("There were process errors.")


def get_ocr_groups_txt_filename(svg_stem: str, ocr_suffix, out_dir: Path) -> Path:
    return out_dir / (svg_stem + f"-calculated-groups{ocr_suffix}.txt")


def get_ocr_groups_json_filename(svg_stem: str, ocr_suffix, out_dir: Path) -> Path:
    return out_dir / (svg_stem + f"-calculated-groups{ocr_suffix}.json")


def make_ocr_groups(ocr_file: Path, ocr_groups_json_file: Path, ocr_groups_txt_file: Path) -> bool:
    logger.info(f'Making OCR groups for file "{ocr_file}"...')

    if not ocr_file.is_file():
        logger.error(f'Could not find ocr file "{ocr_file}".')
        return False

    with ocr_file.open("r") as f:
        jsn_text_data_boxes = json.load(f)

    text_data_polygons: List[OcrBox] = []

    for box, ocr_text, accepted_text, ocr_prob in jsn_text_data_boxes:
        p1 = (box[0], box[1])
        p2 = (box[2], box[3])
        p3 = (box[4], box[5])
        p4 = (box[6], box[7])
        poly_points = [p1, p2, p3, p4]

        text_data_polygons.append(OcrBox(poly_points, ocr_text, ocr_prob, accepted_text))

    groups = make_box_groups(text_data_polygons)

    save_groups_as_json(groups, ocr_groups_json_file)
    groups = load_groups_from_json(ocr_groups_json_file)

    max_text_len = max([len(t[1]) for t in jsn_text_data_boxes])
    max_acc_text_len = max([len(t[2]) for t in jsn_text_data_boxes])

    logger.info(f'Writing OCR groups to file "{ocr_groups_txt_file}"...')
    with ocr_groups_txt_file.open("w") as f:
        for group in groups:
            for ocr_box, dist in groups[group]:
                # noinspection PyProtectedMember
                f.write(
                    f"Group: {group:03d}, "
                    f"text: '{ocr_box.ocr_text:<{max_text_len}}', "
                    f"acc: '{ocr_box.accepted_text:<{max_acc_text_len}}', "
                    f"P: {ocr_box.ocr_prob:4.2f}, "
                    f"box: {get_box_str(ocr_box._box_points)}, rect: {ocr_box.is_approx_rect}\n"
                )

    return True


def make_box_groups(text_data_polygons: List[OcrBox]) -> Dict[int, List[Tuple[OcrBox, float]]]:
    groups: Dict[int, List[Tuple[OcrBox, float]]] = dict()
    num_groups = 0
    for ocr_box in text_data_polygons:
        in_group = False
        for group in groups:
            for grp_ocr_box, _ in groups[group]:
                if ocr_box.is_approx_rect and grp_ocr_box.is_approx_rect:
                    dist = get_rect_dist(
                        ocr_box.min_rotated_rectangle, grp_ocr_box.min_rotated_rectangle
                    )
                else:
                    # noinspection PyProtectedMember
                    dist = get_dist(ocr_box._box_points, grp_ocr_box._box_points)
                if dist < 15:
                    groups[group].append((ocr_box, dist))
                    in_group = True
                    break
            if in_group:
                break
        if not in_group:
            groups[num_groups] = [(ocr_box, 0.0)]
            num_groups += 1

    return groups


def get_rect_dist(
    box_rect1: List[Tuple[float, float]], box_rect2: List[Tuple[float, float]]
) -> float:
    bottom_left = box_rect1[0]
    top_right = box_rect1[1]
    rect1 = Rect(
        bottom_left[0], bottom_left[1], top_right[0] - bottom_left[0], top_right[1] - bottom_left[1]
    )

    bottom_left = box_rect2[0]
    top_right = box_rect2[1]
    rect2 = Rect(
        bottom_left[0], bottom_left[1], top_right[0] - bottom_left[0], top_right[1] - bottom_left[1]
    )

    # print(f"rect1: {rect1.x}, {rect1.y}, {rect1.w}, {rect1.h}")
    # print(f"rect2: {rect2.x}, {rect2.y}, {rect2.w}, {rect2.h}")

    return rect1.distance_to_rect(rect2)


def get_dist(poly1: List[Tuple[float, float]], poly2: List[Tuple[float, float]]) -> float:
    return Polygon(poly1).distance(Polygon(poly2))


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "Make OCR groups for title", CmdArgNames.VOLUME | CmdArgNames.TITLE | CmdArgNames.WORK_DIR
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    comics_database = cmd_args.get_comics_database()

    make_ocr_groups_for_titles(cmd_args.get_titles(), cmd_args.get_work_dir())

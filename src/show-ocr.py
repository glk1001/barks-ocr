import json
import os.path
import sys
from pathlib import Path
from typing import Dict, List

import cv2 as cv
from barks_fantagraphics.comics_cmd_args import CmdArgNames, CmdArgs
from barks_fantagraphics.comics_consts import PNG_FILE_EXT, RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_abbrev_path, get_ocr_no_json_suffix
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from loguru import logger
from loguru_config import LoguruConfig
from PIL import Image, ImageDraw, ImageFont

from utils.ocr_box import OcrBox

APP_LOGGING_NAME = "socr"

COLORS = [
    "green",
    "yellow",
    "blue",
    "red",
    "brown",
    "purple",
    "orange",
    "pink",
    "teal",
    "orchid",
    "blueviolet",
    "tan",
    "olive",
    "palegreen",
    "plum",
    "wheat",
    "gold",
    "hotpink",
]


def get_color(group_id: int) -> str:
    group_id %= len(COLORS)
    return COLORS[group_id]


def ocr_annotate_titles(title_list: List[str], out_dir: Path) -> None:
    for title in title_list:
        ocr_annotate_title(title, out_dir)


def ocr_annotate_title(title: str, out_dir: Path) -> None:
    out_dir = out_dir / title

    logger.info(f'OCR annotating all pages in "{title}" to directory "{out_dir}"...')

    os.makedirs(out_dir, exist_ok=True)
    comic = comics_database.get_comic_book(title)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    ocr_files = comic.get_srce_restored_ocr_story_files(RESTORABLE_PAGE_TYPES)
    panel_segments_files = comic.get_srce_panel_segments_files(RESTORABLE_PAGE_TYPES)

    for svg_file, ocr_file, panel_segments_file in zip(
        svg_files, ocr_files, panel_segments_files
    ):
        svg_stem = Path(svg_file).stem
        png_file = Path(str(svg_file) + PNG_FILE_EXT)

        for ocr_type_file in ocr_file:
            ocr_suffix = get_ocr_no_json_suffix(ocr_type_file)

            ocr_group_file = get_ocr_group_filename(svg_stem, ocr_suffix, out_dir)
            final_text_annotated_image_file = get_final_text_annotated_filename(
                svg_stem, ocr_suffix, out_dir
            )
            boxes_annotated_image_file = get_boxes_annotated_filename(
                svg_stem, ocr_suffix, out_dir
            )

            ocr_annotate_image_with_final_text(
                png_file, ocr_group_file, final_text_annotated_image_file
            )
            ocr_annotate_image_with_individual_boxes(
                png_file, ocr_group_file, boxes_annotated_image_file
            )

            annotate_image_with_panel_bounds(
                panel_segments_file, final_text_annotated_image_file
            )
            annotate_image_with_panel_bounds(
                panel_segments_file, boxes_annotated_image_file
            )


def get_final_text_annotated_filename(svg_stem: str, ocr_suffix, out_dir: Path) -> Path:
    return out_dir / (svg_stem + f"-ocr-gemini-final-text-annotated{ocr_suffix}.png")
    # return os.path.join(out_dir, svg_stem + f"-ocr-calculated-annotated{ocr_suffix}.png")


def get_boxes_annotated_filename(svg_stem: str, ocr_suffix, out_dir: Path) -> Path:
    return out_dir / (svg_stem + f"-ocr-gemini-boxes-annotated{ocr_suffix}.png")
    # return os.path.join(out_dir, svg_stem + f"-ocr-calculated-annotated{ocr_suffix}.png")


def get_ocr_group_filename(svg_stem: str, ocr_suffix: str, out_dir: Path) -> Path:
    # return os.path.join(out_dir, svg_stem + f"-gemini-groups{ocr_suffix}.json")
    return out_dir / (svg_stem + f"-gemini-final-groups{ocr_suffix}.json")
    # return out_dir / (svg_stem + f"-calculated-groups{ocr_suffix}.json")


def get_image_to_annotate(png_file: Path) -> cv.typing.MatLike:
    if not png_file.is_file():
        raise Exception(f'Could not find image file "{png_file}".')

    return get_bw_image_from_alpha(png_file)


def get_json_text_data_boxes(ocr_file: Path) -> Dict[str, any]:
    if not ocr_file.is_file():
        raise Exception(f'Could not find ocr file "{ocr_file}".')

    with ocr_file.open("r") as f:
        json_text_data_boxes = json.load(f)

    return json_text_data_boxes


def annotate_image_with_panel_bounds(
    panel_segments_file: Path,
    annotated_img_file: Path,
) -> None:
    if not annotated_img_file.is_file():
        raise Exception(f'Could not find image file "{annotated_img_file}".')

    write_bounds_to_image_file(
        annotated_img_file, panel_segments_file, annotated_img_file
    )


# TODO: Duplicated from show-panel-bounds
def write_bounds_to_image_file(
    png_file: Path, panel_segments_file: Path, bounds_img_file: Path
) -> bool:
    logger.info(f'Writing bounds for image "{get_abbrev_path(png_file)}"...')

    if not png_file.is_file():
        logger.error(f'Could not find image file "{png_file}".')
        return False
    if not panel_segments_file.is_file():
        logger.error(f'Could not find panel segments file "{panel_segments_file}".')
        return False

    logger.info(
        f'Loading panel segments file "{get_abbrev_path(panel_segments_file)}".'
    )
    with panel_segments_file.open("r") as f:
        panel_segment_info = json.load(f)

    pil_image = Image.open(str(png_file))
    assert pil_image.size[0] == panel_segment_info["size"][0]
    assert pil_image.size[1] == panel_segment_info["size"][1]

    img_rects = ImageDraw.Draw(pil_image)
    for box in panel_segment_info["panels"]:
        x0 = box[0]
        y0 = box[1]
        w = box[2]
        h = box[3]
        x1 = x0 + (w - 1)
        y1 = y0 + (h - 1)
        img_rects.rectangle([x0, y0, x1, y1], outline="green", width=10)

    # x_min, y_min, x_max, y_max = get_min_max_panel_values(panel_segment_info)
    # img_rects.rectangle([x_min, y_min, x_max, y_max], outline="red", width=2)

    img_rects._image.save(bounds_img_file)

    return True


def ocr_annotate_image_with_final_text(
    png_file: Path,
    ocr_file: Path,
    annotated_img_file: Path,
) -> None:
    if annotated_img_file.is_file():
        logger.info(f'Found annotation file - skipping: "{annotated_img_file}".')
        return

    logger.info(f'Annotating image "{png_file}" from ocr file "{ocr_file}"...')

    json_text_data_boxes = get_json_text_data_boxes(ocr_file)
    bw_image = get_image_to_annotate(png_file)

    pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image]))
    img_rects_draw = ImageDraw.Draw(pil_image)
    font_file = "/home/greg/Prj/fonts/verdana.ttf"
    font_size = 25
    font = ImageFont.truetype(font_file, font_size)

    for group in json_text_data_boxes:
        group_id = int(group)
        logger.info(f'Annotating group {group_id}"...')

        text_data = json_text_data_boxes[group]
        ocr_box = OcrBox(
            text_data["text_box"],
            text_data["ocr_text"],
            1.0,
            text_data["ai_text"],
        )
        print(
            f'group: {group_id:02} - text: "{text_data["ai_text"]}",'
            f' box: {text_data["text_box"]}, approx: {ocr_box.is_approx_rect}, rect: {ocr_box.min_rotated_rectangle}'
        )
        img_rects_draw.rectangle(
            ocr_box.min_rotated_rectangle, outline="orchid", width=7, fill="white"
        )

        text = f'{text_data["ai_text"]}'
        top_left = ocr_box.min_rotated_rectangle[0]
        top_left = (top_left[0] + 60, top_left[1] + 5)
        img_rects_draw.text(top_left, text, fill="red", font=font, align="left")

        panel_num = text_data["panel_num"]
        if panel_num != -1:
            info_text = f"{panel_num}:{get_text_type_abbrev(text_data['type'])}"
            top_left = ocr_box.min_rotated_rectangle[0]
            top_left = (top_left[0] + 10, top_left[1] - 15)
            info_box = img_rects_draw.textbbox(
                top_left, info_text, font=font, align="left"
            )
            img_rects_draw.rectangle(info_box, fill="white")
            img_rects_draw.text(
                top_left, info_text, fill="blue", font=font, align="left"
            )

    img_rects_draw._image.save(annotated_img_file)


def get_text_type_abbrev(text_type: str) -> str:
    if text_type == "narration":
        return "n"
    if text_type == "background":
        return "b"
    if text_type == "dialogue":
        return "s"
    if text_type == "think":
        return "t"

    return "?"


def ocr_annotate_image_with_individual_boxes(
    png_file: Path,
    ocr_file: Path,
    annotated_img_file: Path,
) -> None:
    if os.path.isfile(annotated_img_file):
        logger.info(f'Found annotation file - skipping: "{annotated_img_file}".')
        return

    logger.info(
        f'Annotating image with individual boxes "{png_file}" from ocr file "{ocr_file}"...'
    )

    json_text_data_boxes = get_json_text_data_boxes(ocr_file)
    bw_image = get_image_to_annotate(png_file)

    pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image]))
    img_rects_draw = ImageDraw.Draw(pil_image)

    for group in json_text_data_boxes:
        group_id = int(group)

        for box_id in json_text_data_boxes[group]["cleaned_box_texts"]:
            text_data = json_text_data_boxes[group]["cleaned_box_texts"][box_id]
            ocr_box = OcrBox(
                text_data["text_box"],
                text_data["text_frag"],
                0.0,
                "N/A",
            )

            if ocr_box.is_approx_rect:
                img_rects_draw.rectangle(
                    ocr_box.min_rotated_rectangle, outline=get_color(group_id), width=4
                )
            else:
                box = [
                    item for point in ocr_box.min_rotated_rectangle for item in point
                ]
                img_rects_draw.polygon(box, outline=get_color(group_id), width=2)

    img_rects_draw._image.save(annotated_img_file)


if __name__ == "__main__":
    # TODO(glk): Some issue with type checking inspection?
    # noinspection PyTypeChecker
    cmd_args = CmdArgs(
        "OCR annotate titles",
        CmdArgNames.VOLUME | CmdArgNames.TITLE | CmdArgNames.WORK_DIR,
    )
    args_ok, error_msg = cmd_args.args_are_valid()
    if not args_ok:
        logger.error(error_msg)
        sys.exit(1)

    # Global variables accessed by loguru-config.
    log_level = cmd_args.get_log_level()
    log_filename = "batch-ocr.log"
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    comics_database = cmd_args.get_comics_database()

    ocr_annotate_titles(cmd_args.get_titles(), cmd_args.get_work_dir())

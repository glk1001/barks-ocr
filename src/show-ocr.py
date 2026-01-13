# ruff: noqa: ERA001

import json
from pathlib import Path
from typing import Any

import cv2 as cv
import typer
from barks_fantagraphics.barks_titles import is_non_comic_title
from barks_fantagraphics.comics_consts import PNG_FILE_EXT, RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.comics_utils import get_abbrev_path, get_ocr_type
from barks_fantagraphics.ocr_file_paths import (
    OCR_ANNOTATIONS_DIR,
    OCR_PRELIM_DIR,
    get_ocr_boxes_annotated_filename,
    get_ocr_prelim_annotated_filename,
    get_ocr_prelim_groups_json_filename,
)
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from intspan import intspan
from loguru import logger
from loguru_config import LoguruConfig
from PIL import Image, ImageColor, ImageDraw, ImageFont

from utils.ocr_box import OcrBox

APP_LOGGING_NAME = "socr"

# noinspection SpellCheckingInspection
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


def ocr_annotate_titles(comics_database: ComicsDatabase, title_list: list[str]) -> None:
    for title in title_list:
        if is_non_comic_title(title):
            logger.warning(f'Not a comic title "{title}" - skipping.')
            continue

        ocr_annotate_title(comics_database, title)


def ocr_annotate_title(comics_database: ComicsDatabase, title: str) -> None:
    # Special case. Because "Silent Night" is a restored comic, the panel bounds
    # are out of whack.
    annotate_with_panels_bounds = title != "Silent Night"

    volume = comics_database.get_fanta_volume_int(title)
    volume_dirname = comics_database.get_fantagraphics_volume_title(volume)
    gemini_groups_dir = OCR_PRELIM_DIR / volume_dirname
    out_image_dir = OCR_ANNOTATIONS_DIR / volume_dirname
    out_image_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f'OCR annotating all pages in "{title}" to directory "{out_image_dir}"...')

    comic = comics_database.get_comic_book(title)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    ocr_files = comic.get_srce_restored_raw_ocr_story_files(RESTORABLE_PAGE_TYPES)
    panel_segments_files = comic.get_srce_panel_segments_files(RESTORABLE_PAGE_TYPES)

    for svg_file, ocr_file, panel_segments_file in zip(
        svg_files, ocr_files, panel_segments_files, strict=True
    ):
        svg_stem = Path(svg_file).stem
        png_file = Path(str(svg_file) + PNG_FILE_EXT)

        for ocr_type_file in ocr_file:
            ocr_type = get_ocr_type(ocr_type_file)

            ocr_group_file = gemini_groups_dir / get_ocr_prelim_groups_json_filename(
                svg_stem, ocr_type
            )
            prelim_text_annotated_image_file = out_image_dir / get_ocr_prelim_annotated_filename(
                svg_stem, ocr_type
            )

            if (
                prelim_text_annotated_image_file.is_file()
                and prelim_text_annotated_image_file.stat().st_mtime
                > ocr_group_file.stat().st_mtime
            ):
                logger.info(
                    f'Found prelim annotated file - skipping: "{prelim_text_annotated_image_file}".'
                )
                continue

            boxes_annotated_image_file = out_image_dir / get_ocr_boxes_annotated_filename(
                svg_stem, ocr_type
            )

            ocr_annotate_image_with_prelim_text(
                png_file, ocr_group_file, prelim_text_annotated_image_file
            )
            ocr_annotate_image_with_individual_boxes(
                png_file, ocr_group_file, boxes_annotated_image_file
            )

            if not annotate_with_panels_bounds:
                logger.warning(f'"{title}": special case - not annotating with panel bounds.')
            else:
                annotate_image_with_panel_bounds(
                    panel_segments_file, prelim_text_annotated_image_file
                )
                annotate_image_with_panel_bounds(panel_segments_file, boxes_annotated_image_file)


def get_image_to_annotate(png_file: Path) -> cv.typing.MatLike:
    if not png_file.is_file():
        msg = f'Could not find image file "{png_file}".'
        raise FileNotFoundError(msg)

    return get_bw_image_from_alpha(png_file)


def get_json_text_data_boxes(ocr_file: Path) -> dict[str, Any]:
    if not ocr_file.is_file():
        msg = f'Could not find ocr file "{ocr_file}".'
        raise RuntimeError(msg)

    with ocr_file.open("r") as f:
        return json.load(f)


def annotate_image_with_panel_bounds(
    panel_segments_file: Path,
    annotated_img_file: Path,
) -> None:
    if not annotated_img_file.is_file():
        msg = f'Could not find image file "{annotated_img_file}".'
        raise FileNotFoundError(msg)

    write_bounds_to_image_file(annotated_img_file, panel_segments_file, annotated_img_file)


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

    logger.info(f'Loading panel segments file "{get_abbrev_path(panel_segments_file)}".')
    with panel_segments_file.open("r") as f:
        panel_segment_info = json.load(f)

    pil_image = Image.open(str(png_file))
    if pil_image.size[0] != panel_segment_info["size"][0]:
        msg = (
            f'For image "{png_file}", image size[0] {pil_image.size[0]}'
            f" does not match panel segment info size[0] {panel_segment_info['size'][0]}."
        )
        raise RuntimeError(msg)
    if pil_image.size[1] != panel_segment_info["size"][1]:
        msg = (
            f'For image "{png_file}", image size[1] {pil_image.size[1]}'
            f" does not match panel segment info size[1] {panel_segment_info['size'][1]}."
        )
        raise RuntimeError(msg)

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

    # noinspection PyProtectedMember
    img_rects._image.save(bounds_img_file)  # noqa: SLF001

    return True


def ocr_annotate_image_with_prelim_text(
    png_file: Path,
    ocr_file: Path,
    annotated_img_file: Path,
) -> None:
    logger.info(f'Annotating image "{png_file}" from ocr file "{ocr_file}"...')

    # json_text_data_box_groups = get_json_text_data_boxes(ocr_file)
    # scale = 8700 / 9900
    # for group_id, text_data in json_text_data_box_groups["groups"].items():
    #     logger.info(f'Annotating group "{group_id}"...')
    #
    #     text_box = text_data["text_box"]
    #     text_data["text_box"] = [(item[0] * scale, item[1] * scale) for item in text_box]
    # with ocr_file.open("w") as f:
    #     json.dump(json_text_data_box_groups, f, indent=4)

    json_text_data_boxes = get_json_text_data_boxes(ocr_file)["groups"]
    bw_image = get_image_to_annotate(png_file)

    pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image])).convert("RGBA")
    overlay = Image.new("RGBA", pil_image.size, (0, 0, 0, 0))
    img_rects_draw = ImageDraw.Draw(overlay)
    font_file = "/home/greg/Prj/fonts/verdana.ttf"
    font_size = 25
    font = ImageFont.truetype(font_file, font_size)

    color_index = 0
    for group_id, text_data in json_text_data_boxes.items():
        logger.info(f'Annotating group "{group_id}"...')

        text_box = text_data["text_box"]

        ocr_box = OcrBox(
            text_box,
            text_data["ocr_text"],
            1.0,
            text_data["ai_text"],
        )
        # print(
        #     f'group: {group_id:02} - text: "{text_data["ai_text"]}",'
        #     f" box: {text_box, approx: {ocr_box.is_approx_rect},"
        #     f" rect: {ocr_box.min_rotated_rectangle}"
        # )
        # img_rects_draw.rectangle(
        #     ocr_box.min_rotated_rectangle, outline="orchid", width=7, fill=(0,255,255,100)
        # )
        bbox_color = (*ImageColor.getrgb(COLORS[color_index]), 255)
        text_color = "red"
        text_box_color = (*ImageColor.getrgb(COLORS[color_index]), 120)
        img_rects_draw.rectangle(ocr_box.min_rotated_rectangle, outline=bbox_color, width=7)

        text = f"{text_data['ai_text']}"
        top_left = ocr_box.min_rotated_rectangle[0]
        top_left = (top_left[0] + 60, top_left[1] + 5)
        text_box = img_rects_draw.textbbox(top_left, text, font=font, align="left")
        img_rects_draw.rectangle(text_box, fill=text_box_color)
        img_rects_draw.text(
            top_left, text, fill=text_color, font=font, align="left", stroke_width=1
        )

        panel_num = text_data["panel_num"]
        if panel_num != -1:
            info_text = f"{panel_num}:{get_text_type_abbrev(text_data['type'])}"
            top_left = ocr_box.min_rotated_rectangle[0]
            top_left = (top_left[0] + 10, top_left[1] - 15)
            info_box = img_rects_draw.textbbox(top_left, info_text, font=font, align="left")
            img_rects_draw.rectangle(info_box, fill=(0, 255, 255, 100))
            img_rects_draw.text(top_left, info_text, fill=text_color, font=font, align="left")

        color_index += 1
        if color_index == len(COLORS):
            color_index = 0

    final_image = Image.alpha_composite(pil_image, overlay)
    final_image.save(annotated_img_file)


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
    if (
        annotated_img_file.is_file()
        and annotated_img_file.stat().st_mtime > ocr_file.stat().st_mtime
    ):
        logger.info(f'Found annotation file - skipping: "{annotated_img_file}".')
        return

    logger.info(
        f'Annotating image with individual boxes "{png_file}" from ocr file "{ocr_file}"...'
    )

    # scale = 8700 / 9900
    # json_text_data_boxes = get_json_text_data_boxes(ocr_file)
    # for group in json_text_data_boxes["groups"]:
    #     for box_id in json_text_data_boxes["groups"][group]["cleaned_box_texts"]:
    #         text_data = json_text_data_boxes["groups"][group]["cleaned_box_texts"][box_id]
    #         text_box = text_data["text_box"]
    #         if text_box is None:
    #             continue
    #         text_data["text_box"] = [(item[0] * scale, item[1] * scale) for item in text_box]
    # with ocr_file.open("w") as f:
    #     json.dump(json_text_data_boxes, f, indent=4)

    json_text_data_boxes = get_json_text_data_boxes(ocr_file)["groups"]
    bw_image = get_image_to_annotate(png_file)

    pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image]))
    img_rects_draw = ImageDraw.Draw(pil_image)

    for group in json_text_data_boxes:
        group_id = int(group)

        for box_id in json_text_data_boxes[group]["cleaned_box_texts"]:
            text_data = json_text_data_boxes[group]["cleaned_box_texts"][box_id]

            text_box = text_data["text_box"]
            if text_box is None:
                logger.warning(f"No text box found for group {group_id} and box_id {box_id}.")
                continue

            try:
                ocr_box = OcrBox(
                    text_box,
                    text_data["text_frag"],
                    0.0,
                    "N/A",
                )
            except Exception as e:
                logger.error(f"OcrBox error occurred for text_data: {text_data}")
                raise e from e

            if ocr_box.is_approx_rect:
                img_rects_draw.rectangle(
                    ocr_box.min_rotated_rectangle, outline=get_color(group_id), width=4
                )
            else:
                box = [item for point in ocr_box.min_rotated_rectangle for item in point]
                img_rects_draw.polygon(box, outline=get_color(group_id), width=2)

    # noinspection PyProtectedMember
    img_rects_draw._image.save(annotated_img_file)  # noqa: SLF001


app = typer.Typer()
log_level = ""
log_filename = "show-ocr.log"


@app.command(help="Make final ai groups")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    # Global variable accessed by loguru-config.
    global log_level  # noqa: PLW0603
    log_level = log_level_str
    LoguruConfig.load(Path(__file__).parent / "log-config.yaml")

    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()

    ocr_annotate_titles(comics_database, get_titles(comics_database, volumes, title_str))


if __name__ == "__main__":
    app()

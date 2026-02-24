import json
from pathlib import Path
from typing import Any

import cv2 as cv
import typer
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT
from barks_fantagraphics.comic_book import ComicBook
from barks_fantagraphics.comics_consts import PNG_FILE_EXT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import draw_panel_bounds_on_image, get_titles
from barks_fantagraphics.ocr_file_paths import OCR_ANNOTATIONS_DIR
from barks_fantagraphics.panel_boxes import TitlePanelBoxes, check_page_panel_boxes
from barks_fantagraphics.speech_groupers import SpeechGroups, SpeechPageGroup
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from intspan import intspan
from loguru import logger
from loguru_config import LoguruConfig
from PIL import Image, ImageColor, ImageDraw, ImageFont

import barks_ocr.log_setup as _log_setup
from barks_ocr.utils.ocr_box import OcrBox

_RESOURCES = Path(__file__).parent.parent / "resources"

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

DEFAULT_FONT_PATH = Path("/home/greg/Prj/fonts/verdana.ttf")
DEFAULT_FONT_SIZE = 28
TEXT_TYPE_ABBREV_MAP = {
    "narration": "N",
    "background": "B",
    "dialogue": "D",
    "thought": "T",
    "sound effect": "S",
    "sound_effect": "S",
}


def get_color(group_id: int) -> str:
    group_id %= len(COLORS)
    return COLORS[group_id]


def ocr_annotate_titles(
    speech_groups: SpeechGroups,
    title_panel_boxes: TitlePanelBoxes,
    comics_database: ComicsDatabase,
    title_list: list[str],
) -> None:
    for title_str in title_list:
        volume = comics_database.get_fanta_volume_int(title_str)
        volume_dirname = comics_database.get_fantagraphics_volume_title(volume)
        out_image_dir = OCR_ANNOTATIONS_DIR / volume_dirname
        comic = comics_database.get_comic_book(title_str)

        ocr_annotate_title(speech_groups, title_panel_boxes, comic, out_image_dir)


def ocr_annotate_title(
    speech_groups: SpeechGroups,
    title_panel_boxes: TitlePanelBoxes,
    comic: ComicBook,
    out_image_dir: Path,
) -> None:
    title_str = comic.get_ini_title()

    out_image_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f'OCR annotating all pages in "{title_str}" to directory "{out_image_dir}"...')

    title = BARKS_TITLE_DICT[title_str]
    title_speech_page_groups = speech_groups.get_speech_page_groups(title)
    title_pages_panel_boxes = title_panel_boxes.get_page_panel_boxes(title)
    for speech_page_group in title_speech_page_groups:
        fanta_page = speech_page_group.fanta_page
        ocr_type = speech_page_group.ocr_index

        svg_file = comic.get_srce_restored_svg_story_file(fanta_page)
        png_file = Path(str(svg_file) + PNG_FILE_EXT)
        ocr_group_file = comic.get_ocr_prelim_groups_json_file(fanta_page, ocr_type)
        prelim_text_annotated_image_file = comic.get_ocr_prelim_annotated_file(fanta_page, ocr_type)
        boxes_annotated_image_file = comic.get_ocr_boxes_annotated_file(fanta_page, ocr_type)

        if (
            prelim_text_annotated_image_file.is_file()
            and prelim_text_annotated_image_file.stat().st_mtime > ocr_group_file.stat().st_mtime
        ):
            logger.info(
                f'Found prelim annotated file - skipping: "{prelim_text_annotated_image_file}".'
            )
            continue

        bw_image = get_image_to_annotate(png_file)
        pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image])).convert("RGBA")

        page_panel_boxes = title_pages_panel_boxes.pages[fanta_page]
        check_page_panel_boxes(pil_image.size, page_panel_boxes)
        draw_panel_bounds_on_image(pil_image, page_panel_boxes)

        ocr_annotate_image_with_prelim_text(
            speech_page_group, pil_image, prelim_text_annotated_image_file
        )
        ocr_annotate_image_with_individual_boxes(
            pil_image, ocr_group_file, boxes_annotated_image_file
        )


def get_image_to_annotate(png_file: Path) -> cv.typing.MatLike:
    if not png_file.is_file():
        msg = f'Could not find image file "{png_file}".'
        raise FileNotFoundError(msg)

    return get_bw_image_from_alpha(png_file)


def ocr_annotate_image_with_prelim_text(
    speech_page_group: SpeechPageGroup,
    pil_image: Image.Image,
    annotated_img_file: Path,
) -> None:
    logger.info(f'Annotating image "{annotated_img_file}"...')

    speech_groups = speech_page_group.speech_groups

    overlay = Image.new("RGBA", pil_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.truetype(str(DEFAULT_FONT_PATH), DEFAULT_FONT_SIZE)

    color_index = 0
    for group_id, speech_text in speech_groups.items():
        logger.info(f'Annotating group "{group_id}"...')

        text_box = speech_text.text_box
        panel_num = speech_text.panel_num

        ocr_box = OcrBox(
            text_box,
            speech_text.raw_ai_text,
            1.0,
            speech_text.raw_ai_text,
        )
        bbox_color = (*ImageColor.getrgb(COLORS[color_index]), 255)
        text_box_color = (*ImageColor.getrgb(COLORS[color_index]), 50)
        draw.rectangle(ocr_box.min_rotated_rectangle, outline=bbox_color, width=7)

        text_color = "red"
        text = f"{speech_text.raw_ai_text}"
        top_left = ocr_box.min_rotated_rectangle[0]
        top_left = (top_left[0] + 30, ocr_box.min_rotated_rectangle[1][1] + 5)
        text_box = draw.textbbox(top_left, text, font=font, align="left")
        draw.rectangle(text_box, fill=text_box_color)
        draw.text(top_left, text, fill=text_color, font=font, align="left", stroke_width=1)

        if panel_num != -1:
            info_text = f"{panel_num}:{get_text_type_abbrev(speech_text.type)}"
            top_left = ocr_box.min_rotated_rectangle[0]
            top_left = (top_left[0] + 10, top_left[1] - 25)
            info_box = draw.textbbox(top_left, info_text, font=font, align="left")
            draw.rectangle(info_box, fill=(0, 255, 255, 80))
            info_font = ImageFont.truetype(str(DEFAULT_FONT_PATH), int(1.35 * DEFAULT_FONT_SIZE))
            info_text_color = "blue"
            draw.text(
                top_left,
                info_text,
                fill=info_text_color,
                font=info_font,
                align="left",
                stroke_width=1.5,
            )

        color_index += 1
        if color_index == len(COLORS):
            color_index = 0

    final_image = Image.alpha_composite(pil_image, overlay)
    final_image.save(annotated_img_file)


def get_text_type_abbrev(text_type: str) -> str:
    return TEXT_TYPE_ABBREV_MAP.get(text_type, "?")


def ocr_annotate_image_with_individual_boxes(
    pil_image: Image.Image, ocr_file: Path, annotated_img_file: Path
) -> None:
    if (
        annotated_img_file.is_file()
        and annotated_img_file.stat().st_mtime > ocr_file.stat().st_mtime
    ):
        logger.info(f'Found annotation file - skipping: "{annotated_img_file}".')
        return

    logger.info(
        f"Annotating image with individual boxes"
        f' "{annotated_img_file}" from ocr file "{ocr_file}"...'
    )

    json_ocr_groups = get_json_ocr_groups(ocr_file)["groups"]

    draw = ImageDraw.Draw(pil_image)

    for group in json_ocr_groups:
        group_id = int(group)

        for box_id in json_ocr_groups[group]["cleaned_box_texts"]:
            text_data = json_ocr_groups[group]["cleaned_box_texts"][box_id]

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
                draw.rectangle(ocr_box.min_rotated_rectangle, outline=get_color(group_id), width=4)
            else:
                box = [item for point in ocr_box.min_rotated_rectangle for item in point]
                draw.polygon(box, outline=get_color(group_id), width=2)

    pil_image.save(annotated_img_file)


def get_json_ocr_groups(ocr_file: Path) -> dict[str, Any]:
    if not ocr_file.is_file():
        msg = f'Could not find ocr file "{ocr_file}".'
        raise RuntimeError(msg)

    with ocr_file.open("r") as f:
        return json.load(f)


app = typer.Typer()


@app.command(help="Annotate prelim ocr groups")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    _log_setup.log_level = log_level_str
    _log_setup.log_filename = "show-ocr.log"
    _log_setup.APP_LOGGING_NAME = APP_LOGGING_NAME
    LoguruConfig.load(_RESOURCES / "log-config.yaml")

    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)

    volumes = list(intspan(volumes_str))
    comics_database = ComicsDatabase()

    speech_groups = SpeechGroups(comics_database)
    title_panel_boxes = TitlePanelBoxes(comics_database)
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    ocr_annotate_titles(speech_groups, title_panel_boxes, comics_database, title_list)


if __name__ == "__main__":
    app()

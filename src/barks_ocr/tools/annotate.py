import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import cv2 as cv
import typer
from barks_fantagraphics.barks_titles import BARKS_TITLES
from barks_fantagraphics.comic_book import ComicBook
from barks_fantagraphics.comics_consts import CARL_BARKS_FONT_FILE, PNG_FILE_EXT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import draw_panel_bounds_on_image
from barks_fantagraphics.panel_boxes import TitlePanelBoxes, check_page_panel_boxes
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups, SpeechPageGroup, SpeechText
from comic_utils.common_typer_options import LogLevelArg, TitleArg
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from comic_utils.kivy_page_viewer import KivyPageViewer
from loguru import logger
from PIL import Image, ImageColor, ImageDraw, ImageFont
from PIL.ImageDraw import ImageDraw as PilImageDraw
from PIL.ImageFont import FreeTypeFont

from barks_ocr.cli_setup import init_logging
from barks_ocr.utils.ocr_box import OcrBox

APP_LOGGING_NAME = "anno"

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

TEXT_TYPE_ABBREV_MAP = {
    "narration": "N",
    "background": "B",
    "dialogue": "D",
    "thought": "T",
    "sound effect": "S",
    "sound_effect": "S",
    "title": "H",
}

TEXT_FONT_PATH = CARL_BARKS_FONT_FILE
TEXT_FONT_SIZE = 28
TEXT_COLOR = "purple"
TEXT_BOUNDING_BOX_OFFSET = (20, 20)

INFO_FONT_PATH = Path("/home/greg/Prj/fonts/verdana.ttf")
INFO_FONT_SIZE = 28
INFO_TEXT_COLOR = "blue"
INFO_BOUNDING_BOX_OFFSET = (10, -25)


def get_color(group_id: int) -> str:
    return COLORS[group_id % len(COLORS)]


def get_text_type_abbrev(text_type: str) -> str:
    return TEXT_TYPE_ABBREV_MAP.get(text_type, "?")


def get_json_ocr_groups(ocr_file: Path) -> dict[str, Any]:
    if not ocr_file.is_file():
        msg = f'Could not find ocr file "{ocr_file}".'
        raise RuntimeError(msg)

    with ocr_file.open("r") as f:
        return json.load(f)


def _build_prelim_annotated_image(
    speech_page_group: SpeechPageGroup, pil_image: Image.Image
) -> Image.Image:
    """Compose the prelim text overlay onto ``pil_image`` and return a new RGBA image."""
    speech_groups_map = speech_page_group.speech_groups

    overlay = Image.new("RGBA", pil_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    text_font = ImageFont.truetype(str(TEXT_FONT_PATH), TEXT_FONT_SIZE)
    info_font = ImageFont.truetype(str(INFO_FONT_PATH), int(1.35 * INFO_FONT_SIZE))

    color_index = 0
    for group_id, speech_text in speech_groups_map.items():
        logger.debug(f'Annotating group "{group_id}".')

        ocr_text_box = draw_speech_text(color_index, draw, speech_text, text_font)

        if speech_text.panel_num != -1:
            draw_info_text(draw, ocr_text_box, speech_text, info_font)

        color_index += 1
        if color_index == len(COLORS):
            color_index = 0

    return Image.alpha_composite(pil_image, overlay)


def draw_speech_text(
    color_index: int, draw: PilImageDraw, speech_text: SpeechText, text_font: FreeTypeFont
) -> OcrBox:
    ocr_box = OcrBox(
        speech_text.text_box,
        speech_text.raw_ai_text,
        1.0,
        speech_text.raw_ai_text,
    )
    bbox_color = (*ImageColor.getrgb(COLORS[color_index]), 255)
    text_box_color = (*ImageColor.getrgb(COLORS[color_index]), 50)
    draw.rectangle(ocr_box.min_rotated_rectangle, outline=bbox_color, width=7)

    text = f"{speech_text.raw_ai_text}"
    top_left = (
        ocr_box.min_rotated_rectangle[0][0] + TEXT_BOUNDING_BOX_OFFSET[0],
        ocr_box.min_rotated_rectangle[1][1] + TEXT_BOUNDING_BOX_OFFSET[1],
    )
    text_bbox = draw.textbbox(top_left, text, font=text_font, align="left")
    draw.rectangle(text_bbox, fill=text_box_color)
    draw.text(top_left, text, fill=TEXT_COLOR, font=text_font, align="left", stroke_width=1)
    return ocr_box


def draw_info_text(
    draw: PilImageDraw, ocr_text_box: OcrBox, speech_text: SpeechText, info_font: FreeTypeFont
) -> None:
    info_text = f"{speech_text.panel_num}:{get_text_type_abbrev(speech_text.type)}"
    top_left = ocr_text_box.min_rotated_rectangle[0]
    top_left = (
        top_left[0] + INFO_BOUNDING_BOX_OFFSET[0],
        top_left[1] + INFO_BOUNDING_BOX_OFFSET[1],
    )
    info_box = draw.textbbox(top_left, info_text, font=info_font, align="left")
    draw.rectangle(info_box, fill=(0, 255, 255, 80))
    draw.text(
        top_left,
        info_text,
        fill=INFO_TEXT_COLOR,
        font=info_font,
        align="left",
        stroke_width=1.5,
    )


def _draw_individual_boxes_on_image(pil_image: Image.Image, ocr_file: Path) -> None:
    """Mutate ``pil_image`` in place: draw individual OCR box outlines from ``ocr_file``."""
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
            except Exception:
                logger.exception(f"OcrBox error occurred for text_data: {text_data}")
                raise

            if ocr_box.is_approx_rect:
                draw.rectangle(ocr_box.min_rotated_rectangle, outline=get_color(group_id), width=4)
            else:
                box = [item for point in ocr_box.min_rotated_rectangle for item in point]
                draw.polygon(box, outline=get_color(group_id), width=2)


def _save_if_outdated(image: Image.Image, dst_file: Path, src_file: Path, label: str) -> None:
    """Save ``image`` to ``dst_file`` unless ``dst_file`` is already newer than ``src_file``."""
    if dst_file.is_file() and dst_file.stat().st_mtime > src_file.stat().st_mtime:
        logger.info(f'Found {label} file - skipping: "{dst_file}".')
        return

    dst_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f'Saving {label} image to "{dst_file}".')
    image.save(dst_file)


def _build_annotated_pages(
    speech_groups: SpeechGroups,
    title_panel_boxes: TitlePanelBoxes,
    comic: ComicBook,
    engine: OcrTypes,
    save: bool,
) -> list[tuple[str, Image.Image]]:
    title_enum = comic.get_title_enum()
    title_speech_page_groups = speech_groups.get_speech_page_groups(title_enum)
    title_pages_panel_boxes = title_panel_boxes.get_page_panel_boxes(title_enum)

    filtered = [g for g in title_speech_page_groups if g.ocr_index == engine]

    def process(speech_page_group: SpeechPageGroup) -> tuple[str, Image.Image]:
        fanta_page = speech_page_group.fanta_page

        svg_file = comic.get_srce_restored_svg_story_file(fanta_page)
        png_file = Path(str(svg_file) + PNG_FILE_EXT)
        if not png_file.is_file():
            msg = f'Page PNG not found: "{png_file}".'
            raise FileNotFoundError(msg)

        bw_image = get_bw_image_from_alpha(png_file)
        if bw_image is None or bw_image.size == 0:
            msg = f'Could not decode page PNG: "{png_file}".'
            raise RuntimeError(msg)
        pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image])).convert("RGBA")

        page_panel_boxes = title_pages_panel_boxes.pages[fanta_page]
        check_page_panel_boxes(pil_image.size, page_panel_boxes)
        draw_panel_bounds_on_image(pil_image, page_panel_boxes)

        prelim_image = _build_prelim_annotated_image(speech_page_group, pil_image)

        if save:
            ocr_group_file = comic.get_ocr_prelim_groups_json_file(fanta_page, engine)
            prelim_file = comic.get_ocr_prelim_annotated_file(fanta_page, engine)
            boxes_file = comic.get_ocr_boxes_annotated_file(fanta_page, engine)
            _save_if_outdated(prelim_image, prelim_file, ocr_group_file, "prelim annotated")
            _draw_individual_boxes_on_image(pil_image, ocr_group_file)
            _save_if_outdated(pil_image, boxes_file, ocr_group_file, "boxes annotated")

        return fanta_page, prelim_image

    with ThreadPoolExecutor() as executor:
        return list(executor.map(process, filtered))


def show_ocr_annotations(  # noqa: PLR0913
    comics_database: ComicsDatabase,
    title: str,
    engine: OcrTypes,
    start_page: int,
    save: bool,
    win_left: int,
    win_top: int,
) -> None:
    """Display prelim OCR annotations for ``title`` in a Kivy viewer window.

    Args:
        comics_database: The comics database used to resolve the title.
        title: The Barks title to display.
        engine: OCR engine whose prelim annotated images to show.
        start_page: 1-based page index to show first. Clamped to the available range.
        save: When True, also save prelim + boxes annotated PNG files (with mtime skip).
        win_left: Window left position in pixels.
        win_top: Window top position in pixels.

    """
    logger.info(f'Showing OCR annotations [{engine.value}] for "{title}"...')

    speech_groups = SpeechGroups(comics_database)
    title_panel_boxes = TitlePanelBoxes(comics_database)
    comic = comics_database.get_comic_book(title)

    pages = _build_annotated_pages(speech_groups, title_panel_boxes, comic, engine, save)
    if not pages:
        title_name = BARKS_TITLES[comic.get_title_enum()]
        logger.error(f'No prelim OCR pages for engine "{engine.value}" in title "{title_name}".')
        return

    KivyPageViewer(
        window_title=f"OCR annotations [{engine.value}] — {title}",
        pages=pages,
        start_page=start_page,
        win_left=win_left,
        win_top=win_top,
    ).run()


app = typer.Typer()


@app.command(help="Show prelim OCR annotated images for a title")
def main(  # noqa: PLR0913
    title_str: TitleArg,
    engine: OcrTypes = typer.Option(  # noqa: B008
        ..., "--engine", "-e", help="OCR engine to display."
    ),
    page: int = typer.Option(1, "--page", "-p", help="Page number to start on (1-based)."),
    save: bool = typer.Option(default=False, help="Also save prelim + boxes annotated PNGs."),
    win_left: int = typer.Option(100, "--win-left", help="Window left position in pixels."),
    win_top: int = typer.Option(80, "--win-top", help="Window top position in pixels."),
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    init_logging(APP_LOGGING_NAME, "annotate-ocr.log", log_level_str)

    comics_database = ComicsDatabase()

    show_ocr_annotations(comics_database, title_str, engine, page, save, win_left, win_top)


if __name__ == "__main__":
    app()

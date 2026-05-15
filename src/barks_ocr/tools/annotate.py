import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
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
from barks_kivy_ui.page_viewer import KivyPageViewer
from comic_utils.common_typer_options import LogLevelArg, TitleArg
from comic_utils.cv_image_utils import get_bw_image_from_alpha
from kivy.graphics import Color, Rectangle
from kivy.input.motionevent import MotionEvent
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label as KivyLabel
from kivy.uix.widget import Widget
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
TEXT_COLOR = "#000000"
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


@dataclass(frozen=True, slots=True)
class SpeechLabel:
    """Spec for a draggable speech-text label in the viewer.

    ``image_xy`` is the top-left position in PIL image pixel coords (top-left origin).
    """

    text: str
    image_xy: tuple[int, int]


def _build_prelim_annotated_image(
    speech_page_group: SpeechPageGroup, pil_image: Image.Image, save: bool
) -> tuple[Image.Image, Image.Image | None, list[SpeechLabel]]:
    """Compose prelim annotations onto ``pil_image``.

    Returns:
        display_image: ``pil_image`` with OCR boxes and info-tag baked in but the speech
            text drawn separately (shown as movable Kivy labels by the viewer).
        save_image: full annotation with speech text also baked in, or ``None`` when
            ``save`` is False.
        speech_labels: position/text specs for the viewer to render as draggable labels.

    """
    speech_groups_map = speech_page_group.speech_groups

    display_overlay = Image.new("RGBA", pil_image.size, (0, 0, 0, 0))
    display_draw = ImageDraw.Draw(display_overlay)
    text_overlay = Image.new("RGBA", pil_image.size, (0, 0, 0, 0)) if save else None
    text_draw = ImageDraw.Draw(text_overlay) if text_overlay is not None else None

    text_font = ImageFont.truetype(str(TEXT_FONT_PATH), TEXT_FONT_SIZE)
    info_font = ImageFont.truetype(str(INFO_FONT_PATH), int(1.35 * INFO_FONT_SIZE))

    speech_labels: list[SpeechLabel] = []
    color_index = 0
    for group_id, speech_text in speech_groups_map.items():
        logger.debug(f'Annotating group "{group_id}".')

        ocr_box, text_top_left = draw_speech_box(color_index, display_draw, speech_text)

        speech_labels.append(SpeechLabel(text=speech_text.raw_ai_text, image_xy=text_top_left))

        if text_draw is not None:
            bake_speech_text(text_draw, text_top_left, speech_text, text_font, color_index)

        if speech_text.panel_num != -1:
            draw_info_text(display_draw, ocr_box, speech_text, info_font)

        color_index += 1
        if color_index == len(COLORS):
            color_index = 0

    display_image = Image.alpha_composite(pil_image, display_overlay)
    save_image = (
        Image.alpha_composite(display_image, text_overlay) if text_overlay is not None else None
    )
    return display_image, save_image, speech_labels


def draw_speech_box(
    color_index: int, draw: PilImageDraw, speech_text: SpeechText
) -> tuple[OcrBox, tuple[int, int]]:
    """Draw the coloured rectangle around the OCR box. Returns the box and text top-left."""
    ocr_box = OcrBox(
        speech_text.text_box,
        speech_text.raw_ai_text,
        1.0,
        speech_text.raw_ai_text,
    )
    bbox_color = (*ImageColor.getrgb(COLORS[color_index]), 255)
    draw.rectangle(ocr_box.min_rotated_rectangle, outline=bbox_color, width=7)

    text_top_left = (
        int(ocr_box.min_rotated_rectangle[0][0]) + TEXT_BOUNDING_BOX_OFFSET[0],
        int(ocr_box.min_rotated_rectangle[1][1]) + TEXT_BOUNDING_BOX_OFFSET[1],
    )
    return ocr_box, text_top_left


def bake_speech_text(
    draw: PilImageDraw,
    top_left: tuple[int, int],
    speech_text: SpeechText,
    text_font: FreeTypeFont,
    color_index: int,  # noqa: ARG001
) -> None:
    """Draw the speech text and its background rectangle onto ``draw`` (for save mode)."""
    text = f"{speech_text.raw_ai_text}"
    text_bbox = draw.textbbox(top_left, text, font=text_font, align="left")
    draw.rectangle(text_bbox, fill=(255, 255, 255, 255))
    draw.text(top_left, text, fill=TEXT_COLOR, font=text_font, align="left", stroke_width=1)


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
) -> list[tuple[str, Image.Image, list[SpeechLabel]]]:
    title_enum = comic.get_title_enum()
    title_speech_page_groups = speech_groups.get_speech_page_groups(title_enum)
    title_pages_panel_boxes = title_panel_boxes.get_page_panel_boxes(title_enum)

    filtered = [g for g in title_speech_page_groups if g.ocr_index == engine]

    def process(
        speech_page_group: SpeechPageGroup,
    ) -> tuple[str, Image.Image, list[SpeechLabel]]:
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

        display_image, save_image, speech_labels = _build_prelim_annotated_image(
            speech_page_group, pil_image, save
        )

        if save:
            assert save_image is not None
            ocr_group_file = comic.get_ocr_prelim_groups_json_file(fanta_page, engine)
            prelim_file = comic.get_ocr_prelim_annotated_file(fanta_page, engine)
            boxes_file = comic.get_ocr_boxes_annotated_file(fanta_page, engine)
            _save_if_outdated(save_image, prelim_file, ocr_group_file, "prelim annotated")
            _draw_individual_boxes_on_image(pil_image, ocr_group_file)
            _save_if_outdated(pil_image, boxes_file, ocr_group_file, "boxes annotated")

        return fanta_page, display_image, speech_labels

    with ThreadPoolExecutor() as executor:
        return list(executor.map(process, filtered))


class _DraggableLabel(KivyLabel):
    """Kivy Label with a white background, drag-movable by the user."""

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        super().__init__(**kwargs)
        self.dragged = False
        self._drag_offset = (0.0, 0.0)
        with self.canvas.before:  # ty: ignore[unresolved-attribute]
            Color(1.0, 0.97, 0.78, 0.95)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *_args: object) -> None:
        self._bg.pos = self.pos
        self._bg.size = self.size

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if not self.collide_point(*touch.pos):
            return False
        if getattr(touch, "button", "left") != "left":
            return False
        touch.grab(self)
        self._drag_offset = (touch.x - self.x, touch.y - self.y)
        return True

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not self:
            return False
        self.pos = (touch.x - self._drag_offset[0], touch.y - self._drag_offset[1])
        self.dragged = True
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        return True


class _OcrAnnotationsViewer(KivyPageViewer):
    """Page viewer that overlays draggable Kivy labels for the speech text."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        window_title: str,
        pages: list[tuple[str, Image.Image]],
        page_speech_labels: list[list[SpeechLabel]],
        start_page: int,
        win_left: int,
        win_top: int,
    ) -> None:
        super().__init__(
            window_title=window_title,
            pages=pages,
            start_page=start_page,
            win_left=win_left,
            win_top=win_top,
        )
        self._page_speech_labels = page_speech_labels
        self._overlay: FloatLayout | None = None

    def build(self) -> Widget:
        root = super().build()
        # Replace the image widget with a FloatLayout that holds it plus draggable labels.
        assert self._image_widget is not None
        parent = self._image_widget.parent
        assert parent is not None
        parent.remove_widget(self._image_widget)
        self._overlay = FloatLayout(size_hint=(1, 1))
        self._image_widget.size_hint = (1, 1)
        self._image_widget.pos_hint = {"x": 0, "y": 0}
        self._overlay.add_widget(self._image_widget)
        parent.add_widget(self._overlay)
        # When the image widget resizes (initial layout / window resize), refresh labels.
        self._image_widget.bind(size=lambda *_a: self._refresh_label_positions())
        # The overlay didn't exist when super().build() called _show_current(); populate now.
        self._rebuild_labels_for_current_page()
        return root

    def _show_current(self) -> None:
        super()._show_current()
        self._rebuild_labels_for_current_page()

    def _rebuild_labels_for_current_page(self) -> None:
        if self._overlay is None or self._image_widget is None:
            return
        for child in list(self._overlay.children):
            if child is not self._image_widget:
                self._overlay.remove_widget(child)
        rgb = ImageColor.getrgb(TEXT_COLOR)
        text_color_kivy = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, 1.0)
        for spec in self._page_speech_labels[self._index]:
            label = _DraggableLabel(
                text=spec.text,
                font_name=str(TEXT_FONT_PATH),
                font_size=TEXT_FONT_SIZE / 2.0,
                bold=True,
                color=text_color_kivy,
                size_hint=(None, None),
            )
            # Stash the source image-pixel position so we can re-project on resize.
            label.image_xy = spec.image_xy  # type: ignore[attr-defined]
            # Size to fit text once the texture renders, and refresh position afterwards.
            label.bind(texture_size=lambda lbl, val: setattr(lbl, "size", val))
            label.bind(size=lambda lbl, _val: self._reposition_label(lbl))
            self._overlay.add_widget(label)
        self._refresh_label_positions()

    def _refresh_label_positions(self) -> None:
        if self._overlay is None:
            return
        for child in self._overlay.children:
            if isinstance(child, _DraggableLabel):
                self._reposition_label(child)

    def _reposition_label(self, label: _DraggableLabel) -> None:
        if label.dragged or self._image_widget is None or not self._pages:
            return
        _, pil_image = self._pages[self._index]
        src_w, src_h = pil_image.size
        widget_w, widget_h = self._image_widget.size
        if src_w <= 0 or src_h <= 0 or widget_w <= 0 or widget_h <= 0:
            return
        scale = min(widget_w / src_w, widget_h / src_h)
        letterbox_x = (widget_w - src_w * scale) / 2
        letterbox_y = (widget_h - src_h * scale) / 2
        px, py = label.image_xy  # type: ignore[attr-defined]
        wx = self._image_widget.x + letterbox_x + px * scale
        wy = self._image_widget.top - letterbox_y - py * scale
        # Position by top-left, accounting for label's current height.
        label.pos = (wx, wy - label.height)


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

    page_entries = _build_annotated_pages(speech_groups, title_panel_boxes, comic, engine, save)
    if not page_entries:
        title_name = BARKS_TITLES[comic.get_title_enum()]
        logger.error(f'No prelim OCR pages for engine "{engine.value}" in title "{title_name}".')
        return

    pages = [(fanta_page, image) for fanta_page, image, _ in page_entries]
    page_speech_labels = [labels for _, _, labels in page_entries]

    _OcrAnnotationsViewer(
        window_title=f"OCR annotations [{engine.value}] — {title}",
        pages=pages,
        page_speech_labels=page_speech_labels,
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

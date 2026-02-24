# ruff: noqa: E402
import json
from collections.abc import Callable
from io import BytesIO
from pathlib import Path

import typer
from attr import dataclass
from barks_fantagraphics.barks_titles import BARKS_TITLE_DICT, BARKS_TITLES
from barks_fantagraphics.comic_book import get_page_str
from barks_fantagraphics.comics_consts import FONT_DIR, OPEN_SANS_FONT
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page
from barks_fantagraphics.comics_utils import get_backup_file
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import OcrTypes, get_speech_page_group
from comic_utils.comic_consts import PNG_FILE_EXT
from comic_utils.common_typer_options import LogLevelArg
from comic_utils.pil_image_utils import load_pil_image_for_reading
from kivy.config import Config
from loguru import logger
from loguru_config import LoguruConfig
from PIL import Image as PilImage

import barks_ocr.log_setup as _log_setup

APP_LOGGING_NAME = "kpoe"

# Set the main window size using variables
MAIN_WINDOW_X = 200
MAIN_WINDOW_Y = 20
MAIN_WINDOW_WIDTH = 2000
MAIN_WINDOW_HEIGHT = 1480

Config.set("graphics", "position", "custom")  # ty:ignore[unresolved-attribute]
Config.set("graphics", "left", MAIN_WINDOW_X)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "top", MAIN_WINDOW_Y)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "width", MAIN_WINDOW_WIDTH)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "height", MAIN_WINDOW_HEIGHT)  # ty:ignore[unresolved-attribute]

from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle

# noinspection PyUnresolvedReferences
from kivy.properties import (  # ty:ignore[unresolved-import]
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

_RESOURCES = Path(__file__).parent.parent / "resources"

# Kivy 2.3.1 bug: textinput.py calls canvas._remove_group() but Canvas only
# exposes remove_group() (no leading underscore). Patch the alias in.
import inspect as _inspect
import textwrap as _textwrap

import kivy.uix.textinput as _ki_textinput
from kivy.uix.textinput import TextInput as _TextInput

if not hasattr(_TextInput, "_kivy_patch_applied"):
    # Kivy 2.3.1 bug: TextInput._update_graphics_selection calls
    # canvas._remove_group() but Canvas (Cython) only exposes remove_group().
    # Re-compile the method with the correct name.
    # noinspection PyProtectedMember
    _src = _textwrap.dedent(_inspect.getsource(_TextInput._update_graphics_selection))  # noqa: SLF001
    _src = _src.replace("._remove_group(", ".remove_group(")
    _ns: dict = vars(_ki_textinput).copy()
    exec(compile(_src, "<kivy_patch>", "exec"), _ns)  # noqa: S102
    _TextInput._update_graphics_selection = _ns["_update_graphics_selection"]  # noqa: SLF001
    _TextInput._kivy_patch_applied = True  # type: ignore[attr-defined]  # noqa: SLF001

# TODO: Duplicated in 'font_manager.py'.
# Set up custom fonts.
LabelBase.register(
    name=OPEN_SANS_FONT,
    fn_regular=str(FONT_DIR / "OpenSans-Medium.ttf"),
    fn_bold=str(FONT_DIR / "OpenSans-Bold.ttf"),
    fn_italic=str(FONT_DIR / "OpenSans-MediumItalic.ttf"),
    fn_bolditalic=str(FONT_DIR / "OpenSans-BoldItalic.ttf"),
)

EASY_OCR = "EasyOCR"
PADDLE_OCR = "PaddleOCR"
MAX_NUM_PANELS = 8

# Pixels of context padding around the enlarged crop region
CROP_PADDING = 150
# Extra padding used when panel_num is -1 (unassigned) — shows more page context
CROP_PADDING_UNKNOWN = 400
# Screen-space radius (px) for corner drag handles on the bounding box
HANDLE_RADIUS = 14


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class SpeechItem:
    panel_num: int
    group_id: str
    text: str


@dataclass
class QueueEntry:
    volume: int
    fanta_page: int
    engine: str  # "easyocr" or "paddleocr"
    group_id: int


# ── Helper functions ──────────────────────────────────────────────────────────


def load_queue_file(queue_file: Path) -> list[QueueEntry]:
    """Parse a queue file; each line: volume page engine group_id."""
    entries = []
    for raw_line in queue_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 4:  # noqa: PLR2004
            logger.warning(f"Skipping invalid queue line: {line!r}")
            continue
        try:
            entries.append(
                QueueEntry(
                    volume=int(parts[0]),
                    fanta_page=int(parts[1]),
                    engine=parts[2].lower(),
                    group_id=int(parts[3]),
                )
            )
        except ValueError:
            logger.warning(f"Skipping invalid queue line: {line!r}")
    return entries


def get_panel_bounds_from_file(
    segments_file: Path, panel_num: int
) -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) of panel in image coords, or None."""
    if not segments_file.is_file() or panel_num <= 0:
        return None
    with segments_file.open() as f:
        info = json.load(f)
    panels = info.get("panels", [])
    if not (0 < panel_num <= len(panels)):
        return None
    pb = panels[panel_num - 1]
    left, top = pb[0], pb[1]
    return left, top, left + pb[2], top + pb[3]


def get_all_panel_bounds_from_file(
    segments_file: Path,
) -> list[tuple[int, int, int, int]]:
    """Return (left, top, right, bottom) for every panel in the segments file."""
    if not segments_file.is_file():
        return []
    with segments_file.open() as f:
        info = json.load(f)
    panels = info.get("panels", [])
    result = []
    for pb in panels:
        left, top = pb[0], pb[1]
        result.append((left, top, left + pb[2], top + pb[3]))
    return result


def compute_crop_region(
    img_w: int,
    img_h: int,
    panel_bounds: tuple[int, int, int, int] | None,
    text_box: list,
    padding: int = CROP_PADDING,
) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) crop encompassing panel + text box + padding."""
    xs = [p[0] for p in text_box]
    ys = [p[1] for p in text_box]
    tb_l, tb_t, tb_r, tb_b = min(xs), min(ys), max(xs), max(ys)

    if panel_bounds:
        pl, pt, pr, pb = panel_bounds
        left = min(pl, tb_l)
        top = min(pt, tb_t)
        right = max(pr, tb_r)
        bottom = max(pb, tb_b)
    else:
        left, top, right, bottom = tb_l, tb_t, tb_r, tb_b

    left = max(0, int(left) - padding)
    top = max(0, int(top) - padding)
    right = min(img_w, int(right) + padding)
    bottom = min(img_h, int(bottom) + padding)
    return left, top, right, bottom


# ── BoundingBoxCanvas ─────────────────────────────────────────────────────────


class BoundingBoxCanvas(Widget):
    """Kivy widget showing a cropped image with a draggable/resizable bounding box.

    Image is displayed with fit_mode="contain" letterboxing.  All public
    coordinates are in **full-page PIL space** (y=0 at top).  Internally the
    widget works in crop-local PIL space and converts to/from Kivy screen
    space (y=0 at bottom) for drawing and touch handling.
    """

    def __init__(self, on_box_changed: Callable[[list], None], **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._texture = None
        self._img_w = 1
        self._img_h = 1
        self._crop_offset: tuple[int, int] = (0, 0)
        self._text_box: list | None = None  # crop-local PIL coords
        self._panel_bounds_local: tuple[int, int, int, int] | None = None
        # Set when panel_num is -1: all panels drawn as numbered overlays
        self._all_panel_bounds_local: list[tuple[int, int, int, int]] | None = None

        self._on_box_changed = on_box_changed

        # Computed each redraw
        self._scale = 1.0
        self._img_offset_x = 0.0
        self._img_offset_y = 0.0

        # Touch/drag state
        self._dragging = False
        self._drag_corner = -1  # -1 = body drag; 0-3 = corner index
        self._drag_start_tx = 0.0
        self._drag_start_ty = 0.0
        self._drag_start_box: list | None = None

        # Use a managed InstructionGroup so we never call canvas.clear(),
        # which would corrupt Kivy's internal canvas groups used by TextInput.
        self._draw_group = InstructionGroup()
        self.canvas.add(self._draw_group)

        self.bind(size=self._redraw, pos=self._redraw)

    def set_content(
        self,
        pil_image: PilImage.Image,
        text_box_full_page: list,
        crop_offset: tuple[int, int],
        panel_bounds_full_page: tuple[int, int, int, int] | None,
        all_panel_bounds_full_page: list[tuple[int, int, int, int]] | None = None,
    ) -> None:
        """Load a new image + bounding box.  All coords in full-page PIL space.

        When all_panel_bounds_full_page is provided the canvas shows numbered
        outlines for every panel instead of a single highlighted panel boundary.
        This is used when panel_num is -1 so the user can identify the panel.
        """
        self._img_w, self._img_h = pil_image.size
        self._crop_offset = crop_offset
        ox, oy = crop_offset
        raw = [[float(p[0]) - ox, float(p[1]) - oy] for p in text_box_full_page]
        # Normalize to axis-aligned rectangle: corners in TL, TR, BR, BL order.
        xs = [p[0] for p in raw]
        ys = [p[1] for p in raw]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        self._text_box = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        if panel_bounds_full_page:
            pl, pt, pr, pb = panel_bounds_full_page
            self._panel_bounds_local = (pl - ox, pt - oy, pr - ox, pb - oy)
        else:
            self._panel_bounds_local = None
        if all_panel_bounds_full_page:
            self._all_panel_bounds_local = [
                (pl - ox, pt - oy, pr - ox, pb - oy)
                for pl, pt, pr, pb in all_panel_bounds_full_page
            ]
        else:
            self._all_panel_bounds_local = None

        buf = BytesIO()
        pil_image.save(buf, format="png")
        buf.seek(0)
        self._texture = CoreImage(buf, ext="png").texture
        self._redraw()

    def get_text_box_full_page(self) -> list:
        """Return current text box in full-page PIL coords (rounded to int)."""
        if self._text_box is None:
            return []
        ox, oy = self._crop_offset
        return [[round(p[0] + ox), round(p[1] + oy)] for p in self._text_box]

    # ── coordinate helpers ────────────────────────────────────────────────────

    def _update_layout(self) -> None:
        w, h = self.size
        self._scale = min(w / self._img_w, h / self._img_h)
        disp_w = self._img_w * self._scale
        disp_h = self._img_h * self._scale
        self._img_offset_x = self.x + (w - disp_w) / 2
        self._img_offset_y = self.y + (h - disp_h) / 2

    def _local_to_screen(self, x: float, y: float) -> tuple[float, float]:
        """Crop-local PIL coords → Kivy screen coords."""
        sx = x * self._scale + self._img_offset_x
        # Flip Y: PIL y=0 is top; Kivy y=0 is bottom
        sy = (self._img_h - y) * self._scale + self._img_offset_y
        return sx, sy

    def _screen_to_local(self, sx: float, sy: float) -> tuple[float, float]:
        """Kivy screen coords → crop-local PIL coords."""
        x = (sx - self._img_offset_x) / self._scale
        y = self._img_h - (sy - self._img_offset_y) / self._scale
        return x, y

    # ── drawing ───────────────────────────────────────────────────────────────

    def _redraw(self, *_args: object) -> None:
        if self._texture is None:
            return
        self._update_layout()
        g = self._draw_group
        g.clear()
        g.add(Color(1, 1, 1, 1))
        g.add(
            Rectangle(
                texture=self._texture,
                pos=(self._img_offset_x, self._img_offset_y),
                size=(self._img_w * self._scale, self._img_h * self._scale),
            )
        )
        if self._all_panel_bounds_local:
            self._draw_all_panel_bounds(g)
        elif self._panel_bounds_local:
            self._draw_panel_bounds(g)
        if self._text_box:
            self._draw_text_box(g)

    def _draw_panel_bounds(self, g: InstructionGroup) -> None:
        pl, pt, pr, pb = self._panel_bounds_local
        tl = self._local_to_screen(pl, pt)
        tr = self._local_to_screen(pr, pt)
        br = self._local_to_screen(pr, pb)
        bl = self._local_to_screen(pl, pb)
        g.add(Color(0.2, 0.5, 1.0, 0.8))
        g.add(Line(points=[*tl, *tr, *br, *bl, *tl], width=2, dash_offset=6, dash_length=12))

    def _draw_all_panel_bounds(self, g: InstructionGroup) -> None:
        """Draw all panel outlines with numbered labels (used when panel_num is -1)."""
        for i, (pl, pt, pr, pb) in enumerate(self._all_panel_bounds_local):
            tl = self._local_to_screen(pl, pt)
            tr = self._local_to_screen(pr, pt)
            br = self._local_to_screen(pr, pb)
            bl = self._local_to_screen(pl, pb)
            g.add(Color(0.2, 0.8, 0.8, 0.7))
            g.add(Line(points=[*tl, *tr, *br, *bl, *tl], width=1.5, dash_offset=4, dash_length=8))
            # Draw panel number in the top-left corner of each panel
            lbl = CoreLabel(text=str(i + 1), font_size=18, bold=True)
            lbl.refresh()
            texture = lbl.texture
            if texture:
                # tl is the visual top of the panel (high Kivy y); place label inside
                tx = tl[0] + 4
                ty = tl[1] - texture.height - 4
                # Dark background for readability
                g.add(Color(0, 0, 0, 0.6))
                g.add(Rectangle(pos=(tx - 2, ty - 2), size=(texture.width + 4, texture.height + 4)))
                g.add(Color(0.2, 1.0, 1.0, 1.0))
                g.add(Rectangle(texture=texture, pos=(tx, ty), size=texture.size))

    def _draw_text_box(self, g: InstructionGroup) -> None:
        pts = [self._local_to_screen(p[0], p[1]) for p in self._text_box]
        # Box outline
        g.add(Color(1.0, 0.5, 0.0, 1.0))
        flat = [c for pt in pts for c in pt] + list(pts[0])
        g.add(Line(points=flat, width=2.5))
        # Corner handles
        g.add(Color(1.0, 1.0, 0.0, 1.0))
        for pt in pts:
            d = HANDLE_RADIUS
            g.add(Ellipse(pos=(pt[0] - d / 2, pt[1] - d / 2), size=(d, d)))

    # ── touch events ─────────────────────────────────────────────────────────

    def on_touch_down(self, touch: object) -> bool:
        if not self.collide_point(*touch.pos) or self._text_box is None:  # type: ignore[arg-type]
            return False
        pts = [self._local_to_screen(p[0], p[1]) for p in self._text_box]

        # Corner handle hit-test first
        for i, pt in enumerate(pts):
            dist = ((touch.x - pt[0]) ** 2 + (touch.y - pt[1]) ** 2) ** 0.5  # type: ignore[attr-defined]
            if dist <= HANDLE_RADIUS:
                self._dragging = True
                self._drag_corner = i
                self._drag_start_box = [list(p) for p in self._text_box]
                touch.grab(self)  # type: ignore[attr-defined]
                return True

        # Body drag
        if self._point_in_polygon(touch.x, touch.y, pts):  # type: ignore[attr-defined]
            self._dragging = True
            self._drag_corner = -1
            self._drag_start_tx = touch.x  # type: ignore[attr-defined]
            self._drag_start_ty = touch.y  # type: ignore[attr-defined]
            self._drag_start_box = [list(p) for p in self._text_box]
            touch.grab(self)  # type: ignore[attr-defined]
            return True

        return False

    def on_touch_move(self, touch: object) -> bool:
        if touch.grab_current is not self or not self._dragging:  # type: ignore[attr-defined]
            return False
        if self._drag_corner >= 0:
            lx, ly = self._screen_to_local(touch.x, touch.y)  # type: ignore[attr-defined]
            # Corners are in order TL(0), TR(1), BR(2), BL(3).
            # Each corner controls one x-side and one y-side; update those and
            # reconstruct all 4 points so the box stays an axis-aligned rectangle.
            x0, y0 = self._text_box[0]
            x1, y1 = self._text_box[2]
            if self._drag_corner in (0, 3):  # left side
                x0 = lx
            else:  # right side
                x1 = lx
            if self._drag_corner in (0, 1):  # top side (PIL y=0 at top)
                y0 = ly
            else:  # bottom side
                y1 = ly
            self._text_box = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        else:
            dx = (touch.x - self._drag_start_tx) / self._scale  # type: ignore[attr-defined]
            # flip Y axis (Kivy y=0 at bottom, PIL y=0 at top)
            dy = -(touch.y - self._drag_start_ty) / self._scale  # type: ignore[attr-defined]
            for i, p in enumerate(self._drag_start_box):
                self._text_box[i] = [p[0] + dx, p[1] + dy]
        self._redraw()
        return True

    def on_touch_up(self, touch: object) -> bool:
        if touch.grab_current is not self:  # type: ignore[attr-defined]
            return False
        touch.ungrab(self)  # type: ignore[attr-defined]
        if self._dragging:
            self._dragging = False
            self._drag_corner = -1
            self._on_box_changed(self.get_text_box_full_page())
        return True

    @staticmethod
    def _point_in_polygon(x: float, y: float, pts: list) -> bool:
        n = len(pts)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside


# ── EditorApp ────────────────────────────────────────────────────────────────


class EditorApp(App):
    text_str_easyocr = StringProperty()
    text_str_paddleocr = StringProperty()
    edit_label_easyocr = StringProperty("EasyOCR")
    edit_label_paddleocr = StringProperty("PaddleOCR")
    queue_progress_text = StringProperty()

    def __init__(  # noqa: PLR0913
        self,
        volume: int,
        fanta_page: int,
        easyocr_group_id: int,
        paddleocr_group_id: int,
        queue: list[QueueEntry] | None = None,
        queue_index: int = 0,
        initial_engine: str = "easyocr",
    ) -> None:
        super().__init__()

        self._comics_database = ComicsDatabase()
        self._queue = queue
        self._queue_index = queue_index
        self._active_engine = initial_engine  # used for delete tracking

        # Mutable UI references — set during build()
        self._easyocr_canvas: BoundingBoxCanvas | None = None
        self._paddleocr_canvas: BoundingBoxCanvas | None = None
        self._easyocr_panel_num_input: TextInput | None = None
        self._paddleocr_panel_num_input: TextInput | None = None
        self._info_label: Label | None = None
        self._decode_checkbox: CheckBox | None = None
        self._popup: Popup | None = None
        self._has_changes = False

        # Load the initial page data
        self._volume = volume
        self._fanta_page = get_page_str(fanta_page)
        self._load_page_data(volume, self._fanta_page)

        self._set_easyocr_group_id(str(easyocr_group_id))
        self._set_paddleocr_group_id(str(paddleocr_group_id))

        if self._queue:
            self.queue_progress_text = f"{queue_index + 1} / {len(self._queue)}"

        Window.bind(on_request_close=self.on_request_close)

    # ── page / queue loading ──────────────────────────────────────────────────

    def _load_page_data(self, volume: int, fanta_page: str) -> None:
        """Load both OCR speech groups for a given volume + page."""
        self._volume = volume
        self._fanta_page = fanta_page

        title_str, dest_page = get_title_from_volume_page(self._comics_database, volume, fanta_page)
        self._title = BARKS_TITLE_DICT[title_str]
        dest_page_str = get_page_str(dest_page)

        self._easyocr_speech_page_group = get_speech_page_group(
            self._comics_database,
            volume,
            self._title,
            OcrTypes.EASYOCR,
            fanta_page,
            dest_page_str,
        )
        self._paddleocr_speech_page_group = get_speech_page_group(
            self._comics_database,
            volume,
            self._title,
            OcrTypes.PADDLEOCR,
            fanta_page,
            dest_page_str,
        )
        self._easyocr_speech_groups = self._easyocr_speech_page_group.speech_groups
        self._paddleocr_speech_groups = self._paddleocr_speech_page_group.speech_groups

        restored_dir = self._comics_database.get_fantagraphics_restored_volume_image_dir(volume)
        self._srce_image_file = restored_dir / (fanta_page + PNG_FILE_EXT)
        segments_dir = Path(
            self._comics_database.get_fantagraphics_panel_segments_volume_dir(volume)
        )
        self._panel_segments_file = segments_dir / (fanta_page + ".json")

    def _load_queue_entry(self, index: int) -> None:
        """Load the queue entry at *index* and refresh the entire UI."""
        entry = self._queue[index]
        self._queue_index = index
        self._active_engine = entry.engine
        self._has_changes = False

        fanta_page_str = get_page_str(entry.fanta_page)
        self._load_page_data(entry.volume, fanta_page_str)

        primary_id = str(entry.group_id)
        if entry.engine == "easyocr":
            self._set_easyocr_group_id(primary_id)
            fallback = next(iter(self._paddleocr_speech_groups), None)
            if fallback:
                self._set_paddleocr_group_id(fallback)
        else:
            self._set_paddleocr_group_id(primary_id)
            fallback = next(iter(self._easyocr_speech_groups), None)
            if fallback:
                self._set_easyocr_group_id(fallback)

        self.queue_progress_text = f"{index + 1} / {len(self._queue)}"

        if self._easyocr_canvas:
            self._load_easyocr_canvas_content()
        if self._paddleocr_canvas:
            self._load_paddleocr_canvas_content()
        if self._info_label:
            self._info_label.text = self._get_editor_info()

    # ── canvas / image helpers ────────────────────────────────────────────────

    def _load_easyocr_canvas_content(self) -> None:
        """Refresh the EasyOCR BoundingBoxCanvas for the current easyocr group."""
        json_groups = self._easyocr_speech_page_group.speech_page_json.get("groups", {})
        panel_num = json_groups.get(self._easyocr_group_id, {}).get("panel_num", -1)
        self._load_engine_canvas_content(
            canvas=self._easyocr_canvas,
            group_id=self._easyocr_group_id,
            page_group=self._easyocr_speech_page_group,
            panel_num=panel_num,
        )

    def _load_paddleocr_canvas_content(self) -> None:
        """Refresh the PaddleOCR BoundingBoxCanvas for the current paddleocr group."""
        json_groups = self._paddleocr_speech_page_group.speech_page_json.get("groups", {})
        panel_num = json_groups.get(self._paddleocr_group_id, {}).get("panel_num", -1)
        self._load_engine_canvas_content(
            canvas=self._paddleocr_canvas,
            group_id=self._paddleocr_group_id,
            page_group=self._paddleocr_speech_page_group,
            panel_num=panel_num,
        )

    def _load_engine_canvas_content(
        self,
        canvas: BoundingBoxCanvas | None,
        group_id: str,
        page_group: object,
        panel_num: int,
    ) -> None:
        """Parameterized canvas refresh for one engine."""
        if canvas is None:
            return

        raw_json_groups = page_group.speech_page_json.get("groups", {})  # type: ignore[attr-defined]
        group_json = raw_json_groups.get(group_id)
        if group_json is None:
            logger.warning(f"Group {group_id} not found in JSON for canvas refresh.")
            return

        text_box = group_json.get("text_box", [])
        if not text_box:
            logger.warning(f"Group {group_id} has no text_box.")
            return

        if not self._srce_image_file.is_file():
            logger.warning(f'Source image not found: "{self._srce_image_file}".')
            return

        full_img = load_pil_image_for_reading(self._srce_image_file)
        img_w, img_h = full_img.size

        if panel_num <= 0:
            # Unknown panel: show wider crop and overlay all panel outlines
            all_panel_bounds = get_all_panel_bounds_from_file(self._panel_segments_file)
            crop_l, crop_t, crop_r, crop_b = compute_crop_region(
                img_w, img_h, None, text_box, padding=CROP_PADDING_UNKNOWN
            )
            cropped = full_img.crop((crop_l, crop_t, crop_r, crop_b))
            canvas.set_content(
                pil_image=cropped,
                text_box_full_page=text_box,
                crop_offset=(crop_l, crop_t),
                panel_bounds_full_page=None,
                all_panel_bounds_full_page=all_panel_bounds or None,
            )
        else:
            panel_bounds = get_panel_bounds_from_file(self._panel_segments_file, panel_num)
            crop_l, crop_t, crop_r, crop_b = compute_crop_region(
                img_w, img_h, panel_bounds, text_box
            )
            cropped = full_img.crop((crop_l, crop_t, crop_r, crop_b))
            canvas.set_content(
                pil_image=cropped,
                text_box_full_page=text_box,
                crop_offset=(crop_l, crop_t),
                panel_bounds_full_page=panel_bounds,
            )

    # ── App lifecycle ─────────────────────────────────────────────────────────

    def build(self) -> Widget:
        self.text_str_easyocr = self._easyocr_speech_groups[self._easyocr_group_id].raw_ai_text
        self.text_str_paddleocr = self._paddleocr_speech_groups[
            self._paddleocr_group_id
        ].raw_ai_text

        widget = self._create_editor_widget()

        # Populate canvases now that self._easyocr_canvas / _paddleocr_canvas are set
        self._load_easyocr_canvas_content()
        self._load_paddleocr_canvas_content()

        return widget

    def on_request_close(self, *_args: object) -> bool:
        if not self._has_changes:
            return False
        self._show_exit_popup()
        return True  # prevent immediate close

    def _show_exit_popup(self) -> None:
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text="There are unsaved changes.\nAre you sure you want to exit?"))
        button_layout = BoxLayout(spacing=10)

        yes_button = Button(text="Yes, exit")
        yes_button.bind(on_press=self._stop_app)
        button_layout.add_widget(yes_button)

        no_button = Button(text="No, go back")
        no_button.bind(on_press=lambda _btn: self._popup.dismiss())
        button_layout.add_widget(no_button)

        content.add_widget(button_layout)
        self._popup = Popup(
            title="Unsaved Changes",
            content=content,
            size_hint=(None, None),
            size=(420, 200),
            auto_dismiss=False,
        )
        self._popup.open()

    def _stop_app(self, *_args: object) -> None:
        if self._popup:
            self._popup.dismiss()
        self.stop()

    # ── text change callbacks ─────────────────────────────────────────────────

    def _on_easyocr_text_changed(self, instance: TextInput, _value: str) -> None:
        if not instance.focus:
            return
        self._easyocr_speech_groups[
            self._easyocr_group_id
        ].raw_ai_text = self._get_current_easyocr_text()
        self._has_changes = True

    def _on_paddleocr_text_changed(self, instance: TextInput, _value: str) -> None:
        if not instance.focus:
            return
        self._paddleocr_speech_groups[
            self._paddleocr_group_id
        ].raw_ai_text = self._get_current_paddleocr_text()
        self._has_changes = True

    # ── canvas / panel_num callbacks ──────────────────────────────────────────

    def _on_easyocr_box_changed(self, new_text_box: list) -> None:
        """Handle a bounding box change reported by the EasyOCR canvas."""
        self._has_changes = True
        logger.debug(f"EasyOCR text box updated to: {new_text_box}")

    def _on_paddleocr_box_changed(self, new_text_box: list) -> None:
        """Handle a bounding box change reported by the PaddleOCR canvas."""
        self._has_changes = True
        logger.debug(f"PaddleOCR text box updated to: {new_text_box}")

    def _on_easyocr_panel_num_confirmed(self, instance: TextInput) -> None:
        """Validate and apply the EasyOCR panel_num TextInput value."""
        json_groups = self._easyocr_speech_page_group.speech_page_json.get("groups", {})
        json_group = json_groups.get(self._easyocr_group_id)
        current = json_group.get("panel_num", -1) if json_group else -1
        try:
            new_num = int(instance.text.strip())
        except ValueError:
            instance.text = str(current)
            return
        if new_num != current and json_group is not None:
            json_group["panel_num"] = new_num
            self._load_easyocr_canvas_content()
            self._has_changes = True

    def _on_paddleocr_panel_num_confirmed(self, instance: TextInput) -> None:
        """Validate and apply the PaddleOCR panel_num TextInput value."""
        json_groups = self._paddleocr_speech_page_group.speech_page_json.get("groups", {})
        json_group = json_groups.get(self._paddleocr_group_id)
        current = json_group.get("panel_num", -1) if json_group else -1
        try:
            new_num = int(instance.text.strip())
        except ValueError:
            instance.text = str(current)
            return
        if new_num != current and json_group is not None:
            json_group["panel_num"] = new_num
            self._load_paddleocr_canvas_content()
            self._has_changes = True

    @staticmethod
    def _update_panel_num_input_color(instance: TextInput, value: str) -> None:
        """Color the panel_num TextInput background red when the value is -1."""
        try:
            is_unassigned = int(value.strip()) < 0
        except ValueError:
            is_unassigned = True
        instance.background_color = (1.0, 0.4, 0.4, 1) if is_unassigned else (1, 1, 1, 1)

    def _on_easyocr_panel_num_focus(self, instance: TextInput, focused: bool) -> None:
        if not focused:
            self._on_easyocr_panel_num_confirmed(instance)

    def _on_paddleocr_panel_num_focus(self, instance: TextInput, focused: bool) -> None:
        if not focused:
            self._on_paddleocr_panel_num_confirmed(instance)

    # ── group / panel helpers ─────────────────────────────────────────────────

    def _set_easyocr_group_id(self, group_id: str) -> None:
        if group_id not in self._easyocr_speech_groups:
            msg = f"Unknown easyocr group id '{group_id}'."
            raise ValueError(msg)
        self._easyocr_group_id = group_id
        speech_group = self._easyocr_speech_groups[group_id]
        self._easyocr_label = self._get_ocr_label(EASY_OCR, group_id, speech_group.panel_num)
        self.text_str_easyocr = (
            self._encode_for_display(speech_group.raw_ai_text)
            if self._decode_checkbox and self._decode_checkbox.active
            else speech_group.raw_ai_text
        )
        self._set_easyocr_panel_num(speech_group.panel_num)

    def _set_easyocr_panel_num(self, panel_num: int) -> None:
        """Update easyocr panel_num in the JSON dict and the panel_num input widget."""
        json_groups = self._easyocr_speech_page_group.speech_page_json.get("groups", {})
        json_group = json_groups.get(self._easyocr_group_id)
        if json_group is not None:
            json_group["panel_num"] = panel_num
        if self._easyocr_panel_num_input is not None:
            self._easyocr_panel_num_input.text = str(panel_num)

    def _set_paddleocr_group_id(self, group_id: str) -> None:
        if group_id not in self._paddleocr_speech_groups:
            msg = f"Unknown paddleocr group id '{group_id}'."
            raise ValueError(msg)
        self._paddleocr_group_id = group_id
        speech_group = self._paddleocr_speech_groups[group_id]
        self._paddleocr_label = self._get_ocr_label(PADDLE_OCR, group_id, speech_group.panel_num)
        self.text_str_paddleocr = (
            self._encode_for_display(speech_group.raw_ai_text)
            if self._decode_checkbox and self._decode_checkbox.active
            else speech_group.raw_ai_text
        )
        self._set_paddleocr_panel_num(speech_group.panel_num)

    def _set_paddleocr_panel_num(self, panel_num: int) -> None:
        """Update paddleocr panel_num in the JSON dict and the panel_num input widget."""
        json_groups = self._paddleocr_speech_page_group.speech_page_json.get("groups", {})
        json_group = json_groups.get(self._paddleocr_group_id)
        if json_group is not None:
            json_group["panel_num"] = panel_num
        if self._paddleocr_panel_num_input is not None:
            self._paddleocr_panel_num_input.text = str(panel_num)

    @staticmethod
    def _get_ocr_label(ocr_name: str, group_id: str, panel_num: int) -> str:
        return f"{ocr_name}: group_id: {group_id}; panel: {panel_num}"

    # ── info text ─────────────────────────────────────────────────────────────

    def _get_editor_info(self) -> str:
        return f"{BARKS_TITLES[self._title]}  |  Volume {self._volume}  |  Page {self._fanta_page}"

    # ── text encode/decode ────────────────────────────────────────────────────

    @staticmethod
    def _encode_for_display(text: str) -> str:
        return text.encode("unicode_escape").decode("utf-8").replace(r"\n", "\n")

    @staticmethod
    def _decode_from_display(text: str) -> str:
        return text.replace("\n", r"\n").encode("utf-8").decode("unicode_escape")

    # ── widget construction ───────────────────────────────────────────────────

    def _create_editor_widget(self) -> BoxLayout:
        # Build bottom first so self._decode_checkbox is set before the diff closure runs
        bottom = self._get_bottom_layout()

        # Subtitle row — one line at the top of the window
        self._info_label = Label(
            text=self._get_editor_info(),
            size_hint_y=None,
            height=28,
            font_size="13sp",
            halign="left",
            valign="middle",
        )
        self._info_label.bind(size=self._info_label.setter("text_size"))

        easy_col, label_easy, ti_easy = self._get_easyocr_column()
        pad_col, label_pad, ti_pad = self._get_paddleocr_column()

        def update_diff_labels(*_args: object) -> None:
            try:
                t1 = ti_easy.text
                t2 = ti_pad.text
                if self._decode_checkbox.active:
                    t1 = self._decode_from_display(t1)
                    t2 = self._decode_from_display(t2)
                are_different = t1 != t2
                if are_different:
                    self.edit_label_easyocr = f"DIFFS -- {self._easyocr_label}"
                    self.edit_label_paddleocr = f"DIFFS -- {self._paddleocr_label}"
                    label_easy.color = (1, 0, 0, 1)
                    label_pad.color = (1, 0, 0, 1)
                else:
                    self.edit_label_easyocr = self._easyocr_label
                    self.edit_label_paddleocr = self._paddleocr_label
                    label_easy.color = (1, 1, 1, 1)
                    label_pad.color = (1, 1, 1, 1)
            except UnicodeDecodeError:
                pass

        ti_easy.bind(text=update_diff_labels)
        ti_pad.bind(text=update_diff_labels)
        update_diff_labels()

        columns = BoxLayout(orientation="horizontal", spacing=10)
        columns.add_widget(easy_col)
        columns.add_widget(pad_col)

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(self._info_label)
        content.add_widget(columns)
        content.add_widget(bottom)
        return content

    def _get_easyocr_column(self) -> tuple[BoxLayout, Label, TextInput]:
        """Build the EasyOCR column: panel_num row → label → text → canvas (stacked)."""
        col = BoxLayout(orientation="vertical", spacing=4)

        # Compact panel_num row
        panel_num_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=28, spacing=6)
        panel_num_row.add_widget(
            Label(text="EasyOCR  Panel:", size_hint_x=None, width=130, font_size="13sp")
        )
        json_groups = self._easyocr_speech_page_group.speech_page_json.get("groups", {})
        initial_panel_num = json_groups.get(self._easyocr_group_id, {}).get("panel_num", -1)
        self._easyocr_panel_num_input = TextInput(
            text=str(initial_panel_num),
            multiline=False,
            font_size="14sp",
            size_hint_x=None,
            width=55,
            size_hint_y=None,
            height=28,
        )
        self._easyocr_panel_num_input.bind(on_text_validate=self._on_easyocr_panel_num_confirmed)
        self._easyocr_panel_num_input.bind(focus=self._on_easyocr_panel_num_focus)
        self._easyocr_panel_num_input.bind(text=self._update_panel_num_input_color)
        self._update_panel_num_input_color(self._easyocr_panel_num_input, str(initial_panel_num))
        panel_num_row.add_widget(self._easyocr_panel_num_input)
        panel_num_row.add_widget(Widget())  # spacer
        col.add_widget(panel_num_row)

        # Engine label (goes red when texts differ)
        label_easyocr = Label(text=self.edit_label_easyocr, bold=True, size_hint_y=None, height=26)
        self.bind(edit_label_easyocr=label_easyocr.setter("text"))
        label_easyocr.bind(text=self.setter("edit_label_easyocr"))
        col.add_widget(label_easyocr)

        # Short text input
        text_input_easyocr = TextInput(
            text=self.text_str_easyocr,
            font_name=OPEN_SANS_FONT,
            font_size="20sp",
            multiline=True,
            size_hint_y=None,
            height=350,
            padding=10,
            hint_text="Edit EasyOCR text here...",
        )
        self.bind(text_str_easyocr=text_input_easyocr.setter("text"))
        text_input_easyocr.bind(text=self.setter("text_str_easyocr"))
        text_input_easyocr.bind(text=self._on_easyocr_text_changed)
        self.text_str_easyocr = self._encode_for_display(self.text_str_easyocr)
        col.add_widget(text_input_easyocr)

        # Canvas below text — full column width, takes all remaining vertical space
        self._easyocr_canvas = BoundingBoxCanvas(
            on_box_changed=self._on_easyocr_box_changed,
            size_hint_y=1,
        )
        col.add_widget(self._easyocr_canvas)

        return col, label_easyocr, text_input_easyocr

    def _get_paddleocr_column(self) -> tuple[BoxLayout, Label, TextInput]:
        """Build the PaddleOCR column: panel_num row → label → text → canvas (stacked)."""
        col = BoxLayout(orientation="vertical", spacing=4)

        # Compact panel_num row
        panel_num_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=28, spacing=6)
        panel_num_row.add_widget(
            Label(text="PaddleOCR  Panel:", size_hint_x=None, width=140, font_size="13sp")
        )
        json_groups = self._paddleocr_speech_page_group.speech_page_json.get("groups", {})
        initial_panel_num = json_groups.get(self._paddleocr_group_id, {}).get("panel_num", -1)
        self._paddleocr_panel_num_input = TextInput(
            text=str(initial_panel_num),
            multiline=False,
            font_size="14sp",
            size_hint_x=None,
            width=55,
            size_hint_y=None,
            height=28,
        )
        self._paddleocr_panel_num_input.bind(
            on_text_validate=self._on_paddleocr_panel_num_confirmed
        )
        self._paddleocr_panel_num_input.bind(focus=self._on_paddleocr_panel_num_focus)
        self._paddleocr_panel_num_input.bind(text=self._update_panel_num_input_color)
        self._update_panel_num_input_color(self._paddleocr_panel_num_input, str(initial_panel_num))
        panel_num_row.add_widget(self._paddleocr_panel_num_input)
        panel_num_row.add_widget(Widget())  # spacer
        col.add_widget(panel_num_row)

        # Engine label (goes red when texts differ)
        label_paddleocr = Label(
            text=self.edit_label_paddleocr, bold=True, size_hint_y=None, height=26
        )
        self.bind(edit_label_paddleocr=label_paddleocr.setter("text"))
        label_paddleocr.bind(text=self.setter("edit_label_paddleocr"))
        col.add_widget(label_paddleocr)

        # Short text input
        text_input_paddleocr = TextInput(
            text=self.text_str_paddleocr,
            font_name=OPEN_SANS_FONT,
            font_size="20sp",
            multiline=True,
            size_hint_y=None,
            height=350,
            padding=10,
            hint_text="Edit PaddleOCR text here...",
        )
        self.bind(text_str_paddleocr=text_input_paddleocr.setter("text"))
        text_input_paddleocr.bind(text=self.setter("text_str_paddleocr"))
        text_input_paddleocr.bind(text=self._on_paddleocr_text_changed)
        self.text_str_paddleocr = self._encode_for_display(self.text_str_paddleocr)
        col.add_widget(text_input_paddleocr)

        # Canvas below text — full column width, takes all remaining vertical space
        self._paddleocr_canvas = BoundingBoxCanvas(
            on_box_changed=self._on_paddleocr_box_changed,
            size_hint_y=1,
        )
        col.add_widget(self._paddleocr_canvas)

        return col, label_paddleocr, text_input_paddleocr

    def _get_bottom_layout(self) -> BoxLayout:
        outer = BoxLayout(orientation="vertical", size_hint_y=None, height=56, spacing=6)

        # Button row
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)

        # Decode checkbox
        checkbox_layout, self._decode_checkbox = self._add_decode_checkbox()
        checkbox_layout.size_hint_x = None
        checkbox_layout.width = 200
        btn_row.add_widget(checkbox_layout)

        select_btn = Button(text="Select EasyOCR Item", size_hint_y=None, height=50)
        select_btn.bind(on_press=self._show_easyocr_speech_item_popup)
        btn_row.add_widget(select_btn)

        select_btn2 = Button(text="Select PaddleOCR Item", size_hint_y=None, height=50)
        select_btn2.bind(on_press=self._show_paddleocr_speech_item_popup)
        btn_row.add_widget(select_btn2)

        delete_btn = Button(text="Delete Group", size_hint_y=None, height=50)
        delete_btn.bind(on_press=self._handle_delete)
        btn_row.add_widget(delete_btn)

        if self._queue:
            save_next_btn = Button(text="Save & Next", size_hint_y=None, height=50)
            save_next_btn.bind(on_press=lambda _: self._handle_save_and_next())
            btn_row.add_widget(save_next_btn)

            skip_btn = Button(text="Skip", size_hint_y=None, height=50)
            skip_btn.bind(on_press=lambda _: self._handle_skip())
            btn_row.add_widget(skip_btn)

            queue_label = Label(
                text=self.queue_progress_text,
                size_hint_x=None,
                width=100,
                font_size="16sp",
                bold=True,
            )
            self.bind(queue_progress_text=queue_label.setter("text"))
            btn_row.add_widget(queue_label)
        else:
            btn_row.add_widget(self._get_save_exit_button())

        outer.add_widget(btn_row)
        return outer

    def _add_decode_checkbox(self) -> tuple[BoxLayout, CheckBox]:
        checkbox_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
        decode_checkbox = CheckBox(active=True, size_hint_x=None, width=30)
        decode_label = Label(text="Show Unicode", halign="left", valign="middle")
        decode_label.bind(size=decode_label.setter("text_size"))

        def on_checkbox_active(_instance: CheckBox, value: bool) -> None:
            try:
                t1 = self.text_str_easyocr
                t2 = self.text_str_paddleocr
                if value:
                    self.text_str_easyocr = self._encode_for_display(t1)
                    self.text_str_paddleocr = self._encode_for_display(t2)
                else:
                    self.text_str_easyocr = self._decode_from_display(t1)
                    self.text_str_paddleocr = self._decode_from_display(t2)
            except UnicodeDecodeError as e:
                logger.exception(f"Error converting text: {e}")

        decode_checkbox.bind(active=on_checkbox_active)
        checkbox_layout.add_widget(decode_checkbox)
        checkbox_layout.add_widget(decode_label)
        return checkbox_layout, decode_checkbox

    # ── speech item popups ────────────────────────────────────────────────────

    def _show_easyocr_speech_item_popup(self, _instance: Button) -> None:
        self._show_speech_item_popup(
            "Select EasyOCR Speech Item",
            self._get_easyocr_speech_items(),
            self._on_easyocr_speech_item_selected,
        )

    def _show_paddleocr_speech_item_popup(self, _instance: Button) -> None:
        self._show_speech_item_popup(
            "Select PaddleOCR Speech Item",
            self._get_paddleocr_speech_items(),
            self._on_paddleocr_speech_item_selected,
        )

    @staticmethod
    def _show_speech_item_popup(
        popup_title: str,
        items: list[SpeechItem],
        on_speech_item_selected: Callable[[SpeechItem], None],
    ) -> None:
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        scroll = ScrollView()
        list_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        list_layout.bind(minimum_height=list_layout.setter("height"))
        popup = Popup(title=popup_title, content=content, size_hint=(0.9, 0.8))

        def select_item(selected_item: SpeechItem) -> None:
            popup.dismiss()
            on_speech_item_selected(selected_item)

        for item in items:
            btn_text = f"{item.panel_num}({item.group_id}): {item.text.replace(chr(10), ' ')}"
            btn = Button(text=btn_text, font_name=OPEN_SANS_FONT, size_hint_y=None, height=40)
            btn.bind(on_release=lambda _inst, i=item: select_item(i))
            list_layout.add_widget(btn)

        scroll.add_widget(list_layout)
        content.add_widget(scroll)
        close_btn = Button(text="Close", size_hint_y=None, height=40)
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def _get_easyocr_speech_items(self) -> list[SpeechItem]:
        return [
            SpeechItem(panel_num=data.panel_num, group_id=gid, text=data.raw_ai_text or "")
            for gid, data in self._easyocr_speech_groups.items()
        ]

    def _on_easyocr_speech_item_selected(self, speech_item: SpeechItem) -> None:
        self._active_engine = "easyocr"
        self._set_easyocr_group_id(speech_item.group_id)
        self._load_easyocr_canvas_content()

    def _get_paddleocr_speech_items(self) -> list[SpeechItem]:
        return [
            SpeechItem(panel_num=data.panel_num, group_id=gid, text=data.raw_ai_text or "")
            for gid, data in self._paddleocr_speech_groups.items()
        ]

    def _on_paddleocr_speech_item_selected(self, speech_item: SpeechItem) -> None:
        self._active_engine = "paddleocr"
        self._set_paddleocr_group_id(speech_item.group_id)
        self._load_paddleocr_canvas_content()

    # ── save / delete / navigation ────────────────────────────────────────────

    def _get_save_exit_button(self) -> Button:
        btn = Button(text="Save & Exit", size_hint_y=None, height=50)

        def on_save(_instance: Button) -> None:
            self._handle_save()
            self.stop()

        btn.bind(on_press=on_save)
        return btn

    def _get_current_easyocr_text(self) -> str:
        return (
            self._decode_from_display(self.text_str_easyocr)
            if self._decode_checkbox.active
            else self.text_str_easyocr
        )

    def _get_current_paddleocr_text(self) -> str:
        return (
            self._decode_from_display(self.text_str_paddleocr)
            if self._decode_checkbox.active
            else self.text_str_paddleocr
        )

    def _handle_save(self) -> None:
        """Save text, panel_num, and text_box changes to both OCR JSON files."""
        self._save_page_group(
            self._easyocr_speech_page_group,
            self._easyocr_group_id,
            self._easyocr_speech_groups,
            self._easyocr_canvas,
        )
        self._save_page_group(
            self._paddleocr_speech_page_group,
            self._paddleocr_group_id,
            self._paddleocr_speech_groups,
            self._paddleocr_canvas,
        )
        self._has_changes = False

    def _save_page_group(
        self,
        page_group: object,
        group_id: str,
        speech_groups: dict,
        canvas: BoundingBoxCanvas | None,
    ) -> None:
        """Sync in-memory edits to speech_page_json and write to disk.

        panel_num is already synced to speech_page_json via _set_*_panel_num /
        _on_*_panel_num_confirmed, so only text and text_box need updating here.
        """
        ocr_file = page_group.ocr_prelim_groups_json_file  # type: ignore[attr-defined]
        backup_file = self._get_prelim_ocr_backup_file(ocr_file)

        json_groups = page_group.speech_page_json.get("groups", {})  # type: ignore[attr-defined]

        # Sync text for all groups whose raw_ai_text has changed
        changed = False
        for gid, speech_text in speech_groups.items():
            json_group = json_groups.get(gid)
            if json_group is None:
                continue
            if speech_text.raw_ai_text != json_group.get("ai_text"):
                json_group["ai_text"] = speech_text.raw_ai_text
                changed = True

        # Sync text_box from canvas (panel_num already updated in json_group)
        json_group = json_groups.get(group_id)
        if json_group is not None and canvas is not None:
            new_text_box = canvas.get_text_box_full_page()
            if new_text_box and new_text_box != json_group.get("text_box"):
                json_group["text_box"] = new_text_box
                changed = True

        # panel_num changes are tracked via _has_changes but already in json_group;
        # save if anything changed or if we have pending panel_num edits.
        if changed or self._has_changes:
            page_group.save_json(backup_file=backup_file)  # type: ignore[attr-defined]
            logger.info(f'Saved changes to "{ocr_file}". Backup at "{backup_file}".')
        else:
            logger.debug(f'No changes in "{ocr_file}".')

    def _handle_save_and_next(self) -> None:
        self._handle_save()
        self._advance_queue()

    def _handle_skip(self) -> None:
        self._has_changes = False
        self._advance_queue()

    def _handle_delete(self, _instance: object = None) -> None:
        """Prompt for confirmation, then delete the active engine's current group."""
        engine_label = "EasyOCR" if self._active_engine == "easyocr" else "PaddleOCR"
        group_id = (
            self._easyocr_group_id if self._active_engine == "easyocr" else self._paddleocr_group_id
        )
        self._show_confirm_popup(
            title="Delete Group",
            message=f"Delete {engine_label} group {group_id}?\nThis cannot be undone.",
            on_confirm=self._do_delete,
        )

    def _do_delete(self) -> None:
        """Perform the deletion after user confirmation."""
        primary_page_group = (
            self._easyocr_speech_page_group
            if self._active_engine == "easyocr"
            else self._paddleocr_speech_page_group
        )
        primary_group_id = (
            self._easyocr_group_id if self._active_engine == "easyocr" else self._paddleocr_group_id
        )

        json_groups = primary_page_group.speech_page_json.get("groups", {})
        if primary_group_id in json_groups:
            del json_groups[primary_group_id]
            ocr_file = primary_page_group.ocr_prelim_groups_json_file
            backup_file = self._get_prelim_ocr_backup_file(ocr_file)
            primary_page_group.save_json(backup_file=backup_file)
            logger.info(
                f'Deleted group {primary_group_id} from "{ocr_file}". Backup at "{backup_file}".'
            )

        self._has_changes = False

        if self._queue:
            self._advance_queue()
        else:
            self._load_next_group_after_delete(primary_group_id)

    def _load_next_group_after_delete(self, deleted_group_id: str) -> None:
        """After a non-queue delete, load the next available group or close."""
        groups = (
            self._easyocr_speech_groups
            if self._active_engine == "easyocr"
            else self._paddleocr_speech_groups
        )
        remaining = [gid for gid in groups if gid != deleted_group_id]
        if remaining:
            next_id = remaining[0]
            if self._active_engine == "easyocr":
                self._set_easyocr_group_id(next_id)
                self._load_easyocr_canvas_content()
            else:
                self._set_paddleocr_group_id(next_id)
                self._load_paddleocr_canvas_content()
        else:
            self._show_confirm_popup(
                title="No Groups Remaining",
                message="All groups have been deleted.\nClose the editor?",
                on_confirm=self.stop,
            )

    @staticmethod
    def _show_confirm_popup(title: str, message: str, on_confirm: Callable[[], None]) -> None:
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text=message))
        button_layout = BoxLayout(spacing=10, size_hint_y=None, height=44)
        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=(440, 200),
            auto_dismiss=False,
        )
        yes_btn = Button(text="Yes")
        yes_btn.bind(on_press=lambda _: (popup.dismiss(), on_confirm()))
        no_btn = Button(text="Cancel")
        no_btn.bind(on_press=lambda _: popup.dismiss())
        button_layout.add_widget(yes_btn)
        button_layout.add_widget(no_btn)
        content.add_widget(button_layout)
        popup.open()

    def _advance_queue(self) -> None:
        next_index = self._queue_index + 1
        if self._queue is None or next_index >= len(self._queue):
            self._show_queue_done_popup()
            return
        self._load_queue_entry(next_index)

    def _show_queue_done_popup(self) -> None:
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text="All queue entries have been processed."))
        btn = Button(text="Close", size_hint_y=None, height=40)
        popup = Popup(
            title="Queue Complete",
            content=content,
            size_hint=(None, None),
            size=(360, 160),
        )
        btn.bind(on_press=lambda _: (popup.dismiss(), self.stop()))
        content.add_widget(btn)
        popup.open()

    @staticmethod
    def _get_prelim_ocr_backup_file(ocr_file: Path) -> Path:
        return Path(
            str(get_backup_file(ocr_file)).replace(str(OCR_PRELIM_DIR), str(OCR_PRELIM_BACKUP_DIR))
        )


# ── CLI ───────────────────────────────────────────────────────────────────────

app = typer.Typer()


@app.command(help="Prelim OCR Text Editor")
def main(  # noqa: PLR0913
    volume: int = typer.Option(0, help="Volume number (single mode)"),
    fanta_page: int = typer.Option(0, help="Fanta page number (single mode)"),
    easyocr_group_id: int = typer.Option(0, help="EasyOCR group ID (single mode)"),
    paddleocr_group_id: int = typer.Option(0, help="PaddleOCR group ID (single mode)"),
    queue_file: Path = typer.Option(  # noqa: B008
        None,
        "--queue-file",
        help="Queue file: one 'volume page engine group_id' per line",
    ),
    primary_engine: str = typer.Option(
        "easyocr",
        "--primary",
        help="Initial active engine for delete operations: easyocr or paddleocr",
    ),
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    _log_setup.log_level = log_level_str
    _log_setup.log_filename = "kivy-prelim-ocr-editor.log"
    _log_setup.APP_LOGGING_NAME = APP_LOGGING_NAME
    LoguruConfig.load(_RESOURCES / "log-config.yaml")

    if queue_file is not None:
        queue = load_queue_file(queue_file)
        if not queue:
            logger.error(f'Queue file "{queue_file}" contains no valid entries.')
            raise typer.Exit(1)
        first = queue[0]
        EditorApp(
            volume=first.volume,
            fanta_page=first.fanta_page,
            easyocr_group_id=first.group_id if first.engine == "easyocr" else 0,
            paddleocr_group_id=first.group_id if first.engine == "paddleocr" else 0,
            queue=queue,
            queue_index=0,
            initial_engine=first.engine,
        ).run()
    else:
        if not volume or not fanta_page:
            logger.error("Provide --volume and --fanta-page for single mode, or --queue-file.")
            raise typer.Exit(1)
        EditorApp(
            volume=volume,
            fanta_page=fanta_page,
            easyocr_group_id=easyocr_group_id,
            paddleocr_group_id=paddleocr_group_id,
            initial_engine=primary_engine,
        ).run()


if __name__ == "__main__":
    app()

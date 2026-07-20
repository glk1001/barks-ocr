# ruff: noqa: E402
import copy
import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path

import typer
from barks_fantagraphics.barks_titles import ENUM_TO_STR_TITLE, STR_TITLE_TO_ENUM
from barks_fantagraphics.comic_book import get_page_str
from barks_fantagraphics.comic_book_info import ONE_PAGERS
from barks_fantagraphics.comics_consts import FONT_DIR, OPEN_SANS_FONT, PNG_FILE_EXT, PageType
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page
from barks_fantagraphics.comics_utils import get_backup_file
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import (
    OcrTypes,
    SpeechPageGroup,
    SpeechText,
    get_speech_page_group,
)
from comic_utils.common_typer_options import LogLevelArg
from comic_utils.pil_image_utils import load_pil_image_for_reading
from comic_utils.screen_utils import get_centred_position_on_primary_monitor
from kivy.config import Config
from loguru import logger
from PIL import Image as PilImage

from barks_ocr.cli_setup import init_logging
from barks_ocr.utils.group_checks import (
    DISMISSABLE_ISSUE_TYPES,
    DISMISSABLE_PREDICATES,
)

APP_LOGGING_NAME = "kpoe"

MAIN_WINDOW_WIDTH = 2000
MAIN_WINDOW_HEIGHT = 1330
_MAIN_WINDOW_X, _MAIN_WINDOW_Y = get_centred_position_on_primary_monitor(
    MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT
)

Config.set("graphics", "position", "custom")  # ty:ignore[unresolved-attribute]
Config.set("graphics", "left", _MAIN_WINDOW_X)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "top", _MAIN_WINDOW_Y)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "width", MAIN_WINDOW_WIDTH)  # ty:ignore[unresolved-attribute]
Config.set("graphics", "height", MAIN_WINDOW_HEIGHT)  # ty:ignore[unresolved-attribute]
# Disable Kivy's right-click/ctrl-click multitouch emulation — laptop touchpads
# can emit spurious events that fire phantom touches (buttons, highlights).
Config.set("input", "mouse", "mouse,disable_multitouch")  # ty:ignore[unresolved-attribute]
# Stop ProbeSysfs from attaching MTD readers to /dev/input/event* for the
# touchpad/touchscreen. Those raw touch events duplicate SDL2's mouse events
# and cause phantom clicks and drag-selects on laptops.
Config.remove_option("input", "%(name)s")  # ty:ignore[unresolved-attribute]

# Kivy 2.3.1 bug: textinput.py calls canvas._remove_group() but Canvas only
# exposes remove_group() (no leading underscore). Patch the alias in.
import inspect as _inspect
import textwrap as _textwrap

import kivy.uix.textinput as _ki_textinput
from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.input.motionevent import MotionEvent
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
from kivy.uix.textinput import TextInput as _TextInput
from kivy.uix.widget import Widget

if not hasattr(_TextInput, "_kivy_patch_applied"):
    # Kivy 2.3.1 bug: TextInput._update_graphics_selection calls
    # canvas._remove_group() but Canvas (Cython) only exposes remove_group().
    # Re-compile the method with the correct name.
    _src = _textwrap.dedent(_inspect.getsource(_TextInput._update_graphics_selection))  # noqa: SLF001
    _src = _src.replace("._remove_group(", ".remove_group(")
    _ns: dict = vars(_ki_textinput).copy()
    exec(compile(_src, "<kivy_patch>", "exec"), _ns)  # noqa: S102
    _TextInput._update_graphics_selection = _ns["_update_graphics_selection"]  # noqa: SLF001
    _TextInput._kivy_patch_applied = True  # noqa: SLF001

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

# Allowed values for a group's "type" field, shown in the bottom-bar radio row.
TYPE_OPTIONS: tuple[str, ...] = (
    "background",
    "dialogue",
    "narration",
    "sound_effect",
    "thought",
    "title",
)
DEFAULT_TYPE = "dialogue"
TITLE_PAGE_DEFAULT_TYPE = "title"
TITLE_PAGE_ISSUE_TYPE = "title_page"
FLORENCE_CHECK_ISSUE_TYPE = "florence-check"


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
    issue_type: str


class EnginePane:
    """Per-engine mutable state for one OCR column in the editor."""

    def __init__(self, name: str, ocr_type: OcrTypes, text_prop: str, label_prop: str) -> None:
        self.name = name
        self.ocr_type = ocr_type
        self.text_prop = text_prop  # StringProperty name on EditorApp
        self.label_prop = label_prop  # StringProperty name on EditorApp
        self.group_id: str = ""
        self.label: str = ""
        # Always set by _load_page_data() before any method accesses it.
        self.page_group: SpeechPageGroup = None  # ty:ignore[invalid-assignment]
        self.speech_groups: dict[str, SpeechText] = {}
        self.canvas: BoundingBoxCanvas | None = None
        self.panel_num_input: TextInput | None = None

    def json_groups(self) -> dict:
        """Return the live JSON ``groups`` dict (mutable), or an empty dict if missing."""
        return self.page_group.speech_page_json.get("groups", {})

    def json_group(self, group_id: str | None = None) -> dict | None:
        """Return the JSON dict for ``group_id`` (defaults to current), or None."""
        gid = self.group_id if group_id is None else group_id
        return self.json_groups().get(gid)


# ── Helper functions ──────────────────────────────────────────────────────────


def load_queue_file(queue_file: Path) -> list[QueueEntry]:
    """Parse a queue file; each line: volume page engine group_id."""
    entries = []
    for raw_line in queue_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 5:  # noqa: PLR2004
            logger.warning(f"Skipping invalid queue line: {line!r}")
            continue
        try:
            entries.append(
                QueueEntry(
                    volume=int(parts[0]),
                    fanta_page=int(parts[1]),
                    engine=parts[2].lower(),
                    group_id=int(parts[3]),
                    issue_type=parts[4],
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
        self._panel_num: int | None = None
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
        self.canvas.add(self._draw_group)  # ty:ignore[unresolved-attribute]

        self.bind(size=self._redraw, pos=self._redraw)

    def set_content(  # noqa: PLR0913
        self,
        pil_image: PilImage.Image,
        text_box_full_page: list,
        crop_offset: tuple[int, int],
        panel_bounds_full_page: tuple[int, int, int, int] | None,
        all_panel_bounds_full_page: list[tuple[int, int, int, int]] | None = None,
        panel_num: int | None = None,
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
        self._panel_num = panel_num

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
        """Crop-local PIL coords -> Kivy screen coords."""
        sx = x * self._scale + self._img_offset_x
        # Flip Y: PIL y=0 is top; Kivy y=0 is bottom
        sy = (self._img_h - y) * self._scale + self._img_offset_y
        return sx, sy

    def _screen_to_local(self, sx: float, sy: float) -> tuple[float, float]:
        """Kivy screen coords -> crop-local PIL coords."""
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
        if self._panel_num is not None:
            lbl = CoreLabel(text=str(self._panel_num), font_size=26, bold=True)
            lbl.refresh()
            texture = lbl.texture
            if texture:
                tx = tl[0] + 4
                ty = tl[1] - texture.height - 4
                g.add(Color(0, 0, 0.6, 0.6))
                g.add(Rectangle(pos=(tx - 2, ty - 2), size=(texture.width + 4, texture.height + 4)))
                g.add(Color(0.2, 1.0, 0.5, 1.0))
                g.add(Rectangle(texture=texture, pos=(tx, ty), size=texture.size))

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

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if not self.collide_point(*touch.pos) or self._text_box is None:
            return False
        pts = [self._local_to_screen(p[0], p[1]) for p in self._text_box]

        # Corner handle hit-test first
        for i, pt in enumerate(pts):
            dist = ((touch.x - pt[0]) ** 2 + (touch.y - pt[1]) ** 2) ** 0.5
            if dist <= HANDLE_RADIUS:
                self._dragging = True
                self._drag_corner = i
                self._drag_start_box = [list(p) for p in self._text_box]
                touch.grab(self)
                return True

        # Body drag
        if self._point_in_polygon(touch.x, touch.y, pts):
            self._dragging = True
            self._drag_corner = -1
            self._drag_start_tx = touch.x
            self._drag_start_ty = touch.y
            self._drag_start_box = [list(p) for p in self._text_box]
            touch.grab(self)
            return True

        return False

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not self or not self._dragging:
            return False
        if self._drag_corner >= 0:
            lx, ly = self._screen_to_local(touch.x, touch.y)
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
            dx = (touch.x - self._drag_start_tx) / self._scale
            # flip Y axis (Kivy y=0 at bottom, PIL y=0 at top)
            dy = -(touch.y - self._drag_start_ty) / self._scale
            for i, p in enumerate(self._drag_start_box):
                self._text_box[i] = [p[0] + dx, p[1] + dy]
        self._redraw()
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
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
    ) -> None:
        super().__init__()

        self._comics_database = ComicsDatabase()
        self._queue = queue
        self._queue_index = queue_index

        self._easy_pane = EnginePane(
            EASY_OCR, OcrTypes.EASYOCR, "text_str_easyocr", "edit_label_easyocr"
        )
        self._pad_pane = EnginePane(
            PADDLE_OCR, OcrTypes.PADDLEOCR, "text_str_paddleocr", "edit_label_paddleocr"
        )
        self._panes: tuple[EnginePane, EnginePane] = (self._easy_pane, self._pad_pane)

        self._info_label: Label | None = None
        self._decode_checkbox: CheckBox | None = None
        self._has_changes = False

        # Load the initial page data
        self._volume = volume
        self._fanta_page = get_page_str(fanta_page)
        self._load_page_data(volume, self._fanta_page)

        init_group_ids = (
            (self._easy_pane, easyocr_group_id),
            (self._pad_pane, paddleocr_group_id),
        )
        for pane, gid in init_group_ids:
            sid = str(gid)
            if sid not in pane.speech_groups:
                sid = next(iter(pane.speech_groups), sid)
            self._set_group_id(pane, sid)

        if self._queue:
            self.queue_progress_text = f"{queue_index + 1} / {len(self._queue)}"

        Window.bind(on_request_close=self.on_request_close)
        Window.bind(on_key_down=self._on_key_down)

    def _other_pane(self, pane: EnginePane) -> EnginePane:
        """Return the opposite engine pane."""
        return self._pad_pane if pane is self._easy_pane else self._easy_pane

    # ── page / queue loading ──────────────────────────────────────────────────

    def _load_page_data(self, volume: int, fanta_page: str) -> None:
        """Load both OCR speech groups for a given volume + page."""
        self._volume = volume
        self._fanta_page = fanta_page

        title_str, dest_page = get_title_from_volume_page(self._comics_database, volume, fanta_page)
        self._title = STR_TITLE_TO_ENUM[title_str]
        dest_page_str = get_page_str(dest_page)

        for pane in self._panes:
            pane.page_group = get_speech_page_group(
                self._comics_database,
                volume,
                self._title,
                pane.ocr_type,
                fanta_page,
                dest_page_str,
            )
            pane.speech_groups = pane.page_group.speech_groups

        self._srce_image_file = self._get_srce_image_file(title_str, fanta_page)
        segments_dir = Path(
            self._comics_database.get_fantagraphics_panel_segments_volume_dir(volume)
        )
        self._panel_segments_file = segments_dir / (fanta_page + ".json")

    def _get_srce_image_file(self, title_str: str, fanta_page: str) -> Path:
        if STR_TITLE_TO_ENUM[title_str] in ONE_PAGERS:
            # One-pagers have no ini file, so 'get_comic_book' can't resolve them.
            # Their restored page lives directly in the volume's restored image dir.
            return Path(
                self._comics_database.get_fantagraphics_restored_volume_image_dir(self._volume)
            ) / (fanta_page + PNG_FILE_EXT)

        comic = self._comics_database.get_comic_book(title_str)
        srce_image_file = comic.get_final_srce_story_file(fanta_page, PageType.BODY)
        return srce_image_file[0]

    def _load_queue_entry(self, index: int) -> None:
        """Load the queue entry at *index* and refresh the entire UI."""
        entry = self._queue[index]
        self._queue_index = index
        self._has_changes = False

        fanta_page_str = get_page_str(entry.fanta_page)
        self._load_page_data(entry.volume, fanta_page_str)

        primary_id = str(entry.group_id)
        if entry.engine == "easyocr":
            primary, secondary = self._easy_pane, self._pad_pane
        else:
            primary, secondary = self._pad_pane, self._easy_pane

        for pane, gid in ((primary, primary_id), (secondary, primary_id)):
            resolved = gid if gid in pane.speech_groups else next(iter(pane.speech_groups), None)
            if resolved:
                self._set_group_id(pane, resolved)

        self.queue_progress_text = f"{index + 1} / {len(self._queue)}"

        for pane in self._panes:
            if pane.canvas is not None:
                self._load_canvas_content(pane)
        if self._info_label is not None:
            self._info_label.text = self._get_editor_info()

    # ── canvas / image helpers ────────────────────────────────────────────────

    def _load_canvas_content(self, pane: EnginePane) -> None:
        """Refresh the BoundingBoxCanvas for the given engine pane."""
        panel_num = (pane.json_group() or {}).get("panel_num", -1)
        self._load_engine_canvas_content(pane, panel_num)

    def _load_engine_canvas_content(self, pane: EnginePane, panel_num: int) -> None:
        """Parameterized canvas refresh for one engine."""
        canvas = pane.canvas
        if canvas is None:
            return

        group_json = pane.json_group()
        if group_json is None:
            logger.warning(f"Group {pane.group_id} not found in JSON for canvas refresh.")
            return

        text_box = group_json.get("text_box", [])
        if not text_box:
            logger.warning(f"Group {pane.group_id} has no text_box.")
            return

        if not self._srce_image_file.is_file():
            logger.warning(f'Source image not found: "{self._srce_image_file}".')
            return

        full_img = load_pil_image_for_reading(self._srce_image_file)
        img_w, img_h = full_img.size

        if panel_num <= 0:
            # Unknown panel: show wider crop and overlay all panel outlines
            logger.warning(f'Panel num not known for group: "{pane.group_id}".')
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
                panel_num=panel_num,
            )
            logger.debug(
                f"Panel {panel_num}: text_box = {text_box}, panel_bounds = {panel_bounds}."
            )

    # ── App lifecycle ─────────────────────────────────────────────────────────

    def build(self) -> Widget:
        for pane in self._panes:
            setattr(self, pane.text_prop, pane.speech_groups[pane.group_id].raw_ai_text)

        widget = self._create_editor_widget()

        for pane in self._panes:
            self._load_canvas_content(pane)

        return widget

    def on_request_close(self, *_args: object) -> bool:
        if not self._has_changes:
            return False
        self._show_exit_popup()
        return True  # prevent immediate close

    def _on_key_down(
        self,
        _window: object,
        key: int,
        _scancode: int,
        _codepoint: str | None,
        modifier: list[str],
    ) -> bool:
        """Global keyboard shortcuts.

        Ctrl+Enter — Save & Next (queue mode) or Save (single mode).
        Ctrl+S     — Save without advancing.
        """
        if "ctrl" not in modifier:
            return False
        # Enter (13) or numpad Enter (271)
        if key in (13, 271):
            if self._queue:
                self._handle_save_and_next(renumber=True)
            else:
                self._handle_save(renumber=True)
            return True
        if key == ord("s"):
            self._handle_save(renumber=True)
            return True
        return False

    def _show_exit_popup(self) -> None:
        self._show_confirm_popup(
            title="Unsaved Changes",
            message="There are unsaved changes.\nAre you sure you want to exit?",
            on_confirm=self.stop,
            confirm_label="Yes, exit",
            cancel_label="No, go back",
            size=(420, 200),
        )

    # ── pane callbacks (text, box, panel_num) ────────────────────────────────

    def _on_text_changed(self, pane: EnginePane, instance: TextInput, _value: str) -> None:
        """Handle text edit in a pane's TextInput."""
        if not instance.focus:
            return
        pane.speech_groups[pane.group_id] = replace(
            pane.speech_groups[pane.group_id],
            raw_ai_text=self._get_current_text(pane),
        )
        self._has_changes = True

    def _on_box_changed(self, pane: EnginePane, new_text_box: list) -> None:
        """Handle a bounding box change reported by a canvas."""
        json_group = pane.json_group()
        if json_group is not None:
            json_group["text_box"] = new_text_box
        self._has_changes = True
        logger.debug(f"{pane.name} text box updated to: {new_text_box}")

    def _on_panel_num_confirmed(self, pane: EnginePane, instance: TextInput) -> None:
        """Validate and apply a panel_num TextInput value."""
        json_group = pane.json_group()
        current = json_group.get("panel_num", -1) if json_group else -1
        try:
            new_num = int(instance.text.strip())
        except ValueError:
            instance.text = str(current)
            return
        if new_num != current and json_group is not None:
            json_group["panel_num"] = new_num
            self._load_canvas_content(pane)
            self._has_changes = True

    @staticmethod
    def _update_panel_num_input_color(instance: TextInput, value: str) -> None:
        """Color the panel_num TextInput background red when the value is -1."""
        try:
            is_unassigned = int(value.strip()) < 0
        except ValueError:
            is_unassigned = True
        instance.background_color = (1.0, 0.4, 0.4, 1) if is_unassigned else (1, 1, 1, 1)

    # ── group / panel helpers ─────────────────────────────────────────────────

    def _commit_panel_nums(self) -> None:
        """Flush any pending panel_num TextInput edits to the in-memory JSON.

        Must be called before any navigation or save that changes the current group_id,
        because the focus-loss callback is not guaranteed to fire before on_press.
        """
        for pane in self._panes:
            if pane.panel_num_input is not None:
                self._on_panel_num_confirmed(pane, pane.panel_num_input)

    def _set_group_id(self, pane: EnginePane, group_id: str) -> None:
        """Switch a pane to show a different group."""
        if group_id not in pane.speech_groups:
            msg = f"Unknown {pane.name} group id '{group_id}'."
            raise ValueError(msg)
        pane.group_id = group_id
        speech_group = pane.speech_groups[group_id]
        pane.label = self._get_ocr_label(
            pane.name, group_id, self._get_pane_type(pane), self._get_pane_florence_ack(pane)
        )
        # Always push the label to the StringProperty so the header updates even
        # when the text value doesn't change (Kivy skips dispatch for same values).
        setattr(self, pane.label_prop, pane.label)
        setattr(
            self,
            pane.text_prop,
            self._encode_for_display(speech_group.raw_ai_text)
            if self._decode_checkbox and self._decode_checkbox.active
            else speech_group.raw_ai_text,
        )
        # Read from live JSON, not SpeechText — the dataclass is never updated after load,
        # so returning to a previously-edited group would restore the stale original value.
        panel_num = (pane.json_group(group_id) or {}).get("panel_num", speech_group.panel_num)
        self._set_panel_num(pane, panel_num)

    def _set_panel_num(self, pane: EnginePane, panel_num: int) -> None:
        """Update panel_num in the JSON dict and the panel_num input widget."""
        json_group = pane.json_group()
        if json_group is not None:
            json_group["panel_num"] = panel_num
        if pane.panel_num_input is not None:
            pane.panel_num_input.text = str(panel_num)

    @staticmethod
    def _get_ocr_label(ocr_name: str, group_id: str, type_name: str, florence_ack: bool) -> str:
        flor_state = "ack" if florence_ack else "-"
        return f"{ocr_name}: group_id: {group_id} ({type_name})  [flor: {flor_state}]"

    def _get_pane_type(self, pane: EnginePane) -> str:
        return (pane.json_group() or {}).get("type") or DEFAULT_TYPE

    @staticmethod
    def _get_pane_florence_ack(pane: EnginePane) -> bool:
        group = pane.json_group()
        if group is None:
            return False
        return FLORENCE_CHECK_ISSUE_TYPE in (group.get("acknowledged_issues") or [])

    def _refresh_pane_labels(self) -> None:
        """Re-compute both panes' header labels and push to their label props.

        Preserves any current 'DIFFS -- ' prefix the diff-highlighter has set so
        the diff state isn't lost on a type-only refresh.
        """
        for pane in self._panes:
            pane.label = self._get_ocr_label(
                pane.name,
                pane.group_id,
                self._get_pane_type(pane),
                self._get_pane_florence_ack(pane),
            )
            current_prop: str = getattr(self, pane.label_prop)
            if current_prop.startswith("DIFFS -- "):
                setattr(self, pane.label_prop, f"DIFFS -- {pane.label}")
            else:
                setattr(self, pane.label_prop, pane.label)

    # ── info text ─────────────────────────────────────────────────────────────

    def _get_editor_info(self) -> str:
        info = (
            f'"{ENUM_TO_STR_TITLE[self._title]}"'
            f"  |  Volume {self._volume} |  Page {self._fanta_page}"
        )
        if self._queue:
            engine = self._queue[self._queue_index].engine
            issue_type = self._queue[self._queue_index].issue_type
            info += f"  |  {engine} - {issue_type}"
        return info

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
            height=38,
            font_size="16sp",
            halign="center",
            valign="middle",
            color=(1, 1, 0, 1),
        )
        self._info_label.bind(size=self._info_label.setter("text_size"))

        easy_col, label_easy, ti_easy = self._build_engine_column(self._easy_pane)
        pad_col, label_pad, ti_pad = self._build_engine_column(self._pad_pane)

        pane_labels = ((self._easy_pane, label_easy), (self._pad_pane, label_pad))

        def update_diff_labels(*_args: object) -> None:
            try:
                t1 = ti_easy.text
                t2 = ti_pad.text
                if self._decode_checkbox.active:
                    t1 = self._decode_from_display(t1)
                    t2 = self._decode_from_display(t2)
                if t1 != t2:
                    for pane, lbl in pane_labels:
                        setattr(self, pane.label_prop, f"DIFFS -- {pane.label}")
                        lbl.color = (1, 0, 0, 1)
                else:
                    for pane, lbl in pane_labels:
                        setattr(self, pane.label_prop, pane.label)
                        lbl.color = (1, 1, 1, 1)
            except UnicodeDecodeError:
                pass
            self._update_diff_highlight(ti_easy, ti_pad)

        def refresh_on_unfocus(_instance: TextInput, focused: bool) -> None:
            if not focused:
                update_diff_labels()

        ti_easy.bind(text=update_diff_labels)
        ti_pad.bind(text=update_diff_labels)
        ti_easy.bind(focus=refresh_on_unfocus)
        ti_pad.bind(focus=refresh_on_unfocus)
        update_diff_labels()

        columns = BoxLayout(orientation="horizontal", spacing=10)
        columns.add_widget(easy_col)
        columns.add_widget(pad_col)

        content = BoxLayout(orientation="vertical", spacing=18, padding=10)
        content.add_widget(self._info_label)
        content.add_widget(columns)
        content.add_widget(bottom)
        return content

    def _build_engine_column(self, pane: EnginePane) -> tuple[BoxLayout, Label, TextInput]:
        """Build one engine column: header -> text input -> buttons -> canvas."""
        col = BoxLayout(orientation="vertical", spacing=4)

        # Header row: engine label (left) + panel_num input (right)
        header_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=28, spacing=6)
        label_widget = Label(
            text=getattr(self, pane.label_prop),
            bold=True,
            size_hint_x=1,
            halign="left",
            valign="middle",
        )
        label_widget.bind(size=label_widget.setter("text_size"))
        self.bind(**{pane.label_prop: label_widget.setter("text")})
        label_widget.bind(text=self.setter(pane.label_prop))
        header_row.add_widget(label_widget)
        header_row.add_widget(Label(text="panel:", size_hint_x=None, width=50, font_size="13sp"))
        initial_panel_num = (pane.json_group() or {}).get("panel_num", -1)
        pane.panel_num_input = TextInput(
            text=str(initial_panel_num),
            multiline=False,
            font_size="14sp",
            size_hint_x=None,
            width=55,
            size_hint_y=None,
            height=28,
        )
        pane.panel_num_input.bind(
            on_text_validate=lambda inst, p=pane: self._on_panel_num_confirmed(p, inst)
        )
        pane.panel_num_input.bind(
            focus=lambda inst, focused, p=pane: (
                self._on_panel_num_confirmed(p, inst) if not focused else None
            )
        )
        pane.panel_num_input.bind(text=self._update_panel_num_input_color)
        self._update_panel_num_input_color(pane.panel_num_input, str(initial_panel_num))
        header_row.add_widget(pane.panel_num_input)
        col.add_widget(header_row)

        # Text input
        text_input = TextInput(
            text=getattr(self, pane.text_prop),
            font_name=OPEN_SANS_FONT,
            font_size="20sp",
            multiline=True,
            size_hint_y=None,
            height=350,
            padding=10,
            hint_text=f"Edit {pane.name} text here...",
        )
        self.bind(**{pane.text_prop: text_input.setter("text")})
        text_input.bind(text=self.setter(pane.text_prop))
        text_input.bind(text=lambda inst, val, p=pane: self._on_text_changed(p, inst, val))
        setattr(self, pane.text_prop, self._encode_for_display(getattr(self, pane.text_prop)))
        col.add_widget(text_input)

        # Per-engine action buttons
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=36, spacing=6)
        for btn_text, handler in (
            ("Prev", lambda _inst, p=pane: self._handle_prev(p)),
            ("Next", lambda _inst, p=pane: self._handle_next(p)),
            ("Select", lambda _inst, p=pane: self._show_speech_item_popup_for(p)),
            ("Copy In", lambda _inst, p=pane: self._handle_copy_in(p)),
            ("Copy Fmt", lambda _inst, p=pane: self._handle_copy_fmt(p)),
            ("Mark OK", lambda _inst, p=pane: self._show_acknowledge_popup(p)),
            ("Delete", lambda _inst, p=pane: self._handle_delete(p)),
        ):
            btn = Button(text=btn_text, size_hint_y=None, height=36)
            btn.bind(on_press=handler)
            btn_row.add_widget(btn)
        col.add_widget(btn_row)

        # Canvas below buttons
        pane.canvas = BoundingBoxCanvas(
            on_box_changed=lambda tb, p=pane: self._on_box_changed(p, tb),
            size_hint_y=1,
        )
        col.add_widget(pane.canvas)

        return col, label_widget, text_input

    def _get_bottom_layout(self) -> BoxLayout:
        # Single global bar: checkbox on the left, save/skip on the right
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=44, spacing=10)

        checkbox_layout, self._decode_checkbox = self._add_decode_checkbox()
        checkbox_layout.size_hint_x = None
        checkbox_layout.width = 160
        row.add_widget(checkbox_layout)

        prev_both_btn = Button(
            text="Both Prev", size_hint_x=None, width=100, size_hint_y=None, height=44
        )
        prev_both_btn.bind(on_press=self._handle_both_prev)
        row.add_widget(prev_both_btn)

        next_both_btn = Button(
            text="Both Next", size_hint_x=None, width=100, size_hint_y=None, height=44
        )
        next_both_btn.bind(on_press=self._handle_both_next)
        row.add_widget(next_both_btn)

        row.add_widget(Widget())  # spacer

        row.add_widget(self._get_save_button())

        set_type_btn = Button(
            text="Set Type", size_hint_x=None, width=110, size_hint_y=None, height=44
        )
        set_type_btn.bind(on_press=lambda _: self._show_type_popup())
        row.add_widget(set_type_btn)

        set_flor_btn = Button(
            text="Set Flor", size_hint_x=None, width=110, size_hint_y=None, height=44
        )
        set_flor_btn.bind(on_press=lambda _: self._apply_florence_ack_to_current_groups())
        row.add_widget(set_flor_btn)

        if not self._queue:
            row.add_widget(self._get_save_exit_button())
        else:
            row.add_widget(self._get_save_next_queue_item_button())

            skip_btn = Button(text="Skip", size_hint_x=None, width=90, size_hint_y=None, height=44)
            skip_btn.bind(on_press=lambda _: self._handle_skip())
            row.add_widget(skip_btn)

            queue_label = Label(
                text=self.queue_progress_text,
                size_hint_x=None,
                width=100,
                font_size="15sp",
                bold=True,
            )
            self.bind(queue_progress_text=queue_label.setter("text"))
            row.add_widget(queue_label)

        return row

    def _add_decode_checkbox(self) -> tuple[BoxLayout, CheckBox]:
        checkbox_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
        decode_checkbox = CheckBox(active=True, size_hint_x=None, width=30)
        decode_label = Label(text="Show Unicode", halign="left", valign="middle")
        decode_label.bind(size=decode_label.setter("text_size"))

        def on_checkbox_active(_instance: CheckBox, value: bool) -> None:
            try:
                for pane in self._panes:
                    text = getattr(self, pane.text_prop)
                    if value:
                        setattr(self, pane.text_prop, self._encode_for_display(text))
                    else:
                        setattr(self, pane.text_prop, self._decode_from_display(text))
            except UnicodeDecodeError as e:
                logger.exception(f"Error converting text: {e}")

        decode_checkbox.bind(active=on_checkbox_active)
        checkbox_layout.add_widget(decode_checkbox)
        checkbox_layout.add_widget(decode_label)
        return checkbox_layout, decode_checkbox

    # ── type popup ────────────────────────────────────────────────────────────

    def _apply_type_to_current_groups(self, type_name: str) -> None:
        """Write *type_name* to both panes' currently selected group's JSON."""
        changed = False
        for pane in self._panes:
            json_group = pane.json_group()
            if json_group is None:
                continue
            if json_group.get("type") != type_name:
                json_group["type"] = type_name
                changed = True
        if changed:
            self._has_changes = True
            self._refresh_pane_labels()
            logger.debug(f'Type set to "{type_name}" for both panes\' current groups.')

    def _apply_florence_ack_to_current_groups(self) -> None:
        """Add ``florence-check`` to acknowledged_issues on both panes' current groups."""
        changed = False
        affected: list[str] = []
        for pane in self._panes:
            json_group = pane.json_group()
            if json_group is None:
                continue
            acked = list(json_group.get("acknowledged_issues") or [])
            if FLORENCE_CHECK_ISSUE_TYPE not in acked:
                acked.append(FLORENCE_CHECK_ISSUE_TYPE)
                json_group["acknowledged_issues"] = acked
                changed = True
            affected.append(pane.name)
        if changed:
            self._has_changes = True
            self._refresh_pane_labels()
            logger.debug(f"florence-check acknowledged on {', '.join(affected)} current groups.")

    def _show_type_popup(self) -> None:
        """Show a popup with type radio buttons; on Save, apply to both panes.

        For 'title_page' queue entries the radio defaults to 'title'; otherwise
        it reflects the current JSON value (falling back to 'dialogue').
        Nothing is applied unless the user presses Save.
        """
        if self._queue and self._queue[self._queue_index].issue_type == TITLE_PAGE_ISSUE_TYPE:
            current = TITLE_PAGE_DEFAULT_TYPE
        else:
            current = (self._easy_pane.json_group() or {}).get("type") or DEFAULT_TYPE
        if current not in TYPE_OPTIONS:
            current = DEFAULT_TYPE

        radios: dict[str, CheckBox] = {}

        content = BoxLayout(orientation="vertical", padding=10, spacing=8)
        content.add_widget(
            Label(
                text="Set type — applies to both panes' current groups",
                size_hint_y=None,
                height=28,
                bold=True,
            )
        )

        for type_name in TYPE_OPTIONS:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=34, spacing=8)
            cb = CheckBox(
                group="set_type_popup",
                active=(type_name == current),
                size_hint_x=None,
                width=30,
            )
            radios[type_name] = cb
            lbl = Label(text=type_name, halign="left", valign="middle")
            lbl.bind(size=lbl.setter("text_size"))
            row.add_widget(cb)
            row.add_widget(lbl)
            content.add_widget(row)

        button_layout = BoxLayout(spacing=10, size_hint_y=None, height=44)
        popup = Popup(
            title="Set type",
            content=content,
            size_hint=(None, None),
            size=(440, 360),
            auto_dismiss=False,
        )

        def on_save(_inst: Button) -> None:
            selected = next((t for t, c in radios.items() if c.active), None)
            if selected is not None:
                self._apply_type_to_current_groups(selected)
            popup.dismiss()

        save_btn = Button(text="Save")
        save_btn.bind(on_press=on_save)
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_press=lambda _: popup.dismiss())
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        popup.open()

    # ── speech item popups ────────────────────────────────────────────────────

    def _show_speech_item_popup_for(self, pane: EnginePane) -> None:
        """Show the group selection popup for a pane."""
        items = [
            SpeechItem(panel_num=data.panel_num, group_id=gid, text=data.raw_ai_text or "")
            for gid, data in pane.speech_groups.items()
        ]
        self._show_speech_item_popup(
            f"Select {pane.name} Speech Item",
            items,
            lambda item, p=pane: self._on_speech_item_selected(p, item),
        )

    def _on_speech_item_selected(self, pane: EnginePane, speech_item: SpeechItem) -> None:
        self._commit_panel_nums()
        self._set_group_id(pane, speech_item.group_id)
        self._load_canvas_content(pane)

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

    # ── save / delete / navigation ────────────────────────────────────────────

    def _get_save_button(self) -> Button:
        btn = Button(text="Save", size_hint_x=None, width=150, size_hint_y=None, height=46)

        def on_save(_instance: Button) -> None:
            self._handle_save()
            for pane in self._panes:
                self._load_canvas_content(pane)

        btn.bind(on_press=on_save)
        return btn

    def _get_save_exit_button(self) -> Button:
        btn = Button(text="Save & Exit", size_hint_x=None, width=150, size_hint_y=None, height=46)

        def on_save(_instance: Button) -> None:
            self._handle_save(renumber=True)
            self.stop()

        btn.bind(on_press=on_save)
        return btn

    def _get_save_next_queue_item_button(self) -> Button:
        btn = Button(text="Save & Next", size_hint_x=None, width=150, size_hint_y=None, height=46)
        btn.bind(on_press=lambda _: self._handle_save_and_next(renumber=True))

        return btn

    def _get_current_text(self, pane: EnginePane) -> str:
        """Return the current decoded text for a pane."""
        text = getattr(self, pane.text_prop)
        return self._decode_from_display(text) if self._decode_checkbox.active else text

    def _handle_save(self, *, renumber: bool = False) -> None:
        """Save text, panel_num, and text_box changes to both OCR JSON files."""
        self._commit_panel_nums()
        for pane in self._panes:
            self._save_pane(pane, renumber=renumber)
        self._has_changes = False

    def _save_pane(self, pane: EnginePane, *, renumber: bool = False) -> None:
        """Sync in-memory edits to speech_page_json and write to disk.

        panel_num is already synced to speech_page_json via _set_panel_num /
        _on_panel_num_confirmed, so only text and text_box need updating here.
        """
        ocr_file = pane.page_group.ocr_prelim_groups_json_file
        backup_file = self._get_prelim_ocr_backup_file(ocr_file)

        # Sync text for all groups whose raw_ai_text has changed
        changed = False
        for gid, speech_text in pane.speech_groups.items():
            json_group = pane.json_group(gid)
            if json_group is None:
                continue
            if speech_text.raw_ai_text != json_group.get("ai_text"):
                json_group["ai_text"] = speech_text.raw_ai_text
                changed = True

        # Sync text_box from canvas (panel_num already updated in json_group)
        json_group = pane.json_group()
        if json_group is not None and pane.canvas is not None:
            new_text_box = pane.canvas.get_text_box_full_page()
            if new_text_box and new_text_box != json_group.get("text_box"):
                json_group["text_box"] = new_text_box
                changed = True

        if renumber and pane.page_group.renumber_groups():
            changed = True

        # panel_num changes are tracked via _has_changes but already in json_group;
        # save if anything changed or if we have pending panel_num edits.
        if changed or self._has_changes:
            pane.page_group.save_json(backup_file=backup_file)
            logger.info(f'Saved changes to "{ocr_file}". Backup at "{backup_file}".')
        else:
            logger.debug(f'No changes in "{ocr_file}".')

    def _handle_save_and_next(self, *, renumber: bool = False) -> None:
        self._handle_save(renumber=renumber)
        self._advance_queue()

    def _handle_skip(self) -> None:
        if self._has_changes:
            self._show_confirm_popup(
                title="Unsaved Changes",
                message="You have unsaved changes.\nSkip and discard them?",
                on_confirm=self._do_skip,
            )
        else:
            self._do_skip()

    def _do_skip(self) -> None:
        self._has_changes = False
        self._advance_queue()

    def _handle_both_prev(self, _instance: object = None) -> None:
        for pane in self._panes:
            self._handle_prev(pane)

    def _handle_both_next(self, _instance: object = None) -> None:
        for pane in self._panes:
            self._handle_next(pane)

    def _handle_step(self, pane: EnginePane, direction: int) -> None:
        """Step to the previous (direction=-1) or next (direction=+1) group in a pane.

        If the current group_id isn't in the list, the step lands on the "edge"
        appropriate for the direction (prev → last group, next → first group).
        """
        group_ids = list(pane.speech_groups.keys())
        if not group_ids:
            return
        self._commit_panel_nums()
        try:
            idx = group_ids.index(pane.group_id)
        except ValueError:
            idx = 0 if direction < 0 else -1
        self._set_group_id(pane, group_ids[(idx + direction) % len(group_ids)])
        self._load_canvas_content(pane)

    def _handle_prev(self, pane: EnginePane) -> None:
        self._handle_step(pane, -1)

    def _handle_next(self, pane: EnginePane) -> None:
        self._handle_step(pane, 1)

    def _handle_copy_in(self, target: EnginePane) -> None:
        """Copy the current group from the other engine into a new group in target."""
        source = self._other_pane(target)
        self._copy_group_from_other_engine(source, target)

    def _handle_copy_fmt(self, target: EnginePane) -> None:
        """Re-wrap *target* pane's text to match the opposite pane's line pattern."""
        source = self._other_pane(target)
        pattern_text = getattr(self, source.text_prop)
        current_text = getattr(self, target.text_prop)
        new_text = self._apply_line_pattern(current_text, pattern_text)
        if new_text == current_text:
            return
        setattr(self, target.text_prop, new_text)
        # _on_text_changed only fires when the TextInput is focused, so sync
        # raw_ai_text and the change flag explicitly.
        decoded = self._decode_from_display(new_text) if self._decode_checkbox.active else new_text
        target.speech_groups[target.group_id] = replace(
            target.speech_groups[target.group_id],
            raw_ai_text=decoded,
        )
        self._has_changes = True

    @staticmethod
    def _apply_line_pattern(source_text: str, pattern_text: str) -> str:
        """Re-wrap source_text so each line holds the same word count as pattern_text.

        Trailing blank lines in pattern_text are ignored. The final pattern line
        absorbs any leftover words from source_text. If source_text has fewer
        words than the pattern expects, unfilled trailing lines are dropped.
        """
        pattern_lines = pattern_text.rstrip("\n").split("\n")
        line_counts = [len(ln.split()) for ln in pattern_lines]
        if not line_counts:
            return source_text

        words = source_text.split()
        if not words:
            return ""

        out: list[str] = []
        i = 0
        last_idx = len(line_counts) - 1
        for idx, count in enumerate(line_counts):
            if idx == last_idx:
                out.append(" ".join(words[i:]))
                break
            if i >= len(words):
                break
            out.append(" ".join(words[i : i + count]))
            i += count
        return "\n".join(out)

    # ── diff highlighting ────────────────────────────────────────────────────

    @staticmethod
    def _first_diff_index(a: str, b: str) -> int | None:
        """Return the first index where a and b differ, or None if equal."""
        min_len = min(len(a), len(b))
        for i in range(min_len):
            if a[i] != b[i]:
                return i
        return min_len if len(a) != len(b) else None

    @staticmethod
    def _diff_highlight_range(text: str, start: int, max_chars: int = 30) -> tuple[int, int]:
        """Return (start, end) for a highlight running to end-of-line or max_chars."""
        n = len(text)
        if start >= n:
            return n, n
        nl = text.find("\n", start)
        end = n if nl == -1 else nl
        end = min(end, start + max_chars)
        if end == start:
            end = min(start + 1, n)
        return start, end

    def _update_diff_highlight(self, ti_a: TextInput, ti_b: TextInput) -> None:
        """Select the first diff range in both TextInputs, or clear if equal.

        Skips the update while either input has focus so the user's cursor
        and in-progress selection are not disturbed while editing.
        """
        if ti_a.focus or ti_b.focus:
            return
        text_a = ti_a.text
        text_b = ti_b.text
        diff_idx = self._first_diff_index(text_a, text_b)
        if diff_idx is None:
            ti_a.cancel_selection()
            ti_b.cancel_selection()
            return
        start_a, end_a = self._diff_highlight_range(text_a, diff_idx)
        start_b, end_b = self._diff_highlight_range(text_b, diff_idx)
        if start_a < end_a:
            ti_a.select_text(start_a, end_a)
        else:
            ti_a.cancel_selection()
        if start_b < end_b:
            ti_b.select_text(start_b, end_b)
        else:
            ti_b.cancel_selection()

    def _copy_group_from_other_engine(self, source: EnginePane, target: EnginePane) -> None:
        """Copy a group from one engine into a new group in the other engine.

        The new group is inserted immediately after the target's current group_id in
        both the JSON groups dict and the in-memory speech_groups dict so that
        positional ordering is preserved.
        """
        source_group = source.json_group()
        if source_group is None:
            logger.warning(f"Source group {source.group_id} not found.")
            return

        target_json_groups = target.json_groups()
        new_id = str(max((int(k) for k in target_json_groups), default=-1) + 1)

        new_group = copy.deepcopy(source_group)
        new_group["ocr_text"] = ""
        new_group["cleaned_box_texts"] = {}

        ai_text = new_group.get("ai_text", "")
        new_speech_text = SpeechText(
            group_id=new_id,
            panel_num=new_group.get("panel_num", -1),
            raw_ai_text=ai_text,
            ai_text=ai_text.replace("-\n", "-").replace("\u00ad\n", "").replace("\u200b\n", ""),
            type=new_group.get("type", "dialogue"),
            text_box=new_group.get("text_box", []),
        )

        # Rebuild both dicts with the new entry inserted after the target's current group.
        target.page_group.speech_page_json["groups"] = self._insert_after(
            target_json_groups, target.group_id, new_id, new_group
        )
        rebuilt = self._insert_after(target.speech_groups, target.group_id, new_id, new_speech_text)
        target.speech_groups.clear()
        target.speech_groups.update(rebuilt)

        self._commit_panel_nums()
        self._set_group_id(target, new_id)
        self._load_canvas_content(target)
        self._has_changes = True
        logger.info(f"Copied group {source.group_id} as new group {new_id}.")

    @staticmethod
    def _insert_after(d: dict, after_key: str, new_key: str, new_value: object) -> dict:
        """Return a new dict with *new_key* inserted right after *after_key*."""
        result: dict = {}
        inserted = False
        for k, v in d.items():
            result[k] = v
            if k == after_key:
                result[new_key] = new_value
                inserted = True
        if not inserted:
            result[new_key] = new_value
        return result

    def _handle_delete(self, pane: EnginePane) -> None:
        """Delete the current group from a pane and navigate to the neighbor."""
        # Find the best neighbor (previous, or next if first) before removing.
        group_ids = list(pane.speech_groups.keys())
        try:
            idx = group_ids.index(pane.group_id)
        except ValueError:
            idx = -1
        if idx > 0:
            neighbor_id = group_ids[idx - 1]
        elif idx == 0 and len(group_ids) > 1:
            neighbor_id = group_ids[1]
        else:
            neighbor_id = None

        json_groups = pane.json_groups()
        if pane.group_id in json_groups:
            del json_groups[pane.group_id]
        pane.speech_groups.pop(pane.group_id, None)
        logger.info(f"Deleted group {pane.group_id} from in-memory data (not yet saved).")

        self._has_changes = True

        if neighbor_id is not None:
            self._set_group_id(pane, neighbor_id)
            self._load_canvas_content(pane)
        else:
            self._show_confirm_popup(
                title="No Groups Remaining",
                message=f"All {pane.name} groups have been deleted.\nClose the editor?",
                on_confirm=self.stop,
            )

    def _show_acknowledge_popup(self, pane: EnginePane) -> None:
        """Toggle which dismissable ocr_check issues are acknowledged on this group.

        Acknowledged types are skipped on future ocr_check runs. The popup
        shows whether each type is currently firing on the live group, but
        does not gate the checkbox — the user may pre-acknowledge or clear a
        stale entry.
        """
        group = pane.json_group()
        if group is None:
            logger.warning(f"Group {pane.group_id} not found for acknowledge popup.")
            return

        current = set(group.get("acknowledged_issues") or [])
        checkboxes: dict[str, CheckBox] = {}

        content = BoxLayout(orientation="vertical", padding=10, spacing=8)
        content.add_widget(
            Label(
                text=f"Mark OK — {pane.name} group {pane.group_id}",
                size_hint_y=None,
                height=28,
                bold=True,
            )
        )

        for issue_type in DISMISSABLE_ISSUE_TYPES:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=34, spacing=8)
            firing = DISMISSABLE_PREDICATES[issue_type](group)
            cb = CheckBox(active=firing or issue_type in current, size_hint_x=None, width=30)
            checkboxes[issue_type] = cb
            status = "firing" if firing else "not firing"
            lbl = Label(text=f"{issue_type}  ({status})", halign="left", valign="middle")
            lbl.bind(size=lbl.setter("text_size"))
            row.add_widget(cb)
            row.add_widget(lbl)
            content.add_widget(row)

        button_layout = BoxLayout(spacing=10, size_hint_y=None, height=44)
        popup = Popup(
            title="Acknowledge issues",
            content=content,
            size_hint=(None, None),
            size=(460, 380),
            auto_dismiss=False,
        )

        def on_save(_inst: Button) -> None:
            new_list = [t for t in DISMISSABLE_ISSUE_TYPES if checkboxes[t].active]
            if new_list:
                group["acknowledged_issues"] = new_list
            elif "acknowledged_issues" in group:
                del group["acknowledged_issues"]
            self._has_changes = True
            self._refresh_pane_labels()
            popup.dismiss()

        save_btn = Button(text="Save")
        save_btn.bind(on_press=on_save)
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_press=lambda _: popup.dismiss())
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        popup.open()

    @staticmethod
    def _show_confirm_popup(  # noqa: PLR0913
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        confirm_label: str = "Yes",
        cancel_label: str | None = "Cancel",
        size: tuple[int, int] = (440, 200),
        auto_dismiss: bool = False,
    ) -> None:
        """Show a confirm popup; ``cancel_label=None`` produces a single-button popup."""
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text=message))
        button_layout = BoxLayout(spacing=10, size_hint_y=None, height=44)
        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=size,
            auto_dismiss=auto_dismiss,
        )
        yes_btn = Button(text=confirm_label)
        yes_btn.bind(on_press=lambda _: (popup.dismiss(), on_confirm()))
        button_layout.add_widget(yes_btn)
        if cancel_label is not None:
            no_btn = Button(text=cancel_label)
            no_btn.bind(on_press=lambda _: popup.dismiss())
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
        self._show_confirm_popup(
            title="Queue Complete",
            message="All queue entries have been processed.",
            on_confirm=self.stop,
            confirm_label="Close",
            cancel_label=None,
            size=(360, 160),
            auto_dismiss=True,
        )

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
    log_level_str: LogLevelArg = "DEBUG",
) -> None:
    init_logging(APP_LOGGING_NAME, "kivy-prelim-ocr-editor.log", log_level_str)

    if queue_file is not None:
        queue = load_queue_file(queue_file)
        if not queue:
            logger.error(f'Queue file "{queue_file}" contains no valid entries.')
            raise typer.Exit(1)
        first = queue[0]
        EditorApp(
            volume=first.volume,
            fanta_page=first.fanta_page,
            easyocr_group_id=first.group_id,
            paddleocr_group_id=first.group_id,
            queue=queue,
            queue_index=0,
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
        ).run()


if __name__ == "__main__":
    app()

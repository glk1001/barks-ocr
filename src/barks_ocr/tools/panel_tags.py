"""Tag Fantagraphics panels (silhouettes first) and build per-title contact sheets.

Tags live in their own git repo beside the panel segments, one JSON file per page that
mirrors ``Fantagraphics-restored-panel-segments/<volume dir>/<page>.json``::

    {"panels": [{"index": 7, "box": [x, y, w, h],
                 "tags": {"silhouette": {"label": "yes", "source": "folder",
                                         "pixel_score": 0.3265, "note": ""}}}]}

``index`` is the 1-based position of the panel in the segments file and ``box`` is the
segments box, kept so that a regenerated segments file which renumbers its panels is
caught rather than silently mis-attributed. ``label`` is ``yes``, ``no``, ``unsure`` or
null (not yet labelled); ``source`` says who decided it.

``score`` measures the pixel silhouette score and never touches a label. It is a
ranking signal, not a gate: small distant silhouettes score like ordinary panels
(Back to the Klondike 30-7 scores 0.02), so a cut-off that keeps every silhouette lets
nearly every panel through.

``jev`` asks TypeSafe's Jev model yes/no silhouette questions per panel (one about
figures, one about scenery) and stores the higher probability as ``jev_score``, each
question's in ``jev_parts``, with ``jev_model`` and ``jev_question`` (the wording's
version). A panel already scored with the current wording is skipped, so a rerun pays
only for what is missing. It never touches a label either.

``irregular`` is a page-level tag, stored beside the panels as
``{"page": {"irregular_panels": {...}}, "panels": [...]}``: does the page have a panel that
is not a framed rectangle (slanted or cut, round, or borderless)? It is measured from the
page image, not the segments boxes, which are rectangles even round a triangular panel.
``irregular-label`` records a review of a volume's sheet by fanta page number; a page
labelled ``no`` leaves the list for good, since re-measuring never touches a label.
"""

# ruff: noqa: T201

import json
import math
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import typer
from barks_fantagraphics.comics_consts import PageType
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.fanta_comics_info import FIRST_VOLUME_NUMBER, LAST_VOLUME_NUMBER
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from loguru import logger

from barks_ocr.cli_setup import get_comic_titles, init_logging
from barks_ocr.utils.typesafe_jev import JevClient, NoulAnswers

APP_LOGGING_NAME = "ptag"

PANEL_TAGS_DIRNAME = "Fantagraphics-restored-panel-tags"
SHEETS_SUBDIR = "sheets"
SILHOUETTE = "silhouette"

# Pixel score: a silhouette is a large, THICK, flat near-black region, where line art is
# thin black strokes. Panels are resized to a fixed width so the thresholds are scale-free.
WORK_W = 600
BLACK_MAX = 70  # max(R,G,B) at or below this counts as black ink
CORE_R = 4.0  # distance to non-black (px at WORK_W) that makes ink "thick"; strokes are 1-3
MIN_BLOB_FRAC = 0.002  # a solid shape smaller than this share of the panel is ignored

THUMB_W, THUMB_H, SHEET_COLS = 300, 230, 6
CAPTION_H = 22
HEADER_H = 34
DEFAULT_NEAR_MISSES = 12
# An unlabelled panel is a sheet Candidate when Jev's v3 figure answer is at least
# CANDIDATE_FIGURE_MIN or its scenery answer at least CANDIDATE_SCENERY_MIN. Measured on
# 1,331 panels (76 known silhouettes, 250 known non-silhouettes, 12 titles): figure >= 0.6
# or scenery >= 0.95 caught all 76 and let in 17 known false alarms, against v2's 41. The
# scenery cut-off is lowered to 0.93 because two silhouettes rest on it alone (Frozen Gold
# 011:6 at 0.97, All at Sea 100:8 at 0.98): a missed silhouette costs more than a false
# alarm. The scenery answer alone is noisy, so taking max() of the two would undo this.
CANDIDATE_FIGURE_MIN = 0.6
CANDIDATE_SCENERY_MIN = 0.93
CANDIDATE_LEGACY_MIN = 0.7  # for a single-question (v1/v2) jev_score

# Bump JEV_QUESTION_VERSION whenever the wording changes, so old scores are re-asked.
# v3 asks two questions in one request (the image is shared state) and scores the panel
# by the higher: v2's single question let black clothing on a character whose face is
# drawn pass for a silhouette, so the figure question now turns on the face.
JEV_QUESTION_VERSION = "v3"
_JEV_PANEL = "`image` is one panel from a Carl Barks Donald Duck comic. "
JEV_QUESTIONS = {
    "figure": (
        _JEV_PANEL + "Is there at least one character or animal drawn as a silhouette: its "
        "whole body filled with flat black or one very dark colour INCLUDING its head and "
        "face (at most a white eye may show), so that its face, clothing and features are "
        "not drawn? Count it even when it is small or far away, or beside fully coloured "
        "characters. Do NOT count a character whose face is drawn and coloured, however "
        "much black it wears (Donald's black sailor jacket, a black coat or hat, a Beagle "
        "Boy's mask); a black-and-white animal such as a penguin or puffin; or a "
        "black-furred animal whose face, muzzle, teeth or claws are drawn in."
    ),
    "scenery": (
        _JEV_PANEL + "Is there at least one object or piece of scenery (a ship, plane, "
        "vehicle, building, skyline, tree or hill) drawn as a silhouette: a flat black or "
        "very dark shape against a lighter sky or background, with no windows, planks, "
        "panels or other detail drawn inside it? A silhouetted ship's masts and rigging may "
        "still show as lines. Do NOT count a vehicle or building painted a dark colour but "
        "drawn with its details; ordinary black outlines; shadows cast on the ground; dark "
        "doorways or windows; or dark shading in snow, ice or water."
    ),
}
DEFAULT_JEV_WORKERS = 8

# Irregular panels (page level). A panel is a region enclosed by "gutter": page-coloured
# pixels joined to the page edge. Its outline is traced at IRREG_WORK_W and scored twice:
#  - slant_px: the longest total of straight outline segments more than SLANT_ANGLE off
#    horizontal/vertical on any one panel (slanted dividers, cut corners, round panels);
#  - frameless: the largest share of any one panel's outline with no dark frame line
#    within FRAME_R and more than BOX_EDGE_D off the panel's bounding box (borderless
#    panels whose art fades into the page). An unframed edge lying ON the box is a
#    rectangle that lost its frame line, not a vignette: Back to the Klondike 061's
#    moon panel has none in the restored image, its fill running straight to the page.
# Calibrated on Lost in the Andes 020-040 and Back to the Klondike (eye-checked): real
# irregular pages scored slant 300-1900 or frameless 0.13-0.50; framed rectangular pages
# at most slant 106 and frameless 0.02. The cut-offs sit low, for recall.
IRREGULAR = "irregular_panels"
IRREGULAR_MEASURE = "v1"  # bump when the measure changes
IRREG_WORK_W = 1000
PAPER_TOL = 14  # max Lab channel distance from the page colour sampled at two corners
PAPER_CORNER = 20
MIN_PANEL_FRAC = 0.01  # smaller regions (page numbers, stray marks) are not panels
# A region with less frame ink than this share of its area is not a panel: Fantagraphics'
# pale one-colour decorations in the empty space below short gags (Vol. 1 565, 625) have
# no black line art at all, and every panel has some.
MIN_REGION_INK = 0.01
SLANT_EPSILON = 3.0  # approxPolyDP tolerance, px at IRREG_WORK_W
SLANT_MIN_SEG = 30
SLANT_ANGLE = 4.0
FRAME_DARK = 110  # max(R,G,B) of frame ink, tested at full resolution
FRAME_COVER = 0.2  # share of a work pixel that must be frame ink
FRAME_R = 4
BOX_EDGE_D = 3
IRREGULAR_SLANT_MIN = 200.0
IRREGULAR_FRAMELESS_MIN = 0.10
DEFAULT_IRREG_WORKERS = 8
PAGE_THUMB_W, PAGE_THUMB_H, PAGE_SHEET_COLS = 330, 480, 6
IRREGULAR_LIST_FILE = "irregular-pages.tsv"
# Every page of this title is a one-page gag with its own title logo.
ONE_PAGERS_TITLE = "All One-Pagers"

app = typer.Typer(help="Tag panels (silhouettes) and build per-title contact sheets.")


@dataclass(frozen=True)
class PagePanels:
    """One body page of a title: its image, segments file and tags file."""

    story_page: int
    fanta_page: str
    image_file: Path
    segments_file: Path
    tags_file: Path


def silhouette_score(rgb: np.ndarray) -> float:
    """Return the share of a panel covered by thick, solid black shapes.

    Args:
        rgb: The panel image, RGB uint8.

    Returns:
        A score in [0, 1]; known silhouettes run from about 0.02 to 0.5.

    """
    h, w = rgb.shape[:2]
    img = cv2.resize(rgb, (WORK_W, max(1, round(h * WORK_W / w))), interpolation=cv2.INTER_AREA)
    black = (img.max(axis=2) <= BLACK_MAX).astype(np.uint8)
    dist = cv2.distanceTransform(black, cv2.DIST_L2, 5)
    core = (dist >= CORE_R).astype(np.uint8)
    # Grow the thick cores back out to the black they sit in: the solid shapes.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * CORE_R + 3),) * 2)
    solid = cv2.dilate(core, kernel) & black
    area = solid.shape[0] * solid.shape[1]
    n, _, stats, _ = cv2.connectedComponentsWithStats(solid, connectivity=8)
    blobs = (stats[i, cv2.CC_STAT_AREA] / area for i in range(1, n))
    return float(sum(b for b in blobs if b >= MIN_BLOB_FRAC))


@dataclass(frozen=True)
class IrregularScore:
    """A page's irregular-panel measures (see ``IRREGULAR`` above for their meaning)."""

    slant_px: float
    frameless: float
    regions: int


def _slant_length(outline: np.ndarray) -> float:
    """Total length of an outline's long straight segments that lie off the page axes."""
    poly = cv2.approxPolyDP(outline, SLANT_EPSILON, closed=True).reshape(-1, 2)
    total = 0.0
    for a, b in zip(poly, np.roll(poly, -1, axis=0), strict=True):
        dx, dy = (b - a).tolist()
        length = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(abs(dy), abs(dx)))
        if length >= SLANT_MIN_SEG and min(angle, 90 - angle) > SLANT_ANGLE:
            total += length
    return total


def irregular_score(rgb: np.ndarray) -> IrregularScore:
    """Measure how far a page's panels depart from framed rectangles.

    Args:
        rgb: The whole page, RGB uint8, with page-coloured margins at its corners.

    Returns:
        The page's largest per-panel slant length and frameless share, and how many
        panel regions were found (0 means the page colour was not found).

    """
    scale = IRREG_WORK_W / rgb.shape[1]
    size = (IRREG_WORK_W, max(1, round(rgb.shape[0] * scale)))
    lab = cv2.cvtColor(cv2.resize(rgb, size, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2LAB)
    lab = lab.astype(np.int16)
    k = PAPER_CORNER
    corners = np.concatenate([lab[3:k, 3:k].reshape(-1, 3), lab[-k:-3, -k:-3].reshape(-1, 3)])
    paper = np.median(corners, axis=0)
    near_paper = (np.abs(lab - paper).max(axis=2) < PAPER_TOL).astype(np.uint8)
    _, cc = cv2.connectedComponents(near_paper, connectivity=4)
    edge_labels = np.unique(np.concatenate([cc[0], cc[-1], cc[:, 0], cc[:, -1]]))
    gutter = np.isin(cc, edge_labels[edge_labels > 0])

    # Frame ink is found at full resolution, where a 1 px frame line is still black.
    ink = (rgb.max(axis=2) <= FRAME_DARK).astype(np.float32)
    ink_small = (cv2.resize(ink, size, interpolation=cv2.INTER_AREA) > FRAME_COVER).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * FRAME_R + 1,) * 2)
    near_ink = cv2.dilate(ink_small, kernel)

    regions = (~gutter).astype(np.uint8)
    contours, _ = cv2.findContours(regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    slant, frameless, count = 0.0, 0.0, 0
    for outline in contours:
        if cv2.contourArea(outline) < MIN_PANEL_FRAC * regions.size:
            continue
        fill = np.zeros_like(regions)
        cv2.drawContours(fill, [outline], -1, 1, thickness=cv2.FILLED)
        if float(ink_small[fill > 0].mean()) < MIN_REGION_INK:
            continue
        count += 1
        pts = np.asarray(outline, dtype=np.intp).reshape(-1, 2)
        slant = max(slant, _slant_length(outline))
        x, y, w, h = cv2.boundingRect(outline)
        px, py = pts[:, 0], pts[:, 1]
        on_box = (
            (np.abs(px - x) <= BOX_EDGE_D)
            | (np.abs(px - (x + w - 1)) <= BOX_EDGE_D)
            | (np.abs(py - y) <= BOX_EDGE_D)
            | (np.abs(py - (y + h - 1)) <= BOX_EDGE_D)
        )
        unframed = (near_ink[py, px] == 0) & ~on_box
        frameless = max(frameless, float(unframed.mean()))
    return IrregularScore(slant, frameless, count)


def is_irregular_candidate(tag: dict[str, Any]) -> bool:
    """Whether a page's stored measures pass either irregular-panel cut-off."""
    return irregular_closeness(tag) >= 1.0


def irregular_closeness(tag: dict[str, Any]) -> float:
    """Each measure over its cut-off, the larger kept: 1.0 or more is a candidate."""
    return max(
        float(tag.get("slant_px") or 0.0) / IRREGULAR_SLANT_MIN,
        float(tag.get("frameless") or 0.0) / IRREGULAR_FRAMELESS_MIN,
    )


def get_panel_tags_root(comics_database: ComicsDatabase) -> Path:
    """Return the panel-tags repo root: a sibling of the panel-segments root."""
    return comics_database.get_fantagraphics_panel_segments_root_dir().parent / PANEL_TAGS_DIRNAME


def title_pages(comics_database: ComicsDatabase, title: str, tags_root: Path) -> list[PagePanels]:
    """List a title's body pages with their image, segments and tags files.

    Args:
        comics_database: The comics database.
        title: The story title.
        tags_root: The panel-tags repo root.

    Returns:
        One entry per body page, in story order. A page with no restored image takes the
        file the database's own resolver gives (``get_final_srce_story_files``): for an
        ADDED page such as Good Deeds' or Silent Night's, the original scan in
        ``Fantagraphics-fixes-and-additions``. If even that is missing, the restored path
        is kept and :func:`checked_pages` skips the title.

    """
    comic = comics_database.get_comic_book(title)
    images = comic.get_srce_restored_story_files([PageType.BODY])
    if not all(img.is_file() for img in images):
        try:
            finals = comic.get_final_srce_story_files([PageType.BODY])
        except FileNotFoundError as exc:
            logger.warning(f'"{title}": no fallback for its missing restored images: {exc}')
        else:
            images = [
                img if img.is_file() else final
                for img, (final, _) in zip(images, finals, strict=True)
            ]
    segments = comic.get_srce_panel_segments_files([PageType.BODY])
    volume_dir = tags_root / comics_database.get_fantagraphics_volume_title(
        comics_database.get_fanta_volume_int(title)
    )
    return [
        PagePanels(n, img.stem, img, seg, volume_dir / seg.name)
        for n, (img, seg) in enumerate(zip(images, segments, strict=True), start=1)
    ]


def load_segments(segments_file: Path) -> list[list[int]]:
    """Return a segments file's panel boxes as [x, y, w, h] lists."""
    return [list(map(int, box)) for box in json.loads(segments_file.read_text())["panels"]]


def load_tags(page: PagePanels) -> list[dict[str, Any]]:
    """Load a page's tag rows, creating empty rows from the segments when there is no file.

    Raises:
        RuntimeError: If the tags file's boxes no longer match the segments file.

    """
    boxes = load_segments(page.segments_file)
    if not page.tags_file.is_file():
        return [{"index": i, "box": box, "tags": {}} for i, box in enumerate(boxes, start=1)]
    rows = json.loads(page.tags_file.read_text())["panels"]
    if [r["box"] for r in rows] != boxes:
        msg = f'"{page.tags_file}" boxes no longer match "{page.segments_file}"; re-match by box.'
        raise RuntimeError(msg)
    return rows


def load_page_tags(page: PagePanels) -> dict[str, Any]:
    """Load a page's page-level tags (``{}`` when it has none or no file yet)."""
    if not page.tags_file.is_file():
        return {}
    return json.loads(page.tags_file.read_text()).get("page", {})


def save_tags(
    page: PagePanels, rows: list[dict[str, Any]], page_tags: dict[str, Any] | None = None
) -> None:
    """Write a page's tag rows: indent=2, UTF-8 kept, trailing newline.

    Args:
        page: The page.
        rows: Its panel rows.
        page_tags: Its page-level tags; None keeps whatever the file already holds, so a
            panel-only writer never drops them.

    """
    if page_tags is None:
        page_tags = load_page_tags(page)
    data = {"page": page_tags, "panels": rows} if page_tags else {"panels": rows}
    page.tags_file.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if not page.tags_file.is_file() or page.tags_file.read_text() != text:
        page.tags_file.write_text(text)


def load_rgb(image_file: Path) -> np.ndarray:
    """Read an image file as RGB uint8."""
    bgr = cv2.imread(str(image_file), cv2.IMREAD_COLOR)
    if bgr is None:
        msg = f'Cannot read image "{image_file}".'
        raise RuntimeError(msg)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def crop_panel(page_rgb: np.ndarray, segments_size: tuple[int, int], box: list[int]) -> np.ndarray:
    """Cut a panel out of a page, scaling the box if the image and segments sizes differ."""
    fx, fy = page_rgb.shape[1] / segments_size[0], page_rgb.shape[0] / segments_size[1]
    x, y, w, h = box
    return page_rgb[round(y * fy) : round((y + h) * fy), round(x * fx) : round((x + w) * fx)]


def segments_size(segments_file: Path) -> tuple[int, int]:
    """Return the page size a segments file's boxes were measured on."""
    w, h = json.loads(segments_file.read_text())["size"]
    return int(w), int(h)


def score_title(pages: list[PagePanels]) -> int:
    """Write the silhouette pixel score of every panel of a title; labels are untouched.

    Returns:
        The number of panels scored.

    """
    count = 0
    for page in pages:
        rows = load_tags(page)
        page_rgb = load_rgb(page.image_file)
        size = segments_size(page.segments_file)
        for row in rows:
            tag = row["tags"].setdefault(
                SILHOUETTE, {"label": None, "source": None, "pixel_score": None, "note": ""}
            )
            tag["pixel_score"] = round(silhouette_score(crop_panel(page_rgb, size, row["box"])), 4)
            count += 1
        save_tags(page, rows)
    return count


@dataclass(frozen=True)
class SheetItem:
    """One panel to draw on a contact sheet."""

    page: PagePanels
    row: dict[str, Any]

    @property
    def tag(self) -> dict[str, Any]:
        """The panel's tag entry for the sheet's tag (empty when untagged)."""
        return self.row["tags"].get(SILHOUETTE, {})

    @property
    def score(self) -> float:
        """How close the panel comes to being a candidate: 1.0 or more means it is one.

        Each Jev answer is divided by its cut-off and the larger ratio kept; a panel with no
        Jev answer falls back to its pixel score.
        """
        parts = self.tag.get("jev_parts")
        if parts:
            return max(
                parts.get("figure", 0.0) / CANDIDATE_FIGURE_MIN,
                parts.get("scenery", 0.0) / CANDIDATE_SCENERY_MIN,
            )
        jev = self.tag.get("jev_score")
        if jev is not None:
            return float(jev) / CANDIDATE_LEGACY_MIN
        return float(self.tag.get("pixel_score") or 0.0)


def sheet_sections(
    pages: list[PagePanels], tag: str, near_misses: int
) -> list[tuple[str, list[SheetItem]]]:
    """Split a title's panels into the sheet's Yes / Unsure / Candidates / Near-miss sections.

    Candidates are unlabelled panels that pass the Jev cut-offs (see
    ``CANDIDATE_FIGURE_MIN``), in page order: after a Jev run over unreviewed titles,
    they are the panels to check. Near misses are the panels closest to the cut-offs
    among the rest, so a real silhouette that was rejected or fell just under them shows
    up for a second look.
    """
    items = [SheetItem(p, r) for p in pages for r in load_tags(p)]
    yes = [i for i in items if i.tag.get("label") == "yes"]
    unsure = [i for i in items if i.tag.get("label") == "unsure"]
    candidates = [i for i in items if i.tag.get("label") is None and i.score >= 1.0]
    shown = {id(i) for i in (*yes, *unsure, *candidates)}
    rest = sorted((i for i in items if id(i) not in shown), key=lambda i: -i.score)
    rest = rest[:near_misses]
    return [
        (f"{tag.upper()}: YES ({len(yes)})", yes),
        (f"UNSURE ({len(unsure)})", unsure),
        (
            (
                f"CANDIDATES: unlabelled, figure >= {CANDIDATE_FIGURE_MIN} or scenery >= "
                f"{CANDIDATE_SCENERY_MIN} ({len(candidates)})"
            ),
            candidates,
        ),
        (f"NEAR MISSES: top {len(rest)} other scores", rest),
    ]


def _caption(item: SheetItem) -> str:
    """`page:panel (story page-panel) who scores`: who is the source of a yes, else the label.

    Scores are ``f``/``s`` (v3 figure/scenery), ``j`` (a v1/v2 single score) or ``p``
    (pixel score only).
    """
    label = item.tag.get("label")
    what = (item.tag.get("source") or "-") if label == "yes" else (label or "?")
    parts = item.tag.get("jev_parts")
    if parts:
        scores = f"f{parts.get('figure', 0):.2f} s{parts.get('scenery', 0):.2f}"
    elif item.tag.get("jev_score") is not None:
        scores = f"j{float(item.tag['jev_score']):.2f}"
    else:
        scores = f"p{float(item.tag.get('pixel_score') or 0):.2f}"
    index = item.row["index"]
    return f"{item.page.fanta_page}:{index} ({item.page.story_page}-{index}) {what} {scores}"


def build_sheet(title: str, sections: list[tuple[str, list[SheetItem]]], out_file: Path) -> None:
    """Draw a contact sheet: a header per section, then its panels in page order.

    Args:
        title: The story title, drawn at the top.
        sections: (heading, items) pairs; empty sections still get their heading.
        out_file: The PNG to write.

    """
    cache: dict[Path, np.ndarray] = {}

    def crop_of(item: SheetItem) -> Callable[[], np.ndarray]:
        def crop() -> np.ndarray:
            page = item.page
            if page.image_file not in cache:
                cache[page.image_file] = load_rgb(page.image_file)
            size = segments_size(page.segments_file)
            return crop_panel(cache[page.image_file], size, item.row["box"])

        return crop

    grid_sections = [
        (heading, [(crop_of(item), _caption(item)) for item in items])
        for heading, items in sections
    ]
    write_grid_sheet(title, grid_sections, (THUMB_W, THUMB_H, SHEET_COLS), out_file)


GridSection = tuple[str, list[tuple[Callable[[], np.ndarray], str]]]


def write_grid_sheet(
    title: str, sections: list[GridSection], layout: tuple[int, int, int], out_file: Path
) -> None:
    """Draw a contact sheet of thumbnails under section headings and write it as a PNG.

    Args:
        title: Drawn at the top.
        sections: (heading, [(image loader, caption)]) pairs; images are loaded one at a
            time, so a sheet of whole pages never holds them all at once.
        layout: (thumbnail width, thumbnail height, columns).
        out_file: The PNG to write.

    """
    thumb_w, thumb_h, cols = layout
    width = thumb_w * cols
    blocks: list[np.ndarray] = [_text_band(title, width, HEADER_H + 6, scale=0.9)]
    for heading, items in sections:
        blocks.append(_text_band(heading, width, HEADER_H, scale=0.7))
        n_rows = (len(items) + cols - 1) // cols
        if not n_rows:
            continue
        grid = np.full((thumb_h * n_rows, width, 3), 255, np.uint8)
        for k, (load, caption) in enumerate(items):
            img = load()
            s = min((thumb_w - 6) / img.shape[1], (thumb_h - CAPTION_H - 4) / img.shape[0])
            thumb = cv2.resize(
                img, (int(img.shape[1] * s), int(img.shape[0] * s)), interpolation=cv2.INTER_AREA
            )
            ox, oy = (k % cols) * thumb_w, (k // cols) * thumb_h
            th, tw = thumb.shape[:2]
            grid[oy + CAPTION_H : oy + CAPTION_H + th, ox + 3 : ox + 3 + tw] = thumb
            cv2.putText(
                grid,
                caption,
                (ox + 4, oy + 16),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (200, 0, 0),
                1,
                cv2.LINE_AA,
            )
        blocks.append(grid)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_file), cv2.cvtColor(np.vstack(blocks), cv2.COLOR_RGB2BGR))


def _text_band(text: str, width: int, height: int, scale: float) -> np.ndarray:
    band = np.full((height, width, 3), 235, np.uint8)
    cv2.putText(
        band, text, (8, height - 10), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 2, cv2.LINE_AA
    )
    return band


def sheet_file(tags_root: Path, tag: str, title: str) -> Path:
    """Return where a title's contact sheet for a tag is written."""
    return tags_root / SHEETS_SUBDIR / tag / f"{title}.png"


def write_sheet(
    comics_database: ComicsDatabase, title: str, tags_root: Path, near_misses: int
) -> Path:
    """Build and write one title's silhouette contact sheet, returning its path."""
    pages = title_pages(comics_database, title, tags_root)
    out = sheet_file(tags_root, SILHOUETTE, title)
    build_sheet(title, sheet_sections(pages, SILHOUETTE, near_misses), out)
    return out


def jev_title(pages: list[PagePanels], client: JevClient, workers: int, *, force: bool) -> int:
    """Ask Jev about every panel of a title not yet scored with the current wording.

    Args:
        pages: The title's pages.
        client: The Jev client.
        workers: Concurrent requests.
        force: Re-ask panels already scored with the current wording.

    Returns:
        The input tokens billed.

    """
    loaded = [(page, load_tags(page)) for page in pages]
    todo: list[tuple[PagePanels, dict[str, Any]]] = []
    for page, rows in loaded:
        for row in rows:
            tag = row["tags"].setdefault(
                SILHOUETTE, {"label": None, "source": None, "pixel_score": None, "note": ""}
            )
            if force or tag.get("jev_question") != JEV_QUESTION_VERSION:
                todo.append((page, row))
    cache: dict[Path, np.ndarray] = {}
    for page, _ in todo:
        if page.image_file not in cache:
            cache[page.image_file] = load_rgb(page.image_file)

    def ask(item: tuple[PagePanels, dict[str, Any]]) -> NoulAnswers:
        page, row = item
        crop = crop_panel(cache[page.image_file], segments_size(page.segments_file), row["box"])
        return client.ask_image_questions(crop, JEV_QUESTIONS)

    tokens = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for (_, row), answer in zip(todo, pool.map(ask, todo), strict=True):
            tag = row["tags"][SILHOUETTE]
            parts = {qid: round(p, 4) for qid, p in answer.probabilities.items()}
            tag["jev_score"] = max(parts.values())
            tag["jev_parts"] = parts
            tag["jev_model"] = answer.model
            tag["jev_question"] = JEV_QUESTION_VERSION
            tokens += answer.input_tokens
    for page, rows in loaded:
        save_tags(page, rows)
    logger.info(f"Jev scored {len(todo)} panels for {tokens} input tokens.")
    return tokens


def checked_pages(
    comics_database: ComicsDatabase, title: str, tags_root: Path
) -> list[PagePanels] | None:
    """Return a title's pages, or None (with a message) if any page image is missing.

    Checked before any work so that a title with an image that neither the restored
    directory nor the database's resolver can supply is skipped whole, not half-done and
    not billed, and the rest of a volume still runs.
    """
    pages = title_pages(comics_database, title, tags_root)
    missing = [p.image_file.name for p in pages if not p.image_file.is_file()]
    if missing:
        first = pages[0].image_file.parent / missing[0]
        msg = f'SKIPPED "{title}": {len(missing)} page image(s) missing, e.g. "{first}".'
        logger.warning(msg)
        print(msg)
        return None
    return pages


def parse_panel_ids(text: str) -> list[tuple[str, int]]:
    """Parse ``014:5,15:2`` into ``[("014", 5), ("015", 2)]`` (fanta page, panel index).

    Raises:
        typer.BadParameter: On an id that is not ``page:panel``.

    """
    ids = []
    for raw in filter(None, (t.strip() for t in text.split(","))):
        page, sep, panel = raw.partition(":")
        if not (sep and page.isdigit() and panel.isdigit()):
            msg = f'"{raw}" is not a page:panel id such as 014:5.'
            raise typer.BadParameter(msg)
        ids.append((page.zfill(3), int(panel)))
    return ids


def apply_labels(
    pages: list[PagePanels],
    wanted: dict[tuple[str, int], str],
    *,
    accept_candidates: bool,
) -> dict[str, int]:
    """Write a reviewer's labels (source ``human``) into a title's tag files.

    Args:
        pages: The title's pages.
        wanted: (fanta page, panel index) to ``yes``, ``no`` or ``unsure``; these override
            any existing label.
        accept_candidates: Also label ``yes`` every unlabelled candidate not in ``wanted``.
            Other unlabelled panels stay unlabelled: nobody looked at them one by one.

    Returns:
        How many panels were set to each label.

    Raises:
        typer.BadParameter: If an id is not a panel of this title; nothing is written then.

    """
    loaded = [(page, load_tags(page)) for page in pages]
    known = {(page.fanta_page, row["index"]) for page, rows in loaded for row in rows}
    if unknown := sorted(set(wanted) - known):
        ids = ", ".join(f"{p}:{i}" for p, i in unknown)
        msg = f"Not panels of this title: {ids}."
        raise typer.BadParameter(msg)
    counts = {"yes": 0, "no": 0, "unsure": 0}
    for page, rows in loaded:
        for row in rows:
            item = SheetItem(page, row)
            label = wanted.get((page.fanta_page, row["index"]))
            if label is None and accept_candidates and item.tag.get("label") is None:
                label = "yes" if item.score >= 1.0 else None
            if label is None:
                continue
            tag = row["tags"].setdefault(
                SILHOUETTE, {"label": None, "source": None, "pixel_score": None, "note": ""}
            )
            tag["label"], tag["source"] = label, "human"
            counts[label] += 1
        save_tags(page, rows)
    return counts


def irregular_title(pages: list[PagePanels], workers: int) -> list[PagePanels]:
    """Measure and store every page's irregular-panel scores; labels are untouched.

    The measure is local and free, so every page is re-measured on each run.

    Returns:
        The pages that pass the cut-offs and are not labelled ``no``.

    """

    def measure(page: PagePanels) -> IrregularScore:
        return irregular_score(load_rgb(page.image_file))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        scores = list(pool.map(measure, pages))
    flagged = []
    for page, sc in zip(pages, scores, strict=True):
        if not sc.regions:
            logger.warning(f'"{page.image_file}": no panel regions found (page colour?).')
        page_tags = load_page_tags(page)
        tag = page_tags.setdefault(IRREGULAR, {"label": None, "source": None, "note": ""})
        tag["slant_px"] = round(sc.slant_px, 1)
        tag["frameless"] = round(sc.frameless, 4)
        tag["regions"] = sc.regions
        tag["measure"] = IRREGULAR_MEASURE
        save_tags(page, load_tags(page), page_tags)
        if is_irregular_page(tag):
            flagged.append(page)
    return flagged


def is_irregular_page(tag: dict[str, Any]) -> bool:
    """Return whether a page is irregular: labelled ``yes``, or unlabelled and a candidate."""
    label = tag.get("label")
    return label == "yes" or (label is None and is_irregular_candidate(tag))


@dataclass(frozen=True)
class TaggedPage:
    """A page with its title and stored irregular-panel tag."""

    title: str
    page: PagePanels
    tag: dict[str, Any]

    @property
    def title_page(self) -> bool:
        """Whether the page carries a story's title logo, which is printed unframed.

        On most such pages the logo is all the measure sees, so they are listed apart.
        """
        return self.page.story_page == 1 or self.title == ONE_PAGERS_TITLE

    def caption(self) -> str:
        """`fanta page title story-page slant frameless label`, short enough for a thumb."""
        t = self.tag
        return (
            f"{self.page.fanta_page} {self.title[:14]} p{self.page.story_page} "
            f"s{float(t.get('slant_px') or 0):.0f} f{float(t.get('frameless') or 0):.2f}"
            f"{' ' + t['label'] if t.get('label') else ''}"
        )


def volume_tagged_pages(
    comics_database: ComicsDatabase, volume: int, tags_root: Path
) -> list[TaggedPage]:
    """Every page of a volume's titles that holds an irregular-panel tag, in page order."""
    _, titles = get_comic_titles(str(volume), "", exclude_non_comics=True)
    found = [
        TaggedPage(title, page, tag)
        for title in titles
        for page in title_pages(comics_database, title, tags_root)
        if (tag := load_page_tags(page).get(IRREGULAR)) is not None
    ]
    return sorted(found, key=lambda tp: tp.page.fanta_page)


def write_irregular_sheet(
    comics_database: ComicsDatabase, volume: int, tags_root: Path, near_misses: int
) -> Path:
    """Write a volume's sheet of irregular pages plus its closest near misses."""
    tagged = volume_tagged_pages(comics_database, volume, tags_root)
    flagged = [tp for tp in tagged if is_irregular_page(tp.tag) and not tp.title_page]
    title_flagged = [tp for tp in tagged if is_irregular_page(tp.tag) and tp.title_page]
    rest = sorted(
        (tp for tp in tagged if not is_irregular_page(tp.tag)),
        key=lambda tp: -irregular_closeness(tp.tag),
    )[:near_misses]

    def loader(tp: TaggedPage) -> Callable[[], np.ndarray]:
        return lambda: load_rgb(tp.page.image_file)

    sections: list[GridSection] = [
        (
            (
                f"IRREGULAR PANELS: slant >= {IRREGULAR_SLANT_MIN:.0f} or frameless >= "
                f"{IRREGULAR_FRAMELESS_MIN} or labelled yes ({len(flagged)})"
            ),
            [(loader(tp), tp.caption()) for tp in flagged],
        ),
        (
            f"TITLE PAGES: flagged, but often only for the unframed logo ({len(title_flagged)})",
            [(loader(tp), tp.caption()) for tp in title_flagged],
        ),
        (f"NEAR MISSES: top {len(rest)} other pages", [(loader(tp), tp.caption()) for tp in rest]),
    ]
    volume_title = comics_database.get_fantagraphics_volume_title(volume)
    out = tags_root / SHEETS_SUBDIR / IRREGULAR / f"{volume_title}.png"
    write_grid_sheet(volume_title, sections, (PAGE_THUMB_W, PAGE_THUMB_H, PAGE_SHEET_COLS), out)
    return out


def write_irregular_list(comics_database: ComicsDatabase, tags_root: Path) -> tuple[Path, int]:
    """Write every irregular page in the corpus, from the stored tags, as a TSV.

    Returns:
        The file and the number of pages listed.

    """
    columns = ["volume", "fanta_page", "title", "story_page", "title_page", "slant_px"]
    columns += ["frameless", "label"]
    lines = ["\t".join(columns)]
    for volume in range(FIRST_VOLUME_NUMBER, LAST_VOLUME_NUMBER + 1):
        for tp in volume_tagged_pages(comics_database, volume, tags_root):
            if is_irregular_page(tp.tag):
                t = tp.tag
                fields: list[object] = [volume, tp.page.fanta_page, tp.title, tp.page.story_page]
                fields += ["yes" if tp.title_page else "", t.get("slant_px")]
                fields += [t.get("frameless"), t.get("label") or ""]
                lines.append("\t".join(map(str, fields)))
    out = tags_root / IRREGULAR_LIST_FILE
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out, len(lines) - 1


def parse_page_ids(text: str) -> list[str]:
    """Parse ``068-076,151`` into fanta page stems ``["068", ..., "076", "151"]``.

    Raises:
        typer.BadParameter: On an item that is not a page number or a low-high range.

    """
    pages = []
    for raw in filter(None, (t.strip() for t in text.split(","))):
        low, sep, high = raw.partition("-")
        if not (low.isdigit() and (not sep or high.isdigit())) or (sep and int(high) < int(low)):
            msg = f'"{raw}" is not a page number or range such as 068 or 068-076.'
            raise typer.BadParameter(msg)
        pages.extend(f"{n:03d}" for n in range(int(low), int(high if sep else low) + 1))
    return pages


def apply_page_labels(
    tagged: list[TaggedPage], wanted: dict[str, str], *, accept_candidates: bool
) -> dict[str, int]:
    """Write a reviewer's irregular-panel page labels (source ``human``).

    Args:
        tagged: The volume's (or title's) measured pages.
        wanted: Fanta page to ``yes`` or ``no``; these override any existing label.
        accept_candidates: Also label ``yes`` every unlabelled candidate not in ``wanted``,
            except title pages, which are usually flagged only for their logo: a title
            page becomes ``yes`` only when listed.

    Returns:
        How many pages were set to each label.

    Raises:
        typer.BadParameter: If a page is not a measured page in scope; nothing is written.

    """
    known = {tp.page.fanta_page: tp for tp in tagged}
    if unknown := sorted(set(wanted) - set(known)):
        msg = f"Not measured pages of this volume/title: {', '.join(unknown)}."
        raise typer.BadParameter(msg)
    counts = {"yes": 0, "no": 0}
    for tp in tagged:
        label = wanted.get(tp.page.fanta_page)
        if (
            label is None
            and accept_candidates
            and not tp.title_page
            and tp.tag.get("label") is None
            and is_irregular_candidate(tp.tag)
        ):
            label = "yes"
        if label is None:
            continue
        page_tags = load_page_tags(tp.page)
        page_tags[IRREGULAR]["label"], page_tags[IRREGULAR]["source"] = label, "human"
        save_tags(tp.page, load_tags(tp.page), page_tags)
        counts[label] += 1
    return counts


NearMissesOpt = typer.Option(DEFAULT_NEAR_MISSES, "--near-misses", help="Near misses per sheet.")


@app.command(help="Write silhouette pixel scores for every body panel, then build the sheet.")
def score(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    near_misses: int = NearMissesOpt,
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Score each title's panels and rebuild its contact sheet."""
    init_logging(APP_LOGGING_NAME, "panel-tags.log", log_level_str)
    comics_database, titles = get_comic_titles(volumes_str, title_str, exclude_non_comics=True)
    tags_root = get_panel_tags_root(comics_database)
    for title in titles:
        if (pages := checked_pages(comics_database, title, tags_root)) is None:
            continue
        n = score_title(pages)
        out = write_sheet(comics_database, title, tags_root, near_misses)
        logger.info(f'"{title}": scored {n} panels; sheet "{out}".')
        print(f"{title}: {n} panels scored -> {out}")


@app.command(help="Ask Jev (TypeSafe API, billed) a silhouette question about every panel.")
def jev(  # noqa: PLR0913 -- a typer command: one parameter per CLI option.
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    workers: int = typer.Option(DEFAULT_JEV_WORKERS, "--workers", help="Concurrent requests."),
    force: bool = typer.Option(default=False, help="Re-ask panels already scored."),
    near_misses: int = NearMissesOpt,
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Score each title's panels with Jev and rebuild its contact sheet."""
    init_logging(APP_LOGGING_NAME, "panel-tags.log", log_level_str)
    comics_database, titles = get_comic_titles(volumes_str, title_str, exclude_non_comics=True)
    tags_root = get_panel_tags_root(comics_database)
    client = JevClient()
    total = 0
    for title in titles:
        if (pages := checked_pages(comics_database, title, tags_root)) is None:
            continue
        tokens = jev_title(pages, client, workers, force=force)
        total += tokens
        out = write_sheet(comics_database, title, tags_root, near_misses)
        print(f"{title}: {tokens} input tokens -> {out}")
    print(f"Total: {total} input tokens.")


@app.command(help="Record a contact-sheet review: list the exceptions, accept the rest.")
def label(  # noqa: PLR0913 -- a typer command: one parameter per CLI option.
    title_str: TitleArg,
    reject: str = typer.Option("", "--reject", help="page:panel ids to label no, e.g. 014:5,014:6"),
    add: str = typer.Option("", "--add", help="page:panel ids to label yes (any panel)."),
    unsure: str = typer.Option("", "--unsure", help="page:panel ids to label unsure."),
    accept_candidates: bool = typer.Option(
        default=False, help="Label yes every unlabelled candidate not listed above."
    ),
    near_misses: int = NearMissesOpt,
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Label one title's panels from a contact-sheet review, then rebuild its sheet."""
    init_logging(APP_LOGGING_NAME, "panel-tags.log", log_level_str)
    wanted: dict[tuple[str, int], str] = {}
    for text, lab in ((reject, "no"), (add, "yes"), (unsure, "unsure")):
        for pid in parse_panel_ids(text):
            if wanted.get(pid, lab) != lab:
                msg = f"{pid[0]}:{pid[1]} is given two labels ({wanted[pid]} and {lab})."
                raise typer.BadParameter(msg)
            wanted[pid] = lab
    if not wanted and not accept_candidates:
        msg = "Nothing to do: give --reject/--add/--unsure ids and/or --accept-candidates."
        raise typer.BadParameter(msg)
    comics_database = ComicsDatabase()
    tags_root = get_panel_tags_root(comics_database)
    if (pages := checked_pages(comics_database, title_str, tags_root)) is None:
        raise typer.Exit(code=1)
    counts = apply_labels(pages, wanted, accept_candidates=accept_candidates)
    out = write_sheet(comics_database, title_str, tags_root, near_misses)
    logger.info(f'"{title_str}": labelled {counts} (source human).')
    print(
        f"{title_str}: yes {counts['yes']}, no {counts['no']}, unsure {counts['unsure']} -> {out}"
    )


@app.command(help="Find pages with irregular (slanted, round or borderless) panels.")
def irregular(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    workers: int = typer.Option(DEFAULT_IRREG_WORKERS, "--workers", help="Pages measured at once."),
    near_misses: int = NearMissesOpt,
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Measure each title's pages, rebuild its volume's sheet, rewrite the corpus list."""
    init_logging(APP_LOGGING_NAME, "panel-tags.log", log_level_str)
    comics_database, titles = get_comic_titles(volumes_str, title_str, exclude_non_comics=True)
    tags_root = get_panel_tags_root(comics_database)
    volumes: set[int] = set()
    for title in titles:
        if (pages := checked_pages(comics_database, title, tags_root)) is None:
            continue
        flagged = irregular_title(pages, workers)
        volumes.add(comics_database.get_fanta_volume_int(title))
        print(f"{title}: {len(pages)} pages; irregular: {' '.join(p.fanta_page for p in flagged)}")
    for volume in sorted(volumes):
        print(f"Sheet: {write_irregular_sheet(comics_database, volume, tags_root, near_misses)}")
    out, n = write_irregular_list(comics_database, tags_root)
    print(f"{n} irregular pages in the corpus -> {out}")


@app.command(help="Record an irregular-panel sheet review: list the exceptions, accept the rest.")
def irregular_label(  # noqa: PLR0913 -- a typer command: one parameter per CLI option.
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    reject: str = typer.Option("", "--reject", help="Fanta pages to label no, e.g. 068-076,080"),
    add: str = typer.Option("", "--add", help="Fanta pages to label yes (any measured page)."),
    accept_candidates: bool = typer.Option(
        default=False, help="Label yes every unlabelled flagged page not listed (not title pages)."
    ),
    near_misses: int = NearMissesOpt,
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Label one volume's (or title's) pages from its sheet, then rebuild sheet and list."""
    init_logging(APP_LOGGING_NAME, "panel-tags.log", log_level_str)
    wanted: dict[str, str] = {}
    for text, lab in ((reject, "no"), (add, "yes")):
        for page_id in parse_page_ids(text):
            if wanted.get(page_id, lab) != lab:
                msg = f"Page {page_id} is given two labels ({wanted[page_id]} and {lab})."
                raise typer.BadParameter(msg)
            wanted[page_id] = lab
    if not wanted and not accept_candidates:
        msg = "Nothing to do: give --reject/--add pages and/or --accept-candidates."
        raise typer.BadParameter(msg)
    comics_database, titles = get_comic_titles(volumes_str, title_str, exclude_non_comics=True)
    volumes = {comics_database.get_fanta_volume_int(title) for title in titles}
    if len(volumes) != 1:
        msg = "Give one --volume (or one --title): fanta page numbers are per volume."
        raise typer.BadParameter(msg)
    volume = volumes.pop()
    tags_root = get_panel_tags_root(comics_database)
    tagged = [
        tp for tp in volume_tagged_pages(comics_database, volume, tags_root) if tp.title in titles
    ]
    counts = apply_page_labels(tagged, wanted, accept_candidates=accept_candidates)
    sheet = write_irregular_sheet(comics_database, volume, tags_root, near_misses)
    out, n = write_irregular_list(comics_database, tags_root)
    logger.info(f"Volume {volume}: irregular pages labelled {counts} (source human).")
    print(f"Volume {volume}: yes {counts['yes']}, no {counts['no']} -> {sheet}")
    print(f"{n} irregular pages in the corpus -> {out}")


@app.command(help="Build the silhouette contact sheet from the tags as they stand.")
def sheet(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    near_misses: int = NearMissesOpt,
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Rebuild each title's contact sheet without scoring again."""
    init_logging(APP_LOGGING_NAME, "panel-tags.log", log_level_str)
    comics_database, titles = get_comic_titles(volumes_str, title_str, exclude_non_comics=True)
    tags_root = get_panel_tags_root(comics_database)
    for title in titles:
        if checked_pages(comics_database, title, tags_root) is None:
            continue
        print(f"{title}: {write_sheet(comics_database, title, tags_root, near_misses)}")


if __name__ == "__main__":
    app()

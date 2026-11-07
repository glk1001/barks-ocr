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
"""

# ruff: noqa: T201

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import typer
from barks_fantagraphics.comics_consts import PageType
from barks_fantagraphics.comics_database import ComicsDatabase
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from loguru import logger

from barks_ocr.cli_setup import get_comic_titles, init_logging

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
        One entry per body page, in story order.

    """
    comic = comics_database.get_comic_book(title)
    images = comic.get_srce_restored_story_files([PageType.BODY])
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


def save_tags(page: PagePanels, rows: list[dict[str, Any]]) -> None:
    """Write a page's tag rows: indent=2, UTF-8 kept, trailing newline."""
    page.tags_file.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({"panels": rows}, indent=2, ensure_ascii=False) + "\n"
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
        """The pixel score, 0 when not yet scored."""
        return float(self.tag.get("pixel_score") or 0.0)


def sheet_sections(
    pages: list[PagePanels], tag: str, near_misses: int
) -> list[tuple[str, list[SheetItem]]]:
    """Split a title's panels into the sheet's Yes / Unsure / Near-miss sections.

    Near misses are the highest pixel scores among panels not labelled yes or unsure, so a
    real silhouette that was rejected (or never labelled) shows up for a second look.
    """
    items = [SheetItem(p, r) for p in pages for r in load_tags(p)]
    labelled = [i for i in items if tag in i.row["tags"]]
    yes = [i for i in labelled if i.row["tags"][tag]["label"] == "yes"]
    unsure = [i for i in labelled if i.row["tags"][tag]["label"] == "unsure"]
    rest = sorted((i for i in items if i not in yes and i not in unsure), key=lambda i: -i.score)[
        :near_misses
    ]
    return [
        (f"{tag.upper()}: YES ({len(yes)})", yes),
        (f"UNSURE ({len(unsure)})", unsure),
        (f"NEAR MISSES: top {len(rest)} pixel scores not labelled yes/unsure", rest),
    ]


def _caption(item: SheetItem) -> str:
    label = item.tag.get("label") or "unlabelled"
    source = item.tag.get("source") or "-"
    index = item.row["index"]
    what = source if label == "yes" else label
    return f"{item.page.fanta_page}:{index} ({item.page.story_page}-{index}) {what}"


def build_sheet(title: str, sections: list[tuple[str, list[SheetItem]]], out_file: Path) -> None:
    """Draw a contact sheet: a header per section, then its panels in page order.

    Args:
        title: The story title, drawn at the top.
        sections: (heading, items) pairs; empty sections still get their heading.
        out_file: The PNG to write.

    """
    width = THUMB_W * SHEET_COLS
    blocks: list[np.ndarray] = [_text_band(title, width, HEADER_H + 6, scale=0.9)]
    cache: dict[Path, np.ndarray] = {}
    for heading, items in sections:
        blocks.append(_text_band(heading, width, HEADER_H, scale=0.7))
        n_rows = (len(items) + SHEET_COLS - 1) // SHEET_COLS
        if not n_rows:
            continue
        grid = np.full((THUMB_H * n_rows, width, 3), 255, np.uint8)
        for k, item in enumerate(items):
            page = item.page
            if page.image_file not in cache:
                cache[page.image_file] = load_rgb(page.image_file)
            size = segments_size(page.segments_file)
            crop = crop_panel(cache[page.image_file], size, item.row["box"])
            s = min((THUMB_W - 6) / crop.shape[1], (THUMB_H - CAPTION_H - 4) / crop.shape[0])
            thumb = cv2.resize(
                crop, (int(crop.shape[1] * s), int(crop.shape[0] * s)), interpolation=cv2.INTER_AREA
            )
            ox, oy = (k % SHEET_COLS) * THUMB_W, (k // SHEET_COLS) * THUMB_H
            th, tw = thumb.shape[:2]
            grid[oy + CAPTION_H : oy + CAPTION_H + th, ox + 3 : ox + 3 + tw] = thumb
            cv2.putText(
                grid,
                _caption(item),
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
        n = score_title(title_pages(comics_database, title, tags_root))
        out = write_sheet(comics_database, title, tags_root, near_misses)
        logger.info(f'"{title}": scored {n} panels; sheet "{out}".')
        print(f"{title}: {n} panels scored -> {out}")


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
        print(f"{title}: {write_sheet(comics_database, title, tags_root, near_misses)}")


if __name__ == "__main__":
    app()

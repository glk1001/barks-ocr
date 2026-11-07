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
"""

# ruff: noqa: T201

import json
from concurrent.futures import ThreadPoolExecutor
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

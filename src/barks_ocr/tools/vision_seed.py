# ruff: noqa: T201
"""Seed a vision pass on pages that were never grouped: raw OCR boxes in, prelim JSON out.

The ordinary pipeline is OCR (``barks-ocr-batch``) -> Gemini grouping
(``barks-ocr-gemini-*``) -> a vision pass that judges the groups Gemini made.  A
page that was never OCRed has no prelim file, so ``vision-prep`` has nothing to
prep.  This tool lets the vision pass do the grouping itself, in the same reading:

1. ``barks-ocr-batch --engine easyocr --title T`` writes the raw EasyOCR boxes.
2. ``barks-ocr-vision-seed prep --title T`` crops the pages as ``vision-prep``
   does and lists each page's raw boxes -- id, panel, bounds, text -- in
   ``boxes.txt`` (and ``boxes.json``), in place of the groups ``vision-prep``
   would dump.  It writes the same ``queue.json``, ``roster.txt`` and capture
   stubs, so ``vision-apply`` reads the directory unchanged.
3. The pass reads each page and writes two files: ``seed.json``, the page's
   groups in reading order as lists of raw box ids (``"6-13"`` ranges allowed)
   plus the lettering, type and (where needed) panel; and ``result.json``, the
   ordinary vision result, whose group ids are the positions in ``seed.json`` --
   ``"0"`` for the first group.
4. ``barks-ocr-vision-seed build --out-dir D`` writes the easyocr prelim file in
   the Gemini grouper's schema, and the paddleocr prelim as a copy of it.
5. ``barks-ocr-vision-apply --out-dir D --no-mirror`` validates and applies the
   results as for any pass, and ``barks-ocr-vision-seed sync`` then re-copies
   the finished easyocr file onto paddleocr.

**The paddleocr side is a copy, and says so.**  Nothing reads the raw OCR file
beside a prelim once it is built, so a copied file works everywhere; but every
cross-engine check (``ocr_check``, ``engine_compare``, ``vision-mirror``) is
then comparing a file with itself and passes by construction.  The copy carries
a top-level ``copied_from_engine`` key so that can be told apart from agreement.
``sync`` refuses to overwrite a paddleocr file that lacks the key: that one came
from a real PaddleOCR run and is not this tool's to replace.

**Lettering EasyOCR missed** is a seed group with an explicit ``text_box`` and no
box ids, as a pass's ``added_groups`` are.

**Reseeding a Gemini-grouped title.** ``prep --reseed`` also takes pages that
already have Gemini prelim files, so a title nobody has hand-checked yet can be
grouped and read in one pass instead of cleaned by hand: on Vol. 25 the seed
matched the reviewer's cleaned text on 196 of 212 groups against Gemini's 117
(2026-09-29). It refuses the title if any page carries review or vision work --
a ``speaker*``, ``vision_*`` or ``type_reviewed`` key -- since reseeding would
throw that away. ``build`` then backs up both Gemini files into the prelim
backup tree before replacing them, and the real paddleocr file becomes a marked
copy like any other seed page's.

**Refitting boxes after a fitter fix.** ``build`` will not touch an applied page,
so a better box fit does not reach titles already read. ``refit --out-dir D``
recomputes the word-built caption boxes of that directory's applied pages and writes
only the ones that grow, on both engines; a page anyone has reviewed (``speaker_reviewed``
or ``type_reviewed`` on any group) and a hand-set ``text_box`` are left alone.
"""

import json
import re
import shutil
import statistics
from pathlib import Path
from typing import Annotated, Any

import cv2
import numpy as np
import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page
from barks_fantagraphics.comics_utils import get_backup_file
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.panel_boxes import PagePanelBoxes, TitlePanelBoxes
from barks_fantagraphics.speech_groupers import OcrTypes
from barks_fantagraphics.speech_markup import strip_markup
from loguru import logger
from PIL import Image

from barks_ocr.pipeline.gemini_grouper import get_enclosing_box, get_enclosing_panel_num
from barks_ocr.tools.vision_prep import (
    CAPTURE_STUB_FILE,
    CROP_PAD_PX,
    DEFAULT_ROOT,
    GROUP_FIELDS,
    MAX_IMAGE_BYTES,
    ROSTER_FILE,
    _capture_stub,
    _cast_for,
    _crop_panel,
    _page_image_file,
    _slug,
    _write_overview,
    _write_panel,
)
from barks_ocr.utils.vision_schema import GROUP_TYPES, roster_text
from barks_ocr.utils.volume_holds import HOLDS_FILE, held_volumes

app = typer.Typer(help="Seed a vision pass on pages with raw OCR but no prelim groups.")

SEED_ENGINE = OcrTypes.EASYOCR
COPY_ENGINE = OcrTypes.PADDLEOCR
COPIED_FROM_ENGINE_KEY = "copied_from_engine"

# The seed pass writes every group's text itself, where Gemini used to, so the house
# style is checked here: the corpus spaces an em dash on both sides, 4,908 `WORD —`
# and 2,829 `— WORD` against none touching a letter once Camp Counselor's three
# were fixed in review (2026-09-28).
DASH_TOUCHING_LETTER = re.compile(r"[A-Za-z0-9]\u2014|\u2014[A-Za-z0-9]")

# FITTING A CLIPPED TRAILING MARK. EasyOCR's word box usually stops short of a
# closing `!` -- Barks letters it as a thin tapering stroke plus a separate dot, and
# neither reads as part of the word -- so a group box built from word boxes clipped
# it, and on Camp Counselor 31 of the reviewer's 35 box refits were that right edge
# moving out 10-33px. `_fit_trailing_mark` finds the stroke and dot in the page's ink
# and extends the box over them. Scored against that review's 106 balloon boxes:
# every edge within 6px of the reviewer's went from 76 to 89, the mean edge error
# from 2.5 to 1.0px; the two it moved away from the review were a `!` the review had
# itself left clipped (112 g4) and a 10px overshoot (117 g0). The numbers below are
# the ones that scored that.
INK_DARK = 380  # an RGB sum below this is lettering ink
MIN_INK_AREA = 6  # smaller than this is a speck, not a stroke or a dot
BALLOON_TYPES = frozenset({"dialogue", "thought", "narration"})
ART_WORD = 1.5  # a word this many times the page's median height is art lettering
MARK_REACH = 0.6  # the first stroke may start this many word heights past the word
MARK_STEP = 0.3  # a further piece (the dot, a second `!`) this close to the last
MARK_MAX_GROWTH = 0.8  # never extend the word by more than this many word heights
MARK_MAX_WIDTH = 0.45  # a mark is narrow ...
MARK_MAX_HEIGHT = 0.85  # ... and shorter than the word box; a border line is not
MARK_BAND = 0.15  # and stays inside the word's own line, give or take this much
MARK_STEPS = 3
MARK_PAD = 6  # the reviewer's boxes sit about this far past the ink

# TWO MORE EDGES WORD BOXES CLIP, found in Donald's Grandma Duck's review once the
# trailing mark was fixed: an em dash at the start or end of a line (a flat stroke
# EasyOCR does not read as part of the word) and a caption's drop capital (a letter
# one to two lines tall set left of the first word). Scored against both reviewed
# seed titles' 302 word-built boxes: 6 moved closer to the reviewer's, none further.
DASH = "\u2014"
DASH_MAX_HEIGHT = 0.25  # a dash is flat ...
DASH_WIDTH = (0.3, 1.4)  # ... about a letter wide ...
DASH_MID = 0.2  # ... and sits in the middle of its line, clear of top and bottom
DASH_GAP = 0.6  # at most this many word heights outside the word
DROP_CAP_HEIGHT = (1.0, 2.5)  # a drop capital is one to two and a half lines tall
DROP_CAP_MAX_WIDTH = 2.0
DROP_CAP_GAP = 0.3
# An italic drop capital's crossbar or last stroke reaches over the first word's box
# (Crown of the Mayas: T 17px, M 10px, T 24px), so it may also overlap by this much.
DROP_CAP_OVERLAP = 0.8

# AND ONE MORE, found scoring four seeded titles (Camp Counselor, Donald's Grandma
# Duck, Balloonatics, The Day the Farm Stood Still) by the lettering a reviewed box
# holds and the built box cuts off: a lone letter EasyOCR left out at the start of a
# line (`A DUCK,`, `A PLASTIC`). Of 461 balloon boxes, 10 clipped real lettering;
# this fits 2 and moves none of the 382 within 6px of the reviewed box further out.
# A reach of 0.6 word heights also pulled 2 boxes across a joined balloon's seam.
# A whole first or last line EasyOCR never boxed (105's `DISASTER!`) is NOT fitted:
# the next balloon's first line sits as close to the box as a missed line does
# (`AHA!` 8px inside the edge, `DISASTER!` 2px), and fitting it pulled 12 boxes into
# their neighbours. Telling the two apart needs the balloon's interior.
LETTER_HEIGHT = (0.5, 1.2)  # a letter's height, in line heights
LEAD_REACH = 0.5  # a leading letter ends at most this many word heights before the word
LEAD_MAX_WIDTH = 1.2
# The same letter can straddle the word box instead of sitting wholly outside it: a
# caption's first capital, set a little wider than the rest (Crown of the Mayas: AT A
# VILLAGE's A 12px out, AS THE's A 6px). One sticking out more than this many pixels is
# fitted -- in a CAPTION only: at a balloon's edge the same test took a stroke of art
# and chained left through the drawing (Vol. 30's 192, 196 and 138).
LEAD_STRADDLE = 3

BOXES_JSON = "boxes.json"
BOXES_TXT = "boxes.txt"
SEED_FILE = "seed.json"
QUEUE_FILE = "queue.json"

# The keys a vision pass writes onto a group. A prelim file carrying any of them has
# been applied, and `build --replace` must not throw that work away.
APPLIED_MARKERS = ("speaker", "vision_note", "speaker_reviewed")

# What `prep --reseed` will not throw away: any trace of a review or a vision pass on
# a group. Prefixes, so `speaker_confidence`, `speaker_was`, `vision_added` count too.
REVIEW_MARKER_PREFIXES = ("speaker", "vision_")
REVIEW_MARKER_KEYS = frozenset({"type_reviewed"})
# What `refit` will not touch: a page a person has reviewed, whose boxes may be theirs.
REVIEWED_KEYS = ("speaker_reviewed", "type_reviewed")
# And only captions: on Vol. 30's balloons, built before the leading-letter fit, the
# refit took balloon-edge art as letters (a cloud's scallops, speed lines, a torn edge).
REFIT_TYPES = frozenset({"narration"})
REPLACES_PRELIM_KEY = "replaces_prelim"


def _dump_prelim(data: dict) -> str:
    """Return a groups file's text exactly as the prelim repo stores it."""
    return json.dumps(data, indent=4)


def _raw_boxes(raw_file: Path) -> list[dict[str, Any]]:
    """Return the raw OCR boxes, with their ids, quads, raw and accepted text."""
    boxes = []
    for i, (box, ocr_text, accepted_text, prob) in enumerate(json.loads(raw_file.read_text())):
        quad = [[box[0], box[1]], [box[2], box[3]], [box[4], box[5]], [box[6], box[7]]]
        boxes.append(
            {"id": str(i), "quad": quad, "ocr_text": ocr_text, "text": accepted_text, "prob": prob}
        )
    return boxes


def _panel_info(panel_boxes: PagePanelBoxes) -> tuple[dict, list[int]]:
    """Return the panel list in the segments-file shape, and each entry's panel number."""
    ordered = sorted(panel_boxes.panel_boxes, key=lambda b: b.panel_num)
    info = {"panels": [[b.x0, b.y0, b.w, b.h] for b in ordered]}
    return info, [b.panel_num for b in ordered]


def _panel_of(quad: list, panel_boxes: PagePanelBoxes) -> int:
    """Return the panel a box lies inside, else the one holding its centre, else -1."""
    info, nums = _panel_info(panel_boxes)
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    # The grouper's test takes an axis-aligned box, which is all Gemini ever hands
    # it; a raw OCR quad can be rotated a degree or two, and a flat one is degenerate.
    upright = [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]
    if max(xs) > min(xs) and max(ys) > min(ys):
        index = get_enclosing_panel_num(upright, info)
        if index != -1:
            return nums[index - 1]
    cx = sum(xs) / 4
    cy = sum(ys) / 4
    for b in panel_boxes.panel_boxes:
        if b.x0 <= cx <= b.x0 + b.w and b.y0 <= cy <= b.y0 + b.h:
            return b.panel_num
    return -1


def _review_markers(prelim_file: Path) -> set[str]:
    """Return the review or vision-pass keys any group in a prelim file carries."""
    if not prelim_file.is_file():
        return set()
    groups = json.loads(prelim_file.read_text()).get("groups", {})
    return {
        key
        for g in groups.values()
        for key in g
        if key.startswith(REVIEW_MARKER_PREFIXES) or key in REVIEW_MARKER_KEYS
    }


def _seed_pages(
    comics_database: ComicsDatabase, title_str: str, *, reseed: bool = False
) -> list[tuple[str, Path, bool]]:
    """Return (page, raw easyocr file, replaces a prelim) for each page of a title to seed.

    Without ``reseed`` that is every page with no prelim yet. With it, pages that
    already have prelim files are taken too, unless any of them carries review or
    vision work, in which case the whole title is refused.
    """
    comic = comics_database.get_comic_book(title_str)
    volume = comics_database.get_fanta_volume_int(title_str)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    raws = comic.get_srce_restored_ocr_raw_story_files(RESTORABLE_PAGE_TYPES)

    pages: list[tuple[str, Path, bool]] = []
    missing_raw: list[str] = []
    worked: list[str] = []
    for svg, raw_pair in zip(svg_files, raws, strict=True):
        page = Path(svg).name.split(".")[0]
        if get_title_from_volume_page(comics_database, volume, page)[0] != title_str:
            logger.info(f"Page {page} belongs to another title; not seeding it here.")
            continue
        easy_file = comic.get_ocr_prelim_groups_json_file(page, SEED_ENGINE.value)
        has_prelim = easy_file.is_file()
        if has_prelim and not reseed:
            logger.info(f"Page {page} already has an easyocr prelim; use vision-prep for it.")
            continue
        if has_prelim:
            copy_file = comic.get_ocr_prelim_groups_json_file(page, COPY_ENGINE.value)
            markers = _review_markers(easy_file) | _review_markers(copy_file)
            if markers:
                worked.append(f"{page} ({', '.join(sorted(markers))})")
                continue
        raw_file = next(f for f in raw_pair if SEED_ENGINE.value in f.name)
        if not raw_file.is_file():
            missing_raw.append(page)
            continue
        pages.append((page, raw_file, has_prelim))

    if worked:
        msg = (
            f'"{title_str}" has review or vision work that a reseed would throw away,'
            f" on page(s): {'; '.join(worked)}."
        )
        raise typer.BadParameter(msg)
    if missing_raw:
        msg = (
            f'No raw easyocr OCR for "{title_str}" page(s) {", ".join(missing_raw)}.'
            f' Run: barks-ocr-batch --engine easyocr --title "{title_str}"'
        )
        raise typer.BadParameter(msg)
    if not pages:
        hint = "" if reseed else " Pass --reseed to replace Gemini prelim files."
        msg = f'"{title_str}" has no page without a prelim file; nothing to seed.{hint}'
        raise typer.BadParameter(msg)
    return pages


def _boxes_txt(page: str, boxes: list[dict], panel_boxes: PagePanelBoxes) -> str:
    """Return the compact, one-line-per-box listing the pass reads."""
    lines = [f"# page {page}: {len(boxes)} raw easyocr box(es)", "# panels (page coords):"]
    lines += [
        f"#   panel {b.panel_num}: x{b.x0}-{b.x0 + b.w} y{b.y0}-{b.y0 + b.h}"
        f"  (panel-{b.panel_num:02d}.png origin {max(0, b.x0 - CROP_PAD_PX)},"
        f"{max(0, b.y0 - CROP_PAD_PX)})"
        for b in sorted(panel_boxes.panel_boxes, key=lambda b: b.panel_num)
    ]
    lines.append("# id  panel  x0,y0-x1,y1         prob  accepted text  |  raw text")
    for box in boxes:
        xs = [p[0] for p in box["quad"]]
        ys = [p[1] for p in box["quad"]]
        lines.append(
            f"{box['id']:>4}  p{box['panel_num']:<3} {min(xs):>4},{min(ys):>4}-{max(xs):>4},"
            f"{max(ys):>4}  {box['prob']:.2f}  {box['text']}  |  {box['ocr_text']}"
        )
    return "\n".join(lines) + "\n"


def _prep_page(  # noqa: PLR0913 -- one page's inputs, all distinct.
    comics_database: ComicsDatabase,
    title_str: str,
    page: str,
    raw_file: Path,
    panel_boxes: PagePanelBoxes,
    out_dir: Path,
) -> dict:
    """Write one page's crops, raw-box listing and capture stub. Returns its queue entry."""
    page_file = _page_image_file(comics_database, title_str, page)
    if not page_file.is_file():
        msg = f'Page image not found: "{page_file}".'
        raise typer.BadParameter(msg)
    page_image = Image.open(page_file).convert("RGB")

    page_dir = out_dir / page
    page_dir.mkdir(parents=True, exist_ok=True)
    oversized = []
    if _write_overview(page_image, page_dir / "page.png") > MAX_IMAGE_BYTES:
        oversized.append("page.png")
    panel_files: list[str] = []
    for panel_box in panel_boxes.panel_boxes:
        panel = _crop_panel(page_image, panel_box, CROP_PAD_PX)
        names, size = _write_panel(panel, page_dir, panel_box.panel_num)
        if size > MAX_IMAGE_BYTES:
            oversized.append(names[0])
        panel_files.extend(names)
    if oversized:
        msg = f"Page {page}: image(s) over {MAX_IMAGE_BYTES // 1024}KB: {', '.join(oversized)}."
        raise typer.BadParameter(msg)

    boxes = _raw_boxes(raw_file)
    for box in boxes:
        box["panel_num"] = _panel_of(box["quad"], panel_boxes)
    (page_dir / BOXES_JSON).write_text(json.dumps(boxes, indent=2) + "\n")
    (page_dir / BOXES_TXT).write_text(_boxes_txt(page, boxes, panel_boxes))

    panel_nums = [b.panel_num for b in panel_boxes.panel_boxes]
    (page_dir / CAPTURE_STUB_FILE).write_text(_capture_stub(panel_nums))
    return {
        "fanta_page": page,
        "title": title_str,
        "engine": SEED_ENGINE.value,
        "panels": panel_files,
        "panel_nums": panel_nums,
        "num_groups": 0,
        "num_raw_boxes": len(boxes),
        "seed": True,
        "status": "pending",
    }


@app.command(help="Crop a title's un-grouped pages and list their raw OCR boxes.")
def prep(
    title_str: Annotated[str, typer.Option("--title", "-t", help="Story title.")],
    out_dir: Annotated[
        Path | None,
        typer.Option("--out-dir", "-o", help=f"Work directory (default: under {DEFAULT_ROOT})."),
    ] = None,
    reseed: Annotated[
        bool,
        typer.Option(
            "--reseed",
            help="Also take pages that already have Gemini prelim files; build backs them up"
            " and replaces them. Refused if any page carries review or vision work.",
        ),
    ] = False,
) -> None:
    comics_database = ComicsDatabase()
    volume = comics_database.get_fanta_volume_int(title_str)
    holds = held_volumes()
    if volume in holds:
        reason = holds[volume] or "no reason given"
        msg = f"Vol. {volume} is on hold ({reason}) -- see {HOLDS_FILE}."
        raise typer.BadParameter(msg)

    pages = _seed_pages(comics_database, title_str, reseed=reseed)
    out_dir = out_dir or DEFAULT_ROOT.expanduser() / _slug(title_str)
    out_dir.mkdir(parents=True, exist_ok=True)
    title_boxes = TitlePanelBoxes(comics_database).get_page_panel_boxes(
        STR_TITLE_TO_ENUM[title_str]
    )
    entries = []
    for page, raw, replaces in pages:
        entry = _prep_page(comics_database, title_str, page, raw, title_boxes.pages[page], out_dir)
        entry[REPLACES_PRELIM_KEY] = replaces
        entries.append(entry)

    cast, things, titles = _cast_for(entries)
    queue = {
        "volume": volume,
        "engine": SEED_ENGINE.value,
        "titles": titles,
        "story_cast": cast,
        "story_things": things,
        "seed": True,
        "reseed": reseed,
        "pages": entries,
    }
    (out_dir / QUEUE_FILE).write_text(json.dumps(queue, indent=2) + "\n")
    (out_dir / ROSTER_FILE).write_text(roster_text(cast, things))

    total_boxes = sum(e["num_raw_boxes"] for e in entries)
    print(f'Seeded {len(entries)} page(s), {total_boxes} raw box(es) in "{out_dir}".')
    replacing = sum(e[REPLACES_PRELIM_KEY] for e in entries)
    if replacing:
        print(f"{replacing} page(s) replace Gemini prelim files; build backs those up first.")
    print(f'Read "{out_dir / ROSTER_FILE}" first. Per page write {SEED_FILE} and result.json;')
    print(f"then: barks-ocr-vision-seed build --out-dir {out_dir}")


def _expand_ids(ids: list[str | int]) -> list[str]:
    """Expand ``"6-13"`` range entries in a seed group's ``box_ids`` into single ids.

    EasyOCR boxes are word-level -- about fifty to a page -- so a balloon is
    usually a run of consecutive ids, and a range keeps the seed file readable.

    Raises:
        ValueError: for an entry that is neither an id nor an ascending range.

    """
    out: list[str] = []
    for item in ids:
        text = str(item)
        if "-" in text:
            lo, hi = (int(part) for part in text.split("-", 1))
            if hi < lo:
                msg = f"range {text!r} runs backwards"
                raise ValueError(msg)
            out.extend(str(n) for n in range(lo, hi + 1))
        else:
            out.append(str(int(text)))
    return out


def _group_errors(
    where: str, group: dict, boxes: dict[str, dict], panel_nums: list[int]
) -> list[str]:
    """Return what is wrong with one seed group, box reuse aside."""
    errors: list[str] = []
    text = group.get("ai_text")
    if not isinstance(text, str) or not text.strip():
        errors.append(f"{where}: ai_text is empty.")
    elif strip_markup(text) != text:
        errors.append(f"{where}: ai_text carries markup; put emphasis in result.json.")
    elif DASH_TOUCHING_LETTER.search(text):
        errors.append(
            f"{where}: an em dash touches a letter; the corpus spaces it (WORD — / — WORD)."
        )
    if group.get("type") not in GROUP_TYPES:
        errors.append(f"{where}: type {group.get('type')!r} is not in {sorted(GROUP_TYPES)}.")
    ids = group.get("box_ids", [])
    if not ids and not group.get("text_box"):
        errors.append(f"{where}: give box_ids, or a text_box for lettering OCR missed.")
    errors += [f"{where}: box id {i!r} is not in boxes.json." for i in ids if i not in boxes]
    panel = group.get("panel_num")
    if panel is not None and panel not in panel_nums:
        errors.append(f"{where}: panel_num {panel} is not one of {panel_nums}.")
    return errors


def _seed_errors(page: str, seed: dict, boxes: dict[str, dict], panel_nums: list[int]) -> list[str]:
    """Return everything wrong with one page's seed.json, before anything is written."""
    groups = seed.get("groups")
    if not isinstance(groups, list) or not groups:
        return [f"{page}: seed.json needs a non-empty 'groups' list."]
    errors: list[str] = []
    used: dict[str, int] = {}
    for i, group in enumerate(groups):
        where = f"{page} seed group {i}"
        errors += _group_errors(where, group, boxes, panel_nums)
        for box_id in group.get("box_ids", []):
            if box_id in used:
                errors.append(f"{where}: box {box_id} is already in group {used[box_id]}.")
            used[box_id] = i
    return errors


def _ink_components(page_file: Path) -> list[tuple[int, int, int, int]]:
    """Return the bounds (x0, y0, x1, y1) of every connected patch of dark ink on a page.

    Labelled over the WHOLE page, so a balloon outline stays one huge component
    and is never mistaken for a letter; labelling a window round the box cut the
    outline into letter-sized pieces and grew boxes into it.
    """
    image = cv2.imread(str(page_file))
    if image is None:
        msg = f'Could not read page image "{page_file}".'
        raise typer.BadParameter(msg)
    ink = (image.astype(int).sum(axis=2) < INK_DARK).astype(np.uint8)
    _count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(ink, connectivity=8)
    return [
        (int(x), int(y), int(x + w), int(y + h))
        for x, y, w, h, area in stats[1:]
        if area >= MIN_INK_AREA
    ]


def _word_bounds(quad: list) -> tuple[int, int, int, int]:
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    return min(xs), min(ys), max(xs), max(ys)


def _mark_edge(word: tuple, ink: list[tuple[int, int, int, int]]) -> tuple[int, int, int]:
    """Return how far right a clipped trailing mark takes this word, and its top and bottom."""
    _wx0, wy0, wx1, wy1 = word
    wh = wy1 - wy0
    edge, top, bottom = wx1, wy0, wy1
    for step in range(MARK_STEPS):
        reach = (MARK_REACH if step == 0 else MARK_STEP) * wh
        hits = [
            c
            for c in ink
            if -0.3 * wh <= c[0] - edge <= reach
            and c[2] > edge
            and c[2] - c[0] <= MARK_MAX_WIDTH * wh
            and c[3] - c[1] <= MARK_MAX_HEIGHT * wh
            and c[1] >= wy0 - MARK_BAND * wh
            and c[3] <= wy1 + MARK_BAND * wh
            and c[2] <= wx1 + MARK_MAX_GROWTH * wh
        ]
        if not hits:
            break
        edge = max(edge, *(c[2] for c in hits))
        top = min(top, *(c[1] for c in hits))
        bottom = max(bottom, *(c[3] for c in hits))
    return edge, top, bottom


def _fit_trailing_mark(
    text_box: list, members: list[dict], ink: list[tuple[int, int, int, int]], page_wh: float
) -> list:
    """Extend a balloon group's box over any trailing `!` its word boxes clipped."""
    x0, y0, x1, y1 = text_box[0][0], text_box[0][1], text_box[2][0], text_box[2][1]
    words = [_word_bounds(m["quad"]) for m in members]
    for word in words:
        _wx0, wy0, wx1, wy1 = word
        if wy1 - wy0 > ART_WORD * page_wh:
            continue  # art lettering, not a balloon line
        line_mates = [w for w in words if w[0] > wx1 and min(w[3], wy1) - max(w[1], wy0) > 0]
        if line_mates:
            continue  # not the last word on its line
        edge, top, bottom = _mark_edge(word, ink)
        if edge > wx1 + 2:
            x1, y0, y1 = max(x1, edge + MARK_PAD), min(y0, top), max(y1, bottom)
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _text_lines(words: list[tuple[int, int, int, int]]) -> list[list[tuple[int, int, int, int]]]:
    """Group word bounds into lines by vertical overlap, each line left to right."""
    lines: list[list[tuple[int, int, int, int]]] = []
    for word in sorted(words, key=lambda w: (w[1], w[0])):
        for line in lines:
            last = line[-1]
            if min(last[3], word[3]) - max(last[1], word[1]) > 0.5 * (word[3] - word[1]):
                line.append(word)
                break
        else:
            lines.append([word])
    return [sorted(line) for line in lines]


def _is_dash(c: tuple[int, int, int, int], word: tuple[int, int, int, int]) -> bool:
    """Return whether an ink patch is shaped and placed like an em dash on this word's line."""
    h = word[3] - word[1]
    width, height = c[2] - c[0], c[3] - c[1]
    middle = (c[1] + c[3]) / 2
    return (
        height <= DASH_MAX_HEIGHT * h
        and DASH_WIDTH[0] * h <= width <= DASH_WIDTH[1] * h
        and word[1] + DASH_MID * h <= middle <= word[3] - DASH_MID * h
    )


def _fit_edge_dashes(text_box: list, lines: list, ink: list[tuple[int, int, int, int]]) -> list:
    """Extend a box over an em dash just outside the first or last word of any line."""
    x0, y0, x1, y1 = text_box[0][0], text_box[0][1], text_box[2][0], text_box[2][1]
    for line in lines:
        first, last = line[0], line[-1]
        for c in ink:
            if _is_dash(c, first) and 0 <= first[0] - c[2] <= DASH_GAP * (first[3] - first[1]):
                x0 = min(x0, c[0] - MARK_PAD)
            if _is_dash(c, last) and 0 <= c[0] - last[2] <= DASH_GAP * (last[3] - last[1]):
                x1 = max(x1, c[2] + MARK_PAD)
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _fit_drop_capital(text_box: list, lines: list, ink: list[tuple[int, int, int, int]]) -> list:
    """Extend a caption's box over a drop capital set just left of its first word."""
    x0, y0, x1, y1 = text_box[0][0], text_box[0][1], text_box[2][0], text_box[2][1]
    word = lines[0][0]
    h = word[3] - word[1]
    for c in ink:
        width, height = c[2] - c[0], c[3] - c[1]
        if (
            c[0] < word[0]
            and -DROP_CAP_OVERLAP * h <= word[0] - c[2] <= DROP_CAP_GAP * h
            and DROP_CAP_HEIGHT[0] * h <= height <= DROP_CAP_HEIGHT[1] * h
            and width <= DROP_CAP_MAX_WIDTH * h
            and min(c[3], word[3]) - max(c[1], word[1]) > 0.5 * h
        ):
            x0, y0, y1 = (
                min(x0, c[0] - MARK_PAD),
                min(y0, c[1] - MARK_PAD),
                max(y1, c[3] + MARK_PAD),
            )
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _is_letter(c: tuple[int, int, int, int], height: float) -> bool:
    """Return whether an ink patch is sized like a letter on a line this tall."""
    h = c[3] - c[1]
    return LETTER_HEIGHT[0] * height <= h <= LETTER_HEIGHT[1] * height


def _fit_leading_letters(
    text_box: list, lines: list, ink: list[tuple[int, int, int, int]], *, straddle: bool
) -> list:
    """Extend a box left over a letter EasyOCR left out before any line's first word.

    With ``straddle`` (captions only) a letter sticking out of the word box counts too.
    """
    x0, y0, x1, y1 = text_box[0][0], text_box[0][1], text_box[2][0], text_box[2][1]
    for line in lines:
        _fx0, fy0, _fx1, fy1 = line[0]
        h = fy1 - fy0
        edge = line[0][0]
        for _step in range(MARK_STEPS):
            hits = [
                c
                for c in ink
                if edge - c[2] <= LEAD_REACH * h
                and (c[2] <= edge or (straddle and c[0] < edge - LEAD_STRADDLE))
                and c[0] < edge
                and _is_letter(c, h)
                and c[2] - c[0] <= LEAD_MAX_WIDTH * h
                and c[1] >= fy0 - MARK_BAND * h
                and c[3] <= fy1 + MARK_BAND * h
            ]
            if not hits:
                break
            edge = min(c[0] for c in hits)
        if edge < line[0][0]:
            x0 = min(x0, edge - MARK_PAD)
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _word_box(
    group: dict, members: list[dict], ink: list[tuple[int, int, int, int]], page_wh: float
) -> list:
    """Return a group's box built from its word boxes, fitted over ink they clipped."""
    quads = [[tuple(p) for p in m["quad"]] for m in members]
    text_box = [list(p) for p in get_enclosing_box(quads)]
    if group["type"] in BALLOON_TYPES:
        text_box = _fit_trailing_mark(text_box, members, ink, page_wh)
        lines = _text_lines([_word_bounds(m["quad"]) for m in members])
        if DASH in group["ai_text"]:
            text_box = _fit_edge_dashes(text_box, lines, ink)
        if group["type"] == "narration":
            text_box = _fit_drop_capital(text_box, lines, ink)
        text_box = _fit_leading_letters(text_box, lines, ink, straddle=group["type"] == "narration")
    return text_box


def _prelim_group(
    group: dict,
    boxes: dict[str, dict],
    panel_boxes: PagePanelBoxes,
    ink: list[tuple[int, int, int, int]],
    page_wh: float,
) -> dict:
    """Build one prelim group in the Gemini grouper's schema."""
    members = [boxes[i] for i in group.get("box_ids", [])]
    if group.get("text_box"):
        text_box = [list(p) for p in group["text_box"]]
    else:
        text_box = _word_box(group, members, ink, page_wh)
    panel_num = group.get("panel_num") or _panel_of(text_box, panel_boxes)
    return {
        "panel_id": str(panel_num),
        "panel_num": panel_num,
        "text_box": text_box,
        "ocr_text": " ".join(m["ocr_text"] for m in members),
        "ai_text": group["ai_text"],
        "type": group["type"],
        "style": "normal",
        "notes": group.get("notes", ""),
        "cleaned_box_texts": {
            m["id"]: {"text_frag": m["text"], "text_box": m["quad"]} for m in members
        },
    }


def _page_word_height(boxes: dict[str, dict]) -> float:
    """Return the median height of a page's raw word boxes."""
    return statistics.median(
        _word_bounds(b["quad"])[3] - _word_bounds(b["quad"])[1] for b in boxes.values()
    )


def _was_applied(prelim_file: Path) -> bool:
    """Return whether a prelim file already carries a vision pass's annotations."""
    groups = json.loads(prelim_file.read_text()).get("groups", {})
    return any(key in g for g in groups.values() for key in APPLIED_MARKERS)


def _load_seed(seed_file: Path, panel_nums: list[int]) -> tuple[dict, dict[str, dict], list[str]]:
    """Read one page's seed and raw boxes, expand id ranges, and check the seed."""
    page = seed_file.parent.name
    seed = json.loads(seed_file.read_text())
    boxes = {b["id"]: b for b in json.loads((seed_file.parent / BOXES_JSON).read_text())}
    try:
        for group in seed.get("groups") or []:
            group["box_ids"] = _expand_ids(group.get("box_ids", []))
    except ValueError as exc:
        return seed, boxes, [f"{page}: bad box_ids entry: {exc}."]
    return seed, boxes, _seed_errors(page, seed, boxes, panel_nums)


def _overwrite_errors(
    page: str, easy_file: Path, copy_file: Path, *, replaces: bool, replace: bool
) -> list[str]:
    """Return why a page's existing prelim files must not be overwritten, if they must not."""
    errors: list[str] = []
    if replaces:
        # Checked again here: the files may have been worked on since prep.
        markers = _review_markers(easy_file) | _review_markers(copy_file)
        if markers:
            errors.append(
                f"{page}: its prelim files now carry review or vision work"
                f" ({', '.join(sorted(markers))}); not replacing them."
            )
        return errors
    if easy_file.is_file() and _was_applied(easy_file):
        errors.append(f"{page}: {easy_file.name} has been applied to; a rebuild would lose it.")
    elif easy_file.is_file() and not replace:
        errors.append(f"{page}: {easy_file.name} exists; pass --replace to rebuild it.")
    if copy_file.is_file() and COPIED_FROM_ENGINE_KEY not in json.loads(copy_file.read_text()):
        errors.append(f"{page}: {copy_file.name} is a real paddleocr file; not replacing.")
    return errors


def _plan_page(
    comics_database: ComicsDatabase,
    out_dir: Path,
    entry: dict,
    panel_boxes: PagePanelBoxes,
    *,
    replace: bool,
) -> tuple[dict | None, list[str]]:
    """Validate one page's seed and return the prelim it would write, or its errors."""
    page = entry["fanta_page"]
    seed_file = out_dir / page / SEED_FILE
    if not seed_file.is_file():
        logger.warning(f"Page {page}: no {SEED_FILE} yet, skipping.")
        return None, []
    seed, boxes, errors = _load_seed(seed_file, entry["panel_nums"])
    if errors:
        return None, errors
    ink = _ink_components(_page_image_file(comics_database, entry["title"], page))
    page_wh = _page_word_height(boxes)
    groups = {
        str(i): _prelim_group(g, boxes, panel_boxes, ink, page_wh)
        for i, g in enumerate(seed["groups"])
    }
    no_panel = [gid for gid, g in groups.items() if g["panel_num"] == -1]
    if no_panel:
        return None, [f"{page}: group(s) {no_panel} fall in no panel; give panel_num."]
    prelim = {"use_as_final": False, "groups": groups}

    comic = comics_database.get_comic_book(entry["title"])
    easy_file = comic.get_ocr_prelim_groups_json_file(page, SEED_ENGINE.value)
    copy_file = comic.get_ocr_prelim_groups_json_file(page, COPY_ENGINE.value)
    if easy_file.is_file() and easy_file.read_text() == _dump_prelim(prelim):
        logger.info(f"Page {page}: {easy_file.name} is already this seed; leaving it.")
        return None, []
    replaces = entry.get(REPLACES_PRELIM_KEY, False)
    errors = _overwrite_errors(page, easy_file, copy_file, replaces=replaces, replace=replace)
    if errors:
        return None, errors
    grouped = {i for g in seed["groups"] for i in g.get("box_ids", [])}
    unused = [b for b in boxes.values() if b["id"] not in grouped]
    if unused:
        listing = ", ".join(f"{b['id']} {b['text']!r}" for b in unused)
        logger.info(f"Page {page}: {len(unused)} raw box(es) in no group: {listing}")
    return {
        "page": page,
        "prelim": prelim,
        "easy_file": easy_file,
        "copy_file": copy_file,
        "backup": replaces,
    }, []


def _backup_prelim(prelim_file: Path) -> Path:
    """Copy a prelim file into the prelim backup tree, as vision-apply does before a write."""
    backup_file = Path(
        str(get_backup_file(prelim_file)).replace(str(OCR_PRELIM_DIR), str(OCR_PRELIM_BACKUP_DIR))
    )
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(prelim_file, backup_file)
    return backup_file


def _write_page(plan: dict, out_dir: Path) -> None:
    """Write one page's easyocr prelim, its marked paddleocr copy, and groups.json."""
    prelim = plan["prelim"]
    if plan["backup"]:
        for prelim_file in (plan["easy_file"], plan["copy_file"]):
            if prelim_file.is_file():
                logger.info(f"Backed up {prelim_file.name} to {_backup_prelim(prelim_file)}.")
    plan["easy_file"].parent.mkdir(parents=True, exist_ok=True)
    plan["easy_file"].write_text(_dump_prelim(prelim))
    plan["copy_file"].write_text(
        _dump_prelim({COPIED_FROM_ENGINE_KEY: SEED_ENGINE.value, **prelim})
    )
    trimmed = {gid: {f: g.get(f) for f in GROUP_FIELDS} for gid, g in prelim["groups"].items()}
    (out_dir / plan["page"] / "groups.json").write_text(json.dumps(trimmed, indent=2) + "\n")


@app.command(help="Write the easyocr prelim from each page's seed.json, and its paddleocr copy.")
def build(
    out_dir: Annotated[Path, typer.Option("--out-dir", "-o", help="The seed prep directory.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate; write nothing.")] = False,
    replace: Annotated[
        bool,
        typer.Option("--replace", help="Rebuild a seeded prelim that no pass has applied to yet."),
    ] = False,
) -> None:
    queue = json.loads((out_dir / QUEUE_FILE).read_text())
    if not queue.get("seed"):
        msg = f'"{out_dir}" is not a seed directory; use vision-apply on it.'
        raise typer.BadParameter(msg)
    comics_database = ComicsDatabase()
    title_boxes = TitlePanelBoxes(comics_database)
    panel_boxes = {
        t: title_boxes.get_page_panel_boxes(STR_TITLE_TO_ENUM[t]).pages for t in queue["titles"]
    }

    plans: list[tuple[dict, dict]] = []
    errors: list[str] = []
    for entry in queue["pages"]:
        page_boxes = panel_boxes[entry["title"]][entry["fanta_page"]]
        plan, page_errors = _plan_page(comics_database, out_dir, entry, page_boxes, replace=replace)
        errors += page_errors
        if plan is not None:
            plans.append((entry, plan))
    if errors:
        print(f"{len(errors)} problem(s); nothing written:")
        for error in errors:
            print(f"  {error}")
        raise typer.Exit(code=1)

    for entry, plan in plans:
        groups = plan["prelim"]["groups"]
        replacing = " (replaces the Gemini files, backed up first)" if plan["backup"] else ""
        print(
            f"{plan['page']}: {len(groups)} group(s) -> {plan['easy_file'].name} + copy{replacing}"
        )
        if not dry_run:
            _write_page(plan, out_dir)
            entry["num_groups"] = len(groups)
    if not dry_run:
        (out_dir / QUEUE_FILE).write_text(json.dumps(queue, indent=2) + "\n")
    print(f"{'Would write' if dry_run else 'Wrote'} {len(plans)} page(s).")
    if not dry_run and plans:
        print(f"Next: barks-ocr-vision-apply --out-dir {out_dir} --no-mirror --dry-run")


def _contains(outer: list, inner: list) -> bool:
    """Return whether one box encloses another."""
    return (
        outer[0][0] <= inner[0][0]
        and outer[0][1] <= inner[0][1]
        and outer[2][0] >= inner[2][0]
        and outer[2][1] >= inner[2][1]
    )


def _refit_page(comics_database: ComicsDatabase, out_dir: Path, entry: dict) -> tuple[dict, int]:
    """Return an applied page's prelim with its word-built boxes refitted, and how many grew."""
    page = entry["fanta_page"]
    comic = comics_database.get_comic_book(entry["title"])
    easy_file = comic.get_ocr_prelim_groups_json_file(page, SEED_ENGINE.value)
    seed_file = out_dir / page / SEED_FILE
    if not seed_file.is_file() or not easy_file.is_file():
        return {}, 0
    seed, boxes, errors = _load_seed(seed_file, entry["panel_nums"])
    text = easy_file.read_text()
    prelim = json.loads(text)
    groups = prelim["groups"]
    if errors or text != _dump_prelim(prelim):
        print(f"{page}: seed or prelim file does not check out; left alone.")
        return {}, 0
    if any(key in g for g in groups.values() for key in REVIEWED_KEYS):
        print(f"{page}: reviewed; left alone.")
        return {}, 0
    ink = _ink_components(_page_image_file(comics_database, entry["title"], page))
    page_wh = _page_word_height(boxes)
    grown = 0
    for i, seed_group in enumerate(seed["groups"]):
        group = groups.get(str(i))
        if group is None or set(group["cleaned_box_texts"]) != set(seed_group["box_ids"]):
            print(f"{page}: group {i} no longer matches its seed (an add or re-sort?); left alone.")
            return {}, 0
        if seed_group.get("text_box") or seed_group["type"] not in REFIT_TYPES:
            continue
        old = group["text_box"]
        new = _word_box(seed_group, [boxes[b] for b in seed_group["box_ids"]], ink, page_wh)
        if new == old:
            continue
        if not _contains(new, old):
            print(f"{page} g{i}: the refit would cut the box ({old} -> {new}); left alone.")
            continue
        edges = f"x0 {new[0][0] - old[0][0]:+d} y0 {new[0][1] - old[0][1]:+d}"
        edges += f" x1 {new[2][0] - old[2][0]:+d} y1 {new[2][1] - old[2][1]:+d}"
        print(f"{page} g{i} {seed_group['type']}: {edges}  {seed_group['ai_text'][:30]!r}")
        group["text_box"] = new
        grown += 1
    return prelim, grown


@app.command(help="Refit the word-built boxes of a seed directory's applied, unreviewed pages.")
def refit(
    out_dir: Annotated[Path, typer.Option("--out-dir", "-o", help="The seed prep directory.")],
    write: Annotated[
        bool, typer.Option("--write", help="Write; the default is a dry run.")
    ] = False,
) -> None:
    queue = json.loads((out_dir / QUEUE_FILE).read_text())
    if not queue.get("seed"):
        msg = f'"{out_dir}" is not a seed directory.'
        raise typer.BadParameter(msg)
    comics_database = ComicsDatabase()
    pages = boxes_grown = 0
    for entry in queue["pages"]:
        prelim, grown = _refit_page(comics_database, out_dir, entry)
        if not grown:
            continue
        pages += 1
        boxes_grown += grown
        if write:
            comic = comics_database.get_comic_book(entry["title"])
            page = entry["fanta_page"]
            copy_file = comic.get_ocr_prelim_groups_json_file(page, COPY_ENGINE.value)
            comic.get_ocr_prelim_groups_json_file(page, SEED_ENGINE.value).write_text(
                _dump_prelim(prelim)
            )
            if COPIED_FROM_ENGINE_KEY in json.loads(copy_file.read_text()):
                copy_file.write_text(
                    _dump_prelim({COPIED_FROM_ENGINE_KEY: SEED_ENGINE.value, **prelim})
                )
    verb = "Refitted" if write else "Would refit"
    print(f"{verb} {boxes_grown} box(es) on {pages} page(s).")


@app.command(help="Re-copy a title's seeded easyocr prelim files onto their paddleocr copies.")
def sync(
    title_str: Annotated[str, typer.Option("--title", "-t", help="Story title.")],
    write: Annotated[
        bool, typer.Option("--write", help="Write; the default is a dry run.")
    ] = False,
) -> None:
    comics_database = ComicsDatabase()
    comic = comics_database.get_comic_book(title_str)
    svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)
    changed = same = 0
    for svg in svg_files:
        page = Path(svg).name.split(".")[0]
        easy_file = comic.get_ocr_prelim_groups_json_file(page, SEED_ENGINE.value)
        copy_file = comic.get_ocr_prelim_groups_json_file(page, COPY_ENGINE.value)
        if not easy_file.is_file() or not copy_file.is_file():
            continue
        current = json.loads(copy_file.read_text())
        if COPIED_FROM_ENGINE_KEY not in current:
            continue  # A real paddleocr file: not a copy, so not this tool's.
        wanted = _dump_prelim(
            {COPIED_FROM_ENGINE_KEY: SEED_ENGINE.value, **json.loads(easy_file.read_text())}
        )
        if copy_file.read_text() == wanted:
            same += 1
            continue
        changed += 1
        print(f"{page}: {copy_file.name} differs from its easyocr source")
        if write:
            copy_file.write_text(wanted)
    verb = "Re-copied" if write else "Would re-copy"
    print(f"{verb} {changed} page(s); {same} already identical.")


if __name__ == "__main__":
    app()

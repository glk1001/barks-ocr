"""Measure a balloon's lettering from the page image, and judge its text_box by it.

Every other box check in ``ocr_check`` reads the box against something the
engines or the grouper wrote down -- the page's line heights, the OCR fragment
quads, the other engine's box. None of them looks at the ink, so none can see
the fault reviews have spent the most time on: a box that cuts into its own
lettering. The fit check only ever gets easier as a box grows, and nothing asks
whether lettering sits outside it.

This module asks. It finds the lettering's ink inside the balloon's fill and
compares each side of the box with it. A side the lettering crosses is
``box_too_tight``, and where the measurement can be trusted it is padded out to
the house padding; a crossing too deep to trust is ``box_too_tight_deep``; a
side with far more blank fill than the house allows is ``box_too_loose``. Only
the first is ever fixed.

THE HOUSE PADDING IS MEASURED, NOT CHOSEN. 2,588 balloon and caption boxes were
changed by hand in the prelim repo's review commits with their text unchanged
(mined 2026-10-11). Measured against their ink, the reviewed boxes sit a median
7px off the lettering on every side, inter-quartile about 5-9px; before review
the median was 5-6px with a long tail into the lettering, and 89% of the sides a
reviewer moved by more than 3px moved OUTWARD, by a median 7px. The reviewer was
mostly padding out tight boxes, not redrawing them.

A BOX IS TIGHT ONLY WHERE THE LETTERING CROSSES IT, by ``MIN_CLIP_PX`` or more.
The same reviewed boxes often leave a side 0-2px off the ink and were accepted
so, so falling short of the house padding is not a fault; and a 1px crossing is
the anti-aliased rim of the last ink row. Measured with every rule here over the
same edits and over 3,000 random balloon groups no review had touched (Vols.
1-24):

==================  ========  ==========  =========
verdict             reviewed  pre-review  untouched
==================  ========  ==========  =========
tight, fixable          0.9%       10.0%       0.6%
tight, not fixed        0.3%        1.9%       0.1%
tight, deep             1.7%       11.1%       1.1%
loose                   0.1%        0.1%       0.1%
not judged              8.0%        8.0%       2.2%
==================  ========  ==========  =========

The fix, applied to the 260 fixable pre-review boxes, moves each crossed side a
median 10px from where the reviewer put it to 3px, and leaves 12% of the sides it
moves further from the reviewer's than they were.

The first trial write (Vol. 12, 2026-10-11) is why the shape and fill tests read
at ``SHAPE_GREY_MAX`` and ``FILL_TONE_TOLERANCE``. Before them, the reviewer
pulled 18 of its 26 fixed boxes back in: the fix had padded out over pieces of
balloon outline. After them, none of the reviewer's 52 final boxes (26 groups,
both engines) reaches the default queue, and the proposals made from the boxes
as they were before the trial land a median 1px from the reviewer's. The deep
band is never fixed and ``ocr_check`` reports it only on request.

What counts as lettering, and why each test is there:

- **Dark**: one shape is what joins up below ``SHAPE_GREY_MAX``, and its extent
  is its pixels below ``INK_GREY_MAX``.
- **Enclosed by the balloon's own fill.** The fill is the non-ink region most of
  the box's interior belongs to, and a component counts only if at least
  ``MIN_RING_IN_FILL`` of the pixels round it are that fill. This is what keeps
  out the balloon outline and its tail, a thought balloon's puffs, and the
  lettering of a joined balloon next door; without it a quarter of the reviewed
  boxes measured as crossed by their own lettering. The ring is taken round the
  letter with its counters filled -- see ``_ring_in_fill``.
- **Letter-sized**: no taller than ``MAX_LETTER_HEIGHT_LINES`` line heights, which
  still admits a drop capital, and not a thin curve longer than
  ``THIN_CURVE_MIN_LINES`` lines -- an outline arc that slipped the fill test.
- **Connected to the box's own lettering**: seeded from the components centred
  inside the box, then grown through letter-sized components a word space along
  a line or a line space below it -- see ``_grow_from_box``. That is how a
  letter the box cuts off is found.

Lettering touching the balloon outline merges with it into one component and
fails the size tests, so it goes unmeasured. That only ever makes the measured
extent SMALLER, which can hide a clip but never invent one -- and it lowers the
ink coverage, which is the gate on writing a fix.

Only dialogue, thought and narration are judged. Sound effects, signs and titles
are lettering drawn over art, where "the balloon's fill" does not exist and the
measurement is noise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2
import numpy as np

from barks_ocr.utils.ocr_box import text_box_problem

if TYPE_CHECKING:
    from pathlib import Path

    from barks_fantagraphics.barks_titles import Titles
    from barks_fantagraphics.comics_database import ComicsDatabase

BALLOON_TYPES: frozenset[str] = frozenset({"dialogue", "thought", "narration"})

INK_GREY_MAX = 110  # grey below this is ink: what the lettering's extent is measured on
# Grey below this is part of a SHAPE: what decides which pixels belong together,
# and where the balloon's fill is. At INK_GREY_MAX a thin or faint run of balloon
# outline breaks into letter-sized pieces, each ringed by light pixels, and the
# grey background leaks through the breaks into the fill -- so scallops, bumps
# and a tail's root measured as lettering outside the box, and the first trial
# --fix-padding (Vol. 12, 2026-10-11) padded boxes out over them: the reviewer
# pulled 18 of its 26 boxes back in. The looser cut keeps the outline whole and
# the fill sealed, and takes a letter's anti-aliased rim in with the letter.
SHAPE_GREY_MAX = 170
# The fill is also the balloon's own TONE, within this many grey levels of the
# median inside the box. Without it the grey ground beside a white balloon was
# "fill" too wherever the two met, and a piece of outline between them passed as
# a letter enclosed by fill.
FILL_TONE_TOLERANCE = 20
RING_GAP_PX = 2  # the fill test reads a ring this far out, past a letter's anti-aliased rim
HOUSE_PADDING_PX = 7  # the reviewed boxes' median, every side
# The lettering must cross the edge by at least this much to make the box tight.
# A 1px crossing is the anti-aliased rim of the last ink row or column: invisible,
# and as common on the reviewed boxes as the 0-2px margins reviewers accept.
MIN_CLIP_PX = 2
MAX_FIXABLE_CLIP_PX = 8  # a deeper crossing is a clip OR a mis-measure: a person decides
LOOSE_PADDING_PX = 25  # this much blank fill on a side is box_too_loose
MIN_INK_COVERAGE = 0.9  # the measured letters must explain this much of the box's ink to fix
# Letters taller than this many of the page's reference line heights are display
# lettering -- a shout, a song -- and are not judged. On the reviewed boxes this
# leaves out 2.8% of the ones measuring fine and 40% of the deep crossings, which
# were HELP! HELP!, SNORT! GROWL!, BAA! and the like, drawn over open sky.
DISPLAY_LETTER_RATIO = 1.0

SEARCH_MARGIN_LINES = 0.8  # how far past the box to look for lettering it cuts off
MIN_SEARCH_MARGIN_PX = 12
MIN_RING_IN_FILL = 0.9
MAX_LETTER_HEIGHT_LINES = 3.2
THIN_CURVE_MIN_LINES = 2.0
THIN_CURVE_MAX_DENSITY = 0.08
MIN_LETTER_HEIGHT_LINES = 0.3  # a seed shorter than this is punctuation, not a letter
MIN_CHAIN_HEIGHT = 0.5  # a component joins the chain at this many letter heights...
MAX_CHAIN_HEIGHT = 1.5  # ...up to this many
WORD_GAP_LETTERS = 1.0  # the gap the chain jumps along a line, in letter heights
LINE_GAP_LETTERS = 0.7  # ...and between lines
REACH_LETTERS = 1.5  # nothing wholly further out than this past the box joins the chain
MIN_COMPONENT_PX = 3
COVERAGE_INSET_PX = 2  # ignore the box's own edge when counting the ink inside it
INNER_FILL_INSET_PX = 3  # sample the fill this far inside the box

TOO_TIGHT_ISSUE = "box_too_tight"
# A crossing deeper than MAX_FIXABLE_CLIP_PX. Kept apart because it is where a
# real clip and a mis-measure overlap: 45 of the 2,588 reviewed boxes -- accepted by
# a reviewer, so mostly the measurement's error -- cross that deep, against 287 of
# the same groups before review.
TOO_TIGHT_DEEP_ISSUE = "box_too_tight_deep"
TOO_LOOSE_ISSUE = "box_too_loose"

SIDES = ("left", "top", "right", "bottom")

Bounds = tuple[int, int, int, int]  # x0, y0, x1, y1 -- x1/y1 exclusive


@dataclass(frozen=True)
class LetteringInk:
    """Where a box's lettering actually is, as measured off the page image.

    Attributes:
        bounds: The lettering's extent in page pixels, ``(x0, y0, x1, y1)`` with
            the far edges exclusive.
        letter_height: The median height of the box's own letters, in pixels.
        coverage: The share of the ink inside the box that belongs to the
            measured lettering. Low when something dark the measurement could
            not place -- a letter merged into the outline, art -- is in there.
        empty_margins: Per side, in ``SIDES`` order, whether the strip between
            the box edge and the lettering holds no ink at all.

    """

    bounds: Bounds
    letter_height: float
    coverage: float
    empty_margins: tuple[bool, bool, bool, bool]


@dataclass(frozen=True)
class PaddingVerdict:
    """What the ink says about a box, and the box it would be fixed to.

    Attributes:
        issue_type: ``TOO_TIGHT_ISSUE``, ``TOO_TIGHT_DEEP_ISSUE``,
            ``TOO_LOOSE_ISSUE``, or None when the box is within the house standard.
        padding: Per side, in ``SIDES`` order, pixels from the box edge in to
            the lettering. Negative where the lettering crosses the edge.
        fixed_box: The corrected ``text_box`` when a tight box can be fixed
            safely, else None.
        note: What the reviewer is told -- the measurement, and why a tight box
            was not fixed.

    """

    issue_type: str | None
    padding: tuple[int, int, int, int]
    fixed_box: list[list[int]] | None
    note: str


def page_image_file(
    comics_database: ComicsDatabase, title: Titles, volume: int, fanta_page: str
) -> Path:
    """Return the restored page image the ``text_box`` coordinates are measured on.

    The same lookup the Kivy editor draws its crops from, one-pagers included.

    Args:
        comics_database: The comics database.
        title: The title the page belongs to.
        volume: The Fantagraphics volume.
        fanta_page: The page's scan stem.

    Returns:
        The image file's path.

    """
    from pathlib import Path  # noqa: PLC0415 -- the TYPE_CHECKING import is not runtime

    from barks_fantagraphics.barks_titles import ENUM_TO_STR_TITLE  # noqa: PLC0415
    from barks_fantagraphics.comic_book_info import ONE_PAGERS  # noqa: PLC0415
    from barks_fantagraphics.comics_consts import PNG_FILE_EXT, PageType  # noqa: PLC0415

    if title in ONE_PAGERS:
        image_dir = comics_database.get_fantagraphics_restored_volume_image_dir(volume)
        return Path(image_dir) / (fanta_page + PNG_FILE_EXT)
    comic = comics_database.get_comic_book(ENUM_TO_STR_TITLE[title])
    return comic.get_final_srce_story_file(fanta_page, PageType.BODY)[0]


def _box_bounds(text_box: list) -> Bounds:
    xs = [int(point[0]) for point in text_box]
    ys = [int(point[1]) for point in text_box]
    return min(xs), min(ys), max(xs), max(ys)


def _ring_in_fill(fill_labels: np.ndarray, component: np.ndarray, fill: int) -> float:
    """Return the share of the pixels just outside *component* that belong to the fill region.

    The ring is taken round the component with its counters filled in. The
    counter of an O, A, B, D, P, R, 0, 6, 8 or 9 is a non-ink region of its own,
    not the balloon's fill, and a ring that took in its edge failed every such
    letter: measured coverage then sat at a median 64% on boxes whose lettering
    was entirely measurable.
    """
    gap = RING_GAP_PX
    mask = cv2.copyMakeBorder(component, gap, gap, gap, gap, cv2.BORDER_CONSTANT, value=0)
    outside = mask.copy()
    flood_mask = np.zeros((mask.shape[0] + 2, mask.shape[1] + 2), np.uint8)
    cv2.floodFill(outside, flood_mask, (0, 0), 2)
    solid = (outside != 2).astype(np.uint8)  # noqa: PLR2004
    inner = cv2.dilate(solid, np.ones((2 * gap - 1, 2 * gap - 1), np.uint8))
    ring = cv2.dilate(solid, np.ones((2 * gap + 1, 2 * gap + 1), np.uint8)) - inner
    return float((fill_labels[ring > 0] == fill).mean())


def _letter_components(
    shapes: np.ndarray,
    ink: np.ndarray,
    fill_labels: np.ndarray,
    fill: int,
    line_height: float,
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Label the region's shapes and return (labels, stats, the ids that are lettering).

    Shapes are cut at ``SHAPE_GREY_MAX``; a shape with fewer than
    ``MIN_COMPONENT_PX`` pixels of real ink (``INK_GREY_MAX``) is a smudge.
    """
    count, labels, stats, _ = cv2.connectedComponentsWithStats(shapes, connectivity=8)
    ink_px = np.bincount(labels[ink], minlength=count)
    gap = RING_GAP_PX
    padded_fill = cv2.copyMakeBorder(fill_labels, gap, gap, gap, gap, cv2.BORDER_CONSTANT, value=-1)
    height, width = shapes.shape
    letters: list[int] = []
    for i in range(1, count):
        x, y, w, h, area = (int(v) for v in stats[i])
        if ink_px[i] < MIN_COMPONENT_PX:
            continue
        if x == 0 or y == 0 or x + w >= width or y + h >= height:
            continue  # runs off the search region: outline or art
        if h > MAX_LETTER_HEIGHT_LINES * line_height or w > 0.9 * width:
            continue
        if max(w, h) > THIN_CURVE_MIN_LINES * line_height and area / (w * h) < (
            THIN_CURVE_MAX_DENSITY
        ):
            continue  # a long thin curve: an outline arc or a tail
        component = (labels[y : y + h, x : x + w] == i).astype(np.uint8)
        ring_fill = padded_fill[y : y + h + 2 * gap, x : x + w + 2 * gap]
        if _ring_in_fill(ring_fill, component, fill) >= MIN_RING_IN_FILL:
            letters.append(i)
    return labels, stats, letters


def _rect(stats: np.ndarray, i: int) -> Bounds:
    x, y, w, h = (int(v) for v in stats[i][:4])
    return x, y, x + w, y + h


def _seed_letters(
    stats: np.ndarray, letters: list[int], box: Bounds, line_height: float
) -> tuple[set[int], float]:
    """Return the letters centred in *box*, and their median height (0.0 when none).

    Seeds shorter than ``MIN_LETTER_HEIGHT_LINES`` are punctuation, and are left
    out of the median so that a stop-heavy line does not shrink it.
    """
    bx0, by0, bx1, by1 = box
    taken = set()
    for i in letters:
        x0, y0, x1, y1 = _rect(stats, i)
        if bx0 <= (x0 + x1) / 2 <= bx1 and by0 <= (y0 + y1) / 2 <= by1:
            taken.add(i)
    if not taken:
        return taken, 0.0
    heights = [_rect(stats, i)[3] - _rect(stats, i)[1] for i in taken]
    tall = [h for h in heights if h >= MIN_LETTER_HEIGHT_LINES * line_height]
    return taken, float(np.median(tall or heights))


def _grow_from_box(
    stats: np.ndarray, letters: list[int], box: Bounds, line_height: float
) -> tuple[set[int], float]:
    """Take the letters centred in *box*, plus every letter-like component chained to them.

    The chain is what finds a letter the box cuts off, and it is kept to the
    box's own lettering in three ways, each against the box's median letter
    height rather than its line height, which also counts the leading:

    - only a component of that height joins it, or a smaller one (a stop, a
      hyphen) sitting within the vertical span of the lettering already taken;
    - the gap it may jump is a word space along a line, ``WORD_GAP_LETTERS``,
      but only a line space between lines, ``LINE_GAP_LETTERS``;
    - and nothing lying wholly more than ``REACH_LETTERS`` beyond the box joins
      at all. A box that cuts lettering cuts the letter at its edge; a chain
      left to run followed a dotted balloon border, or the next balloon's
      words, as far as the search region went.

    A single gap of 0.6 line heights in any direction, with no size test, took
    in the next balloon down, a scalloped edge, music notes and art: of 12
    deep crossings sampled on Vol. 12, at most two were real clips.

    Returns the components taken and the median letter height.
    """
    taken, letter_h = _seed_letters(stats, letters, box, line_height)
    if not taken:
        return taken, letter_h
    bx0, by0, bx1, by1 = box
    reach = REACH_LETTERS * letter_h
    gap_x, gap_y = WORD_GAP_LETTERS * letter_h, LINE_GAP_LETTERS * letter_h
    span_y0 = min(_rect(stats, t)[1] for t in taken)
    span_y1 = max(_rect(stats, t)[3] for t in taken)

    candidates = []
    for i in set(letters) - taken:
        x0, y0, x1, y1 = _rect(stats, i)
        if x1 < bx0 - reach or x0 > bx1 + reach or y1 < by0 - reach or y0 > by1 + reach:
            continue
        h = y1 - y0
        sized = MIN_CHAIN_HEIGHT * letter_h <= h <= MAX_CHAIN_HEIGHT * letter_h
        punctuation = h < MIN_CHAIN_HEIGHT * letter_h and span_y0 <= (y0 + y1) / 2 <= span_y1
        if sized or punctuation:
            candidates.append(i)

    def near(a: int, b: int) -> bool:
        ax0, ay0, ax1, ay1 = _rect(stats, a)
        cx0, cy0, cx1, cy1 = _rect(stats, b)
        dx = max(cx0 - ax1, ax0 - cx1, 0)
        dy = max(cy0 - ay1, ay0 - cy1, 0)
        return (dy == 0 and dx <= gap_x) or (dx == 0 and dy <= gap_y)

    grew = True
    while grew:
        grew = False
        for i in list(candidates):
            if any(near(i, t) for t in taken):
                taken.add(i)
                candidates.remove(i)
                grew = True
    return taken, letter_h


def measure_lettering(gray: np.ndarray, text_box: list, n_lines: int) -> LetteringInk | None:
    """Find the lettering a box encloses, or cuts off, on the page image.

    Args:
        gray: The page image as 8-bit grayscale, in ``text_box`` coordinates.
        text_box: The group's four corner points.
        n_lines: How many lines of text the group holds.

    Returns:
        The measured lettering, or None when there is nothing measurable: a
        malformed box, no balloon fill inside it, or no lettering centred in it.

    """
    if text_box_problem(text_box) is not None:
        return None
    x0, y0, x1, y1 = _box_bounds(text_box)
    line_height = (y1 - y0) / max(n_lines, 1)
    margin = int(max(MIN_SEARCH_MARGIN_PX, SEARCH_MARGIN_LINES * line_height))
    page_h, page_w = gray.shape
    rx0, ry0 = max(0, x0 - margin), max(0, y0 - margin)
    rx1, ry1 = min(page_w, x1 + margin), min(page_h, y1 + margin)
    if rx1 - rx0 < 2 or ry1 - ry0 < 2:  # noqa: PLR2004
        return None
    region = gray[ry0:ry1, rx0:rx1]
    ink = region < INK_GREY_MAX
    shapes = (region < SHAPE_GREY_MAX).astype(np.uint8)

    box = (x0 - rx0, y0 - ry0, x1 - rx0, y1 - ry0)
    inset = INNER_FILL_INSET_PX
    inner_box = (
        slice(max(box[1] + inset, 0), max(box[3] - inset, 1)),
        slice(max(box[0] + inset, 0), max(box[2] - inset, 1)),
    )
    light = region[inner_box][shapes[inner_box] == 0]
    if light.size == 0:
        return None
    tone = int(np.median(light))
    fill_mask = (shapes == 0) & (np.abs(region.astype(np.int16) - tone) <= FILL_TONE_TOLERANCE)
    _, fill_labels = cv2.connectedComponents(fill_mask.astype(np.uint8), connectivity=4)
    inner = fill_labels[inner_box]
    inner_fill = inner[inner > 0]
    if inner_fill.size == 0:
        return None
    fill = int(np.bincount(inner_fill).argmax())

    labels, stats, letters = _letter_components(shapes, ink, fill_labels, fill, line_height)
    taken, letter_height = _grow_from_box(stats, letters, box, line_height)
    if not taken:
        return None

    # The extent is the real ink of the shapes taken, not the shapes' rims, which
    # is the cut HOUSE_PADDING_PX was measured on.
    lettering = np.isin(labels, list(taken)) & ink
    rows, cols = np.nonzero(lettering)
    ix0, iy0 = int(cols.min()), int(rows.min())
    ix1, iy1 = int(cols.max()) + 1, int(rows.max()) + 1

    c = COVERAGE_INSET_PX
    inner_box = (slice(max(box[1] + c, 0), box[3] - c), slice(max(box[0] + c, 0), box[2] - c))
    total = int(ink[inner_box].sum())
    coverage = float(lettering[inner_box].sum() / total) if total else 0.0

    margins = (
        ink[iy0:iy1, max(box[0], 0) : max(ix0 - 1, 0)],
        ink[max(box[1], 0) : max(iy0 - 1, 0), ix0:ix1],
        ink[iy0:iy1, ix1 + 1 : box[2]],
        ink[iy1 + 1 : box[3], ix0:ix1],
    )
    empty = tuple(strip.size == 0 or not strip.any() for strip in margins)

    return LetteringInk(
        bounds=(ix0 + rx0, iy0 + ry0, ix1 + rx0, iy1 + ry0),
        letter_height=letter_height,
        coverage=coverage,
        empty_margins=(empty[0], empty[1], empty[2], empty[3]),
    )


def _free_run(gray: np.ndarray, ink: Bounds, side: int, limit: int) -> int:
    """How many ink-free pixels lie beyond the lettering's edge on *side*, up to *limit*.

    Read across the lettering's own span, so a balloon outline running close to
    the text stops the run, but ink diagonally off a corner does not.
    """
    x0, y0, x1, y1 = ink
    page_h, page_w = gray.shape
    for step in range(1, limit + 1):
        if side == 0:
            col = x0 - step
            line = gray[y0:y1, col] if col >= 0 else None
        elif side == 1:
            row = y0 - step
            line = gray[row, x0:x1] if row >= 0 else None
        elif side == 2:  # noqa: PLR2004
            col = x1 - 1 + step
            line = gray[y0:y1, col] if col < page_w else None
        else:
            row = y1 - 1 + step
            line = gray[row, x0:x1] if row < page_h else None
        if line is None or (line < INK_GREY_MAX).any():
            return step - 1
    return limit


def _padding(text_box: list, ink: Bounds) -> tuple[int, int, int, int]:
    # The far sides are read as box edge minus the ink's exclusive edge, which is
    # how HOUSE_PADDING_PX was measured off the reviewed boxes.
    x0, y0, x1, y1 = _box_bounds(text_box)
    ix0, iy0, ix1, iy1 = ink
    return ix0 - x0, iy0 - y0, x1 - ix1, y1 - iy1


def _fixed_box(
    gray: np.ndarray, text_box: list, ink: LetteringInk, padding: tuple[int, int, int, int]
) -> tuple[list[list[int]] | None, str]:
    """Pad each crossed side out to the house padding; (box, "") or (None, why not)."""
    if ink.coverage < MIN_INK_COVERAGE:
        return None, (
            f"not fixed: the measured lettering explains only {ink.coverage:.0%} of the ink"
            f" in the box"
        )
    if -min(padding) > MAX_FIXABLE_CLIP_PX:
        return None, "not fixed: a crossing this deep is a clip or a mis-measure"
    x0, y0, x1, y1 = _box_bounds(text_box)
    edges = [x0, y0, x1, y1]
    ix0, iy0, ix1, iy1 = ink.bounds
    # Where each edge goes, given `room` free pixels beyond the lettering: the
    # near sides need HOUSE_PADDING_PX free pixels for the house padding, the
    # far sides one more, since the edge itself sits on the last of them.
    edge_at = (
        lambda room: ix0 - room,
        lambda room: iy0 - room,
        lambda room: ix1 - 1 + room,
        lambda room: iy1 - 1 + room,
    )
    for side, pad in enumerate(padding):
        if pad >= 0:
            continue
        far = side >= 2  # noqa: PLR2004
        # With the balloon outline right against the lettering there is no room
        # for any padding, and the box goes to the ink: on a far side that is one
        # pixel past it, since the edge itself must cover the last ink column.
        # Refusing instead left the commonest tight box of all unfixed -- a
        # bottom line of lettering sitting on the outline, 44 of Vol. 12's 116.
        room = max(_free_run(gray, ink.bounds, side, HOUSE_PADDING_PX + far), int(far))
        edges[side] = edge_at[side](room)
    nx0, ny0, nx1, ny1 = edges
    return [[nx0, ny0], [nx1, ny0], [nx1, ny1], [nx0, ny1]], ""


def _judged_lettering(
    gray: np.ndarray, group: dict, page_line_height: float | None
) -> LetteringInk | None:
    """Measure the group's lettering, or return None when the group is not judged."""
    from barks_fantagraphics.speech_markup import strip_markup  # noqa: PLC0415

    text = strip_markup(group.get("ai_text") or "").strip()
    text_box = group.get("text_box")
    if group.get("type") not in BALLOON_TYPES or not text or not isinstance(text_box, list):
        return None
    ink = measure_lettering(gray, text_box, text.count("\n") + 1)
    if ink is None:
        return None
    if page_line_height and ink.letter_height > DISPLAY_LETTER_RATIO * page_line_height:
        return None
    return ink


def judge_padding(
    gray: np.ndarray, group: dict, page_line_height: float | None = None
) -> PaddingVerdict | None:
    """Judge one group's ``text_box`` against its lettering's ink.

    Args:
        gray: The page image as 8-bit grayscale, in ``text_box`` coordinates.
        group: The stored group.
        page_line_height: The page's reference line height, as ``ocr_check``
            computes it. When given, display lettering is not judged.

    Returns:
        The verdict, or None when the group is not judged: not a balloon type,
        no text, display lettering, or nothing measurable.

    """
    ink = _judged_lettering(gray, group, page_line_height)
    if ink is None:
        return None

    text_box = group["text_box"]
    padding = _padding(text_box, ink.bounds)
    shown = ", ".join(f"{name} {pad}" for name, pad in zip(SIDES, padding, strict=True))
    if min(padding) <= -MIN_CLIP_PX:
        fixed, why = _fixed_box(gray, text_box, ink, padding)
        note = f"padding px {shown}" + (f"; {why}" if why else "")
        deep = -min(padding) > MAX_FIXABLE_CLIP_PX
        return PaddingVerdict(
            TOO_TIGHT_DEEP_ISSUE if deep else TOO_TIGHT_ISSUE, padding, fixed, note
        )
    loose = [
        SIDES[side]
        for side, pad in enumerate(padding)
        if pad > LOOSE_PADDING_PX and ink.empty_margins[side]
    ]
    if loose:
        note = f"padding px {shown}; blank fill on the {', '.join(loose)}"
        return PaddingVerdict(TOO_LOOSE_ISSUE, padding, None, note)
    return PaddingVerdict(None, padding, None, f"padding px {shown}")

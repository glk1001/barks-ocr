# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the per-word measurements is the whole point.
"""Stroke-width emphasis check over every group of a title, in one process.

    export VISION_OUT_DIR=~/barks-vision/<slug>
    uv run --offline python scripts/vision/allbold.py [--narration-only] [PAGE ...]

Barks sets emphasis in a heavier weight of the same face, so a bold word has a
visibly larger mean stroke width than its neighbours on the same line. The
distance transform of the black mask gives that directly: twice the mean
interior distance is the stroke width. This reports **every** word's ratio
against the group's own baseline, with its x-range and the stored line beside
it, and marks each line `=` or `!` for whether the blob count matches the word
count.

Treat it as a SCREEN, not a verdict. Confirm anything under about 1.3x with a
crop, and ignore a hit on the first word of a caption -- that is the drop
capital. **Read the x-ranges**: a hit whose range sits on the edge of the text
box is the balloon outline, not lettering, and the ratio alone cannot show that.
A `!` line means the split disagreed with the text, so the word-to-ratio pairing
on that line is a guess.

MERGED FROM `allbold.py` AND `bold2.py`, which had diverged in
`~/barks-vision/vision-tools/` and both claimed to be `allbold.py` in their
docstrings. Taken from each:

  * From `bold2`: printing every word's ratio and x-range rather than only the
    hits, and saying `NO-PANEL` / `TOO-LITTLE-INK` out loud. The older
    `allbold` skipped those groups **silently**, so a group that was never
    measured looked exactly like a group with no emphasis.
  * From `allbold`: `--narration-only`, which `bold2` had dropped.
  * Fixed here: `bold2` discovered pages by globbing `1*`, so on a title whose
    pages do not start with 1 -- `069`, say -- a run with no page arguments
    silently measured nothing. Pages are now any directory holding a
    `groups.json`.

Two things that took a while to get right, both worth leaving alone:

  * Ink is restricted to pixels near "paper", or a dark background inside the
    text box gets measured as lettering.
  * Paper means the cream balloon fill AND the yellow caption boxes. Without the
    yellow, every narration group returns "no ink in box" and a whole title's
    captions are silently skipped.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

NARRATION_TYPES = ("narration", "title")

INK_MAX = 110  # a pixel is lettering below this, on the brightest channel
PAPER_MIN = 190  # cream balloon fill: every channel above this...
PAPER_MAX_SPREAD = 40  # ...and near-neutral
YELLOW_R, YELLOW_G, YELLOW_B = 200, 180, 170  # the caption boxes
PAPER_REACH = 7  # how far from paper ink still counts as lettering

MIN_BOX_INK = 60  # below this the box holds no lettering at all
MIN_LINE_INK = 120
MIN_WORD_INK = 40
SOLID_INK = 260  # a word this solid is real lettering, not an outline sliver
MIN_SOLID_WORDS = 3  # fewer than this and there is no baseline worth having

LINE_THRESHOLD = 0.06  # row is part of a line above this fraction of the peak
MIN_LINE_ROWS = 6
MIN_WORD_COLS = 3
DEFAULT_GAP = 9  # column gap that separates two words

# (x0, x1, stroke width, ink pixels)
Word = tuple[int, int, float, int]
# (line number, y0, y1, median stroke, words)
Line = tuple[int, int, int, float, list[Word]]


def ink_mask(path: str) -> np.ndarray:
    """Return the lettering mask for one panel: dark pixels that sit near paper.

    Args:
        path: a `panel-NN.png` from a prepped vision out-dir.

    Returns:
        A boolean H x W array, True where the pixel is lettering.

    """
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.int32)
    top, bottom = im.max(2), im.min(2)
    ink = top < INK_MAX
    cream = (bottom > PAPER_MIN) & ((top - bottom) < PAPER_MAX_SPREAD)
    yellow = (im[..., 0] > YELLOW_R) & (im[..., 1] > YELLOW_G) & (im[..., 2] < YELLOW_B)
    paper = cream | yellow
    return ink & ndimage.binary_dilation(paper, np.ones((3, 3), bool), iterations=PAPER_REACH)


def _split_lines(ink: np.ndarray) -> list[tuple[int, int]]:
    """Return (y0, y1) for each row band carrying lettering."""
    rows = ink.sum(1)
    threshold = max(2, rows.max() * LINE_THRESHOLD)
    lines: list[tuple[int, int]] = []
    start: int | None = None
    for i, value in enumerate(rows):
        if value > threshold and start is None:
            start = i
        elif value <= threshold and start is not None:
            if i - start >= MIN_LINE_ROWS:
                lines.append((start, i))
            start = None
    if start is not None and len(rows) - start >= MIN_LINE_ROWS:
        lines.append((start, len(rows)))
    return lines


def _split_words(band: np.ndarray, gap: int) -> list[list[int]]:
    """Return [x0, x1] for each word in one line band, merging sub-gap splits."""
    cols = band.sum(0)
    runs: list[list[int]] = []
    start: int | None = None
    for i, value in enumerate(cols):
        if value > 0 and start is None:
            start = i
        elif value == 0 and start is not None:
            if i - start >= MIN_WORD_COLS:
                runs.append([start, i])
            start = None
    if start is not None:
        runs.append([start, len(cols)])

    merged: list[list[int]] = []
    for run in runs:
        if merged and run[0] - merged[-1][1] < gap:
            merged[-1][1] = run[1]
        else:
            merged.append(list(run))
    return merged


def measure(  # noqa: PLR0913 -- a box is four coordinates, and they travel together.
    ink_full: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    gap: int = DEFAULT_GAP,
) -> list[Line]:
    """Measure the stroke width of every word inside one text box.

    Args:
        ink_full: the panel's lettering mask.
        x0: left edge of the text box, in panel coordinates.
        y0: top edge.
        x1: right edge.
        y1: bottom edge.
        gap: column gap that separates two words.

    Returns:
        One entry per line of lettering found, each carrying its words.

    """
    ink = ink_full[max(0, y0) : y1, max(0, x0) : x1]
    if ink.sum() < MIN_BOX_INK:
        return []

    out: list[Line] = []
    for number, (row_a, row_b) in enumerate(_split_lines(ink), start=1):
        band = ink[row_a:row_b]
        if band.sum() < MIN_LINE_INK:
            continue
        words: list[Word] = []
        for word_a, word_b in _split_words(band, gap):
            sub = band[:, word_a:word_b]
            if sub.sum() < MIN_WORD_INK:
                continue
            # asarray because distance_transform_edt is typed as returning an
            # array, a tuple or None depending on flags neither checker narrows.
            distance = np.asarray(ndimage.distance_transform_edt(np.pad(sub, 1)))
            stroke = 2 * distance[distance > 0].mean()
            words.append((word_a + x0, word_b + x0, float(stroke), int(sub.sum())))
        if words:
            out.append(
                (number, row_a + y0, row_b + y0, float(np.median([w[2] for w in words])), words)
            )
    return out


def _pages(out_dir: Path, wanted: list[str]) -> list[str]:
    """Return the page names to measure, in order.

    Args:
        out_dir: the prepped vision out-dir.
        wanted: page names given on the command line; empty means every page.

    Returns:
        Page directory names, sorted.

    """
    if wanted:
        return wanted
    # Any directory holding a groups.json. Globbing "1*" -- what bold2 did --
    # silently matched nothing on a title whose pages start with 0.
    return sorted(p.parent.name for p in out_dir.glob("*/groups.json"))


def main() -> None:
    """Measure emphasis across a title and print every word's ratio."""
    out_dir = Path(os.environ["VISION_OUT_DIR"]).expanduser()
    narration_only = "--narration-only" in sys.argv
    wanted = [a for a in sys.argv[1:] if not a.startswith("-")]

    boxes_files = sorted(out_dir.glob("boxes-*.json"))
    if not boxes_files:
        print(f"allbold: no boxes-*.json in {out_dir} -- run dump_boxes.py first")
        raise SystemExit(2)
    boxes = json.loads(boxes_files[0].read_text())
    pad = boxes["pad"]

    for page in _pages(out_dir, wanted):
        groups = json.loads((out_dir / page / "groups.json").read_text())
        ink_cache: dict[str, np.ndarray] = {}

        for gid, group in sorted(groups.items(), key=lambda kv: int(kv[0])):
            if narration_only and group.get("type") not in NARRATION_TYPES:
                continue

            panel_num = str(group["panel_num"])
            origin = boxes["pages"][page].get(panel_num)
            panel = out_dir / page / f"panel-{int(panel_num):02d}.png"
            usable = origin and panel_num.isdigit() and int(panel_num) > 0 and panel.exists()
            if not usable:
                # Say so. The version this replaces skipped silently, and an
                # unmeasured group then looked like a group with no emphasis.
                print(f"--- {page} g{gid} p{panel_num} NO-PANEL {json.dumps(group['ai_text'])}")
                continue

            key = str(panel)
            if key not in ink_cache:
                ink_cache = {key: ink_mask(key)}  # one panel at a time, as before

            box = group["text_box"]
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            off_x, off_y = origin["x0"] - pad, origin["y0"] - pad
            lines = measure(
                ink_cache[key],
                min(xs) - off_x,
                min(ys) - off_y,
                max(xs) - off_x,
                max(ys) - off_y,
            )

            solid = [w for *_, words in lines for w in words if w[3] >= SOLID_INK]
            if len(solid) < MIN_SOLID_WORDS:
                print(
                    f"--- {page} g{gid} p{panel_num} TOO-LITTLE-INK {json.dumps(group['ai_text'])}"
                )
                continue

            base = float(np.median([w[2] for w in solid]))
            text_lines = group["ai_text"].split("\n")
            print(f"--- {page} g{gid} p{panel_num} base={base:.2f}")
            for number, _y0, _y1, _median, words in lines:
                real = [w for w in words if w[3] >= SOLID_INK]
                stored = (
                    text_lines[number - 1].split()
                    if number - 1 < len(text_lines)
                    else ["<no-line>"]
                )
                ratios = " ".join(f"{w[2] / base:.2f}@{w[0]}-{w[1]}" for w in real)
                mark = "=" if len(real) == len(stored) else "!"
                print(f"   L{number}{mark} [{ratios}]  {' '.join(stored)}")


if __name__ == "__main__":
    main()

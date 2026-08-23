# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# what it found is the whole point of running it.
"""Find yellow caption boxes that no OCR group covers.

    python3 scripts/vision/caption_sweep.py <out-dir> <boxes.json> <prelim-dir> <lo> <hi>

Why this exists: `audit_missed_text.py` diffs a page's `visible_text` against
the groups, so a SECOND copy of a string the pass already recorded once is
invisible to it. Adventure Down Under 117 carries two `LATER!` captions, on
panels 4 and 8; the pass transcribed one, and the audit reported nothing.

A caption box is a yellow fill inside a black rectangular border with black
lettering in it -- not just any yellow. Sand, a sunflower bedspread,
firelight and a yellow shirt all read as yellow, and a plain colour
test returns dozens of them per title. Four things separate a real caption:

  * BOTH caption yellows. Vol. 5 uses a saturated #f8e600 and a pale
    #f8ea89, and matching only the saturated one misses about a third.
  * A PANEL CORNER. Barks puts captions at the top left, and requiring the
    blob to start near the panel origin removes essentially every false
    positive. This is the strongest single signal.
  * A dark border on most sides, and a blob that fills its own bounding box.
  * A plausible amount of black ink inside it -- the lettering.

Run it alongside the missed-text audit, not instead of it: the audit catches
non-caption lettering this cannot see, and this catches duplicate captions
the audit cannot.

The boxes file comes from `dump_boxes.py`; the prelim directory is the one
holding `<page>-easyocr-gemini-prelim-groups.json`.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

# A caption's yellow, covering both the saturated and the pale printing.
YELLOW_MIN_R = 200
YELLOW_MIN_G = 185
YELLOW_MAX_B = 165
YELLOW_MIN_R_MINUS_B = 90
YELLOW_MIN_G_MINUS_B = 70

DARK_MAX = 90  # a border stroke and the lettering are both this dark.

MIN_AREA = 1000  # px of yellow; below this it is a highlight, not a box.
MIN_SIDE = 18  # px; a caption is never thinner than this.
MIN_FILL = 0.45  # blob area / bbox area -- a box is rectangular.
MIN_DARK_SIDES = 3  # of 4, sampled just outside the bbox.
BORDER_PROBE = 4  # px sampled outside each edge.
BORDER_DARK_FRACTION = 0.55  # of that band, to count the side as bordered.
MIN_INK = 0.09  # black inside the bbox: the lettering.
MAX_INK = 0.60
CORNER = 60  # px; the box must start this close to the panel origin.
COVERED = 0.25  # bbox fraction under a group before it counts as covered.


def covered_fraction(box: tuple[int, int, int, int], group: tuple[int, int, int, int]) -> float:
    """Return how much of `box` lies inside `group`, both in full-page coords."""
    x0 = max(box[0], group[0])
    y0 = max(box[1], group[1])
    x1 = min(box[2], group[2])
    y1 = min(box[3], group[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    area = (box[2] - box[0]) * (box[3] - box[1])
    return (x1 - x0) * (y1 - y0) / max(area, 1)


def group_boxes(prelim: str, page: str) -> list[tuple[int, int, int, int]]:
    """Every group's text_box on a page, as full-page (x0, y0, x1, y1)."""
    groups_file = Path(prelim) / f"{page}-easyocr-gemini-prelim-groups.json"
    with groups_file.open(encoding="utf-8") as handle:
        groups = json.load(handle)["groups"]
    boxes = []
    for group in groups.values():
        xs = [point[0] for point in group["text_box"]]
        ys = [point[1] for point in group["text_box"]]
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
    return boxes


def masks(panel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Build the caption-yellow and the dark-ink masks for one panel image."""
    red, green, blue = panel[..., 0], panel[..., 1], panel[..., 2]
    yellow = (
        (red > YELLOW_MIN_R)
        & (green > YELLOW_MIN_G)
        & (blue < YELLOW_MAX_B)
        & ((red - blue) > YELLOW_MIN_R_MINUS_B)
        & ((green - blue) > YELLOW_MIN_G_MINUS_B)
    )
    dark = (red < DARK_MAX) & (green < DARK_MAX) & (blue < DARK_MAX)
    return yellow, dark


def bordered_sides(dark: np.ndarray, ys: slice, xs: slice) -> int:
    """How many of the four sides just outside the bbox are a dark stroke."""
    height, width = dark.shape
    bands = [
        (max(0, ys.start - BORDER_PROBE), ys.start, xs.start, xs.stop),
        (ys.stop, min(height, ys.stop + BORDER_PROBE), xs.start, xs.stop),
        (ys.start, ys.stop, max(0, xs.start - BORDER_PROBE), xs.start),
        (ys.start, ys.stop, xs.stop, min(width, xs.stop + BORDER_PROBE)),
    ]
    return sum(
        1
        for y0, y1, x0, x1 in bands
        if dark[y0:y1, x0:x1].size and dark[y0:y1, x0:x1].mean() > BORDER_DARK_FRACTION
    )


def sweep_panel(
    path: Path, origin: tuple[int, int], boxes: list[tuple[int, int, int, int]]
) -> list[tuple[str, bool]]:
    """Report every caption-shaped yellow block in one panel, and whether a group covers it."""
    with Image.open(path) as image:
        panel = np.asarray(image.convert("RGB")).astype(int)
    yellow, dark = masks(panel)
    labels, _ = ndimage.label(yellow)
    found = []
    for index, slices in enumerate(ndimage.find_objects(labels), start=1):
        area = int((labels[slices] == index).sum())
        if area < MIN_AREA:
            continue
        ys, xs = slices
        width, height = xs.stop - xs.start, ys.stop - ys.start
        if min(width, height) < MIN_SIDE:
            continue
        if xs.start > CORNER or ys.start > CORNER:
            continue
        fill = area / (width * height)
        if fill < MIN_FILL:
            continue
        sides = bordered_sides(dark, ys, xs)
        if sides < MIN_DARK_SIDES:
            continue
        ink = dark[ys.start : ys.stop, xs.start : xs.stop].mean()
        if not MIN_INK < ink < MAX_INK:
            continue
        box = (xs.start + origin[0], ys.start + origin[1], xs.stop + origin[0], ys.stop + origin[1])
        best = max((covered_fraction(box, group) for group in boxes), default=0.0)
        described = (
            f"{width}x{height} fill={fill:.2f} border={sides}/4 ink={ink:.2f} "
            f"panel({xs.start},{ys.start}) overlap={best:.0%}"
        )
        found.append((described, best >= COVERED))
    return found


def main() -> int:
    """Sweep a page range and print every caption box, flagging the uncovered ones."""
    expected_args = 6
    if len(sys.argv) != expected_args:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    outdir, boxfile, prelim, lo, hi = (
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        int(sys.argv[4]),
        int(sys.argv[5]),
    )
    with Path(boxfile).open(encoding="utf-8") as handle:
        boxes_json = json.load(handle)
    pad = boxes_json["pad"]

    uncovered = 0
    for number in range(lo, hi + 1):
        page = f"{number:03d}"
        boxes = group_boxes(prelim, page)
        for panel_path in sorted(Path(outdir).joinpath(page).glob("panel-*.png")):
            panel_num = str(int(panel_path.name[6:8]))
            panel_box = boxes_json["pages"][page].get(panel_num)
            if panel_box is None:
                continue
            origin = (panel_box["x0"] - pad, panel_box["y0"] - pad)
            for line, is_covered in sweep_panel(panel_path, origin, boxes):
                flag = "" if is_covered else "   <-- NO GROUP"
                if not is_covered:
                    uncovered += 1
                print(f"  {page} p{panel_num:>2s} caption {line}{flag}")
    print(f"{uncovered} caption box(es) with no group")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the census is the whole point.
"""Connected-component ink census for nephew caps and costume colour.

    uv run --offline python scripts/vision/capscan.py <panel.png> [MIN_AREA] [MAX_AREA]

WHY THIS EXISTS. Colour is a file to sample, not an image to look at. A `Counter`
over a panel's ink answers "which ink is this cap" for a few hundred tokens
instead of a whole panel image, and answers it *better* than the eye: it is what
caught two caps printing an identical `#0a9e9c`, and the teal bands at H179 that
read as green. Load a panel for **tails and figures**; sample the file for
**colour**.

Reports EVERY blob in the size window, largest first and **never truncated** --
a cap can be a few dozen ink pixels, and a census that elides its tail is worse
than none. Coordinates are PANEL pixels, the same space as `text_box`.

THE BAND EDGES ARE HARD, AND CAPS LAND ON THEM. That is this script's known
failure, not a quirk: on *Lost in the Andes!* 031 panel 3 it reported
`red: 0 / green: 0 / blue: 0` for three plainly coloured caps, each missing its
band by under two degrees. Note also that `green` here is H140-182, which holds
almost nothing in these volumes -- the *cap* green lives in `leafgrn` (H95-140),
so reading "green: 0" as "no green cap" is backwards. When a band comes back
empty and a name hangs on it, re-run `capwide.py`, which spans the edges, and
crop before naming anybody.

This is a screen, not a verdict. A blob still has to sit on a HEAD to be a cap.
"""

import sys

import numpy as np
from PIL import Image
from scipy import ndimage

# Kept exactly as the bands have always been: capwide.py exists to widen them,
# and it is only a useful second opinion while these stay put.
RED_LO, RED_HI = 340.0, 12.0  # wraps through 0
GREEN_LO, GREEN_HI = 140.0, 182.0
BLUE_LO, BLUE_HI = 183.0, 235.0
LEAFGRN_LO, LEAFGRN_HI = 95.0, 140.0
YELLOW_LO, YELLOW_HI = 40.0, 65.0

MIN_SAT = 0.40
MIN_VAL = 0.25

EPSILON = 1e-9  # a pixel is chromatic only above this delta

ARG_MIN_AREA = 2  # sys.argv index of the optional MIN_AREA
ARG_MAX_AREA = 3  # sys.argv index of the optional MAX_AREA

DEFAULT_MIN_AREA = 25
DEFAULT_MAX_AREA = 10**9

# (area, centre x, centre y, x0, y0, x1, y1, hue, saturation, value, hex)
Blob = tuple[int, int, int, int, int, int, int, float, float, float, str]


def _hsv(im: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (hue in degrees, saturation, value) for an RGB image scaled to 0..1.

    Args:
        im: an H x W x 3 array of floats in 0..1.

    Returns:
        Three H x W arrays: hue in 0..360, saturation and value in 0..1.

    """
    red, green, blue = im[..., 0], im[..., 1], im[..., 2]
    top, bottom = im.max(2), im.min(2)
    delta = top - bottom
    sat = np.where(top > 0, delta / np.where(top == 0, 1, top), 0.0)
    hue = np.zeros_like(top)
    lit = delta > EPSILON
    at_red = lit & (top == red)
    at_green = lit & (top == green) & (top != red)
    at_blue = lit & (top == blue) & (top != red) & (top != green)
    hue[at_red] = ((green - blue)[at_red] / delta[at_red]) % 6
    hue[at_green] = ((blue - red)[at_green] / delta[at_green]) + 2
    hue[at_blue] = ((red - green)[at_blue] / delta[at_blue]) + 4
    return hue * 60.0, sat, top


def _bands(hue: np.ndarray) -> dict[str, np.ndarray]:
    """Return one boolean mask per roster ink band, keyed by band name.

    `leafgrn` stops one step short of `green`'s lower edge rather than meeting
    it, so a pixel at exactly H140 lands in one census and not both.

    Args:
        hue: an H x W array of hues in degrees.

    Returns:
        Five H x W boolean masks, keyed by band name.

    """
    return {
        "red": (hue >= RED_LO) | (hue <= RED_HI),
        "green": (hue >= GREEN_LO) & (hue <= GREEN_HI),
        "blue": (hue >= BLUE_LO) & (hue <= BLUE_HI),
        "leafgrn": (hue >= LEAFGRN_LO) & (hue < LEAFGRN_HI),
        "yellow": (hue >= YELLOW_LO) & (hue <= YELLOW_HI),
    }


def scan(
    path: str,
    min_area: int = DEFAULT_MIN_AREA,
    max_area: int = DEFAULT_MAX_AREA,
) -> dict[str, tuple[int, list[Blob]]]:
    """Census every coloured blob in one panel, per band, largest first.

    Args:
        path: a `panel-NN.png` from a prepped vision out-dir.
        min_area: drop blobs smaller than this, in pixels.
        max_area: drop blobs larger than this, in pixels.

    Returns:
        One entry per band, mapping the band name to (blobs found before the
        size window was applied, the blobs inside it). The first number matters:
        "0 in window" and "0 at all" call for different next moves.

    """
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255.0
    hue, sat, val = _hsv(im)
    lit = (sat > MIN_SAT) & (val > MIN_VAL)

    out: dict[str, tuple[int, list[Blob]]] = {}
    for name, in_band in _bands(hue).items():
        labels, count = ndimage.label(in_band & lit)
        rows: list[Blob] = []
        for i, extent in enumerate(ndimage.find_objects(labels), start=1):
            blob = labels[extent] == i
            area = int(blob.sum())
            if area < min_area or area > max_area:
                continue
            ys, xs = extent
            # Median over the blob, not the value at one pixel: a cap is shaded,
            # and its centre pixel is as likely to be a highlight as the ink.
            hue_m = float(np.median(hue[extent][blob]))
            sat_m = float(np.median(sat[extent][blob]))
            val_m = float(np.median(val[extent][blob]))
            rgb = (np.median(im[extent][blob] * 255, axis=0)).astype(int)
            rows.append(
                (
                    area,
                    int((xs.start + xs.stop) / 2),
                    int((ys.start + ys.stop) / 2),
                    int(xs.start),
                    int(ys.start),
                    int(xs.stop),
                    int(ys.stop),
                    hue_m,
                    sat_m,
                    val_m,
                    f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
                )
            )
        out[name] = (count, sorted(rows, key=lambda row: -row[0]))
    return out


def main() -> None:
    """Print the full ink census for the panel named on the command line."""
    path = sys.argv[1]
    min_area = int(sys.argv[ARG_MIN_AREA]) if len(sys.argv) > ARG_MIN_AREA else DEFAULT_MIN_AREA
    max_area = int(sys.argv[ARG_MAX_AREA]) if len(sys.argv) > ARG_MAX_AREA else DEFAULT_MAX_AREA

    with Image.open(path) as probe:
        size = probe.size
    print(f"== {path}  size={size}  window={min_area}-{max_area}px")

    for name, (count, rows) in scan(path, min_area, max_area).items():
        if count == 0:
            print(f"-- {name}: 0 blob(s) total")
            continue
        print(f"-- {name}: {count} blob(s) total, {len(rows)} in window")
        for area, c_x, c_y, x0, y0, x1, y1, hue, sat, val, hex_at in rows:
            print(
                f"   area={area:5d} c=({c_x},{c_y}) box=({x0},{y0},{x1},{y1}) "
                f"H={hue:6.1f} S={sat:.2f} V={val:.2f} {hex_at}"
            )


if __name__ == "__main__":
    main()

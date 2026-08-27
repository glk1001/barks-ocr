# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the census is the whole point.
"""`capscan.py` with the hue band edges widened, because caps land on them.

    uv run --offline python scripts/vision/capwide.py <panel.png> [MIN_AREA]

WHY THIS EXISTS. `capscan.py`'s bands have hard edges, and the Vol. 6/7 cap inks
sit right on them once the art shades. On *Lost in the Andes!* 031 panel 3
capscan reported `red: 0 / green: 0 / blue: 0`, the pass wrote "NO red, NO green
and NO blue ink at any size" into three notes and called all three boys
`nephews` -- and a 1.7x crop shows three plainly coloured caps, which the review
then named. Measured:

| boy | ink | hue | why capscan missed it |
|---|---|---|---|
| left | `#1fa3a8` | 182.2 | the 1-degree crack between `green` (<=182) and `blue` (>=183) |
| middle | `#81331c` | 13.7 | 1.7 degrees outside `red` (<=12) |
| right | `#65a44c` | 103.0 | reported, but under `leafgrn` |

Note also that capscan's band named `green` is H140-182, which holds almost
nothing in these volumes: the *cap* green lives in `leafgrn` (H95-140). Reading
its "green: 0" as "no green cap" is backwards. The green band here spans what
capscan splits between the two, so one number answers "is there a green cap".

This is a screen, not a verdict. A blob still has to sit on a HEAD to be a cap,
and on a title whose inks shade this far, crop the row at 1.5-2x before naming
anybody.
"""

import sys

import numpy as np
from PIL import Image
from scipy import ndimage

# Widened against capscan's red H>=340|<=12, green H140-182, blue H183-235.
RED_LO, RED_HI = 335.0, 18.0
GREEN_LO, GREEN_HI = 90.0, 176.0
BLUE_LO, BLUE_HI = 176.0, 240.0

# Same floors as capscan, so the only difference is the hue edges.
MIN_SAT = 0.40
MIN_VAL = 0.25

EPSILON = 1e-9  # a pixel is chromatic only above this delta
ARG_MIN_AREA = 2  # sys.argv index of the optional MIN_AREA

DEFAULT_MIN_AREA = 40
MAX_ROWS_SHOWN = 8

Blob = tuple[int, int, int, int, int, str, float, float]


def _hue(im: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (hue in degrees, saturation, value) for an RGB image in 0..1."""
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


def scan(path: str, min_area: int = DEFAULT_MIN_AREA) -> dict[str, list[Blob]]:
    """Census the roster-coloured blobs in one panel, largest first.

    Args:
        path: a `panel-NN.png` from a prepped vision out-dir.
        min_area: drop blobs smaller than this, in pixels.

    Returns:
        One list per band, each blob as
        (area, x0, x1, y0, y1, hex, hue, saturation).

    """
    im = np.array(Image.open(path).convert("RGB")).astype(np.float64) / 255.0
    red, green, blue = im[..., 0], im[..., 1], im[..., 2]
    hue, sat, val = _hue(im)
    bands = {
        "red": (hue >= RED_LO) | (hue <= RED_HI),
        "green": (hue >= GREEN_LO) & (hue <= GREEN_HI),
        "blue": (hue >= BLUE_LO) & (hue <= BLUE_HI),
    }
    out: dict[str, list[Blob]] = {}
    for name, band in bands.items():
        labels, count = ndimage.label(band & (sat > MIN_SAT) & (val > MIN_VAL))
        rows: list[Blob] = []
        for i in range(1, count + 1):
            ys, xs = np.where(labels == i)
            if len(ys) < min_area:
                continue
            y_c, x_c = int(ys.mean()), int(xs.mean())
            hex_at = (
                f"#{int(red[y_c, x_c] * 255):02x}"
                f"{int(green[y_c, x_c] * 255):02x}"
                f"{int(blue[y_c, x_c] * 255):02x}"
            )
            rows.append(
                (
                    len(ys),
                    int(xs.min()),
                    int(xs.max()),
                    int(ys.min()),
                    int(ys.max()),
                    hex_at,
                    round(float(hue[y_c, x_c]), 1),
                    round(float(sat[y_c, x_c]), 2),
                )
            )
        out[name] = sorted(rows, reverse=True)
    return out


def main() -> None:
    """Print the widened-band census for the panel named on the command line."""
    path = sys.argv[1]
    min_area = int(sys.argv[ARG_MIN_AREA]) if len(sys.argv) > ARG_MIN_AREA else DEFAULT_MIN_AREA
    print(f"== {path}  (widened bands, min_area={min_area})")
    for name, rows in scan(path, min_area).items():
        print(f"-- {name}: {len(rows)} blob(s)")
        for area, x0, x1, y0, y1, hex_at, hue, sat in rows[:MAX_ROWS_SHOWN]:
            print(f"     a={area:6d} x{x0}-{x1} y{y0}-{y1} {hex_at} H={hue} S={sat}")


if __name__ == "__main__":
    main()

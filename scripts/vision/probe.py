# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the histogram is the whole point.
"""Probe one region's pixel histogram, with no saturation floor to hide a shadow.

    uv run --offline python scripts/vision/probe.py <panel.png> [x0 y0 x1 y1]

WHY THIS EXISTS. `capwide.py` screens a whole panel for cap-sized blobs above a
`MIN_SAT` of 0.40, and that floor HIDES a cap that is drawn in shadow. On *Echo
System* it reported `green: 0` on a panel holding a 146px `#68a36f` cap: the ink
is a real roster green, it is simply desaturated by the shading over it, and a
census keyed to saturation cannot see it.

So this tool does the opposite thing. It takes a region you already believe is a
head, drops the saturation floor to near zero, and prints WHAT IS ACTUALLY
THERE -- every chromatic hue band by pixel count, with a representative hex and
the saturation range each band spans. A shadowed cap shows up as a band with a
few hundred pixels at S=0.2 instead of as a zero.

Read it by RANKING THE HEADS IN ONE PANEL AGAINST EACH OTHER, never against an
absolute threshold. The printing shifts per title, per page and per panel; what
survives is that the three caps in a panel differ from one another. Probe each
head, then ask which band dominates each -- not whether any band clears a bar.

Never write "no cap ink" off a capwide zero. Probe the head first.
"""

import sys

import numpy as np
from PIL import Image

# Hue bands, matching capwide.py so the two tools agree about what a colour is.
BANDS: list[tuple[str, float, float]] = [
    ("red", 335.0, 18.0),  # wraps through 0
    ("orange", 18.0, 45.0),
    ("yellow", 45.0, 70.0),
    ("green", 90.0, 176.0),
    ("blue", 176.0, 240.0),
    ("purple", 240.0, 300.0),
    ("pink", 300.0, 335.0),
]
BAND_YELLOW_GREEN = ("yellow-green", 70.0, 90.0)

MIN_SAT = 0.06  # near zero on purpose: the point is to see the shadowed ink
MIN_VAL = 0.10  # below this it is black line-work, not a colour

EPSILON = 1e-9
ARG_BOX_START = 2
ARG_BOX_LEN = 4
TOP_BANDS_SHOWN = 6


def _hsv(im: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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


def _in_band(hue: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Mask the hues inside [lo, hi), wrapping through 0 when lo > hi."""
    if lo > hi:
        return (hue >= lo) | (hue < hi)
    return (hue >= lo) & (hue < hi)


def probe(path: str, box: tuple[int, int, int, int] | None = None) -> None:
    """Print the chromatic histogram of one region of a panel.

    Args:
        path: a `panel-NN.png` from a prepped vision out-dir.
        box: `(x0, y0, x1, y1)` in panel coordinates, or None for the whole panel.

    """
    img = Image.open(path).convert("RGB")
    if box is not None:
        img = img.crop(box)
    arr = np.asarray(img).astype(np.float64) / 255.0
    hue, sat, val = _hsv(arr)

    total = arr.shape[0] * arr.shape[1]
    chromatic = (sat >= MIN_SAT) & (val >= MIN_VAL)
    where = f"{box}" if box else "whole panel"
    print(f"{path}  {where}  {arr.shape[1]}x{arr.shape[0]} = {total}px")
    print(f"  chromatic (S>={MIN_SAT}, V>={MIN_VAL}): {int(chromatic.sum())}px")

    rows = []
    for name, lo, hi in [*BANDS, BAND_YELLOW_GREEN]:
        mask = chromatic & _in_band(hue, lo, hi)
        count = int(mask.sum())
        if not count:
            continue
        med_rgb = np.median(arr[mask], axis=0) * 255.0
        hexcode = "#{:02x}{:02x}{:02x}".format(*(round(c) for c in med_rgb))
        rows.append(
            (
                count,
                name,
                hexcode,
                float(np.median(hue[mask])),
                float(sat[mask].min()),
                float(np.median(sat[mask])),
                float(sat[mask].max()),
            )
        )

    rows.sort(reverse=True)
    print(f"  {'band':<13}{'px':>7}  {'hex':<9}{'H':>7}  {'S min/med/max':>20}")
    for count, name, hexcode, med_hue, s_lo, s_med, s_hi in rows[:TOP_BANDS_SHOWN]:
        pct = 100.0 * count / total
        print(
            f"  {name:<13}{count:>7}  {hexcode:<9}{med_hue:>7.1f}"
            f"  {s_lo:>5.2f}/{s_med:.2f}/{s_hi:.2f}  ({pct:.1f}% of region)"
        )
    if not rows:
        print("  no chromatic pixels at all")


def main() -> None:
    """Read the panel path and optional box off the command line and probe it."""
    if len(sys.argv) < ARG_BOX_START:
        print(__doc__)
        raise SystemExit(2)
    box = None
    if len(sys.argv) >= ARG_BOX_START + ARG_BOX_LEN:
        vals = [int(v) for v in sys.argv[ARG_BOX_START : ARG_BOX_START + ARG_BOX_LEN]]
        box = (vals[0], vals[1], vals[2], vals[3])
    probe(sys.argv[1], box)


if __name__ == "__main__":
    main()

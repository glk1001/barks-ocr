# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the head census is the whole point.
"""Locate duck HEADS in a panel from their beaks, and any cap ink sitting on one.

    uv run --offline python scripts/vision/heads.py <panel.png> [MIN_BEAK] [MIN_CAP]

A Barks beak is a saturated orange blob; the head is the near-white region it
touches. Reports each beak, the white head blob attached to it, and any
saturated red/green/blue ink on that head -- a cap -- with its hex, for a few
hundred tokens instead of a panel image.

THIS IS THE FORMER `heads2.py`. There were two of these in
`~/barks-vision/vision-tools/` carrying the *same* docstring, and the older one
was the one the README documented while the finding *"a heads2 zero is not a
bare head"* was about this one. The older version is retired; it differed in
three ways, all of which made it miss caps:

  * **No crown strip.** The white skull region stops at the cap line, so a
    figure in a dark cap runs up to a head-height above the white box and the
    crown fell outside the search. This version searches that strip.
  * **A 250px cap floor**, against 120 here, and settable. A cap in shadow or at
    distance is a few dozen pixels.
  * **Centroid below head-mid meant scenery.** A tall cap whose centroid sits
    low was dropped; the test here is where the ink *starts*.

A census of zero still is not proof of a bare head -- it is a reason to crop.
Ink has to sit on a HEAD to be a cap, and height in frame is not depth order.
"""

import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ARG_MIN_BEAK = 2  # sys.argv index of the optional MIN_BEAK
ARG_MIN_CAP = 3  # sys.argv index of the optional MIN_CAP

DEFAULT_MIN_BEAK = 300
DEFAULT_MIN_CAP = 120

# The beak: saturated orange, and bright.
BEAK_HUE_LO, BEAK_HUE_HI = 20.0, 48.0
BEAK_MIN_SAT = 0.55
BEAK_MIN_VAL = 0.60

# The skull: near-white means every channel high and the spread between them low.
WHITE_MIN_CHANNEL = 0.72
WHITE_MAX_SPREAD = 0.16

# Cap ink. Wider bands than capscan.py, because a cap on a head is already
# located -- the risk here is missing one, not a false positive in scenery.
CAP_RED_LO, CAP_RED_HI = 336.0, 12.0  # wraps through 0
CAP_GREEN_LO, CAP_GREEN_HI = 90.0, 182.0
CAP_BLUE_LO, CAP_BLUE_HI = 183.0, 245.0
CAP_MIN_SAT = 0.55
CAP_MIN_VAL = 0.30

EPSILON = 1e-9
WHITE_ERODE = 2  # trims the skull to a core before labelling
BEAK_REACH = 6  # dilation that finds the skull a beak touches
HEAD_REGROW = 2  # regrows the eroded core back onto the white mask
CAP_REACH = 8  # how far off the head cap ink may sit

MIN_CROWN_HEIGHT = 12  # floor on the strip searched above the skull
MIN_CROWN_PAD = 8


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


def _cap_ink(
    im: np.ndarray,
    hsv: tuple[np.ndarray, np.ndarray, np.ndarray],
    near: np.ndarray,
    head_mid: float,
    min_cap: int,
) -> list[str]:
    """Describe every roster-coloured blob sitting on one head.

    Args:
        im: the panel as floats in 0..1.
        hsv: the panel's (hue in degrees, saturation, value) planes.
        near: mask of the head plus its crown strip.
        head_mid: y of the head's middle; ink starting below it is scenery.
        min_cap: drop cap blobs smaller than this, in pixels.

    Returns:
        One formatted line per cap blob found.

    """
    hue, sat, val = hsv
    bands = {
        "red": (hue >= CAP_RED_LO) | (hue <= CAP_RED_HI),
        "green": (hue >= CAP_GREEN_LO) & (hue <= CAP_GREEN_HI),
        "blue": (hue >= CAP_BLUE_LO) & (hue <= CAP_BLUE_HI),
    }
    lit = (sat > CAP_MIN_SAT) & (val > CAP_MIN_VAL)

    caps: list[str] = []
    for name, in_band in bands.items():
        labels, _ = ndimage.label(near & in_band & lit)
        for j, extent in enumerate(ndimage.find_objects(labels), start=1):
            blob = labels[extent] == j
            area = int(blob.sum())
            if area < min_cap:
                continue
            ys, xs = extent
            # Where the ink STARTS, not its centroid: a tall cap has a low
            # centroid and was dropped by the version this replaces.
            if ys.start > head_mid:
                continue
            rgb = (np.median(im[extent][blob] * 255, axis=0)).astype(int)
            caps.append(
                f"{name}({xs.start},{ys.start},{xs.stop},{ys.stop}) a={area} "
                f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            )
    return caps


def find_heads(
    path: str,
    min_beak: int = DEFAULT_MIN_BEAK,
    min_cap: int = DEFAULT_MIN_CAP,
) -> tuple[tuple[int, int], list[str]]:
    """Report every duck head in a panel, left to right, with its cap ink.

    Args:
        path: a `panel-NN.png` from a prepped vision out-dir.
        min_beak: drop beak blobs smaller than this, in pixels.
        min_cap: drop cap blobs smaller than this, in pixels.

    Returns:
        The panel's (width, height) and one formatted line per beak found.

    """
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0
    hue, sat, val = _hsv(im)
    bottom = im.min(2)
    height, width = val.shape
    cross = np.ones((3, 3), bool)

    beak = (hue >= BEAK_HUE_LO) & (hue <= BEAK_HUE_HI) & (sat > BEAK_MIN_SAT) & (val > BEAK_MIN_VAL)
    white = (bottom > WHITE_MIN_CHANNEL) & ((val - bottom) < WHITE_MAX_SPREAD)
    white_labels, _ = ndimage.label(ndimage.binary_erosion(white, cross, iterations=WHITE_ERODE))
    beak_labels, _ = ndimage.label(beak)

    found: list[tuple[int, str]] = []
    for i, extent in enumerate(ndimage.find_objects(beak_labels), start=1):
        area = int((beak_labels[extent] == i).sum())
        if area < min_beak:
            continue
        ys, xs = extent

        # The skull this beak touches: reach out from the beak and take the
        # white label it overlaps most.
        reach = ndimage.binary_dilation(beak_labels == i, cross, iterations=BEAK_REACH)
        ids, counts = np.unique(white_labels[reach & (white_labels > 0)], return_counts=True)

        head = ""
        if len(ids):
            head_mask = (
                ndimage.binary_dilation(
                    white_labels == int(ids[counts.argmax()]), cross, iterations=HEAD_REGROW
                )
                & white
            )
            h_ys, h_xs = np.nonzero(head_mask)
            hx0, hx1, hy0, hy1 = h_xs.min(), h_xs.max(), h_ys.min(), h_ys.max()
            head = (
                f" head+beak x=({min(hx0, xs.start)}..{max(hx1, xs.stop)})"
                f" white=({hx0},{hy0},{hx1},{hy1}) area={head_mask.sum()}"
            )

            near = ndimage.binary_dilation(head_mask, cross, iterations=CAP_REACH)
            # THE WHITE BOX STOPS AT THE CAP LINE. A dark cap sits on top of the
            # skull, so the figure runs up to a head-height above the box and ink
            # in that strip is the crown, not background.
            crown = max(MIN_CROWN_HEIGHT, hy1 - hy0)
            pad = max(MIN_CROWN_PAD, (hx1 - hx0) // 4)
            crown_rows = slice(max(0, hy0 - crown), hy0 + 1)
            crown_cols = slice(max(0, hx0 - pad), min(width, hx1 + pad + 1))
            near[crown_rows, crown_cols] = True

            caps = _cap_ink(im, (hue, sat, val), near, (hy0 + hy1) / 2, min_cap)
            if caps:
                head += "  CAP-INK: " + "; ".join(caps)

        found.append(
            (xs.start, f"beak a={area:5d} box=({xs.start},{ys.start},{xs.stop},{ys.stop}){head}")
        )

    return (width, height), [line for _, line in sorted(found)]


def main() -> None:
    """Print the head census for the panel named on the command line."""
    path = sys.argv[1]
    min_beak = int(sys.argv[ARG_MIN_BEAK]) if len(sys.argv) > ARG_MIN_BEAK else DEFAULT_MIN_BEAK
    min_cap = int(sys.argv[ARG_MIN_CAP]) if len(sys.argv) > ARG_MIN_CAP else DEFAULT_MIN_CAP

    (width, height), lines = find_heads(path, min_beak, min_cap)
    print(f"== {path} {width}x{height}")
    for line in lines:
        print("  " + line)


if __name__ == "__main__":
    main()

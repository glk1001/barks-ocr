# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# where it put the crop is the whole point of running it.
"""Crop a region given in PANEL coordinates from a prepped panel-NN.png, and upscale.

    uv run --offline python scripts/vision/pcrop.py <panel.png> <x0> <y0> <x1> <y1> <scale> <dest>

WHY THIS EXISTS. `crop.py` takes coordinates in the FULL-PAGE space, which is
what `text_box` uses. But `capscan.py`, `capwide.py`, `probe.py` and `heads.py`
all report PANEL pixels, so following up a census hit meant converting by hand
every time -- and the arithmetic is exactly the silent-miss the two coordinate
spaces already cause. This is the panel-local counterpart: paste the box a
census printed straight in.

Use `crop.py` when the numbers came out of `groups.json`, and this when they
came out of a census.
"""

import sys

from PIL import Image


def main() -> None:
    """Crop and upscale one panel-local region."""
    if len(sys.argv) != 8:  # noqa: PLR2004 -- script, argv shape is the usage line
        print(__doc__)
        raise SystemExit(2)
    src, dest = sys.argv[1], sys.argv[7]
    x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6])
    scale = float(sys.argv[6])
    with Image.open(src) as opened:
        image = opened.convert("RGB")
        box = (max(0, x0), max(0, y0), min(image.width, x1), min(image.height, y1))
        crop = image.crop(box)
    crop = crop.resize(
        (int(crop.width * scale), int(crop.height * scale)), Image.Resampling.LANCZOS
    )
    crop.save(dest)
    print(f"{dest} {crop.size} from {src} {list(box)} x{scale}")


if __name__ == "__main__":
    main()

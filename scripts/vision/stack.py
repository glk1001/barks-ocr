# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# what it wrote is the whole point of running it.
"""Stack several panel-coordinate crops into one labelled image, top to bottom.

    uv run --offline python scripts/vision/stack.py \
        <dest> <scale> <panel.png>:<x0>,<y0>,<x1>,<y1> ...

WHY THIS EXISTS. `montage.py` is the per-page contact sheet and `pcrop.py` is
the single follow-up crop; between them sits the case that costs the most
images -- half a dozen cheap yes/no questions spread over different pages. Is
this balloon a cloud or does it have a pointed tail? Does this crown carry a
band? Each needs a couple of hundred pixels and none of them needs a whole
panel, but asked one at a time they are six image reads.

Stacked they are one. On the twenty-fifth batch this is most of the difference
between the 4.4 images per page the first title cost and the 1.8 the third one
did; see `docs/vision-pass-cost.md` for the ladder it belongs to.

Each crop is labelled with `<page>/<file>` so a finding can be carried back to
the panel it came from. Coordinates are PANEL pixels, the same space
`capscan.py` and `heads.py` report and `pcrop.py` takes.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

LABEL_HEIGHT = 18


def main() -> None:
    """Write the stacked contact strip named by argv[1]."""
    if len(sys.argv) < 4:  # noqa: PLR2004 -- script, argv shape is the usage line
        print(__doc__)
        raise SystemExit(2)
    dest, scale = sys.argv[1], float(sys.argv[2])
    crops: list[tuple[str, Image.Image]] = []
    for spec in sys.argv[3:]:
        path, _, box = spec.rpartition(":")
        x0, y0, x1, y1 = (int(v) for v in box.split(","))
        with Image.open(path) as opened:
            crop = opened.convert("RGB").crop((x0, y0, x1, y1))
        crop = crop.resize(
            (int(crop.width * scale), int(crop.height * scale)), Image.Resampling.LANCZOS
        )
        parts = Path(path).parts
        crops.append(("/".join(parts[-2:]), crop))

    width = max(crop.width for _, crop in crops)
    height = sum(crop.height + LABEL_HEIGHT for _, crop in crops)
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    y = 0
    for label, crop in crops:
        draw.text((3, y + 3), label, fill="black")
        y += LABEL_HEIGHT
        sheet.paste(crop, (0, y))
        y += crop.height
    sheet.save(dest)
    print(f"{dest} {sheet.size} -- {len(crops)} crop(s)")


if __name__ == "__main__":
    main()

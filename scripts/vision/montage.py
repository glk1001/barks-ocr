# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# what it wrote is the whole point.
"""Lay every panel of one page out as a single labelled contact sheet.

    uv run --offline python scripts/vision/montage.py <page-dir> out.png [CELL]

WHY THIS EXISTS. This is the default per-page view, and for most pages it is the
only one: bold, balloon shape, who is in frame, and whether anyone wears a cap at
all are all legible at 250px. One montage costs one image read where opening
each panel separately costs a dozen, which is most of the difference between a
run at 1.9 images per page and the 9.4-per-page batch that burned a session
limit. See `docs/vision-pass-cost.md` for the ladder this sits at the top of.

Each cell is outlined and labelled with its panel number, so a finding can be
carried back to `panel-NN.png` -- which is where to go for a tail, a figure, or
anything a name hangs on. The montage is for triage, not for naming anybody.

`<page-dir>` is a page directory inside a prepped vision out-dir, holding
`panel-NN.png` files at source resolution.
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ARG_CELL = 3  # sys.argv index of the optional CELL size

DEFAULT_CELL = 230  # longest edge of one cell, in pixels
MAX_COLS = 4
GAP = 8  # padding around and between cells

SHEET_RGB = (250, 250, 250)
OUTLINE_RGB = (200, 0, 0)
LABEL_RGB = (255, 0, 0)

PANEL_STEM_SLICE = slice(6, 8)  # the NN of "panel-NN.png"


def build(page_dir: Path, cell: int = DEFAULT_CELL) -> tuple[Image.Image, int]:
    """Compose every `panel-NN.png` in *page_dir* into one labelled grid.

    Args:
        page_dir: a page directory from a prepped vision out-dir.
        cell: longest edge of a single cell, in pixels.

    Returns:
        The composed sheet and the number of panels placed on it.

    """
    panels = []
    for path in sorted(page_dir.glob("panel-*.png")):
        with Image.open(path) as handle:
            im = handle.convert("RGB")
        scale = cell / max(im.size)
        resized = im.resize(
            (max(1, int(im.width * scale)), max(1, int(im.height * scale))),
            Image.Resampling.LANCZOS,
        )
        panels.append((path.name[PANEL_STEM_SLICE], resized))

    cols = min(MAX_COLS, len(panels)) or 1
    rows = math.ceil(len(panels) / cols)
    sheet = Image.new(
        "RGB",
        (cols * (cell + GAP) + GAP, rows * (cell + GAP) + GAP),
        SHEET_RGB,
    )

    draw = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(panels):
        x = GAP + (i % cols) * (cell + GAP)
        y = GAP + (i // cols) * (cell + GAP)
        sheet.paste(im, (x, y))
        draw.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=OUTLINE_RGB)
        draw.text((x + 2, y + 2), label, fill=LABEL_RGB)

    return sheet, len(panels)


def main() -> None:
    """Write the contact sheet named on the command line."""
    page_dir = Path(sys.argv[1]).expanduser()
    out = Path(sys.argv[2]).expanduser()
    cell = int(sys.argv[ARG_CELL]) if len(sys.argv) > ARG_CELL else DEFAULT_CELL

    if not page_dir.is_dir():
        print(f"montage: not a directory: {page_dir}")
        raise SystemExit(2)

    sheet, count = build(page_dir, cell)
    if count == 0:
        # A page with no panel crops is a prep that did not finish, not a
        # wordless page -- say so rather than writing an empty sheet.
        print(f"montage: no panel-NN.png in {page_dir} -- was the page prepped?")
        raise SystemExit(1)

    sheet.save(out)
    print(out, sheet.size, count, "panels")


if __name__ == "__main__":
    main()

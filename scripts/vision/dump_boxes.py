# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# saying what it wrote is the only feedback it gives.
"""Dump one title's panel boxes to a plain JSON, so crop.py needs no barks imports.

    uv run python scripts/vision/dump_boxes.py "Some Title" ~/barks-vision/<slug>/boxes-<slug>.json

Write it **into the out-dir**, named ``boxes-<out-dir-name>.json``: that is where
``crop.py`` looks for it given the out-dir, and keeping it there means a title's
scratch is self-contained and throwing the directory away costs nothing.

Lives in the repo rather than beside the scratch it writes into. It used to sit
loose in ``~/barks-vision`` while ``SKILL.md`` -- which *is* versioned -- told
readers to run it from there, so the documented procedure was broken on any
fresh clone. Found 2026-08-07 while working out what a laptop would need.

Must be run with ``uv run`` from the barks-ocr checkout so the path deps resolve.
"""

import json
import sys
from pathlib import Path

from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.panel_boxes import TitlePanelBoxes

# Imported rather than copied. The two used to be separate constants with a
# "keep in step" comment between them, which is a drift waiting to happen: the
# panel PNG's origin is (x0 - pad, y0 - pad), so a pad that disagreed with
# prep's would offset every crop by a few pixels and silently.
from barks_ocr.tools.vision_prep import CROP_PAD_PX

EXPECTED_ARGV = 3  # script, title, destination

if len(sys.argv) != EXPECTED_ARGV:
    msg = 'usage: dump_boxes.py "Some Title" <out.json>'
    raise SystemExit(msg)

title_str = sys.argv[1]
out = Path(sys.argv[2]).expanduser()

db = ComicsDatabase()
title_boxes = TitlePanelBoxes(db).get_page_panel_boxes(STR_TITLE_TO_ENUM[title_str])

pages = {
    fanta_page: {
        str(b.panel_num): {"x0": b.x0, "y0": b.y0, "w": b.w, "h": b.h}
        for b in page_boxes.panel_boxes
    }
    for fanta_page, page_boxes in title_boxes.pages.items()
}

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"title": title_str, "pad": CROP_PAD_PX, "pages": pages}, indent=1))
print(f"wrote {out} -- {len(pages)} page(s)")

# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing where it put the crop is the whole point of running it.
"""Crop a region of a comic panel, given full-page text_box coordinates, and upscale it.

    python3 scripts/vision/crop.py <out-dir> <page> <panel> <x0> <y0> <x1> <y1> <scale> <dest>

Why this exists: `text_box` in groups.json is in full-page source coordinates,
and only `panel-NN.png` shares those coordinates. `page.png` is the downscaled
overview (about half), so the same numbers land somewhere else on it and the
miss is silent -- what comes back is plausible comic art with no balloon tail
in it. Always crop from the panel files.

The panel PNG's origin in full-page coords is (panel.x0 - pad, panel.y0 - pad),
which is what the boxes JSON supplies. Generate that first:

    uv run python scripts/vision/dump_boxes.py "Some Title" <out-dir>/boxes-<slug>.json

The boxes file is looked for beside this script and then inside the out-dir.
Now that this lives in the repo, the out-dir is the one that matters -- the
script-dir lookup is kept only so an older scratch layout still resolves.

No barks imports here, deliberately: this runs per crop, often a dozen times on
one page, and `python3` starts in milliseconds where `uv run` pays for the whole
barks import graph every time.

Scale guide: 2-3x to see which hat a tail leans at, 4-6x to settle a letter,
8-12x to judge a cap crown of only a few dozen ink pixels.
"""

import json
import sys
from pathlib import Path

from PIL import Image

USAGE = __doc__.strip().splitlines()[2].strip()
# out-dir, page, panel, x0, y0, x1, y1, scale, dest -- plus argv[0].
EXPECTED_ARGV = 10

if len(sys.argv) != EXPECTED_ARGV:
    msg = f"usage: {USAGE}"
    raise SystemExit(msg)

out_dir, page, panel_num = Path(sys.argv[1]).expanduser(), sys.argv[2], sys.argv[3]
x0, y0, x1, y1 = (int(v) for v in sys.argv[4:8])
scale = float(sys.argv[8])
dest = Path(sys.argv[9]).expanduser()

name = f"boxes-{out_dir.name}.json"
for candidate in (Path(__file__).resolve().parent / name, out_dir / name):
    if candidate.is_file():
        boxes_file = candidate
        break
else:
    msg = f"no {name} beside this script or in {out_dir} -- run dump_boxes.py first"
    raise SystemExit(msg)

data = json.loads(boxes_file.read_text())
pad = data["pad"]
try:
    box = data["pages"][page][str(int(panel_num))]
except KeyError:
    known = sorted(data["pages"].get(page, {}))
    msg = f"page {page} panel {panel_num} not in {boxes_file.name}; panels for that page: {known}"
    raise SystemExit(msg) from None
ox, oy = box["x0"] - pad, box["y0"] - pad

src = out_dir / page / f"panel-{int(panel_num):02d}.png"
if not src.is_file():
    tiles = sorted((out_dir / page).glob(f"panel-{int(panel_num):02d}-*.png"))
    msg = f"{src} missing; panel was tiled as {[t.name for t in tiles]} -- crop from a tile by hand"
    raise SystemExit(msg)

img = Image.open(src).convert("RGB")
cx0, cy0 = max(0, x0 - ox), max(0, y0 - oy)
cx1, cy1 = min(img.width, x1 - ox), min(img.height, y1 - oy)
if cx1 <= cx0 or cy1 <= cy0:
    msg = (
        f"empty crop: panel is {img.size}, asked for {(cx0, cy0, cx1, cy1)}"
        f" after origin ({ox},{oy})"
    )
    raise SystemExit(msg)

crop = img.crop((cx0, cy0, cx1, cy1))
crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.Resampling.LANCZOS)
crop.save(dest)
print(f"{dest}  panel={src.name} origin=({ox},{oy}) crop={(cx0, cy0, cx1, cy1)} -> {crop.size}")

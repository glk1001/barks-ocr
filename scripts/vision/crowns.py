# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the surviving blobs is the whole point of running it.
"""Keep only the cap ink that actually sits on a crown, from a `title_heads.py` census.

    uv run --offline python scripts/vision/crowns.py <census-file> [PAGE ...]

WHY THIS EXISTS. `title_heads.py` prints, for every head it finds, the cap ink ANYWHERE
in the panel -- so a red roof, a shop awning, Scrooge's coat and Donald's bow tie all
arrive attached to whichever head the census happened to be describing. Three batches
running, the review's largest error class was a blob read as a cap when it was scenery,
and the roster's answer is the same each time: a blob has to sit on a head.

This does that test arithmetically instead of by eye. A blob survives only if its
centre-x falls inside the head's white-skull span (with a 10px margin) and its bottom
edge is at or above the skull's upper third -- i.e. it is on the crown or just above it,
which is where a cap is drawn. Everything else is dropped, and a head with nothing left
prints `NO INK ON CROWN`.

It is a SCREEN, not a verdict, and it fails in both directions. Rows whose white-skull
box is wider than 300px or larger than 30000px are skipped as the whole-panel fallback
the census emits when it cannot isolate a head; and where the census's white box is the
head PLUS the beak -- which it is whenever the duck faces left -- the span is shifted and
a real cap can be dropped. When a name hangs on the answer, still crop.

Feeds on `title_heads.py <out-dir> <MIN_BEAK> <MIN_CAP>` written with a LOW MIN_CAP
(8 is what found the 25px and 10px rims in Vol. 18); at the default 25 the thin-rim
constructions are invisible before this script ever sees them.
"""

import re
import sys
from pathlib import Path

HEAD = re.compile(r"white=\((\d+),(\d+),(\d+),(\d+)\) area=(\d+)")
BLOB = re.compile(r"(red|green|blue|leafgrn|yellow)\((\d+),(\d+),(\d+),(\d+)\) a=(\d+) (#\w+)")

MAX_HEAD_WIDTH = 300  # wider than this is the census's whole-panel fallback row
MAX_HEAD_AREA = 30000  # ditto by area
X_MARGIN = 10  # how far outside the skull span a crown blob may still centre
CROWN_FRACTION = 0.45  # a blob must end within this much of the way down the skull


def main() -> None:
    """Print one line per head, with only the ink that sits on its crown."""
    pages = set(sys.argv[2:])
    panel = ""
    seen: set[tuple[str, tuple[int, int, int, int]]] = set()
    for line in Path(sys.argv[1]).read_text().splitlines():
        if not line.startswith(" "):
            panel = line.split(" (")[0].strip()
            continue
        m = HEAD.search(line)
        if not m:
            continue
        x0, y0, x1, y1, area = (int(v) for v in m.groups())
        if x1 - x0 > MAX_HEAD_WIDTH or area > MAX_HEAD_AREA:
            continue
        if pages and panel.split()[0] not in pages:
            continue
        key = (panel, (x0, y0, x1, y1))
        if key in seen:
            continue
        seen.add(key)
        height = y1 - y0
        on_crown = [
            f"{band} a={a} {hex_at} ({bx0},{by0},{bx1},{by1})"
            for band, bx0, by0, bx1, by1, a, hex_at in BLOB.findall(line)
            if x0 - X_MARGIN <= (int(bx0) + int(bx1)) // 2 <= x1 + X_MARGIN
            and int(by1) <= y0 + CROWN_FRACTION * height
        ]
        found = "; ".join(on_crown) if on_crown else "NO INK ON CROWN"
        print(f"{panel} head x{x0}-{x1} y{y0}-{y1} -> {found}")


if __name__ == "__main__":
    main()

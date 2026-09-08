# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the totals is the whole point.
"""Print capscan's per-band blob TOTALS for every panel of a prepped title, one line each.

    uv run --offline python scripts/vision/title_bands.py <out-dir> [MIN_AREA] [MAX_AREA]

WHY THIS EXISTS. The roster will not let a pass write `no cap ink` without quoting
the census's own `N blob(s) total` line, and a pass wants that number for the whole
title at once -- one line per panel, so the panels that could possibly carry a cap
are visible before any of them is opened.

It is what shows, in one screen, that a title takes its caps OFF indoors. On *The
Price of Fame* it put `leafgrn` on three panels out of eighty, which settled that
six of the seven names in the whole title had to come off one page and that the
other forty nephew groups were collectives forced by the art rather than declined.

READ THE `leafgrn` COLUMN, NOT THE `green` ONE. In Vol. 13 and Vol. 15 the cap
green lands at H109-116 and never in capscan's `green` band at all, so a `green`
column of zeroes says nothing about caps. `docs/cap-scanning.md` has the rest.

The totals are counted BEFORE the size window, which is the number the roster asks
for: `0 in window` and `0 at all` want different next moves.
"""

import sys
from pathlib import Path

from capscan import DEFAULT_MAX_AREA, DEFAULT_MIN_AREA, scan

ARG_MIN_AREA = 2  # sys.argv index of the optional MIN_AREA
ARG_MAX_AREA = 3  # sys.argv index of the optional MAX_AREA

# The four roster inks. `yellow` is deliberately left out: it is scenery in every
# volume read so far and it would be the widest column on the line.
BANDS = ("red", "green", "blue", "leafgrn")


def sweep(
    out_dir: Path,
    min_area: int = DEFAULT_MIN_AREA,
    max_area: int = DEFAULT_MAX_AREA,
) -> None:
    """Print one line per panel giving each band's total blob count.

    Args:
        out_dir: a prepped vision out-dir, holding one directory per page.
        min_area: drop blobs smaller than this, in pixels.
        max_area: drop blobs larger than this, in pixels.

    """
    for page in sorted(p for p in out_dir.iterdir() if p.is_dir()):
        for panel in sorted(page.glob("panel-*.png")):
            census = scan(str(panel), min_area, max_area)
            totals = " ".join(f"{band}={census[band][0]:4d}" for band in BANDS)
            print(f"{page.name} {panel.stem}  {totals}")


def main() -> None:
    """Sweep the out-dir named on the command line."""
    if len(sys.argv) < 2:  # noqa: PLR2004 -- script, argv shape is the usage line
        print(__doc__)
        raise SystemExit(2)
    out_dir = Path(sys.argv[1])
    if not out_dir.is_dir():
        print(f"title_bands: {out_dir} is not a directory")
        raise SystemExit(2)
    min_area = int(sys.argv[ARG_MIN_AREA]) if len(sys.argv) > ARG_MIN_AREA else DEFAULT_MIN_AREA
    max_area = int(sys.argv[ARG_MAX_AREA]) if len(sys.argv) > ARG_MAX_AREA else DEFAULT_MAX_AREA
    sweep(out_dir, min_area, max_area)


if __name__ == "__main__":
    main()

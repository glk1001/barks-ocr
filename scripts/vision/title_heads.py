# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the census is the whole point.
"""Run the head census over every panel of a prepped title, in one process.

    uv run --offline python scripts/vision/title_heads.py <out-dir> [MIN_BEAK] [MIN_CAP]

WHY THIS EXISTS. `heads.py` answers one panel, and a pass wants the whole title
before it reads page 1: which panels hold a head at all, and which of those carry
cap ink sitting on one. Asked panel by panel that is one interpreter start per
panel; this imports `find_heads` and loops, which is about ninety seconds for two
hundred and forty panels.

**REDIRECT IT TO A FILE AND READ THE FILE.** A title-wide census runs to hundreds
of lines, and piping it through `tail` has already cost a batch: on *The Secret of
Atlantis* a `tail -140` silently dropped the first twenty-one pages and left eleven
pages looking like the only ones carrying cap ink. Every absence claim that came
out of that was written against an output limit rather than against the art. It is
the same filtered-view trap the roster names, reached from a different direction.

A zero here is still not a bare head -- `docs/cap-scanning.md` says why. It is a
reason to crop, not a finding.
"""

import sys
from pathlib import Path

from heads import DEFAULT_MIN_BEAK, DEFAULT_MIN_CAP, find_heads

ARG_MIN_BEAK = 2  # sys.argv index of the optional MIN_BEAK
ARG_MIN_CAP = 3  # sys.argv index of the optional MIN_CAP


def sweep(
    out_dir: Path,
    min_beak: int = DEFAULT_MIN_BEAK,
    min_cap: int = DEFAULT_MIN_CAP,
) -> None:
    """Print the head census for every panel of a prepped out-dir, in page order.

    Args:
        out_dir: a prepped vision out-dir, holding one directory per page.
        min_beak: drop beak blobs smaller than this, in pixels.
        min_cap: drop cap blobs smaller than this, in pixels.

    """
    for page in sorted(p for p in out_dir.iterdir() if p.is_dir()):
        for panel in sorted(page.glob("panel-*.png")):
            size, lines = find_heads(str(panel), min_beak, min_cap)
            if not lines:
                print(f"{page.name} {panel.stem} {size} -- no beaks")
                continue
            print(f"{page.name} {panel.stem} {size}")
            for line in lines:
                print(f"    {line}")


def main() -> None:
    """Sweep the out-dir named on the command line."""
    if len(sys.argv) < 2:  # noqa: PLR2004 -- script, argv shape is the usage line
        print(__doc__)
        raise SystemExit(2)
    out_dir = Path(sys.argv[1])
    if not out_dir.is_dir():
        print(f"title_heads: {out_dir} is not a directory")
        raise SystemExit(2)
    min_beak = int(sys.argv[ARG_MIN_BEAK]) if len(sys.argv) > ARG_MIN_BEAK else DEFAULT_MIN_BEAK
    min_cap = int(sys.argv[ARG_MIN_CAP]) if len(sys.argv) > ARG_MIN_CAP else DEFAULT_MIN_CAP
    sweep(out_dir, min_beak, min_cap)


if __name__ == "__main__":
    main()

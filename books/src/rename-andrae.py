#!/usr/bin/env python3
"""Copy scanned pages into ``jpg_pages`` with sequential ``andrae-myth`` names.

Source files look like ``Scan 2026-07-11_16-29-13 (1).jpg``. The scan happened
in several batches whose parenthesized counter restarts at ``(1)`` each time, so
that number is *not* a reliable page order. The zero-padded ``HH-MM-SS``
timestamp, however, increases monotonically across every file, so ordering by
filename yields true scan order. This script copies the files in that order into
the destination directory, renaming each to ``andrae-myth-{num:03d}.jpg``
starting at ``num=60`` and incrementing by one per file.
"""

import shutil
from pathlib import Path

import typer
from loguru import logger

app = typer.Typer(add_completion=False)

_BOOK_DIR = Path("/home/greg/Books/Carl Barks/Books/Carl Barks and the Disney Comic Book")
_SRC_DIR = _BOOK_DIR / "Scan 2026-07-14"
_DST_DIR = _BOOK_DIR / "jpg_pages"
_START_NUM = 120


def _copy_renamed(src_dir: Path, dst_dir: Path, start_num: int) -> int:
    """Copy ``src_dir`` jpgs into ``dst_dir`` with sequential names.

    Args:
        src_dir: Directory holding the scanned ``*.jpg`` pages.
        dst_dir: Destination directory (created if missing).
        start_num: The first sequence number to assign.

    Returns:
        The number of files copied.

    """
    dst_dir.mkdir(parents=True, exist_ok=True)

    src_files = sorted(src_dir.glob("*.jpg"), key=lambda p: p.name)
    for offset, src in enumerate(src_files):
        num = start_num + offset
        dst = dst_dir / f"andrae-myth-{num:03d}.jpg"
        shutil.copy2(src, dst)
        logger.info(f"{src.name} -> {dst.name}")

    return len(src_files)


@app.command()
def main(
    src_dir: Path = typer.Option(  # noqa: B008
        _SRC_DIR,
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory of scanned jpg pages to copy.",
    ),
    dst_dir: Path = typer.Option(  # noqa: B008
        _DST_DIR,
        file_okay=False,
        dir_okay=True,
        help="Destination directory for the renamed pages.",
    ),
    start_num: int = typer.Option(
        _START_NUM,
        help="First sequence number for the andrae-myth-NNN.jpg names.",
    ),
) -> None:
    """Copy scanned pages into ``dst_dir`` renamed as ``andrae-myth-NNN.jpg``."""
    count = _copy_renamed(src_dir, dst_dir, start_num)
    logger.info(
        f"Done. Copied {count} file(s) into {dst_dir} "
        f"(andrae-myth-{start_num:03d}.jpg .. andrae-myth-{start_num + count - 1:03d}.jpg)."
    )


if __name__ == "__main__":
    app()

# ruff: noqa: INP001

"""Load LlamaParse structured output from one or more scan directories.

A "scan directory" is the output directory of ``scripts/llama-parse-pdf.py`` for
one PDF: it contains per-spread ``.json`` / ``.md`` / ``.jpg`` files. Spreads are
discovered by globbing ``*_spread_*.json`` and read in filename-sorted order;
the per-spread JSON is the sole source of truth for items and printed page
numbers, so any older sidecar manifest in the directory is ignored. Multiple
parse directories can be stitched together in the order they are passed in,
so a book parsed into ad-hoc sections reassembles correctly.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SpreadRecord:
    """One LlamaParse-parsed two-page book spread.

    Attributes:
        parse_dir: Directory containing the spread files.
        spread_stem: Filename stem, e.g. ``CB-Conversations-scan-1-rotated_spread_013``.
        spread_num_global: 1-based index across all parse dirs.
        items: Raw LlamaParse items (``pages[0].items``) preserving reading order
            and the ``book_side`` annotation added by the parse script.
        printed_page_number: Raw printed-page-number string from the spread's
            page metadata (e.g. ``"xxvi, xxvii"`` or ``"49"``), or ``None``.

    """

    parse_dir: Path
    spread_stem: str
    spread_num_global: int
    items: list[dict]
    printed_page_number: str | None


def _iter_spread_json_paths(parse_dir: Path) -> list[Path]:
    """Return spread JSON paths in filename-sorted reading order.

    Filenames follow ``*_spread_NNN.json`` (with optional alphabetic suffixes
    like ``019a`` for late-inserted spreads); plain lexicographic sort places
    those between ``019`` and ``020``, which matches reading order.
    """
    return sorted(parse_dir.glob("*_spread_*.json"))


def _load_spread_json(json_path: Path) -> tuple[list[dict], str | None]:
    """Load a spread's per-spread JSON and extract items + printed page number.

    Args:
        json_path: Path to the spread's JSON file.

    Returns:
        ``(items, printed_page_number)`` where ``items`` is ``pages[0].items`` and
        ``printed_page_number`` is ``pages[0].printed_page_number`` (or ``None``).

    """
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    pages = data.get("pages") or []
    if not pages:
        return [], None
    page = pages[0]
    return list(page.get("items") or []), page.get("printed_page_number")


def iter_spreads(parse_dirs: list[Path]) -> Iterator[SpreadRecord]:
    """Yield every spread across the given parse directories in order.

    Directories are visited in the order given. Within each directory, spreads
    are discovered by globbing ``*_spread_*.json`` and visited in
    filename-sorted order.

    Args:
        parse_dirs: Parse directory paths in reading order.

    Yields:
        One ``SpreadRecord`` per spread.

    Raises:
        FileNotFoundError: If a parse directory contains no spread JSON files.

    """
    global_num = 0
    for parse_dir in parse_dirs:
        json_paths = _iter_spread_json_paths(parse_dir)
        if not json_paths:
            msg = f"No *_spread_*.json files found in {parse_dir}"
            raise FileNotFoundError(msg)
        for json_path in json_paths:
            global_num += 1
            items, printed = _load_spread_json(json_path)
            yield SpreadRecord(
                parse_dir=parse_dir,
                spread_stem=json_path.stem,
                spread_num_global=global_num,
                items=items,
                printed_page_number=printed,
            )

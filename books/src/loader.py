# ruff: noqa: INP001

"""Load LlamaParse structured output from one or more scan directories.

A "scan directory" is the output directory of ``scripts/llama-parse-pdf.py`` for
one PDF: it contains a ``{stem}_manifest.json`` and per-spread ``.json`` / ``.md``
/ ``.jpg`` files. Multiple parse directories can be stitched together in the order
they are passed in, so a book parsed into ad-hoc sections reassembles correctly.
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
        spread_num_in_parse: Index within the spread's parse dir as recorded in
            the manifest. Usually a 1-based int, but may be a string such as
            ``"19a"`` when a late-arrived spread is inserted between existing
            ones without renumbering.
        items: Raw LlamaParse items (``pages[0].items``) preserving reading order
            and the ``book_side`` annotation added by the parse script.
        printed_page_number: Raw printed-page-number string from the spread's
            page metadata (e.g. ``"xxvi, xxvii"`` or ``"49"``), or ``None``.

    """

    parse_dir: Path
    spread_stem: str
    spread_num_global: int
    spread_num_in_parse: int | str
    items: list[dict]
    printed_page_number: str | None


def _find_manifest(parse_dir: Path) -> Path:
    """Return the single ``*_manifest.json`` file in ``parse_dir``.

    Args:
        parse_dir: Directory expected to contain one manifest.

    Returns:
        Path to the manifest JSON.

    Raises:
        FileNotFoundError: If no manifest is found.
        RuntimeError: If multiple manifests are found.

    """
    matches = sorted(parse_dir.glob("*_manifest.json"))
    if not matches:
        msg = f"No *_manifest.json found in {parse_dir}"
        raise FileNotFoundError(msg)
    if len(matches) > 1:
        msg = f"Multiple manifests found in {parse_dir}: {[m.name for m in matches]}"
        raise RuntimeError(msg)
    return matches[0]


def _load_spread_json(parse_dir: Path, spread_entry: dict) -> tuple[list[dict], str | None]:
    """Load a spread's per-spread JSON and extract items + printed page number.

    Args:
        parse_dir: Directory containing the spread JSON.
        spread_entry: One ``spreads[]`` entry from the manifest.

    Returns:
        ``(items, printed_page_number)`` where ``items`` is ``pages[0].items`` and
        ``printed_page_number`` is ``pages[0].printed_page_number`` (or ``None``).

    """
    json_path = parse_dir / spread_entry["json"]
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    pages = data.get("pages") or []
    if not pages:
        return [], None
    page = pages[0]
    return list(page.get("items") or []), page.get("printed_page_number")


def iter_spreads(parse_dirs: list[Path]) -> Iterator[SpreadRecord]:
    """Yield every spread across the given parse directories in order.

    Directories are visited in the order given. Within each directory, spreads are
    visited in the order recorded in that directory's manifest.

    Args:
        parse_dirs: Parse directory paths in reading order.

    Yields:
        One ``SpreadRecord`` per spread.

    """
    global_num = 0
    for parse_dir in parse_dirs:
        manifest_path = _find_manifest(parse_dir)
        with manifest_path.open(encoding="utf-8") as f:
            manifest = json.load(f)
        for entry in manifest.get("spreads", []):
            global_num += 1
            items, printed = _load_spread_json(parse_dir, entry)
            stem = Path(entry["json"]).stem
            yield SpreadRecord(
                parse_dir=parse_dir,
                spread_stem=stem,
                spread_num_global=global_num,
                spread_num_in_parse=entry["spread_num"],
                items=items,
                printed_page_number=printed,
            )

# ruff: noqa: INP001

"""Load LlamaParse structured output from one or more scan directories.

A "scan directory" is the output directory of ``scripts/llama-parse-pdf.py`` for
one PDF: it contains per-spread or per-page ``.json`` / ``.md`` / ``.jpg`` files.
Two filename layouts are supported:

* Two-page-spread output (``*_spread_NNN.json``): each JSON describes one
  printed two-page spread; items carry a ``book_side`` ("left" / "right") tag.
* Single-page output (e.g. ``CBatAotCB-NNN.json``): each JSON describes one
  printed page; items have no ``book_side``.

Either layout is discovered by globbing ``*.json`` and reading in
filename-sorted order. The per-file JSON is the sole source of truth for items
and printed page numbers, so any older sidecar manifest in the directory is
ignored. Multiple parse directories can be stitched together in the order they
are passed in, so a book parsed into ad-hoc sections reassembles correctly.
"""

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SpreadRecord:
    """One LlamaParse-parsed unit (a two-page spread or a single page).

    Attributes:
        parse_dir: Directory containing the source files.
        spread_stem: Filename stem, e.g. ``CB-Conversations-scan-1-rotated_spread_013``
            for spread output or ``CBatAotCB-001`` for single-page output.
        spread_num_global: 1-based index across all parse dirs.
        items: Raw LlamaParse items (``pages[0].items``) preserving reading order.
            For spread output, items carry a ``book_side`` annotation added by the
            parse script; for single-page output, items have no ``book_side``.
        printed_page_number: Raw printed-page-number string from the page
            metadata (e.g. ``"xxvi, xxvii"`` for a spread or ``"49"`` for a
            single page), or ``None``.

    """

    parse_dir: Path
    spread_stem: str
    spread_num_global: int
    items: list[dict]
    printed_page_number: str | None


def _iter_parse_json_paths(parse_dir: Path) -> list[Path]:
    """Return parse JSON paths in filename-sorted reading order.

    Two filename layouts are accepted: ``*_spread_NNN.json`` (with optional
    alphabetic suffixes like ``019a`` for late-inserted spreads) and the
    single-page form (e.g. ``CBatAotCB-NNN.json`` with front/back-matter
    variants like ``CBatAotCB-000-09-ix.json``). Plain lexicographic sort
    matches reading order in both cases.
    """
    return sorted(parse_dir.glob("*.json"))


_REPRINTED_PREFIX = "Reprinted: "

# Matches a ``"Reprinted: ..."`` reprint-source clause through the end of its
# line. Tolerates markdown emphasis markers around the whole clause
# (``*Reprinted: ...*``, ``**Reprinted:** ...``) or around just the word with
# the colon outside (``*Reprinted*: ...``), and the inline form that trails a
# strip description (``"... golf balls. Reprinted: ..."``). The required colon
# keeps mid-text "Reprinted from ..." mentions untouched.
_REPRINTED_CLAUSE_RE = re.compile(r"\s*[*_]*Reprinted[*_]*\s*:.*$")


def _is_reprinted_item(item: dict) -> bool:
    """Return True for a standalone "Reprinted: ..." caption item to drop entirely.

    These are the per-strip reprint-source captions in the comic-pages section
    of the book (e.g. ``"Reprinted: *Walt Disney's Comics* No. 449, ..."``).
    They are identified by their first JSON key being ``md`` whose value starts
    with ``"Reprinted: "`` — items that merely mention "Reprinted from" mid-text
    keep a different leading key and are preserved.
    """
    first_key = next(iter(item), None)
    if first_key != "md":
        return False
    md = item.get("md")
    return isinstance(md, str) and md.startswith(_REPRINTED_PREFIX)


def _strip_reprinted_lines(item: dict) -> None:
    """Strip any ``"Reprinted: ..."`` reprint-source clause from ``md``/``value``.

    Some comic-strip-listing items glue a reprint-source clause onto the strip
    description rather than emitting it as a standalone item, so they aren't
    caught by ``_is_reprinted_item``. The clause may be its own
    newline-delimited line (possibly wrapped in markdown emphasis, e.g.
    ``*Reprinted: ...*`` or ``**Reprinted:** ...``) or trail the description
    inline (``"... golf balls. Reprinted: ..."``). Each line is truncated at the
    clause: a line that was nothing but the clause is dropped, and an inline
    clause is cut while the leading description text is kept.
    """
    for key in ("md", "value"):
        text = item.get(key)
        if not isinstance(text, str):
            continue
        out: list[str] = []
        for line in text.split("\n"):
            stripped = _REPRINTED_CLAUSE_RE.sub("", line)
            if stripped == line:
                out.append(line)
            elif stripped.strip():
                out.append(stripped.rstrip())
            # else: the whole line was a reprint clause -> drop it
        item[key] = "\n".join(out)


def _load_parse_json(json_path: Path) -> tuple[list[dict], str | None]:
    """Load a parse JSON and extract items + printed page number.

    Reprint-source captions are removed: items whose first key is ``md`` with a
    value starting with ``"Reprinted: "`` are dropped entirely
    (``_is_reprinted_item``), and any ``"Reprinted: ..."`` line embedded inside
    a surviving item is stripped (``_strip_reprinted_lines``).

    Args:
        json_path: Path to the parse JSON file (one spread or one page).

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
    items: list[dict] = []
    for item in page.get("items") or []:
        if _is_reprinted_item(item):
            continue
        _strip_reprinted_lines(item)
        md = item.get("md")
        if item.get("type") == "text" and isinstance(md, str) and not md.strip():
            # The item was nothing but a reprint clause; drop it entirely.
            continue
        items.append(item)
    return items, page.get("printed_page_number")


def iter_spreads(parse_dirs: list[Path]) -> Iterator[SpreadRecord]:
    """Yield every parse unit (spread or page) across the given dirs in order.

    Directories are visited in the order given. Within each directory, parse
    files are discovered by globbing ``*.json`` and visited in filename-sorted
    order.

    Args:
        parse_dirs: Parse directory paths in reading order.

    Yields:
        One ``SpreadRecord`` per parse JSON file.

    Raises:
        FileNotFoundError: If a parse directory contains no JSON files.

    """
    global_num = 0
    for parse_dir in parse_dirs:
        json_paths = _iter_parse_json_paths(parse_dir)
        if not json_paths:
            msg = f"No *.json files found in {parse_dir}"
            raise FileNotFoundError(msg)
        for json_path in json_paths:
            global_num += 1
            items, printed = _load_parse_json(json_path)
            yield SpreadRecord(
                parse_dir=parse_dir,
                spread_stem=json_path.stem,
                spread_num_global=global_num,
                items=items,
                printed_page_number=printed,
            )

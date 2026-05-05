#!/usr/bin/env python3
"""Normalize quote characters in LlamaParse text-bearing fields.

For each input path (a JSON file, or a directory searched recursively for
``*.json``), this script rewrites the ``value``, ``md``, and ``caption``
strings on every ``pages[].items[]`` entry so that all double and single
quotes — straight or already-curly — are reset to typographically correct
curly quotes (U+201C/U+201D and U+2018/U+2019). Files are edited in place.

Both ``value`` (used by indexers/spellcheckers) and ``md`` (used by the EPUB
builder) are processed, so curly quotes show up in rendered output as well as
in raw text fields.

Existing curly quotes are first folded back to straight, then re-decided, so
misoriented curlies emitted upstream (e.g. by LlamaParse) are corrected.
Opening vs. closing is decided by the preceding character: a quote preceded
by start-of-string, whitespace, an opening bracket, an em-/en-dash, a hyphen,
an ellipsis, a Markdown emphasis marker (``*`` / ``_``), or an already-open
curly is treated as opening; otherwise it's closing. In-word apostrophes
(e.g. ``Barks's``) therefore become a right-single curly (U+2019), matching
typographic norms.
"""

import json
from pathlib import Path

import typer
from curly_quotes import curlify
from loguru import logger

app = typer.Typer(add_completion=False)

_TEXT_FIELDS: tuple[str, ...] = ("value", "md", "caption")


def _process_file(path: Path) -> int:
    """Curlify text-bearing fields in ``path`` and rewrite it.

    The ``value``, ``md``, and ``caption`` fields on every item are updated.

    Args:
        path: A LlamaParse JSON file.

    Returns:
        The number of fields that were modified.

    """
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    for page in data.get("pages") or []:
        for item in page.get("items") or []:
            for field in _TEXT_FIELDS:
                original = item.get(field)
                if not isinstance(original, str) or not original:
                    continue
                updated = curlify(original)
                if updated != original:
                    item[field] = updated
                    changed += 1

    if changed:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return changed


def _iter_json_paths(path: Path) -> list[Path]:
    """Return JSON paths under ``path`` (recursive when it's a directory).

    Args:
        path: A file or directory.

    Returns:
        Sorted list of ``*.json`` file paths.

    Raises:
        FileNotFoundError: If ``path`` does not exist.

    """
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(path.rglob("*.json"))
    msg = f"Path does not exist: {path}"
    raise FileNotFoundError(msg)


@app.command()
def main(
    paths: list[Path] = typer.Argument(  # noqa: B008
        ...,
        exists=True,
        help="JSON files or directories to process (directories searched recursively).",
    ),
) -> None:
    """Replace straight quotes with curly quotes in LlamaParse ``value`` fields."""
    json_paths: list[Path] = []
    for p in paths:
        json_paths.extend(_iter_json_paths(p))
    if not json_paths:
        logger.warning("No JSON files found.")
        raise typer.Exit(0)

    total_files = 0
    total_fields = 0
    for jp in json_paths:
        try:
            changed = _process_file(jp)
        except json.JSONDecodeError as exc:
            logger.error(f"Skipping {jp}: invalid JSON ({exc})")
            continue
        if changed:
            total_files += 1
            total_fields += changed
            logger.info(f"{jp}: updated {changed} field(s)")

    logger.info(
        f"Done. Files scanned: {len(json_paths)}; files modified: {total_files}; "
        f"text fields changed: {total_fields}."
    )


if __name__ == "__main__":
    app()

# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing the verdict is the whole point of running it.
"""Say whether a seed title's paddleocr copy still matches its easyocr source.

    uv run python scripts/vision/seed_copy_check.py "Some Title"

On a page built by `barks-ocr-vision-seed`, the paddleocr file is a copy of the
easyocr file, marked with a top-level `copied_from_engine`, and it should stay an
exact copy. A review writes to both engines, though, and it often refits a box
on easyocr alone. `seed sync --write` puts the copy right. `vision-mirror` does
not, because it copies no `text_box`. *The Invisible Intruder* was closed with
the mirror on 2026-10-07 and left 20 boxes diverged, and the mirror's dry run
still reported both engines matching.

Prints `seed pages: N` and then `diverged: M page(s), B box(es), F other
field(s)`, followed by one line per differing group. A title with no seed pages
prints `seed pages: 0` and nothing else: its two engines are separate OCR runs
and are expected to disagree on boxes.
"""

import sys
from typing import Any

from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import SpeechGroups

SEED_MARKER = "copied_from_engine"
TEXT_BOX = "text_box"
MAX_DETAIL_LINES = 40


def _pages_by_engine(title_str: str) -> dict[str, dict[str, dict[str, Any]]]:
    """Return {fanta_page: {engine: page_json}} for every page of the title."""
    pages: dict[str, dict[str, dict[str, Any]]] = {}
    speech_groups = SpeechGroups(ComicsDatabase())
    for page_group in speech_groups.get_speech_page_groups(
        STR_TITLE_TO_ENUM[title_str], skip_missing=True
    ):
        engine = page_group.ocr_index.value
        pages.setdefault(page_group.fanta_page, {})[engine] = page_group.speech_page_json
    return pages


def _compare_page(
    page: str, source: dict[str, Any], copy: dict[str, Any]
) -> tuple[int, int, list[str]]:
    """Return (boxes, other fields, detail lines) where the copy differs from its source."""
    src_groups, cpy_groups = source.get("groups", {}), copy.get("groups", {})
    boxes = 0
    others = 0
    details: list[str] = []
    for gid in sorted(set(src_groups) | set(cpy_groups), key=int):
        src, cpy = src_groups.get(gid), cpy_groups.get(gid)
        if src is None or cpy is None:
            others += 1
            details.append(f"  {page} g{gid}: only on {'paddleocr' if src is None else 'easyocr'}")
            continue
        fields = sorted(k for k in set(src) | set(cpy) if src.get(k) != cpy.get(k))
        if not fields:
            continue
        boxes += TEXT_BOX in fields
        others += sum(1 for f in fields if f != TEXT_BOX)
        details.append(f"  {page} g{gid}: {', '.join(fields)}")
    rest = sorted(
        k
        for k in (set(source) | set(copy)) - {"groups", SEED_MARKER}
        if source.get(k) != copy.get(k)
    )
    if rest:
        others += len(rest)
        details.append(f"  {page} page fields: {', '.join(rest)}")
    return boxes, others, details


def main() -> None:
    """Print the seed-copy verdict for the title named on the command line."""
    pages = _pages_by_engine(sys.argv[1])
    seed_pages = 0
    diverged_pages = 0
    boxes = 0
    others = 0
    details: list[str] = []
    for page in sorted(pages):
        source, copy = pages[page].get("easyocr"), pages[page].get("paddleocr")
        if source is None or copy is None or SEED_MARKER not in copy:
            continue
        seed_pages += 1
        page_boxes, page_others, page_details = _compare_page(page, source, copy)
        boxes += page_boxes
        others += page_others
        details += page_details
        diverged_pages += bool(page_details)

    print(f"seed pages: {seed_pages}")
    if not seed_pages:
        return
    print(f"diverged: {diverged_pages} page(s), {boxes} box(es), {others} other field(s)")
    for line in details[:MAX_DETAIL_LINES]:
        print(line)
    if len(details) > MAX_DETAIL_LINES:
        print(f"  ... and {len(details) - MAX_DETAIL_LINES} more")


if __name__ == "__main__":
    main()

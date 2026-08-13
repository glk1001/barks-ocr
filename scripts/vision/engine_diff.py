# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing the per-page diff is the whole point of running it.
"""Diff the two OCR engines' groups, page by page, for one title or the corpus.

    uv run python scripts/vision/engine_diff.py ["Some Title"]

Why this exists, and why it is not part of `audit_missed_text.py`: that audit
compares the pass's `visible_text` against the text the groups already carry, so
it is blind to two things. A second copy of an already-grouped string looks
covered, and lettering only one engine ever grouped is never asked about at all.
Both show up here as a page where the engines disagree.

A count difference is normal -- the two engines split and merge balloons
differently -- so read the strings, not the number. What matters is a string one
engine has and the other has nothing like.
"""

import re
import sys

from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import SpeechGroups

from barks_ocr.utils.title_selection import resolve_titles

ENGINES_PER_PAGE = 2


def normalize(text: str | None) -> str:
    """Reduce lettering to bare words, so punctuation and case cannot fake a diff."""
    return re.sub(r"[^A-Z0-9]+", " ", (text or "").upper()).strip()


def covered(needle: str, others: set[str]) -> bool:
    """Say whether another engine's group carries this text, whole, inside a longer group."""
    return any(needle and (needle in other or other in needle) for other in others)


def diff_title(speech_groups: SpeechGroups, title_str: str) -> int:
    """Print the per-page engine diff for one title; return the number of odd pages."""
    pages: dict[str, dict[str, list[str]]] = {}
    for page_group in speech_groups.get_speech_page_groups(
        STR_TITLE_TO_ENUM[title_str], skip_missing=True
    ):
        texts = [g.get("ai_text") for g in page_group.speech_page_json.get("groups", {}).values()]
        pages.setdefault(page_group.fanta_page, {})[str(page_group.ocr_index)] = texts

    odd = 0
    for page, engines in sorted(pages.items()):
        names = sorted(engines)
        if len(names) != ENGINES_PER_PAGE:
            print(f"  {page}: only {names}")
            odd += 1
            continue
        first, second = (engines[name] for name in names)
        set_first = {normalize(t) for t in first} - {""}
        set_second = {normalize(t) for t in second} - {""}
        only_first = sorted(t for t in set_first if not covered(t, set_second))
        only_second = sorted(t for t in set_second if not covered(t, set_first))
        if not only_first and not only_second:
            continue
        odd += 1
        print(f"  {page}: {names[0]}={len(first)} {names[1]}={len(second)}")
        for text in only_first:
            print(f"      only {names[0]}: {text[:90]!r}")
        for text in only_second:
            print(f"      only {names[1]}: {text[:90]!r}")
    return odd


def main() -> None:
    """Diff every page of the named title, or of the whole corpus when none is named."""
    only_title = sys.argv[1] if len(sys.argv) > 1 else ""
    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    titles = resolve_titles(comics_database, "", only_title)

    total = 0
    for title_str in titles:
        print(f'=== "{title_str}"')
        total += diff_title(speech_groups, title_str)
    print(f"{total} page(s) where the engines carry text the other has nothing like.")


if __name__ == "__main__":
    main()

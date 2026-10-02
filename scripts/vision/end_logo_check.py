# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing the verdict is the whole point of running it.
"""Say whether a title's last story page carries a `the End` group.

    uv run python scripts/vision/end_logo_check.py "Some Title"

EasyOCR never boxes Barks' script end logo, so a pass groups it only if it
notices the logo in the last panel's corner -- and the missed-text audit cannot
catch the miss, because the pass that missed the group also left it out of
`visible_text`. Eleven Vol. 30 seed titles went out without it (2026-10-02).

Advisory: many stories end with no logo at all (31 of the 42 seed titles checked
that day), so a page without the group is a thing to LOOK at, not a defect.
Prints `the End: present on <page>` or `the End: absent on <page>`.
"""

import sys

from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import SpeechGroups


def main() -> None:
    """Print whether the title's last page has a `the End` group on either engine."""
    title_str = sys.argv[1]
    speech_groups = SpeechGroups(ComicsDatabase())
    last_page = ""
    texts: list[str] = []
    for page_group in speech_groups.get_speech_page_groups(
        STR_TITLE_TO_ENUM[title_str], skip_missing=True
    ):
        page = page_group.fanta_page
        if page > last_page:
            last_page, texts = page, []
        if page == last_page:
            groups = page_group.speech_page_json.get("groups", {}).values()
            texts += [" ".join((g.get("ai_text") or "").split()).lower() for g in groups]
    if not last_page:
        print("the End: no pages found")
        return
    verdict = "present" if "the end" in texts else "absent"
    print(f"the End: {verdict} on {last_page}")


if __name__ == "__main__":
    main()

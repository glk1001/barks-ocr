# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the census is the whole point.
"""Assert that no title has silently dropped out of the corpus scans.

    uv run --offline python scripts/vision/title_census.py            # check
    uv run --offline python scripts/vision/title_census.py --update   # re-baseline

WHY THIS EXISTS. `Panels segments info file ... is older than srce image file`
is an mtime gate, and `vision-status` swallows it at DEBUG. An affected title
does not error -- it simply vanishes from `--titles`, `--todo` and `--next`, and
from every corpus sweep that walks the same list. Nothing says so. The only
visible symptom is the denominator in "N of 441 title(s)" quietly getting
smaller, and nobody reads a denominator.

So the denominator is recorded, and this compares against it. **A drop is an
error**; a rise is normal as the database grows and is reported so the baseline
can be moved deliberately.

It stores the title NAMES, not just the count, because the count alone leaves
you looping a suspect volume through `title_pages()` to work out which one went.
Naming them costs a few KB and answers the question directly.

This takes about 40 seconds -- it builds every title's page list -- so it is not
in `closeout.sh`, which runs per title in about two. Run it after a batch, or
whenever a sweep's denominator looks wrong.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import SpeechGroups

from barks_ocr.tools.vision_status import scan_titles

BASELINE = Path(__file__).with_name("title-count-baseline.json")

MAX_LISTED = 20


def census() -> list[str]:
    """Return every title the corpus scan can currently see, sorted.

    Returns:
        Title names, sorted, as `vision-status --titles` would count them.

    """
    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    return sorted(stat.title for stat in scan_titles(comics_database, speech_groups))


def _write(titles: list[str]) -> None:
    """Record *titles* as the new baseline."""
    BASELINE.write_text(
        json.dumps(
            {
                "recorded": datetime.now(UTC).date().isoformat(),
                "count": len(titles),
                "titles": titles,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"baseline written: {len(titles)} title(s) -> {BASELINE.name}")


def main() -> None:
    """Compare the visible titles against the recorded baseline."""
    titles = census()

    if "--update" in sys.argv:
        _write(titles)
        return

    if not BASELINE.exists():
        print(f"No baseline yet. Recording the current {len(titles)} title(s).")
        _write(titles)
        return

    recorded = json.loads(BASELINE.read_text(encoding="utf-8"))
    known = set(recorded["titles"])
    seen = set(titles)

    vanished = sorted(known - seen)
    added = sorted(seen - known)

    print(f"baseline {recorded['count']} title(s), recorded {recorded['recorded']}")
    print(f"visible  {len(titles)} title(s)")

    if added:
        print(f"\n{len(added)} new title(s) -- re-baseline with --update:")
        for title in added[:MAX_LISTED]:
            print(f"    + {title}")
        if len(added) > MAX_LISTED:
            print(f"    ... and {len(added) - MAX_LISTED} more")

    if not vanished:
        print("\nNo title has dropped out of the scan.")
        return

    print(f"\n{len(vanished)} TITLE(S) HAVE VANISHED FROM THE SCAN:")
    for title in vanished[:MAX_LISTED]:
        print(f"    - {title}")
    if len(vanished) > MAX_LISTED:
        print(f"    ... and {len(vanished) - MAX_LISTED} more")
    print("\n  Most likely the panel-segments mtime gate, which vision-status hides")
    print("  in its debug log. Verify the segmentation still matches the image")
    print("  before touching anything -- it is a staleness gate, not corruption.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()

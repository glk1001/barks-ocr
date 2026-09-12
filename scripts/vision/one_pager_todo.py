# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the work list is the whole point.
"""List the one-pagers the vision pass has not read, oldest first.

    uv run --offline python scripts/vision/one_pager_todo.py

WHY THIS EXISTS. ``barks-ocr-vision-status --titles --todo`` is the work list for
every other kind of story, and it deliberately SKIPS one-pagers: they have no
``.ini``, so ``get_comic_book`` cannot resolve them, and trying to resolve them
aborted the whole report. Skipping is the right call for that tool, but it leaves
the one-pagers with no work list at all -- they have to be asked for by name and
are never offered by ``--todo``.

This rebuilds the same list for them alone, derived from the corpus on every run
for the same reason ``vision_status`` derives its own: a separate record of what
is on disk could only drift away from what is on disk.

IT KEEPS ``vision_status``'S OWN DEFINITION OF "READ" rather than inventing one:
a page is read iff some group on it carries ``vision_note``. Group ``speaker`` is
NOT the test. Groups added by hand in the editor carry a speaker without the pass
ever having run, and counting those marked thirteen untouched stories as partly
done and then hid every one of them from ``--todo``.

Order is ``int(Titles.X)``, which ``vision_status.scan_titles`` documents as
chronological across all 450 titles with no inversions, so nothing here parses a
date.

THE THIRD AND FOURTH STATES ARE NOT A BACKLOG. ``READ`` and ``--`` mean what they
look like. ``NO PAGES`` and ``UNRESOLVED`` mean the title does not resolve to any
page in the restored volumes -- 50 of the 155 one-pagers as of 2026-09-12 -- so
they are not work waiting to be done, they are simply not in the scanned books.
Read the summary line, not just the table, before sizing a batch.

Assumes the barks-ocr repo as the working directory, because the barks path
dependencies resolve from there.
"""

from collections.abc import Collection
from typing import NamedTuple

from barks_fantagraphics.barks_titles import ENUM_TO_STR_TITLE, Titles
from barks_fantagraphics.comic_book_info import ONE_PAGERS
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from loguru import logger

from barks_ocr.utils.title_selection import title_pages
from barks_ocr.utils.vision_schema import VISION_NOTE_KEY

TITLE_WIDTH = 44
UNKNOWN = "?"

STATE_READ = "READ"
STATE_UNREAD = "--"
STATE_PART = "part"
STATE_NO_PAGES = "NO PAGES"


class Row(NamedTuple):
    """One one-pager's line in the work list."""

    order: int
    title: str
    volume: str
    pages: str
    state: str


def _pages_read(speech_groups: SpeechGroups, title: Titles, pages: Collection[str]) -> int:
    """Count how many of a title's pages the vision pass has actually read.

    Args:
        speech_groups: the loaded speech groups for the corpus.
        title: the one-pager being measured.
        pages: the fanta page numbers that belong to this title.

    Returns:
        The number of those pages carrying at least one ``vision_note`` group.

    """
    read = 0
    for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True):
        if page_group.ocr_index != OcrTypes.EASYOCR or page_group.fanta_page not in pages:
            continue
        groups = page_group.speech_page_json.get("groups", {})
        if any(VISION_NOTE_KEY in group for group in groups.values()):
            read += 1
    return read


def _scan(comics_database: ComicsDatabase, speech_groups: SpeechGroups) -> list[Row]:
    """Walk every one-pager and work out its state.

    The database is quietened for the duration, as ``vision_status.scan_titles``
    does and for the same reason: resolving every title walks every page's panel
    boxes and warns per page about bounding-box heights, none of it about
    coverage.

    Args:
        comics_database: the comics database.
        speech_groups: the loaded speech groups for the corpus.

    Returns:
        One ``Row`` per one-pager, in chronological (enum) order.

    """
    logger.disable("barks_fantagraphics")
    try:
        rows: list[Row] = []
        for title in sorted(ONE_PAGERS, key=int):
            title_str = ENUM_TO_STR_TITLE[title]
            try:
                pages = title_pages(comics_database, speech_groups, title_str, OcrTypes.EASYOCR)
            except Exception as exc:  # noqa: BLE001 -- any resolution failure is "not in the books".
                rows.append(Row(int(title), title_str, UNKNOWN, UNKNOWN, f"UNRESOLVED: {exc}"))
                continue
            if not pages:
                rows.append(Row(int(title), title_str, UNKNOWN, UNKNOWN, STATE_NO_PAGES))
                continue
            try:
                volume = str(comics_database.get_fanta_volume_int(title_str))
            except Exception:  # noqa: BLE001 -- the page list is what matters; the volume is a label.
                volume = UNKNOWN
            read = _pages_read(speech_groups, title, pages)
            if read >= len(pages):
                state = STATE_READ
            elif read:
                state = STATE_PART
            else:
                state = STATE_UNREAD
            rows.append(Row(int(title), title_str, volume, ",".join(pages), state))
        return rows
    finally:
        logger.enable("barks_fantagraphics")


def _report(rows: list[Row]) -> None:
    """Print the table and the summary that sizes the next batch.

    Args:
        rows: the scanned one-pagers, in chronological order.

    """
    print(f"{'ord':>4}  {'title':{TITLE_WIDTH}} {'vol':>4} {'pages':>8}  state")
    for row in rows:
        print(
            f"{row.order:>4}  {row.title[:TITLE_WIDTH]:{TITLE_WIDTH}}"
            f" {row.volume:>4} {row.pages:>8}  {row.state}"
        )

    read = [r for r in rows if r.state == STATE_READ]
    unread = [r for r in rows if r.state == STATE_UNREAD]
    part = [r for r in rows if r.state == STATE_PART]
    absent = [r for r in rows if r not in read and r not in unread and r not in part]
    print(
        f"\ntotal {len(rows)}   read {len(read)}   unread {len(unread)}"
        f"   part {len(part)}   not in the books {len(absent)}"
    )
    print("\nThe next batch comes off the `--` rows, oldest first.")
    for row in absent:
        print(f"  not in the books: {row.title} -- {row.state}")


def main() -> None:
    """Scan every one-pager and print the work list."""
    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    _report(_scan(comics_database, speech_groups))


if __name__ == "__main__":
    main()

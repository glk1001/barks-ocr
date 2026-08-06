# ruff: noqa: T201
"""Report which titles the vision pass has read, and under which rules.

Derived from the corpus on every run rather than kept in a ledger beside it.
That is a deliberate difference from the sibling repo's ``restore-ledger.jsonl``
and ``upscale-ledger.jsonl``, and the reason is that the two workloads are not
the same shape.  A restore run is long, unattended and can be stopped half way
through, so its ledger exists to answer "where did I get to" for work that
cannot simply be repeated.  A vision pass is one title in one session and is
idempotent -- applying a result twice changes nothing -- so there is no lost
position to recover, and a separate record of what is on disk could only drift
away from what is actually on disk.

What a scan cannot recover is what a *human review* concluded, because that is
an event rather than a state.  See ``docs/vision-pass.md``; the agreed shape is
to store the pass's original call on the group beside the reviewer's answer, not
to add a ledger.

The scan is fast enough to be a routine question: the whole corpus is ~11,000
small JSON files and a full report takes a few seconds.
"""

import collections
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.barks_titles import ENUM_TO_STR_TITLE, STR_TITLE_TO_ENUM, Titles
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from comic_utils.common_typer_options import LogLevelArg
from loguru import logger

from barks_ocr.cli_setup import init_logging
from barks_ocr.utils.title_selection import title_pages
from barks_ocr.utils.vision_schema import (
    CAPTURE_PROMPT_VERSION,
    CAPTURE_PROMPT_VERSION_KEY,
    CAPTURE_RULES,
    SPEAKER_KEY,
)

APP_LOGGING_NAME = "visstat"

CAPTURE_SUFFIX = "-page-capture.json"
PRELIM_GLOB = "*-easyocr-gemini-prelim-groups.json"
_VOL_RE = re.compile(r"Vol\.? (\d+)")

# The cohort that predates provenance being written at all.  Its capture records
# carry nulls, which is the only thing identifying them.
UNSTAMPED = "unstamped (pre-2026-08-03)"

# Titles that are finished but can never satisfy ``read == pages``, and so would
# be offered as the next job for ever.
#
# A page counts as read when at least one of its groups carries a speaker, so a
# page with no groups at all can never count.  *Donald Duck Finds Pirate Gold*
# (1942) is fully read and fully reviewed -- all 385 groups -- but three of its
# 64 pages (032, 036 and 048) are wordless, so it sits at 61/64 permanently and
# `--next` kept re-offering it once every other early title was done.
#
# Deliberately a named special case rather than a general "a page with no groups
# is done" rule.  That rule is the real fix, but it cannot be written until the
# 155 one-pagers that cannot be prepped are settled, and on its own it would
# quietly mark a page that has simply not been prepped yet as finished -- which
# is the failure this list is meant to prevent, not cause.  A second title
# needing an entry here is the signal to write the general rule instead.
_ALWAYS_DONE = frozenset({ENUM_TO_STR_TITLE[int(Titles.DONALD_DUCK_FINDS_PIRATE_GOLD)]})

# Fail loudly at import rather than silently never matching if a title is ever
# renamed -- a special case that quietly stops applying is worse than none, since
# the symptom is just the old bug coming back.  Raised rather than asserted so it
# survives `python -O`.
if _unknown := sorted(_ALWAYS_DONE - STR_TITLE_TO_ENUM.keys()):
    msg = f"Unknown title(s) in _ALWAYS_DONE: {_unknown}"
    raise ValueError(msg)


class VolumeStat:
    """One volume's tally."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pages = 0
        self.annotated = 0
        self.captured = 0
        self.groups = 0
        self.annotated_groups = 0
        self.versions: collections.Counter[str] = collections.Counter()


def _volume_of(path: Path) -> tuple[int, str]:
    """Return the (number, directory name) of the volume a prelim file sits in."""
    name = path.parent.name
    match = _VOL_RE.search(name)
    return (int(match.group(1)) if match else 0, name)


def scan(prelim_dir: Path) -> dict[str, VolumeStat]:
    """Walk the prelim tree and tally vision coverage per volume.

    Args:
        prelim_dir: The root holding one directory per Fantagraphics volume.

    Returns:
        The per-volume tallies, keyed by directory name.

    """
    stats: dict[str, VolumeStat] = {}
    for prelim in sorted(prelim_dir.glob(f"*/{PRELIM_GLOB}")):
        _num, vol_name = _volume_of(prelim)
        stat = stats.setdefault(vol_name, VolumeStat(vol_name))
        stat.pages += 1

        groups = json.loads(prelim.read_text()).get("groups", {})
        stat.groups += len(groups)
        annotated = [g for g in groups.values() if g.get(SPEAKER_KEY)]
        if not annotated:
            continue
        stat.annotated += 1
        stat.annotated_groups += len(annotated)

        capture = prelim.parent / (prelim.name.split("-")[0] + CAPTURE_SUFFIX)
        if not capture.is_file():
            continue
        stat.captured += 1
        record = json.loads(capture.read_text())
        version = record.get(CAPTURE_PROMPT_VERSION_KEY)
        stat.versions[UNSTAMPED if version is None else f"v{version}"] += 1
    return stats


def _report(stats: dict[str, VolumeStat], *, show_all: bool) -> None:
    """Print the tally, widest number last."""
    touched = {k: v for k, v in stats.items() if v.annotated}
    shown = stats if show_all else touched

    print(f"{'volume':52} {'pages':>6} {'read':>6} {'capture':>8} {'groups':>8}")
    for name in sorted(shown, key=lambda n: _volume_of(Path(n) / "x")):
        s = shown[name]
        print(
            f"{name[:52]:52} {s.pages:>6} {s.annotated:>6} {s.captured:>8} {s.annotated_groups:>8}"
        )

    pages = sum(s.pages for s in stats.values())
    read = sum(s.annotated for s in stats.values())
    captured = sum(s.captured for s in stats.values())
    print(
        f"\n{read} of {pages} page(s) read ({100 * read / pages:.1f}%), "
        f"{captured} with a page capture, {pages - read} remaining."
    )
    print(f"{len(touched)} of {len(stats)} volume(s) touched.")

    versions: collections.Counter[str] = collections.Counter()
    for s in stats.values():
        versions.update(s.versions)
    if not versions:
        return
    print(f"\ncapture prompt version (current is v{CAPTURE_PROMPT_VERSION}):")
    for version, count in sorted(versions.items()):
        note = ""
        if version == UNSTAMPED:
            note = "  <- read before provenance was written; rules unknown"
        elif version != f"v{CAPTURE_PROMPT_VERSION}":
            note = "  <- read under older rules"
        print(f"   {version:26} {count:>5} page(s){note}")
    print(f"\nrules in force now: {', '.join(CAPTURE_RULES)}")


@dataclass(frozen=True)
class TitleStat:
    """One story's coverage, for the work list."""

    order: int
    year: int
    title: str
    volume: int
    pages: int
    read: int
    captured: int
    versions: tuple[str, ...]

    @property
    def state(self) -> str:
        """Return a short word for how far this title has got."""
        if not self.read:
            return "--"
        if self.read < self.pages:
            return f"part ({self.read}/{self.pages})"
        return "done" if self.captured == self.pages else f"done, {self.captured} capture"


def scan_titles(comics_database: ComicsDatabase, speech_groups: SpeechGroups) -> list[TitleStat]:
    """Return every story that has OCR, in the order Barks wrote them.

    **The `Titles` enum is already chronological**, which was checked rather than
    assumed: across all 450 titles carrying a submitted year there is not one
    inversion between enum order and year. So the work order is `int(Titles.X)`
    and no date parsing is needed.

    Derived from the corpus on every call, like the volume scan above and for the
    same reason -- a title is read iff its groups carry a speaker, so there is
    nothing to keep in step and nothing to go stale.
    """
    logger.debug("Scanning titles...")

    # Resolving all 450 titles walks every page's panel boxes, and the database
    # warns per page about bounding-box heights -- 13MB of it, none of it about
    # coverage. Silenced for the scan only, and restored straight after, so a
    # real warning from anywhere else still reaches the caller.
    logger.disable("barks_fantagraphics")
    try:
        titles = _scan_titles(comics_database, speech_groups)
    finally:
        logger.enable("barks_fantagraphics")

    logger.debug("Finished scanning titles.")
    return titles


def _scan_titles(comics_database: ComicsDatabase, speech_groups: SpeechGroups) -> list[TitleStat]:
    """Walk every title. See ``scan_titles``, which wraps this to quieten the database."""
    stats: list[TitleStat] = []
    for title_str, title in STR_TITLE_TO_ENUM.items():
        try:
            pages = title_pages(comics_database, speech_groups, title_str, OcrTypes.EASYOCR)
        except Exception as exc:  # noqa: BLE001 -- see below.
            # Silent by design, and it is the common case rather than an error:
            # the 155 one-pagers have no .ini to resolve, and the essays and
            # introductions are not stories. Logging each would bury the report
            # under a hundred lines saying the corpus is shaped as documented.
            logger.debug(f'Skipping "{title_str}": {exc}')
            continue
        if not pages:
            continue
        comic = comics_database.get_comic_book(title_str)
        read = captured = 0
        versions: collections.Counter[str] = collections.Counter()
        for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True):
            if page_group.ocr_index != OcrTypes.EASYOCR or page_group.fanta_page not in pages:
                continue
            groups = page_group.speech_page_json.get("groups", {})
            if not any(g.get(SPEAKER_KEY) for g in groups.values()):
                continue
            read += 1
            capture = page_group.ocr_prelim_groups_json_file.parent / (
                page_group.fanta_page + CAPTURE_SUFFIX
            )
            if not capture.is_file():
                continue
            captured += 1
            version = json.loads(capture.read_text()).get(CAPTURE_PROMPT_VERSION_KEY)
            versions[UNSTAMPED if version is None else f"v{version}"] += 1
        stats.append(
            TitleStat(
                order=int(title),
                year=comic.submitted_year,
                title=title_str,
                volume=comics_database.get_fanta_volume_int(title_str),
                pages=len(pages),
                read=read,
                captured=captured,
                versions=tuple(sorted(versions)),
            )
        )
    return sorted(stats, key=lambda s: s.order)


def _unread(stats: list[TitleStat]) -> list[TitleStat]:
    """Titles still to read, oldest first, skipping those that can never count.

    The single answer to "what is next", used by both `--next` and the footer of
    `--titles`.  They asked it separately before, so fixing one left the other
    still naming a finished story.  See `_ALWAYS_DONE`.
    """
    return [s for s in stats if s.read < s.pages and s.title not in _ALWAYS_DONE]


def _report_titles(stats: list[TitleStat], *, start: int, limit: int, todo_only: bool) -> None:
    """Print the chronological work list."""
    shown = [s for s in stats if not (todo_only and s.read)]
    window = shown[start : start + limit] if limit else shown[start:]

    print(f"{'#':>5} {'year':>6}  {'title':<44}{'vol':>4}{'pages':>6}  state")
    for i, s in enumerate(window, start=start + 1):
        note = f"  [{', '.join(s.versions)}]" if s.versions else ""
        print(f"{i:>5} {s.year:>6}  {s.title[:44]:<44}{s.volume:>4}{s.pages:>6}  {s.state}{note}")

    left = _unread(stats)
    # Counted as done rather than dropped, so the two figures still sum to the
    # corpus and the outstanding page count stops including pages nothing will
    # ever read.
    done = len(stats) - len(left)
    print(
        f"\n{done} of {len(stats)} title(s) done; "
        f"{len(left)} left, {sum(s.pages - s.read for s in left)} page(s)."
    )
    if left:
        nxt = left[0]
        print(f'next: "{nxt.title}" ({nxt.year}, vol {nxt.volume}, {nxt.pages}p)')
        print(f'  barks-ocr-name-grep   --title "{nxt.title}"')
        print(f'  barks-ocr-vision-prep --title "{nxt.title}"')


app = typer.Typer()


@app.command(help="Report which pages the vision pass has read, and under which rules.")
def main(  # noqa: PLR0913
    show_all: Annotated[
        bool,
        typer.Option("--all", help="List every volume, not only those with vision data."),
    ] = False,
    by_title: Annotated[
        bool,
        typer.Option("--titles", help="Per-story work list, in the order Barks wrote them."),
    ] = False,
    todo_only: Annotated[
        bool, typer.Option("--todo", help="With --titles, hide stories already read.")
    ] = False,
    next_only: Annotated[
        int, typer.Option("--next", help="Print just the next N unread stories and stop.")
    ] = 0,
    start: Annotated[int, typer.Option("--from", help="With --titles, skip this many.")] = 0,
    limit: Annotated[
        int, typer.Option("--limit", help="With --titles, show at most this many. 0 for all.")
    ] = 40,
    log_level_str: LogLevelArg = "WARNING",
) -> None:
    """Scan the prelim tree and report vision-pass coverage."""
    init_logging(APP_LOGGING_NAME, "vision-status.log", log_level_str)
    if not (by_title or next_only):
        _report(scan(OCR_PRELIM_DIR), show_all=show_all)
        return

    comics_database = ComicsDatabase()
    stats = scan_titles(comics_database, SpeechGroups(comics_database))
    if next_only:
        assert next_only > 0
        # Bare title on stdout, so a shell can use it directly.
        remaining = _unread(stats)
        if not remaining:
            raise typer.Exit(code=1)
        print(", ".join([f'"{t.title}"' for t in remaining[0:next_only]]))
        return
    _report_titles(stats, start=start, limit=limit, todo_only=todo_only)


if __name__ == "__main__":
    app()

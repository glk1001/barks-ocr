# ruff: noqa: INP001 -- a standalone script, not a package module.
"""Report the vision pass over some volumes: progress, correction rate and cost.

    uv run --offline python scripts/vision/volume_summary.py 16-18
    uv run --offline python scripts/vision/volume_summary.py 16 18 20

Answers "how are the last few volumes going" in one run, instead of reading it
back out of fifty findings sections by hand. One `rich` table per volume, a
totals row in each, and a cross-volume table when more than one is named.

WHERE EACH NUMBER COMES FROM.

- **Pages and passed state** come from `vision_status.scan_titles`, the same scan
  behind `barks-ocr-vision-status --titles`, narrowed to the volumes asked for.
  It drops pages the page map claims for a title but which belong to another
  story, which `review_findings.py` does not -- that is why it once counted
  *Genghis Khan* as 287 groups instead of 269.
- **Groups, review progress and corrections** come from the easyocr groups of
  each passed page. A correction is a group whose `speaker_was` differs from its
  current speaker. A `_was` equal to the current value records a correction that
  never happened (the editor used to write those) and is not counted.
- **Groups added in review** are counted separately and kept out of the rate: a
  review's add is born `unknown` and given its first speaker, which would
  otherwise read as an overruling. A review add is a `vision_added` group with no
  `vision_note`. A group the *pass* added carries its note and counts like any
  other: when the review changes its speaker, that is a real correction (*Good
  Canoes* 058 g10, *The Custard Gun* 093 g6). The hand tallies in the findings
  doc counted review adds as corrections, so their per-title totals run higher.
- **Cost** has two axes, both from `docs/vision-cost-ledger.csv`. Nothing in
  the corpus records either, so a title missing from the ledger shows `--`, and
  a ledger row covering several titles is shown as shared.
  `Img/pg` is images read, the axis `docs/vision-pass-cost.md` governs.
  `Calls/pg` and `Mtok/pg` are the API calls and millions of cache-read tokens
  per page that `scripts/vision/usage_census.py --by-title` credits to the
  title from the session transcripts -- context re-reading is ~90% of token
  consumption, so these move the bill in a way images/page does not. Both are
  per-title sums, so unlike an average context they total per volume.

A passed but unreviewed title has no `speaker_was` yet, so its rate reads 0%.
The `reviewed` column is coloured when it is short of the group count, so that a
0% can be told apart from a clean review.

The rate by the confidence the pass wrote needs the pass's commit and is not
here; `review_findings.py --since` gives it per title.
"""

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from intspan import intspan
from loguru import logger
from rich import box
from rich.console import Console
from rich.table import Table

from barks_ocr.tools.vision_status import TitleStat, scan_titles
from barks_ocr.utils.title_selection import title_pages
from barks_ocr.utils.vision_schema import (
    NEPHEW_NAMES,
    SPEAKER_KEY,
    SPEAKER_REVIEWED_KEY,
    SPEAKER_WAS_KEY,
    VISION_ADDED_KEY,
    VISION_NOTE_KEY,
)

LEDGER = Path(__file__).resolve().parents[2] / "docs" / "vision-cost-ledger.csv"

# Tokens re-read per page above this are coloured: the batches of 2026-09-14/15
# ran near 1M a page and those of 2026-09-20/21 near 4M, so 4M marks a dear title.
HOT_MTOK_PER_PAGE = 4.0
TITLE_SEP = " | "
COLLECTIVE = "nephews"
TITLE_WIDTH = 26

# A correction rate is read against the reviewer's stated tolerance: about 10%
# wrong on nephew calls is fine, so red starts there and yellow at half of it.
HIGH_RATE = 10.0
MID_RATE = 5.0

_console = Console()


@dataclass
class Tally:
    """Group counts for one title, or summed over several."""

    groups: int = 0
    added: int = 0
    reviewed: int = 0
    corrections: int = 0
    nephew_groups: int = 0
    nephew_corrections: int = 0

    def add(self, other: "Tally") -> None:
        """Accumulate another tally into this one.

        Args:
            other: The tally to add.

        """
        self.groups += other.groups
        self.added += other.added
        self.reviewed += other.reviewed
        self.corrections += other.corrections
        self.nephew_groups += other.nephew_groups
        self.nephew_corrections += other.nephew_corrections


@dataclass(frozen=True)
class CostUnit:
    """One ledger row: the images read for one title, or for several together."""

    volume: int
    titles: tuple[str, ...]
    pages: int
    images: int
    calls: int | None = None
    tokens_m: float | None = None


@dataclass(frozen=True)
class VolumeReport:
    """What one volume contributed, for the cross-volume table."""

    volume: int
    titles_passed: int
    titles: int
    tally: Tally
    passed_pages: int
    costed_pages: int
    images: int
    metered_pages: int
    calls: int
    tokens_m: float


def parse_volumes(args: list[str]) -> list[int]:
    """Return the volumes named on the command line, e.g. ``16-18`` or ``16 18``.

    Args:
        args: The command-line arguments.

    Returns:
        The sorted, de-duplicated volume numbers.

    """
    return sorted(set(intspan(",".join(args)))) if args else []


def load_ledger(path: Path) -> list[CostUnit]:
    """Read the cost ledger, skipping its comment lines.

    Args:
        path: The ledger CSV.

    Returns:
        One unit per data row.

    """
    lines = [line for line in path.read_text().splitlines() if not line.startswith("#")]
    return [
        CostUnit(
            volume=int(row["volume"]),
            titles=tuple(t.strip() for t in row["titles"].split(TITLE_SEP)),
            pages=int(row["pages"]),
            images=int(row["images"]),
            calls=optional_int(row.get("calls")),
            tokens_m=float(row["tokens_m"]) if row.get("tokens_m") else None,
        )
        for row in csv.DictReader(lines)
    ]


def optional_int(value: str | None) -> int | None:
    """Read a ledger cell that is blank on every row predating the census.

    Args:
        value: The raw cell, or None when the column is absent altogether.

    Returns:
        The integer, or None when the cell is missing or empty.

    """
    return int(value) if value else None


def in_nephew_domain(speaker: object) -> bool:
    """Return whether a speaker value is one of the boys or the collective.

    Args:
        speaker: A speaker value from a group.

    Returns:
        True for Huey, Dewey, Louie or ``nephews``.

    """
    return speaker in NEPHEW_NAMES or speaker == COLLECTIVE


def tally_title(
    comics_database: ComicsDatabase, speech_groups: SpeechGroups, stat: TitleStat
) -> Tally:
    """Count one passed title's groups, reviews and speaker corrections.

    Args:
        comics_database: The comics database.
        speech_groups: The speech-group loader.
        stat: The title's coverage from the status scan.

    Returns:
        The title's tally over its easyocr groups.

    """
    tally = Tally()
    pages = set(
        title_pages(comics_database, speech_groups, stat.title, OcrTypes.EASYOCR, warn=False)
    )
    for page_group in speech_groups.get_speech_page_groups(
        STR_TITLE_TO_ENUM[stat.title], skip_missing=True
    ):
        if page_group.ocr_index != OcrTypes.EASYOCR or page_group.fanta_page not in pages:
            continue
        for group in page_group.speech_page_json.get("groups", {}).values():
            if group.get(VISION_ADDED_KEY) and not group.get(VISION_NOTE_KEY):
                tally.added += 1
                continue
            tally.groups += 1
            speaker = group.get(SPEAKER_KEY)
            tally.reviewed += bool(group.get(SPEAKER_REVIEWED_KEY))
            tally.nephew_groups += in_nephew_domain(speaker)
            if SPEAKER_WAS_KEY in group and group[SPEAKER_WAS_KEY] != speaker:
                tally.corrections += 1
                was = group[SPEAKER_WAS_KEY]
                tally.nephew_corrections += in_nephew_domain(speaker) or in_nephew_domain(was)
    return tally


def rate_cell(part: int, whole: int) -> str:
    """Return a correction rate coloured against the tolerance.

    Args:
        part: Corrections.
        whole: Groups.

    Returns:
        Marked-up cell text.

    """
    if not whole:
        return "[dim]--[/]"
    value = 100 * part / whole
    colour = "red" if value >= HIGH_RATE else "yellow" if value >= MID_RATE else "green"
    return f"[{colour}]{value:.1f}%[/]"


def reviewed_cell(reviewed: int, groups: int) -> str:
    """Return how far review has got, named rather than counted when it is done.

    Args:
        reviewed: Groups carrying `speaker_reviewed`.
        groups: Groups in the title.

    Returns:
        Marked-up cell text.

    """
    if reviewed == groups:
        return "[green]all[/]"
    return f"[yellow]{reviewed}/{groups}[/]"


def cost_cell(title: str, units: list[CostUnit]) -> str:
    """Describe what the ledger records for one title.

    Args:
        title: The title.
        units: Every ledger unit.

    Returns:
        Images per page, marked ``*`` when the ledger row covers several
        titles, or a dim dash when the title is not in the ledger.

    """
    unit = next((u for u in units if title in u.titles), None)
    if unit is None:
        return "[dim]--[/]"
    rate = f"{unit.images / unit.pages:.2f}"
    return rate if len(unit.titles) == 1 else f"{rate}[dim]*[/]"


def metered_cell(title: str, units: list[CostUnit]) -> tuple[str, str]:
    """Describe the calls and tokens the ledger credits to one title, per page.

    Args:
        title: The title.
        units: Every ledger unit.

    Returns:
        Calls per page and millions of tokens per page, each marked ``*`` when
        the row covers several titles, or dim dashes when nothing is recorded.

    """
    unit = next((u for u in units if title in u.titles), None)
    if unit is None or unit.calls is None or unit.tokens_m is None:
        return "[dim]--[/]", "[dim]--[/]"
    return metered_rate(unit.calls, unit.tokens_m, unit.pages, shared=len(unit.titles) > 1)


def metered_rate(
    calls: int, tokens_m: float, pages: int, *, shared: bool = False
) -> tuple[str, str]:
    """Return calls per page and millions of tokens per page as cell text.

    Args:
        calls: API calls credited.
        tokens_m: Millions of cache-read tokens credited.
        pages: Pages they cover.
        shared: Mark both cells as covering several titles.

    Returns:
        The two cells, or dim notes when no page is metered.

    """
    if not pages:
        return "[dim]--[/]", "[dim]--[/]"
    mark = "[dim]*[/]" if shared else ""
    per_page = tokens_m / pages
    style = "bold yellow" if per_page > HOT_MTOK_PER_PAGE else "bold"
    return f"{calls / pages:.1f}{mark}", f"[{style}]{per_page:.2f}[/]{mark}"


def cost_rate(images: int, pages: int) -> str:
    """Return images per page, or a dim note when nothing is costed.

    Args:
        images: Images read.
        pages: Pages they cover.

    Returns:
        Marked-up cell text.

    """
    return f"[bold]{images / pages:.2f}[/]" if pages else "[dim]not recorded[/]"


def volume_table(volume: int, caption: str) -> Table:
    """Build the per-title table for one volume, with its columns.

    Args:
        volume: The volume number.
        caption: The line printed under the table.

    Returns:
        An empty-bodied table, ready for rows.

    """
    table = Table(
        title=f"Vol. {volume}",
        caption=caption,
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold magenta",
    )
    table.add_column("Title", no_wrap=True, overflow="ellipsis", max_width=TITLE_WIDTH)
    table.add_column("Pages", justify="right")
    table.add_column("Groups", justify="right")
    table.add_column("Rev", justify="right")
    table.add_column("Corr", justify="right")
    table.add_column("Rate", justify="right")
    table.add_column("Img/pg", justify="right")
    table.add_column("Calls/pg", justify="right")
    table.add_column("Mtok/pg", justify="right")
    return table


def report_volume(
    volume: int, stats: list[TitleStat], tallies: dict[str, Tally], units: list[CostUnit]
) -> VolumeReport:
    """Print one volume's table and return what it contributed.

    Args:
        volume: The volume number.
        stats: The volume's titles from the status scan.
        tallies: Tallies for the passed titles, by title.
        units: Every ledger unit.

    Returns:
        The volume's totals, for the cross-volume table.

    """
    passed = [s for s in stats if s.read]
    total = Tally()
    for stat in passed:
        total.add(tallies[stat.title])
    passed_pages = sum(s.read for s in passed)
    vol_units = [u for u in units if u.volume == volume]
    costed_pages = sum(u.pages for u in vol_units)
    images = sum(u.images for u in vol_units)
    metered = [u for u in vol_units if u.calls is not None and u.tokens_m is not None]
    report = VolumeReport(
        volume,
        len(passed),
        len(stats),
        total,
        passed_pages,
        costed_pages,
        images,
        sum(u.pages for u in metered),
        sum(u.calls or 0 for u in metered),
        sum(u.tokens_m or 0.0 for u in metered),
    )

    if not passed:
        _console.print(f"\n[bold magenta]Vol. {volume}[/]: [dim]nothing passed yet[/]")
        return report

    caption = (
        f"{len(passed)} of {len(stats)} titles passed, "
        f"{passed_pages} of {sum(s.pages for s in stats)} pages   "
        f"+{total.added} added in review   "
        f"nephew domain {total.nephew_corrections}/{total.nephew_groups} "
        f"({rate_cell(total.nephew_corrections, total.nephew_groups)})"
    )
    if any(len(u.titles) > 1 for u in vol_units):
        caption += "   * images recorded for several titles together"
    table = volume_table(volume, caption)
    for stat in passed:
        tally = tallies[stat.title]
        pages = str(stat.pages)
        if stat.read != stat.pages:
            pages = f"[yellow]{stat.read}/{stat.pages}[/]"
        table.add_row(
            stat.title,
            pages,
            str(tally.groups),
            reviewed_cell(tally.reviewed, tally.groups),
            str(tally.corrections),
            rate_cell(tally.corrections, tally.groups),
            cost_cell(stat.title, units),
            *metered_cell(stat.title, units),
        )
    table.add_section()
    table.add_row(
        "[bold]total[/]",
        f"[bold]{passed_pages}[/]",
        f"[bold]{total.groups}[/]",
        reviewed_cell(total.reviewed, total.groups),
        f"[bold]{total.corrections}[/]",
        rate_cell(total.corrections, total.groups),
        cost_rate(images, costed_pages),
        *metered_rate(report.calls, report.tokens_m, report.metered_pages),
    )
    _console.print()
    _console.print(table)

    left = [s for s in stats if s.read < s.pages]
    if left:
        _console.print(
            f"[dim]   left: {len(left)} title(s), {sum(s.pages - s.read for s in left)} page(s)"
            f" -- next[/] [cyan]{left[0].title}[/]"
        )
    return report


def report_totals(reports: list[VolumeReport]) -> None:
    """Print one row per volume, with a grand total.

    Args:
        reports: Each volume's contribution, in the order asked for.

    """
    table = Table(
        title="All volumes",
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold magenta",
    )
    table.add_column("Volume", justify="right")
    table.add_column("Titles", justify="right")
    table.add_column("Pages", justify="right")
    table.add_column("Groups", justify="right")
    table.add_column("Reviewed", justify="right")
    table.add_column("Corr", justify="right")
    table.add_column("Rate", justify="right")
    table.add_column("Images/page", justify="right")
    table.add_column("Calls/page", justify="right")
    table.add_column("Mtok/page", justify="right")

    grand = Tally()
    pages = costed = images = metered = calls = 0
    tokens_m = 0.0
    for report in reports:
        metered += report.metered_pages
        calls += report.calls
        tokens_m += report.tokens_m
        grand.add(report.tally)
        pages += report.passed_pages
        costed += report.costed_pages
        images += report.images
        table.add_row(
            str(report.volume),
            f"{report.titles_passed}/{report.titles}",
            str(report.passed_pages),
            str(report.tally.groups),
            reviewed_cell(report.tally.reviewed, report.tally.groups),
            str(report.tally.corrections),
            rate_cell(report.tally.corrections, report.tally.groups),
            cost_rate(report.images, report.costed_pages),
            *metered_rate(report.calls, report.tokens_m, report.metered_pages),
        )
    table.add_section()
    table.add_row(
        "[bold]all[/]",
        "",
        f"[bold]{pages}[/]",
        f"[bold]{grand.groups}[/]",
        reviewed_cell(grand.reviewed, grand.groups),
        f"[bold]{grand.corrections}[/]",
        rate_cell(grand.corrections, grand.groups),
        cost_rate(images, costed),
        *metered_rate(calls, tokens_m, metered),
    )
    _console.print()
    _console.print(table)


def main() -> None:
    """Print the report for the volumes named on the command line."""
    volumes = parse_volumes(sys.argv[1:])
    if not volumes:
        _console.print(__doc__)
        sys.exit(2)

    logger.remove()
    logger.add(sys.stderr, level="ERROR")

    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    wanted = frozenset(volumes)
    stats = scan_titles(comics_database, speech_groups, wanted)
    units = load_ledger(LEDGER)

    # Only the volumes asked for were scanned, so a ledger row from any other
    # volume is unknown here for a harmless reason and must not be reported.
    known = {s.title for s in stats}
    for unit in units:
        if unit.volume not in wanted:
            continue
        for title in unit.titles:
            if title not in known:
                _console.print(f"[yellow]!! ledger title not found in the corpus:[/] {title!r}")

    logger.disable("barks_fantagraphics")
    try:
        tallies = {s.title: tally_title(comics_database, speech_groups, s) for s in stats if s.read}
    finally:
        logger.enable("barks_fantagraphics")

    reports = [
        report_volume(volume, [s for s in stats if s.volume == volume], tallies, units)
        for volume in volumes
    ]
    if len(volumes) > 1:
        report_totals(reports)


if __name__ == "__main__":
    main()

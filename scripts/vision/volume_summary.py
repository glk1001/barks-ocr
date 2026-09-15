# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the summary is the whole point.
"""Report the vision pass over some volumes: progress, correction rate and cost.

    uv run --offline python scripts/vision/volume_summary.py 16-18
    uv run --offline python scripts/vision/volume_summary.py 16 18 20

Answers "how are the last few volumes going" in one run, instead of reading it
back out of fifty findings sections by hand.

WHERE EACH NUMBER COMES FROM.

- **Pages and passed state** come from `vision_status.scan_titles`, the same scan
  behind `barks-ocr-vision-status --titles`. It drops pages the page map claims
  for a title but which belong to another story, which `review_findings.py` does
  not -- that is why it once counted *Genghis Khan* as 287 groups instead of 269.
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
- **Cost** is images read, from `docs/vision-cost-ledger.csv`. Nothing in the
  corpus records it, so a title missing from the ledger shows `--`, and a
  ledger row covering several titles is shown as shared.

A passed but unreviewed title has no `speaker_was` yet, so its rate reads 0%.
The `reviewed` column is there so that a 0% can be told apart from a clean
review.

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
TITLE_SEP = " | "
COLLECTIVE = "nephews"
TITLE_WIDTH = 42


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
        )
        for row in csv.DictReader(lines)
    ]


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


def pct(part: int, whole: int) -> str:
    """Format a percentage, or a dash when there is nothing to divide by.

    Args:
        part: The numerator.
        whole: The denominator.

    Returns:
        e.g. ``"5.4%"``.

    """
    return f"{100 * part / whole:.1f}%" if whole else "--"


def title_cost(title: str, units: list[CostUnit]) -> str:
    """Describe what the ledger records for one title.

    Args:
        title: The title.
        units: Every ledger unit.

    Returns:
        Images per page, a shared-unit note, or ``--`` when unrecorded.

    """
    unit = next((u for u in units if title in u.titles), None)
    if unit is None:
        return "--"
    rate = f"{unit.images}/{unit.pages} = {unit.images / unit.pages:.2f}"
    return rate if len(unit.titles) == 1 else f"shared {rate}"


def report_volume(
    volume: int, stats: list[TitleStat], tallies: dict[str, Tally], units: list[CostUnit]
) -> tuple[Tally, int, int, int]:
    """Print one volume's summary and per-title table.

    Args:
        volume: The volume number.
        stats: The volume's titles from the status scan.
        tallies: Tallies for the passed titles, by title.
        units: Every ledger unit.

    Returns:
        The volume's summed tally, passed pages, costed pages and images read.

    """
    passed = [s for s in stats if s.read]
    total = Tally()
    for stat in passed:
        total.add(tallies[stat.title])
    passed_pages = sum(s.read for s in passed)
    vol_units = [u for u in units if u.volume == volume]
    costed_pages = sum(u.pages for u in vol_units)
    images = sum(u.images for u in vol_units)

    print(
        f"\n== Vol. {volume}: {len(passed)} of {len(stats)} titles passed, "
        f"{passed_pages} of {sum(s.pages for s in stats)} pages"
    )
    if not passed:
        return total, 0, 0, 0
    print(
        f"   groups {total.groups} (+{total.added} added in review), "
        f"reviewed {total.reviewed}/{total.groups}"
    )
    print(
        f"   speaker corrections {total.corrections} ({pct(total.corrections, total.groups)}), "
        f"nephew domain {total.nephew_corrections} of {total.nephew_groups} "
        f"({pct(total.nephew_corrections, total.nephew_groups)})"
    )
    rate = f"{images / costed_pages:.2f} per page" if costed_pages else "not recorded"
    print(f"   images {images} over {costed_pages} costed pages = {rate}")

    print(
        f"\n   {'title':<{TITLE_WIDTH}} {'pages':>5} {'groups':>6} {'added':>5} "
        f"{'reviewed':>8} {'corr':>4} {'rate':>6}  images/page"
    )
    for stat in passed:
        t = tallies[stat.title]
        pages = str(stat.pages) if stat.read == stat.pages else f"{stat.read}/{stat.pages}"
        print(
            f"   {stat.title[:TITLE_WIDTH]:<{TITLE_WIDTH}} {pages:>5} {t.groups:>6} {t.added:>5} "
            f"{t.reviewed:>8} {t.corrections:>4} {pct(t.corrections, t.groups):>6}  "
            f"{title_cost(stat.title, units)}"
        )

    left = [s for s in stats if s.read < s.pages]
    if left:
        print(
            f"\n   left: {len(left)} title(s), {sum(s.pages - s.read for s in left)} page(s)"
            f" -- next {left[0].title!r}"
        )
    return total, passed_pages, costed_pages, images


def main() -> None:
    """Print the summary for the volumes named on the command line."""
    volumes = parse_volumes(sys.argv[1:])
    if not volumes:
        print(__doc__)
        sys.exit(2)

    logger.remove()
    logger.add(sys.stderr, level="ERROR")

    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    all_stats = scan_titles(comics_database, speech_groups)
    stats = [s for s in all_stats if s.volume in volumes]
    units = load_ledger(LEDGER)

    known = {s.title for s in all_stats}
    for unit in units:
        for title in unit.titles:
            if title not in known:
                print(f"!! ledger title not found in the corpus: {title!r}")

    logger.disable("barks_fantagraphics")
    try:
        tallies = {s.title: tally_title(comics_database, speech_groups, s) for s in stats if s.read}
    finally:
        logger.enable("barks_fantagraphics")

    grand = Tally()
    passed_pages = costed_pages = images = 0
    for volume in volumes:
        total, p, c, i = report_volume(
            volume, [s for s in stats if s.volume == volume], tallies, units
        )
        grand.add(total)
        passed_pages, costed_pages, images = passed_pages + p, costed_pages + c, images + i

    if len(volumes) > 1:
        rate = f"{images / costed_pages:.2f} per page" if costed_pages else "not recorded"
        print(
            f"\n== All {len(volumes)} volumes: {passed_pages} pages passed, {grand.groups} groups, "
            f"{grand.corrections} corrections ({pct(grand.corrections, grand.groups)}), "
            f"reviewed {grand.reviewed}/{grand.groups}, images {images}/{costed_pages} = {rate}"
        )


if __name__ == "__main__":
    main()

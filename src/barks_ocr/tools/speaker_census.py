# ruff: noqa: T201
"""Census of the speaker attributions recorded across the prelim OCR corpus.

``vision_apply`` and the kivy editor both canonicalize what they write, but a
free-form ``other:`` name is still only text: two spellings of one character
remain two speakers and nothing downstream reconciles them.  This walks the
corpus and prints what has actually accumulated — counts per name, spellings
that differ only in case, and the names recurring often enough to be worth
promoting into the roster in ``utils/vision_schema.py``.

Read-only.  It reports what a human should decide about; it changes nothing.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Annotated, Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.fanta_comics_info import FIRST_VOLUME_NUMBER, LAST_VOLUME_NUMBER
from barks_fantagraphics.speech_groupers import SpeechGroups
from comic_utils.common_typer_options import TitleArg, VolumesArg
from intspan import intspan

from barks_ocr.utils.vision_schema import (
    OTHER_PREFIX,
    ROSTER,
    SPEAKER_KEY,
    normalize_speaker,
    speaker_key,
)

app = typer.Typer()

# A free-form name seen this often is no longer a one-off. Promoting it to the
# roster makes it exact-matched, so its spelling can no longer drift.
DEFAULT_PROMOTE_AT = 10

# How many places to name when listing where a spelling was used.
MAX_SHOWN_OCCURRENCES = 4


@dataclass(frozen=True)
class Occurrence:
    """Where one speaker value was found."""

    volume: int
    fanta_page: str
    engine: str
    group_id: str

    def __str__(self) -> str:
        """Return the compact 'vol 1 p077 easyocr g3' form used in the report."""
        return f"vol {self.volume} p{self.fanta_page} {self.engine} g{self.group_id}"


def _collect(
    comics_database: ComicsDatabase, speech_groups: SpeechGroups, title_list: list[str]
) -> dict[str, list[Occurrence]]:
    """Return every stored speaker value mapped to where it occurs."""
    found: dict[str, list[Occurrence]] = defaultdict(list)
    for title_str in title_list:
        title = STR_TITLE_TO_ENUM[title_str]
        volume = comics_database.get_fanta_volume_int(title_str)
        for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True):
            for group_id, group in page_group.speech_page_json.get("groups", {}).items():
                speaker = group.get(SPEAKER_KEY)
                if isinstance(speaker, str) and speaker:
                    found[speaker].append(
                        Occurrence(
                            volume, page_group.fanta_page, page_group.ocr_index.value, group_id
                        )
                    )
    return found


def _print_counts(heading: str, counts: list[tuple[str, int]]) -> None:
    if not counts:
        return
    print(f"\n{heading}")
    width = max(len(name) for name, _ in counts)
    for name, count in counts:
        print(f"  {name.ljust(width)}  {count:5d}")


def _by_count(pairs: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Sort by descending count, then by name so equal counts are stable."""
    return sorted(pairs, key=lambda kv: (-kv[1], kv[0]))


def _print_variants(found: dict[str, list[Occurrence]]) -> bool:
    """Print spellings that collapse onto one speaker. Returns whether any exist."""
    by_key: dict[str, list[str]] = defaultdict(list)
    for speaker in found:
        by_key[speaker_key(speaker)].append(speaker)
    variants = {key: spellings for key, spellings in by_key.items() if len(spellings) > 1}
    if not variants:
        return False

    print("\nVariant spellings — one speaker recorded more than one way:")
    for key in sorted(variants):
        print(f'  "{key}"')
        for spelling in sorted(variants[key]):
            places = found[spelling]
            shown = ", ".join(str(o) for o in places[:MAX_SHOWN_OCCURRENCES])
            more = (
                f", +{len(places) - MAX_SHOWN_OCCURRENCES} more"
                if len(places) > MAX_SHOWN_OCCURRENCES
                else ""
            )
            print(f"    {spelling!r:40} {len(places):4d}   {shown}{more}")
    return True


def _print_anomalies(found: dict[str, list[Occurrence]]) -> bool:
    """Print values that are off-roster or not in canonical form. Returns whether any exist."""
    off_roster = [s for s in found if s not in ROSTER and not s.startswith(OTHER_PREFIX)]
    non_canonical = [s for s in found if s != normalize_speaker(s)]
    if off_roster:
        print("\nOff-roster values — neither a roster name nor an 'other:' name:")
        for speaker in _by_count([(s, len(found[s])) for s in off_roster]):
            print(f"  {speaker[0]!r:40} {speaker[1]:5d}   {found[speaker[0]][0]}")
    if non_canonical:
        print("\nNot in canonical form — written before normalization, or by hand:")
        for speaker in sorted(non_canonical):
            print(f"  {speaker!r:40} -> {normalize_speaker(speaker)!r}")
    return bool(off_roster or non_canonical)


def _report(found: dict[str, list[Occurrence]], promote_at: int) -> None:
    """Print the whole census."""
    total = sum(len(places) for places in found.values())
    if not total:
        print("No speaker attributions recorded yet.")
        return

    by_engine = Counter(o.engine for places in found.values() for o in places)
    engines = ", ".join(f"{count} {engine}" for engine, count in sorted(by_engine.items()))
    print(f"{total} group(s) carry a speaker across {len(found)} distinct value(s): {engines}.")
    print("Both engines are counted — a line annotated on each is counted twice.")

    _print_counts("Roster", _by_count([(s, len(p)) for s, p in found.items() if s in ROSTER]))

    free_form = {s: p for s, p in found.items() if s.startswith(OTHER_PREFIX)}
    # Quoted, so a name stored with stray whitespace is visible as such here and
    # not merely mentioned further down.
    _print_counts(
        f'Free-form ("{OTHER_PREFIX}")',
        _by_count([(repr(s[len(OTHER_PREFIX) :]), len(p)) for s, p in free_form.items()]),
    )

    # Totalled across spellings, so a name split three ways still reads as one.
    totals: dict[str, int] = defaultdict(int)
    for speaker, places in free_form.items():
        totals[speaker_key(speaker)] += len(places)
    candidates = _by_count([(k, n) for k, n in totals.items() if n >= promote_at])
    if candidates:
        print(f"\nPromotion candidates (>= {promote_at} uses) — worth a roster entry:")
        for name, count in candidates:
            print(f"  {name[len(OTHER_PREFIX) :]!r:40} {count:5d}")
        print("  Add to SPEAKER_OPTIONS in utils/vision_schema.py; roster.txt regenerates.")

    flagged = _print_variants(found)
    flagged = _print_anomalies(found) or flagged
    if not flagged:
        print("\nNo variant spellings and nothing off-roster.")


@app.command(help="Report the speaker attributions accumulated across the prelim OCR corpus.")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    promote_at: Annotated[
        int,
        typer.Option("--promote-at", help="Free-form uses at which to suggest a roster entry."),
    ] = DEFAULT_PROMOTE_AT,
) -> None:
    if volumes_str and title_str:
        msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(msg)

    comics_database = ComicsDatabase()
    # A census over everything is the useful default, so an unqualified run means
    # the whole corpus. `get_titles` asserts on an empty volume list, so the range
    # has to be spelled out rather than left to it.
    if volumes_str:
        volumes: list[Any] = list(intspan(volumes_str))
    elif title_str:
        volumes = []
    else:
        volumes = list(range(FIRST_VOLUME_NUMBER, LAST_VOLUME_NUMBER + 1))
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    speech_groups = SpeechGroups(comics_database)
    found = _collect(comics_database, speech_groups, title_list)

    print(f"Speaker census over {len(title_list)} title(s).")
    _report(found, promote_at)


if __name__ == "__main__":
    app()

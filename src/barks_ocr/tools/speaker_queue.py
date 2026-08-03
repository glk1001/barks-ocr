# ruff: noqa: T201
"""Build a kivy-editor review queue from the speaker calls already in the corpus.

``vision_apply --queue-speakers`` writes a queue as a side effect of applying a
run, which is the right thing while a title is being read. It cannot answer the
other question: *given everything already annotated, what should be looked at
next?*

Two things make that a separate tool rather than a flag.

It reads the **corpus**, not a ``vision_prep`` out-dir. Those out-dirs are
scratch, and the five trial titles' ``result.json`` files no longer validate at
all now that ``identified_by`` is required -- so their queues cannot be
regenerated through ``vision_apply`` even in principle. Anything already on disk
is still queryable.

And it **samples**. A flat queue over one selector is dominated by whatever the
corpus happens to hold a lot of: the trial's 197 ``other:`` calls are 67% one
title, and three names are 55% of them, so auditing them all would mostly re-ask
one question about one story. ``--per-name`` asks the useful question instead --
which *kinds* of call are unreliable -- by taking a few of each distinct name.

```bash
barks-ocr-speaker-queue --other --per-name 3 --out ~/barks-vision/other-audit.txt
barks-ocr-speaker-queue --volume 6 --confidence low,medium
barks-ocr-speaker-queue --collective --unreviewed --per-title 10
barks-ocr-speaker-queue --speaker none,narrator --per-title 8
```

Read-only apart from the queue file it writes.
"""

import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from comic_utils.common_typer_options import TitleArg, VolumesArg

from barks_ocr.utils.title_selection import resolve_titles
from barks_ocr.utils.vision_schema import (
    IDENTIFIED_BY_KEY,
    NEPHEW_NAMES,
    OTHER_PREFIX,
    SPEAKER_CONFIDENCE_KEY,
    SPEAKER_KEY,
    SPEAKER_REVIEWED_KEY,
    VISION_SPEAKER_ISSUE,
    speaker_key,
)

app = typer.Typer()

# Free-form names whose risk is not "the wrong character". A collective can
# hardly be given to the wrong one, and an animal is really a test of the
# convention that it reaches `characters` only when the art gives it a balloon.
# Grouping the queue by this makes a partial review still a complete answer for
# the kinds already walked, rather than a random slice of everything.
COLLECTIVE_HINTS = ("crowd", "crows", "players", "people", "boys", "men")
ANIMAL_HINTS = ("horse", "goat", "kitten", "dog", "cat", "owl", "squirrel", "skunk")


@dataclass(frozen=True)
class Call:
    """One stored speaker call, and where it lives."""

    volume: int
    fanta_page: str
    group_id: str
    title: str
    speaker: str
    reviewed: bool
    confidence: str | None
    has_evidence: bool

    def line(self, engine: str) -> str:
        """Return the queue-file line for this call."""
        return f"{self.volume} {self.fanta_page} {engine} {self.group_id} {VISION_SPEAKER_ISSUE}"


def _kind(name: str) -> str:
    """Return the risk class of one free-form speaker name."""
    lowered = name.lower()
    if any(h in lowered for h in COLLECTIVE_HINTS):
        return "collective"
    if any(h in lowered for h in ANIMAL_HINTS):
        return "animal"
    # A name a reader could look up has a capital past the first word, or starts
    # with one that is not an article. Everything else is a role: "the sheriff".
    words = name.split()
    if any(w[:1].isupper() for w in words[1:]) or (words and words[0][:1].isupper()):
        return "named one-off"
    return "unnamed role"


def _collect(
    comics_database: ComicsDatabase,
    speech_groups: SpeechGroups,
    titles: list[str],
    engine: OcrTypes,
) -> list[Call]:
    """Return every stored speaker call across *titles*."""
    calls: list[Call] = []
    for title_str in titles:
        title = STR_TITLE_TO_ENUM[title_str]
        volume = comics_database.get_fanta_volume_int(title_str)
        for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True):
            if page_group.ocr_index != engine:
                continue
            for group_id, group in page_group.speech_page_json.get("groups", {}).items():
                speaker = group.get(SPEAKER_KEY)
                if not speaker:
                    continue
                calls.append(
                    Call(
                        volume=volume,
                        fanta_page=page_group.fanta_page,
                        group_id=group_id,
                        title=title_str,
                        speaker=speaker,
                        reviewed=bool(group.get(SPEAKER_REVIEWED_KEY)),
                        confidence=group.get(SPEAKER_CONFIDENCE_KEY),
                        has_evidence=bool(group.get(IDENTIFIED_BY_KEY)),
                    )
                )
    return calls


@dataclass(frozen=True)
class Selectors:
    """Which calls a run wants. Every field defaults to "do not filter"."""

    other: bool = False
    collective: bool = False
    nephews: bool = False
    unreviewed: bool = False
    missing_evidence: bool = False
    confidences: frozenset[str] = frozenset()
    # Compared as `speaker_key`, the same canonical form the census groups on, so
    # `--speaker donald` finds `Donald` and `--speaker other:Donald` finds it too.
    speakers: frozenset[str] = frozenset()

    def keeps(self, call: Call) -> bool:
        """Return whether *call* survives every selector.

        Written as the reasons to reject rather than a chain of guards, so
        adding a selector is one line and the "unset means do not filter"
        contract stays visible in each row.
        """
        rejected = (
            self.other and not call.speaker.startswith(OTHER_PREFIX),
            self.collective and call.speaker != "nephews",
            self.nephews and call.speaker not in NEPHEW_NAMES,
            self.speakers and speaker_key(call.speaker) not in self.speakers,
            self.unreviewed and call.reviewed,
            # `none` is exempt from `identified_by` in the validator -- nobody
            # said it, so there is no evidence to name -- and a queue that offers
            # those groups anyway disagrees with the schema and pads the backlog
            # by 156 groups nobody should open.
            self.missing_evidence and (call.has_evidence or call.speaker == "none"),
            self.confidences and call.confidence not in self.confidences,
        )
        return not any(rejected)


def _cap(calls: list[Call], bucket: Callable[[Call], str], limit: int) -> list[Call]:
    """Keep at most *limit* calls per bucket, spread across pages.

    Unreviewed first, then evenly through the pages rather than clustered on
    one: three calls from a single page test one panel, not one bucket.
    """
    grouped: dict[str, list[Call]] = defaultdict(list)
    for call in calls:
        grouped[bucket(call)].append(call)

    picked: list[Call] = []
    for rows in grouped.values():
        # Numeric on the group id, matching how the queue lines are ordered:
        # sorted as text, group 10 would come before group 5 and the sample
        # would depend on an ordering nobody intended.
        rows.sort(key=lambda c: (c.reviewed, c.fanta_page, int(c.group_id)))
        step = max(1, len(rows) // limit)
        picked.extend(rows[::step][:limit])
    return picked


def _sample(calls: list[Call], per_name: int, per_title: int) -> list[Call]:
    """Thin the queue so no one bucket dominates it.

    **Which bucket depends on the population**, and getting that wrong makes the
    flag useless rather than merely suboptimal.

    ``--per-name`` is right when many speakers share a queue and one of them is
    most of it: the free-form calls are 22 names of which one is 54 of 197, so
    capping per name covers every name in a fraction of the groups.

    ``--per-title`` is right when the queue is **one** speaker and the thing that
    varies is the story. The collective is the case: `nephews` is a single value,
    so ``--per-name`` would return that many calls in total and nothing else --
    but Sheriff is 47 of the 102, and whether the collective was the right answer
    depends almost entirely on how a title draws its caps. Billions draws them
    capless throughout so the collective is forced; Sheriff's are readable on
    many pages, which is where over-caution would show. Sampling per title puts
    each drawing style in the sample.

    Given both, the caps apply in turn -- name first, then title -- so the title
    cap is exact and the name cap is an upper bound.
    """
    if per_name > 0:
        calls = _cap(calls, lambda c: c.speaker, per_name)
    if per_title > 0:
        calls = _cap(calls, lambda c: c.title, per_title)
    return calls


@app.command(help="Build a kivy-editor speaker-review queue from what is already annotated.")
def main(  # noqa: PLR0913
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    out: Annotated[Path, typer.Option("--out", "-o", help="Queue file to write.")] = Path(
        "speaker-queue.txt"
    ),
    engine_str: Annotated[
        str, typer.Option("--engine", help="Which engine's calls to queue.")
    ] = OcrTypes.EASYOCR.value,
    other: Annotated[bool, typer.Option("--other", help=f'Only "{OTHER_PREFIX}" names.')] = False,
    collective: Annotated[
        bool, typer.Option("--collective", help='Only the "nephews" collective.')
    ] = False,
    nephews: Annotated[
        bool, typer.Option("--nephews", help="Only individually-named nephews.")
    ] = False,
    speakers: Annotated[
        str,
        typer.Option(
            "--speaker",
            help="Comma-separated speaker values, e.g. 'none,narrator' or 'Donald'."
            " The general form of the three flags above.",
        ),
    ] = "",
    confidences: Annotated[
        str, typer.Option("--confidence", help="Comma-separated confidences to include.")
    ] = "",
    unreviewed: Annotated[
        bool, typer.Option("--unreviewed", help="Skip calls a human has already confirmed.")
    ] = False,
    per_name: Annotated[
        int,
        typer.Option(
            "--per-name",
            help="Sample at most this many of each distinct speaker. 0 takes everything.",
        ),
    ] = 0,
    per_title: Annotated[
        int,
        typer.Option(
            "--per-title",
            help="Sample at most this many from each title. Use for single-speaker"
            " queues like --collective, where --per-name has nothing to spread across.",
        ),
    ] = 0,
    missing_evidence: Annotated[
        bool,
        typer.Option("--missing-evidence", help=f"Only calls with no {IDENTIFIED_BY_KEY}."),
    ] = False,
) -> None:
    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    titles = resolve_titles(comics_database, volumes_str, title_str)
    engine = OcrTypes(engine_str)

    calls = _collect(comics_database, speech_groups, titles, engine)
    annotated = len(calls)

    selectors = Selectors(
        other=other,
        collective=collective,
        nephews=nephews,
        unreviewed=unreviewed,
        missing_evidence=missing_evidence,
        confidences=frozenset(c.strip() for c in confidences.split(",") if c.strip()),
        speakers=frozenset(speaker_key(s.strip()) for s in speakers.split(",") if s.strip()),
    )
    kept = [c for c in calls if selectors.keeps(c)]

    if not kept:
        # A mistyped --speaker is the likely cause and the fix is knowing what is
        # actually stored, so say so rather than leaving the caller to guess.
        print("No calls match those selectors. Speaker values present:")
        for value, count in Counter(c.speaker for c in calls).most_common():
            print(f"  {count:>4}  {value}")
        raise typer.Exit(code=1)
    calls = kept

    selected = _sample(calls, per_name, per_title)

    # Grouped by risk class, so stopping half way still leaves a complete answer
    # for the kinds already walked rather than a random half of everything.
    by_kind: dict[str, list[Call]] = defaultdict(list)
    for call in selected:
        name = call.speaker[len(OTHER_PREFIX) :] if call.speaker.startswith(OTHER_PREFIX) else ""
        by_kind[_kind(name) if name else "roster"].append(call)

    lines = [f"# vision-check speaker review -- {annotated} annotated, {len(selected)} queued"]
    tally: Counter[str] = Counter()
    for kind in ("named one-off", "unnamed role", "collective", "animal", "roster"):
        rows = by_kind.get(kind, [])
        if not rows:
            continue
        lines.append(f"# --- {kind} ---")
        for call in sorted(rows, key=lambda c: (c.volume, c.fanta_page, int(c.group_id))):
            lines.append(call.line(engine.value))
            tally[f"{kind}: {call.speaker}"] += 1

    out.expanduser().write_text("\n".join(lines) + "\n")

    print(f"{annotated} annotated call(s) across {len(titles)} title(s); {len(selected)} queued.")
    for label, count in sorted(tally.items()):
        print(f"  {count:>3}  {label}")

    # Also by title, since a single-speaker queue -- the collective is the case --
    # collapses the breakdown above to one uninformative line, and the title is
    # then the axis the sample was actually spread across.
    per_title_tally = Counter(call.title for call in selected)
    available = Counter(call.title for call in calls)
    if len(per_title_tally) > 1:
        print("\n  by title:")
        for title_name, count in sorted(per_title_tally.items()):
            of = available[title_name]
            suffix = f" of {of}" if count != of else ""
            print(f"    {count:>3}{suffix:<8}  {title_name}")
    print(f'\nWrote "{out}".')
    print(f"  uv run barks-ocr-kivy-editor -- --queue-file {out}")


if __name__ == "__main__":
    sys.exit(app())

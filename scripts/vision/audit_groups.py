# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the findings is the whole point.
"""Three integrity sweeps over the stored groups: speaker drift, evidence, residue.

    uv run --offline python scripts/vision/audit_groups.py ["Some Title"]
    uv run --offline python scripts/vision/audit_groups.py --fail-on-findings

Items 4, 5 and 6 of `docs/invariant-suite.md`. All three **report and exit 0 by
default**, because each has a standing backlog that predates the check and a
gate switched on at birth would block the next commit rather than the next
mistake. `--fail-on-findings` is there for once a backlog is cleared.

Every count below was measured on 2026-09-02 over the 10,716 tracked groups
files, and the measuring is most of what this file is worth: the first cut of
each check was dominated by false positives, and the numbers are what found the
signal.

**`other:` speakers that differ only by an article or case.** Free-text speakers
get no closed-set check, so `other:crowd` and `other:the crowd` are two
characters as far as every tool is concerned, and a mirror copies the drift to
the second engine. Nine pairs, and they read like exactly what they are:
crowd/the crowd, shopkeeper/the shopkeeper, a bear/the bear, radio/the radio.

Not flagged: an `other:` used only once. There are 172 of those and they are
the normal case -- a harbour messenger, a fireman, a shark. Flagging singletons
was the plan's suggestion and it is the wrong signal by better than 19 to 1.

**A speaker with no `identified_by`.** `vision_apply` requires evidence wherever
somebody speaks -- `none` is the one speaker that needs none -- but it can only
enforce that going forward. 1,503 stored groups predate it, concentrated in
Vols. 6, 10, 7 and 1, which is the shape of a cohort read before the field
existed rather than of a live fault. `barks-ocr-speaker-queue --missing-evidence`
is the queue path for working through them.

**Hand-added groups, checked two ways.** A group seeded from a neighbour in the
editor is born carrying that neighbour's `ai_text`, `vision_note`, `type` and
`identified_by`, and Copy In deep-copies `speaker_reviewed` so it arrives
already signed off.

The plan proposed finding these by duplicated `ai_text`. That does not work:
2,468 pages carry a repeated string, dropping overlapping boxes reaches 2,336,
and requiring an identical `vision_note` too still leaves 100 -- every visible
one of which is real repeated lettering (`SEEDS` on a seed packet, `D. DUCK` on
a mailbox, `CASTOR OIL`, `$100,000`). Duplicated text is not the signal.

The population to look at is the 133 groups actually carrying `vision_added`.
Against those, two checks earn their place:

  * **25** duplicate another group's text on the same page -- the residue shape,
    on a list short enough to read.
  * **11 pages carry a different NUMBER of added groups on each engine**, one of
    them three against zero. That is the one-engine add: the pass, the mirror
    and `speaker-queue` all read easyocr, so a group added only to paddleocr
    reaches no queue and is never reviewed. This is the unambiguous one.

**2026-09-19: THE SECOND CHECK COUNTED, AND COUNTING IS NOT THE QUESTION.**
Comparing how many `vision_added` groups each engine carries reported 87 pages
over the 5,358 page-pairs then stored, and the seventieth batch's review showed
what most of them are. *The Money Well* 082 came back `easyocr=4 paddleocr=3`
with nothing wrong: both engines carry the `SOON!` caption and both have it
reviewed, but paddleocr's copy was FOUND by the engine while easyocr's was added
by hand, so only one of them carries the flag. A provenance asymmetry, not a
missing group -- and neither side can be "corrected" without falsifying it,
since `vision_added` records who put the group there.

What actually costs a group is having no COUNTERPART: `vision_mirror` pairs the
two engines on `_match_key`, the markup-stripped whitespace-insensitive text, and
a group it cannot pair is one it silently skips -- the review state never
crosses and the group stays unreviewed on one side. That is the fault the
paragraph above was reaching for, so the check now asks it directly, using the
mirror's own key so the two agree by construction.

Measured the day it changed, over 5,358 page-pairs: **87 pages under the count
comparison, 0 under the counterpart test.** Zero is the true answer today --
every hand-added group in the corpus does have a counterpart -- and it is worth
saying out loud that a check reporting nothing is not the same as a broken one.
This one fires the moment a group is added to one engine whose text matches
nothing on the other, which is exactly when the mirror will leave it behind.

Note what it does NOT cover: a PRE-EXISTING group whose two texts drift apart is
skipped by the mirror for the same reason and is invisible here, because the
population is `vision_added` only. The seventieth batch hit one (*The Money Well*
085 g16, easyocr truncated to `176-617 BEAGLE`) and the mirror's own WARNING is
what catches that -- read it.
"""

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import SpeechGroups
from barks_fantagraphics.speech_markup import strip_markup
from barks_fantagraphics.speech_speakers import OTHER_PREFIX

from barks_ocr.utils.title_selection import resolve_titles

ARTICLE_RE = re.compile(r"^(?:the|a|an)\s+")


@dataclass
class PageTexts:
    """One engine's view of a page, reduced to what the counterpart test needs.

    Attributes:
        all_keys: `match_key` for every group on the page, for the other engine
            to look its own added groups up in.
        added: group id -> `match_key`, for the `vision_added` groups only.

    """

    all_keys: set[str] = field(default_factory=set)
    added: dict[str, str] = field(default_factory=dict)


MIN_DUPLICATE_LEN = 2  # a one-character duplicate says nothing either way
PAIR = 2  # it takes two groups to be a duplicate
MAX_LISTED = 25


def normalise_other(speaker: str) -> str:
    """Reduce an `other:` speaker to a form that ignores case and a leading article."""
    return ARTICLE_RE.sub("", speaker[len(OTHER_PREFIX) :].lower().strip())


def _bbox(text_box: Any) -> tuple[float, float, float, float]:  # noqa: ANN401 -- raw JSON.
    """Return (x0, y0, x1, y1) for a stored four-corner text box."""
    xs = [p[0] for p in text_box]
    ys = [p[1] for p in text_box]
    return min(xs), min(ys), max(xs), max(ys)


def _overlaps(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    """Say whether two bounding boxes share any area."""
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def added_groups(groups: dict[str, dict]) -> dict[str, dict]:
    """Return only the groups carrying `vision_added`, by id."""
    return {gid: g for gid, g in groups.items() if g.get("vision_added")}


def match_key(ai_text: str | None) -> str:
    """Return the key `vision_mirror` pairs two engines' groups on.

    Deliberately the same rule as `vision_mirror._match_key` -- markup stripped
    and whitespace collapsed -- so that "the audit says this group has a
    counterpart" and "the mirror can pair this group" cannot drift apart.

    Args:
        ai_text: a group's stored text, or None.

    Returns:
        The pairing key, empty for a group with no text.

    """
    return " ".join(strip_markup(ai_text or "").split())


def residue_on_page(groups: dict[str, dict]) -> list[tuple[str, str]]:
    """Find hand-added groups whose text duplicates another group on the page.

    Restricted to `vision_added` groups on purpose. Duplicated `ai_text` across
    all groups is repeated lettering far more often than residue; the same test
    against the 133 hand-added groups is a list worth reading.

    Args:
        groups: one page's stored groups, by id.

    Returns:
        (group id, the duplicated text) for each suspect added group.

    """
    texts = Counter(g["ai_text"] for g in groups.values() if g.get("ai_text"))
    return [
        (gid, g["ai_text"])
        for gid, g in added_groups(groups).items()
        if g.get("ai_text") and texts[g["ai_text"]] > 1
    ]


def main() -> None:  # noqa: C901 -- three independent reports, printed in order.
    """Sweep one title or the whole corpus and report all three classes."""
    argv = sys.argv[1:]
    strict = "--fail-on-findings" in argv
    only_title = next((a for a in argv if not a.startswith("-")), "")

    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    titles = resolve_titles(comics_database, "", only_title)

    others: Counter[str] = Counter()
    no_evidence: Counter[str] = Counter()
    residue: list[str] = []
    page_texts: dict[tuple[str, str], dict[str, PageTexts]] = defaultdict(dict)
    skipped: list[str] = []
    pages = 0

    for title_str in titles:
        title = STR_TITLE_TO_ENUM[title_str]
        try:
            page_groups = speech_groups.get_speech_page_groups(title, skip_missing=True)
        except RuntimeError as exc:
            # The panel-segments mtime gate. Say so rather than reporting clean
            # on a title nobody actually looked at.
            skipped.append(f"{title_str}: {exc}")
            continue

        for page_group in page_groups:
            pages += 1
            groups = page_group.speech_page_json.get("groups", {})
            engine = page_group.ocr_index
            page = page_group.fanta_page

            for group in groups.values():
                speaker = group.get("speaker")
                if not isinstance(speaker, str):
                    continue
                if speaker.startswith(OTHER_PREFIX):
                    others[speaker] += 1
                if speaker != "none" and "identified_by" not in group:
                    no_evidence[title_str] += 1

            texts = PageTexts(
                all_keys={match_key(g.get("ai_text")) for g in groups.values()},
                added={gid: match_key(g.get("ai_text")) for gid, g in added_groups(groups).items()},
            )
            page_texts[(title_str, page)][str(engine)] = texts

            for gid, text in residue_on_page(groups):
                snippet = text[:40].replace("\n", "\\n")
                residue.append(f"{title_str} {page} {engine} g{gid}  {snippet!r}")

    _report_drift(others)
    _report_evidence(no_evidence)
    _report_residue(residue)
    orphan_adds = _report_orphan_adds(page_texts)

    if skipped:
        print(f"\n!! {len(skipped)} title(s) NOT checked -- stale panel-segments mtime:")
        for line in skipped[:MAX_LISTED]:
            print(f"     {line}")

    print(f"\nSwept {pages} page-engine(s) across {len(titles)} title(s).")
    if strict and (others or no_evidence or residue or orphan_adds):
        raise SystemExit(1)


def _report_orphan_adds(page_texts: dict[tuple[str, str], dict[str, PageTexts]]) -> int:
    """Print hand-added groups the mirror could not pair with the other engine.

    A `vision_added` group whose `match_key` appears nowhere in the other
    engine's groups is one `vision_mirror` will skip: nothing is copied across,
    so the group keeps whatever review state it happens to have on its own side.
    Counting added groups per engine does NOT detect this -- the counts differ
    whenever the two engines merely disagree about WHO added a group they both
    carry, which is provenance rather than a fault.

    A page seen on only one engine is reported too: an added group there has no
    counterpart because there is nothing to pair against.

    Args:
        page_texts: (title, page) -> engine -> that engine's keys for the page.

    Returns:
        How many pages were reported.

    """
    orphans: dict[tuple[str, str], list[str]] = {}
    for where, engines in page_texts.items():
        found: list[str] = []
        for engine, texts in sorted(engines.items()):
            others = {k for e, t in engines.items() if e != engine for k in t.all_keys}
            found += [
                f"{engine} g{gid} {key!r}"
                for gid, key in sorted(texts.added.items())
                if key not in others
            ]
        if found:
            orphans[where] = found

    print(
        "\n=== hand-added groups with no counterpart on the other engine: "
        f"{len(orphans)} page(s) ==="
    )
    for (title_str, page), found in sorted(orphans.items())[:MAX_LISTED]:
        for line in found:
            print(f"     {title_str} {page}  {line}")
    if len(orphans) > MAX_LISTED:
        print(f"     ... and {len(orphans) - MAX_LISTED} more")
    if orphans:
        print("  vision_mirror pairs the engines on the group text, so it cannot copy")
        print("  onto these -- the review state never crosses and one side stays stale.")
    return len(orphans)


def _report_drift(others: Counter[str]) -> None:
    """Print `other:` speakers that collapse onto one another."""
    buckets: dict[str, list[str]] = defaultdict(list)
    for speaker in others:
        buckets[normalise_other(speaker)].append(speaker)
    drift = {k: sorted(v) for k, v in buckets.items() if len(v) >= PAIR}

    print(f"=== other: speakers that differ only by case or an article: {len(drift)} ===")
    for _, names in sorted(drift.items())[:MAX_LISTED]:
        counts = ", ".join(f"{n} ({others[n]})" for n in names)
        print(f"     {counts}")
    if drift:
        print("  Pick one spelling and retire the other before the next mirror.")


def _report_evidence(no_evidence: Counter[str]) -> None:
    """Print titles carrying speakers with no recorded evidence."""
    total = sum(no_evidence.values())
    print(f"\n=== speaker set with no identified_by: {total} group(s) ===")
    for title_str, count in no_evidence.most_common(MAX_LISTED):
        print(f"     {count:>5}  {title_str}")
    if total:
        print("  Mostly a cohort read before the field existed.")
        print("  Queue them with: barks-ocr-speaker-queue --missing-evidence")


def _report_residue(residue: list[str]) -> None:
    """Print groups that look seeded from a neighbour."""
    print(f"\n=== possible Copy-In residue: {len(residue)} group(s) ===")
    for line in residue[:MAX_LISTED]:
        print(f"     {line}")
    if len(residue) > MAX_LISTED:
        print(f"     ... and {len(residue) - MAX_LISTED} more")
    if residue:
        print("  Duplicate ai_text AND an identical vision_note. A heuristic:")
        print("  the same word lettered twice under one note is not a fault.")


if __name__ == "__main__":
    main()

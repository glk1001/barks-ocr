# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the corrections is the whole point.
"""Collect a finished review's corrections, grouped, ready to be written as rules.

    uv run --offline python scripts/vision/review_findings.py "Some Title"
    uv run --offline python scripts/vision/review_findings.py "Some Title" --since HEAD~4
    uv run --offline python scripts/vision/review_findings.py            # whole corpus

The `### Findings to paste into the next run` block in
`docs/vision-pass-run-prompt.md` is the one input a run needs that nothing
derives — the skill reads the most recent section before page 1, and it is what
stops a corrected error class coming back. It went eight titles and eight days
without an entry, because writing one meant reading a review back out of memory.

It does not. **Every correction is already on disk**: `speaker_was`,
`cap_colour_was` and `type_was` hold what the pass said, the current fields hold
what the review made it, and `vision_note` holds the pass's own reasoning for
getting it wrong. On one measured title the reviewer left a `speaker_review_note`
on 1 correction in 26 — so the reviewer's prose is not the raw material and never
was. The pass's stated reasoning is.

This prints that material grouped by the direction of the correction, which is
what turns a list into a rule: twelve `nephews` -> a name is a different finding
from twelve names -> `nephews`, and both are different from a name swapped for
another name.

WHAT IT CANNOT RECOVER WITHOUT `--since`. A review sets `speaker_confidence` to
`high`, overwriting what the pass wrote, so the medium-against-high correction
rate — the single most useful number in any of these reviews, 31.0% against 7.3%
on *Lost in the Andes!* — is gone from the current state. Pass `--since <ref>`
and it is read from the git blob of the pass's own commit instead.

The output is raw material, not the finding. Reading it and stating the rule is
the judgement, and a rule inferred from a correction can misread WHY it was made.
"""

import json
import subprocess
import sys
from collections import Counter, defaultdict

from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import SpeechGroups

from barks_ocr.utils.title_selection import resolve_titles
from barks_ocr.utils.vision_schema import (
    CAP_COLOUR_KEY,
    CAP_COLOUR_WAS_KEY,
    NEPHEW_NAMES,
    SPEAKER_CONFIDENCE_KEY,
    SPEAKER_KEY,
    SPEAKER_REVIEW_NOTE_KEY,
    SPEAKER_WAS_KEY,
    TYPE_KEY,
    TYPE_WAS_KEY,
    VISION_NOTE_KEY,
)

COLLECTIVE = "nephews"
DONALD = "Donald"

NOTE_CHARS = 88
MAX_PER_CLASS = 12


def classify(was: str, now: str) -> str:
    """Name the shape of one speaker correction.

    The direction is what makes a finding: twelve `nephews` sharpened to names is
    an under-naming rule, twelve names collapsed to `nephews` is the opposite
    one, and a name swapped for another name is a tail-tracing rule. Lumping them
    together as "26 speaker corrections" says nothing.

    Args:
        was: the speaker the pass wrote.
        now: the speaker the review left.

    Returns:
        A short class name for grouping.

    """
    was_nephew, now_nephew = was in NEPHEW_NAMES, now in NEPHEW_NAMES
    nephew_domain = (was_nephew or was == COLLECTIVE, now_nephew or now == COLLECTIVE)
    rules = [
        (was == COLLECTIVE and now_nephew, "nephews -> a name (under-naming)"),
        (was_nephew and now == COLLECTIVE, "a name -> nephews (over-naming)"),
        (was_nephew and now_nephew, "one nephew -> another (attribution)"),
        (was == DONALD and nephew_domain[1], "Donald -> the nephew domain"),
        (nephew_domain[0] and now == DONALD, "the nephew domain -> Donald"),
        (was.startswith("other:") or now.startswith("other:"), "an other: role"),
    ]
    return next((name for hit, name in rules if hit), f"{was} -> {now}")


def _blob_groups(ref: str, path: str) -> dict:
    """Return one groups file's groups at *ref*, or {} when it is not there."""
    proc = subprocess.run(  # noqa: S603 -- fixed argv, no shell.
        ["git", "-C", str(OCR_PRELIM_DIR), "show", f"{ref}:{path}"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return {}
    return json.loads(proc.stdout).get("groups", {})


def main() -> None:  # noqa: C901, PLR0912, PLR0915 -- one report, printed in sections.
    """Print a title's corrections, grouped by direction, with both sides' notes."""
    argv = sys.argv[1:]
    since = argv[argv.index("--since") + 1] if "--since" in argv else ""
    engine = argv[argv.index("--engine") + 1] if "--engine" in argv else "easyocr"
    only_title = next((a for a in argv if not a.startswith("-")), "")

    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    titles = resolve_titles(comics_database, "", only_title)

    groups_seen = 0
    nephew_domain = 0
    by_class: dict[str, list[str]] = defaultdict(list)
    caps: list[str] = []
    types: list[str] = []
    phantom = 0
    was_confidence: Counter[str] = Counter()
    corrected_confidence: Counter[str] = Counter()

    for title_str in titles:
        try:
            page_groups = speech_groups.get_speech_page_groups(
                STR_TITLE_TO_ENUM[title_str], skip_missing=True
            )
        except RuntimeError as exc:
            print(f"!! skipping {title_str}: {exc}")
            continue

        for page_group in page_groups:
            if str(page_group.ocr_index) != engine:
                continue
            page = page_group.fanta_page
            before = {}
            if since:
                rel = str(page_group.ocr_prelim_groups_json_file).replace(
                    str(OCR_PRELIM_DIR) + "/", ""
                )
                before = _blob_groups(since, rel)

            for gid, group in page_group.speech_page_json.get("groups", {}).items():
                groups_seen += 1
                speaker = group.get(SPEAKER_KEY)
                if speaker in NEPHEW_NAMES or speaker == COLLECTIVE:
                    nephew_domain += 1

                old_conf = (before.get(gid) or {}).get(SPEAKER_CONFIDENCE_KEY)
                if old_conf:
                    was_confidence[old_conf] += 1

                if SPEAKER_WAS_KEY in group:
                    was, now = group.get(SPEAKER_WAS_KEY), speaker
                    if was == now:
                        # A `_was` equal to its current value records a
                        # correction that never happened; the editor used to
                        # write these in pairs. Count, do not classify.
                        phantom += 1
                    else:
                        if old_conf:
                            corrected_confidence[old_conf] += 1
                        note = (group.get(VISION_NOTE_KEY) or "").replace("\n", " ")
                        review_note = (group.get(SPEAKER_REVIEW_NOTE_KEY) or "").replace("\n", " ")
                        cap_moved = CAP_COLOUR_WAS_KEY in group
                        line = f"{page} g{gid}: {was!r} -> {now!r}"
                        if cap_moved:
                            line += (
                                f"   [cap {group.get(CAP_COLOUR_WAS_KEY)!r}"
                                f" -> {group.get(CAP_COLOUR_KEY)!r}]"
                            )
                        if note:
                            line += f"\n          pass: {note[:NOTE_CHARS]}"
                        if review_note:
                            line += f"\n          REVIEWER: {review_note[:NOTE_CHARS]}"
                        by_class[classify(str(was), str(now))].append(line)

                if CAP_COLOUR_WAS_KEY in group and SPEAKER_WAS_KEY not in group:
                    caps.append(
                        f"{page} g{gid}: cap {group.get(CAP_COLOUR_WAS_KEY)!r}"
                        f" -> {group.get(CAP_COLOUR_KEY)!r}  (speaker unchanged: {speaker!r})"
                    )
                if TYPE_WAS_KEY in group:
                    types.append(
                        f"{page} g{gid}: {group.get(TYPE_WAS_KEY)!r} -> {group.get(TYPE_KEY)!r}"
                    )

    total = sum(len(v) for v in by_class.values())
    scope = only_title or f"{len(titles)} title(s)"
    print(f"=== {scope} — {engine} — {groups_seen} groups, {nephew_domain} in the nephew domain\n")
    print(f"speaker corrections: {total}", end="")
    if groups_seen:
        print(f"  ({100 * total / groups_seen:.1f}% of groups)", end="")
    if nephew_domain:
        in_domain = sum(len(v) for k, v in by_class.items() if "nephew" in k or "Donald" in k)
        pct = 100 * in_domain / nephew_domain
        print(f", {in_domain} in the nephew domain ({pct:.1f}%)", end="")
    print()

    for name, lines in sorted(by_class.items(), key=lambda kv: -len(kv[1])):
        print(f"\n--- {name}: {len(lines)}")
        for line in lines[:MAX_PER_CLASS]:
            print(f"     {line}")
        if len(lines) > MAX_PER_CLASS:
            print(f"     ... and {len(lines) - MAX_PER_CLASS} more")

    if caps:
        print(f"\n--- cap_colour corrected with the speaker LEFT ALONE: {len(caps)}")
        print("      (the hue was misread but the name survived -- a palette finding,")
        print("       not an attribution one)")
        for line in caps[:MAX_PER_CLASS]:
            print(f"     {line}")

    if types:
        print(f"\n--- type corrections: {len(types)}")
        for line in types[:MAX_PER_CLASS]:
            print(f"     {line}")

    if phantom:
        print(f"\n!! {phantom} group(s) carry a _was equal to the current value.")
        print("   Those record a correction that never happened; do not count them.")

    if since:
        print(f"\n--- correction rate by the confidence the PASS wrote (vs {since})")
        for level in ("high", "medium", "low"):
            n = was_confidence.get(level, 0)
            if not n:
                continue
            bad = corrected_confidence.get(level, 0)
            print(f"     {level:<7} {bad:>4} of {n:>4} corrected  ({100 * bad / n:.1f}%)")
    else:
        print("\n(no --since given, so the pass's own confidences are gone: a review")
        print(" overwrites them with 'high'. Pass --since <the pass's commit> for the")
        print(" medium-against-high rate, which is usually the most useful number here.)")


if __name__ == "__main__":
    main()

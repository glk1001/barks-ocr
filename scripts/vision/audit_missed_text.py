# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing what it found is the whole point of running it.
"""Find lettering a vision pass saw but neither OCR engine ever grouped.

    uv run python scripts/vision/audit_missed_text.py [--title "Some Title"] [--csv out.csv]

The pass already notices this. When it reads a page it transcribes the
non-speech lettering into the page capture's ``visible_text`` -- signs, plates,
sound effects painted into the art. Nothing downstream compares that against the
groups, so lettering neither engine found is recorded and then quietly dropped:
it never becomes a searchable, box-anchored group and never reaches a review
queue. Diffing the two finds the class with no change to the pipeline.

Reads the corpus, not an out-dir, so it still answers for titles whose scratch
directory is long gone. Read-only apart from the optional CSV.

Two filters matter, and they pull in opposite directions:

* **Story-logo echoes are not findings.** Some passes wrote the story logo into
  ``visible_text`` on every page of the run rather than only the splash that
  carries it. On the first corpus sweep that was 63 of 78 raw hits. They are
  suppressed by matching against every ``title``-typed group in the title.
* **Do not clear a hit because the lettering is grouped elsewhere in the
  title.** That is exactly the real case: *The Mad Chemist*'s ``313`` licence
  plate is grouped on page 131 and missed on 128 and 129. Matching is per page.

Found 2026-08-08, after four such gaps turned up by hand in one ten-page title.

Three classes it could NOT see were added 2026-09-16, after a reviewer found five
such groups by hand in one batch while this reported two of them:

* **A sign a character reads aloud.** The balloon contains the sign's words, so a
  membership test says covered while the sign itself was never boxed. Matching is
  now against the lettering groups, not all of them.
* **A sign the art repeats.** Three A-1 PEA-NUTS sacks in one panel, one grouped,
  reads as covered because a set has no multiplicity. Counted now -- which needs
  ``visible_text`` to list a repeated sign once per instance.
* **A drawn device.** ``!``, ``?``, a ring of ``$``. ``normalize`` deletes
  everything that is not a letter or a digit, so these reduced to the empty string
  and were skipped as nothing to compare. ``device_key`` keeps the marks.

Must be run with ``uv run`` from the barks-ocr checkout so the path deps resolve.
"""

import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups, SpeechPageGroup
from barks_fantagraphics.speech_markup import strip_markup, unescape_markup
from loguru import logger

from barks_ocr.utils.title_selection import resolve_titles
from barks_ocr.utils.vision_schema import TYPE_KEY, VISIBLE_TEXT_KEY

CAPTURE_FILE_SUFFIX = "-page-capture.json"
CAPTURE_MODEL_KEY = "capture_model"
TITLE_TYPE = "title"
# Types that are somebody TALKING. Lettering quoted inside one of these is not
# the same thing as the lettering being boxed in the art.
SPEECH_TYPES = frozenset({"dialogue", "thought", "narration"})
IGNORE_FILE = Path(__file__).with_name("missed-text-ignore.txt")
SCOPED_ENTRY_FIELDS = 3  # volume, page, and the lettering itself

# Tuned on the one case that prompted it: FZZZZT! against a grouped FZZZT!
# scores 0.91. The length floor keeps short strings, where a couple of shared
# characters is most of the string, from matching each other by chance.
NEAR_MATCH_RATIO = 0.85
MIN_NEAR_MATCH_LEN = 4

# title, volume, fanta_page, lettering, engines that grouped it (empty = neither)
Finding = tuple[str, int, str, str, list[OcrTypes]]
# ... and the grouped text it nearly matches, for the near-miss class
NearMiss = tuple[str, int, str, str, str]


def normalize(text: str | None) -> str:
    """Reduce lettering to letters and digits for comparison.

    Quote style, dashes, case, line breaks and emphasis markup all differ freely
    between what the art shows and what an engine grouped, and none of those
    differences mean the lettering was missed.

    Accents are FOLDED, not dropped. Stripping them outright made a group carry
    fewer letters than the page capture of the same sign, so the two never
    matched and the item reported as a near miss for ever. Vol. 3 209's hat-shop
    sign is the case that found it: the group spells the name with a macron over
    the e and the capture spells it with a plain double e, which reduced to a
    one-letter difference. An accented E or N is the same case. Measured over
    1838 pages, folding removes that one false near miss and changes nothing
    else.
    """
    folded = unicodedata.normalize("NFKD", strip_markup(unescape_markup(text or "")))
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", folded.upper())


def device_key(text: str | None) -> str:
    r"""Reduce a DRAWN DEVICE to a comparable key, keeping its punctuation.

    ``normalize`` deletes everything that is not a letter or a digit, so a drawn
    device -- a lone ``!``, a ``?``, a row of ``$`` signs -- reduces to the empty
    string and is then skipped as "nothing to compare". The audit could not see
    a device even when the pass had transcribed one, which is how the ring of
    dollar signs round Scrooge's head on *Back to Long Ago!* 102 panel 3 reached
    a reviewer by hand: a device is lettering, it just has no letters.

    Whitespace is dropped so ``$ $ $\n$`` and ``$$$$`` compare equal; a run of
    one repeated mark is collapsed to that mark, because the pass counts a row of
    exclamation marks by eye and the engines do not.
    """
    squashed = re.sub(r"\s+", "", strip_markup(unescape_markup(text or "")))
    if not squashed:
        return ""
    if len(set(squashed)) == 1:
        return squashed[0]
    return squashed


def comparable(text: str | None) -> str:
    """Return the key this lettering matches on: its letters, or its marks if it has none."""
    return normalize(text) or device_key(text)


def load_ignores() -> set[tuple[int | None, str | None, str]]:
    """Read the ignore list as (volume, page, normalized lettering) entries.

    A bare line ignores the lettering wherever it appears; a line led by two
    integers scopes it to one page. Volume and page are None for a bare entry.
    """
    if not IGNORE_FILE.is_file():
        return set()
    entries: set[tuple[int | None, str | None, str]] = set()
    for raw_line in IGNORE_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=2)
        scoped = len(parts) == SCOPED_ENTRY_FIELDS and parts[0].isdigit() and parts[1].isdigit()
        if scoped:
            entries.add((int(parts[0]), parts[1], normalize(parts[2])))
        else:
            entries.add((None, None, normalize(line)))
    return {e for e in entries if e[2]}


def ignored(entries: set[tuple[int | None, str | None, str]], finding: Finding) -> bool:
    """Whether the ignore list covers this finding."""
    _, volume, page, item, _ = finding
    needle = normalize(item)
    return any(
        needle == text and (vol is None or (vol == volume and pg == page))
        for vol, pg, text in entries
    )


def covers(needle: str, grouped: set[str]) -> bool:
    """Whether any grouped text is, or contains, this lettering.

    Containment matters: an engine often folds a sign into a larger group rather
    than giving it one of its own, and that still leaves the lettering findable.
    """
    return any(needle == text or needle in text for text in grouped)


def near_match(needle: str, grouped: set[str]) -> str | None:
    """Return the closest grouped text if one is nearly this lettering, else None.

    The pass transcribes ``visible_text`` by eye, and on a sound effect that means
    counting repeated letters: it wrote ``FZZZZT!`` where the group -- which
    both engines found -- says ``FZZZT!``. That is a wobble in the transcription,
    not lettering anybody missed, and reporting it as a gap sends a reviewer to
    a page where there is nothing to add.

    Held apart from ``covers`` rather than folded into it, and reported as its
    own class: a near match is a guess about which of two readings is right, and
    that is a judgement for a reader, not something to resolve silently.
    """
    if len(needle) < MIN_NEAR_MATCH_LEN:
        return None  # short strings collide by chance
    best = max(grouped, key=lambda text: SequenceMatcher(None, needle, text).ratio(), default="")
    if best and SequenceMatcher(None, needle, best).ratio() >= NEAR_MATCH_RATIO:
        return best
    return None


def index_pages(
    page_groups: list[SpeechPageGroup],
) -> tuple[
    dict[str, dict[OcrTypes, set[str]]],
    dict[str, dict[OcrTypes, Counter[str]]],
    dict[str, dict[OcrTypes, set[str]]],
    dict[str, Path],
    set[str],
]:
    """Fold a title's page groups into per-page lookups.

    ``get_speech_page_groups`` yields one entry per (page, engine), so the
    grouped text has to be collected back into a page before a page's single
    capture can be compared against it.

    Returns, per page per engine: the grouped text, how many groups carry each
    text, and the subset of it grouped as LETTERING rather than as speech -- then
    each page's capture file and the title's story-logo texts.

    The count is what catches a sign the art shows more than once and an engine
    boxed once: *Donald's Pet Service* 103 panel 3 stands three A-1 PEA-NUTS
    sacks side by side and one was grouped, which a set comparison reads as
    covered. The lettering subset is what catches a sign a CHARACTER READS ALOUD,
    where the balloon contains the sign's words and so covers them without the
    sign itself ever being boxed.
    """
    grouped_text: dict[str, dict[OcrTypes, set[str]]] = defaultdict(dict)
    grouped_counts: dict[str, dict[OcrTypes, Counter[str]]] = defaultdict(dict)
    grouped_lettering: dict[str, dict[OcrTypes, set[str]]] = defaultdict(dict)
    capture_files: dict[str, Path] = {}
    logos: set[str] = set()
    for page_group in page_groups:
        page = page_group.fanta_page
        groups = page_group.speech_page_json.get("groups", {})
        engine = page_group.ocr_index
        grouped_text[page][engine] = {comparable(g.get("ai_text")) for g in groups.values()}
        grouped_counts[page][engine] = Counter(
            comparable(g.get("ai_text")) for g in groups.values()
        )
        # Lettering the art itself carries, as against somebody saying it aloud.
        grouped_lettering[page][engine] = {
            comparable(g.get("ai_text"))
            for g in groups.values()
            if g.get(TYPE_KEY) not in SPEECH_TYPES
        }
        capture_files.setdefault(
            page, page_group.ocr_prelim_groups_json_file.parent / (page + CAPTURE_FILE_SUFFIX)
        )
        logos |= {
            normalize(g.get("ai_text")) for g in groups.values() if g.get(TYPE_KEY) == TITLE_TYPE
        }
    logos.discard("")
    return grouped_text, grouped_counts, grouped_lettering, capture_files, logos


def page_capture(capture_file: Path) -> list[str] | None:
    """Return a page's ``visible_text``, or None when there is nothing to check."""
    if not capture_file.is_file():
        return None
    capture = json.loads(capture_file.read_text(encoding="utf-8"))
    if not capture.get(CAPTURE_MODEL_KEY):
        return None  # never vision-passed, so visible_text carries no claim
    return capture.get(VISIBLE_TEXT_KEY) or None


@dataclass(frozen=True)
class PageIndex:
    """One page's grouped text, indexed the three ways the audit needs to ask about it.

    ``per_engine`` is what each engine grouped, ``counts`` is how many groups
    carry each text, and ``lettering`` is the subset grouped as something the ART
    carries rather than as somebody speaking.
    """

    per_engine: dict[OcrTypes, set[str]]
    counts: dict[OcrTypes, Counter[str]]
    lettering: dict[OcrTypes, set[str]]
    every_text: set[str]
    logos: set[str]


def classify(needle: str, item: str, wanted: int, index: PageIndex) -> tuple[str, str, list]:
    """Decide what one piece of ``visible_text`` is; return a verdict, a line and engines.

    Verdicts are ``missing``, ``one-engine``, ``near``, ``suppressed`` and
    ``covered``. For ``near`` the line is the grouped text it nearly matches.

    Two of the cases exist because a set comparison answers the wrong question.
    A sign whose words a CHARACTER READS ALOUD is contained by that balloon, so
    it tests as covered while never having been boxed. And a sign the art shows
    more often than the engines grouped it -- three peanut sacks, one group --
    needs a count, not a membership test.
    """
    have = [engine for engine, texts in index.per_engine.items() if covers(needle, texts)]
    if not have:
        if any(needle == logo or needle in logo or logo in needle for logo in index.logos):
            return "suppressed", item, []
        close = near_match(needle, index.every_text)
        return ("near", close, []) if close else ("missing", item, [])
    if not any(covers(needle, index.lettering[engine]) for engine in have):
        return "missing", f"{item}  [quoted aloud, not boxed]", []
    short = [engine for engine in have if index.counts[engine].get(needle, 0) < wanted]
    if short:
        grouped_n = min(index.counts[engine].get(needle, 0) for engine in short)
        return "missing", f"{item}  [{wanted} in the art, {grouped_n} grouped]", []
    if len(have) < len(index.per_engine):
        return "one-engine", item, have
    return "covered", item, []


def audit_title(
    comics_database: ComicsDatabase, speech_groups: SpeechGroups, title_str: str
) -> tuple[list[Finding], list[NearMiss], int, int]:
    """Audit one title.

    Returns its findings, its near misses, the pages checked and the number of
    story-logo echoes dropped.
    """
    title = STR_TITLE_TO_ENUM[title_str]
    volume = comics_database.get_fanta_volume_int(title_str)
    try:
        page_groups = speech_groups.get_speech_page_groups(title, skip_missing=True)
    except RuntimeError as exc:
        # The panel-segments mtime gate. Surfaced, not swallowed: an audit that
        # answers "nothing missing" while silently not having looked is worse
        # than one that admits it could not look.
        logger.warning(f'Skipping "{title_str}": {exc}')
        return [], [], 0, 0

    grouped_text, grouped_counts, grouped_lettering, capture_files, logos = index_pages(page_groups)
    findings: list[Finding] = []
    near_misses: list[NearMiss] = []
    pages_checked = 0
    suppressed = 0

    for page, per_engine in sorted(grouped_text.items()):
        visible = page_capture(capture_files[page])
        if visible is None:
            continue
        pages_checked += 1
        index = PageIndex(
            per_engine=per_engine,
            counts=grouped_counts[page],
            lettering=grouped_lettering[page],
            every_text=set().union(*per_engine.values()) if per_engine else set(),
            logos=logos,
        )
        wanted = Counter(comparable(item) for item in visible)
        wanted.pop("", None)
        seen: Counter[str] = Counter()
        for item in visible:
            needle = comparable(item)
            if not needle:
                continue
            seen[needle] += 1
            if seen[needle] > 1:
                continue  # one report per distinct lettering; multiplicity handled below
            verdict, line, engines = classify(needle, item, wanted[needle], index)
            if verdict == "suppressed":
                suppressed += 1
            elif verdict == "near":
                near_misses.append((title_str, volume, page, item, line))
            elif verdict != "covered":
                findings.append((title_str, volume, page, line, engines))

    return findings, near_misses, pages_checked, suppressed


def report(
    findings: list[Finding],
    near_misses: list[NearMiss],
    pages: int,
    suppressed: int,
    ignores: int,
) -> None:
    """Print the sweep result, worst class first."""
    neither = [f for f in findings if not f[4]]
    one_only = [f for f in findings if f[4]]

    print(f"Swept {pages} vision-passed page(s) carrying {VISIBLE_TEXT_KEY}.")
    print(f"Suppressed {suppressed} story-logo echo(es) on pages that carry no logo.")
    # Never silent: an ignore list that hides its own size is a way to stop
    # seeing a problem rather than a way to record a decision about it.
    print(f"Ignored {ignores} finding(s) listed in {IGNORE_FILE.name}.\n")

    print(f"=== grouped by NEITHER engine: {len(neither)} ===")
    for title_str, volume, page, item, _ in neither:
        print(f"  vol {volume:<3} {page}  {item!r:<42} {title_str}")

    print(f"\n=== grouped by only ONE engine: {len(one_only)} ===")
    for title_str, volume, page, item, have in one_only:
        engines = ", ".join(str(engine) for engine in have)
        print(f"  vol {volume:<3} {page}  {item!r:<42} {title_str}  (only {engines})")

    print(f"\n=== nearly a grouped text -- check the transcription: {len(near_misses)} ===")
    for title_str, volume, page, item, close in near_misses:
        print(f"  vol {volume:<3} {page}  {item!r:<42} {title_str}  vs grouped {close!r}")

    if neither:
        by_volume: dict[int, int] = defaultdict(int)
        for _, volume, _, _, _ in neither:
            by_volume[volume] += 1
        print("\n=== missing-from-both, by volume ===")
        for volume, count in sorted(by_volume.items(), key=lambda kv: -kv[1]):
            print(f"  {count:>3}  vol {volume}")


def write_csv(findings: list[Finding], dest: Path) -> None:
    """Write every finding to *dest* for turning into a review queue."""
    with dest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("title", "volume", "page", "lettering", "grouped_by"))
        for title_str, volume, page, item, have in findings:
            grouped = "|".join(str(engine) for engine in have) or "neither"
            writer.writerow((title_str, volume, page, item, grouped))
    print(f"\nwrote {dest}")


def main() -> None:
    """Sweep the corpus, or one title, and report lettering no group covers."""
    argv = sys.argv[1:]
    only_title = argv[argv.index("--title") + 1] if "--title" in argv else None
    csv_out = Path(argv[argv.index("--csv") + 1]).expanduser() if "--csv" in argv else None

    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    # Via the shared helper, not STR_TITLE_TO_ENUM: that enum carries titles the
    # database has no entry for, and looking their volume up raises KeyError.
    titles = resolve_titles(comics_database, "", only_title or "")

    findings: list[Finding] = []
    near_misses: list[NearMiss] = []
    pages = 0
    suppressed = 0
    for title_str in titles:
        found, close, checked, dropped = audit_title(comics_database, speech_groups, title_str)
        findings += found
        near_misses += close
        pages += checked
        suppressed += dropped

    ignores = load_ignores()
    kept = [f for f in findings if not ignored(ignores, f)]

    report(kept, near_misses, pages, suppressed, len(findings) - len(kept))
    if csv_out:
        write_csv(kept, csv_out)


if __name__ == "__main__":
    main()

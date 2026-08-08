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

Must be run with ``uv run`` from the barks-ocr checkout so the path deps resolve.
"""

import csv
import json
import re
import sys
from collections import defaultdict
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
IGNORE_FILE = Path(__file__).with_name("missed-text-ignore.txt")
SCOPED_ENTRY_FIELDS = 3  # volume, page, and the lettering itself

# title, volume, fanta_page, lettering, engines that grouped it (empty = neither)
Finding = tuple[str, int, str, str, list[OcrTypes]]


def normalize(text: str | None) -> str:
    """Reduce lettering to letters and digits for comparison.

    Quote style, dashes, case, line breaks and emphasis markup all differ freely
    between what the art shows and what an engine grouped, and none of those
    differences mean the lettering was missed.
    """
    return re.sub(r"[^A-Z0-9]", "", strip_markup(unescape_markup(text or "")).upper())


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


def index_pages(
    page_groups: list[SpeechPageGroup],
) -> tuple[dict[str, dict[OcrTypes, set[str]]], dict[str, Path], set[str]]:
    """Fold a title's page groups into per-page lookups.

    ``get_speech_page_groups`` yields one entry per (page, engine), so the
    grouped text has to be collected back into a page before a page's single
    capture can be compared against it.

    Returns the grouped text per page per engine, each page's capture file, and
    the title's story-logo texts.
    """
    grouped_text: dict[str, dict[OcrTypes, set[str]]] = defaultdict(dict)
    capture_files: dict[str, Path] = {}
    logos: set[str] = set()
    for page_group in page_groups:
        page = page_group.fanta_page
        groups = page_group.speech_page_json.get("groups", {})
        grouped_text[page][page_group.ocr_index] = {
            normalize(g.get("ai_text")) for g in groups.values()
        }
        capture_files.setdefault(
            page, page_group.ocr_prelim_groups_json_file.parent / (page + CAPTURE_FILE_SUFFIX)
        )
        logos |= {
            normalize(g.get("ai_text")) for g in groups.values() if g.get(TYPE_KEY) == TITLE_TYPE
        }
    logos.discard("")
    return grouped_text, capture_files, logos


def page_capture(capture_file: Path) -> list[str] | None:
    """Return a page's ``visible_text``, or None when there is nothing to check."""
    if not capture_file.is_file():
        return None
    capture = json.loads(capture_file.read_text(encoding="utf-8"))
    if not capture.get(CAPTURE_MODEL_KEY):
        return None  # never vision-passed, so visible_text carries no claim
    return capture.get(VISIBLE_TEXT_KEY) or None


def audit_title(
    comics_database: ComicsDatabase, speech_groups: SpeechGroups, title_str: str
) -> tuple[list[Finding], int, int]:
    """Audit one title; return its findings, pages checked, and logo echoes dropped."""
    title = STR_TITLE_TO_ENUM[title_str]
    volume = comics_database.get_fanta_volume_int(title_str)
    try:
        page_groups = speech_groups.get_speech_page_groups(title, skip_missing=True)
    except RuntimeError as exc:
        # The panel-segments mtime gate. Surfaced, not swallowed: an audit that
        # answers "nothing missing" while silently not having looked is worse
        # than one that admits it could not look.
        logger.warning(f'Skipping "{title_str}": {exc}')
        return [], 0, 0

    grouped_text, capture_files, logos = index_pages(page_groups)
    findings: list[Finding] = []
    pages_checked = 0
    suppressed = 0

    for page, per_engine in sorted(grouped_text.items()):
        visible = page_capture(capture_files[page])
        if visible is None:
            continue
        pages_checked += 1
        for item in visible:
            needle = normalize(item)
            if not needle:
                continue
            have = [engine for engine, texts in per_engine.items() if covers(needle, texts)]
            if have:
                if len(have) < len(per_engine):
                    findings.append((title_str, volume, page, item, have))
            elif any(needle == logo or needle in logo or logo in needle for logo in logos):
                suppressed += 1
            else:
                findings.append((title_str, volume, page, item, []))

    return findings, pages_checked, suppressed


def report(findings: list[Finding], pages: int, suppressed: int, ignores: int) -> None:
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
    pages = 0
    suppressed = 0
    for title_str in titles:
        found, checked, dropped = audit_title(comics_database, speech_groups, title_str)
        findings += found
        pages += checked
        suppressed += dropped

    ignores = load_ignores()
    kept = [f for f in findings if not ignored(ignores, f)]

    report(kept, pages, suppressed, len(findings) - len(kept))
    if csv_out:
        write_csv(kept, csv_out)


if __name__ == "__main__":
    main()

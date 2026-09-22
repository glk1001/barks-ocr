# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# where it put each queue is the whole point of running it.
"""Turn the missed-text audit's findings into queue files the Kivy editor can load.

    uv run --offline python scripts/vision/audit_missed_text.py --csv /tmp/backlog.csv
    uv run --offline python scripts/vision/missed_text_queue.py /tmp/backlog.csv <out-dir>

WHY THIS EXISTS. The audit's printout is NOT a queue: `load_queue_file` wants
five whitespace-separated fields, `volume page engine group kind`, with an
INTEGER group id, and it skips every line that does not parse -- so a file of
report text loads as nothing at all, with one warning per line. That happened
once already (2026-09-03) and the finding reached the reviewer by hand.

A missed-text item has no group of its own yet; that is what makes it a finding.
So each entry is PARKED on a real group on the same page, which is what gives the
editor somewhere to open. Parking prefers a group that already carries the same
lettering -- the `N in the art, M grouped` class always has one, and it sits in
the same or a adjacent panel -- and falls back to the page's first group,
which at least opens the right page. The lettering and the class follow the kind
field, where the parser ignores them and the reviewer can read them.

Three files are written, because the classes are three different jobs:

  queue-missed-counted.txt   the art shows it N times, the engines grouped M.
                             Mostly `1 in the art, 0 grouped` -- a real sign the
                             engines missed. The biggest and most useful class.
  queue-missed-read-aloud.txt lettering with no group of its own whose words sit
                             inside a character's balloon. Genuine, and the case
                             the read-aloud check was built for.
  queue-missed-plain.txt     neither engine grouped it and nothing contains it.

AND A FOURTH, `queue-missed.txt`, WHICH IS EVERY CLASS IN ONE FILE. That is the
name the vision-pass skill tells the reviewer to expect, and until 2026-09-22
nothing wrote it: the per-class files existed, the hand-back named one of them,
and the reviewer was looking for a file that was never created. The class follows
the kind field here too, so one queue can be worked start to finish and the
split files remain for when the classes want handling separately.
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PRELIM = Path("/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim")
ENGINES = ("easyocr", "paddleocr")
ANNOTATION = re.compile(r"\s\s\[(?:quoted aloud, not boxed|\d+ in the art, \d+ grouped)\]$")
COUNTED = re.compile(r"\[(\d+) in the art, (\d+) grouped\]$")


def normalize(text: str) -> str:
    """Letters and digits only -- the same key the audit matches on."""
    return "".join(ch for ch in (text or "").upper() if ch.isalnum())


def device_key(text: str) -> str:
    """Return a drawn device's marks, for lettering that has no letters."""
    squashed = re.sub(r"\s+", "", text or "")
    if not squashed:
        return ""
    return squashed[0] if len(set(squashed)) == 1 else squashed


def comparable(text: str) -> str:
    """Return the key this lettering matches on: its letters, or its marks."""
    return normalize(text) or device_key(text)


def volume_dirs() -> dict[int, Path]:
    """Map a volume number to its prelim directory."""
    out: dict[int, Path] = {}
    for path in PRELIM.iterdir():
        m = re.match(r"Carl Barks Vol\. (\d+) - ", path.name)
        if m and path.is_dir():
            out[int(m.group(1))] = path
    return out


def park_on(vol_dir: Path, page: str, needle: str) -> dict[str, int]:
    """Pick a group id per engine to hang this finding on.

    Three choices, best first. A group carrying exactly this lettering is a
    sibling instance, which the counted class has whenever M > 0 and which sits in
    the same or a adjacent panel. Failing that, a group whose text CONTAINS
    the lettering is the balloon a character reads the sign aloud in -- that is
    the whole read-aloud class, and the balloon is drawn near the sign. Only then
    the page's lowest group id, which at least opens the right page.
    """
    parked: dict[str, int] = {}
    for engine in ENGINES:
        f = vol_dir / f"{page}-{engine}-gemini-prelim-groups.json"
        if not f.is_file():
            continue
        groups = json.loads(f.read_text()).get("groups", {})
        if not groups:
            continue
        keyed = {int(k): comparable(g.get("ai_text") or "") for k, g in groups.items()}
        same = [k for k, text in keyed.items() if text == needle]
        holds = [k for k, text in keyed.items() if needle and needle in text]
        parked[engine] = min(same or holds or list(keyed))
    return parked


def classify_row(lettering: str) -> str:
    """Which of the three queues this finding belongs in."""
    if "[quoted aloud, not boxed]" in lettering:
        return "read-aloud"
    return "counted" if COUNTED.search(lettering) else "plain"


HEADERS = {
    "counted": (
        "# MISSED TEXT -- the art shows this lettering N times and the engines grouped M.\n"
        "# Mostly `1 in the art, 0 grouped`: a real sign neither engine boxed. ADD a group\n"
        "# for each missing instance in the editor.\n"
    ),
    "read-aloud": (
        "# MISSED TEXT -- lettering with no group of its own, whose words sit inside a\n"
        "# character's balloon. The sign itself is unboxed and unsearchable even though the\n"
        "# words appear on the page. ADD a group for the sign.\n"
    ),
    "plain": (
        "# MISSED TEXT -- neither engine grouped it and no group contains it. Check each\n"
        "# against the art: some are real signs, some are drawn devices carrying no\n"
        "# characters, which belong in missed-text-ignore.txt instead.\n"
    ),
}

PREAMBLE = (
    "#\n"
    "# Each entry is PARKED on an existing group on the same page -- a missed item has\n"
    "# no group of its own, so the editor needs somewhere to open. Where the lettering\n"
    "# already exists as a group elsewhere on the page, that group is used and will be\n"
    "# in the same or a adjacent panel; otherwise the page's first group is used.\n"
    "# The lettering and the class follow the kind field, where the parser ignores them.\n"
    "#\n"
    "# Fields: volume page engine group kind    then the lettering, for reading.\n"
)


COMBINED_HEADER = (
    "# MISSED TEXT -- every class in one queue. This is the file the vision-pass\n"
    "# skill names; the queue-missed-<class>.txt files beside it hold the same\n"
    "# entries split by the job each class wants. Work this one unless you have a\n"
    "# reason to take the classes separately.\n"
)


def write_queue(dest: Path, header: str, entries: list[tuple], *, with_class: bool) -> int:
    """Write one queue file and return the number of findings it holds.

    Args:
        dest: the file to write.
        header: the class-specific comment block that opens it.
        entries: (volume, page, gid, engine, text, title) or the same with a
            leading class name when `with_class` is set.
        with_class: whether each entry carries its class as its first element.

    Returns:
        The number of findings, which is one per engine pair.

    """
    entries.sort(key=lambda e: e[1:5] if with_class else e[:4])
    found = len(entries) // len(ENGINES)
    summary = f"# {len(entries)} line(s), {found} finding(s), one line per engine.\n#\n"
    lines = [header, PREAMBLE, summary]
    for entry in entries:
        cls = entry[0] if with_class else ""
        vol, page, gid, engine, text, title = entry[1:] if with_class else entry
        tail = f"{text}  [{cls}]  ({title})" if cls else f"{text}  ({title})"
        lines.append(f"{vol} {page:03d} {engine} {gid} missed-text {tail}\n")
    dest.write_text("".join(lines))
    return found


def main() -> None:
    """Write the per-class queue files and the combined one from an audit CSV."""
    if len(sys.argv) != 3:  # noqa: PLR2004 -- script, argv shape is the usage line
        sys.exit(__doc__)
    rows = list(csv.DictReader(Path(sys.argv[1]).expanduser().open()))
    out_dir = Path(sys.argv[2]).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    vols = volume_dirs()
    buckets: dict[str, list[tuple]] = defaultdict(list)
    skipped = 0
    for row in rows:
        volume, page, lettering = int(row["volume"]), row["page"], row["lettering"]
        raw = ANNOTATION.sub("", lettering)
        needle = comparable(raw)
        vol_dir = vols.get(volume)
        if vol_dir is None:
            skipped += 1
            continue
        parked = park_on(vol_dir, page, needle)
        if not parked:
            skipped += 1
            continue
        shown = raw.replace("\n", " / ")
        note = (COUNTED.search(lettering) or [None])[0] if COUNTED.search(lettering) else ""
        for engine, gid in sorted(parked.items()):
            shown_note = f"{shown}  {note}" if note else shown
            buckets[classify_row(lettering)].append(
                (volume, int(page), gid, engine, shown_note, row["title"])
            )

    combined: list[tuple] = []
    for name, entries in sorted(buckets.items()):
        dest = out_dir / f"queue-missed-{name}.txt"
        found = write_queue(dest, HEADERS[name], list(entries), with_class=False)
        print(f"wrote {dest}  --  {len(entries)} line(s), {found} finding(s)")
        combined += [(name, *entry) for entry in entries]

    if combined:
        dest = out_dir / "queue-missed.txt"
        found = write_queue(dest, COMBINED_HEADER, combined, with_class=True)
        print(f"wrote {dest}  --  {len(combined)} line(s), {found} finding(s), all classes")
    if skipped:
        print(f"skipped {skipped} finding(s) with no locatable page or groups")


if __name__ == "__main__":
    main()

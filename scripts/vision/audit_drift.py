# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the drift is the whole point.
"""Detect an id renumber, or a lost `vision_added`, between two states of the corpus.

    uv run --offline python scripts/vision/audit_drift.py                 # HEAD vs working tree
    uv run --offline python scripts/vision/audit_drift.py --since HEAD~5
    uv run --offline python scripts/vision/audit_drift.py --since HEAD~5 --until HEAD

Item 3 of `docs/invariant-suite.md`, the one it called the real project. The
plan said the check "wants either the git blob of the previous commit or a
checkpoint written by prep" -- the prelim repo has 380 commits, so the
checkpoint already exists and nothing new has to be written to get one.

TWO FAULTS, both of which have destroyed work.

**An id that now carries different text**, compared with emphasis markup
stripped -- an apply writing `[b]...[/b]` into `ai_text` changes the bytes and
nothing else, and is the commonest edit in the corpus. Comparing raw text made
it 90% of the output. The editor renumbers ids on a delete
*and* on an add, and can re-sort a page into reading order with neither. A
stored `result.json` is keyed by id, so after any of those it is silently
pointed at the wrong group, and applying it writes each annotation onto its
neighbour. This reports every id whose `ai_text` changed between the two states
-- which is the renumber, seen from the side that matters.

**A `vision_added` flag that disappeared.** It marks a hand-add, predates the
pass, and sits on different ids per engine, so it is easy to drop in a rewrite
and impossible to reconstruct. Groups are matched between the two states by
**(text, occurrence)** -- never by id, which is the thing under suspicion, and
never by text alone, which collides whenever a page letters the same word twice.

Read what it prints. A page genuinely re-lettered during a review will show ids
carrying new text and that is correct; the question is always whether a stored
`result.json` was written against the old numbering.
"""

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from barks_fantagraphics.speech_markup import strip_markup

GROUPS_GLOB = "*-gemini-prelim-groups.json"
MAX_LISTED = 30


def _git(*args: str) -> str:
    """Run git in the prelim repo and return stdout."""
    return subprocess.run(  # noqa: S603 -- fixed argv, no shell.
        ["git", "-C", str(OCR_PRELIM_DIR), *args],  # noqa: S607
        capture_output=True,
        check=True,
        text=True,
    ).stdout


def _blob(ref: str, path: str) -> dict | None:
    """Return one groups file's parsed content at *ref*, or None if absent there."""
    proc = subprocess.run(  # noqa: S603 -- fixed argv, no shell.
        ["git", "-C", str(OCR_PRELIM_DIR), "show", f"{ref}:{path}"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return json.loads(proc.stdout)


def _working(path: str) -> dict | None:
    """Return one groups file's parsed content from the working tree."""
    full = Path(OCR_PRELIM_DIR) / path
    if not full.exists():
        return None
    return json.loads(full.read_bytes())


def occurrence_keys(groups: dict[str, dict]) -> dict[str, tuple[str, int]]:
    """Key every group by (its text, which occurrence of that text it is).

    Never by id -- that is the thing under suspicion -- and never by text alone,
    which collides whenever a page letters the same word twice.

    Args:
        groups: one page's stored groups, by id.

    Returns:
        group id -> (ai_text, occurrence index), in id order.

    """
    seen: Counter[str] = Counter()
    keys: dict[str, tuple[str, int]] = {}
    for gid in sorted(groups, key=lambda k: int(k) if k.isdigit() else 0):
        text = strip_markup(groups[gid].get("ai_text") or "")
        keys[gid] = (text, seen[text])
        seen[text] += 1
    return keys


def _shifted_from(gid: str, now: str, old_text: dict[str, str]) -> str:
    """Say whether this id took its neighbour's old text, i.e. the page renumbered."""
    if not gid.isdigit() or not now:
        return ""
    for step in (-1, 1):
        neighbour = str(int(gid) + step)
        if old_text.get(neighbour) == now:
            return f"  [SHIFTED from g{neighbour}]"
    return ""


def compare(old: dict, new: dict, where: str) -> tuple[list[str], list[str]]:
    """Compare one page's groups across two states.

    Args:
        old: the earlier groups file content.
        new: the later groups file content.
        where: a label for the page, used in the reported lines.

    Returns:
        (ids whose text changed, `vision_added` flags that disappeared).

    """
    old_groups = old.get("groups", {})
    new_groups = new.get("groups", {})

    # A SHIFT is the fault; an isolated retype is not. If an id's new text is
    # what its NEIGHBOUR used to hold, the page was renumbered under a stored
    # result.json. If the text is simply different, somebody corrected it.
    old_text = {g: strip_markup(v.get("ai_text") or "") for g, v in old_groups.items()}

    renumbered: list[str] = []
    for gid, group in old_groups.items():
        if gid not in new_groups:
            continue
        # Strip emphasis before comparing: an apply writing [b]...[/b] into
        # ai_text changes the bytes and nothing else, and it is the single most
        # common edit in the corpus. Comparing raw text makes it 90% of the noise.
        was = strip_markup(group.get("ai_text") or "")
        now = strip_markup(new_groups[gid].get("ai_text") or "")
        if was == now:
            continue
        shifted = _shifted_from(gid, now, old_text)
        renumbered.append(f"{where} g{gid}: {was[:34]!r} -> {now[:34]!r}{shifted}")

    # Match by (text, occurrence) so a renumber cannot hide a dropped flag.
    new_by_key = {key: gid for gid, key in occurrence_keys(new_groups).items()}
    lost: list[str] = []
    for gid, key in occurrence_keys(old_groups).items():
        if not old_groups[gid].get("vision_added"):
            continue
        match = new_by_key.get(key)
        if match is None:
            lost.append(f"{where} g{gid}: group gone entirely ({key[0][:30]!r})")
        elif not new_groups[match].get("vision_added"):
            lost.append(f"{where} g{gid} -> g{match}: vision_added dropped ({key[0][:30]!r})")
    return renumbered, lost


def _changed_files(since: str, until: str | None) -> list[str]:
    """Return the groups files that differ between the two states."""
    args = ["diff", "--name-only", since, *([until] if until else [])]
    return [p for p in _git(*args).split("\n") if p.endswith("prelim-groups.json")]


def _report(title: str, lines: list[str], footer: list[str]) -> None:
    """Print one findings block, elided past MAX_LISTED."""
    print(f"=== {title}: {len(lines)} ===")
    for line in lines[:MAX_LISTED]:
        print(f"     {line}")
    if len(lines) > MAX_LISTED:
        print(f"     ... and {len(lines) - MAX_LISTED} more")
    if lines:
        for line in footer:
            print(f"  {line}")


def main() -> None:
    """Compare two states of the corpus and report renumbers and lost flags."""
    argv = sys.argv[1:]
    since = argv[argv.index("--since") + 1] if "--since" in argv else "HEAD"
    until = argv[argv.index("--until") + 1] if "--until" in argv else None

    changed = _changed_files(since, until)
    print(f"comparing {since}..{until or 'working tree'}: {len(changed)} groups file(s) changed\n")

    renumbered: list[str] = []
    lost: list[str] = []
    by_title: Counter[str] = Counter()

    for path in changed:
        old = _blob(since, path)
        new = _blob(until, path) if until else _working(path)
        if old is None or new is None:
            continue
        page = Path(path).name.split("-")[0]
        engine = "easyocr" if "easyocr" in path else "paddleocr"
        where = f"{Path(path).parent.name[:28]} {page} {engine}"
        page_renumbered, page_lost = compare(old, new, where)
        renumbered += page_renumbered
        lost += page_lost
        if page_renumbered:
            by_title[Path(path).parent.name[:34]] += len(page_renumbered)

    _report(
        "ids now carrying different text",
        renumbered,
        [
            "SHIFTED means the id took its neighbour's text -- the page was",
            "renumbered, and a result.json keyed by id now points elsewhere.",
            "A line without it is an ordinary retype.",
        ],
    )
    if by_title:
        print("  by title:")
        for title_str, count in by_title.most_common(MAX_LISTED):
            print(f"     {count:>4}  {title_str}")

    print()
    _report(
        "vision_added flags lost",
        lost,
        ["vision_added marks a hand-add. It cannot be reconstructed."],
    )
    if lost:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

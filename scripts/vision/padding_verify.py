# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and
# printing the verdict is the whole point of running it.
"""Verify one volume's uncommitted ``--fix-padding`` write, and write its spot-check queue.

    uv run --offline python scripts/vision/padding_verify.py VOLUME QUEUE_FILE

Run by ``scripts/vision/padding_rollout.sh`` after ``ocr_check --fix-padding`` has
written a volume and before anything is committed. It reads only that volume's
uncommitted groups files in the prelim repo -- a reviewer may be editing another
volume in the same tree, which is how the 2026-10-11 rollout met a reviewer's Vol. 1
edits in the middle of Vol. 7 -- and refuses the write unless:

- every changed file is a ``*-gemini-prelim-groups.json`` that still round-trips as
  ``json.dumps(d, indent=4)``;
- no group was added or removed, and no page-level field changed;
- ``text_box`` is the only field that changed on any group;
- on every page touched, the set of (group, field) differences BETWEEN THE TWO
  ENGINES is what it was at HEAD. Engines that agreed still agree, so a seed
  title's paddleocr copy is still exact, and a pair that differed was not made to
  differ differently.

On success it prints ``CHANGED <entries> files <files>`` and writes QUEUE_FILE, one
``volume page engine group box_padded`` line per changed group, sorted by volume,
page, group and engine, for the kivy editor. On failure it prints ``FAIL ...`` and
exits 1, leaving the tree as it was.

The prelim directory is ``OCR_PRELIM_DIR``, so ``BARKS_OCR_PRELIM_DIR`` moves it as it
moves every barks-ocr command.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR

GROUPS_SUFFIX = "-gemini-prelim-groups.json"
TEXT_BOX = "text_box"
ENGINES = ("easyocr", "paddleocr")
ARG_COUNT = 3


def _git(*args: str) -> str:
    return subprocess.run(  # noqa: S603 -- fixed argv, no shell.
        ["git", "-C", str(OCR_PRELIM_DIR), *args],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _head_json(path: str) -> dict | None:
    """Return the file as committed at HEAD, or None when HEAD does not have it."""
    try:
        return json.loads(_git("show", f"HEAD:{path}"))
    except subprocess.CalledProcessError:
        return None


def _engine_diffs(easy: dict, paddle: dict) -> set[tuple[str, str]]:
    """Return every (group id, field) on which the two engines' groups differ."""
    out: set[tuple[str, str]] = set()
    for gid in set(easy) | set(paddle):
        if gid not in easy or gid not in paddle:
            out.add((gid, "<missing>"))
            continue
        fields = set(easy[gid]) | set(paddle[gid])
        out |= {(gid, k) for k in fields if easy[gid].get(k) != paddle[gid].get(k)}
    return out


def _fail(message: str) -> NoReturn:
    print(f"FAIL {message}")
    sys.exit(1)


def _check_file(path: str) -> list[tuple[str, int, str]]:
    """Check one changed groups file; return (page, group, engine) for each changed group."""
    if not path.endswith(GROUPS_SUFFIX):
        _fail(f"not a groups file: {path}")
    raw = (OCR_PRELIM_DIR / path).read_text()
    new = json.loads(raw)
    if json.dumps(new, indent=4) != raw:
        _fail(f"format: {path}")
    old = _head_json(path)
    if old is None or set(old) != set(new) or set(old["groups"]) != set(new["groups"]):
        _fail(f"structure: {path}")
    if any(old[k] != new[k] for k in old if k != "groups"):
        _fail(f"page field changed: {path}")
    name = Path(path).name
    page, engine = name[:3], name.split("-")[1]
    changed = []
    for gid, group in new["groups"].items():
        before = old["groups"][gid]
        fields = {k for k in set(group) | set(before) if group.get(k) != before.get(k)}
        if fields - {TEXT_BOX}:
            _fail(f"{path} group {gid} changed {sorted(fields)}")
        if fields:
            changed.append((page, int(gid), engine))
    return changed


def _check_engine_parity(pages: set[tuple[str, str]]) -> None:
    for volume_dir, page in sorted(pages):
        easy_path, paddle_path = (f"{volume_dir}/{page}-{e}{GROUPS_SUFFIX}" for e in ENGINES)
        head_easy, head_paddle = _head_json(easy_path), _head_json(paddle_path)
        if head_easy is None or head_paddle is None:
            continue
        now_easy = json.loads((OCR_PRELIM_DIR / easy_path).read_text())
        now_paddle = json.loads((OCR_PRELIM_DIR / paddle_path).read_text())
        if _engine_diffs(head_easy["groups"], head_paddle["groups"]) != _engine_diffs(
            now_easy["groups"], now_paddle["groups"]
        ):
            _fail(f"engine agreement changed on {volume_dir} page {page}")


def main() -> None:
    """Verify the volume named on the command line and write its queue file."""
    if len(sys.argv) != ARG_COUNT:
        print(__doc__)
        sys.exit(2)
    volume, queue_file = int(sys.argv[1]), Path(sys.argv[2])
    prefix = f"Carl Barks Vol. {volume} - "
    files = [f for f in _git("diff", "--name-only").splitlines() if f.startswith(prefix)]

    entries: list[tuple[str, int, str]] = []
    pages: set[tuple[str, str]] = set()
    for path in files:
        entries += _check_file(path)
        pages.add((path.split("/", 1)[0], Path(path).name[:3]))
    _check_engine_parity(pages)

    entries.sort()
    with queue_file.open("w") as queue:
        queue.write(f"# Vol. {volume}: text_boxes --fix-padding padded out to their lettering\n")
        queue.write(f"# {len(entries)} entries\n")
        for page, gid, engine in entries:
            queue.write(f"{volume} {page} {engine} {gid} box_padded\n")
    print(f"CHANGED {len(entries)} files {len(files)}")


if __name__ == "__main__":
    main()

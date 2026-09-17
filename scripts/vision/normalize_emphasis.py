# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# what it would change is the whole point of running it.
"""Rewrite `[i]` emphasis as `[b]` across the prelim groups files; dry run by default.

    uv run --offline python scripts/vision/normalize_emphasis.py            # report
    uv run --offline python scripts/vision/normalize_emphasis.py --write    # do it

WHY THIS EXISTS. The vision roster used to generate its emphasis line from
`EMPHASIS_TAGS`, so it offered `[b]WORD[/b], [i]WORD[/i]` as equal options and
whole batches drifted into `[i]`. Measured 2026-09-17: 35,706 `[b]` tags against
2,540 `[i]`. The roster now says emphasis is `[b]`, and `vision_apply` refuses an
`[i]` that does not cover the whole group; this tool brings the existing corpus
into line with that rule. The rule itself, and the only definition of a slanted
face, is `barks_ocr.utils.emphasis`.

What it changes: `ai_text` only, on every groups file under the prelim root
(which honours `BARKS_OCR_PRELIM_DIR`). What it leaves alone: a group whose `[i]`
runs cover all of its lettering -- a caption or balloon set entirely in a slanted
face -- and `vision_note`, which is the pass's reasoning and quotes tags on
purpose.

Safety, checked on every file before anything is written:
  * the groups file round-trips as `json.dumps(indent=4)` with no trailing
    newline, so a one-tag edit cannot reformat the file;
  * each changed group's lettering is identical once tags are stripped, and its
    markup still passes `speech_markup.validate_markup`.
Any failure aborts the whole run with nothing written. Git is the backup: commit
the result one volume at a time, and stage explicit paths, never a glob.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from barks_fantagraphics.speech_markup import strip_markup, validate_markup

from barks_ocr.utils.emphasis import normalize_emphasis

GROUPS_GLOB = "*/*-gemini-prelim-groups.json"
VOLUME_RE = re.compile(r"Carl Barks Vol\. (\d+) - ")


class Plan:
    """What a run would write, grouped by volume, and anything that makes it unsafe."""

    def __init__(self) -> None:
        """Start an empty plan."""
        self.files: list[tuple[Path, dict]] = []
        self.by_volume: dict[int, list[str]] = defaultdict(list)
        self.groups_changed = 0
        self.problems: list[str] = []


def _plan_file(path: Path, prelim: Path, plan: Plan) -> None:
    """Normalise one groups file in memory and record it in ``plan`` if it changes."""
    raw = path.read_text(encoding="utf-8")
    if "[i]" not in raw:
        return
    data = json.loads(raw)
    if json.dumps(data, indent=4) != raw:
        plan.problems.append(f"{path}: does not round-trip as json.dumps(indent=4)")
        return
    touched = False
    for gid, group in data.get("groups", {}).items():
        text = group.get("ai_text") or ""
        new = normalize_emphasis(text)
        if new == text:
            continue
        if strip_markup(new) != strip_markup(text):
            plan.problems.append(f"{path.name} g{gid}: lettering would change")
        plan.problems.extend(f"{path.name} g{gid}: {p}" for p in validate_markup(new))
        group["ai_text"] = new
        plan.groups_changed += 1
        touched = True
    if touched:
        plan.files.append((path, data))
        match = VOLUME_RE.match(path.parent.name)
        volume = int(match.group(1)) if match else -1
        plan.by_volume[volume].append(str(path.relative_to(prelim)))


def main() -> None:
    """Report, or with --write apply, the emphasis rewrite."""
    write = "--write" in sys.argv[1:]
    prelim = Path(OCR_PRELIM_DIR)
    plan = Plan()
    for path in sorted(prelim.glob(GROUPS_GLOB)):
        _plan_file(path, prelim, plan)

    print(f"prelim root: {prelim}")
    print(
        f"{plan.groups_changed} group(s) in {len(plan.files)} file(s)"
        f" across {len(plan.by_volume)} volume(s)"
    )
    for volume, files in sorted(plan.by_volume.items()):
        print(f"  vol {volume:>2}: {len(files)} file(s)")
    if plan.problems:
        print(f"\nABORTED -- {len(plan.problems)} safety problem(s), nothing written:")
        for problem in plan.problems[:20]:
            print(f"  {problem}")
        sys.exit(1)
    if not write:
        print("\nDRY RUN -- nothing written. Re-run with --write.")
        return
    for path, data in plan.files:
        path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    print(f"\nwrote {len(plan.files)} file(s)")


if __name__ == "__main__":
    main()

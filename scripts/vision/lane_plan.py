# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the plan is the whole point.
"""Split the vision-pass work list into concurrent lanes of about N pages each.

    uv run --offline python scripts/vision/lane_plan.py [--lanes 2] [--pages 40] [--slack 8]
    uv run --offline python scripts/vision/lane_plan.py --show

WHY THIS EXISTS. Two or more vision passes can run at once, each in its own Claude
Code session and its own prelim worktree (`scripts/vision/lanes.sh`). They must not
share a VOLUME: the prelim repo's pre-commit hook takes one volume per commit, and
two branches editing one volume's pages is exactly what made *The Paul Bunyan
Machine* re-apply on 2026-09-24 -- the pass had run against files another branch
was rewriting. So a volume belongs to one lane per round, and this script does the
bookkeeping.

The list is `vision-status --todo`, through the same `unread_titles`, so a lane
never gets a title the status report calls done. It is read from the MAIN prelim
checkout: run this with `BARKS_OCR_PRELIM_DIR` unset, after the last round's lanes
are merged, or it plans from a lane's partial view.

HOW TITLES ARE DEALT. Oldest first. A title goes to the lane that already owns its
volume, or, for a new volume, to the lightest lane -- as long as the lane stays
under `--pages` + `--slack`. A title that does not fit is skipped, and so is every
later title of that volume, so a volume is never read out of order across rounds.
A lane is full once it reaches `--pages`.

Writes `~/barks-vision/lanes/lane-<N>.json` (the lane session reads it) and prints
the title block each lane session should say back. `--show` prints the current
plan without making a new one.
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import SpeechGroups
from loguru import logger

from barks_ocr.tools.vision_status import scan_titles, unread_titles

LANES_DIR = Path.home() / "barks-vision" / "lanes"
PRELIM_OVERRIDE_ENV = "BARKS_OCR_PRELIM_DIR"


@dataclass
class Lane:
    """One lane's share of the work list."""

    lane: int
    branch: str
    worktree: str
    created: str
    titles: list[dict] = field(default_factory=list)
    volumes: list[int] = field(default_factory=list)
    pages: int = 0


def worktree_path(n: int) -> Path:
    """Return the prelim worktree a lane works in, beside the main checkout.

    Args:
        n: The lane number.

    Returns:
        The worktree directory, e.g. `.../Fantagraphics-restored-ocr/Prelim-lane1`.

    """
    return Path(OCR_PRELIM_DIR).parent / f"Prelim-lane{n}"


def deal(todo: list, n_lanes: int, target: int, slack: int) -> list[Lane]:
    """Deal the unread titles into lanes that share no volume.

    Args:
        todo: Unread `TitleStat`s, oldest first.
        n_lanes: How many lanes.
        target: The page count at which a lane stops taking titles.
        slack: How far past `target` one title may take a lane.

    Returns:
        The lanes, each with its titles in chronological order.

    """
    today = datetime.now(tz=UTC).date().isoformat()
    lanes = [Lane(n, f"lane{n}", str(worktree_path(n)), today) for n in range(1, n_lanes + 1)]
    owner: dict[int, Lane] = {}
    blocked: set[int] = set()
    for t in todo:
        if all(lane.pages >= target for lane in lanes):
            break
        if t.volume in blocked:
            continue
        pages = t.pages - t.read
        if t.volume in owner:
            candidates = [owner[t.volume]]
        else:
            candidates = sorted(lanes, key=lambda lane: lane.pages)
        lane = next(
            (c for c in candidates if c.pages < target and c.pages + pages <= target + slack),
            None,
        )
        if lane is None:
            # Keep the volume in order: nothing later in it jumps this title.
            blocked.add(t.volume)
            continue
        owner[t.volume] = lane
        if t.volume not in lane.volumes:
            lane.volumes.append(t.volume)
        lane.titles.append({"title": t.title, "volume": t.volume, "pages": pages, "year": t.year})
        lane.pages += pages
    return lanes


def show(lanes: list[Lane]) -> None:
    """Print each lane's title block and how to start its session.

    Args:
        lanes: The lanes to print.

    """
    for lane in lanes:
        print(f"== lane {lane.lane}: {lane.pages} pages, volumes {lane.volumes}")
        for t in lane.titles:
            print(f"   {t['year']}  {t['title']:<44} vol {t['volume']:>2}  {t['pages']:>3}p")
        print(f"   worktree {lane.worktree}  (branch {lane.branch})")
        print(
            f"   start:   cd {Path.cwd()} && BARKS_OCR_PRELIM_DIR='{lane.worktree}' claude"
            f"   then:  /vision-pass lane {lane.lane}\n"
        )


def main() -> int:
    """Plan the lanes, or show the current plan.

    Returns:
        A process exit code.

    """
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lanes", type=int, default=2)
    ap.add_argument("--pages", type=int, default=40)
    ap.add_argument("--slack", type=int, default=8)
    ap.add_argument("--show", action="store_true", help="Print the current plan and stop.")
    args = ap.parse_args()

    if args.show:
        files = sorted(LANES_DIR.glob("lane-*.json"))
        if not files:
            print("no plan yet", file=sys.stderr)
            return 1
        show([Lane(**json.loads(f.read_text())) for f in files])
        return 0

    if os.environ.get(PRELIM_OVERRIDE_ENV):
        print(
            f"{PRELIM_OVERRIDE_ENV} is set; plan from the main checkout, not a lane.",
            file=sys.stderr,
        )
        return 1

    # The scan warns once per title whose page map claims a one-pager's page; that is
    # the corpus as documented, not something a plan can act on.
    logger.disable("barks_ocr")
    comics_database = ComicsDatabase()
    todo = unread_titles(scan_titles(comics_database, SpeechGroups(comics_database)))
    logger.enable("barks_ocr")
    lanes = deal(todo, args.lanes, args.pages, args.slack)

    LANES_DIR.mkdir(parents=True, exist_ok=True)
    for stale in LANES_DIR.glob("lane-*.json"):
        stale.unlink()
    for lane in lanes:
        (LANES_DIR / f"lane-{lane.lane}.json").write_text(json.dumps(asdict(lane), indent=2) + "\n")
    show(lanes)
    return 0


if __name__ == "__main__":
    sys.exit(main())

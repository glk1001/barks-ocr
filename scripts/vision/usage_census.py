# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the census is the whole point.
"""Report what a vision pass cost in Claude Code tokens, from the session transcripts.

    uv run --offline python scripts/vision/usage_census.py            # today
    uv run --offline python scripts/vision/usage_census.py --since 2026-09-18
    uv run --offline python scripts/vision/usage_census.py --all --detail

`docs/vision-cost-ledger.csv` records images read, which is the axis
`docs/vision-pass-cost.md` governs. It is not the axis that dominates the bill.
Measured over this project's transcripts, **context re-reading is ~88% of token
consumption** and output is ~12%: every turn re-sends the whole accumulated
conversation, so the cost of a session is roughly `turns x average context`.

That makes `avg_ctx` -- cache-read divided by API calls -- the number worth
watching, and it is the one nothing else records. It is a per-call average over
the life of the session, so it rises with session length: a short session sits
near 160K, a 700-call session near 480K, where auto-compaction plateaus it.

COUNTING. Claude Code writes one JSONL record per *content block*, and every
block of one assistant message repeats that message's `usage` verbatim. Summing
the records therefore over-counts every figure by the blocks-per-message factor
(~2.5x here). This script keys on `message.id` and counts each API call once.
`turns` below means API calls, not content blocks.

Sub-agent calls (`isSidechain`) are billed too and are counted; `--detail`
splits them out, since a fan-out of agents inflates call count at low context
and so pulls `avg_ctx` down without the main thread having got any cheaper.

The cost share weights raw counters into input-token-equivalents at the
published Opus ratios -- cache read 0.1x, cache write 1.25x, output 5x -- so the
three are comparable. On a subscription no dollar figure is implied; the shares
and the trend are the point.
"""

import argparse
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Claude Code stores transcripts under a slug of the project's absolute path,
# with every separator turned into a dash. Derived, not hardcoded, so a checkout
# somewhere else still finds its own sessions. The repo path is used as written:
# resolving a symlink here would point at a slug that does not exist.
REPO_DIR = Path(__file__).resolve().parent.parent.parent
TRANSCRIPT_ROOT = Path.home() / ".claude" / "projects"

# Input-token-equivalents. Cache reads bill at a tenth of a fresh input token,
# cache writes at 1.25x, output at 5x.
WEIGHT_CACHE_READ = 0.1
WEIGHT_CACHE_WRITE = 1.25
WEIGHT_OUTPUT = 5.0

# The observed plateau is 480-515K. A session averaging above this is carrying
# more context than the long sessions that prompted the check.
HOT_AVG_CONTEXT = 450_000


@dataclass
class Session:
    """Deduplicated token counters for one Claude Code session transcript."""

    name: str
    last: str = ""
    calls: int = 0
    sidechain_calls: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    fresh_input: int = 0
    seen: set[str] = field(default_factory=set)

    @property
    def avg_context(self) -> float:
        """Mean context re-read per API call, in tokens."""
        return self.cache_read / self.calls if self.calls else 0.0

    @property
    def units(self) -> float:
        """Total cost in input-token-equivalents."""
        return (
            self.cache_read * WEIGHT_CACHE_READ
            + self.cache_write * WEIGHT_CACHE_WRITE
            + self.output * WEIGHT_OUTPUT
        )


def transcript_dir(repo: Path = REPO_DIR) -> Path:
    """Return the Claude Code transcript directory for a project checkout.

    Args:
        repo: The project's absolute path, symlinks left intact.

    Returns:
        The directory holding that project's session JSONL files. It may not
        exist, which simply means no session has run from that path.

    """
    return TRANSCRIPT_ROOT / str(repo).replace("/", "-")


def read_session(path: Path) -> Session:
    """Sum one transcript's usage counters, counting each API call once.

    Args:
        path: A session JSONL file.

    Returns:
        The session's counters. `calls` is zero for a transcript with no
        assistant turns, which the caller is expected to drop.

    """
    session = Session(name=path.stem[:8])
    for line in path.open(errors="replace"):
        # Cheap reject first: these files run to hundreds of megabytes and only
        # assistant records carry usage.
        if '"usage"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        message = record.get("message") or {}
        usage = message.get("usage") or {}
        message_id = message.get("id")
        if not usage or not message_id or message_id in session.seen:
            continue
        session.seen.add(message_id)
        session.calls += 1
        if record.get("isSidechain"):
            session.sidechain_calls += 1
        session.last = (record.get("timestamp") or session.last)[:10]
        session.output += usage.get("output_tokens") or 0
        session.cache_read += usage.get("cache_read_input_tokens") or 0
        session.cache_write += usage.get("cache_creation_input_tokens") or 0
        session.fresh_input += usage.get("input_tokens") or 0
    return session


def collect(directory: Path, since: str | None, min_calls: int) -> list[Session]:
    """Read every transcript in a directory, newest last.

    Args:
        directory: The project's transcript directory.
        since: Keep sessions whose last activity is on or after this ISO date,
            or None for all of them.
        min_calls: Drop sessions with fewer API calls than this.

    Returns:
        Matching sessions, sorted by date of last activity.

    """
    sessions = []
    for path in sorted(directory.glob("*.jsonl")):
        # mtime is the cheap pre-filter: opening a 150MB transcript to learn it
        # is three weeks old costs more than the whole rest of the run.
        if since:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).strftime("%Y-%m-%d")
            if mtime < since:
                continue
        session = read_session(path)
        if session.calls >= min_calls and (not since or session.last >= since):
            sessions.append(session)
    sessions.sort(key=lambda s: s.last)
    return sessions


def report(sessions: list[Session], *, detail: bool) -> int:
    """Print the census and return the number of sessions over the context bar.

    Args:
        sessions: Sessions to report, in display order.
        detail: Also print the per-session table and the sub-agent split.

    Returns:
        How many sessions averaged more than `HOT_AVG_CONTEXT`.

    """
    if not sessions:
        print("=== sessions: 0 ===")
        print("no matching session transcripts -- nothing to report")
        return 0

    if detail:
        print(
            f"{'session':9} {'date':11} {'calls':>7} {'sub':>6} "
            f"{'avgCtx_k':>9} {'cacheR_M':>9} {'out_k':>8}"
        )
        for s in sessions:
            print(
                f"{s.name:9} {s.last:11} {s.calls:7d} {s.sidechain_calls:6d} "
                f"{s.avg_context / 1e3:9.0f} {s.cache_read / 1e6:9.1f} {s.output / 1e3:8.1f}"
            )
        print()

    calls = sum(s.calls for s in sessions)
    cache_read = sum(s.cache_read for s in sessions)
    cache_write = sum(s.cache_write for s in sessions)
    output = sum(s.output for s in sessions)
    avg_context = cache_read / calls if calls else 0.0
    hot = [s for s in sessions if s.avg_context > HOT_AVG_CONTEXT]

    # Headings in the `=== label: N ===` shape closeout.sh parses with sed.
    print(f"=== sessions: {len(sessions)} ===")
    print(f"=== api calls: {calls} ===")
    print(f"=== avg context per call: {round(avg_context / 1e3)} ===")
    print(f"=== sessions over {HOT_AVG_CONTEXT // 1000}K avg context: {len(hot)} ===")
    print()

    units = (
        cache_read * WEIGHT_CACHE_READ + cache_write * WEIGHT_CACHE_WRITE + output * WEIGHT_OUTPUT
    )
    print(f"{'component':14} {'raw':>12} {'units':>12} {'share':>7}")
    for label, raw, weight in (
        ("cache read", cache_read, WEIGHT_CACHE_READ),
        ("cache write", cache_write, WEIGHT_CACHE_WRITE),
        ("output", output, WEIGHT_OUTPUT),
    ):
        weighted = raw * weight
        share = weighted / units * 100 if units else 0.0
        print(f"{label:14} {raw / 1e6:11.1f}M {weighted / 1e6:11.1f}M {share:6.1f}%")
    if units:
        context_share = cache_read * WEIGHT_CACHE_READ + cache_write * WEIGHT_CACHE_WRITE
        print(f"\ncontext re-reading: {context_share / units * 100:.1f}% of consumption")
    for s in hot:
        print(
            f"!! {s.name} ({s.last}) averaged "
            f"{s.avg_context / 1e3:.0f}K context over {s.calls} calls"
        )
    return len(hot)


def main() -> None:
    """Parse arguments and print the census."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--since", metavar="YYYY-MM-DD", help="sessions last active on or after this date"
    )
    group.add_argument(
        "--all", action="store_true", help="every session ever recorded for this project"
    )
    parser.add_argument("--detail", action="store_true", help="also print the per-session table")
    parser.add_argument(
        "--min-calls", type=int, default=50, help="ignore sessions shorter than this (default 50)"
    )
    parser.add_argument(
        "--repo", type=Path, default=REPO_DIR, help="project checkout to census (default: this one)"
    )
    args = parser.parse_args()

    since = None if args.all else (args.since or datetime.now(tz=UTC).strftime("%Y-%m-%d"))
    directory = transcript_dir(args.repo)
    if not directory.is_dir():
        print("=== sessions: 0 ===")
        print(f"no transcript directory for {args.repo} (looked in {directory})")
        return

    report(collect(directory, since, args.min_calls), detail=args.detail)


if __name__ == "__main__":
    main()

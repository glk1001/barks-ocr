# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# the census is the whole point.
"""Report what a vision pass cost in Claude Code tokens, from the session transcripts.

    uv run --offline python scripts/vision/usage_census.py            # today
    uv run --offline python scripts/vision/usage_census.py --since 2026-09-18
    uv run --offline python scripts/vision/usage_census.py --all --detail
    uv run --offline python scripts/vision/usage_census.py --by-title [--write-ledger]
    uv run --offline python scripts/vision/usage_census.py --trend

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

PER TITLE (`--by-title`). A session usually reads a whole batch, so its total
says nothing about which title was dear. Each API call is credited to the title
the session was working on at that moment: the one whose out-dir
(`barks-vision/<slug>`) or `--title "..."` the most recent tool call named. A
tool call naming several titles (a loop over the batch) shares the calls that
follow it evenly; calls before a session's first mention are its start-up
overhead, shared evenly over its titles; calls more than `IDLE_CALLS` after the
last mention are left uncredited, so tooling work at the end of a session does
not land on the last title read.

A session counts for a title only if it RAN the pipeline on it --
`vision-prep`, `vision-apply`, `vision-mirror` or `closeout.sh` -- within
`SESSION_WINDOW_DAYS` of the ledger row's `recorded` date. Opening an old
out-dir to copy its format, or a corpus sweep that happens to pass a
`--title`, then credits nothing. The first version of this without that
restriction billed 318 calls of a 2026-08-31 cleanup session to a title first
read on 2026-09-23.

This is an attribution, not a meter. Do NOT read a per-title `avg_ctx` off it:
context grows through a session, so a title's average context mostly says where
in the session it was read (measured over 24 batch sessions, median 298K for the
first title against 535K for the last). Calls per page and tokens re-read per
page are the per-title measures, and `--trend` sums them by batch, where the
attribution noise cancels.

`--write-ledger` stores the attribution in the ledger's `calls` and `tokens_m`
columns (millions of cache-read tokens). A row whose sessions are no longer on
disk keeps what it has: Claude Code prunes old transcripts, and the ledger is
the only copy that outlives them. That is also why `--trend` reads the ledger
and not the transcripts.
"""

import argparse
import json
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
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

LEDGER = REPO_DIR / "docs" / "vision-cost-ledger.csv"
TITLE_SEP = " | "

# Per-title attribution. A page costs 2-10 calls and every one of them names the
# out-dir, so 25 calls without a mention means the session has moved on.
IDLE_CALLS = 25
# A batch is read and closed out within a day or two; five days keeps a later
# mirror session while shutting out an unrelated sweep weeks away.
SESSION_WINDOW_DAYS = 5
# `--trend` flags the latest batch when its tokens per page exceed the median of
# the previous TREND_BASELINE batch dates by this factor.
TREND_BASELINE = 5
TREND_HOT_FACTOR = 1.25

SLUG_RE = re.compile(r"barks-vision/([A-Za-z0-9-]+)")
OUT_DIR_RE = re.compile(r"--out-dir[= ]+\S*?barks-vision/([A-Za-z0-9-]+)")
TITLE_RE = re.compile(r"""--title[= ]+(?:\\?"(.+?)\\?"|'(.+?)')""")
CLOSEOUT_TITLE_RE = re.compile(r'closeout\.sh(?:\s+--stage\s+\w+)?\s+\\?"(.+?)\\?"')
WORK_RE = re.compile(r"barks-ocr-vision-(?:prep|apply|mirror)|closeout\.sh")


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


@dataclass
class LedgerRow:
    """One cost-ledger row: its leading fields, and its note exactly as written."""

    fields: dict[str, str]
    raw_note: str

    @property
    def titles(self) -> list[str]:
        """The row's titles; several when the images could not be split."""
        return [t.strip() for t in self.fields["titles"].split(TITLE_SEP)]

    @property
    def recorded(self) -> date:
        """The date the row was written, which anchors its session window."""
        return date.fromisoformat(self.fields["recorded"])


@dataclass
class Credit:
    """API calls and cache-read tokens credited to one title."""

    calls: float = 0.0
    cache_read: float = 0.0
    sessions: set[str] = field(default_factory=set)


def read_ledger(path: Path = LEDGER) -> tuple[list[str], list[str], list[LedgerRow]]:
    """Read the cost ledger in a form that writes back byte for byte.

    The note is the LAST column and by the file's own convention may hold bare
    commas, so it is not CSV-parsed at all: it is everything after the comma that
    ends the field before it. No other field ever holds a comma or a quote, which
    `write_ledger` asserts rather than assumes.

    Args:
        path: The ledger CSV.

    Returns:
        The leading comment lines, the column names, and the data rows.

    """
    lines = path.read_text().splitlines()
    comments = [line for line in lines if line.startswith("#")]
    header, *data = [line for line in lines if not line.startswith("#")]
    columns = header.split(",")
    leading = len(columns) - 1
    rows = []
    for line in data:
        parts = line.split(",", leading)
        rows.append(LedgerRow(dict(zip(columns[:-1], parts[:leading], strict=True)), parts[-1]))
    return comments, columns, rows


def write_ledger(path: Path, comments: list[str], columns: list[str], rows: list[LedgerRow]) -> str:
    """Write the ledger in its own format: comment header, header row, data rows.

    Args:
        path: Where to write it.
        comments: The comment lines, verbatim.
        columns: Column names, in file order; the note is the last.
        rows: The data rows.

    Returns:
        The text written.

    Raises:
        ValueError: A leading field holds a comma or a quote, which would shift
            every column after it.

    """
    out = [*comments, ",".join(columns)]
    for row in rows:
        leading = [row.fields[c] for c in columns[:-1]]
        if any("," in f or '"' in f for f in leading):
            msg = f"ledger field would need quoting: {leading}"
            raise ValueError(msg)
        out.append(",".join([*leading, row.raw_note]))
    text = "\n".join(out) + "\n"
    path.write_text(text)
    return text


def title_slug(title: str) -> str:
    """Return a title's out-dir name, by the rule `vision_prep._slug` uses.

    Args:
        title: The story title.

    Returns:
        The slug, e.g. ``black-wednesday``.

    """
    keep = "".join(c.lower() if c.isalnum() else "-" for c in title)
    return "-".join(filter(None, keep.split("-")))


def _tool_inputs(record: dict) -> list[str]:
    """Return every tool call's input in one assistant record, as JSON text."""
    content = (record.get("message") or {}).get("content") or []
    return [
        json.dumps(block.get("input"), ensure_ascii=False)
        for block in content
        if isinstance(block, dict) and block.get("type") == "tool_use"
    ]


def _named(text: str, by_slug: dict[str, str], titles: set[str]) -> list[str]:
    """Return the ledger titles one tool input names, by out-dir or `--title`."""
    found = [by_slug[s] for s in SLUG_RE.findall(text) if s in by_slug]
    found += [a or b for a, b in TITLE_RE.findall(text) if (a or b) in titles]
    found += [t for t in CLOSEOUT_TITLE_RE.findall(text) if t in titles]
    return list(dict.fromkeys(found))


def _worked_titles(
    records: list[dict], by_slug: dict[str, str], recorded: dict[str, date]
) -> set[str]:
    """Return the titles a session ran the pipeline on inside their window."""
    worked: set[str] = set()
    for record in records:
        day = date.fromisoformat((record.get("timestamp") or "1970-01-01")[:10])
        for text in _tool_inputs(record):
            if not WORK_RE.search(text):
                continue
            named = {by_slug[s] for s in OUT_DIR_RE.findall(text) if s in by_slug}
            named |= set(_named(text, {}, set(recorded)))
            worked |= {t for t in named if abs((day - recorded[t]).days) <= SESSION_WINDOW_DAYS}
    return worked


def _assistant_records(path: Path) -> list[dict]:
    """Return a transcript's assistant records, skipping lines that do not parse."""
    records = []
    for line in path.open(errors="replace"):
        # Cheap reject first, as in read_session: only assistant records matter.
        if '"assistant"' not in line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    return records


def _share(
    ledger_credit: dict[str, Credit], titles: list[str], cache_read: int, session: str
) -> None:
    """Split one API call evenly over the titles it is credited to."""
    for title in titles:
        ledger_credit[title].calls += 1 / len(titles)
        ledger_credit[title].cache_read += cache_read / len(titles)
        ledger_credit[title].sessions.add(session)


def credit_session(
    path: Path,
    by_slug: dict[str, str],
    recorded: dict[str, date],
    ledger_credit: dict[str, Credit],
) -> None:
    """Credit one session's API calls to the titles it was working on.

    Args:
        path: A session JSONL file.
        by_slug: Ledger title for each out-dir slug.
        recorded: Each ledger title's `recorded` date.
        ledger_credit: Running totals per title, updated in place.

    """
    records = _assistant_records(path)
    worked = _worked_titles(records, by_slug, recorded)
    if not worked:
        return
    session = path.stem[:8]
    seen: set[str] = set()
    active: list[str] = []
    idle: int | None = None  # None until the session first names a title
    startup: list[int] = []
    for record in records:
        message = record.get("message") or {}
        usage = message.get("usage") or {}
        message_id = message.get("id")
        if usage and message_id and message_id not in seen:
            seen.add(message_id)
            cache_read = usage.get("cache_read_input_tokens") or 0
            if idle is None:
                startup.append(cache_read)
            elif (idle := idle + 1) <= IDLE_CALLS:
                _share(ledger_credit, active, cache_read, session)
        for text in _tool_inputs(record):
            named = [t for t in _named(text, by_slug, set(recorded)) if t in worked]
            if named:
                active, idle = named, 0
    for cache_read in startup:
        _share(ledger_credit, sorted(worked), cache_read, session)


def credit_titles(directory: Path, rows: list[LedgerRow]) -> dict[str, Credit]:
    """Credit every transcript's calls to the ledger's titles.

    Args:
        directory: The project's transcript directory.
        rows: The ledger rows, which fix the titles and their dates.

    Returns:
        Calls and cache-read tokens per title, for titles any session ran on.

    """
    recorded = {t: row.recorded for row in rows for t in row.titles}
    by_slug = {title_slug(t): t for t in recorded}
    ledger_credit: dict[str, Credit] = defaultdict(Credit)
    for path in sorted(directory.glob("*.jsonl")):
        credit_session(path, by_slug, recorded, ledger_credit)
    return ledger_credit


def by_title(directory: Path, *, write: bool) -> None:
    """Print each ledger row's credited cost, and store it when asked.

    Args:
        directory: The project's transcript directory.
        write: Store `calls` and `tokens_m` in the ledger.

    """
    comments, columns, rows = read_ledger()
    ledger_credit = credit_titles(directory, rows)
    print(
        f"{'vol':>3} {'title':42} {'pages':>5} {'calls':>6} {'Mtok':>7} "
        f"{'calls/pg':>8} {'Mtok/pg':>7}  sessions"
    )
    changed = 0
    for row in rows:
        mine = [ledger_credit[t] for t in row.titles if t in ledger_credit]
        calls = sum(c.calls for c in mine)
        pages = int(row.fields["pages"])
        label = f"{row.fields['volume']:>3} {row.fields['titles'][:42]:42} {pages:5d}"
        if calls < 1:
            print(f"{label} {'--':>6}  (no session on disk; ledger kept)")
            continue
        tokens_m = sum(c.cache_read for c in mine) / 1e6
        sessions = ",".join(sorted({s for c in mine for s in c.sessions}))
        print(
            f"{label} {calls:6.0f} {tokens_m:7.1f} "
            f"{calls / pages:8.1f} {tokens_m / pages:7.2f}  {sessions}"
        )
        new = {"calls": str(round(calls)), "tokens_m": f"{tokens_m:.1f}"}
        if any(row.fields.get(k) != v for k, v in new.items()):
            row.fields.update(new)
            changed += 1
    print(f"\n=== ledger rows changed: {changed} of {len(rows)} ===")
    if write and changed:
        write_ledger(LEDGER, comments, columns, rows)
        print(f"wrote {LEDGER}")


def trend() -> None:
    """Print cost per page by batch date, read from the ledger alone."""
    _, _, rows = read_ledger()
    # pages, images, pages with a cost, calls, Mtok -- per recorded date
    days: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0.0])
    for row in rows:
        day = days[row.fields["recorded"]]
        day[0] += int(row.fields["pages"])
        day[1] += int(row.fields["images"])
        if row.fields.get("calls") and row.fields.get("tokens_m"):
            day[2] += int(row.fields["pages"])
            day[3] += int(row.fields["calls"])
            day[4] += float(row.fields["tokens_m"])
    print(f"{'recorded':10} {'pages':>5} {'img/pg':>6} {'calls/pg':>8} {'Mtok/pg':>7}")
    per_page = []
    for day, (pages, images, costed, calls, tokens) in sorted(days.items()):
        cost = f"{calls / costed:8.1f} {tokens / costed:7.2f}" if costed else f"{'--':>8} {'--':>7}"
        print(f"{day:10} {pages:5.0f} {images / pages:6.2f} {cost}")
        if costed:
            per_page.append(tokens / costed)
    if len(per_page) < 2:  # noqa: PLR2004 -- a latest and at least one to compare it to
        return
    latest = per_page[-1]
    previous = per_page[-1 - TREND_BASELINE : -1]
    baseline = statistics.median(previous)
    # Headings in the `=== label: N ===` shape closeout.sh parses with sed.
    print(f"\n=== latest Mtok/page: {latest:.2f} ===")
    print(f"=== baseline Mtok/page: {baseline:.2f} (median of {len(previous)}) ===")
    if latest > baseline * TREND_HOT_FACTOR:
        print(f"!! the latest batch cost {latest / baseline:.2f}x the baseline per page")


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
        "--by-title", action="store_true", help="credit calls to each ledger title and print them"
    )
    parser.add_argument(
        "--write-ledger", action="store_true", help="with --by-title: store calls and tokens_m"
    )
    parser.add_argument(
        "--trend", action="store_true", help="cost per page by batch date, from the ledger alone"
    )
    parser.add_argument(
        "--min-calls", type=int, default=50, help="ignore sessions shorter than this (default 50)"
    )
    parser.add_argument(
        "--repo", type=Path, default=REPO_DIR, help="project checkout to census (default: this one)"
    )
    args = parser.parse_args()

    if args.trend:
        trend()
        return
    since = None if args.all else (args.since or datetime.now(tz=UTC).strftime("%Y-%m-%d"))
    directory = transcript_dir(args.repo)
    if not directory.is_dir():
        print("=== sessions: 0 ===")
        print(f"no transcript directory for {args.repo} (looked in {directory})")
        return

    if args.by_title:
        by_title(directory, write=args.write_ledger)
        return
    report(collect(directory, since, args.min_calls), detail=args.detail)


if __name__ == "__main__":
    main()

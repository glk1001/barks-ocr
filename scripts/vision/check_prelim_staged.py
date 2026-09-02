# ruff: noqa: INP001, T201 -- a standalone script, not a package module, and printing
# what it refused is the whole point.
"""Pre-commit checks for the prelim OCR data repo: volume span, and JSON format.

    uv run --offline python scripts/vision/check_prelim_staged.py [--repo DIR]

Installed as the prelim repo's `.git/hooks/pre-commit`, which is a three-line
forwarder into this file so the logic stays version-controlled here rather than
in an unversioned `.git/hooks/`. Bypass a single commit with `--no-verify`.

TWO CHECKS.

**Does the staged set span more than one volume?** A vision pass touches one
title, and a volume pathspec matches the decade above it -- `"Carl Barks Vol. 1*"`
also matches Vol. 19, and `"Carl Barks Vol. 2*"` matches Vol. 20 through Vol. 29,
ten volumes at once. The repo usually holds unrelated in-progress work, so a glob
that over-matches sweeps somebody else's editing session into your commit.

This WARNS; it does not refuse. Replaying the check over all 380 commits found
**19 that span more than one volume, and none of them a mistake**: they are the
corpus-wide sweeps this workflow runs on purpose -- the `other:` speaker audit
(6 volumes), "settle every outstanding vision text correction" (3), "confirm the
last 34 type corrections in the corpus" (2), an em-dash fix that reached 23. The
spans run from 2 to 23 for deliberate work, so neither the fact of spanning nor
its size separates an accident from intent, and a gate firing on 5% of real
commits would be trained away inside a month. A named, counted warning printed
at commit time still makes "I meant one title and staged ten volumes" obvious.

It does NOT hardcode Vol. 19. That directory is tracked and its owner commits it
under their own name; a hook cannot tell who is committing, and one that refused
it outright would block the person it belongs to.

**Every staged prelim JSON must round-trip byte-exactly.** This one refuses.
The format is `json.dumps(d, indent=4)`, ASCII-escaped, no trailing newline. A one-string
edit written back with any other setting reformats the whole file and the diff
then hides the real change. Measured across a 300-file random sample of the
11,120 on disk: 300 round-trip exactly, 0 exceptions. The backlog is empty, so
unlike the rest of the checks in `docs/invariant-suite.md` this one is safe to
refuse on from the day it is installed.

WHAT THIS CANNOT SEE. By the time a pre-commit hook runs, git has already
expanded a directory or glob pathspec into individual paths, so "you staged a
directory" is not recoverable here -- only its consequences are. Nor can it see
a file you *meant* to stage and did not.
"""

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

VOLUME_RE = re.compile(r"Carl Barks Vol\. (\d+)")

# suffix -> (indent, trailing newline). Measured over every tracked file at
# HEAD; see the module docstring for the counts behind each row.
FORMATS: dict[str, tuple[int, bool]] = {
    "-gemini-prelim-groups.json": (4, False),
    "-page-capture.json": (2, True),
    "-panel-descriptions.json": (2, True),
}
# Only this one is consistent enough on disk to refuse a commit over.
GATED = ("-gemini-prelim-groups.json",)

MAX_LISTED = 8  # per group, before the listing is elided


def staged_paths(repo: Path) -> list[str]:
    """Return the repo-relative paths staged for commit, additions and edits only.

    Args:
        repo: the prelim repo's working tree.

    Returns:
        Staged paths, excluding deletions (there is nothing left to parse).

    """
    out = subprocess.run(  # noqa: S603 -- fixed argv, no shell, path from the caller.
        ["git", "-C", str(repo), "diff", "--cached", "--name-only", "-z", "--diff-filter=d"],  # noqa: S607
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def volume_of(path: str) -> str | None:
    """Return the volume number a staged path sits under, or None."""
    match = VOLUME_RE.search(path)
    return match.group(1) if match else None


def check_span(paths: list[str]) -> list[str]:
    """Note a staged set covering more than one volume. Advisory, never fatal.

    Args:
        paths: staged repo-relative paths.

    Returns:
        Warning lines; empty if the set covers at most one volume.

    """
    by_volume: dict[str, int] = defaultdict(int)
    for path in paths:
        volume = volume_of(path)
        if volume:
            by_volume[volume] += 1

    if len(by_volume) <= 1:
        return []

    listed = sorted(by_volume.items(), key=lambda kv: -kv[1])
    lines = [f"staged set spans {len(by_volume)} volumes:"]
    lines += [f"    Vol. {v:<3} {n:>5} file(s)" for v, n in listed[:MAX_LISTED]]
    if len(listed) > MAX_LISTED:
        lines.append(f"    ... and {len(listed) - MAX_LISTED} more")
    lines.append("  A vision pass touches one title. A volume pathspec matches the")
    lines.append('  decade above it -- "Carl Barks Vol. 2*" is Vol. 20 through 29.')
    lines.append("  Deliberate corpus sweeps look like this too -- check the list, not the fact.")
    return lines


def check_format(repo: Path, paths: list[str]) -> tuple[list[str], list[str]]:
    """Compare each staged JSON against the format its kind is written in.

    Args:
        repo: the prelim repo's working tree.
        paths: staged repo-relative paths.

    Returns:
        (fatal lines, advisory lines). Only groups files are fatal.

    """
    fatal: list[str] = []
    noted: list[str] = []
    for path in paths:
        suffix = next((k for k in FORMATS if path.endswith(k)), None)
        if suffix is None:
            continue
        indent, newline = FORMATS[suffix]
        # The staged content, not the working tree's -- they can differ.
        blob = subprocess.run(  # noqa: S603 -- fixed argv, no shell.
            ["git", "-C", str(repo), "show", f":{path}"],  # noqa: S607
            capture_output=True,
            check=False,
        )
        if blob.returncode != 0:
            continue
        raw = blob.stdout
        try:
            want = json.dumps(json.loads(raw), indent=indent).encode()
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            fatal.append(f"{path}  ({type(exc).__name__})")
            continue
        if newline:
            want += b"\n"
        if raw == want:
            continue
        note = f"{path}  (expected indent={indent}"
        note += ", trailing newline)" if newline else ", no trailing newline)"
        (fatal if suffix in GATED else noted).append(note)

    return _format_lines(fatal, fatal=True), _format_lines(noted, fatal=False)


def _format_lines(offenders: list[str], *, fatal: bool) -> list[str]:
    """Render one offender list as output lines, or nothing when it is empty."""
    if not offenders:
        return []
    what = "not in the expected format" if fatal else "written in an unexpected format"
    lines = [f"{len(offenders)} staged file(s) {what}:"]
    lines += [f"    {o}" for o in offenders[:MAX_LISTED]]
    if len(offenders) > MAX_LISTED:
        lines.append(f"    ... and {len(offenders) - MAX_LISTED} more")
    if fatal:
        lines.append("  A scripted edit written back any other way reformats the whole file")
        lines.append("  and the diff then hides the real change.")
    return lines


def _emit(kind: str, count: int, lines: list[str]) -> None:
    """Print one labelled block of check output."""
    print(f"\nprelim pre-commit: {kind} ({count} staged path(s))\n")
    for line in lines:
        print(f"  {line}" if not line.startswith(" ") else line)


def main() -> None:
    """Warn on a multi-volume stage, and refuse a badly formatted one."""
    argv = sys.argv[1:]
    repo = Path(argv[argv.index("--repo") + 1]) if "--repo" in argv else Path.cwd()

    paths = staged_paths(repo)
    if not paths:
        return

    # Advisory: the history says spanning is deliberate 19 times out of 19, so
    # this is here to be read, not to stop anything.
    warnings = check_span(paths)
    if warnings:
        _emit("NOTE", len(paths), warnings)

    errors, noted = check_format(repo, paths)
    if noted:
        _emit("NOTE", len(paths), noted)
    if not errors:
        return

    _emit("REFUSING", len(paths), errors)
    print("\n  Bypass this commit only: git commit --no-verify\n")
    raise SystemExit(1)


if __name__ == "__main__":
    main()

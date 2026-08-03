# ruff: noqa: T201
"""Report which titles the vision pass has read, and under which rules.

Derived from the corpus on every run rather than kept in a ledger beside it.
That is a deliberate difference from the sibling repo's ``restore-ledger.jsonl``
and ``upscale-ledger.jsonl``, and the reason is that the two workloads are not
the same shape.  A restore run is long, unattended and can be stopped half way
through, so its ledger exists to answer "where did I get to" for work that
cannot simply be repeated.  A vision pass is one title in one session and is
idempotent -- applying a result twice changes nothing -- so there is no lost
position to recover, and a separate record of what is on disk could only drift
away from what is actually on disk.

What a scan cannot recover is what a *human review* concluded, because that is
an event rather than a state.  See ``docs/vision-pass.md``; the agreed shape is
to store the pass's original call on the group beside the reviewer's answer, not
to add a ledger.

The scan is fast enough to be a routine question: the whole corpus is ~11,000
small JSON files and a full report takes a few seconds.
"""

import collections
import json
import re
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from comic_utils.common_typer_options import LogLevelArg

from barks_ocr.cli_setup import init_logging
from barks_ocr.utils.vision_schema import (
    CAPTURE_PROMPT_VERSION,
    CAPTURE_PROMPT_VERSION_KEY,
    CAPTURE_RULES,
    SPEAKER_KEY,
)

APP_LOGGING_NAME = "visstat"

CAPTURE_SUFFIX = "-page-capture.json"
PRELIM_GLOB = "*-easyocr-gemini-prelim-groups.json"
_VOL_RE = re.compile(r"Vol\.? (\d+)")

# The cohort that predates provenance being written at all.  Its capture records
# carry nulls, which is the only thing identifying them.
UNSTAMPED = "unstamped (pre-2026-08-03)"


class VolumeStat:
    """One volume's tally."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pages = 0
        self.annotated = 0
        self.captured = 0
        self.groups = 0
        self.annotated_groups = 0
        self.versions: collections.Counter[str] = collections.Counter()


def _volume_of(path: Path) -> tuple[int, str]:
    """Return the (number, directory name) of the volume a prelim file sits in."""
    name = path.parent.name
    match = _VOL_RE.search(name)
    return (int(match.group(1)) if match else 0, name)


def scan(prelim_dir: Path) -> dict[str, VolumeStat]:
    """Walk the prelim tree and tally vision coverage per volume.

    Args:
        prelim_dir: The root holding one directory per Fantagraphics volume.

    Returns:
        The per-volume tallies, keyed by directory name.

    """
    stats: dict[str, VolumeStat] = {}
    for prelim in sorted(prelim_dir.glob(f"*/{PRELIM_GLOB}")):
        _num, vol_name = _volume_of(prelim)
        stat = stats.setdefault(vol_name, VolumeStat(vol_name))
        stat.pages += 1

        groups = json.loads(prelim.read_text()).get("groups", {})
        stat.groups += len(groups)
        annotated = [g for g in groups.values() if g.get(SPEAKER_KEY)]
        if not annotated:
            continue
        stat.annotated += 1
        stat.annotated_groups += len(annotated)

        capture = prelim.parent / (prelim.name.split("-")[0] + CAPTURE_SUFFIX)
        if not capture.is_file():
            continue
        stat.captured += 1
        record = json.loads(capture.read_text())
        version = record.get(CAPTURE_PROMPT_VERSION_KEY)
        stat.versions[UNSTAMPED if version is None else f"v{version}"] += 1
    return stats


def _report(stats: dict[str, VolumeStat], *, show_all: bool) -> None:
    """Print the tally, widest number last."""
    touched = {k: v for k, v in stats.items() if v.annotated}
    shown = stats if show_all else touched

    print(f"{'volume':52} {'pages':>6} {'read':>6} {'capture':>8} {'groups':>8}")
    for name in sorted(shown, key=lambda n: _volume_of(Path(n) / "x")):
        s = shown[name]
        print(
            f"{name[:52]:52} {s.pages:>6} {s.annotated:>6} {s.captured:>8} {s.annotated_groups:>8}"
        )

    pages = sum(s.pages for s in stats.values())
    read = sum(s.annotated for s in stats.values())
    captured = sum(s.captured for s in stats.values())
    print(
        f"\n{read} of {pages} page(s) read ({100 * read / pages:.1f}%), "
        f"{captured} with a page capture, {pages - read} remaining."
    )
    print(f"{len(touched)} of {len(stats)} volume(s) touched.")

    versions: collections.Counter[str] = collections.Counter()
    for s in stats.values():
        versions.update(s.versions)
    if not versions:
        return
    print(f"\ncapture prompt version (current is v{CAPTURE_PROMPT_VERSION}):")
    for version, count in sorted(versions.items()):
        note = ""
        if version == UNSTAMPED:
            note = "  <- read before provenance was written; rules unknown"
        elif version != f"v{CAPTURE_PROMPT_VERSION}":
            note = "  <- read under older rules"
        print(f"   {version:26} {count:>5} page(s){note}")
    print(f"\nrules in force now: {', '.join(CAPTURE_RULES)}")


app = typer.Typer()


@app.command(help="Report which pages the vision pass has read, and under which rules.")
def main(
    show_all: Annotated[
        bool,
        typer.Option("--all", help="List every volume, not only those with vision data."),
    ] = False,
    log_level_str: LogLevelArg = "WARNING",
) -> None:
    """Scan the prelim tree and report vision-pass coverage."""
    init_logging(APP_LOGGING_NAME, "vision-status.log", log_level_str)
    _report(scan(OCR_PRELIM_DIR), show_all=show_all)


if __name__ == "__main__":
    app()

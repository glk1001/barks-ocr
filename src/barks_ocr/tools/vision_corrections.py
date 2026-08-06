# ruff: noqa: T201
"""Find the text and type corrections a vision pass proposed that nobody has acted on.

The speaker side of a vision pass has three places a missed call surfaces --
``vision_apply --queue-speakers``, ``barks-ocr-speaker-queue`` and the
``speaker_reviewed`` flag the editor stamps. The other two corrections a pass
makes had none of that, and an audit on 2026-08-06 found what that costs: five
text corrections outstanding across three volumes, and 52 type corrections of
which none had ever been reviewed.

They went missing for different reasons, and this tool closes both.

**Text** was a switch nobody flipped. ``vision_apply --queue-out`` has always
written a text-correction queue, and ``_correction_applied`` has always kept it
idempotent, but the run procedure passed only ``--out-dir`` and
``--capture-model``, so the queue was never generated on any title. The
proposals were never lost -- ``vision_corrected_text`` sits on the group
forever -- they were simply never handed to anybody.

**Type** had no mechanism at all. See ``TYPE_REVIEWED_KEY`` for why it needs a
flag where text does not.

Reading the **corpus** rather than a ``vision_prep`` out-dir is what makes this
answerable for old runs. Out-dirs are scratch and several no longer validate
against the current schema, so their queues cannot be regenerated through
``vision_apply`` even in principle -- but every proposal ever made is still on
the group. Same reasoning as ``speaker_queue``.

Both engines by default, because a text correction is a change to ``ai_text``
and each engine holds its own copy. ``vision_mirror`` copies the ``vision_``
annotations across but not ``ai_text`` itself -- rightly, since the two engines
disagree about that field in general -- so a correction applied to one engine
leaves the other still wrong. The 2026-08-06 audit found all five outstanding
on both sides.

```bash
barks-ocr-vision-corrections                        # everything outstanding
barks-ocr-vision-corrections --title "Snow Fun"
barks-ocr-vision-corrections --text -o queue-text.txt
barks-ocr-vision-corrections --type --volume 1-2 -o queue-type.txt
```

Read-only apart from the queue file it writes.
"""

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from barks_fantagraphics.speech_markup import strip_markup
from comic_utils.common_typer_options import TitleArg, VolumesArg
from loguru import logger

from barks_ocr.utils.title_selection import resolve_titles
from barks_ocr.utils.vision_schema import (
    TYPE_KEY,
    TYPE_REVIEWED_KEY,
    TYPE_WAS_KEY,
    VISION_CORRECTED_TEXT_KEY,
    VISION_TEXT_ISSUE,
    VISION_TEXT_REVIEWED_KEY,
    VISION_TYPE_ISSUE,
)

app = typer.Typer()

# Both, unless --engine narrows it. See the module docstring: `ai_text` is not
# mirrored, so a text correction is outstanding on each engine independently.
ALL_ENGINES: tuple[OcrTypes, ...] = (OcrTypes.EASYOCR, OcrTypes.PADDLEOCR)

# How much of a corrected line to show before cutting it. Long enough that the
# changed word is usually visible, short enough that a 40-row audit still fits
# on a screen; --verbose prints them whole.
SNIPPET = 60


@dataclass(frozen=True)
class Correction:
    """One outstanding correction, and where it lives."""

    volume: int
    fanta_page: str
    group_id: str
    title: str
    engine: OcrTypes
    issue: str
    # What the group says now, and what the pass said the art says. Both empty
    # for a type correction that was never disputed by a second reader.
    stored: str
    proposed: str

    def line(self) -> str:
        """Return the queue-file line for this correction."""
        return f"{self.volume} {self.fanta_page} {self.engine.value} {self.group_id} {self.issue}"

    def sort_key(self) -> tuple[int, str, int, str]:
        """Volume, page, group, engine -- the order the reviewer asked queues to be in."""
        return (self.volume, self.fanta_page, int(self.group_id), self.engine.value)


def _text_correction(group: dict) -> tuple[str, str] | None:
    """Return (stored, proposed) when a text correction is still outstanding.

    Two ways out, because a correction can be finished by being taken *or*
    turned down:

    Accepted -- the stored ``ai_text`` now says what the proposal says. Markup
    is stripped from both sides, matching ``vision_apply``: a reviewer applying
    a correction in the editor keeps the emphasis tags, so the stored text
    legitimately carries markup the proposal -- written before the tags existed
    -- never had. Comparing raw would re-offer finished work forever, which is
    exactly what an audit that skipped the stripping reported before this was
    written.

    Rejected -- ``vision_text_reviewed`` is set and the text was deliberately
    left alone. Without this the queue has no way to hear "no", and a
    correction the reviewer disagreed with is offered again on every run.
    """
    proposed = group.get(VISION_CORRECTED_TEXT_KEY)
    if not proposed or group.get(VISION_TEXT_REVIEWED_KEY):
        return None
    stored = group.get("ai_text") or ""
    if strip_markup(stored) == strip_markup(proposed):
        return None
    return stored, proposed


def _type_correction(group: dict) -> tuple[str, str] | None:
    """Return (was, now) when a type correction has not been reviewed.

    Unlike the text side there is nothing to compare, so this rests entirely on
    the flag -- see ``TYPE_REVIEWED_KEY``.
    """
    if TYPE_WAS_KEY not in group or group.get(TYPE_REVIEWED_KEY):
        return None
    return group.get(TYPE_WAS_KEY) or "", group.get(TYPE_KEY) or ""


def _collect(  # noqa: PLR0913
    comics_database: ComicsDatabase,
    speech_groups: SpeechGroups,
    titles: list[str],
    engines: tuple[OcrTypes, ...],
    skipped: list[str],
    *,
    want_text: bool,
    want_type: bool,
) -> list[Correction]:
    """Return every outstanding correction across *titles*, appending to *skipped*.

    A title whose panel-segments file is older than its page image raises out of
    the page walk -- an mtime gate, not corruption. It is caught here so one
    stale volume cannot stop a corpus-wide audit, and the title is appended to
    *skipped* so the caller can say so.

    Deliberately not swallowed. ``vision_status`` logs this at DEBUG, which is
    why an affected title just disappears from ``--titles`` and ``--todo`` with
    a denominator quietly one smaller. An audit whose whole purpose is "is
    anything outstanding?" cannot answer "no" while silently not having looked.
    """
    found: list[Correction] = []
    for title_str in titles:
        title = STR_TITLE_TO_ENUM[title_str]
        volume = comics_database.get_fanta_volume_int(title_str)
        try:
            page_groups = speech_groups.get_speech_page_groups(title, skip_missing=True)
        except RuntimeError as exc:
            logger.debug(f'Skipping "{title_str}": {exc}')
            skipped.append(title_str)
            continue
        for page_group in page_groups:
            if page_group.ocr_index not in engines:
                continue
            for group_id, group in page_group.speech_page_json.get("groups", {}).items():
                checks = (
                    (want_text, VISION_TEXT_ISSUE, _text_correction(group)),
                    (want_type, VISION_TYPE_ISSUE, _type_correction(group)),
                )
                for wanted, issue, pair in checks:
                    if not wanted or pair is None:
                        continue
                    found.append(
                        Correction(
                            volume=volume,
                            fanta_page=page_group.fanta_page,
                            group_id=group_id,
                            title=title_str,
                            engine=page_group.ocr_index,
                            issue=issue,
                            stored=pair[0],
                            proposed=pair[1],
                        )
                    )
    return found


def _show(value: str, *, verbose: bool) -> str:
    """Render one side of a correction for the console."""
    shown = value.replace("\n", "\\n")
    if not verbose and len(shown) > SNIPPET:
        shown = shown[:SNIPPET] + "..."
    return shown


def _report(found: list[Correction], *, verbose: bool) -> None:
    """Print the corrections, grouped by issue kind."""
    for issue in (VISION_TEXT_ISSUE, VISION_TYPE_ISSUE):
        rows = [c for c in found if c.issue == issue]
        if not rows:
            continue
        print(f"\n=== {issue} ({len(rows)}) ===")
        for c in sorted(rows, key=Correction.sort_key):
            where = f"  vol {c.volume:<3} {c.fanta_page} {c.engine.value:<10} g{c.group_id:<4}"
            print(f"{where} {c.title}")
            if issue == VISION_TEXT_ISSUE:
                print(f"      stored: {_show(c.stored, verbose=verbose)}")
                print(f"      art:    {_show(c.proposed, verbose=verbose)}")
            else:
                print(f"      type:   {c.stored} -> {c.proposed}")


def _report_skipped(skipped: list[str]) -> None:
    """Say which titles could not be read, so a clean result is never overstated."""
    if not skipped:
        return
    print(f"\n!! {len(skipped)} title(s) NOT checked -- stale panel-segments mtime:")
    for title_str in skipped:
        print(f"     {title_str}")
    print("   Verify the segmentation still matches the image before re-running.")


@app.command(help="List text and type corrections a vision pass proposed that nobody has acted on.")
def main(  # noqa: PLR0913
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Write a kivy-editor queue file as well."),
    ] = None,
    engine_str: Annotated[
        str,
        typer.Option(
            "--engine",
            help="Restrict to one engine. Both by default, because `ai_text` is not mirrored.",
        ),
    ] = "",
    text_only: Annotated[
        bool, typer.Option("--text", help="Only outstanding text corrections.")
    ] = False,
    type_only: Annotated[
        bool, typer.Option("--type", help="Only unreviewed type corrections.")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Print corrected text in full rather than clipped.")
    ] = False,
) -> None:
    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    titles = resolve_titles(comics_database, volumes_str, title_str)
    engines = (OcrTypes(engine_str),) if engine_str else ALL_ENGINES

    # Neither flag means both kinds, which is the useful default for "is anything
    # outstanding?" -- the question this tool exists to answer.
    want_text = text_only or not type_only
    want_type = type_only or not text_only

    skipped: list[str] = []
    found = _collect(
        comics_database,
        speech_groups,
        titles,
        engines,
        skipped,
        want_text=want_text,
        want_type=want_type,
    )
    read = len(titles) - len(skipped)

    if not found:
        print(f"Nothing outstanding across {read} title(s).")
        _report_skipped(skipped)
        return

    _report(found, verbose=verbose)

    by_issue = Counter(c.issue for c in found)
    print(f"\n{len(found)} outstanding across {read} title(s):")
    for issue, count in sorted(by_issue.items()):
        print(f"  {count:>4}  {issue}")
    by_volume = Counter(c.volume for c in found)
    print("  by volume: " + ", ".join(f"vol {v}: {n}" for v, n in sorted(by_volume.items())))

    if out is not None:
        header = f"# vision-check corrections -- {len(found)} outstanding\n"
        lines = [c.line() for c in sorted(found, key=Correction.sort_key)]
        path = out.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(header + "\n".join(lines) + "\n")
        print(f'\nWrote "{path}" ({len(lines)} entries).')
        print(f"  uv run barks-ocr-kivy-editor -- --queue-file {path}")

    _report_skipped(skipped)


if __name__ == "__main__":
    sys.exit(app())

# ruff: noqa: T201
"""Export a story's speech as an ordered script.

The OCR corpus stores speech per page, keyed by an opaque group id.  That is the
right shape for correcting it and the wrong shape for reading it: nothing in the
prelim JSON says which line comes first, and a page's groups only fall into
reading order because ``renumber_groups`` happens to have sorted them.

This assembles the pieces already on disk — the speech, the panel numbers, and
the speaker attributions the vision pass writes — into one ordered document per
title.  It runs a full title in a second or so and needs no vision session,
which makes it the cheapest possible check that ``(title, page, panel_num)``
actually addresses the corpus.

**The output is verbatim comic dialogue and never leaves this machine.**  It is
the same material the OCR corpus deliberately keeps in a private repo; see
``docs/vision-pass.md``.

Read-only with respect to the corpus.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups, SpeechPageGroup, SpeechText
from comic_utils.common_typer_options import TitleArg, VolumesArg
from loguru import logger

from barks_ocr.utils.title_selection import resolve_titles
from barks_ocr.utils.vision_schema import SPEAKER_KEY

app = typer.Typer()

# Mirrors `speech_groupers._group_sort_key`, which is the canonical reading order
# for this corpus and which `renumber_groups` writes to disk.  Bubbles whose tops
# land in the same band count as one row and read left-to-right.  Kept in step
# with that function by hand: it is private, and duplicating one constant beats
# reaching across the package boundary for it.
Y_BUCKET_PX = 100

# `panel_num` for a group the grouper could not place in any panel.  These are
# real lines and must appear in the script; they sort to the end of their page.
UNPLACED_PANEL = -1
# The sentinel `speech_groupers._group_sort_key` uses to push those groups last.
UNPLACED_SORTS_AFTER = 999

# Types that are not someone speaking. Shown as a marker so a script reads
# honestly rather than turning a shop sign into a character's line.
NON_SPEECH_TYPES = frozenset({"sound_effect", "background"})

# Written when the vision pass has attributed some of a page's groups but not
# this one, so a partially-attributed story does not read as if the blanks were
# deliberate silences.
NO_SPEAKER = "-"

TEXT_FORMAT = "text"
JSON_FORMAT = "json"

HEADER_RULE = "=" * 78

# Stamped on every script, in both formats. The publication class is a property
# of the data (see `utils/vision_schema.py`), so it travels with the artifact
# rather than living only in the documentation.
LOCAL_ONLY_NOTE = "Verbatim comic dialogue. Local-only -- do not publish or redistribute."


@dataclass(frozen=True, slots=True)
class Line:
    """One speech group, placed in reading order."""

    fanta_page: str
    panel_num: int
    group_id: str
    speaker: str
    type: str
    text: str

    @property
    def is_placed(self) -> bool:
        """Whether the grouper managed to put this line in a panel."""
        return self.panel_num != UNPLACED_PANEL


def _within_panel_key(speech: SpeechText) -> tuple[float, float]:
    """Return the (banded y, x) sort key that orders bubbles inside one panel."""
    min_y = min(point[1] for point in speech.text_box)
    min_x = min(point[0] for point in speech.text_box)
    return round(min_y / Y_BUCKET_PX) * Y_BUCKET_PX, min_x


def _page_lines(page_group: SpeechPageGroup) -> list[Line]:
    """Return one page's groups in reading order.

    ``SpeechPageGroup.get_panel_groups`` is not used here: it drops every group
    whose ``panel_num`` is -1, which would silently lose real dialogue from the
    script.  Unplaced groups are kept and sorted to the end of the page instead.

    Args:
        page_group: The page to read.

    Returns:
        The page's lines, ordered by panel, then top-to-bottom, then left-to-right.

    """
    speakers = {
        group_id: group.get(SPEAKER_KEY)
        for group_id, group in page_group.speech_page_json.get("groups", {}).items()
    }
    any_speaker = any(speakers.values())

    def sort_key(speech: SpeechText) -> tuple[int, float, float]:
        # An unplaced group has no panel to sort within, so it goes after every
        # placed one. Matches `speech_groupers._group_sort_key`, which uses the
        # same sentinel.
        panel = speech.panel_num if speech.panel_num != UNPLACED_PANEL else UNPLACED_SORTS_AFTER
        return (panel, *_within_panel_key(speech))

    ordered = sorted(page_group.speech_groups.values(), key=sort_key)

    return [
        Line(
            fanta_page=page_group.fanta_page,
            panel_num=speech.panel_num,
            group_id=speech.group_id,
            speaker=(speakers.get(speech.group_id) or NO_SPEAKER) if any_speaker else "",
            type=speech.type or "",
            text=speech.ai_text,
        )
        for speech in ordered
    ]


def _title_lines(
    speech_groups: SpeechGroups, title_str: str, engine: OcrTypes
) -> tuple[list[Line], list[str]]:
    """Return one title's lines in page order, plus the pages that had no OCR.

    Only one engine is read.  The two engines' group ids do not correspond, so
    interleaving them would produce a script in which the same line appears
    twice under two different numbers.

    Args:
        speech_groups: The corpus accessor.
        title_str: The canonical story title.
        engine: Which OCR pass to read.

    Returns:
        A ``(lines, missing_pages)`` pair.

    """
    title = STR_TITLE_TO_ENUM[title_str]
    pages = [
        page_group
        for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True)
        if page_group.ocr_index == engine
    ]
    pages.sort(key=lambda p: p.fanta_page)

    lines = [line for page_group in pages for line in _page_lines(page_group)]
    missing = [m.fanta_page for m in speech_groups.get_missing_prelim_pages(title)]
    return lines, sorted(set(missing))


def _format_text(title_str: str, volume: int, engine: OcrTypes, lines: list[Line]) -> str:
    """Render the script as an indented, page-and-panel document."""
    speakers_known = any(line.speaker for line in lines)
    width = max((len(line.speaker) for line in lines), default=0)

    pages = len({line.fanta_page for line in lines})
    out: list[str] = [
        HEADER_RULE,
        title_str,
        f"Fantagraphics volume {volume} - {engine.value} - {pages} page(s), {len(lines)} line(s)",
        "",
        LOCAL_ONLY_NOTE,
        HEADER_RULE,
    ]

    page = panel = None
    for line in lines:
        if line.fanta_page != page:
            page = line.fanta_page
            panel = None
            out += ["", f"-- page {page} " + "-" * 58]
        if line.panel_num != panel:
            panel = line.panel_num
            label = f"panel {panel}" if line.is_placed else "unplaced"
            out += ["", f"  {label}"]

        marker = f" [{line.type}]" if line.type in NON_SPEECH_TYPES else ""
        prefix = f"    {line.speaker.ljust(width)}  " if speakers_known else "    "
        body = line.text.splitlines() or [""]
        out.append(f"{prefix}{body[0]}{marker}")
        # Continuation lines hang under the first, so a multi-line balloon stays
        # one visual block rather than reading as several separate lines.
        out += [" " * len(prefix) + part for part in body[1:]]

    return "\n".join(out) + "\n"


def _format_json(title_str: str, volume: int, engine: OcrTypes, lines: list[Line]) -> str:
    """Render the script as machine-readable JSON."""
    payload = {
        "title": title_str,
        "volume": volume,
        "engine": engine.value,
        "publication_class": "VERBATIM",
        "note": LOCAL_ONLY_NOTE,
        "lines": [
            {
                "page": line.fanta_page,
                "panel": line.panel_num,
                "group_id": line.group_id,
                "speaker": line.speaker or None,
                "type": line.type or None,
                "text": line.text,
            }
            for line in lines
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _slug(title_str: str) -> str:
    """Return a filename-safe form of a story title."""
    keep = [c.lower() if c.isalnum() else "-" for c in title_str]
    return "-".join(filter(None, "".join(keep).split("-")))


@dataclass
class Totals:
    """What one run produced, for the closing summary."""

    titles: int = 0
    lines: int = 0
    unplaced: int = 0
    missing: dict[str, list[str]] = field(default_factory=dict)


def _export(  # noqa: PLR0913
    comics_database: ComicsDatabase,
    speech_groups: SpeechGroups,
    title_list: list[str],
    engine: OcrTypes,
    out_dir: Path | None,
    out_format: str,
) -> Totals:
    """Render every selected title, to files or to stdout. Returns the tallies."""
    render = _format_text if out_format == TEXT_FORMAT else _format_json
    suffix = ".txt" if out_format == TEXT_FORMAT else ".json"
    totals = Totals()

    for title_str in title_list:
        lines, missing = _title_lines(speech_groups, title_str, engine)
        if missing:
            totals.missing[title_str] = missing
        if not lines:
            logger.warning(f'No {engine.value} speech found for "{title_str}".')
            continue

        totals.titles += 1
        totals.lines += len(lines)
        totals.unplaced += sum(1 for line in lines if not line.is_placed)

        volume = comics_database.get_fanta_volume_int(title_str)
        rendered = render(title_str, volume, engine, lines)
        if out_dir:
            (out_dir / (_slug(title_str) + suffix)).write_text(rendered)
        else:
            print(rendered)

    return totals


def _print_summary(totals: Totals, engine: OcrTypes, out_dir: Path | None) -> None:
    """Print what was written, and anything that wants a human's attention."""
    if out_dir:
        print(f'Wrote {totals.titles} script(s) to "{out_dir}".')
    print(f"{totals.lines} line(s) across {totals.titles} title(s), {engine.value}.")

    if totals.unplaced:
        # Not an error -- the line is in the script either way. But a page whose
        # groups are mostly unplaced has a panel_num problem worth fixing.
        print(f"{totals.unplaced} line(s) carry no panel number and were placed at page end.")

    if totals.missing:
        pages = sum(len(v) for v in totals.missing.values())
        print(f"\nMissing prelim OCR -- {pages} page(s) absent, skipped:")
        for title_str, absent in sorted(totals.missing.items()):
            print(f"  {title_str}: {', '.join(absent)}")


@app.command(help="Export a story's speech as an ordered script (verbatim; local-only).")
def main(
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    engine: Annotated[
        OcrTypes, typer.Option("--engine", "-e", help="Which OCR pass to read.")
    ] = OcrTypes.EASYOCR,
    out_dir: Annotated[
        Path | None,
        typer.Option("--out-dir", "-o", help="Write one file per title here (default: stdout)."),
    ] = None,
    out_format: Annotated[
        str, typer.Option("--format", "-f", help=f"'{TEXT_FORMAT}' or '{JSON_FORMAT}'.")
    ] = TEXT_FORMAT,
) -> None:
    if out_format not in {TEXT_FORMAT, JSON_FORMAT}:
        msg = f"Unknown --format {out_format!r}; want '{TEXT_FORMAT}' or '{JSON_FORMAT}'."
        raise typer.BadParameter(msg)

    comics_database = ComicsDatabase()
    title_list = resolve_titles(comics_database, volumes_str, title_str)
    speech_groups = SpeechGroups(comics_database)
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    totals = _export(comics_database, speech_groups, title_list, engine, out_dir, out_format)
    _print_summary(totals, engine, out_dir)


if __name__ == "__main__":
    app()

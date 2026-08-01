# ruff: noqa: T201
"""Merge a Claude Code vision pass back into the prelim OCR group JSON.

Reads the ``result.json`` files written under a ``vision_prep`` output directory
and, for each group, adds ``speaker``, ``speaker_confidence``, ``cap_colour`` and
``emphasis_spans``.  Panel descriptions go to a sibling per-page file rather than
into the group JSON, because ``final_groups.py`` copies only the ``groups`` key
and would silently drop a new top-level section.

``ai_text`` is never modified.  Proposed text corrections are written to a
kivy-editor queue file for review instead, in the same format ``ocr_check``
emits.  ``--queue-speakers`` writes a second, separate queue of the groups
whose speaker attribution the model was unsure of, so the two reviews can be
worked through independently.

Everything is validated before anything is written: unknown group ids, emphasis
spans that fall outside the current ``ai_text``, and speakers outside the roster
all abort the run.  Saves go through ``save_json(backup_file=...)`` so the
previous prelim JSON is preserved.
"""

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_utils import get_backup_file
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from loguru import logger

from barks_ocr.utils.vision_schema import (
    CAP_COLOUR_SET,
    CONFIDENCES,
    EMPHASIS_KINDS,
    OTHER_PREFIX,
    VISION_SPEAKER_ISSUE,
    VISION_TEXT_ISSUE,
    is_valid_speaker,
    normalize_speaker,
)

app = typer.Typer()

PANEL_FILE_SUFFIX = "-panel-descriptions.json"

# result.json key -> key written on the group.  The reasoning fields are prefixed
# because the group already carries a Gemini-written `notes`, and a bare `note`
# sitting beside it would be a trap.  The first four are deliberately left
# unprefixed: they were written that way in the first run and renaming them now
# would orphan the existing data for no gain.
#
# Every key is written on every group, including as None.  That keeps re-runs
# idempotent and, for `vision_text_ok`, distinguishes "checked and correct" from
# "never checked".
APPLIED_KEYS = {
    "speaker": "speaker",
    "speaker_confidence": "speaker_confidence",
    "cap_colour": "cap_colour",
    "emphasis_spans": "emphasis_spans",
    "note": "vision_note",
    "text_ok": "vision_text_ok",
    "corrected_text": "vision_corrected_text",
}


def _check_speaker(speaker: Any, where: str, errors: list[str]) -> None:  # noqa: ANN401
    if not isinstance(speaker, str):
        errors.append(f"{where}: speaker must be a string, got {speaker!r}.")
    elif not is_valid_speaker(speaker):
        errors.append(
            f'{where}: speaker "{speaker}" is not in the roster'
            f' and is not a non-empty "{OTHER_PREFIX}" name.'
        )


def _check_spans(spans: Any, ai_text: str, where: str, errors: list[str]) -> None:  # noqa: ANN401
    if not isinstance(spans, list):
        errors.append(f"{where}: emphasis_spans must be a list.")
        return
    for span in spans:
        if not (isinstance(span, list) and len(span) == 3):  # noqa: PLR2004
            errors.append(f"{where}: bad emphasis span {span!r}; want [start, end, kind].")
            continue
        start, end, kind = span
        if not (isinstance(start, int) and isinstance(end, int)):
            errors.append(f"{where}: span offsets must be ints, got {span!r}.")
        elif not 0 <= start < end <= len(ai_text):
            errors.append(
                f"{where}: span [{start}, {end}] is outside ai_text of length {len(ai_text)}."
            )
        if kind not in EMPHASIS_KINDS:
            errors.append(f'{where}: unknown emphasis kind "{kind}".')


def _validate_group(gid: str, entry: dict, ai_text: str, where: str, errors: list[str]) -> None:
    _check_speaker(entry.get("speaker"), where, errors)
    if entry.get("speaker_confidence") not in CONFIDENCES:
        errors.append(f"{where}: speaker_confidence must be one of {sorted(CONFIDENCES)}.")
    cap = entry.get("cap_colour")
    if cap is not None and cap not in CAP_COLOUR_SET:
        errors.append(f'{where}: cap_colour "{cap}" is not one of {sorted(CAP_COLOUR_SET)}.')
    _check_spans(entry.get("emphasis_spans"), ai_text, where, errors)
    if not entry.get("text_ok") and not entry.get("corrected_text"):
        errors.append(f"{where}: text_ok is false but no corrected_text was supplied.")
    del gid


def _load_results(out_dir: Path) -> tuple[dict, list[tuple[str, dict]]]:
    """Return the queue plus (fanta_page, result) for every page marked done."""
    queue_file = out_dir / "queue.json"
    if not queue_file.is_file():
        msg = f'No queue file at "{queue_file}". Run barks-ocr-vision-prep first.'
        raise typer.BadParameter(msg)

    queue = json.loads(queue_file.read_text())
    results: list[tuple[str, dict]] = []
    for entry in queue["pages"]:
        page = entry["fanta_page"]
        result_file = out_dir / page / "result.json"
        if not result_file.is_file():
            logger.warning(f"Page {page}: no result.json yet, skipping.")
            continue
        results.append((page, json.loads(result_file.read_text())))
    return queue, results


def _normalize_results(results: list[tuple[str, dict]]) -> int:
    """Canonicalize every speaker in place. Returns how many values changed.

    Done before validation so the value that is checked is the value that gets
    stored — otherwise a model writing ``"other: Argus"`` for a character
    already recorded as ``"other:Argus"`` would quietly split it in two.
    """
    changed = 0
    for _page, result in results:
        for entry in result.get("groups", {}).values():
            speaker = entry.get("speaker")
            if not isinstance(speaker, str):
                continue  # `_check_speaker` reports the type error.
            canonical = normalize_speaker(speaker)
            if canonical != speaker:
                entry["speaker"] = canonical
                changed += 1
    return changed


def _queue_lines_for_page(
    page: str,
    result: dict,
    volume: int,
    engine: OcrTypes,
    speaker_confidences: frozenset[str],
) -> tuple[list[str], list[str]]:
    """Return this page's (text-correction, speaker-review) kivy-editor queue lines."""
    text_lines: list[str] = []
    speaker_lines: list[str] = []
    for gid, entry in result["groups"].items():
        prefix = f"{volume} {int(page)} {engine.value} {int(gid)}"
        if not entry.get("text_ok"):
            text_lines.append(f"{prefix} {VISION_TEXT_ISSUE}")
        if entry.get("speaker_confidence") in speaker_confidences:
            speaker_lines.append(f"{prefix} {VISION_SPEAKER_ISSUE}")
    return text_lines, speaker_lines


def _apply_page(page_group: Any, result: dict, *, dry_run: bool) -> int:  # noqa: ANN401
    """Write one page's annotations. Returns the number of groups changed."""
    json_groups = page_group.speech_page_json.get("groups", {})
    page = page_group.fanta_page
    changed = 0

    for gid, entry in result["groups"].items():
        group = json_groups[gid]
        for result_key, stored_key in APPLIED_KEYS.items():
            group[stored_key] = entry.get(result_key)
        changed += 1

    if dry_run:
        return changed

    ocr_file = page_group.ocr_prelim_groups_json_file
    backup_file = Path(
        str(get_backup_file(ocr_file)).replace(str(OCR_PRELIM_DIR), str(OCR_PRELIM_BACKUP_DIR))
    )
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    page_group.save_json(backup_file=backup_file)

    panel_file = ocr_file.parent / (page + PANEL_FILE_SUFFIX)
    panel_file.write_text(json.dumps(result["panels"], indent=2, ensure_ascii=False) + "\n")

    return changed


def _write_queue(queue_out: Path, header: str, lines: list[str]) -> int:
    """Write a de-duplicated kivy-editor queue file. Returns the entry count."""
    unique = sorted(set(lines))
    queue_out.parent.mkdir(parents=True, exist_ok=True)
    queue_out.write_text(header + "\n".join(unique) + "\n")
    return len(unique)


def _parse_confidences(spec: str) -> frozenset[str]:
    """Parse the comma-separated ``--speaker-confidences`` value."""
    wanted = frozenset(c.strip() for c in spec.split(",") if c.strip())
    unknown = wanted - CONFIDENCES
    if unknown:
        msg = f"Unknown speaker confidence(s) {sorted(unknown)}; want {sorted(CONFIDENCES)}."
        raise typer.BadParameter(msg)
    return wanted


def _resolve_and_validate(
    results: list[tuple[str, dict]], speech_groups: SpeechGroups, engine: OcrTypes
) -> tuple[dict[str, Any], list[str]]:
    """Resolve every page's group data and validate its result. Returns (pages, errors)."""
    page_groups: dict[str, Any] = {}
    errors: list[str] = []
    for page, result in results:
        title = STR_TITLE_TO_ENUM[result["title"]]
        found = [
            pg
            for pg in speech_groups.get_speech_page_groups(title, skip_missing=True)
            if pg.ocr_index == engine and pg.fanta_page == page
        ]
        if not found:
            errors.append(f"Page {page}: no {engine.value} groups found.")
            continue
        page_groups[page] = found[0]
        json_groups = found[0].speech_page_json.get("groups", {})

        for gid, entry in result["groups"].items():
            where = f"page {page} group {gid}"
            if gid not in json_groups:
                errors.append(f"{where}: group id does not exist in the prelim JSON.")
                continue
            _validate_group(gid, entry, json_groups[gid].get("ai_text") or "", where, errors)
    return page_groups, errors


@app.command(help="Merge a Claude Code vision pass back into the prelim OCR group JSON.")
def main(
    out_dir: Annotated[
        Path, typer.Option("--out-dir", "-o", help="The vision_prep output directory.")
    ],
    queue_out: Annotated[
        Path | None,
        typer.Option("--queue-out", help="Where to write the text-correction review queue."),
    ] = None,
    queue_speakers: Annotated[
        Path | None,
        typer.Option("--queue-speakers", help="Where to write the speaker review queue."),
    ] = None,
    speaker_confidences: Annotated[
        str,
        typer.Option(
            "--speaker-confidences",
            help="Comma-separated speaker_confidence values to queue for review.",
        ),
    ] = "low",
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Validate and report, but write nothing.")
    ] = False,
) -> None:
    wanted_confidences = _parse_confidences(speaker_confidences)

    queue, results = _load_results(out_dir)
    volume = int(queue["volume"])
    engine = OcrTypes(queue["engine"])

    speech_groups = SpeechGroups(ComicsDatabase())

    normalized = _normalize_results(results)
    if normalized:
        print(f"Canonicalized {normalized} speaker value(s) before validating.")

    # Resolve every page and validate everything before writing a single file.
    page_groups, errors = _resolve_and_validate(results, speech_groups, engine)

    if errors:
        print(f"Validation failed with {len(errors)} error(s); nothing was written:")
        for err in errors:
            print(f"  - {err}")
        raise typer.Exit(code=1)

    text_lines: list[str] = []
    speaker_lines: list[str] = []
    total = 0
    for page, result in results:
        total += _apply_page(page_groups[page], result, dry_run=dry_run)
        page_text, page_speaker = _queue_lines_for_page(
            page, result, volume, engine, wanted_confidences
        )
        text_lines += page_text
        speaker_lines += page_speaker

    queues = (
        (queue_out, "text corrections", text_lines),
        (queue_speakers, "speaker review", speaker_lines),
    )
    for path, what, lines in queues:
        if path is not None and not dry_run:
            header = f"# vision-check {what} (volume {volume}, engine {engine.value})\n"
            print(f'Review queue ({what}): "{path}" ({_write_queue(path, header, lines)} entries).')

    verb = "Would annotate" if dry_run else "Annotated"
    print(f"{verb} {total} group(s) across {len(results)} page(s).")
    if dry_run:
        print(f"{len(set(text_lines))} group(s) have proposed text corrections.")
        print(
            f"{len(set(speaker_lines))} group(s) have a speaker call at"
            f" confidence {sorted(wanted_confidences)}."
        )


if __name__ == "__main__":
    app()

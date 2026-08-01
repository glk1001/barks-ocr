# ruff: noqa: T201
"""Merge a Claude Code vision pass back into the prelim OCR group JSON.

Reads the ``result.json`` files written under a ``vision_prep`` output directory
and, for each group, adds ``speaker``, ``speaker_confidence``, ``cap_colour`` and
``emphasis_spans``.

Each page's structured capture -- who is depicted, the setting, the time of day,
the non-speech lettering, a couple of plain sentences, and any panel worth
addressing on its own -- goes to a sibling per-page file rather than into the
group JSON, because ``final_groups.py`` copies only the ``groups`` key and would
silently drop a new top-level section.  Every field it holds is stamped with its
publication class, so an exporter never has to look that up elsewhere.

``ai_text`` is never modified.  Proposed text corrections are written to a
kivy-editor queue file for review instead, in the same format ``ocr_check``
emits.  ``--queue-speakers`` writes a second, separate queue of the groups
whose speaker attribution the model was unsure of, so the two reviews can be
worked through independently.

Everything is validated before anything is written: unknown group ids, emphasis
spans falling outside the current ``ai_text``, a character who is neither on the
roster nor tagged for this story, a setting or time of day outside the
vocabulary, a ``panels_of_note`` entry naming a panel the page does not have,
and any capture field nobody has given a publication class -- each aborts the
run.  Saves go through ``save_json(backup_file=...)`` so the previous prelim
JSON is preserved.
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

from barks_ocr.utils.story_cast import story_characters
from barks_ocr.utils.vision_schema import (
    BEATS_KEY,
    CAP_COLOUR_SET,
    CHARACTERS_KEY,
    CONFIDENCES,
    EMPHASIS_KINDS,
    FIELD_CLASS,
    OTHER_PREFIX,
    PANELS_OF_NOTE_KEY,
    SETTING_KEY,
    TIME_OF_DAY_KEY,
    TIMES_OF_DAY,
    VISIBLE_TEXT_KEY,
    VISION_SPEAKER_ISSUE,
    VISION_TEXT_ISSUE,
    is_valid_setting,
    is_valid_speaker,
    nephew_needs_collective,
    normalize_setting,
    normalize_speaker,
)

app = typer.Typer()

CAPTURE_FILE_SUFFIX = "-page-capture.json"

# The capture keys a result may carry. Anything else is rejected: an unclassified
# field has no publication class, so it cannot be exported safely later, and
# silently storing it would defer that problem to whoever writes the exporter.
CAPTURE_KEYS = frozenset(
    {
        CHARACTERS_KEY,
        SETTING_KEY,
        TIME_OF_DAY_KEY,
        VISIBLE_TEXT_KEY,
        BEATS_KEY,
        PANELS_OF_NOTE_KEY,
    }
)

# How many sentences a page's `beats` may run to. The cap is the schema's only
# guard against the capture layer drifting into a page-by-page retelling, which
# is both the wrong shape for retrieval and the thing that starts to look like
# an abridgment rather than a description.
MAX_BEATS = 3

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


def _check_speaker(
    speaker: Any,  # noqa: ANN401
    where: str,
    errors: list[str],
    cast: frozenset[str] = frozenset(),
) -> None:
    if not isinstance(speaker, str):
        errors.append(f"{where}: speaker must be a string, got {speaker!r}.")
    elif not is_valid_speaker(speaker, cast):
        errors.append(
            f'{where}: speaker "{speaker}" is not in the roster, not tagged for this'
            f' story, and not a non-empty "{OTHER_PREFIX}" name.'
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


def _validate_group(  # noqa: PLR0913
    gid: str,
    entry: dict,
    ai_text: str,
    where: str,
    errors: list[str],
    cast: frozenset[str] = frozenset(),
) -> None:
    speaker = entry.get("speaker")
    confidence = entry.get("speaker_confidence")
    _check_speaker(speaker, where, errors, cast)
    if confidence not in CONFIDENCES:
        errors.append(f"{where}: speaker_confidence must be one of {sorted(CONFIDENCES)}.")
    elif (
        isinstance(speaker, str)
        and isinstance(confidence, str)
        and nephew_needs_collective(speaker, confidence)
    ):
        errors.append(
            f'{where}: "{speaker}" at {confidence} confidence -- if the cap cannot be read,'
            ' the answer is "nephews", and that is not a low-confidence call.'
        )
    cap = entry.get("cap_colour")
    if cap is not None and cap not in CAP_COLOUR_SET:
        errors.append(f'{where}: cap_colour "{cap}" is not one of {sorted(CAP_COLOUR_SET)}.')
    _check_spans(entry.get("emphasis_spans"), ai_text, where, errors)
    if not entry.get("text_ok") and not entry.get("corrected_text"):
        errors.append(f"{where}: text_ok is false but no corrected_text was supplied.")
    del gid


def _check_str_list(value: Any, key: str, where: str, errors: list[str]) -> list[str]:  # noqa: ANN401
    """Validate a list-of-strings capture field. Returns it, or [] when unusable."""
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        errors.append(f"{where}: {key} must be a list of strings, got {value!r}.")
        return []
    return value


def _check_panels_of_note(
    value: Any,  # noqa: ANN401
    panel_nums: list[int],
    where: str,
    errors: list[str],
) -> None:
    """Validate ``panels_of_note`` against the panels the page actually has."""
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{where}: {PANELS_OF_NOTE_KEY} must be a list.")
        return
    for item in value:
        if not (isinstance(item, list) and len(item) == 2):  # noqa: PLR2004
            errors.append(
                f"{where}: bad {PANELS_OF_NOTE_KEY} entry {item!r}; want [panel, phrase]."
            )
            continue
        panel, phrase = item
        if panel not in panel_nums:
            errors.append(
                f"{where}: {PANELS_OF_NOTE_KEY} names panel {panel!r},"
                f" but this page has panels {panel_nums}."
            )
        if not isinstance(phrase, str) or not phrase.strip():
            errors.append(f"{where}: {PANELS_OF_NOTE_KEY} entry for panel {panel} has no phrase.")


def _validate_capture(
    capture: dict, panel_nums: list[int], cast: frozenset[str], where: str, errors: list[str]
) -> None:
    """Validate one page's capture record against the schema and this story's cast."""
    unknown = set(capture) - CAPTURE_KEYS
    if unknown:
        errors.append(
            f"{where}: unknown capture field(s) {sorted(unknown)}."
            " Add them to FIELD_CLASS and CAPTURE_KEYS first, or drop them."
        )

    errors.extend(
        f'{where}: character "{name}" is not on the roster, not tagged for this'
        f' story, and not a non-empty "{OTHER_PREFIX}" name.'
        for name in _check_str_list(capture.get(CHARACTERS_KEY), CHARACTERS_KEY, where, errors)
        if not is_valid_speaker(name, cast)
    )

    setting = capture.get(SETTING_KEY)
    if setting is not None and not is_valid_setting(setting):
        errors.append(f'{where}: setting "{setting}" is not in the vocabulary.')

    time_of_day = capture.get(TIME_OF_DAY_KEY)
    if time_of_day is not None and time_of_day not in TIMES_OF_DAY:
        errors.append(
            f'{where}: {TIME_OF_DAY_KEY} "{time_of_day}" is not one of {sorted(TIMES_OF_DAY)}.'
        )

    _check_str_list(capture.get(VISIBLE_TEXT_KEY), VISIBLE_TEXT_KEY, where, errors)

    beats = _check_str_list(capture.get(BEATS_KEY), BEATS_KEY, where, errors)
    if len(beats) > MAX_BEATS:
        errors.append(f"{where}: {len(beats)} beats; at most {MAX_BEATS} are allowed.")

    _check_panels_of_note(capture.get(PANELS_OF_NOTE_KEY), panel_nums, where, errors)


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

        capture = result.get("capture") or {}
        names = capture.get(CHARACTERS_KEY)
        if isinstance(names, list):
            for i, name in enumerate(names):
                if isinstance(name, str) and (canonical := normalize_speaker(name)) != name:
                    names[i] = canonical
                    changed += 1
        setting = capture.get(SETTING_KEY)
        if isinstance(setting, str) and (canonical := normalize_setting(setting)) != setting:
            capture[SETTING_KEY] = canonical
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

    capture = result.get("capture")
    if capture is not None:
        # Beside the prelim JSON rather than inside it: `final_groups.py` copies
        # only the `groups` key and would silently drop a new top-level section.
        capture_file = ocr_file.parent / (page + CAPTURE_FILE_SUFFIX)
        capture_file.write_text(json.dumps(_stamped(capture), indent=2, ensure_ascii=False) + "\n")

    return changed


def _stamped(capture: dict) -> dict:
    """Return the capture record with its per-field publication classes recorded.

    Written into the file rather than left to the reader.  The class is a
    property of the data, and an exporter that has to look the answer up
    elsewhere is one refactor away from not looking it up at all.
    """
    return {
        **capture,
        "_publication_class": {key: FIELD_CLASS[key].value for key in sorted(capture)},
    }


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
    results: list[tuple[str, dict]],
    speech_groups: SpeechGroups,
    engine: OcrTypes,
    panel_nums_by_page: dict[str, list[int]],
) -> tuple[dict[str, Any], list[str]]:
    """Resolve every page's group data and validate its result. Returns (pages, errors)."""
    page_groups: dict[str, Any] = {}
    errors: list[str] = []
    # Cached per title: the tag lookup walks every character group, and a run is
    # usually one story, so recomputing it per page would be pure waste.
    casts: dict[str, frozenset[str]] = {}

    for page, result in results:
        title_str = result["title"]
        title = STR_TITLE_TO_ENUM[title_str]
        if title_str not in casts:
            casts[title_str] = frozenset(story_characters(title))

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
            _validate_group(
                gid, entry, json_groups[gid].get("ai_text") or "", where, errors, casts[title_str]
            )

        capture = result.get("capture")
        if capture is not None:
            _validate_capture(
                capture,
                panel_nums_by_page.get(page, []),
                casts[title_str],
                f"page {page} capture",
                errors,
            )
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
    panel_nums_by_page = {
        entry["fanta_page"]: entry.get("panel_nums") or [] for entry in queue["pages"]
    }
    page_groups, errors = _resolve_and_validate(results, speech_groups, engine, panel_nums_by_page)

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

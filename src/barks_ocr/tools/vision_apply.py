# ruff: noqa: T201
"""Merge a Claude Code vision pass back into the prelim OCR group JSON.

Reads the ``result.json`` files written under a ``vision_prep`` output directory
and, for each group, adds ``speaker``, ``speaker_confidence``, ``cap_colour`` and
the group's emphasis, which is written inline into ``ai_text`` as ``[b]``/``[i]``
markup rather than held as offsets beside it.

Each page's structured capture -- who is depicted, the setting, the time of day,
the non-speech lettering, a couple of plain sentences, and any panel worth
addressing on its own -- goes to a sibling per-page file rather than into the
group JSON, because ``final_groups.py`` copies only the ``groups`` key and would
silently drop a new top-level section.  Every field it holds is stamped with its
publication class, so an exporter never has to look that up elsewhere.

The **words** of ``ai_text`` are never modified: emphasis markup is added to it,
and validation refuses the run unless the marked-up text strips back to exactly
what is already stored.  Proposed text corrections are written to a
kivy-editor queue file for review instead, in the same format ``ocr_check``
emits.  ``--queue-speakers`` writes a second, separate queue of the groups
whose speaker attribution the model was unsure of, so the two reviews can be
worked through independently.

Everything is validated before anything is written: unknown group ids, emphasis
markup that is malformed or does not strip back to the stored text, a character
who is neither on the
roster nor tagged for this story, a setting or time of day outside the
vocabulary, a ``panels_of_note`` entry naming a panel the page does not have,
an over-long ``objects`` inventory, and any capture field nobody has given a
publication class -- each aborts the run.  Saves go through
``save_json(backup_file=...)`` so the previous prelim JSON is preserved.

So does a result with **no capture at all**.  The schema is one record per page,
and a missing one used to apply cleanly and print a group count that read as
success, which is how a whole title once merged 136 groups and zero capture
records without saying so anywhere.  The commonest cause is filling in the
``page-capture.json`` stub ``vision_prep`` leaves in the page directory and never
copying it into ``result.json``; the error says so when it can see that is what
happened.  ``--no-capture`` is how a deliberately groups-only run says it meant
it -- the pilot, for instance, predates page capture entirely.
"""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_utils import get_backup_file
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from barks_fantagraphics.speech_markup import strip_markup, validate_markup
from loguru import logger

from barks_ocr.tools.vision_mirror import MirrorReport, mirror_title
from barks_ocr.utils.story_cast import story_characters
from barks_ocr.utils.vision_schema import (
    BEATS_KEY,
    CAP_COLOUR_SET,
    CAPTURE_MODEL_KEY,
    CAPTURE_PROMPT_VERSION,
    CAPTURE_PROMPT_VERSION_KEY,
    CAPTURE_RULES,
    CAPTURE_RULES_KEY,
    CAPTURED_KEY,
    CHARACTERS_KEY,
    CONFIDENCES,
    EMPHASIS_MARKUP_KEY,
    FIELD_CLASS,
    IDENTIFIED_BY_KEY,
    IDENTIFIED_BY_SET,
    MAX_OBJECTS,
    NEPHEW_NAMES,
    OBJECTS_KEY,
    OTHER_PREFIX,
    PANELS_OF_NOTE_KEY,
    SETTING_KEY,
    TIME_OF_DAY_KEY,
    TIMES_OF_DAY,
    VISIBLE_TEXT_KEY,
    VISION_SPEAKER_ISSUE,
    VISION_TEXT_ISSUE,
    collapse_whitespace,
    invalid_identified_by,
    is_valid_setting,
    is_valid_speaker,
    nephew_needs_collective,
    normalize_setting,
    normalize_speaker,
)

app = typer.Typer()

CAPTURE_FILE_SUFFIX = "-page-capture.json"
# What `vision_prep` calls the per-page stub inside the output directory. Named
# here so the "you left it in the stub" diagnosis below cannot drift from it.
STUB_FILE_NAME = "page-capture.json"

# The capture keys a result may carry. Anything else is rejected: an unclassified
# field has no publication class, so it cannot be exported safely later, and
# silently storing it would defer that problem to whoever writes the exporter.
CAPTURE_KEYS = frozenset(
    {
        CHARACTERS_KEY,
        SETTING_KEY,
        TIME_OF_DAY_KEY,
        VISIBLE_TEXT_KEY,
        OBJECTS_KEY,
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
    "identified_by": IDENTIFIED_BY_KEY,
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


def _check_emphasis(markup: Any, ai_text: str, where: str, errors: list[str]) -> None:  # noqa: ANN401
    """Validate a group's marked-up text against the ``ai_text`` on disk.

    Two things are checked, and the second is the important one.  The markup
    must be well formed, and it must **strip back to exactly the stored text**.

    That equality is what makes writing emphasis into ``ai_text`` safe.  The
    vision pass reads the crops at prep time and the result is applied later, so
    the text can move underneath it -- an editor session, a bulk substitution, an
    earlier queued correction.  Under the retired offsets scheme that produced a
    span still in range and pointing at the wrong words, with nothing to notice.
    Here it is a refused run with the diff printed, before anything is written.
    """
    if markup is None:
        return
    if not isinstance(markup, str):
        errors.append(f"{where}: {EMPHASIS_MARKUP_KEY} must be a string, got {markup!r}.")
        return

    errors.extend(f"{where}: {problem}." for problem in validate_markup(markup))

    # Both sides stripped: on a re-run the stored ai_text already carries the
    # previous pass's tags, and it is the words that have to match, not the
    # emphasis.
    stripped = strip_markup(markup)
    stored_plain = strip_markup(ai_text)
    if stripped != stored_plain:
        errors.append(
            f"{where}: {EMPHASIS_MARKUP_KEY} does not match the stored ai_text once the"
            f" tags are removed, so the text has changed since the crops were read."
            f"\n  stored:  {stored_plain!r}\n  stripped:{stripped!r}"
        )


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
    _check_identified_by(entry.get("identified_by"), speaker, cap, where, errors)
    _check_emphasis(entry.get(EMPHASIS_MARKUP_KEY), ai_text, where, errors)
    if not entry.get("text_ok") and not entry.get("corrected_text"):
        errors.append(f"{where}: text_ok is false but no corrected_text was supplied.")
    del gid


def _check_identified_by(
    value: Any,  # noqa: ANN401
    speaker: Any,  # noqa: ANN401
    cap: Any,  # noqa: ANN401
    where: str,
    errors: list[str],
) -> None:
    """Validate the evidence list behind a speaker call.

    Required wherever somebody speaks, because a call with no recorded evidence
    is exactly the irreversible state this field was added to end. ``none`` is
    the one speaker that needs none -- nobody said it.

    The one cross-check worth making here: a ``cap_colour`` was read but the call
    does not claim to rest on it, or the reverse. Both are cheap to state and
    either is a sign the two fields were filled in independently rather than
    describing one judgement.
    """
    if speaker == "none":
        return
    if value is None:
        errors.append(
            f"{where}: identified_by is required when somebody speaks"
            f" -- one or more of {sorted(IDENTIFIED_BY_SET)}."
        )
        return
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        errors.append(f"{where}: identified_by must be a list of strings, got {value!r}.")
        return
    if not value:
        errors.append(f"{where}: identified_by is empty; omit the speaker or name the evidence.")
        return
    unknown = invalid_identified_by(value)
    if unknown:
        errors.append(
            f"{where}: identified_by {unknown} not in {sorted(IDENTIFIED_BY_SET)}."
            " The vocabulary is closed on purpose -- add a kind rather than free text."
        )
        return
    # Only one direction is an error. Claiming to have identified somebody by a
    # colour that was never recorded is incoherent.
    if cap is None and "cap-colour" in value:
        errors.append(
            f'{where}: identified_by claims "cap-colour" but cap_colour is null.'
            " Record the colour that was read."
        )
    # The reverse -- a colour recorded without being cited as evidence -- used to
    # be an error here and is now deliberately allowed, because it is the single
    # most informative state the two fields can be in: the tail identified the
    # nephew, a colour was read, and they DISAGREE. Rejecting it forced the
    # reader either to drop the observation or to claim the colour as evidence
    # for a call it did not support, and the second is how 30 later-named
    # collective calls came to cite a cap reading that can no longer be told from
    # one written in from the convention afterwards.


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

    objects = _check_str_list(capture.get(OBJECTS_KEY), OBJECTS_KEY, where, errors)
    if len(objects) > MAX_OBJECTS:
        # An inventory matches every query and so discriminates nothing. This is
        # a different concern from MAX_BEATS, which guards against retelling.
        errors.append(f"{where}: {len(objects)} objects; at most {MAX_OBJECTS} are allowed.")
    errors.extend(
        f"{where}: {OBJECTS_KEY} entry {name!r} is blank." for name in objects if not name.strip()
    )

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
        changed += _normalize_capture(result.get("capture") or {})
    return changed


def _normalize_list_in_place(values: Any, canonicalize: Callable[[str], str]) -> int:  # noqa: ANN401
    """Canonicalize a list of strings in place. Returns how many changed."""
    if not isinstance(values, list):
        return 0
    changed = 0
    for i, value in enumerate(values):
        if isinstance(value, str) and (canonical := canonicalize(value)) != value:
            values[i] = canonical
            changed += 1
    return changed


def _normalize_capture(capture: dict) -> int:
    """Canonicalize one page's capture record in place. Returns how many changed."""
    changed = _normalize_list_in_place(capture.get(CHARACTERS_KEY), normalize_speaker)

    setting = capture.get(SETTING_KEY)
    if isinstance(setting, str) and (canonical := normalize_setting(setting)) != setting:
        capture[SETTING_KEY] = canonical
        changed += 1

    # Objects are free text with no vocabulary behind them, so whitespace is the
    # only drift fixable mechanically. "fly  swatter" and "fly swatter " are one
    # object; anything subtler is for the census and a human.
    changed += _normalize_list_in_place(capture.get(OBJECTS_KEY), collapse_whitespace)
    return changed


def _correction_applied(entry: dict, group: dict) -> bool:
    """Whether the group's stored text already matches the correction proposed for it.

    What stops the text-correction queue from re-offering work that is done.
    ``text_ok`` records what the pass found when it read the crops and never
    changes afterwards, so queueing on it alone hands back every correction ever
    proposed, on every run, forever.  The speaker queue avoids this with
    ``speaker_reviewed``; the text side needs no such flag, because the group
    already carries the answer -- if ``ai_text`` says what ``vision_corrected_text``
    says, somebody has applied it.

    Both sides are stripped.  A human applying a correction in the editor keeps
    the emphasis, so the stored text can carry tags that the proposed correction
    -- written before the markup existed -- never had.  The pilot's ``077 g1`` is
    exactly that: the stored text carries a bold on SABOTEURS that the proposed
    correction, written before the markup existed, does not -- the same words
    either way.

    Args:
        entry: The group's entry in ``result.json``.
        group: The stored prelim OCR group.

    Returns:
        True when the correction has already landed, so nothing is to be queued.

    """
    corrected = entry.get("corrected_text")
    if not corrected:
        return False
    return strip_markup(group.get("ai_text") or "") == strip_markup(corrected)


def _queue_lines_for_page(  # noqa: PLR0913
    page: str,
    result: dict,
    json_groups: dict,
    volume: int,
    engine: OcrTypes,
    speaker_confidences: frozenset[str],
) -> tuple[list[str], list[str]]:
    """Return this page's (text-correction, speaker-review) kivy-editor queue lines."""
    text_lines: list[str] = []
    speaker_lines: list[str] = []
    unreferenced = _unreferenced_nephews(result, json_groups)
    for gid, entry in result["groups"].items():
        prefix = f"{volume} {int(page)} {engine.value} {int(gid)}"
        if not entry.get("text_ok") and not _correction_applied(entry, json_groups.get(gid, {})):
            text_lines.append(f"{prefix} {VISION_TEXT_ISSUE}")
        if entry.get("speaker_confidence") in speaker_confidences or gid in unreferenced:
            speaker_lines.append(f"{prefix} {VISION_SPEAKER_ISSUE}")
    return text_lines, speaker_lines


def _unreferenced_nephews(result: dict, json_groups: dict) -> frozenset[str]:
    """Return group ids naming one nephew by cap colour with no sibling to check it against.

    Measured on the 50-call audit of 2026-08-03: an individual nephew named in a
    panel where **no other nephew speaks** was wrong 4 times in 17 (24%), against
    1 in 33 (3%) where the panel has two or three of them talking.  The pass is
    not worse at those panels -- it has less to go on.  Three caps side by side
    are read against each other; a single cap is read against nothing, and on the
    restored colour green in shadow prints close enough to blue that all four
    errors ran between those two.

    So these are queued whatever confidence the pass gave them, which is nearly
    always ``high``.  The confidence field is deliberately **not** rewritten: it
    records what the pass believed, and this is the reviewer knowing something
    about the configuration that the pass could not.

    Args:
        result: The page's parsed ``result.json``.
        json_groups: The page's stored groups, for ``panel_num``.

    Returns:
        The group ids to queue for a speaker review.

    """
    by_panel: dict[Any, list[str]] = {}
    for gid, entry in result["groups"].items():
        if entry.get("speaker") in NEPHEW_NAMES:
            panel = json_groups.get(gid, {}).get("panel_num")
            by_panel.setdefault(panel, []).append(gid)
    return frozenset(
        group_ids[0]
        for group_ids in by_panel.values()
        if len(group_ids) == 1 and result["groups"][group_ids[0]].get("cap_colour")
    )


def _apply_page(
    page_group: Any,  # noqa: ANN401
    result: dict,
    capture_model: str | None,
    *,
    dry_run: bool,
) -> int:
    """Write one page's annotations. Returns the number of groups changed."""
    json_groups = page_group.speech_page_json.get("groups", {})
    page = page_group.fanta_page
    changed = 0

    for gid, entry in result["groups"].items():
        group = json_groups[gid]
        for result_key, stored_key in APPLIED_KEYS.items():
            group[stored_key] = entry.get(result_key)

        # Emphasis goes into `ai_text` itself. Validation has already checked
        # that this strips back to the stored words, so the only thing changing
        # is which of them are tagged.
        #
        # An absent field leaves `ai_text` alone rather than clearing existing
        # tags. Absent means "this run said nothing about emphasis here", which
        # is not the same as "there is none", and a re-run must not silently
        # delete emphasis a human added in the editor.
        markup = entry.get(EMPHASIS_MARKUP_KEY)
        if markup is not None:
            group["ai_text"] = markup
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
        capture_file.write_text(
            json.dumps(_stamped(capture, capture_model), indent=2, ensure_ascii=False) + "\n"
        )

    return changed


def _stamped(capture: dict, capture_model: str | None) -> dict:
    """Return the capture record with its provenance and publication classes.

    Both are written into the file rather than left to the reader.  The
    publication class is a property of the data, and an exporter that has to look
    the answer up elsewhere is one refactor away from not looking it up at all.

    The provenance keys were declared, documented and rendered into
    ``vision_prep``'s stub from the start and never written, because they were
    absent from ``CAPTURE_KEYS`` and so rejected on the way in.  Every record
    written before 2026-08-03 carries nulls, which is now what identifies that
    cohort.  They are filled in **here** rather than accepted from the result
    file because the version and the rule list are properties of the code doing
    the applying, not claims the reading session should be trusted to make about
    itself.

    Args:
        capture: The page's capture record, as the pass wrote it.
        capture_model: The model that read the crops, if it was declared.

    Returns:
        The record to write.

    """
    stamped = {
        **capture,
        CAPTURE_MODEL_KEY: capture_model,
        CAPTURE_PROMPT_VERSION_KEY: CAPTURE_PROMPT_VERSION,
        CAPTURED_KEY: datetime.now().astimezone().isoformat(timespec="seconds"),
        CAPTURE_RULES_KEY: list(CAPTURE_RULES),
    }
    return {
        **stamped,
        "_publication_class": {key: FIELD_CLASS[key].value for key in sorted(stamped)},
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


def _stub_is_filled(out_dir: Path, page: str) -> bool:
    """Return whether the prep stub for a page has been written into but left there.

    ``vision_prep`` drops a ``page-capture.json`` stub in each page directory as
    somewhere to compose the record, but ``vision_apply`` reads the capture from
    ``result.json``.  Filling the stub and never copying it across looks exactly
    like doing no capture at all, so the two cases are told apart here and the
    error says which one happened.
    """
    stub_file = out_dir / page / STUB_FILE_NAME
    if not stub_file.is_file():
        return False
    try:
        stub = json.loads(stub_file.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return any(stub.get(key) for key in CAPTURE_KEYS)


def _missing_capture_errors(results: list[tuple[str, dict]], out_dir: Path) -> list[str]:
    """Report every page whose result carries no capture record.

    Separate from ``_resolve_and_validate`` because it is a different kind of
    check: that one asks whether the capture is *valid*, this one whether it is
    *there*.  A missing one used to apply cleanly and print a group count that
    read as success, which is how a whole title once merged its groups and no
    capture at all without saying so.
    """
    errors = []
    for page, result in results:
        if result.get("capture") is not None:
            continue
        where = f'page {page}: no "capture" key in result.json'
        if _stub_is_filled(out_dir, page):
            errors.append(
                f"{where} — but {page}/{STUB_FILE_NAME} has been filled in."
                " The stub is scratch space; copy it into result.json under a"
                ' "capture" key.'
            )
        else:
            errors.append(f"{where}. Pass --no-capture if this run is groups-only.")
    return errors


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


def _mirror_to_other_engine(
    speech_groups: SpeechGroups,
    results: list[tuple[str, dict]],
    engine: OcrTypes,
    *,
    dry_run: bool,
) -> None:
    """Copy this run's annotations onto the engine the pass did not read.

    Runs once per title touched, and reports through the mirror's own tally so
    the line-break and word differences it refuses to cross are visible here
    rather than only when the standalone command is run.
    """
    other = next(t for t in OcrTypes if t != engine)
    report = MirrorReport()
    for title_str in dict.fromkeys(result["title"] for _page, result in results):
        mirror_title(
            speech_groups,
            STR_TITLE_TO_ENUM[title_str],
            engine,
            other,
            report,
            dry_run=dry_run,
        )
    verb = "Would mirror" if dry_run else "Mirrored"
    print(
        f"{verb} {report.fields_copied} group(s) and {report.markup_copied} emphasis run(s)"
        f" onto {other.value}."
    )
    report.log(dry_run=dry_run)


@app.command(help="Merge a Claude Code vision pass back into the prelim OCR group JSON.")
def main(  # noqa: PLR0913
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
    no_capture: Annotated[
        bool,
        typer.Option(
            "--no-capture",
            help="Allow results with no page capture, for a groups-only or pre-capture run.",
        ),
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Validate and report, but write nothing.")
    ] = False,
    capture_model: Annotated[
        str | None,
        typer.Option(
            "--capture-model",
            help="The model that read the crops, recorded on every capture record.",
        ),
    ] = None,
    no_mirror: Annotated[
        bool,
        typer.Option(
            "--no-mirror",
            help="Do not copy the annotations onto the other engine's groups.",
        ),
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
    if not no_capture:
        errors += _missing_capture_errors(results, out_dir)

    if errors:
        print(f"Validation failed with {len(errors)} error(s); nothing was written:")
        for err in errors:
            print(f"  - {err}")
        raise typer.Exit(code=1)

    text_lines: list[str] = []
    speaker_lines: list[str] = []
    total = 0
    for page, result in results:
        total += _apply_page(page_groups[page], result, capture_model, dry_run=dry_run)
        page_text, page_speaker = _queue_lines_for_page(
            page,
            result,
            page_groups[page].speech_page_json.get("groups", {}),
            volume,
            engine,
            wanted_confidences,
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

    # Mirror before the closing line, so the tally reports what actually
    # happened on both engines. The corpus carries both all the way through so
    # their differences can be reconciled down to one set of finals, and a pass
    # that annotated only one of them would hand back a fresh pile of
    # differences to reconcile -- 219 of them on Plenty of Pets alone.
    if not no_mirror:
        _mirror_to_other_engine(speech_groups, results, engine, dry_run=dry_run)

    verb = "Would annotate" if dry_run else "Annotated"
    captured = sum(1 for _page, result in results if result.get("capture") is not None)
    # Count the capture records too. The group total alone reads as success even
    # when every page wrote nothing but groups, which is how a whole title once
    # applied with no capture at all and said so nowhere.
    print(f"{verb} {total} group(s) and {captured} page capture(s) across {len(results)} page(s).")
    if dry_run:
        print(f"{len(set(text_lines))} group(s) have proposed text corrections.")
        # Not all of these are queued for their confidence any more: the
        # lone-panel rule adds groups the pass was sure about.
        print(
            f"{len(set(speaker_lines))} group(s) queued for speaker review"
            f" (confidence {sorted(wanted_confidences)}, plus any nephew named"
            f" alone in a panel)."
        )


if __name__ == "__main__":
    app()

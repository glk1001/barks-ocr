"""The vocabulary the vision pass writes, and that the editor offers back.

``vision_apply`` validates a Claude Code vision result against these names
before writing anything; ``kivy_editor``'s speaker popup offers the same names
for review. They live here so the two cannot drift — a roster entry the editor
offers but the validator rejects would be a silent trap.

See ``docs/vision-pass.md`` for what each field means.
"""

import re

# Ordered, because the editor lays the roster out in this order. Free-form
# speakers are allowed only behind ``OTHER_PREFIX``, so a typo in a main-cast
# name is caught rather than silently becoming a new character.
#
# "nephews" is not a fourth nephew: it is the honest answer when the line is one
# of the three but the art will not say which. The Huey-red / Dewey-blue /
# Louie-green convention was not firmly fixed in the early years, and 085 p3 of
# the pilot gives two nephews the same green. It also covers a line the three
# speak together. Prefer it to guessing a name; it is not the same as "unknown",
# which means the speaker could not be placed at all.
SPEAKER_OPTIONS: tuple[str, ...] = (
    "Donald",
    "Huey",
    "Dewey",
    "Louie",
    "nephews",
    "Daisy",
    "Gladstone",
    "Scrooge",
    "Gyro",
    "narrator",
    "none",
    "unknown",
)
ROSTER: frozenset[str] = frozenset(SPEAKER_OPTIONS)
OTHER_PREFIX = "other:"

# Glosses for the entries that are easy to use wrongly, rendered into the
# roster file the vision pass is handed. The named cast needs no explanation.
SPEAKER_NOTES: dict[str, str] = {
    "nephews": "one of the three but the art will not say which, or all three at once",
    "narrator": "a caption box, not a character",
    "none": "nobody speaks it: a sound effect, a sign, background lettering",
    "unknown": "the speaker could not be placed at all",
}

CONFIDENCE_OPTIONS: tuple[str, ...] = ("high", "medium", "low")
CONFIDENCES: frozenset[str] = frozenset(CONFIDENCE_OPTIONS)

CAP_COLOUR_OPTIONS: tuple[str, ...] = ("red", "blue", "green")
CAP_COLOUR_SET: frozenset[str] = frozenset(CAP_COLOUR_OPTIONS)

EMPHASIS_KINDS: frozenset[str] = frozenset({"bold", "italic"})

# Keys written onto a prelim group by `vision_apply` and read back by the editor.
SPEAKER_KEY = "speaker"
SPEAKER_CONFIDENCE_KEY = "speaker_confidence"
CAP_COLOUR_KEY = "cap_colour"
VISION_NOTE_KEY = "vision_note"

# Written by the editor only. `speaker_confidence` alone cannot tell a human's
# confirmation from the model's own confident guess, and the difference is the
# whole point of the review pass.
SPEAKER_REVIEWED_KEY = "speaker_reviewed"

# The confidence a reviewed group carries: a human looked at the art.
REVIEWED_CONFIDENCE = "high"

# Queue issue types, shared between the queues `vision_apply` writes and the
# editor's info bar.
VISION_TEXT_ISSUE = "vision-text"
VISION_SPEAKER_ISSUE = "vision-speaker"


_WHITESPACE_RE = re.compile(r"\s+")
_ROSTER_BY_CASEFOLD: dict[str, str] = {name.casefold(): name for name in SPEAKER_OPTIONS}


def normalize_speaker(speaker: str) -> str:
    """Return the canonical stored form of *speaker*.

    Free-form names are where drift gets in. ``"other: Argus  McFiendy"`` and
    ``"other:Argus McFiendy"`` name one character but are two distinct speakers,
    and nothing downstream would ever reconcile them, so outer and repeated
    whitespace is collapsed. A roster name written behind the prefix
    (``"other:Donald"``) is unwrapped to the roster entry it already is.

    Case is deliberately left alone: "McFiendy" has no safe automatic casing,
    and title-casing it would be a different kind of wrong. Case variants are
    surfaced by ``barks-ocr-speaker-census`` for a human to merge instead.

    Args:
        speaker: The speaker value as written.

    Returns:
        The value to store. Unchanged if it is already canonical.

    """
    speaker = _WHITESPACE_RE.sub(" ", speaker.strip())
    if not speaker.startswith(OTHER_PREFIX):
        return speaker
    name = speaker[len(OTHER_PREFIX) :].strip()
    if not name:
        return speaker  # Names no one; `is_valid_speaker` rejects it either way.
    return _ROSTER_BY_CASEFOLD.get(name.casefold(), OTHER_PREFIX + name)


def speaker_key(speaker: str) -> str:
    """Return a key that collapses the spellings of one speaker onto one value.

    Case-insensitive, unlike :func:`normalize_speaker`, so the census can group
    ``other:crows`` with ``other:Crows`` and show them side by side.

    Args:
        speaker: The speaker value as stored.

    Returns:
        A grouping key. Not a storable speaker value.

    """
    return normalize_speaker(speaker).casefold()


def roster_text() -> str:
    """Render the vocabulary as the ``roster.txt`` handed to the vision pass.

    Generated rather than written by hand: the names the pass is told and the
    names ``vision_apply`` will accept are then the same names by construction.

    Returns:
        The full text of the roster file, newline-terminated.

    """
    lines = [
        "# Vision pass vocabulary — generated from barks_ocr/utils/vision_schema.py.",
        "# `vision_apply` validates every result.json against exactly these values,",
        "# and anything else aborts the run once the reading work is already done.",
        "",
        "speaker — one of:",
    ]
    width = max(len(name) for name in SPEAKER_OPTIONS)
    lines += [
        f"  {name.ljust(width)}  {SPEAKER_NOTES.get(name, '')}".rstrip() for name in SPEAKER_OPTIONS
    ]
    lines += [
        f'  anyone else goes behind the prefix: "{OTHER_PREFIX}Grandma Duck".',
        "  The name after the colon must not be empty.",
        "",
        f"speaker_confidence — one of: {', '.join(CONFIDENCE_OPTIONS)}",
        f"cap_colour — one of: {', '.join(CAP_COLOUR_OPTIONS)}, or null when no cap is visible",
        (
            "emphasis_spans — [[start, end, kind], ...], kind one of:"
            f" {', '.join(sorted(EMPHASIS_KINDS))}"
        ),
        "  start and end are character offsets into the group's current ai_text.",
    ]
    return "\n".join(lines) + "\n"


def is_valid_speaker(speaker: str) -> bool:
    """Return whether *speaker* is a roster name or a properly prefixed free-form one.

    A bare ``"other:"`` with nothing after it is not valid — it names no one.

    Args:
        speaker: The speaker value to check.

    Returns:
        True if the value is acceptable for the ``speaker`` field.

    """
    if speaker in ROSTER:
        return True
    return speaker.startswith(OTHER_PREFIX) and bool(speaker[len(OTHER_PREFIX) :].strip())

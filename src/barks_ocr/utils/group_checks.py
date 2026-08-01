"""Heuristic OCR-group checks that the user can dismiss per-group.

`ocr_check.py` raises these issue types as warnings, and the Kivy editor
lets the user mark any subset of them as acknowledged on the group's prelim
JSON. Once acknowledged, future `ocr_check` runs skip them for that group.

Adding a check means adding a predicate and one entry to
`DISMISSABLE_PREDICATES` — both `ocr_check` and the editor's acknowledge popup
read the registry, so neither needs touching.
"""

import re
from collections.abc import Callable

DISMISSABLE_ISSUE_TYPES: tuple[str, ...] = (
    "short_text",
    "error_notes",
    "page_number_notes",
    "dot_at_end_of_sentence",
    "em_dash_spacing",
    "double_hyphen",
    "unbalanced_quotes",
    "invalid_type",
    "whitespace",
    "florence-check",
)

# The `type` vocabulary Gemini is asked for. Anything else is a mis-labelled
# group: the corpus carries 26, as "caption", "speech", "dialogtext" and
# "dialogtext_bubble_id".
VALID_GROUP_TYPES: frozenset[str] = frozenset(
    {"dialogue", "narration", "thought", "sound_effect", "background", "title"}
)

# Word-uppercased forms (e.g. "MR", "PROF") that, when followed by ".", should
# NOT be flagged as a sentence end. Add common comic abbreviations as needed.
_SENTENCE_END_ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "MR",
        "MRS",
        "MS",
        "DR",
        "PROF",
        "ST",
        "JR",
        "SR",
        "SGT",
        "LT",
        "CAPT",
        "COL",
        "GEN",
        "MAJ",
        "REV",
        "GOV",
        "M.D",
        "PRES",
        "SEN",
        "REP",
        "HON",
        "INC",
        "LTD",
        "CO",
        "U.S",
        "VS",
        "ETC",
    }
)

_SENTENCE_END_RE = re.compile(r"((?:\w+\.)*\w*)(?<!\.)\.(?=\s*$|\s+[A-Z])", re.MULTILINE)

EM_DASH = "—"
# What may sit next to an em-dash. A line break or either edge of the text
# counts, so the wrapped and interrupted forms both pass.
_EM_DASH_BREAK_CHARS = frozenset({" ", "\n"})
_TERMINAL_PUNCTUATION = frozenset({"!", "?"})
_ADRIFT_PUNCTUATION_RE = re.compile(r"\s+[!?]")
_HYPHEN_RUN_RE = re.compile(r"-{2,}")


def is_short_text(group: dict) -> bool:
    ai_text = (group.get("ai_text") or "").strip().lower()
    return (len(ai_text) == 1) and (ai_text not in ("?", "!"))


def is_ai_detected_error(group: dict) -> bool:
    notes = (group.get("notes") or "").strip().lower()
    return "error" in notes and "art" in notes and "background" in notes


def has_page_number_notes(group: dict) -> bool:
    notes = (group.get("notes") or "").strip().lower()
    return "page number" in notes


def has_dot_at_end_of_sentence(group: dict) -> bool:
    ai_text = group.get("ai_text") or ""
    for match in _SENTENCE_END_RE.finditer(ai_text):
        word_before = match.group(1).upper()
        if word_before not in _SENTENCE_END_ABBREVIATIONS:
            return True
    return False


def has_em_dash_spacing_error(group: dict) -> bool:
    """Whether any em-dash is spaced against the corpus convention.

    One rule, replacing two narrower regexes. An em-dash must be preceded by a
    space, a line break or the start of the text, and followed by one of those,
    the end of the text, or terminal punctuation it hugs ("BEHIND -!"). What it
    must not do is float away from that punctuation ("WHAT GEEFS - ?").

    The convention is overwhelming — 5599 spaced both sides, 2566 ending a line,
    2000 ending the text. The old pair missed ~400 real breaches (a word run
    straight into a dash, doubled dashes) while flagging 191 occurrences of
    "OUT! - UH, OH!", which is correct usage: 60 of the 75 acknowledgements in
    the corpus were dismissals of exactly that false positive.
    """
    ai_text = group.get("ai_text") or ""
    for match in re.finditer(EM_DASH, ai_text):
        # Either edge of the text reads as a break, so a leading dash is fine.
        before = ai_text[match.start() - 1] if match.start() else "\n"
        if before not in _EM_DASH_BREAK_CHARS:
            return True

        rest = ai_text[match.end() :]
        if not rest:
            continue  # the dash ends the text: interrupted speech
        if rest[0] in _TERMINAL_PUNCTUATION:
            continue  # hugging its punctuation: "BEHIND -!"
        if rest[0] not in _EM_DASH_BREAK_CHARS:
            return True  # runs straight into a word, or another dash
        if _ADRIFT_PUNCTUATION_RE.match(rest):
            return True  # "WHAT GEEFS - ?"

    return False


def has_double_hyphen(group: dict) -> bool:
    """Whether the text has a run of hyphens, almost always an unconverted em-dash."""
    return bool(_HYPHEN_RUN_RE.search(group.get("ai_text") or ""))


def has_unbalanced_quotes(group: dict) -> bool:
    """Whether the text has an odd number of double-quote characters."""
    return ((group.get("ai_text") or "").count('"') % 2) == 1


def has_invalid_type(group: dict) -> bool:
    """Whether the group's ``type`` is outside the expected vocabulary."""
    return (group.get("type") or "").strip().lower() not in VALID_GROUP_TYPES


def has_whitespace_error(group: dict) -> bool:
    """Whether the text has stray whitespace: outer, per-line trailing, or doubled."""
    ai_text = group.get("ai_text") or ""
    if not ai_text:
        return False
    return (
        ai_text != ai_text.strip()
        or "  " in ai_text
        or any(line != line.rstrip() for line in ai_text.split("\n"))
    )


def cleaned_whitespace(ai_text: str) -> str:
    """Return ai_text with outer, trailing and doubled spaces removed.

    Line structure is preserved — the wrapping is meaningful and is what the
    line-height checks in ``ocr_check`` measure.
    """
    lines = [re.sub(r" {2,}", " ", line).rstrip() for line in ai_text.split("\n")]
    return "\n".join(lines).strip()


def with_em_dashes(ai_text: str) -> str:
    """Return ai_text with each run of two or more hyphens as a single em-dash.

    Runs, not pairs: the corpus has 221 of them and 70 are three hyphens or
    more, so a plain "--" swap would leave a stray hyphen behind.

    61 of those runs touch a word on at least one side, so converting them
    leaves an em-dash that ``has_em_dash_spacing_error`` will then flag. That is
    the intended outcome — the transcription is now right and only the spacing
    is in question, which needs a human.
    """
    return _HYPHEN_RUN_RE.sub(EM_DASH, ai_text)


def _never_fires(group: dict) -> bool:
    # florence-check is an external check (florence_check.py); it has no
    # in-process predicate, so the acknowledge popup never auto-checks it.
    # The user toggles it manually to opt a group out of future florence runs.
    del group
    return False


DISMISSABLE_PREDICATES: dict[str, Callable[[dict], bool]] = {
    "short_text": is_short_text,
    "error_notes": is_ai_detected_error,
    "page_number_notes": has_page_number_notes,
    "dot_at_end_of_sentence": has_dot_at_end_of_sentence,
    "em_dash_spacing": has_em_dash_spacing_error,
    "double_hyphen": has_double_hyphen,
    "unbalanced_quotes": has_unbalanced_quotes,
    "invalid_type": has_invalid_type,
    "whitespace": has_whitespace_error,
    "florence-check": _never_fires,
}

# Issue types that were renamed or merged. 75 groups carry an acknowledgement
# under "dash_wrong_space" from when the em-dash rule was two narrower checks;
# honouring the old name keeps those dismissals alive without rewriting any
# prelim file.
_ACKNOWLEDGEMENT_ALIASES: dict[str, tuple[str, ...]] = {
    "em_dash_spacing": ("dash_wrong_space", "dash_no_spaces"),
}


def get_fired_dismissable_issues(group: dict) -> list[str]:
    """Return the dismissable issue types currently firing on *group*."""
    return [t for t, pred in DISMISSABLE_PREDICATES.items() if pred(group)]


def is_acknowledged(group: dict, issue_type: str) -> bool:
    """Return True if *issue_type*, or a name it superseded, is acknowledged."""
    acknowledged = group.get("acknowledged_issues") or []
    if issue_type in acknowledged:
        return True
    return any(alias in acknowledged for alias in _ACKNOWLEDGEMENT_ALIASES.get(issue_type, ()))

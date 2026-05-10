"""Heuristic OCR-group checks that the user can dismiss per-group.

`ocr_check.py` raises these issue types as warnings, and the Kivy editor
lets the user mark any subset of them as acknowledged on the group's prelim
JSON. Once acknowledged, future `ocr_check` runs skip them for that group.
"""

import re
from collections.abc import Callable

DISMISSABLE_ISSUE_TYPES: tuple[str, ...] = (
    "short_text",
    "error_notes",
    "page_number_notes",
    "dot_at_end_of_sentence",
    "dash_wrong_space",
    "dash_no_spaces",
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
_DASH_WRONG_SPACE_RE = re.compile("—\\s+[!?]|[!?]\\s+—")
_DASH_NO_SPACES_RE = re.compile("[^\\W\\d_]—[^\\W\\d_]")


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


def has_dash_wrong_space(group: dict) -> bool:
    ai_text = group.get("ai_text") or ""
    return bool(_DASH_WRONG_SPACE_RE.search(ai_text))


def has_dash_no_spaces(group: dict) -> bool:
    ai_text = group.get("ai_text") or ""
    return bool(_DASH_NO_SPACES_RE.search(ai_text))


DISMISSABLE_PREDICATES: dict[str, Callable[[dict], bool]] = {
    "short_text": is_short_text,
    "error_notes": is_ai_detected_error,
    "page_number_notes": has_page_number_notes,
    "dot_at_end_of_sentence": has_dot_at_end_of_sentence,
    "dash_wrong_space": has_dash_wrong_space,
    "dash_no_spaces": has_dash_no_spaces,
}


def get_fired_dismissable_issues(group: dict) -> list[str]:
    """Return the dismissable issue types currently firing on *group*."""
    return [t for t, pred in DISMISSABLE_PREDICATES.items() if pred(group)]


def is_acknowledged(group: dict, issue_type: str) -> bool:
    """Return True if *issue_type* is in the group's acknowledged_issues list."""
    return issue_type in (group.get("acknowledged_issues") or [])

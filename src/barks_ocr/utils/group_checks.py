"""Heuristic OCR-group checks that the user can dismiss per-group.

`ocr_check.py` raises these issue types as warnings, and the Kivy editor
lets the user mark any subset of them as acknowledged on the group's prelim
JSON. Once acknowledged, future `ocr_check` runs skip them for that group.
"""

from collections.abc import Callable

DISMISSABLE_ISSUE_TYPES: tuple[str, ...] = (
    "short_text",
    "error_notes",
    "page_number_notes",
)


def is_short_text(group: dict) -> bool:
    ai_text = (group.get("ai_text") or "").strip().lower()
    return (len(ai_text) == 1) and (ai_text not in ("?", "!"))


def is_ai_detected_error(group: dict) -> bool:
    notes = (group.get("notes") or "").strip().lower()
    return "error" in notes and "art" in notes and "background" in notes


def has_page_number_notes(group: dict) -> bool:
    notes = (group.get("notes") or "").strip().lower()
    return "page number" in notes


DISMISSABLE_PREDICATES: dict[str, Callable[[dict], bool]] = {
    "short_text": is_short_text,
    "error_notes": is_ai_detected_error,
    "page_number_notes": has_page_number_notes,
}


def get_fired_dismissable_issues(group: dict) -> list[str]:
    """Return the dismissable issue types currently firing on *group*."""
    return [t for t, pred in DISMISSABLE_PREDICATES.items() if pred(group)]


def is_acknowledged(group: dict, issue_type: str) -> bool:
    """Return True if *issue_type* is in the group's acknowledged_issues list."""
    return issue_type in (group.get("acknowledged_issues") or [])

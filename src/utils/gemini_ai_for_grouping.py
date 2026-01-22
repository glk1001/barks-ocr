import copy
from typing import Any


def get_cleaned_text(text: str) -> tuple[str, str]:
    reason = ""
    if r"\\n" in text:
        text = text.replace(r"\\n", "\\n")
        reason = "Double backslash newline"
    if r"\\'" in text:
        text = text.replace(r"\\'", "'")
        reason = "Double backslash single quote"
    if r"\'" in text:
        text = text.replace(r"\'", "'")
        reason = "Single backslash single quote"

    return text, reason


def norm2ai(bounds: list[dict[str, Any]], height: int, width: int) -> list[dict[str, Any]]:
    """Convert normal image bounds to AI supported Bounds."""
    norm_bounds = copy.deepcopy(bounds)

    for bound in norm_bounds:
        box = bound["text_box"]
        norm_box = []
        for xy in box:
            x = int((xy[0] / width) * 1000)
            y = int((xy[1] / height) * 1000)
            # Note: Gemini coords have y values before x values.
            norm_box.append(y)
            norm_box.append(x)

        bound["text_box"] = norm_box

    return norm_bounds

# ruff: noqa: INP001, T201, SLF001 -- a standalone script, not a package module;
# printing the tally is the whole point; and it deliberately measures
# `ocr_check`'s own private checks rather than a copy of them that could drift.
"""Classify every cross-engine `text_mismatch` as a reading or a wrapping fault.

    uv run --offline python scripts/vision/wrap_mismatch_sweep.py [VOLUMES]

`text_mismatch` is by far the largest issue class, and most of it is not a
disagreement about the words at all. The two engines routinely hold the identical
word sequence and differ only in where the lines break -- a *format* error in one
of them, reported as if the reading were in doubt.

This sizes that class and asks, of each wrap-only pair, whether anything in
`ocr_check` can already see it: a wrong wrap usually makes the text overflow its
box (`text_does_not_fit`) or pack the lines too tightly (`too_many_lines`), and
`--fix-newlines` will then transplant the other engine's pattern. What is left
over -- both sides passing every layout check, and so invisible to the fixers --
is the interesting residue. For those, the engine's own `cleaned_box_texts`
fragments are consulted: they come off the real lettering, so the line bands they
fall into say how the drawing actually broke the lines.

Corpus at 2026-08-27 (vols 1-29): 5,722 mismatched pairs, 3,734 of them wrap-only,
3,134 of those already visible to a fixer, 600 not. Of the 600 the fragment bands
decide 154. Every one of the 3,734 is in vols 21-29.

See `wrap_fix_simulation.py` for what `--fix-newlines` would actually rewrite, and
for the band test's accuracy.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from intspan import intspan
from loguru import logger
from PIL import ImageFont

from barks_ocr.tools import ocr_check as oc

# The layout checks log every measurement at DEBUG, which buries the tally.
logger.remove()

# Two line proportions closer than this are the same answer, not a winner.
BAND_DECISION_MARGIN = 0.05
MIN_BANDS_TO_COMPARE = 2


def volume_dirs(volumes: list[int]) -> list[tuple[int, Path]]:
    """Return the prelim directory for each requested volume, in volume order.

    Args:
        volumes: Volume numbers to include; empty means every volume.

    Returns:
        (volume number, directory) pairs, skipping the "(copy)" duplicates.

    """
    found: list[tuple[int, Path]] = []
    for path in OCR_PRELIM_DIR.glob("Carl Barks Vol. *"):
        match = re.search(r"Vol\. (\d+)", path.name)
        if match is None or "(copy)" in path.name:
            continue
        volume = int(match.group(1))
        if not volumes or volume in volumes:
            found.append((volume, path))
    return sorted(found)


def line_bands(group: dict) -> list[float]:
    """Return the width of each line band in the engine's own OCR fragments.

    The fragments in ``cleaned_box_texts`` are measured off the drawing, so the
    y-bands they fall into are how the lettering really breaks -- evidence that
    needs no second engine and no image.

    Args:
        group: One group's JSON dict.

    Returns:
        One width per band, top to bottom; empty when the fragments are unusable.

    """
    fragments = group.get("cleaned_box_texts") or {}
    if not fragments:
        return []

    rows: list[tuple[float, float, float]] = []
    for fragment in fragments.values():
        box = fragment.get("text_box") or []
        if oc.text_box_problem(box) is not None:
            return []
        rows.append((min(p[1] for p in box), min(p[0] for p in box), max(p[0] for p in box)))
    rows.sort()

    # Half a line height apart is a new line: fragments of one line sit within a
    # few pixels of each other, and the next line is a full line height away.
    tolerance = max(10.0, (oc._implied_line_height(group) or 30) * 0.5)
    widths: list[float] = []
    band_y: float | None = None
    left = right = 0.0
    for y, x0, x1 in rows:
        if band_y is None or y - band_y > tolerance:
            if band_y is not None:
                widths.append(right - left)
            band_y, left, right = y, x0, x1
        else:
            left, right = min(left, x0), max(right, x1)
    if band_y is not None:
        widths.append(right - left)
    return widths


def rendered_line_widths(group: dict) -> list[float]:
    """Return the stored wrap's line widths, measured the way the fit check does."""
    lines = oc._plain(group).split("\n")
    _width, height = oc._box_wh(group["text_box"])
    size = max(oc.FIT_MIN_FONT_SIZE, int(height / len(lines) * oc.FIT_HEIGHT_FRACTION))
    font = ImageFont.truetype(str(oc.FIT_FONT_PATH), size)
    return [font.getbbox(line)[2] - font.getbbox(line)[0] for line in lines]


def shape_error(group: dict) -> float | None:
    """How far the stored wrap's line proportions sit from the fragment bands.

    Both sides are normalized against their own longest line, so the comic's font
    and Verdana never have to agree on absolute width -- only on which line is
    long and which is short.

    Args:
        group: One group's JSON dict.

    Returns:
        Mean absolute difference in proportion, or None when the two cannot be
        compared (a different number of lines, or no usable fragments).

    """
    measured, drawn = line_bands(group), rendered_line_widths(group)
    if len(measured) != len(drawn) or len(measured) < MIN_BANDS_TO_COMPARE:
        return None
    if max(measured) <= 0 or max(drawn) <= 0:
        return None
    scaled_measured = [x / max(measured) for x in measured]
    scaled_drawn = [x / max(drawn) for x in drawn]
    return sum(abs(a - b) for a, b in zip(scaled_measured, scaled_drawn, strict=True)) / len(
        scaled_measured
    )


def classify_pair(easy_group: dict, paddle_group: dict, counts: Counter) -> None:
    """Tally one mismatched pair: real difference, or which fixer could reach it."""
    easy_text, paddle_text = oc._plain(easy_group), oc._plain(paddle_group)
    counts["text_mismatch"] += 1
    if easy_text.split() != paddle_text.split():
        counts["real text difference"] += 1
        return

    counts["wrap-only"] += 1
    same_lines = easy_text.count("\n") == paddle_text.count("\n")
    counts["  same line count" if same_lines else "  different line count"] += 1


def sweep(volumes: list[int]) -> Counter:
    """Walk every page of the requested volumes and tally its mismatched pairs."""
    counts: Counter = Counter()
    for _volume, vol_dir in volume_dirs(volumes):
        for easy_file in sorted(vol_dir.glob("*-easyocr-gemini-prelim-groups.json")):
            paddle_file = Path(str(easy_file).replace("-easyocr-", "-paddleocr-"))
            if not paddle_file.exists():
                continue
            page = easy_file.name.split("-")[0]
            try:
                easy = json.loads(easy_file.read_text())["groups"]
                paddle = json.loads(paddle_file.read_text())["groups"]
            except (ValueError, KeyError):
                counts["unreadable page"] += 1
                continue

            easy_panels, paddle_panels = oc._groups_by_panel(easy), oc._groups_by_panel(paddle)
            easy_median = oc._page_median_line_height(easy, oc.LINE_HEIGHT_BIMODAL_RATIO)
            paddle_median = oc._page_median_line_height(paddle, oc.LINE_HEIGHT_BIMODAL_RATIO)

            for panel in sorted((set(easy_panels) | set(paddle_panels)) - {-1}):
                pairs = zip(easy_panels.get(panel, []), paddle_panels.get(panel, []), strict=False)
                for (_easy_id, easy_group), (_paddle_id, paddle_group) in pairs:
                    easy_text, paddle_text = oc._plain(easy_group), oc._plain(paddle_group)
                    if easy_text == paddle_text:
                        continue
                    classify_pair(easy_group, paddle_group, counts)
                    if easy_text.split() != paddle_text.split():
                        continue
                    _tally_reach(easy_group, paddle_group, easy_median, paddle_median, page, counts)
    return counts


def _tally_reach(  # noqa: PLR0913
    easy_group: dict,
    paddle_group: dict,
    easy_median: float | None,
    paddle_median: float | None,
    page: str,
    counts: Counter,
) -> None:
    """Tally whether a fixer sees this wrap-only pair, and what the bands say."""
    try:
        settled = oc._layout_ok(easy_group, page, easy_median) and oc._layout_ok(
            paddle_group, page, paddle_median
        )
    except (KeyError, TypeError, ValueError):
        counts["  unmeasurable"] += 1
        return

    if not settled:
        counts["  a fixer already sees it"] += 1
        return

    counts["  NO fixer sees it"] += 1
    easy_error, paddle_error = shape_error(easy_group), shape_error(paddle_group)
    if easy_error is None or paddle_error is None:
        counts["    bands unusable"] += 1
    elif abs(easy_error - paddle_error) < BAND_DECISION_MARGIN:
        counts["    bands cannot separate them"] += 1
    else:
        counts["    bands pick a winner"] += 1


def main() -> None:
    """Sweep the volumes named on the command line, or every volume."""
    volumes = list(intspan(sys.argv[1])) if len(sys.argv) > 1 else []
    counts = sweep(volumes)
    for label, count in counts.items():
        print(f"{count:6}  {label}")


if __name__ == "__main__":
    main()

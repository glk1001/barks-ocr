# ruff: noqa: INP001, T201, SLF001 -- a standalone script, not a package module;
# printing the tally is the whole point; and it deliberately drives `ocr_check`'s
# own private fixer rather than a copy of it that could drift.
"""What `--fix-newlines` would really rewrite, and whether the bands can be trusted.

    uv run --offline python scripts/vision/wrap_fix_simulation.py [VOLUMES] [--out FILE]

The companion to `wrap_mismatch_sweep.py`, which sizes the wrap-only class. This
one answers the two questions that decide what to do about it.

**What a fix pass would do.** For every wrap-only pair a layout check already
flags, `_check_text_layout` is run on a *copy* with `--fix-newlines` on, so the
transplant is exercised without writing anything. The refusals matter as much as
the rewrites: the fixer declines unless the donor is itself well laid out and the
result passes too.

**Whether the bands can settle the rest.** For pairs no fixer sees, each side's
stored wrap is scored against its own OCR fragment bands, and the closer one
wins. Vols 21-29 at 2026-08-27: 2,756 sides rewritten, 2,752 of them landing on
the other engine's exact wrapping; 561 refused; and of 154 band-decided pairs,
144 say paddleocr.

That skew is real rather than an artefact -- checked against the drawings, the
band test was right on 5 of 6 sampled pairs, two of them naming easyocr. The one
failure was a sign whose top line is hidden behind a balloon, where easyocr's
fragments see one line fewer than paddleocr's; requiring the two engines' band
counts to agree removes it, and 12 others, from the 154.

The band helpers are duplicated from `wrap_mismatch_sweep.py` rather than
imported: neither file is a package module, and a sys.path graft to share forty
lines costs more than it saves.
"""

import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_DIR
from intspan import intspan
from loguru import logger
from PIL import ImageFont

from barks_ocr.tools import ocr_check as oc

# The layout checks log every measurement at DEBUG, which buries the tally.
logger.remove()

BAND_DECISION_MARGIN = 0.05
MIN_BANDS_TO_COMPARE = 2
SAMPLE_ROWS = 10


def volume_dirs(volumes: list[int]) -> list[tuple[int, Path]]:
    """Return the prelim directory for each requested volume, in volume order."""
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
    """Return the width of each line band in the engine's own OCR fragments."""
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


def shape_error(group: dict) -> float | None:
    """How far the stored wrap's line proportions sit from the fragment bands."""
    measured = line_bands(group)
    lines = oc._plain(group).split("\n")
    _width, height = oc._box_wh(group["text_box"])
    size = max(oc.FIT_MIN_FONT_SIZE, int(height / len(lines) * oc.FIT_HEIGHT_FRACTION))
    font = ImageFont.truetype(str(oc.FIT_FONT_PATH), size)
    drawn = [font.getbbox(line)[2] - font.getbbox(line)[0] for line in lines]

    if len(measured) != len(drawn) or len(measured) < MIN_BANDS_TO_COMPARE:
        return None
    if max(measured) <= 0 or max(drawn) <= 0:
        return None
    scaled_measured = [x / max(measured) for x in measured]
    scaled_drawn = [x / max(drawn) for x in drawn]
    return sum(abs(a - b) for a, b in zip(scaled_measured, scaled_drawn, strict=True)) / len(
        scaled_measured
    )


def simulate_transplant(  # noqa: PLR0913
    checker: oc.OcrChecker,
    group: dict,
    group_id: str,
    donor_groups: dict,
    medians: tuple[float | None, float | None],
    page: str,
) -> tuple[bool, str | None, str]:
    """Run the wrapping fixer over a copy of one group, writing nothing.

    Args:
        checker: An OcrChecker built with ``FixFlags(newlines=True)``.
        group: The group to rewrap.
        group_id: Its id, for the fixer's log lines.
        donor_groups: The other engine's groups for the same page.
        medians: (this page's line-height median, the donor page's).
        page: Fanta page number, for the fit check's log lines.

    Returns:
        (was rewritten, the issue still standing if not, the resulting text).

    """
    working = copy.deepcopy(group)
    context = oc.PageContext(
        volume=0,
        fanta_page=page,
        engine="",
        # `_check_text_layout` and the transplant never touch the panel boxes;
        # building a real PagePanelBoxes here would need the whole title loaded.
        # (ty checks this file through the pre-commit hook, which passes staged
        # paths directly, even though ty.toml's own scope is `src` alone.)
        panel_boxes=None,  # ty: ignore[invalid-argument-type]
        line_heights=oc.PageLineHeights(own=medians[0], other=medians[1]),
        # A stand-in for the donor SpeechPageGroup: the transplant only ever
        # reads `speech_page_json`.
        other_page_group=SimpleNamespace(  # ty: ignore[invalid-argument-type]
            speech_page_json={"groups": donor_groups}
        ),
    )
    fixed, issue, _ratio = checker._check_text_layout(working, group_id, context)
    return fixed, issue, oc._plain(working)


def sweep(volumes: list[int]) -> tuple[Counter, list[tuple]]:
    """Simulate the fixer and score the bands over every wrap-only pair.

    Args:
        volumes: Volume numbers to include; empty means every volume.

    Returns:
        (tally, the band-decided pairs as rows for the sample table).

    """
    checker = oc.OcrChecker(ComicsDatabase(), oc.FixFlags(newlines=True))
    counts: Counter = Counter()
    decided: list[tuple] = []

    for volume, vol_dir in volume_dirs(volumes):
        for easy_file in sorted(vol_dir.glob("*-easyocr-gemini-prelim-groups.json")):
            paddle_file = Path(str(easy_file).replace("-easyocr-", "-paddleocr-"))
            if not paddle_file.exists():
                continue
            page = easy_file.name.split("-")[0]
            try:
                easy = json.loads(easy_file.read_text())["groups"]
                paddle = json.loads(paddle_file.read_text())["groups"]
            except (ValueError, KeyError):
                continue

            easy_panels, paddle_panels = oc._groups_by_panel(easy), oc._groups_by_panel(paddle)
            medians = (
                oc._page_median_line_height(easy, oc.LINE_HEIGHT_BIMODAL_RATIO),
                oc._page_median_line_height(paddle, oc.LINE_HEIGHT_BIMODAL_RATIO),
            )

            for panel in sorted((set(easy_panels) | set(paddle_panels)) - {-1}):
                pairs = zip(easy_panels.get(panel, []), paddle_panels.get(panel, []), strict=False)
                for (easy_id, easy_group), (paddle_id, paddle_group) in pairs:
                    easy_text, paddle_text = oc._plain(easy_group), oc._plain(paddle_group)
                    if easy_text == paddle_text or easy_text.split() != paddle_text.split():
                        continue
                    counts["wrap-only pairs"] += 1
                    _measure_pair(
                        checker,
                        counts,
                        decided,
                        (volume, page, panel),
                        ((easy_id, easy_group, easy), (paddle_id, paddle_group, paddle)),
                        medians,
                    )
    return counts, decided


def _measure_pair(  # noqa: PLR0913
    checker: oc.OcrChecker,
    counts: Counter,
    decided: list[tuple],
    where: tuple[int, str, int],
    sides: tuple[tuple[str, dict, dict], tuple[str, dict, dict]],
    medians: tuple[float | None, float | None],
) -> None:
    """Simulate the fixer on one pair, or score its bands when no fixer sees it."""
    volume, page, panel = where
    (easy_id, easy_group, easy), (paddle_id, paddle_group, paddle) = sides
    try:
        easy_ok = oc._layout_ok(easy_group, page, medians[0])
        paddle_ok = oc._layout_ok(paddle_group, page, medians[1])
    except (KeyError, TypeError, ValueError):
        counts["  unmeasurable"] += 1
        return

    if easy_ok and paddle_ok:
        counts["  no fixer sees it"] += 1
        easy_error, paddle_error = shape_error(easy_group), shape_error(paddle_group)
        if easy_error is None or paddle_error is None:
            counts["    bands unusable"] += 1
            return
        if abs(easy_error - paddle_error) < BAND_DECISION_MARGIN:
            counts["    bands cannot separate"] += 1
            return
        winner = "paddle" if paddle_error < easy_error else "easy"
        # The one verified failure had the engines seeing a different number of
        # lines -- an occluded top line -- so flag that rather than trust it.
        guarded = len(line_bands(easy_group)) == len(line_bands(paddle_group))
        counts[f"    bands say {winner}"] += 1
        if not guarded:
            counts["      ...but the engines' band counts differ"] += 1
        decided.append(
            (
                volume,
                page,
                panel,
                easy_id,
                paddle_id,
                round(easy_error, 3),
                round(paddle_error, 3),
                winner,
                guarded,
            )
        )
        return

    # Both sides are checked: a pair can have either engine flagged, or both.
    counts["  a fixer sees it"] += 1
    sides_to_fix = (
        (easy_group, easy_id, paddle, paddle_group, medians, easy_ok),
        (paddle_group, paddle_id, easy, easy_group, medians[::-1], paddle_ok),
    )
    for group, group_id, donor_page, donor_group, page_medians, settled in sides_to_fix:
        if settled:
            continue
        fixed, issue, new_text = simulate_transplant(
            checker, group, group_id, donor_page, page_medians, page
        )
        if not fixed:
            counts[f"    refused ({issue})"] += 1
            continue
        counts["    REWRITTEN"] += 1
        counts[
            "      ...to the other engine's wrap"
            if new_text == oc._plain(donor_group)
            else "      ...to a third wrapping"
        ] += 1


def main() -> None:
    """Sweep the volumes named on the command line, or every volume."""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    volumes = list(intspan(args[0])) if args else []
    counts, decided = sweep(volumes)

    for label, count in counts.items():
        print(f"{count:6}  {label}")

    print(f"\nband-decided pairs: {len(decided)}")
    print("sample (vol, page, panel, easy id, paddle id, easy err, paddle err, winner, guarded):")
    step = max(1, len(decided) // SAMPLE_ROWS)
    for row in decided[::step][:SAMPLE_ROWS]:
        print("  ", row)

    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
        out.write_text(json.dumps(decided, indent=1))
        print(f"\nAll {len(decided)} decided pairs written to {out}")


if __name__ == "__main__":
    main()

# ruff: noqa: T201
import json
import math
import subprocess
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from enum import Enum, auto
from itertools import zip_longest
from pathlib import Path
from statistics import mean, median

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_titles
from barks_fantagraphics.comics_utils import get_backup_file
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.panel_boxes import PagePanelBoxes, TitlePagesPanelBoxes, TitlePanelBoxes
from barks_fantagraphics.speech_groupers import (
    OcrTypes,
    SpeechGroups,
    SpeechPageGroup,
    # Private, and imported anyway: it *is* the order `renumber_groups()`
    # numbers by, and a local copy of the key would silently drift from it --
    # which is the whole fault `_out_of_order_group` exists to catch.
    _group_sort_key,
)
from barks_fantagraphics.speech_markup import escape_markup, has_markup, strip_markup
from comic_utils.common_typer_options import TitleArg, VolumesArg
from intspan import intspan
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from barks_ocr.utils.engine_compare import BOX_IOU_MIN, box_iou, differing_attrs
from barks_ocr.utils.geometry import Rect
from barks_ocr.utils.group_checks import (
    PANEL_HAS_NO_TEXT_ISSUE,
    TEXT_NEVER_FITS_ISSUE,
    cleaned_whitespace,
    get_fired_dismissable_issues,
    is_acknowledged,
    panels_with_no_groups,
    with_dash_fixes,
)
from barks_ocr.utils.ocr_box import OcrBox, PointList, points_bbox, text_box_problem

# ── Text-fit constants ────────────────────────────────────────────────────────

FIT_FONT_PATH = Path("/home/greg/Prj/fonts/verdana.ttf")
FIT_WIDTH_TOLERANCE = 1.5  # allow 50% overflow (Verdana is not the comic's font)
FIT_WIDTH_TOLERANCE_SFX = 4.0  # allow 300% overflow: sound-effect lettering is stylized
FIT_HEIGHT_FRACTION = 0.75  # derived font size ≈ box line height * this
FIT_MIN_FONT_SIZE = 8
MIN_MATCH_RATIO = 0.7  # SequenceMatcher threshold for cross-engine pairing
MAX_FIX_PASSES = 5  # one fix can enable another; cap the re-check loop
# Lettering that is deliberately unlike the surrounding dialogue, so neither its
# width nor its line height says anything about the page. "title" is the
# splash-page logo: hand-drawn, one huge word per line, and nothing Verdana can
# model — measured strictly it produced 18 bogus text_does_not_fit flags.
STYLIZED_TYPES = ("sound_effect", "background", "title")
# Below this, lettering counts as axis-aligned and the group's text_box is the
# right thing to measure. Matches OcrBox.is_approx_rect.
FRAGMENT_ANGLE_THRESHOLD_DEG = 5.0

# ── Line-height constants ─────────────────────────────────────────────────────
# The fit check derives font size from box height / line count, so extra line
# breaks only ever make text easier to pass. These catch that inverse failure by
# comparing a group's line packing against the rest of its page.
# Real lettering is very consistent within a page, so correct groups cluster
# tightly around the median.
#
# Two bands, because one threshold cannot serve both needs. Below the outlier
# fraction the packing is unambiguous and always reported. Between the two lies
# a band that is mostly noise — on the cleaned vol 1, 66 of 72 flags sat there,
# while the uncleaned vols 19/21 barely change across it (5.1% -> 4.6%) — so it
# is reported only on request, as "too_many_lines_marginal".
LINE_HEIGHT_OUTLIER_FRACTION = 0.85  # below this * page median => surplus line breaks
LINE_HEIGHT_MARGINAL_FRACTION = 0.9  # ...and below this => marginal, opt-in
MIN_GROUPS_FOR_LINE_HEIGHT = 5  # too few groups for a trustworthy page median
MIN_LINES_FOR_LINE_HEIGHT = 2  # one-line boxes measure high; see _implied_line_height
# When the plain median sits this far above the page's densest cluster of line
# heights, the median is measuring the wrong lettering -- see
# ``_page_median_line_height``. 1.2 clears the 1.05-1.15 shoulder of ordinary
# pages by a wide margin: 9,395 of 10,190 corpus pages sit at a ratio of 1.0.
LINE_HEIGHT_BIMODAL_RATIO = 1.2
_MODE_SMALLEST_SAMPLE = 2  # half-sample recursion stops here and averages the pair
BAR_WIDTH = 24  # width of the engine-agreement progress bar

_FIT_FONT_MISSING_WARNED: list[bool] = [False]
_FIT_MEASURE_DRAW = ImageDraw.Draw(Image.new("RGB", (1, 1)))

# ── Issue data ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PageLineHeights:
    """Median implied line height for a page, in this engine and the other one."""

    own: float | None
    other: float | None


@dataclass(frozen=True)
class PageContext:
    """Which page/engine is being checked, and what the checks need about it.

    All of this is derivable from the ``SpeechPageGroup``; carrying it together
    keeps it off every check's parameter list.
    """

    volume: int
    fanta_page: str
    engine: str
    panel_boxes: PagePanelBoxes
    line_heights: PageLineHeights
    other_page_group: SpeechPageGroup | None

    @classmethod
    def build(
        cls,
        page_group: SpeechPageGroup,
        panel_boxes: PagePanelBoxes,
        line_heights: PageLineHeights,
        other_page_group: SpeechPageGroup | None,
    ) -> "PageContext":
        """Derive the context from the page group being checked."""
        return cls(
            volume=page_group.fanta_vol,
            fanta_page=page_group.fanta_page,
            engine=str(page_group.ocr_index),
            panel_boxes=panel_boxes,
            line_heights=line_heights,
            other_page_group=other_page_group,
        )


@dataclass(frozen=True)
class MissingPrelim:
    """A title's pages that have no prelim OCR file — a gap in the OCR data.

    Split by how much is missing: a page with neither engine's file is OCR
    that never ran, while a page missing only one engine's file is a
    lopsided capture that engine agreement can never confirm.
    """

    volume: int
    title_str: str
    pages_both: list[str]
    pages_by_engine: dict[str, list[str]]


@dataclass(frozen=True)
class UnreadablePrelim:
    """A prelim OCR file that will not parse, and why."""

    volume: int
    title_str: str
    json_file: Path
    reason: str


def _build_missing_prelim(
    volume: int, title_str: str, missing_by_page: dict[str, set[str]]
) -> MissingPrelim:
    """Fold {page: missing engines} into a MissingPrelim for one title."""
    pages_both = sorted(p for p, engines in missing_by_page.items() if len(engines) > 1)
    pages_by_engine: dict[str, list[str]] = defaultdict(list)
    for page in sorted(missing_by_page):
        engines = missing_by_page[page]
        if len(engines) == 1:
            pages_by_engine[next(iter(engines))].append(page)
    return MissingPrelim(volume, title_str, pages_both, dict(pages_by_engine))


@dataclass(frozen=True)
class TitleAgreement:
    """How many of a title's pages both engines read identically."""

    agreed: int
    total: int
    volume: int = 0
    title_str: str = ""

    def with_title(self, volume: int, title_str: str) -> "TitleAgreement":
        """Return a copy labelled with the title it belongs to."""
        return TitleAgreement(self.agreed, self.total, volume, title_str)


@dataclass(frozen=True)
class MissingPanel:
    """A panel one engine found speech in and the other did not."""

    volume: int
    fanta_page: str
    panel_num: int
    missing_in: str


@dataclass(frozen=True)
class FixFlags:
    """Which repairs a run is allowed to write. All off by default."""

    panel_nums: bool = False
    groups_order: bool = False
    newlines: bool = False
    whitespace: bool = False
    dashes: bool = False

    def any_enabled(self) -> bool:
        """Whether this run will write to the prelim files at all."""
        return any(
            (self.panel_nums, self.groups_order, self.newlines, self.whitespace, self.dashes)
        )


@dataclass(frozen=True)
class LineHeightLimits:
    """The two line-height bands, and whether the marginal one is reported."""

    outlier: float = LINE_HEIGHT_OUTLIER_FRACTION
    marginal: float = LINE_HEIGHT_MARGINAL_FRACTION
    include_marginal: bool = False
    bimodal_ratio: float = LINE_HEIGHT_BIMODAL_RATIO


# One queue entry per group carries the group's most severe issue; this is
# that order, worst first. Types not listed (the dismissable cosmetic ones)
# rank after all of these.
_QUEUE_SEVERITY: tuple[str, ...] = (
    "bad_text_box",
    "invalid_markup",
    # Beside `invalid_markup` because it is the same kind of fault: a stored
    # value outside its vocabulary, which no downstream consumer can interpret.
    # It used to be unlisted, and an unlisted type ranks after every issue here
    # -- so a group with a bad `type` and anything else at all was queued under
    # the anything else, and the bad type was never the thing the reviewer was
    # sent to look at. Vol 27 page 138 had six invalid types and offered five.
    "invalid_type",
    "empty_text",
    # Ahead of everything below it because it invalidates them: the cross-engine
    # checks pair a panel's groups positionally, and a queue entry pointing at
    # a group id a renumber is about to change points at the wrong group.
    "groups_out_of_order",
    "panel_unassigned",
    # Same fault as `panel_unassigned`, and the panel it belongs in is known;
    # below it because --fix-panel-nums clears this one without a reviewer.
    "panel_num_fixable",
    "panel_num_out_of_range",
    "panel_num_mismatch",
    # Last of the panel_num block, because it is the weakest of them: it names a
    # page, not a fault in the group it is anchored to, and a silent panel is
    # legitimate. Any concrete per-group diagnosis above should win the entry.
    "panel_nums_not_contiguous",
    "text_does_not_fit",
    "too_many_lines",
    "too_many_lines_marginal",
    # The cross-engine block. A box disagreement is a concrete geometry fault and
    # is worth seeing ahead of a text diff; an attribute difference is the least
    # urgent of the set. "box_mismatch" and "text_mismatch" cannot both fire on
    # one pair — the box check only runs where the two readings are identical —
    # so their order only matters against the checks above.
    "box_mismatch",
    "text_mismatch",
    "attrs_mismatch",
    "only_in_easy",
    "only_in_paddle",
)


def _severity_rank(issue_type: str) -> int:
    try:
        return _QUEUE_SEVERITY.index(issue_type)
    except ValueError:
        return len(_QUEUE_SEVERITY)


@dataclass
class IssueFound:
    volume: int
    fanta_page: str
    engine: str
    group_id: str
    issue_type: str
    panel_num: int
    text: str
    notes: str
    ratio: float | None = None


def _format_page_ranges(fanta_pages: list[str]) -> str:
    """Collapse sorted page numbers into ranges, keeping their zero padding.

    ``intspan`` would do the collapsing but returns bare ints, and these pages
    are named after zero-padded files ("096-easyocr-...json"), so the padding
    has to survive.
    """
    if not fanta_pages:
        return ""

    runs: list[list[str]] = [[fanta_pages[0]]]
    for page in fanta_pages[1:]:
        if int(page) == int(runs[-1][-1]) + 1:
            runs[-1].append(page)
        else:
            runs.append([page])

    return ", ".join(run[0] if len(run) == 1 else f"{run[0]}-{run[-1]}" for run in runs)


def _print_engine_agreement(all_agreement: list[TitleAgreement]) -> None:
    """Print how many pages both engines read identically, by volume and overall.

    This is the completion metric. A page both engines agree on has independent
    corroboration and needs no further reconciliation; the rest is the work left.
    """
    per_volume: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    for entry in all_agreement:
        per_volume[entry.volume][0] += entry.agreed
        per_volume[entry.volume][1] += entry.total

    agreed = sum(v[0] for v in per_volume.values())
    total = sum(v[1] for v in per_volume.values())
    if not total:
        return

    print()
    print(f"Engine agreement — {agreed}/{total} pages ({agreed / total:.1%}):")
    for volume in sorted(per_volume):
        vol_agreed, vol_total = per_volume[volume]
        if not vol_total:
            continue
        fraction = vol_agreed / vol_total
        bar = "#" * round(fraction * BAR_WIDTH)
        print(
            f"  Vol {volume:>2}  {bar:<{BAR_WIDTH}}  {fraction:>5.1%}  ({vol_agreed}/{vol_total})"
        )


def _print_missing_panels(all_missing_panels: list[MissingPanel]) -> None:
    """List panels one engine found speech in and the other did not."""
    if not all_missing_panels:
        return

    by_page: dict[tuple[int, str], list[MissingPanel]] = defaultdict(list)
    for entry in all_missing_panels:
        by_page[(entry.volume, entry.fanta_page)].append(entry)

    print()
    print(f"Panels seen by only one engine — {len(all_missing_panels)}:")
    for volume, fanta_page in sorted(by_page):
        parts = [
            f"panel {m.panel_num} (none in {m.missing_in})"
            for m in sorted(by_page[(volume, fanta_page)], key=lambda m: m.panel_num)
        ]
        print(f"  Vol {volume:>2}  page {fanta_page}: {', '.join(parts)}")


POINT_COORDS = 2


def _box_wh(text_box: PointList) -> tuple[int, int]:
    """Return (width, height) in pixels from the text_box's min rotated rect."""
    x0, y0, x1, y1 = points_bbox(OcrBox(text_box, "", 0, "").min_rotated_rectangle)
    return int(x1 - x0), int(y1 - y0)


def _rotated_frame_wh(group: dict) -> tuple[int, int] | None:
    """(width, height) of the lettering in its own rotated frame, or None.

    The group's ``text_box`` is always axis-aligned, so for angled lettering
    it is inflated in both dimensions and the fit check derives a font size
    far larger than the art's — 'HOORAY!' on a slant reads as a 112px-tall
    single line. The OCR engines' fragment quads in ``cleaned_box_texts`` do
    follow the angle; when their median baseline angle is past the axis
    threshold, measure the text in that frame instead: rotate every fragment
    corner back by the angle and take the bounding box.

    Returns None when the group has no usable fragments or its lettering is
    not measurably angled — the axis-aligned box is then the right measure.
    """
    fragments = group.get("cleaned_box_texts") or {}
    angles: list[float] = []
    points: list[tuple[float, float]] = []
    for frag in fragments.values():
        quad = frag.get("text_box") or []
        if text_box_problem(quad) is not None:
            return None
        p0, p1, _p2, p3 = quad
        side_a = (p1[0] - p0[0], p1[1] - p0[1])
        side_b = (p3[0] - p0[0], p3[1] - p0[1])
        long_side = side_a if math.hypot(*side_a) >= math.hypot(*side_b) else side_b
        if math.hypot(*long_side) <= 0:
            return None
        angle = math.degrees(math.atan2(long_side[1], long_side[0]))
        # A baseline and its reverse are the same line: fold into (-90, 90].
        if angle <= -90:  # noqa: PLR2004
            angle += 180
        elif angle > 90:  # noqa: PLR2004
            angle -= 180
        angles.append(angle)
        points.extend(quad)

    if not angles:
        return None
    frame_angle = _circular_median_deg(angles)
    if abs(frame_angle) < FRAGMENT_ANGLE_THRESHOLD_DEG:
        return None

    rad = math.radians(-frame_angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    xs = [p[0] * cos_a - p[1] * sin_a for p in points]
    ys = [p[0] * sin_a + p[1] * cos_a for p in points]
    return int(max(xs) - min(xs)), int(max(ys) - min(ys))


def _circular_median_deg(angles: list[float]) -> float:
    """Return the most central of a set of baseline angles folded into (-90, 90].

    A plain ``median`` cannot serve here. Vertically set lettering puts its
    fragments at about +89 and -89 degrees, which is 2 degrees apart on the page
    and 178 apart on the number line, so the median lands near 0 — under
    ``FRAGMENT_ANGLE_THRESHOLD_DEG``, and the vertical sound effect that the
    rotated frame exists for loses its rescue. Measuring the spread as an angle
    rather than a difference fixes that, and taking the most central *observed*
    angle keeps the median's resistance to one stray fragment.

    Args:
        angles: Baseline angles in degrees, each already folded into (-90, 90].

    Returns:
        The angle from ``angles`` closest to all the others.

    """

    def separation(left: float, right: float) -> float:
        # A baseline and its reverse are the same line, so the two angles are
        # never more than 90 degrees apart however far apart they are written.
        gap = abs(left - right) % 180.0
        return min(gap, 180.0 - gap)

    return min(angles, key=lambda candidate: sum(separation(candidate, a) for a in angles))


def _text_fits_in_box(
    ai_text: str,
    text_box: PointList,
    fanta_page: str = "",
    *,
    strict: bool = True,
    width_tolerance: float = FIT_WIDTH_TOLERANCE,
) -> bool:
    """Render ai_text at a box-calibrated font size; check it fits text_box width.

    See ``_text_fits_in_wh`` — this just supplies the box's axis-aligned
    dimensions and short-circuits the unmeasurable cases.
    """
    if not ai_text.strip() or text_box_problem(text_box) is not None:
        return True
    return _text_fits_in_wh(
        ai_text, _box_wh(text_box), fanta_page, strict=strict, width_tolerance=width_tolerance
    )


def _text_fits_in_wh(  # noqa: C901
    ai_text: str,
    box_wh: tuple[int, int],
    fanta_page: str = "",
    *,
    strict: bool = True,
    width_tolerance: float = FIT_WIDTH_TOLERANCE,
) -> bool:
    """Render ai_text at a size calibrated to the given dimensions; check the width.

    Derives the font size from the box height divided by the number of lines so
    that fewer lines means a larger font — which is exactly the Gemini failure
    mode (multiple lines collapsed into one). The widest rendered line must fit
    within box width * FIT_WIDTH_TOLERANCE.

    When ``strict`` is False the check is run twice — once in each orientation
    (swapping w and h) — and the text is considered to fit if either passes.
    This avoids false positives for groups whose text may be rotated (e.g.
    sound effects), since ``text_box`` itself is always axis-aligned and
    carries no rotation information.
    """
    box_w, box_h = box_wh
    if box_w <= 0 or box_h <= 0:
        return True

    lines = ai_text.split("\n")
    n_lines = max(1, len(lines))

    def _fits_one_orientation(w: int, h: int) -> tuple[bool, str]:
        """Return (fits, debug_msg). Font derives from h; widest line compared to w."""
        font_size = max(FIT_MIN_FONT_SIZE, int(h / n_lines * FIT_HEIGHT_FRACTION))
        try:
            font = ImageFont.truetype(str(FIT_FONT_PATH), font_size)
        except OSError:
            if not _FIT_FONT_MISSING_WARNED[0]:
                logger.warning(f'Fit-check font not found: "{FIT_FONT_PATH}". Skipping fit checks.')
                _FIT_FONT_MISSING_WARNED[0] = True
            return True, ""

        max_line_w = 0
        widest_line = ""
        for line in lines:
            if not line:
                continue
            left, _top, right, _bottom = _FIT_MEASURE_DRAW.textbbox((0, 0), line, font=font)
            line_w = right - left
            if line_w > max_line_w:
                max_line_w = line_w
                widest_line = line

        allowed_w = w * width_tolerance
        msg = (
            f"w={w}px h={h}px n_lines={n_lines} font_size={font_size}"
            f" widest_line_w={max_line_w}px allowed={allowed_w:.1f}px"
            f" (tolerance={width_tolerance}) widest_line={widest_line!r}"
        )
        return max_line_w <= allowed_w, msg

    page_prefix = f"page={fanta_page}: " if fanta_page else ""

    ok_h, msg_h = _fits_one_orientation(box_w, box_h)
    if ok_h:
        return True
    if strict:
        logger.debug(f"{page_prefix}Text does not fit (strict): {msg_h}")
        return False

    ok_v, msg_v = _fits_one_orientation(box_h, box_w)
    if ok_v:
        return True

    logger.debug(
        f"{page_prefix}Text does not fit (lenient, neither orientation):"
        f" horizontal=[{msg_h}] vertical=[{msg_v}]"
    )
    return False


def _plain(group: dict) -> str:
    """Return the group's ai_text with emphasis markup removed and outer space trimmed.

    Every measurement in this module -- width fit, line height, the cross-engine
    similarity ratio -- is about the lettering, so all of them read through here.
    Measuring the marked-up string instead would count ``[b]`` as six characters
    of text and report boxes as overfull that are not.
    """
    return strip_markup(group.get("ai_text") or "").strip()


def _is_stylized(group: dict) -> bool:
    """Whether the group's lettering is stylized, so its metrics are unreliable."""
    return (group.get("type") or "").strip().lower() in STYLIZED_TYPES


def _fit_params(group: dict) -> tuple[bool, float]:
    """Return the (strict, width_tolerance) fit parameters for a group.

    Keyed off the group's ``type``: only unknown types get the strict
    single-orientation check; the stylized types also get a wider tolerance.
    """
    group_type = (group.get("type") or "").strip().lower()
    stylized_types = STYLIZED_TYPES
    # Thought balloons are lettered exactly like dialogue, so they get the
    # same lenient treatment; only unknown types keep the strict check.
    strict = group_type not in ("dialogue", "narration", "thought", *stylized_types)
    width_tolerance = (
        FIT_WIDTH_TOLERANCE_SFX if group_type in stylized_types else FIT_WIDTH_TOLERANCE
    )
    return strict, width_tolerance


def _group_text_fits(group: dict, fanta_page: str = "") -> bool:
    """Return whether the group's own ai_text fits its own text_box.

    Angled lettering gets a second chance in its own rotated frame — the
    axis-aligned box overstates both dimensions there, so the axis check
    over-flags. The rotated frame is consulted only after the axis check
    fails: it can clear a false flag but never create a new one. Measured
    on vols 1-19: 23 of 37 angled text_does_not_fit flags clear; the rest
    genuinely overflow.
    """
    strict, width_tolerance = _fit_params(group)
    ai_text = _plain(group)
    if _text_fits_in_box(
        ai_text,
        group.get("text_box") or [],
        fanta_page,
        strict=strict,
        width_tolerance=width_tolerance,
    ):
        return True

    rotated_wh = _rotated_frame_wh(group)
    if rotated_wh is None:
        return False
    return _text_fits_in_wh(
        ai_text, rotated_wh, fanta_page, strict=strict, width_tolerance=width_tolerance
    )


def _implied_line_height(group: dict) -> float | None:
    """Box height per text line, or None when the group cannot be measured.

    Stylized groups are excluded: their lettering size is deliberately unlike
    the surrounding dialogue, so they are neither judged nor used as evidence.

    Single-line groups are excluded for a separate reason. ``box_h / n_lines``
    is not the line height — it is the line height plus the balloon's vertical
    padding divided by the line count. A one-line box charges the whole padding
    to its only line, so it measures about 19% high corpus-wide (median ratio
    to the page median: 1.19 at one line against 1.00 at three). Left in, they
    inflate the median and push correctly wrapped multi-line groups under the
    threshold. They are not worth judging either: one line cannot be too many.
    """
    ai_text = _plain(group)
    text_box = group.get("text_box") or []
    if not ai_text or _is_stylized(group) or text_box_problem(text_box) is not None:
        return None

    n_lines = len(ai_text.split("\n"))
    if n_lines < MIN_LINES_FOR_LINE_HEIGHT:
        return None

    _box_w, box_h = _box_wh(text_box)
    if box_h <= 0:
        return None

    return box_h / n_lines


def _half_sample_mode(values: list[float]) -> float:
    """Return the centre of the densest cluster in *values*.

    Repeatedly keeps the half of the sorted sample with the smallest range, so
    it converges on the tightest concentration of values rather than on the
    middle of the list. Unlike the median it is not moved by *how many* values
    lie in the other cluster, only by how tightly they sit -- which is what
    makes it survive a page where the contaminating register is the majority.
    """
    ordered = sorted(values)
    while len(ordered) > _MODE_SMALLEST_SAMPLE:
        half = (len(ordered) + 1) // 2
        widths = [(ordered[i + half - 1] - ordered[i], i) for i in range(len(ordered) - half + 1)]
        _width, start = min(widths)
        ordered = ordered[start : start + half]
    return mean(ordered)


def _page_median_line_height(
    json_groups: dict, bimodal_ratio: float = LINE_HEIGHT_BIMODAL_RATIO
) -> float | None:
    """Return the page's reference line height, or None if too few groups to judge.

    Normally the plain median of the page's implied line heights: body
    lettering is very consistent within a page, so the correctly boxed groups
    cluster tightly and the median lands among them.

    Some pages carry two registers, though, and then the median measures the
    wrong one. Vol 3 page 257 is the clearest case -- the carol relayed through
    the loudspeakers is free-lettered at 69-127px against ordinary dialogue at
    41px, and **seven of its twelve measurable groups are the carol**, so the
    median lands at 70.75 and every correctly wrapped dialogue balloon on the
    page is flagged while the actual outliers pass. The same inversion arrives
    by a second route on the uncleaned volumes, where a majority of loosely
    drawn boxes lifts the median off the true lettering (vol 26 page 161 and
    others). Rejecting outliers would not help: the median is already inside
    the contaminating mode, so there is nothing for it to anchor on.

    So the page is checked for that shape and, when it has it, the median of
    the densest cluster is used instead. The test is deliberately one-sided --
    only a median sitting *above* the mode is replaced -- which mirrors the
    one-directionality of the check it feeds: ``_is_line_height_outlier`` fires
    only below the reference, so only an inflated reference creates false
    flags. Measured over all 10,190 corpus pages, that is not a nicety but the
    whole safety argument: 63 pages would gain a flag if the mode were
    substituted unconditionally, and **every one of them has the mode above the
    median**, so the ratio gate excludes the lot. Of the pages it does catch,
    26 trip the gate (0.26%) and their flags fall from 101 to 4.
    """
    heights = [h for g in json_groups.values() if (h := _implied_line_height(g)) is not None]
    if len(heights) < MIN_GROUPS_FOR_LINE_HEIGHT:
        return None

    page_median = median(heights)
    mode = _half_sample_mode(heights)
    if mode > 0 and (page_median / mode) > bimodal_ratio:
        return mode
    return page_median


def _line_height_ratio(group: dict, page_median: float | None) -> float | None:
    """Return the group's implied line height as a fraction of its page's median.

    This is the inverse of the fit check. ``_text_fits_in_box`` derives the font
    size from box height / line count, so surplus line breaks shrink the font
    and always pass — only too *few* lines can ever fail it. A group whose
    implied line height sits well below the rest of the page is the signature of
    a spurious line break, and how far below is how confident that reading is.

    Returns None when the group cannot be judged: single-line and stylized
    groups, and pages with too few groups to hold a trustworthy median.
    """
    if page_median is None or page_median <= 0:
        return None

    line_height = _implied_line_height(group)
    if line_height is None:
        return None

    return line_height / page_median


def _is_line_height_outlier(
    group: dict, page_median: float | None, fraction: float = LINE_HEIGHT_OUTLIER_FRACTION
) -> bool:
    """Whether the group's lines are packed far tighter than the page norm."""
    ratio = _line_height_ratio(group, page_median)
    return ratio is not None and ratio < fraction


def _layout_ok(
    group: dict,
    fanta_page: str,
    page_median: float | None,
    fraction: float = LINE_HEIGHT_OUTLIER_FRACTION,
) -> bool:
    """Whether a group's text both fits its box and is wrapped like the page norm."""
    return _group_text_fits(group, fanta_page) and not _is_line_height_outlier(
        group, page_median, fraction
    )


def _apply_line_pattern(source_text: str, pattern_text: str) -> str:
    """Re-wrap source_text so each line holds the same word count as pattern_text.

    Duplicated from EditorApp._apply_line_pattern in kivy_editor.py — inlined
    here to avoid importing Kivy just for a 15-line text helper.
    """
    pattern_lines = pattern_text.rstrip("\n").split("\n")
    line_counts = [len(ln.split()) for ln in pattern_lines]

    words = source_text.split()
    if not words:
        return ""

    out: list[str] = []
    i = 0
    last_idx = len(line_counts) - 1
    for idx, count in enumerate(line_counts):
        if idx == last_idx:
            # Only if there are words left for it. A donor with more lines than
            # the source has words would otherwise end the result in "\n", and
            # that empty line drags the group's implied line height down —
            # inflating n_lines for every later measurement, until a
            # --fix-whitespace pass strips it again and the file flip-flops.
            if i < len(words):
                out.append(" ".join(words[i:]))
            break
        if i >= len(words):
            break
        out.append(" ".join(words[i : i + count]))
        i += count
    return "\n".join(out)


def _find_matching_group(
    group: dict,
    other_page_group: SpeechPageGroup | None,
    min_ratio: float = MIN_MATCH_RATIO,
) -> dict | None:
    """Best-matching group in the other engine, restricted to same panel_num.

    Returns the other engine's json_group dict, or None if no candidate clears
    min_ratio. Pairs by best similarity ratio, unlike the positional pairing
    in ``_check_engine_agreement`` — a transplant donor has to be the right
    text, not just the text in the right position.
    """
    if other_page_group is None:
        return None

    panel_num = int(group.get("panel_num", -1))
    ai_text = _plain(group)
    if not ai_text:
        return None

    other_groups = other_page_group.speech_page_json.get("groups", {})

    best_ratio = 0.0
    best_group: dict | None = None
    for other in other_groups.values():
        if int(other.get("panel_num", -1)) != panel_num:
            continue
        other_text = _plain(other)
        if not other_text:
            continue
        ratio = SequenceMatcher(None, ai_text, other_text).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_group = other

    return best_group if best_ratio >= min_ratio else None


def _other_ocr_type(ocr_type: OcrTypes) -> OcrTypes:
    return OcrTypes.PADDLEOCR if ocr_type == OcrTypes.EASYOCR else OcrTypes.EASYOCR


def _reading_order_key(group: dict) -> tuple[float, float, float]:
    """Return ``_group_sort_key``'s position for a group, tolerating a bad box.

    ``_group_sort_key`` raises on a text_box it cannot read. That box is
    reported as ``bad_text_box`` in its own right, so park the group at the end
    of the page rather than letting it abort the comparison.

    Args:
        group: One group's JSON dict.

    Returns:
        (panel, banded y, x), sorting an unreadable box last.

    """
    if text_box_problem(group.get("text_box")) is not None:
        return math.inf, math.inf, math.inf
    return _group_sort_key(group)


def _groups_by_panel(json_groups: dict) -> dict[int, list[tuple[str, dict]]]:
    """Group ``(group_id, group)`` by panel_num, in reading order within a panel.

    The group dict rather than just its text, because the cross-engine checks
    compare the box and the attributes too; the text comes back out via
    ``_plain``.

    Read from the live JSON rather than ``SpeechPageGroup.speech_groups``, which
    is built at load time and would not see fixes applied earlier in this pass.

    Ordered spatially — the same key ``renumber_groups()`` numbers by — and not
    by group id. The ids are only in reading order once a renumber has run, and
    that runs only under ``--fix-groups-order``, which the documented roll-call
    invocation does not pass. ``_check_engine_agreement`` pairs these lists
    positionally, so trusting stale ids there offsets every pair in a panel and
    reports a ``text_mismatch`` on each — naming nothing that would let the
    reviewer see the real fault. Groups whose ids *are* stale are reported
    separately, as ``groups_out_of_order``.
    """
    by_panel: dict[int, list[tuple[str, dict]]] = defaultdict(list)
    for group_id, group in sorted(json_groups.items(), key=lambda kv: _reading_order_key(kv[1])):
        if _plain(group):
            by_panel[int(group.get("panel_num", -1))].append((group_id, group))
    return by_panel


def _out_of_order_group(json_groups: dict) -> tuple[str, str] | None:
    """Return the first group id a renumber would move, with what is wrong.

    Mirrors ``renumber_groups()``'s own "did anything change" test without
    writing: ids must run 0..n-1, and that order must be the page's reading
    order. ``sorted`` is stable, so two groups with identical positions are not
    reported as a swap.

    Args:
        json_groups: One page/engine's groups, in the order they are stored.

    Returns:
        (group id, what is wrong with it), or None when the numbering is sound.

    """
    items = list(json_groups.items())
    if not items:
        return None
    if any(text_box_problem(group.get("text_box")) is not None for _gid, group in items):
        # `renumber_groups()` raises on such a box, so `_check_page_group` skips
        # the page rather than strand a title half-written. Reporting an order
        # the fixer will not repair would only queue an entry nobody can act on;
        # the box itself is reported as `bad_text_box`.
        return None

    in_reading_order = sorted(items, key=lambda kv: _reading_order_key(kv[1]))
    for position, ((group_id, _group), (wanted_id, _wanted)) in enumerate(
        zip(items, in_reading_order, strict=True)
    ):
        if group_id != str(position):
            return group_id, f"group ids are not 0..{len(items) - 1} in order"
        if group_id != wanted_id:
            return group_id, f"reading order puts group {wanted_id} here"
    return None


def _panel_num_gap(
    json_groups: dict, page_panel_boxes: PagePanelBoxes
) -> tuple[str, list[int]] | None:
    """Return the first group after a hole in the page's panel numbering.

    The groups on a page should occupy panels 1..n with nothing skipped. A
    skipped panel is either a panel whose lettering was never grouped, or a run
    of groups filed under the wrong panel — neither of which any other check
    sees. ``panel_num_mismatch`` needs the box to sit wholly inside a different
    *real* panel, and the cross-engine ``MissingPanel`` only fires when the two
    engines disagree; a page where both engines skip the same panel is silent
    today.

    Bounded above by the highest panel that *has* text, not by the page's panel
    count: a story that ends on a wordless panel is ordinary Barks and is not a
    fault. Only an interior hole is reported.

    Two suppressions, both to keep the entry pointing at something a reviewer
    can act on:

    - A panel_num beyond the page's panel count is ignored when taking the
      maximum, so one group claiming panel 99 does not invent 90-odd missing
      panels. The claim itself is reported as ``panel_num_out_of_range``.
    - A page holding any unassigned (-1) group is skipped entirely. That group's
      text may well belong to the empty panel, so the gap is a restatement of
      ``panel_unassigned``/``panel_num_fixable`` and resolves itself once those
      are worked. This is 34 of the 454 page/engine gaps in the corpus.

    Args:
        json_groups: One page/engine's groups, as stored.
        page_panel_boxes: The page's panel boxes, for the upper bound.

    Returns:
        (anchor group id, the missing panel numbers), or None when the
        numbering has no hole. The anchor is the first group, in reading order,
        of the panel that follows the first hole.

    """
    gap = panels_with_no_groups(json_groups, len(page_panel_boxes.panel_boxes))
    if not gap:
        return None

    texted = [(group_id, group) for group_id, group in json_groups.items() if _plain(group)]
    next_panel = min(
        panel
        for panel in (int(group.get("panel_num", -1)) for _gid, group in texted)
        if panel > gap[0] and panel not in gap
    )
    anchor_id, _anchor = min(
        (item for item in texted if int(item[1].get("panel_num", -1)) == next_panel),
        key=lambda item: _reading_order_key(item[1]),
    )
    return anchor_id, gap


def _get_reduced_text_box(text_box: PointList, reduce_by: int) -> tuple[bool, PointList | None]:
    p0_x = text_box[0][0] + reduce_by
    p0_y = text_box[0][1] + reduce_by
    p1_x = text_box[1][0] - reduce_by
    p1_y = text_box[1][1] + reduce_by
    p2_x = text_box[2][0] - reduce_by
    p2_y = text_box[2][1] - reduce_by
    p3_x = text_box[3][0] + reduce_by
    p3_y = text_box[3][1] - reduce_by

    if p1_x <= p0_x or p2_y <= p0_y:
        return False, None

    return True, [(p0_x, p0_y), (p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)]


def _get_enclosing_panel_num(box: PointList, page_panel_boxes: PagePanelBoxes) -> int:
    x0, y0, x1, y1 = points_bbox(OcrBox(box, "", 0, "").min_rotated_rectangle)
    box_rect = Rect(x0, y0, x1 - x0, y1 - y0)

    for i, panel_box in enumerate(page_panel_boxes.panel_boxes):
        panel_rect = Rect(panel_box.x0, panel_box.y0, panel_box.w, panel_box.h)
        if panel_rect.is_rect_inside_rect(box_rect):
            return i + 1

    return -1


def _is_in_wrong_panel(group: dict, page_panel_boxes: PagePanelBoxes) -> bool:
    """Whether the text_box sits wholly inside a panel other than the one claimed.

    Deliberately narrow. A box that is inside *no* panel proves nothing — speech
    balloons routinely overhang the gutter, and 5.9% of groups do — so only a box
    that lands squarely in a different panel counts. That is rare (~0.2%) and
    is a genuine mis-assignment every time.
    """
    panel_num = int(group.get("panel_num", -1))
    text_box = group.get("text_box") or []
    if panel_num == -1 or not text_box:
        return False

    enclosing = _get_enclosing_panel_num(text_box, page_panel_boxes)
    return enclosing not in (-1, panel_num)


class PanelNumState(Enum):
    PANEL_NUM_SET = auto()
    PANEL_NUM_NOT_SET_FIXABLE = auto()
    PANEL_NUM_NOT_SET_UNFIXABLE = auto()


def _prelim_backup_file(ocr_file: Path) -> Path:
    """Timestamped backup path for a prelim file, mirrored under the backup root."""
    return Path(
        str(get_backup_file(ocr_file)).replace(str(OCR_PRELIM_DIR), str(OCR_PRELIM_BACKUP_DIR))
    )


# ── Checker ───────────────────────────────────────────────────────────────────


class OcrChecker:
    """Checks prelim OCR JSON files for issues and writes a kivy-editor queue file."""

    def __init__(
        self,
        comics_database: ComicsDatabase,
        fixes: FixFlags | None = None,
        line_height_limits: LineHeightLimits | None = None,
        box_iou_min: float = BOX_IOU_MIN,
    ) -> None:
        self._comics_database = comics_database
        self._fixes = fixes or FixFlags()
        self._limits = line_height_limits or LineHeightLimits()
        self._box_iou_min = box_iou_min
        self._speech_groups = SpeechGroups(comics_database)
        self._title_panel_boxes = TitlePanelBoxes(self._comics_database)

    # ── Public API ────────────────────────────────────────────────────────────

    def check_titles(
        self,
        title_list: list[str],
        output_file: Path,
    ) -> None:
        """Check all pages of each title; print issues and write a queue file."""
        # Before anything reads a group: a malformed file makes the loader raise,
        # which used to end the whole run on a traceback naming one file. Every
        # other page in the volume went unchecked, and a second bad file was not
        # even reported. This finds them all first and says so plainly.
        if unreadable := self._unreadable_prelims(title_list):
            self._print_unreadable_prelims(unreadable)
            raise typer.Exit(code=1)

        all_issues: list[IssueFound] = []
        all_missing: list[MissingPrelim] = []
        all_missing_panels: list[MissingPanel] = []
        all_agreement: list[TitleAgreement] = []

        for title_str in title_list:
            print("-" * 80)
            title = STR_TITLE_TO_ENUM[title_str]
            volume = self._comics_database.get_fanta_volume_int(title_str)
            page_groups = self._speech_groups.get_speech_page_groups(title, skip_missing=True)

            missing_by_page: dict[str, set[str]] = defaultdict(set)
            for m in self._speech_groups.get_missing_prelim_pages(title):
                missing_by_page[m.fanta_page].add(str(m.ocr_index))
            if missing_by_page:
                all_missing.append(_build_missing_prelim(volume, title_str, missing_by_page))

            pages: dict[str, dict[OcrTypes, SpeechPageGroup]] = defaultdict(dict)
            for pg in page_groups:
                pages[pg.fanta_page][pg.ocr_index] = pg

            if not pages:
                # Nothing of this title's own to check. The synthetic "All
                # One-Pagers" collection is the case: all 133 of its pages are
                # reprints, OCR'd in the volume they came from, so the page map
                # is empty by design. Asking for its panel boxes would load
                # geometry for pages that deliberately have no segments file --
                # the one-pagers are in no title, so nothing ever segmented
                # them. Missing prelims are still reported above.
                print(f'  No pages to check in "{title_str}" (Vol. {volume}).')
                continue

            page_panel_boxes = self._title_panel_boxes.get_page_panel_boxes(title)

            title_issues, missing_panels, agreement, passes = self._check_title_to_convergence(
                title_str, pages, page_panel_boxes
            )
            if passes > 1:
                logger.info(f'"{title_str}": converged after {passes} passes.')

            if title_issues:
                print(f'Issues in "{title_str}" (Vol. {volume}):')
                for issue in title_issues:
                    self._print_issue(issue)
            else:
                print(f'  No issues in "{title_str}" (Vol. {volume}).')

            all_issues.extend(title_issues)
            all_missing_panels.extend(missing_panels)
            all_agreement.append(agreement.with_title(volume, title_str))

        self._print_issues_summary(all_issues)
        _print_engine_agreement(all_agreement)
        _print_missing_panels(all_missing_panels)
        self._print_missing_prelims(all_missing)
        self._write_queue_file(all_issues, output_file)

    # ── Per-title passes ──────────────────────────────────────────────────────

    def _check_title_to_convergence(
        self,
        title_str: str,
        pages: dict[str, dict[OcrTypes, SpeechPageGroup]],
        page_panel_boxes: TitlePagesPanelBoxes,
    ) -> tuple[list[IssueFound], list[MissingPanel], TitleAgreement, int]:
        """Re-run the check pass until one applies no fixes.

        Returns (issues, missing_panels, agreement, passes).

        A fix can supply exactly the donor another group was waiting on — pages
        are checked and saved in order, so a group never sees a donor repaired
        later in the same pass. Repeating until nothing changes lets those
        knock-on fixes land in one invocation. Only the final pass's issues are
        returned; earlier passes list issues that were then fixed.
        """
        result = self._check_title_pages(pages, page_panel_boxes)
        passes = 1
        while result[-1] and passes < MAX_FIX_PASSES:
            passes += 1
            result = self._check_title_pages(pages, page_panel_boxes)

        title_issues, missing_panels, agreement, there_were_fixes = result
        if there_were_fixes:
            logger.warning(
                f'"{title_str}": still applying fixes after {MAX_FIX_PASSES} passes.'
                f" Giving up — re-run to continue."
            )

        return title_issues, missing_panels, agreement, passes

    def _check_title_pages(
        self,
        pages: dict[str, dict[OcrTypes, SpeechPageGroup]],
        page_panel_boxes: TitlePagesPanelBoxes,
    ) -> tuple[list[IssueFound], list[MissingPanel], TitleAgreement, bool]:
        """One full pass over a title's pages.

        Returns (issues, missing_panels, agreement, any_fixes_applied).
        """
        issues: list[IssueFound] = []
        missing_panels: list[MissingPanel] = []
        agreed = 0
        any_fixes = False

        for fanta_page in sorted(pages):
            variants = pages[fanta_page]
            for ocr_index, page_group in variants.items():
                other = variants.get(_other_ocr_type(ocr_index))
                page_issues, there_were_fixes = self._check_page_group(
                    page_group, page_panel_boxes, other
                )
                issues.extend(page_issues)
                if there_were_fixes:
                    any_fixes = True

            # Once per page, after both engines have had their fixes applied.
            pair_issues, pair_missing, agree = self._check_engine_agreement(variants)
            issues.extend(pair_issues)
            missing_panels.extend(pair_missing)
            agreed += agree

        return issues, missing_panels, TitleAgreement(agreed, len(pages)), any_fixes

    # ── Per-page / per-group checks ───────────────────────────────────────────

    def _check_page_group(
        self,
        page_group: SpeechPageGroup,
        page_panel_boxes: TitlePagesPanelBoxes,
        other_page_group: SpeechPageGroup | None = None,
    ) -> tuple[list[IssueFound], bool]:
        """Check one page/engine, applying any enabled fixes.

        Returns (issues, there_were_fixes).
        """
        panel_boxes = page_panel_boxes.pages.get(page_group.fanta_page)
        if panel_boxes is None:
            logger.error(
                f"No panel boxes for vol {page_group.fanta_vol}"
                f" page {page_group.fanta_page} ({page_group.ocr_index}) — page skipped."
            )
            return [], False

        issues: list[IssueFound] = []
        there_were_fixes = False

        if self._fixes.groups_order:
            groups_before = page_group.speech_page_json.get("groups", {})
            bad_boxes = [
                gid for gid, g in groups_before.items() if text_box_problem(g.get("text_box"))
            ]
            if bad_boxes:
                # renumber_groups() raises on a malformed text_box, and an
                # abort here would strand the title half-written. The bad box
                # itself is reported as an issue below.
                logger.warning(
                    f"Page {page_group.fanta_page} ({page_group.ocr_index}): bad text_box in"
                    f" group(s) {', '.join(bad_boxes)} — skipping group renumbering."
                )
            elif page_group.renumber_groups():
                there_were_fixes = True

        # Read the groups only after any renumbering: renumber_groups() rebinds
        # speech_page_json["groups"] to a freshly keyed dict, and the checks must
        # report the new group ids or the queue file would point at the old ones.
        json_groups = page_group.speech_page_json.get("groups", {})

        context = PageContext.build(
            page_group,
            panel_boxes=panel_boxes,
            line_heights=PageLineHeights(
                own=_page_median_line_height(json_groups, self._limits.bimodal_ratio),
                other=_page_median_line_height(
                    other_page_group.speech_page_json.get("groups", {})
                    if other_page_group is not None
                    else {},
                    self._limits.bimodal_ratio,
                ),
            ),
            other_page_group=other_page_group,
        )

        issues.extend(self._order_issue(context, json_groups))
        issues.extend(self._panel_gap_issue(context, json_groups))

        for group_id, group in json_groups.items():
            group_issues, there_were_group_fixes = self._check_group(context, group_id, group)
            issues.extend(group_issues)
            if there_were_group_fixes:
                there_were_fixes = True

        if self._apply_text_fixes(json_groups):
            there_were_fixes = True

        if there_were_fixes:
            page_group.save_json(
                backup_file=_prelim_backup_file(page_group.ocr_prelim_groups_json_file)
            )

        return issues, there_were_fixes

    @staticmethod
    def _order_issue(context: PageContext, json_groups: dict) -> list[IssueFound]:
        """Report a page whose group ids are not in reading order.

        One entry per page/engine, on the first group that is out of place.
        Nothing else here would say so: ``--fix-groups-order`` silently repairs
        it when it is passed, and the checks say nothing at all when it is not,
        while the cross-engine comparison quietly depends on the ordering being
        right.

        Args:
            context: The page being checked.
            json_groups: That page/engine's groups, as stored.

        Returns:
            One ``groups_out_of_order`` issue, or an empty list.

        """
        out_of_order = _out_of_order_group(json_groups)
        if out_of_order is None:
            return []

        group_id, problem = out_of_order
        group = json_groups[group_id]
        notes = (group.get("notes") or "").strip()
        note = f"{problem}; re-run with --fix-groups-order"
        return [
            IssueFound(
                volume=context.volume,
                fanta_page=context.fanta_page,
                engine=context.engine,
                group_id=group_id,
                issue_type="groups_out_of_order",
                panel_num=int(group.get("panel_num", -1)),
                text=_plain(group),
                notes=f"{notes}; {note}" if notes else note,
            )
        ]

    @staticmethod
    def _panel_gap_issue(context: PageContext, json_groups: dict) -> list[IssueFound]:
        """Report a page that skips a panel number.

        One entry per page/engine. The finding is about a panel that holds *no*
        group, so there is nothing in it to anchor to; the entry is anchored on
        the first group of the next panel that does have one, since that is the
        nearest thing an editor can open.

        That split is the whole difficulty in reading one of these, so both
        halves are spelled out. ``panel_num`` is the **empty** panel, not the
        anchor group's own — on every other issue those are the same panel, and
        printing the anchor's made the line name a group in panel 4 while
        complaining about panel 3, with nothing saying why. The note then says
        which panel the anchor group is actually in, so the two numbers on the
        line are never silently different.

        Silenced per page/engine by ``PANEL_HAS_NO_TEXT_ISSUE`` on the anchor
        group — the reviewer's "that panel really is wordless". Deliberately not
        the queue entry's own name, so the editor does not pre-tick it and a
        reflexive Save cannot dismiss the finding unlooked-at.

        Args:
            context: The page being checked.
            json_groups: That page/engine's groups, as stored.

        Returns:
            One ``panel_nums_not_contiguous`` issue, or an empty list.

        """
        gap = _panel_num_gap(json_groups, context.panel_boxes)
        if gap is None:
            return []

        group_id, missing_panels = gap
        group = json_groups[group_id]
        if is_acknowledged(group, PANEL_HAS_NO_TEXT_ISSUE):
            # Read off the anchor because that is where the editor's "Mark OK"
            # popup can put it -- the skipped panel has no group of its own.
            # So the acknowledgement only holds while the anchor stays the
            # anchor; edit the page and it re-fires, which is the safe way round.
            return []

        notes = (group.get("notes") or "").strip()
        anchor_panel = int(group.get("panel_num", -1))
        many = len(missing_panels) > 1
        panels_str = ", ".join(str(panel) for panel in missing_panels)
        note = (
            f"panel{'s' if many else ''} {panels_str} hold{'' if many else 's'} no group"
            f" — this group is the first of panel {anchor_panel}"
        )
        return [
            IssueFound(
                volume=context.volume,
                fanta_page=context.fanta_page,
                engine=context.engine,
                group_id=group_id,
                issue_type="panel_nums_not_contiguous",
                panel_num=missing_panels[0],
                text=_plain(group),
                notes=f"{notes}; {note}" if notes else note,
            )
        ]

    def _check_group(
        self,
        context: PageContext,
        group_id: str,
        group: dict,
    ) -> tuple[list[IssueFound], bool]:
        """Run every group-level check. Returns (issues, there_were_fixes)."""
        ai_text = _plain(group)
        box_problem = text_box_problem(group.get("text_box"))

        panel_num_state: PanelNumState | None = None
        panel_num = int(group.get("panel_num", -1))
        if box_problem is None:
            panel_num_state, panel_num = self._get_panel_num_state(group, context.panel_boxes)

        issues: list[IssueFound] = []
        there_were_fixes = False

        def add(issue_type: str, ratio: float | None = None, extra_note: str = "") -> None:
            notes = (group.get("notes") or "").strip()
            if extra_note:
                notes = f"{notes}; {extra_note}" if notes else extra_note
            issues.append(
                IssueFound(
                    volume=context.volume,
                    fanta_page=context.fanta_page,
                    engine=context.engine,
                    group_id=group_id,
                    issue_type=issue_type,
                    panel_num=panel_num,
                    text=ai_text,
                    notes=notes,
                    ratio=ratio,
                )
            )

        if box_problem is not None:
            # A malformed box gets no geometric checks — every one of them,
            # and the panel-num fixer, indexes its four corner points.
            add("bad_text_box", extra_note=f"text_box {box_problem}")
        elif panel_num_state == PanelNumState.PANEL_NUM_NOT_SET_FIXABLE:
            there_were_fixes = self._deal_with_fixable_panel_num(group, group_id, panel_num)
            if not there_were_fixes:
                # The fixer writes only under --fix-panel-nums; without it the
                # group keeps panel_num -1. Nothing downstream would name it:
                # `panel_unassigned` covers the unfixable case only, and
                # _groups_by_panel files -1 under a panel the cross-engine
                # checks skip. Left as it was, the groups the tool has
                # positively diagnosed were the ones it dropped from the queue.
                add("panel_num_fixable", extra_note=f"panel_num should be {panel_num}")
        elif panel_issue := self._panel_issue(group, panel_num_state, panel_num, context):
            add(panel_issue)

        if not ai_text:
            add("empty_text")
        else:
            text_issues, layout_fixed = self._text_issues(
                context, group_id, group, skip_layout=box_problem is not None
            )
            for issue_type, ratio in text_issues:
                add(issue_type, ratio)
            there_were_fixes = there_were_fixes or layout_fixed

        return issues, there_were_fixes

    def _text_issues(
        self,
        context: PageContext,
        group_id: str,
        group: dict,
        *,
        skip_layout: bool,
    ) -> tuple[list[tuple[str, float | None]], bool]:
        """Text-level issues for one group with text. Returns (issues, layout_fixed).

        The registry checks come straight off utils/group_checks.py, so adding
        a check there needs no change here. The layout check is skipped for a
        malformed text_box, whose geometry means nothing.
        """
        found: list[tuple[str, float | None]] = [
            (t, None) for t in get_fired_dismissable_issues(group) if not is_acknowledged(group, t)
        ]
        if skip_layout:
            return found, False

        layout_fixed, layout_issue, layout_ratio = self._check_text_layout(group, group_id, context)
        if layout_issue:
            found.append((layout_issue, layout_ratio))
        return found, layout_fixed

    @staticmethod
    def _panel_issue(
        group: dict,
        panel_num_state: PanelNumState | None,
        panel_num: int,
        context: PageContext,
    ) -> str | None:
        """Which panel-assignment issue applies, or None when the panel num is sound."""
        if panel_num_state == PanelNumState.PANEL_NUM_NOT_SET_UNFIXABLE:
            return "panel_unassigned"
        if not 1 <= panel_num <= len(context.panel_boxes.panel_boxes):
            # _is_in_wrong_panel cannot see this: it only fires when the box
            # sits wholly inside a different real panel.
            return "panel_num_out_of_range"
        if _is_in_wrong_panel(group, context.panel_boxes):
            return "panel_num_mismatch"
        return None

    # ── Cross-engine agreement ────────────────────────────────────────────────

    def _check_engine_agreement(
        self,
        variants: dict[OcrTypes, SpeechPageGroup],
    ) -> tuple[list[IssueFound], list[MissingPanel], bool]:
        """Compare the two engines for one page. Returns (issues, missing, agree).

        Runs **once per page**, not once per engine — the callers loop over
        engines, and doing this there would report every mismatch twice.

        Two levels of comparison, kept apart on purpose:

        - **How the page was read** — which panels hold groups, and what those
          groups say. ``only_in_easy``, ``only_in_paddle``, ``text_mismatch``.
        - **What is recorded about a group both engines read identically** —
          where its box sits (``box_mismatch``) and what its other fields say
          (``attrs_mismatch``).

        Both engines reading a page the same way is the strongest evidence the
        page is right, so ``agree`` is what the completion metric counts — and it
        counts **only the first level**. The second is reported and queued like
        any other issue but deliberately kept out of the metric: a stale
        ``speaker_reviewed_date`` is worth fixing and says nothing about whether
        the page was read correctly. Folding it in would take engine agreement
        from 70% to 24% overnight and make every historical figure incomparable.
        Do not simplify this back to ``not issues``.
        """
        easy = variants.get(OcrTypes.EASYOCR)
        paddle = variants.get(OcrTypes.PADDLEOCR)
        if easy is None or paddle is None:
            return [], [], False

        easy_panels = _groups_by_panel(easy.speech_page_json.get("groups", {}))
        paddle_panels = _groups_by_panel(paddle.speech_page_json.get("groups", {}))

        reading_issues: list[IssueFound] = []
        record_issues: list[IssueFound] = []
        missing: list[MissingPanel] = []
        volume, fanta_page = easy.fanta_vol, easy.fanta_page

        def issue(  # noqa: ANN202, PLR0913
            engine: str,
            group_id: str,
            issue_type: str,
            panel: int,
            text: str,
            ratio: float | None = None,
            notes: str = "",
        ):
            return IssueFound(
                volume=volume,
                fanta_page=fanta_page,
                engine=engine,
                group_id=group_id,
                issue_type=issue_type,
                panel_num=panel,
                text=text,
                notes=notes,
                ratio=ratio,
            )

        # panel -1 is not a panel: unassigned groups are already reported
        # per-group as panel_unassigned, and counting them here as a missing
        # panel would block the page from ever agreeing.
        for panel in sorted((set(easy_panels) | set(paddle_panels)) - {-1}):
            in_easy, in_paddle = easy_panels.get(panel, []), paddle_panels.get(panel, [])
            if not in_easy or not in_paddle:
                missing.append(
                    MissingPanel(
                        volume,
                        fanta_page,
                        panel,
                        str(OcrTypes.EASYOCR) if not in_easy else str(OcrTypes.PADDLEOCR),
                    )
                )
                continue

            for easy_item, paddle_item in zip_longest(in_easy, in_paddle):
                if easy_item is None:
                    gid, group = paddle_item
                    reading_issues.append(
                        issue(str(OcrTypes.PADDLEOCR), gid, "only_in_paddle", panel, _plain(group))
                    )
                    continue
                if paddle_item is None:
                    gid, group = easy_item
                    reading_issues.append(
                        issue(str(OcrTypes.EASYOCR), gid, "only_in_easy", panel, _plain(group))
                    )
                    continue

                easy_id, easy_group = easy_item
                paddle_id, paddle_group = paddle_item
                easy_text, paddle_text = _plain(easy_group), _plain(paddle_group)

                if easy_text != paddle_text:
                    reading_issues.append(
                        issue(
                            str(OcrTypes.EASYOCR),
                            easy_id,
                            "text_mismatch",
                            panel,
                            easy_text,
                            SequenceMatcher(None, easy_text, paddle_text).ratio(),
                        )
                    )
                    # The pair may simply be mis-paired — positional pairing does
                    # not guarantee these are the same lettering — so a box or
                    # attribute verdict on it would be measuring nothing.
                    continue

                record_issues.extend(
                    self._compare_matched_pair(
                        easy_group, paddle_group, panel, easy_id, paddle_id, issue
                    )
                )

        return (
            reading_issues + record_issues,
            missing,
            not reading_issues and not missing,
        )

    def _compare_matched_pair(  # noqa: PLR0913
        self,
        easy_group: dict,
        paddle_group: dict,
        panel: int,
        easy_id: str,
        paddle_id: str,
        issue: Callable[..., IssueFound],
    ) -> list[IssueFound]:
        """Box and attribute checks for one pair the two engines read identically.

        Reported against easyocr, as ``text_mismatch`` is, so a group's whole
        cross-engine story sits on one queue entry. The paddleocr group id goes
        in the notes because the two engines number their groups independently —
        without it, the entry names a group the reviewer cannot find in the other
        pane.
        """
        found: list[IssueFound] = []
        text = _plain(easy_group)
        other = f"paddleocr group {paddle_id}"

        iou = box_iou(easy_group.get("text_box") or [], paddle_group.get("text_box") or [])
        if iou is not None and iou < self._box_iou_min:
            found.append(
                issue(
                    str(OcrTypes.EASYOCR),
                    easy_id,
                    "box_mismatch",
                    panel,
                    text,
                    iou,
                    f"{other}; text_box IoU {iou:.2f}",
                )
            )

        if differing := differing_attrs(easy_group, paddle_group):
            found.append(
                issue(
                    str(OcrTypes.EASYOCR),
                    easy_id,
                    "attrs_mismatch",
                    panel,
                    text,
                    None,
                    f"{other}; differs on {', '.join(differing)}",
                )
            )

        return found

    def _apply_text_fixes(self, json_groups: dict) -> bool:
        """Apply the unambiguous string rewrites. Returns whether anything changed.

        Both are pure cleanups with no judgement in them — stray whitespace
        and "--" for an em-dash — which is why they can run unattended while the
        wrapping fixes need cross-engine evidence.

        A group that has acknowledged the issue a fixer exists for is left
        alone, exactly as the check leaves it alone. Otherwise the next --fix
        run would quietly undo the dismissal the user made in the editor, and
        the run after that would do it again.

        Groups carrying emphasis markup are skipped, like the line-pattern
        transplant skips them: the fixers edit the raw stored string, and
        rewriting around ``[b]``/``[i]`` tags is exactly the offset problem
        this module refuses to solve mechanically. The issue stays reported
        for a hand fix in the editor.
        """
        changed = False
        for group_id, group in json_groups.items():
            before = group.get("ai_text") or ""
            after = before
            if self._fixes.whitespace and not is_acknowledged(group, "whitespace"):
                after = cleaned_whitespace(after)
            if self._fixes.dashes:
                after = with_dash_fixes(after, group)
            if after == before:
                continue
            if has_markup(before):
                logger.warning(
                    f"Group {group_id}: ai_text needs cleanup but carries emphasis"
                    f" markup, so the text fixes were skipped."
                    f" Fix it by hand in the editor."
                )
                continue
            group["ai_text"] = after
            changed = True
            logger.info(f"Group {group_id}: cleaned up ai_text.")
        return changed

    # ── Text-layout check + optional fix ──────────────────────────────────────

    def _check_text_layout(
        self,
        group: dict,
        group_id: str,
        context: PageContext,
    ) -> tuple[bool, str | None, float | None]:
        """Return (fix_applied, issue_type_to_add, line_height_ratio).

        Two opposite wrapping failures are checked, both repaired the same way —
        by transplanting the other engine's line pattern:

        - too few lines: the text overflows its box → "text_does_not_fit".
        - too many lines: the lines are packed far tighter than the rest of the
          page, which the fit check cannot see → "too_many_lines", or
          "too_many_lines_marginal" in the noisier band just above it.

        A group acknowledging ``text-will-never-fit`` skips **both**: the
        reviewer has said the lettering cannot be made to sit in the box as
        drawn, and the two checks are that one judgement measured from opposite
        sides. Both read box height / line count — the fit check turns it into a
        font size and tests the width, the line-height check tests it against
        the page median — so a box too small in both dimensions fails the
        line-height half while *passing* the fit half on its shrunken font, and
        a narrow but tall box does the reverse. Which one fires is an accident
        of the wrapping, so silencing one half alone leaves the group reported
        by the other for the same single fault.

        The wrapping fixer is gated with it: no issue reported, so no transplant
        is attempted, and the layout the reviewer accepted is not quietly
        rewritten on the next ``--fix`` pass.

        Well-formed → (False, None, ratio). Ill-formed with no fix flag, or with
        the transplant rejected → (False, issue_type, ratio). Transplant applied
        → (True, None, ratio).
        """
        ai_text = _plain(group)
        text_box = group.get("text_box") or []
        if not ai_text or not text_box:
            return False, None, None

        ratio = _line_height_ratio(group, context.line_heights.own)

        if is_acknowledged(group, TEXT_NEVER_FITS_ISSUE):
            return False, None, ratio

        if not _group_text_fits(group, context.fanta_page):
            issue = "text_does_not_fit"
        elif ratio is not None and ratio < self._limits.outlier:
            issue = "too_many_lines"
        elif self._limits.include_marginal and ratio is not None and ratio < self._limits.marginal:
            issue = "too_many_lines_marginal"
        else:
            return False, None, ratio

        if not self._fixes.newlines:
            return False, issue, ratio

        if not self._transplant_line_pattern(group, group_id, context):
            return False, issue, ratio

        return True, None, ratio

    def _transplant_line_pattern(
        self,
        group: dict,
        group_id: str,
        context: PageContext,
    ) -> bool:
        """Rewrap group's ai_text to the other engine's line pattern, if that helps.

        Returns whether ai_text was changed. This is the non-interactive
        equivalent of the kivy editor's "Copy Fmt" button. The donor must itself
        be well laid out, and the rewrapped result must be too, or nothing is
        written.
        """
        if has_markup(group.get("ai_text") or ""):
            # Rewrapping rebuilds the string from a donor's line pattern, which
            # would have to carry the emphasis tags across to their new
            # positions -- the offset-mapping problem this whole scheme exists to
            # avoid. Refuse and say so, rather than silently dropping the bold or
            # wrapping on a character count that includes "[b]".
            logger.warning(
                f"Group {group_id}: badly wrapped text, but it carries emphasis"
                f" markup, so the line-pattern transplant was skipped."
                f" Rewrap it by hand in the editor."
            )
            return False

        ai_text = _plain(group)

        match = _find_matching_group(group, context.other_page_group)
        if match is None:
            logger.warning(
                f"Group {group_id}: badly wrapped text and no matching"
                f" group found in the other engine to transplant newlines from."
            )
            return False

        if not _layout_ok(
            match, context.fanta_page, context.line_heights.other, self._limits.outlier
        ):
            logger.warning(
                f"Group {group_id}: badly wrapped text but the matching group"
                f" in the other engine is not well laid out either,"
                f" so its line pattern is not worth transplanting."
            )
            return False

        pattern_text = _plain(match)
        new_text = _apply_line_pattern(ai_text, pattern_text)
        if new_text == ai_text:
            logger.warning(
                f"Group {group_id}: badly wrapped text but line-pattern transplant"
                f" produced no change."
            )
            return False

        # The rewrap was built from `_plain()`, which resolved `&amp;`, `&bl;`
        # and `&br;` back to `&`, `[` and `]`. Escape them again before storing:
        # ai_text on disk is Kivy markup, and the reader would act on a bare
        # bracket. `has_markup` above only sees `[b]`/`[i]`, so an escaped
        # string reaches here -- 59 corpus groups hold an ampersand and 31 hold
        # brackets. Round-trips exactly, the text carrying no tags.
        stored_text = escape_markup(new_text)

        if not _layout_ok(
            {**group, "ai_text": stored_text},
            context.fanta_page,
            context.line_heights.own,
            self._limits.outlier,
        ):
            logger.warning(
                f"Group {group_id}: line-pattern transplant did not produce a well"
                f" laid out result, so ai_text was left unchanged."
            )
            return False

        group["ai_text"] = stored_text
        logger.info(f"Group {group_id}: rewrapped ai_text using other-engine pattern.")
        return True

    # ── Predicates ────────────────────────────────────────────────────────────

    def _get_panel_num_state(
        self, group: dict, page_panel_boxes: PagePanelBoxes
    ) -> tuple[PanelNumState, int]:
        panel_num = int(group.get("panel_num", -1))
        if panel_num != -1:
            return PanelNumState.PANEL_NUM_SET, panel_num
        return self._can_replace_missing_panel_num(group, page_panel_boxes)

    def _deal_with_fixable_panel_num(self, group: dict, group_id: str, panel_num: int) -> bool:
        if self._fixes.panel_nums:
            group["panel_num"] = panel_num
            logger.warning(f"For group {group_id}, fixed panel_num = {panel_num}.")
            return True

        logger.warning(
            f"For group {group_id}, panel_num is not set"
            f" (and should be {panel_num})"
            f" but fix panel nums = {self._fixes.panel_nums}."
        )
        return False

    # ── Panel-num fix helpers ─────────────────────────────────────────────────
    # TODO: Duplicated code from string_replacers
    def _can_replace_missing_panel_num(
        self, group: dict, page_panel_boxes: PagePanelBoxes
    ) -> tuple[PanelNumState, int]:
        # Read both fields the way `_get_panel_num_state` does. It defends
        # against an absent panel_num with a -1 default and then routes exactly
        # that case here, where a `group["panel_num"]` would have raised
        # KeyError -- and nothing up the stack catches it, so a single such
        # group would take down a whole multi-volume run.
        panel_num = int(group.get("panel_num", -1))
        assert panel_num == -1

        text_box = group.get("text_box") or []
        if text_box_problem(text_box) is not None:
            # `_check_group` screens these out before it asks; belt and braces,
            # since every line below indexes the four corner points.
            return PanelNumState.PANEL_NUM_NOT_SET_UNFIXABLE, -1

        for reduce_by in [20, 40, 60]:
            can_do, reduced_box = _get_reduced_text_box(text_box, reduce_by)
            if not can_do:
                logger.warning(f"Could not reduce text box: {text_box}")
                break
            assert reduced_box
            new_panel_num = _get_enclosing_panel_num(reduced_box, page_panel_boxes)
            if new_panel_num != -1:
                return PanelNumState.PANEL_NUM_NOT_SET_FIXABLE, new_panel_num

        logger.warning(f"Could not find enclosing panel for box: {text_box}")

        return PanelNumState.PANEL_NUM_NOT_SET_UNFIXABLE, -1

    # ── Output helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _write_queue_file(all_issues: list[IssueFound], output_file: Path) -> None:
        """Write de-duplicated queue file: one entry per unique (vol, page, engine, group_id).

        A group with several issues gets one entry carrying its most severe
        one (per ``_QUEUE_SEVERITY``), not whichever check happened to run
        first, so triage by issue type sees the worst of each group.

        An issue with a number behind it carries that as a sixth field, so a
        queue can be triaged before it is worked: the line-height ratio, the
        text-similarity ratio, or the box IoU, depending on the issue.
        ``load_queue_file`` reads only the first five fields, so the extra one
        costs the editor nothing.
        """
        best: dict[tuple[int, str, str, str], IssueFound] = {}
        for issue in all_issues:
            key = (issue.volume, issue.fanta_page, issue.engine, issue.group_id)
            held = best.get(key)
            if held is None or _severity_rank(issue.issue_type) < _severity_rank(held.issue_type):
                best[key] = issue

        queue_lines: list[str] = []
        for issue in best.values():
            ratio_str = "" if issue.ratio is None else f" {issue.ratio:.2f}"
            page = int(issue.fanta_page) if issue.fanta_page.isdigit() else issue.fanta_page
            queue_lines.append(
                f"{issue.volume}"
                f" {page}"
                f" {issue.engine}"
                f" {issue.group_id}"
                f" {issue.issue_type}"
                f"{ratio_str}"
            )
        output_file.write_text("\n".join(queue_lines) + ("\n" if queue_lines else ""))
        print(f'\nQueue file: "{output_file}" ({len(queue_lines)} entries).')

    @staticmethod
    def _print_issues_summary(all_issues: list[IssueFound]) -> None:
        print()
        print("=" * 80)
        counts: Counter[str] = Counter(issue.issue_type for issue in all_issues)
        print(f"Total issues: {len(all_issues)}")
        for issue_type, count in sorted(counts.items()):
            print(f"  {issue_type}: {count}")

    def _unreadable_prelims(self, title_list: list[str]) -> list[UnreadablePrelim]:
        """Return every prelim OCR file for these titles that will not parse.

        A file that is present but malformed is a different fault from one that
        is absent, and far quieter. Corruption that preserves a file's byte
        length and mtime -- a character typed over another -- is invisible to
        ``git status`` too, because git trusts its stat cache and never re-hashes
        it. One such file sat in the corpus with a stray ``!`` inside a
        ``text_box``, and every sweep that wrapped ``json.load`` in a
        ``try/except`` skipped it and reported nothing wrong.

        Reads the files directly rather than through ``SpeechGroups``, which
        raises on the first bad one; the point here is to find all of them.
        """
        unreadable: list[UnreadablePrelim] = []
        for title_str in title_list:
            title = STR_TITLE_TO_ENUM[title_str]
            volume = self._comics_database.get_fanta_volume_int(title_str)
            # Private, and the only way to get the paths without also parsing
            # them. `get_missing_prelim_pages` walks the same iterator for the
            # same reason -- it wants the paths, not the contents.
            for *_, json_file in self._speech_groups._iter_prelim_pages(title):  # noqa: SLF001
                if not json_file.is_file():
                    continue  # absent is `MissingPrelim`, reported separately
                try:
                    json.loads(json_file.read_text())
                except (OSError, ValueError) as e:
                    unreadable.append(UnreadablePrelim(volume, title_str, json_file, str(e)))
        return unreadable

    @staticmethod
    def _print_unreadable_prelims(unreadable: list[UnreadablePrelim]) -> None:
        """Report the malformed files and stop, rather than half-checking a volume."""
        print()
        print(f"Unreadable prelim OCR — {len(unreadable)} file(s) will not parse:")
        for u in sorted(unreadable, key=lambda x: (x.volume, str(x.json_file))):
            print(f"  Vol {u.volume}  {u.json_file.name}")
            print(f"      {u.title_str}")
            print(f"      {u.reason}")
        print()
        print("Nothing was checked. Restore each file and re-run:")
        print('  git -C "<prelim repo>" show "HEAD:<path>" > "<path>"')
        print(
            "Use `show >` rather than `checkout`: if the corruption did not change"
            " the file's size, git believes it matches the index and checkout is a"
            " no-op."
        )

    @staticmethod
    def _print_missing_prelims(all_missing: list[MissingPrelim]) -> None:
        """List the pages that were skipped for want of a prelim OCR file.

        These are not editor work, so they are kept out of the queue file. They
        are OCR that never ran, and the only place they surface otherwise is a
        warning buried in the log.
        """
        if not all_missing:
            return

        total = sum(
            len(m.pages_both) + sum(len(pages) for pages in m.pages_by_engine.values())
            for m in all_missing
        )
        print()
        print(f"Missing prelim OCR — {total} page(s), OCR never ran on these:")
        for missing in sorted(all_missing, key=lambda m: (m.volume, m.title_str)):
            parts: list[str] = []
            if missing.pages_both:
                parts.append(f"both engines: {_format_page_ranges(missing.pages_both)}")
            parts.extend(
                f"{engine} only: {_format_page_ranges(missing.pages_by_engine[engine])}"
                for engine in sorted(missing.pages_by_engine)
            )
            print(f"  Vol {missing.volume:>2}  {missing.title_str}: {'; '.join(parts)}")

    @staticmethod
    def _print_issue(issue: IssueFound) -> None:
        text_preview = issue.text.replace("\n", "\\n")[:60]
        notes_str = f", notes={issue.notes!r}" if issue.notes else ""
        ratio_str = "" if issue.ratio is None else f" ratio={issue.ratio:.2f}"
        print(
            f"  [{issue.issue_type}]"
            f" page={issue.fanta_page} {issue.engine} group={issue.group_id}"
            f" panel={issue.panel_num}{ratio_str}"
            f" text={text_preview!r}{notes_str}"
        )


# ── CLI ───────────────────────────────────────────────────────────────────────

app = typer.Typer()


MAX_DIRTY_PATHS_SHOWN = 10


class PrelimRepoStatus(Enum):
    """What git could tell us about the prelim work tree."""

    READ = auto()  # `dirty` is authoritative: empty means a clean tree
    NOT_A_REPO = auto()
    GIT_FAILED = auto()


@dataclass(frozen=True)
class PrelimRepoState:
    """The prelim repo as git reports it, with the two failure modes kept apart."""

    status: PrelimRepoStatus
    dirty: list[str]
    error: str = ""


def _prelim_repo_state() -> PrelimRepoState:
    """Return the prelim repo's uncommitted paths, or why they could not be read.

    "Not a work tree" and "git would not answer" used to come back as the same
    None, and the caller read both as "not version-controlled: warn and carry
    on". An index.lock, a permissions error or a momentarily missing git then
    disarmed the --fix undo gate on a repo that *did* have uncommitted prelim
    edits — the one situation the gate exists for.

    Returns:
        The work tree's porcelain status lines, or the reason there are none.

    """
    git = ("git", "-C", str(OCR_PRELIM_DIR))
    try:
        inside = subprocess.run(  # noqa: S603
            [*git, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
        if inside.returncode != 0:
            # `git` ran and said no. It says the same for a path that is simply
            # outside any repo, which is not a fault -- so only a stderr that
            # does not name that case is treated as one.
            stderr = inside.stderr.strip()
            if "not a git repository" in stderr.lower():
                return PrelimRepoState(PrelimRepoStatus.NOT_A_REPO, [])
            return PrelimRepoState(
                PrelimRepoStatus.GIT_FAILED, [], stderr or "git rev-parse failed"
            )
        if inside.stdout.strip() != "true":
            return PrelimRepoState(PrelimRepoStatus.NOT_A_REPO, [])

        status = subprocess.run(  # noqa: S603
            [*git, "status", "--porcelain"], capture_output=True, text=True, check=False
        )
        if status.returncode != 0:
            return PrelimRepoState(
                PrelimRepoStatus.GIT_FAILED, [], status.stderr.strip() or "git status failed"
            )
    except (OSError, subprocess.SubprocessError) as exc:
        return PrelimRepoState(PrelimRepoStatus.GIT_FAILED, [], str(exc))

    return PrelimRepoState(
        PrelimRepoStatus.READ, [line for line in status.stdout.splitlines() if line.strip()]
    )


def _check_prelim_repo_clean(*, force: bool) -> None:
    """Abort a --fix run unless the prelim edits it will overwrite are recoverable.

    The fixers rewrite ai_text and panel_num in place. Each written file gets a
    timestamped copy under the backup dir, but requiring a clean tree first is
    what makes ``git diff`` afterwards mean something, and what lets a whole
    run be undone in one command.

    Args:
        force: Skip the check, having accepted that the run cannot be undone.

    Raises:
        typer.Exit: When the prelim repo has uncommitted changes, or when git
            could not say whether it does.

    """
    state = _prelim_repo_state()

    if state.status == PrelimRepoStatus.NOT_A_REPO:
        logger.warning(
            f'Prelim dir is not a git repo: "{OCR_PRELIM_DIR}".'
            f" A --fix pass there cannot be undone."
        )
        return

    if state.status == PrelimRepoStatus.GIT_FAILED:
        # Whether there is anything to lose is precisely what could not be
        # established, so this is not the "no repo, nothing to check" case.
        if force:
            logger.warning(f"--force: proceeding though git could not be read ({state.error}).")
            return
        print(f"ERROR: could not read the prelim repo's status: {state.error}")
        print(
            f'  git -C "{OCR_PRELIM_DIR}" status --porcelain\n'
            f"\nFix that first, or re-run with --force to write without an undo path."
        )
        raise typer.Exit(1)

    dirty = state.dirty
    if not dirty or force:
        if dirty and force:
            logger.warning(f"--force: overwriting with {len(dirty)} uncommitted change(s) present.")
        return

    print(f"ERROR: {len(dirty)} uncommitted change(s) in the prelim repo:")
    for line in dirty[:MAX_DIRTY_PATHS_SHOWN]:
        print(f"  {line}")
    if len(dirty) > MAX_DIRTY_PATHS_SHOWN:
        print(f"  ... and {len(dirty) - MAX_DIRTY_PATHS_SHOWN} more")
    print(
        f"\nCommit or stash them first, so this --fix pass can be undone:\n"
        f'  git -C "{OCR_PRELIM_DIR}" add -A && git -C "{OCR_PRELIM_DIR}" commit\n'
        f"\nOr re-run with --force to overwrite them anyway."
    )
    raise typer.Exit(1)


def _default_output_file(volumes_str: str) -> Path:
    today = datetime.now(tz=UTC).date().isoformat()
    if volumes_str:
        safe = volumes_str.replace(",", "_").replace(" ", "")
        return Path(f"ocr-check-vol-{safe}-{today}.txt")
    return Path(f"ocr-check-{today}.txt")


@app.command(help="Check prelim OCR JSON files for issues and write a kivy-editor queue file.")
def main(  # noqa: PLR0913
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    output: Path = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Queue file path (default: auto-named ocr-check-vol-N-DATE.txt in CWD)",
    ),
    fix_panel_nums: bool = False,
    fix_groups_order: bool = False,
    fix_newlines: bool = False,
    fix_whitespace: bool = typer.Option(
        default=False,
        help="Strip outer/trailing whitespace and collapse doubled spaces in ai_text.",
    ),
    fix_dashes: bool = typer.Option(
        default=False,
        help="Rewrite '--' as an em-dash in ai_text and normalize the spacing around it.",
    ),
    force: bool = typer.Option(
        default=False,
        help="Run a --fix pass even with uncommitted prelim changes (they cannot be recovered).",
    ),
    include_marginal: bool = typer.Option(
        default=False,
        help="Also report the noisier line-height band as 'too_many_lines_marginal'.",
    ),
    line_height_threshold: float = typer.Option(
        LINE_HEIGHT_OUTLIER_FRACTION,
        help="Flag as 'too_many_lines' below this fraction of the page median line height.",
    ),
    line_height_marginal: float = typer.Option(
        LINE_HEIGHT_MARGINAL_FRACTION,
        help="Upper edge of the marginal band; only used with --include-marginal.",
    ),
    line_height_bimodal: float = typer.Option(
        LINE_HEIGHT_BIMODAL_RATIO,
        help=(
            "Measure a page against its densest cluster of line heights, not its median,"
            " when the median sits above that cluster by more than this ratio."
        ),
    ),
    box_iou_min: float = typer.Option(
        BOX_IOU_MIN,
        help="Flag as 'box_mismatch' when the engines' text_boxes overlap below this IoU.",
    ),
) -> None:
    if volumes_str and title_str:
        err_msg = "Options --volume and --title are mutually exclusive."
        raise typer.BadParameter(err_msg)
    if line_height_marginal < line_height_threshold:
        err_msg = (
            f"--line-height-marginal ({line_height_marginal}) must not be below"
            f" --line-height-threshold ({line_height_threshold})."
        )
        raise typer.BadParameter(err_msg)
    if not 0.0 <= box_iou_min <= 1.0:
        err_msg = f"--box-iou-min ({box_iou_min}) must be between 0 and 1."
        raise typer.BadParameter(err_msg)
    if line_height_bimodal < 1.0:
        # At or below 1.0 the mode would replace the median on nearly every
        # page, including the 63 where it sits *above* it and adds flags.
        err_msg = f"--line-height-bimodal ({line_height_bimodal}) must be at least 1.0."
        raise typer.BadParameter(err_msg)

    fixes = FixFlags(
        panel_nums=fix_panel_nums,
        groups_order=fix_groups_order,
        newlines=fix_newlines,
        whitespace=fix_whitespace,
        dashes=fix_dashes,
    )
    if fixes.any_enabled():
        _check_prelim_repo_clean(force=force)

    comics_database = ComicsDatabase()
    volumes = list(intspan(volumes_str)) if volumes_str else []
    title_list = get_titles(comics_database, volumes, title_str, exclude_non_comics=True)

    limits = LineHeightLimits(
        outlier=line_height_threshold,
        marginal=line_height_marginal,
        include_marginal=include_marginal,
        bimodal_ratio=line_height_bimodal,
    )
    output_file = output or _default_output_file(volumes_str)
    OcrChecker(comics_database, fixes, limits, box_iou_min).check_titles(title_list, output_file)


if __name__ == "__main__":
    app()

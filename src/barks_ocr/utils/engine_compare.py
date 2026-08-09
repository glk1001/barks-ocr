"""Comparing the same group as the two OCR engines recorded it.

Every page is read twice, by EasyOCR and PaddleOCR. Where the two engines agree
on the lettering they should also agree on where it sits and what is recorded
about it — `ocr_check` reports the exceptions as "box_mismatch" and
"attrs_mismatch", and the Kivy editor's Diff popup shows and repairs them.

Both tools read this module rather than each keeping its own copy of the field
list, which is the drift `vision_schema` exists to prevent and which the group
`type` vocabulary already fell into once.
"""

from barks_ocr.utils.ocr_box import PointList, points_bbox, text_box_problem

# Below this intersection-over-union, the two engines boxed different things.
# Measured over the 65,649 cross-engine pairs that read identically: median IoU
# 0.932, p10 0.801, p1 0.363. IoU rather than a pixel distance because it
# normalizes: a 30px edge slip is nothing on a 500px balloon and most of a 150px
# caption.
#
# 0.4 flags 761 pairs (1.16%), down from 1,188 at the original 0.5. Loosened
# because most of what it reports is a padding difference rather than a
# disagreement about where the lettering is: across the whole 0.1-0.5 range
# about three quarters of flagged pairs have one box wholly inside the other
# (`AK!` at 71x42 against 109x68, `GEE!` at 99x37 against 135x67). That ratio is
# flat, so there is no threshold that separates the two — see the calibration
# doc. Tunable per run with --box-iou-min.
BOX_IOU_MIN = 0.4

# Fields that differ between the engines by construction, so a difference in one
# says nothing about either reading. Percentages are over the pairs that read
# identically, so they measure the field's noise, not the corpus's errors.
ENGINE_LOCAL_FIELDS: frozenset[str] = frozenset(
    {
        "ocr_text",  # the raw engine output — that is the whole point of it (91%)
        "cleaned_box_texts",  # per-engine fragment quads (98%)
        "notes",  # Gemini writes them per engine, per file (90%)
        "text_box",  # "box_mismatch" owns this one, with a tolerance (93%)
        "florence_passed",  # florence_check runs against one engine at a time (99.9%)
        "panel_id",  # an engine-local id; panel_num is the shared one (11%)
    }
)

# Not engine-local, but not worth reporting either. "style" is a whole-group
# Gemini judgement that `docs/ocr-check-calibration.md` lists under "What is not
# validated", and it was over half of every attrs_mismatch raised — 3,789 pairs,
# of which 2,540 are nothing more interesting than "normal" against "emphasized".
# Reporting it buried the 2,342 "type" disagreements the check exists to find.
UNVALIDATED_FIELDS: frozenset[str] = frozenset({"style", "type_was"})

UNCOMPARED_FIELDS: frozenset[str] = ENGINE_LOCAL_FIELDS | UNVALIDATED_FIELDS


def box_iou(box_a: PointList, box_b: PointList) -> float | None:
    """Intersection over union of two text_boxes, or None if either is unusable.

    Both boxes are axis-aligned as stored, so the axis-aligned extents are the
    boxes themselves — no rotated-frame handling here, unlike the fit check.

    Returns None rather than 0.0 for a malformed box: that is "bad_text_box"'s to
    report, and every geometric check is gated on ``text_box_problem`` the same
    way. Scoring it as a total mismatch would report the same fault twice, the
    second time under the wrong name.
    """
    if text_box_problem(box_a) is not None or text_box_problem(box_b) is not None:
        return None

    ax0, ay0, ax1, ay1 = points_bbox(box_a)
    bx0, by0, bx1, by1 = points_bbox(box_b)

    overlap_w = min(ax1, bx1) - max(ax0, bx0)
    overlap_h = min(ay1, by1) - max(ay0, by0)
    if overlap_w <= 0 or overlap_h <= 0:
        return 0.0

    intersection = overlap_w * overlap_h
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - intersection
    return intersection / union if union > 0 else 0.0


def normalized_attr(value: object) -> object:
    """Collapse the empty forms to None so absent and empty compare equal.

    A field the vision pass wrote as ``[]`` on one engine and never wrote at all
    on the other is not a disagreement. Without this, ``emphasis_spans`` reads as
    differing on all 152 pairs that carry it, purely because one side stores the
    empty list and the other omits the key.
    """
    return None if value in ([], "", {}) else value


def differing_attrs(group_a: dict, group_b: dict) -> list[str]:
    """Names of the compared attributes that differ between two groups."""
    fields = (set(group_a) | set(group_b)) - UNCOMPARED_FIELDS
    return sorted(
        field
        for field in fields
        if normalized_attr(group_a.get(field)) != normalized_attr(group_b.get(field))
    )

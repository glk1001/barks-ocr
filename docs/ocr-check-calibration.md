# `ocr_check` — where the constants came from

Why the wrapping checks in `src/barks_ocr/tools/ocr_check.py` are tuned the way they
are. Written 2026-08-01, measured against the corpus as it stood then (5560 easyocr
prelim pages across 30 volume dirs).

Raw scripts and outputs behind every figure here:
`~/barks-vision/ocr-check-calibration/` (`scripts/`, `outputs/`).

---

## The two failure modes are not symmetric

`_text_fits_in_box` derives the font size from `box_h / n_lines` and then tests only
**width**. That has a consequence worth stating plainly, because it is not obvious
from reading the function:

> Adding line breaks shrinks the derived font, which narrows every line, which makes
> the text *easier* to pass. Height is never tested — it cannot be, since the font was
> defined to make it fit.

So the fit check is one-directional. It catches text collapsed onto **too few** lines
(the Gemini failure mode it was written for) and structurally **cannot** catch too
**many** lines. `too_many_lines` exists to cover the other direction, and it needs a
completely different signal — hence the page-median line height.

---

## `--fix-newlines` fit guards

Before the guards, the transplant fired on any donor found by `_find_matching_group`,
with no check that the donor fit its own box and no check that the rewrap helped.

Measured across every volume with prelim data (vols 8, 9, 20 abort on missing files —
a pre-existing data gap, not a code fault):

| outcome | groups |
|---|---|
| old and new both apply the same fix | 1032 |
| **old wrote a change the guards now block** | **72** |
| skipped by both | 228 |

Of the 72, the donor-fit guard catches 59 and the result-fit guard 7. They are real
bad writes, not conservatism. Two representative cases:

```
'THE LIONS YIELD!\nTHEY FLEE!'  ->  'THE LIONS YIELD! THEY FLEE!'
```

Collapsing two lines into one makes the overflow *worse*, because font size derives
from `box_h / n_lines`. Several appeared as easyocr/paddleocr pairs each rewrapping to
the other's bad pattern, so the old behaviour was not even idempotent. In every one of
the 72, the old code cleared `text_does_not_fit` while the text still overflowed.

Reproduce: `scripts/old_vs_new.py <volumes>` → `outputs/old-vs-new-per-volume-sweep.txt`.

---

## `MAX_FIX_PASSES = 5`

Pages are checked and saved in order, and within a page easyocr is processed before
paddleocr. A group therefore never sees a donor repaired later in the same pass — the
symptom was `--fix-newlines` "skipping some" and needing to be run twice.

`_check_title_to_convergence` repeats until a pass applies nothing. On vol 19 with both
`--fix-groups-order` and `--fix-newlines`, **every title converged in 2–3 passes** and
none hit the cap, which also confirms `renumber_groups()` is idempotent and does not
drive the loop. 5 is headroom, not a working value.

Reproduce: `scripts/flags.py <out> <vol> <panel_nums> <groups_order> <newlines>`.

---

## `LINE_HEIGHT_OUTLIER_FRACTION = 0.9`

A group is flagged when `box_h / n_lines` falls below this fraction of the page median.

**Calibrate on uncleaned volumes.** Vol 5 and the other low volumes have been manually
cleaned, so their wrapping reflects deliberate choices and they make the threshold look
far more aggressive than it is. Vols 19 and 21 are the honest sample.

Flag rate by threshold:

| threshold | vol 19 | vol 21 | vol 18 (already fixed at 0.8) |
|---|---|---|---|
| 0.95 | 397 (11.5%) | 545 (13.1%) | 205 (4.8%) |
| **0.92** | 271 (7.9%) | 354 (8.5%) | 64 (1.5%) |
| **0.90** | **257 (7.5%)** | **325 (7.8%)** | 41 (1.0%) |
| 0.85 | 239 (6.9%) | 283 (6.8%) | 29 (0.7%) |
| 0.80 | 203 (5.9%) | 254 (6.1%) | 0 (0.0%) |

The uncleaned volumes show a broad plateau from 0.75 to 0.92 and then a jump at 0.95
(vol 19: 271 → 397). **0.95 is the false-positive knee; 0.90 sits safely below it with
headroom.** Do not raise it without re-running this sweep.

The value was raised from an initial 0.8 because a real case sat at **0.82** — vol 18
page 031 group 15, where easyocr split `LOOK AT 'EM DIVE!` across two lines, dropping
the derived font from 28px to 22px while paddleocr had it right.

Reproduce: `scripts/threshold.py <volumes>`, `scripts/page_fonts.py <vol> <page> <engine>`.

### Fixability — the check earns its keep

Flag counts alone do not tell you whether a flag is real. On uncleaned volumes, running
`--fix-newlines` resolves **43%** of them using independent cross-engine evidence:

| | flagged | after `--fix-newlines` | auto-fixed |
|---|---|---|---|
| vol 19 | 202 | 116 | 86 (43%) |
| vol 21 | 240 | 136 | 104 (43%) |

The rewrites are unambiguous — 7-line balloons collapsed to 3, orphaned single-word
lines rejoined:

```
'WHO COULD THAT\nBE? I\nWISH\nI COULD\nHAVE GOTTEN\nA LOOK\nAT HIM!'
  ->  'WHO COULD THAT BE? I WISH\nI COULD HAVE GOTTEN A LOOK\nAT HIM!'
```

Reproduce: `scripts/show_fixes.py <out> <vol> <limit>` → `outputs/vol19-21-fixability.txt`.

### `MIN_GROUPS_FOR_LINE_HEIGHT = 5`

A page median from fewer than five measurable groups is not worth trusting. Stylized
types (`sound_effect`, `background`) are excluded both as subjects and as evidence —
their lettering is deliberately unlike the surrounding dialogue.

---

## What is **not** validated

- **`FIT_WIDTH_TOLERANCE = 1.5`** — inherited, never calibrated. It allows a line 50%
  wider than its box (the comment saying "10%" was wrong and was corrected). This is
  why some visibly overflowing text still passes; tightening it was out of scope.
- **`style == "emphasized"` is not ground truth for word-level bold.** It is a
  *whole-group* flag. On vol 1 pages 076-085, no group carries it despite the pages
  containing five unmistakable bold words. Do not use it to validate the vision pass.
- **`--volume N` aborts on a missing prelim file** rather than skipping the page.
  Vols 8, 9, 20 and vol 1 (page 500) all trip this. Use `--title` as a workaround.

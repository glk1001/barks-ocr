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

## The `--fix-*` flags require a clean prelim repo

The fixers rewrite `ai_text` and `panel_num` in place through a bare
`save_json()` — no backup, unlike the kivy editor and `vision_apply`, which pass
`save_json(backup_file=...)`.

Since 2026-08-01 the prelim files are a private git repo
(`~/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim`, `barks-ocr-prelim`), so
the answer is a guard rather than a backup: a `--fix` pass refuses to start
unless the tree is clean. That is strictly better than a backup, because it
forces the recoverable state to exist *before* the destructive write, and it
makes `git diff` afterwards show exactly what the fixer did.

```
$ barks-ocr-check --volume 19 --fix-newlines
ERROR: 3 uncommitted change(s) in the prelim repo:
   M "Carl Barks Vol. 19 .../031-easyocr-gemini-prelim-groups.json"
   ...
Commit or stash them first, so this --fix pass can be undone
```

`--force` overrides it, with a warning naming the count. If the prelim dir is
not a git work tree the check degrades to a warning rather than blocking, so the
tool still runs on a machine without the data repo.

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

> **Superseded 2026-08-01.** The sweep below measured a biased metric, and the case it
> cites has since been fixed on disk (vol 18 page 031 group 15 now reads three lines at
> ratio 1.068), so it can no longer serve as a regression test. Kept for the record;
> the current values come from the two sections that follow.

| threshold | vol 19 | vol 21 | vol 18 (already fixed at 0.8) |
|---|---|---|---|
| 0.95 | 397 (11.5%) | 545 (13.1%) | 205 (4.8%) |
| **0.92** | 271 (7.9%) | 354 (8.5%) | 64 (1.5%) |
| **0.90** | **257 (7.5%)** | **325 (7.8%)** | 41 (1.0%) |
| 0.85 | 239 (6.9%) | 283 (6.8%) | 29 (0.7%) |
| 0.80 | 203 (5.9%) | 254 (6.1%) | 0 (0.0%) |

Reproduce: `scripts/threshold.py <volumes>`, `scripts/page_fonts.py <vol> <page> <engine>`.

### The metric was biased by line count

`box_h / n_lines` is **not** the line height. It is the line height plus the balloon's
vertical padding divided by the line count:

```
box_h = n_lines * line_height + padding    =>    box_h/n = line_height + padding/n
```

The padding is charged once but divided by `n`, so short groups measure high. Median
ratio to the page median, by line count (vols 1, 19, 21, easyocr):

| n_lines | 1 | 2 | 3 | 4 | 5 | 6+ |
|---|---|---|---|---|---|---|
| median ratio | **1.188** | 1.020 | 0.998 | 0.986 | 0.976 | 0.959 |
| % flagged at 0.9 | 13.7% | 8.5% | 9.6% | 12.8% | 18.1% | 19.9% |

One-line groups sat 19% above the page median. Left in the median they inflated it and
pushed correctly wrapped multi-line groups under the threshold — and they were *also*
being judged, which is meaningless: **24% of all flags were on single-line groups**, and
one line cannot be too many lines. `MIN_LINES_FOR_LINE_HEIGHT = 2` drops them from both
roles at once, since `_implied_line_height` feeds the median and the test alike.

`type: title` joined `STYLIZED_TYPES` in the same pass. A splash-page logo is hand-drawn
at one huge word per line — vol 1 page 010's is 160px per line against a page median of
46 — so it is evidence of nothing. It also cleared 18 bogus `text_does_not_fit` flags
corpus-wide, since `STYLIZED_TYPES` drives `_fit_params` too.

The reported case was **vol 1 page 010 panel 4**: `PULL, YOU SWABS, / THERE'S A BIG BLOW /
COMING!` — correctly wrapped, flagged in both engines. That page has only seven
measurable groups, three of them polluting: the title logo (ratio 3.48) and two one-line
`AYE!` balloons (1.44, 1.48). They pulled the median from ~42 to 46.

A regression model (`box_h = L*n + P` fitted per page) was tried and **rejected**: it
centres the ratio across line counts but widens the spread, raising flag rates at the
same threshold (vol 18 0.3% → 2.8%).

### Two bands, because one threshold cannot do both jobs

With the metric fixed, vol 1 shows a cliff exactly where the uncleaned volumes show a
plateau:

| threshold | vol 1 (cleaned) | vol 18 (cleaned) | vol 19 | vol 21 |
|---|---|---|---|---|
| 0.95 | 375 (19.3%) | 126 (3.2%) | 225 (7.7%) | 281 (8.0%) |
| 0.92 | 168 (8.6%) | 24 (0.6%) | 155 (5.3%) | 185 (5.3%) |
| 0.90 | 77 (4.0%) | 9 (0.2%) | 147 (5.1%) | 172 (4.9%) |
| **0.85** | **6 (0.3%)** | 6 (0.2%) | 133 (4.6%) | 151 (4.3%) |
| 0.80 | 4 (0.2%) | 2 (0.1%) | 106 (3.6%) | 127 (3.6%) |

A cleaned volume should not hold 66 real wrapping errors bunched in one 0.05-wide band,
and the uncleaned volumes lose only ~9% of their flags across the same span. So the band
is split rather than picked:

- **below `LINE_HEIGHT_OUTLIER_FRACTION = 0.85`** → `too_many_lines`, always reported;
- **0.85 to `LINE_HEIGHT_MARGINAL_FRACTION = 0.9`** → `too_many_lines_marginal`, reported
  only with `--include-marginal`.

Both edges are CLI-tunable (`--line-height-threshold`, `--line-height-marginal`).

| | default `too_many_lines` | `--include-marginal` adds |
|---|---|---|
| vol 1 (cleaned) | 6 | +71 |
| vol 18 (cleaned) | 6 | +3 |
| vol 19 | 131 | +13 |
| vol 21 | 147 | +16 |

The split is what makes the marginal band's character visible: it is nearly all of vol
1's flags and almost none of vol 19's.

Every line-height issue now carries its ratio, in the console line and as a **sixth
field** in the queue file, so a queue can be triaged before it is worked.
`load_queue_file` reads only the first five fields, so the editor is unaffected.

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

A page median from fewer than five measurable groups is not worth trusting. Raising the
bar for what counts as measurable took the unjudged-page count from 34 to 94; that is
the price of the fix, and it is what makes page 010 come out right — it has exactly four
multi-line groups, and at a minimum of 4 its paddleocr `g3` is flagged again at 0.83.

Stylized types (`sound_effect`, `background`, `title`) are excluded both as subjects and
as evidence —
their lettering is deliberately unlike the surrounding dialogue.

---

## What is **not** validated

- **`FIT_WIDTH_TOLERANCE = 1.5`** — inherited, never calibrated. It allows a line 50%
  wider than its box (the comment saying "10%" was wrong and was corrected). This is
  why some visibly overflowing text still passes; tightening it was out of scope.
- **`style == "emphasized"` is not ground truth for word-level bold.** It is a
  *whole-group* flag. On vol 1 pages 076-085, no group carries it despite the pages
  containing five unmistakable bold words. Do not use it to validate the vision pass.
- **The marginal band has not been checked against the art.** It is called noise on
  distributional evidence — a cliff on cleaned volumes against a plateau on uncleaned
  ones — not because anyone looked at the pages. `--include-marginal` plus the ratio in
  the queue file is there so that can be settled properly.

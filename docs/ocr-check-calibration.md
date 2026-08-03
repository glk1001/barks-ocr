# `ocr_check` — where the constants came from

Why the wrapping checks in `src/barks_ocr/tools/ocr_check.py` are tuned the way they
are. Written 2026-08-01, measured against the corpus as it stood then (5560 easyocr
prelim pages across 30 volume dirs).

Raw scripts and outputs behind every figure here:
`~/barks-vision/ocr-check-calibration/` (`scripts/`, `outputs/`).

---

## Engine agreement is the completion metric

Every page is OCR'd twice, by EasyOCR and PaddleOCR, and reconciled by hand until
the two agree. A page both engines read identically has independent corroboration
and needs nothing further; the rest is the work left. `ocr_check` reports it per
volume, and it separates the corpus cleanly:

```
Engine agreement — 3595/5358 pages (67.1%):
  Vol  1  ########################  100.0%  (155/155)
  Vol 18  ##################         74.1%  (126/170)
  Vol 19  ###                        12.4%  ( 21/170)
```

Vols 1-17 and 28 sit at 94-100%, vol 18 at 74%, and vols 19-27 and 29 at 2-12%.

The comparison runs **once per page pair**, not once per engine — the surrounding
loops visit each page twice, and comparing there would report every mismatch
twice. It reads from the live `speech_page_json` rather than
`SpeechPageGroup.speech_groups`, which is built at load time and would not see
fixes applied earlier in the same pass.

`only_in_easy` / `only_in_paddle` / `text_mismatch` came from `compare.py`, now
deleted. The fold-in was verified equivalent: on vol 18 both report the same
10 / 13 / 65.

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

## Angled lettering gets a second chance in its own frame

The group `text_box` is always axis-aligned (the Gemini grouper writes it that
way), so for lettering drawn on a slant it overstates **both** dimensions —
`HOORAY!` at ~20° on vol 2 page 040 reads as a 112px-tall single line, the
derived font is enormous, and `text_does_not_fit` fires on text that plainly
fits its balloon.

The OCR engines' fragment quads in `cleaned_box_texts` do follow the angle.
When their median baseline angle passes `FRAGMENT_ANGLE_THRESHOLD_DEG` (5°,
matching `OcrBox.is_approx_rect`), `_group_text_fits` re-measures in that
frame: every fragment corner rotated back by the angle, bounding box taken,
same font-from-height width test.

Applied **one-directionally, after the axis check fails** — the rotated frame
can clear a false flag but never create a new one. Measured on vols 1-19
before adopting: 37 of the then-current `text_does_not_fit` flags were on
angled groups; 23 cleared in the rotated frame (all verified plausible —
diagonal captions like `NEXT MORNING`, slanted cheers) and 14 genuinely
overflow. Groups without usable fragments fall back to the axis-only check
unchanged. The line-height checks stay on axis geometry deliberately: the
inflated height makes angled groups measure *roomy*, which fails safe there.

## The em-dash rule, and what measuring it changed

Two regexes became one positive rule: an em-dash needs a space, line break or
text edge before it, and one of those, the end of the text, or terminal
punctuation it hugs (`BEHIND —!`) after it. What it may not do is drift away
from that punctuation (`WHAT GEEFS — ?`).

**2026-08-03: the punctuation cases were questioned, flipped, and reverted the
same day.** The convention as stated from memory ("space on both sides,
always") would have made `BOOK —!` wrong and `WHAT GEEFS — ?` right; checked
against standard typography — interruption punctuation binds to the dash as
one unit — and the reviewed vols 1-18 (80 hugging to 16 spaced, and the art
hugs), the original hugging rule stands. One change was kept from the
episode: a **closing double quote may hug the dash** (`GET SICK —"`,
interrupted speech ending a quotation) — the original rule wrongly flagged
all 30 corpus cases of it.

Measured contexts, which is what settled the rule:

| correct | | wrong | |
|---|---|---|---|
| `SP — SP` | 5599 | `alnum — \n` | 196 |
| `SP — \n` | 2566 | `alnum — $` | 185 |
| `SP — $` | 2000 | `alnum — alnum` | 62 |
| `—!` hugging | 90 | `alnum — SP` | 31 |
| `! —` between clauses | 191 | `SP — —` doubled | 30 |
| | | `— !` adrift | 37 |

**The old check was over-flagging, and the acknowledgements prove it.** Its
`[!?]\s+—` half fired on 191 occurrences of `FIGURE THIS OUT! — UH, OH!`, which
is correct usage — and **60 of the 75 `dash_wrong_space` acknowledgements in the
corpus were dismissals of exactly that**. Meanwhile it missed ~400 real breaches.
Net effect of the rewrite: **+493 real catches, −183 false positives**.

Old issue names are honoured as aliases when reading `acknowledged_issues`
(`_ACKNOWLEDGEMENT_ALIASES`), so none of the 75 dismissals was orphaned and no
prelim file needed rewriting.

## Checks added after measuring, and checks rejected after measuring

Every candidate was counted against all 10,716 prelim files before being adopted.
Added:

| check | hits | |
|---|---|---|
| `text_mismatch` | 8080 | engines disagree on the text |
| `only_in_paddle` / `only_in_easy` | 996 / 535 | one engine has a group the other lacks |
| `double_hyphen` | 198 | a hyphen run standing in for an em-dash |
| `whitespace` | 122 | outer, per-line trailing, or doubled |
| `panel_num_mismatch` | 74 | text_box lies wholly inside a *different* panel |
| `unbalanced_quotes` | 51 | odd number of `"` |
| `invalid_type` | 26 | `caption`, `speech`, `dialogtext`, `dialogtext_bubble_id` |

Added 2026-08-03, structural rather than measured — each one is a data error
whenever it fires, so there was nothing to calibrate:

- **`invalid_markup`** — `speech_markup.validate_markup` over the stored
  `ai_text`: unbalanced or mis-nested `[b]`/`[i]`, disallowed tags, unescaped
  `&`/`[`/`]`. Dismissable, in the `group_checks` registry.
- **`bad_text_box`** — a `text_box` that is missing, not 4 points, has a
  malformed point, or has zero area. It also gates every geometric check and
  fixer for that group; such boxes used to be skipped silently and then crash
  a `--fix` pass.
- **`panel_num_out_of_range`** — a set `panel_num` of 0 or beyond the page's
  panel count, which `panel_num_mismatch` structurally cannot see (it needs
  the box to sit wholly inside a different *real* panel).

**Rejected, so they are not proposed again:**

- **duplicate text on a page (2407), or within one panel (1020)** — legitimate:
  two nephews both say `AYE!`.
- **em-dash at a line break (2532)** — ordinary wrapping.
- **soft hyphen at a line break (806)** — that *is* the wrap convention;
  `speech_groupers` strips `­\n` when building `ai_text`. Only a soft hyphen
  **not** at a line end is wrong, and there are 2.
- **text_box not inside any panel (5.9%)** — balloons overhang gutters. Only the
  "inside a *different* panel" variant is precise enough, at 0.2%.

## The `--fix-*` flags require a clean prelim repo

The fixers rewrite `ai_text` and `panel_num` in place. Since 2026-08-03 each
written file also gets a timestamped copy under the backup dir, like the kivy
editor and `vision_apply` — but the clean-tree guard remains the real safety.

Since 2026-08-01 the prelim files are a private git repo
(`~/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim`, `barks-ocr-prelim`), so
the primary answer is a guard rather than a backup: a `--fix` pass refuses to
start unless the tree is clean. That is strictly better than a backup, because
it forces the recoverable state to exist *before* the destructive write, and it
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

`--fix-whitespace` and `--fix-dashes` are the unattended ones — pure string
cleanups with no judgement in them, unlike the wrapping fixes, which need
cross-engine evidence. Two things learned building them:

- **The dash fixer converts hyphen *runs*, not pairs.** 70 of the 221 runs in the
  corpus are three hyphens or more, so a plain `--` swap turned `HOW ARE ---`
  into `HOW ARE —-`. Caught by running the fixer against the repo and reading
  `git diff` — which is the guard earning its keep on its first outing.
- **61 of those runs touch a word**, so converting them leaves an em-dash that
  `em_dash_spacing` then flags. That is intended: the transcription is now right
  and only the spacing is open, which needs a human.

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

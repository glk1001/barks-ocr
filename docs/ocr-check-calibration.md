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

**Agreement counts how the page was *read*, and nothing else.** `box_mismatch` and
`attrs_mismatch` — see *Comparing the record, not just the reading* below — are
reported and queued but deliberately excluded from this metric.

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

## Comparing the record, not just the reading

The cross-engine comparison used to stop at the text. Two groups could hold the same
lettering while disagreeing about where that lettering sits and what kind of lettering
it is, and nothing looked. `type` alone disagreed on **2,342** pairs — the class the
vision pass structurally cannot see (see *paddleocr-only type errors*), because it reads
one engine at a time.

So on every pair the two engines read **identically**, two further checks run:
`box_mismatch` and `attrs_mismatch`. Both are reported against easyocr, as
`text_mismatch` already is, with the paddleocr group id in the notes — the engines number
their groups independently, so without it the entry names a group that cannot be found in
the other pane.

They run *only* where the readings match. A positional pair with differing text is
already reported as `text_mismatch` and may simply be mis-paired, so a box or attribute
verdict on it would be measuring nothing.

### `BOX_IOU_MIN = 0.4`

Intersection over union of the two axis-aligned boxes. Measured over the 65,649 pairs
that read identically:

| | p1 | p5 | p10 | p25 | p50 |
|---|---|---|---|---|---|
| IoU | 0.363 | 0.701 | 0.801 | 0.889 | **0.932** |

| threshold | pairs | share |
|---|---|---|
| IoU < 0.50 | 1,188 | 1.81% |
| IoU < 0.45 | 939 | 1.43% |
| **IoU < 0.40** | **761** | **1.16%** |
| IoU < 0.35 | 615 | 0.94% |
| IoU < 0.30 | 504 | 0.77% |
| IoU < 0.20 | 345 | 0.53% |

IoU rather than a pixel distance because it normalises: a 30px edge slip is nothing on a
500px balloon and most of a 150px caption. **111 pairs do not overlap at all**, and
several of those carry a degenerate box on one side (`WHOOSH!` at 309x7, `ZOOM` at
195x4). Tunable per run with `--box-iou-min`.

It shipped at 0.5 and was loosened to 0.4 on 2026-08-09, which is a judgement about queue
size rather than a knee in the data — there is no knee, and the sweep below is the reason
to say so out loud.

A malformed box on either side yields no verdict at all rather than a score of 0:
`bad_text_box` already owns that fault, and every geometric check in the module is gated
on `text_box_problem` the same way.

#### Most of what it flags is padding, not disagreement

Split the flagged pairs by whether one box sits wholly inside the other — the engines
agreeing on where the lettering is and differing only on how much room to give it:

| band | pairs | nested | offset | nested share |
|---|---|---|---|---|
| 0.45–0.50 | 249 | 189 | 60 | 76% |
| 0.40–0.45 | 178 | 147 | 31 | 83% |
| 0.35–0.40 | 146 | 103 | 43 | 71% |
| 0.30–0.35 | 111 | 83 | 28 | 75% |
| 0.25–0.30 | 101 | 77 | 24 | 76% |
| 0.10–0.25 | 185 | 132 | 53 | 71% |
| **0.00–0.10** | **218** | **71** | **147** | **33%** |

The share is flat at roughly three quarters all the way from 0.5 down to 0.10, and only
flips below 0.10. Two things follow.

**Lowering the threshold does not improve the signal, it just shortens the queue.** Every
band drops nested and offset pairs in the same proportion, so 0.4 against 0.5 is 427
fewer flags of the same mixture, not 427 fewer false ones. The typical nested case is a
short exclamation where one engine boxes the glyphs and the other the balloon — `AK!` at
71x42 against 109x68, `GEE!` at 99x37 against 135x67. Whether that is benign depends on
what reads the box: for the fit and line-height checks a box 2.4x taller is not a detail,
and those run per engine off exactly this geometry.

**If only genuine offsets are wanted, the threshold is the wrong instrument.** The clean
separation is nesting, not overlap: exempting nested pairs would leave ~286 offset pairs
at 0.5, more real disagreement than 0.4 reports while queueing far less padding. Not
done, because "one box inside the other" is not automatically correct — see above — and
it would need its own calibration.

### Which attributes must match

Everything the two groups carry, minus the fields that are engine-local by construction.
The exclusions, with their differ-rate over identically-read pairs — these measure the
field's noise, not the corpus's errors:

| excluded | differs | why |
|---|---|---|
| `ocr_text` | 91% | the raw engine output; that is the whole point of it |
| `cleaned_box_texts` | 98% | per-engine fragment quads |
| `notes` | 90% | Gemini writes them per engine, per file |
| `text_box` | 93% | `box_mismatch` owns it, with a tolerance |
| `florence_passed` | 99.9% | `florence_check` runs against one engine at a time |
| `panel_id` | 11% | an engine-local id; `panel_num` is the shared one |

**Absent and empty compare equal** — `[]`, `""` and `{}` all normalise to `None`. Without
that, `emphasis_spans` reads as differing on all 152 pairs that carry it, purely because
one side stores the empty list and the other omits the key.

What actually fires, corpus-wide (6,432 pairs, some naming more than one field):

| field | pairs |
|---|---|
| `style` | 3,789 |
| `type` | 2,342 |
| `speaker_reviewed_date` / `speaker_reviewed` | 389 / 308 |
| `acknowledged_issues` | 78 |
| `identified_by` | 62 |
| `type_was` / `speaker_was` / `cap_colour_was` | 46 / 42 / 11 |
| `speaker` / `speaker_confidence` / `cap_colour` | 42 / 42 / 41 |
| `speaker_review_note` | 27 |
| `ai_text` | 1 |

Two things worth knowing about that table. `style` is over half of it and the docs
already list it under *What is not validated* — it is a Gemini judgement, and 2,540 of
its mismatches are just `normal` vs `emphasized`, so treat it as the low-value tail. And
the `*_was` / `*_reviewed*` rows are review bookkeeping: they mean a reviewer edited one
engine and `vision-mirror` has not been run, not that the lettering is wrong.

The lone `ai_text` row is not a contradiction of "read identically". The text comparison
runs on `_plain`, which strips emphasis markup, so a pair whose markup differs but whose
lettering does not passes the reading check and is caught here instead.

### Working them in the editor

Both are fixed through the Kivy editor's **Diff** button, one per pane. Two things
support it:

- **The other engine's box is drawn on the crop**, dashed and grey-white, under the
  editable orange one and with no handles. A `box_mismatch` is then a picture rather than
  a number — you can see which of the two boxes the lettering is actually in. It appears
  whenever a counterpart exists, not only when the IoU is bad.
- **The pane header carries a marker** — `[diff: box 0.34; type, speaker]` — so a
  disagreement is visible while stepping through groups, without opening anything.

The popup lists the IoU row first, then one row per differing field, each showing both
engines' values with a button that takes the other engine's. **Take all** does the lot.
Every action writes into the pane you opened it from and never the other file, so the
reviewer always picks which reading wins.

Taking a field the other engine does not carry **removes** it rather than writing an
empty value, so the two sides end up equal under the same absent-is-empty rule
`differing_attrs` compares by. Writing `None` would leave the row on screen for ever.

The editor and `ocr_check` both read `utils/engine_compare.py` — the field list, the
normalisation and the IoU live there once. The `type` vocabulary was duplicated across
two modules once before and drifted; this does not repeat it.

A pair the two engines read *differently* has no counterpart at all: the popup says to
reconcile the text first, and no ghost box or marker is drawn. That matches when the
checks run at all.

### Why neither counts towards engine agreement

Folding them in would take agreement from **70.0% to 24.3%**, and the drop is dominated
by that bookkeeping tail rather than by anything about how a page was read. A stale
`speaker_reviewed_date` is worth fixing and says nothing about whether the two engines
read the page the same way.

So `_check_engine_agreement` accumulates the two levels separately and computes
`agree` from the reading level alone. The temptation to simplify it back to
`not issues` is why the docstring says so in as many words. Verified on the corpus: with
both checks live, agreement is **3749/5358 (70.0%)** and every pre-existing issue count
is unchanged to the unit.

## `text-will-never-fit`, the last resort on the layout checks

Everything above narrows the layout checks towards the flags a reviewer can act
on, and some groups survive all of it: the lettering is transcribed correctly,
the wrapping is what the balloon does, and the box is simply too small to hold
that text at page-normal lettering. Nothing in the file is wrong, so no edit
clears the flag — the reviewer ticks `text-will-never-fit` in the editor's
**Mark OK** popup and `ocr_check` stops running its layout checks on that group.

It is registered in `DISMISSABLE_PREDICATES` against `_never_fires`, like
`florence-check`: the checks themselves live in `ocr_check`, need the rendered
font and the page's geometry, and cannot run from `group_checks`. So the popup
always shows it as "not firing" and never pre-ticks it — including from a
`text_does_not_fit` or `too_many_lines` queue entry, deliberately, since most of
both is a fixable box or a stray line break and this acknowledgement gives up on
the group's layout for good.

### It covers both checks, because they are two halves of one measurement

It first shipped covering the fit check only, on the reasoning that accepting an
overflow says nothing about line packing. That reasoning does not survive the
arithmetic: both checks read the same box against the same line count, from
opposite sides. The fit check derives its font from box height / line count and
compares the widest rendered line to the box width; the line-height check
compares that same box height / line count to the page median.

So a box that cannot be reconciled with its text lands on whichever side its
wrapping puts it. Too small in *both* dimensions and the derived font goes tiny,
the width test passes, and the implied line height falls under the 0.85 bar —
`too_many_lines`. Narrow but tall enough and the font is page-normal, the line
height is unremarkable, and the width test fails — `text_does_not_fit`. The
reviewer's judgement is about the box and the text, not about which of the two
arithmetics caught them, so one acknowledgement covers both.

No reviewed group needs it for the line-height half *yet*. Vol 3 page 117 group
11 looked like one — 7 lines in a 173x83 box, implied line height 11.9px against
a page median of 38 — and turned out to be a data error rather than a never-fit:
the box is correctly drawn around the curved `$100,000` on the money bag, and it
is the `ai_text` that is wrong, a duplicate of the `HAW! HAW! HAW!` balloon
beside it (group 10). Corrected to `$100,000` it is single-line, so the
line-height check does not judge it at all. A cautionary example rather than a
supporting one: a deep line-height outlier on a small box is worth a look at the
art before it is accepted, because a duplicated `ai_text` produces exactly that
signature.

Per *An acknowledged group is off limits to its fixer* below, the
`--fix-newlines` transplant is gated with the checks — no issue reported means
no transplant attempted, so the layout the reviewer accepted is not quietly
rewritten on the next `--fix` pass.

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

Added 2026-08-27, both of them holes rather than new ideas — the tool already
knew about each fault and said nothing a reviewer could act on:

- **`groups_out_of_order`** (951 page/engine entries) — see the section below.
- **`panel_num_fixable`** (190 groups) — a `panel_num` of -1 that the tool can
  place itself. `--fix-panel-nums` writes it; without that flag the group was
  logged as a warning and then dropped, so the groups that had been positively
  diagnosed were the ones missing from the queue while the *un*diagnosable ones
  (`panel_unassigned`, 340) were in it.

Added 2026-08-28:

- **A space before a sentence's `!` or `?`** ("SCARE !", "HAIRY HARRY ???") —
  folded into the existing `whitespace` check and `--fix-whitespace`, not given
  a type of its own: it is the same class of slip as a doubled space, and the
  corpus carries **187 groups** of it. Spaces and tabs only, so the 10 groups
  where the art wrapped the punctuation onto its own line ("SCARE\n!") keep
  their line break. It requires an alphanumeric before the space, which is what
  keeps it off `— !` — `with_dash_fixes` already owns that one, and two fixers
  claiming a group is how they fight over it.

Added 2026-08-27:

- **`panel_nums_not_contiguous`** (416 page/engine entries) — a page that skips
  a panel number. See the section below; unlike the two above it, this one is a
  prompt to look rather than a fault.

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
cross-engine evidence. Three things learned building them:

- **The dash fixer converts hyphen *runs*, not pairs.** 70 of the 221 runs in the
  corpus are three hyphens or more, so a plain `--` swap turned `HOW ARE ---`
  into `HOW ARE —-`. Caught by running the fixer against the repo and reading
  `git diff` — which is the guard earning its keep on its first outing.
- **The fixer also spaces a dash off the word before it.** This started as a
  deliberate omission — 61 of the runs touch a word, and leaving them for
  `em_dash_spacing` to flag was called intended. It was not: the AI writes
  `WAY—` directly far more often than a hyphen run ever produced it, so the
  same mechanical edit was reaching the queue 490 times with no fixer able to
  make it (vol 4 page 048 group 4 is the case that surfaced it). The corpus
  puts a break before the dash **10,699 to 490**, so the rewrite carries no
  more judgement than the run conversion does.
- **Carve-outs in a fixer are a bug, not a nicety.** The first version of the
  spacing rewrite exempted the closed-up `IN—AND HOW` form behind a lookahead
  and left the right-hand side of the dash alone entirely, on the grounds that
  `em_dash_spacing` would flag what was left and a human would judge it. That
  reasoning does not survive contact with the numbers: **158 groups came out of
  `--fix-dashes` still flagged**, and not one of them needed judgement — they
  needed a rule. The exemption's own evidence, a 71-to-9 corpus count for the
  closed form, was measuring the AI's habit rather than the art, which is
  exactly the objection that had already retired the identical argument for the
  490 `WAY—` cases.

So `--fix-dashes` now enforces one rule end to end, the same one
`has_em_dash_spacing_error` tests: **an em-dash takes a break — space, line
break or text edge — on its left, and a break, a text edge, or its own hugging
punctuation on its right.** Four ordered rewrites in `with_dash_fixes` get there,
and they are idempotent, so the fix loop converges on the first pass. Corpus
counts for each class it now settles:

| Class | Occurrences | Handling |
|---|---|---|
| `HOW ARE ---` hyphen runs | 221 | converted to one dash |
| `WAY—`, dash hugging the word before it | 490 | space inserted (break-before wins 10,699 to 490) |
| `IN—AND HOW`, dash closed between two words | 67 | spaced both sides |
| `CAME ASHORE — !`, punctuation adrift by a space | 30 | pulled back to `—!` |
| `'EXPECT'— AIR`, dash hugging closing punctuation | 7 | space inserted |
| `WHAT'S THIS —FLY SPRAY?`, space left but not right | 7 | space inserted |

Two classes are settled in the *check* instead, because no edit would improve
them: `AD INFINITUM —)` and `GREAT SECRET —'` join the hugging set (3 cases —
spacing a dash off a closing paren would be worse), and punctuation adrift
across a *line break*, `WELL, I'LL BE —\n!!!`, stops being flagged at all (8
cases — that is the art's wrapping, and closing it up would merge two lines that
the line-fit checks measure).

- **One class is left flagged on purpose.** The doubled dash `——` — `MINIE MO
  ——`, `ME —— AND WITHOUT` — 34 occurrences over 16 page/group spots. Collapsing
  it to a single dash would be defensible by analogy with the hyphen run, and
  was declined: it is a reading of the lettering, not a spacing convention. The
  left-hand rewrite excludes `EM_DASH` from its lookbehind precisely so the
  fixer cannot quietly turn `——` into `— —` on its way past.

### An acknowledged group is off limits to its fixer

A fixer runs on the same groups its check reports, which has to include *not*
running on a group the reviewer has dismissed. Otherwise the next `--fix` pass
silently reinstates the very edit the dismissal rejected, and the pass after
that does it again — the acknowledgement becomes unusable against anything a
fixer can write. `with_dash_fixes` therefore returns its input untouched when
the group acknowledges `em_dash_spacing` or `double_hyphen` (old
`dash_wrong_space`/`dash_no_spaces` names included), and `--fix-whitespace`
skips a group acknowledging `whitespace`. Corpus: **117 groups** carry a dash
acknowledgement, 45 of them still breaching the rule and correctly silent.

It is all-or-nothing per group, not per rewrite. Vol 7 page 135 group 6 settled
that: the reviewer accepted `dash_wrong_space` and hand-restored `SPUT! — --`,
and gating each rewrite on its own check would have re-run the hyphen-run
conversion — `double_hyphen` not being acknowledged there — putting `— —`
straight back. A group that has been looked at once is finished with the
machine.

**This was found the hard way.** The first run of the widened fixer rewrote
**23 already-acknowledged groups** across vols 1, 2 and 17 before the gate
existed, including `AND IF WE\nWIN — ?` → `WIN —?`, dismissed years earlier
under the old name. They were restored from `HEAD`; the guard that made it
recoverable was, again, running against a clean repo and reading `git diff`.

## `MAX_FIX_PASSES = 5`

Pages are checked and saved in order, and within a page easyocr is processed before
paddleocr. A group therefore never sees a donor repaired later in the same pass — the
symptom was `--fix-newlines` "skipping some" and needing to be run twice.

`_check_title_to_convergence` repeats until a pass applies nothing. On vol 19 with both
`--fix-groups-order` and `--fix-newlines`, **every title converged in 2–3 passes** and
none hit the cap, which also confirms `renumber_groups()` is idempotent and does not
drive the loop. 5 is headroom, not a working value.

Reproduce: `scripts/flags.py <out> <vol> <panel_nums> <groups_order> <newlines>`.

## Group order is checked, not just fixed

`renumber_groups()` orders a page's groups by `(panel_num, banded y, x)`, and
`--fix-groups-order` is the only thing that calls it. Nothing checked whether the
stored ids were *already* in that order, and two things quietly assumed they were.

`_groups_by_panel` sorted by `int(group_id)` and `_check_engine_agreement` pairs
those lists positionally. Run `--fix-panel-nums` without `--fix-groups-order` and a
group changes panel, its id goes stale, and every pair in that panel is offset by one
— a `text_mismatch` on each, the page out of the agreement metric, and no issue
naming the cause. A group appended by an editor at `max(id) + 1` does the same. The
roll-call invocation passes no fix flags at all, so the repair never ran there.

So the pairing now sorts on `speech_groupers._group_sort_key` itself — imported
rather than copied, because a local copy drifting from it is the exact fault being
caught — and a page whose ids are not in that order is reported as
`groups_out_of_order`: one entry per page/engine, on the first group out of place.
It ranks above every check below it in `_QUEUE_SEVERITY`, since a queue entry naming
a group id that a renumber is about to change points at the wrong group. It stays
silent on a page holding a malformed `text_box`, because `renumber_groups()` raises
on one and `_check_page_group` skips the page — an entry telling the reviewer to
re-run the fixer would not be true there.

Corpus: **951 page/engine entries** across vols 1-29, one `--fix-groups-order` pass
from being cleared. Vol 6 page 113 is the shape of it — keys `0…9, 12, 10, 11`,
a group added later and numbered last.

The pairing change on its own is small and in the right direction. Measured over
vols 1-8, 19 and 21 (1,910 pages) with the old id sort swapped back in: two
`text_mismatch` flags disappear (vol 7 page 131 group 7, at ratio 0.18, among them)
and engine agreement moves 1872 → 1873 pages.

---

## `panel_nums_not_contiguous` — a page that skips a panel

The groups on a page should occupy panels 1..n with nothing skipped. A hole is
either lettering that was never grouped, or a run of groups filed under the wrong
panel. Nothing saw it: `panel_num_mismatch` needs the box to sit wholly inside a
different *real* panel, `panel_num_out_of_range` only checks one group's number
against the panel count, and the cross-engine `MissingPanel` fires only when the
two engines *disagree* — so a page where both engines skip the same panel said
nothing at all. That last case is 197 pages, and is the whole of what this check
adds; the 71 pages where only one engine has the hole were already named by
`MissingPanel` (which is printed, never queued).

Bounded above by the highest panel that has text, not by the page's panel count.
Ending on a wordless panel is ordinary Barks — 67 easyocr pages (1.3%) do — and
is not a fault, so only an interior hole is reported. Two suppressions keep the
entry pointing at something workable:

- A `panel_num` past the page's panel count is ignored when taking the maximum,
  so one group claiming panel 99 does not invent 90-odd missing panels. In the
  corpus this never bites (0 pages), but `panel_num_out_of_range` exists, so the
  two checks should not report the same group twice.
- A page holding any unassigned (-1) group is skipped. That group's text may be
  the missing panel's, so the hole restates `panel_unassigned` /
  `panel_num_fixable` and clears itself once those are worked. 34 of 454.

Corpus: **416 page/engine entries**, ~3.9% of the 10,716 prelim files.

One entry per page/engine. The finding is about a panel holding *no* group, so
there is nothing in it to anchor to; the entry is anchored on the first group —
in reading order — of the next panel that does have one, that being the nearest
thing an editor can open. `panel_num` on the entry is therefore the **empty**
panel, not the anchor group's own. On every other issue the two are the same
panel, and printing the anchor's made the line name a group in panel 4 while
complaining about panel 3 with nothing saying why (vol 21 page 63 is the case
that showed it up). The note now names the anchor's panel too, so the two
numbers on the line are never silently different.

### Verifying one in the editor

The panel the issue is about holds no group, so Prev/Next cannot reach it — they
step through groups, and the nearest one back is in the panel *before* the hole.
So on a `panel_nums_not_contiguous` queue entry the editor widens its crop to
span the empty panel(s) as well as the anchor's, outlining them in amber with
their real panel numbers (the existing teal overlay numbers by list position,
which would label panel 3 as "1" when drawing a subset). The verification is
"is that panel really wordless?", and it is a two-second look once it is on
screen.

Scoped so nothing else changes: only while the current queue entry is one of
these, only for the contiguous run of empty panels ending at `panel_num - 1`,
and computed from each pane's own groups so a one-engine hole widens only that
pane. Navigate away with Prev/Next and the ordinary crop comes back.

`panels_with_no_groups` lives in `utils/group_checks.py` for this — `ocr_check`
and the editor must agree on which panels are empty, and a second copy of the
arithmetic drifting from the first would point the reviewer at the wrong panel.

### Acknowledging one

`panel-has-no-text` in the `group_checks` registry, set from the editor's
"Mark OK" popup — the reviewer's "that skipped panel really is wordless". It has
no predicate (`_never_fires`, like `text-will-never-fit` and `florence-check`):
`ocr_check` decides when the issue fires and reads the acknowledgement itself,
because the judgement needs the whole page and its panel boxes, which a
predicate over one group cannot see.

Two things follow from there being no group in the skipped panel to mark:

- **It is anchor-bound.** It is stored on, and read back off, the anchor group.
  Delete or add a group, the ids shift, the anchor may become a different group,
  and the acknowledgement stops being found. The issue re-fires — the safe
  direction to fail in, but it does mean these do not survive heavy editing.
- **It is per page/engine, not per panel.** A page skipping two panels is one
  issue naming both, so one acknowledgement covers both, including a panel that
  later turns out to have had lettering.

The name deliberately differs from the queue type `panel_nums_not_contiguous`,
so the popup's name-match does not pre-tick it. Same reasoning as
`text-will-never-fit`: a reflexive Save must not dismiss a finding nobody looked
at, and looking at the panel is the entire work here.

**It ranks last in the `panel_num` block on purpose, because its precision is
low.** A silent panel is legitimate and common, and nothing here can tell one
from a missed group without looking at the art. Three hits spot-checked against
the pages — vol 1 pages 122 panel 5, 139 panel 1 and 140 panel 5 — were all
genuinely wordless. Treat an entry as a prompt to look at the page, not as a
defect; anything the tool has concretely diagnosed about the anchor group
outranks it and takes the queue slot.

---

## `LINE_HEIGHT_OUTLIER_FRACTION = 0.85`, `LINE_HEIGHT_MARGINAL_FRACTION = 0.9`

A group is flagged when `box_h / n_lines` falls below this fraction of the page median.
The heading read `LINE_HEIGHT_OUTLIER_FRACTION = 0.9` until 2026-08-09 — the value the
first sweep below arrived at, left behind when *Two bands* split it into 0.85 and 0.9.

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

### One engine flags it, the other does not: read the denominator

The median is computed **per engine, per page** — `PageLineHeights.own` is the median of
the page as *this* engine boxed it. So an identical group can land on opposite sides of
the bar in the two engines, because the thing that differs is the denominator, not the
group.

**Vol 4 page 046 group 9** is the clean example. The group is the same in both engines
down to the pixel — box `520x116`, three lines, implied line height **38.667** — and
only paddleocr reports `too_many_lines`:

| | easyocr | paddleocr |
|---|---|---|
| g1 `TWENTY-FIVE!...` | 776x87 → 43.50 | 820x109 → **54.50** |
| g11 `WHAT A SYSTEM!` | 378x85 → 42.50 | 415x110 → **55.00** |
| g3 / g6 / g8 | 49.50 / 40.67 / 38.75 | 50.25 / 42.00 / 40.00 |
| **page median** | **41.583** | **46.125** |
| **g9 ratio** | 38.667/41.583 = **0.930** | 38.667/46.125 = **0.838** |

Paddleocr drew every other box on the page looser, and two of them much looser, so its
median rises by 4.5px and g9 crosses the 0.85 bar without changing at all. The small-N
effect above is the amplifier: six measurable groups means the median is the mean of the
3rd and 4th values, so two padded boxes move it directly.

**How to read one.** A one-engine `too_many_lines` is evidence about the *page*, not the
group. Compare the flagged group's box against the other engine's: if they agree and the
two ratios straddle the bar, the fault is loose boxes elsewhere on the page, and
tightening those is the real correction — it clears the flag by fixing what is actually
wrong. Only when the boxes genuinely differ is the flagged group itself the suspect.

**Not a defect to design out.** The metric has to be relative, since absolute line
heights vary by page and volume, and a per-engine reading can only honestly be judged
against its own engine's median — a shared or cross-engine median would import one
engine's boxing errors into the other's page. The cross-engine transplant already
depends on this: `_layout_ok` judges a candidate donor against *its* engine's median
(`line_heights.other`), which is what makes "the donor is well laid out" mean anything.

### `LINE_HEIGHT_BIMODAL_RATIO = 1.2` — when the median measures the wrong lettering

Added 2026-08-15, after vol 3 reported ten `too_many_lines` on one page and every one
of them was wrong.

The section above assumes the page median lands among the body lettering. On a page
carrying **two registers** it does not, and then the check inverts completely — it
flags the correctly wrapped groups and passes the outliers. Vol 3 page 257 (*Silent
Night*) is the clearest case. The carol relayed through the planted loudspeakers is
free-lettered at 69–127px against ordinary dialogue at 41px, and **seven of the twelve
measurable groups are the carol**:

| | | |
|---|---|---|
| g7 41.00 → 0.58 **FLAG** | g3 41.25 → 0.58 **FLAG** | g5 41.40 → 0.59 **FLAG** |
| g10 44.00 → 0.62 **FLAG** | g0 55.00 → 0.78 **FLAG** | g9 69.50 → 0.98 |
| g4 72.00 → 1.02 | g6 74.50 → 1.05 | g12 81.00 → 1.14 |
| g13 103.00 → 1.46 | g1 116.50 → 1.65 | g2 127.00 → 1.80 |

Median 70.75; the page's actual dialogue norm is **41.4**. All five flags are ordinary,
correctly wrapped balloons, in both engines.

It is partly traceable to the vision pass: `g1`, `g2`, `g12` and `g13` carry
`type_was: sound_effect` and were retyped to `dialogue` under the relayed-voice rule,
which dropped them out of `STYLIZED_TYPES` and into the median. Retyping them back is
**not** the fix — the label is right, and it only moves the median to 49.5, leaving
three flags, because `ALL IS CALM/BRIGHT` and one `SILENT NIGHT` were never
`sound_effect`.

**Outlier rejection cannot fix this.** With the contaminating register in the majority,
the median is already inside it, so there is nothing to anchor a rejection rule on. What
separates the two registers is density, not count: body lettering is a fixed printed
size and clusters within a fraction of a pixel (41.0, 41.25, 41.4), while display
lettering is hand-drawn and sprawls. So `_half_sample_mode` recurses on whichever half
of the sorted sample has the smallest range, converging on the tightest cluster — 41.325
here — and `_page_median_line_height` uses it in place of the median when

```
page_median / mode > LINE_HEIGHT_BIMODAL_RATIO
```

**The gate is one-sided on purpose, and that is the entire safety argument.** The check
fires only *below* the reference, so only an inflated reference invents flags. Over all
10,190 corpus pages, substituting the mode unconditionally would add flags on 63 pages —
and **every one of those has the mode above the median** (ratios 0.77–0.98), so a gate
that only replaces an inflated median excludes the lot by construction. Verified against
the shipped function: **26 pages change, 0 gain a flag.**

The threshold sits clear of the noise. Ratio distribution over the corpus:

| ratio | 0.8 | 0.9 | 1.0 | 1.1 | 1.2 | 1.3 | 1.4 | 1.5 | 1.7 | 1.8 | 2.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pages | 6 | 49 | **9,395** | 701 | 18 | 9 | 5 | 2 | 3 | 1 | 1 |

92% of pages sit at 1.0 and never reach the branch. The 1.1 bucket is the shoulder of
ordinary pages, and 1.2 clears it; loosening to 1.15 would add 13 pages for 13 flags,
tightening to 1.25 would drop 5 pages that lose 17 flags between them.

Effect, by volume:

| vol | 3 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 29 | **all** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| before | 10 | 166 | 151 | 123 | 154 | 145 | 145 | 138 | 150 | 66 | **1,307** |
| after | 0 | 155 | 137 | 116 | 140 | 126 | 142 | 132 | 141 | 62 | **1,210** |

**Every manually cleaned volume is untouched** — vols 1–18 and 28 do not appear in that
table at all, which is what says the 0.85 calibration still means what it meant.

The uncleaned volumes reach the same inversion by a different route: not display
lettering but a *majority of loosely drawn boxes* lifting the median off the true
lettering. Vol 26 page 161 flags six groups at 37.0–41.0 against a median of 48.2 while
everything from 55 to 75 passes. That is the "loose boxes elsewhere on the page"
diagnosis of the section above, now made by the estimator instead of by the reviewer —
and the mode lands at 36–38px on vols 23, 24 and 26 alike, matching the body-lettering
norm measured independently on the clean volumes.

Tunable with `--line-height-bimodal`, floored at 1.0 (below that the mode would replace
the median on nearly every page, including the 63 where it would add flags).

### The transplant used to be blocked by the fault it repairs

Where the bimodal guard runs out. `_transplant_line_pattern` accepted a rewrap only if
it was well laid out against the **recipient's own** page median — but on a page where
one engine under-wrapped most of its groups, that median is computed from the very fault
being repaired, and there is no second cluster for the mode to find because the whole
page leans one way.

Vol 21 page 174 is the case. Easyocr has 12 of its 18 groups not fitting; paddleocr has
2, both tiny sound effects. Easyocr's median reads **57.5** against paddleocr's **38.3**
(the guard did fire, pulling it from 72.5 to 57.5 — not nearly enough). Group 1 is one
unwrapped 80-character line whose text matches paddleocr's exactly; the transplant
rebuilds paddleocr's five lines and the result *fits*, but scores 177/5 = 35.4 against
57.5 — ratio 0.62, under the 0.85 threshold — and was thrown away. Vol 21 had **19**
such rewraps rejected and **none** accepted, on pages 174 and 166 (own median 66.0
against 37.05).

So the rewrap is now accepted if it is well laid out against **either** page's median.
Widened rather than swapped to the donor's, because the donor page can be the poisoned
one just as easily. The guard still bites: `_layout_ok`'s fit half is measured against
the recipient's own box either way, so a donor line count that genuinely cannot sit in
this box is still caught.

Corpus, over every group that does not fit and has a well-laid-out donor: 2561 rewraps
were accepted before and still are, **172 are newly accepted**, and 30 are still refused
— 8 too tight by both medians and 22 that still do not fit. A widening of 6.7%, not a
rubber stamp.

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

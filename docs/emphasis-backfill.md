# OUTSTANDING: the emphasis backfill

**Status: NOT DONE. Opened 2026-09-22.** A full-corpus re-screen of
`emphasis_markup` is owed, and until it runs the later volumes are known to be
short of bold runs. `scripts/closeout.sh` prints a TODO row on every close-out
while this file says `Status: NOT DONE`; change that line when it is finished
and the row goes away.

## Why it is owed

`scripts/vision/emphasis_candidates.py` shipped with a fixed 1.30 stroke-width
threshold, taken from `allbold.py`'s *"confirm anything under about 1.3x with a
crop"*. That sentence is a **confidence** line, not a detection floor. Measured
over 3,261 word ratios the distribution is cleanly bimodal — plain lettering
masses at 0.90–1.10, a trough at 1.10–1.20, and bold rises from 1.20 and peaks
at **1.30–1.35** — so the cut sat inside the bold peak.

The same 1.30 has been in `allbold.py`'s docstring since it entered the repo
(2026-09-02) and in the `vision-tools` original before that, so **every pass
that consulted it is suspect**, not just the one that used the generator.

Fixed at source on 2026-09-22: the tool now splits each group at the widest gap
in its own sorted ratios, because `allbold` reports every word against its OWN
GROUP's baseline and a balloon that is mostly bold compresses all of them.

## What is NOT wrong, so nobody re-opens it

**The low rates in the early volumes are correct.** Emphasis density tracks the
volume, not the reading date — the passes simply ran chronologically:

| vol | runs/speech group | | vol | runs/speech group |
|---|---|---|---|---|
| 1 | 0.10 | | 12 | 0.60 |
| 2 | 0.20 | | 14 | 0.84 |
| 3 | 0.33 | | 16 | 0.88 |
| 5 | 0.34 | | 19 | 0.61 |
| 8 | 0.38 | | 21 | 0.62 |
| 10 | 0.48 | | 22 | 0.85 |

Barks' letterer used the bold-italic face more and more over the years. Checked
directly: *Farragut the Falcon* (Vol. 2, 1944) records **zero** bold runs over
121 speech groups, which is the worst block in the corpus — and five of its
balloons cropped at 2.2x (`COCKADOODLE DOO!`, `NOW FARRAGUT'S HEADED FOR THE
RIVER!`, `THERE'S A FALCON DIVING NOW!` and two more) carry **no bold at all**.
That zero is right. Every page carries the `inline-emphasis` capture rule and
all but 10 are prompt version 6, so this is not a late-arriving feature either.

## The size of it, measured

| title | vol | stored | detector finds | flagged lines uncropped |
|---|---|---|---|---|
| Land of the Pygmy Indians | 16 | 227 | 254 (+12%) | 75 |
| Forbidden Valley | 19 | 187 | 258 (+38%) | 58 |

And the flagged lines are where most of it hides: on *The Prize of Pizarro* the
47 of them yielded **12 more runs and 4 places already marked WRONG**. At that
rate those 75 and 58 are worth roughly another 20 and 15, so the real shortfall
is about **20% for Vol. 16 and 45% for Vol. 19**.

Corrected in full on 2026-09-22, for calibration: *The Prize of Pizarro*
129 → 205 runs, *The Lovelorn Fireman* 33 → 71.

**Vols. 12–22 hold ~22,000 speech groups.** A 15–40% shortfall there is on the
order of **2,000–5,000 missing runs**. Vols. 1–3 hold little emphasis and are
not worth the compute.

## How to run it

Per title, no corpus writes and no image tokens:

```bash
uv run --offline barks-ocr-vision-prep --title "<title>"
D=~/barks-vision/<slug>
uv run --offline python scripts/vision/dump_boxes.py "<title>" $D/bx.json
uv run --offline python scripts/vision/panel_boxes.py $D > $D/boxes.txt   # REQUIRED
VISION_OUT_DIR=$D uv run --offline python scripts/vision/allbold.py > raw.txt
uv run --offline python scripts/vision/emphasis_candidates.py raw.txt $D
```

`boxes.txt` is not optional: `allbold` reports PANEL x while `text_box` is PAGE
x, and without it the balloon-outline filter silently does nothing. Then diff
the run count against the stored `ai_text` and rank the titles by shortfall.

A prep is ~30s and ~70MB of crops, so plan the disk: 200 titles is well over
10GB if they are kept. Delete each out-dir once its numbers are recorded.

## Three things that will bite whoever does it

- **THE DETECTOR OVER-CALLS ON LOW-EMPHASIS TITLES.** On *Farragut the Falcon*
  it proposed `DOO`, `NOW` and `THERE'S`, none of which are bold: `DOO!` is a
  single-blob line with nothing to compare against, `NOW` sits at 1.17, and
  `THERE'S` is a 33px blob that is probably an apostrophe. **It is a screen. A
  title's numbers are an upper bound until the balloons are cropped.**
- **THE `??` LINES NEED CROPS AND THEY ARE WHERE THE MISSES ARE.** `allbold`
  flags a line whose blob count disagrees with its word count; the generator
  prints those unmarked. Skipping them is how the first pass lost twenty runs it
  had already reasoned out. 47 balloons stack into eight images at 2x.
- **CLEARING A TAG NEEDS THE UNTAGGED TEXT SENT EXPLICITLY.** An absent
  `emphasis_markup` means "this run said nothing about emphasis", so it KEEPS
  what is stored — popping the key does not remove a tag. And `vision_mirror`
  does not carry a removal to the other engine, so a cleared group needs the
  paddleocr side done by hand.

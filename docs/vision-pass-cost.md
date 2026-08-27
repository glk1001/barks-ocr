# What a vision-pass page is allowed to cost

The reading rules live in `vision_schema.py`, which generates `roster.txt`. The
procedure lives in the `vision-pass` skill. **This file is the third thing:
how much looking a page is worth.**

It exists because on 2026-08-19 a three-title batch cost 9.4 images per page
against a fourteen-session median of 4.9 and a best of 2.1 — and came back
*less* accurate than the cheapest run in the set.

## The number that settles the trade-off

The reviewer's stated tolerance, 2026-08-23: **about 10% wrong on nephew cap
calls is fine.** Every panel is reviewed anyway, so one fix in ten is cheaper
for a human than a pass that looks at everything.

Measured on the batch that prompted this file — *Donald's Posy Patch*, *Donald
Mines His Own Business*, *Magical Misery*, 393 groups:

```
speaker corrections                17 / 393  =  4.3%   whole batch
    of which in the nephew domain  16 / 174  =  9.2%   Huey/Dewey/Louie/nephews
```

Measured again on the 2026-08-25 batch — *Christmas on Bear Mountain*, *The
Terrible Turkey*, *Wintertime Wager*, 532 groups:

```
speaker corrections                22 / 532  =  4.1%   whole batch
    of which in the nephew domain  18 / 197  =  9.1%   Huey/Dewey/Louie/nephews
images read                        56 / 40 pages = 1.40 per page
```

The batch average holds, but it is carried by one twenty-page title whose caps
are off indoors for seventeen of its pages. Split by title the nephew domain
runs **6.5% / 12.8% / 12.0%** — the two ten-page titles, where the caps actually
print, both went over. Where the caps are readable the error is roughly double
the batch figure, and the corrections there were not close calls: they were caps
already measured into the note and then not used. That is a reading discipline
to fix, not an image budget to raise.

Measured again on the 2026-08-25 batch — *Watching the Watchman*, *Darkest
Africa*, *Wired*, 567 groups:

```
speaker corrections                24 / 567  =  4.2%   whole batch
    of which in the nephew domain  21 / 187  = 11.2%   Huey/Dewey/Louie/nephews
images read                        63 / 42 pages = 1.50 per page
```

Split by title the nephew domain runs **14.0% / 15.5% / 0.0%**, and the spread is
the whole story. *Wired* returned **0 corrections in 144 groups** because the
story has no cap key at all — bare heads, then identical red messenger caps on
all four ducks — so there was nothing to get wrong and the collective was forced
rather than chosen. *Darkest Africa* is not a cap problem either: 12 of its 15
corrections are **Donald against nephew under identical pith helmets**, which no
cap rule addresses.

The lesson for the budget is that the nephew percentage is only meaningful where
caps actually print. Where they do not, the number to watch is whether Donald can
be told from a boy — and the cheapest discriminator there is not an image at all,
it is a `capscan` for his red bow tie, which survives under any hat.

**9.2% is already at tolerance.** Accuracy is therefore *not* the binding
constraint, and has not been for some time. Cost is. Every rule below trades
looking for money at an exchange rate the reviewer has said they will take.

The corollary is the part that is easy to get wrong: **do not spend images
buying accuracy you have already been told is unnecessary.** A crop that moves
the nephew error from 9% to 8% is a bad trade. A crop that stops a whole page
being mis-attributed is still a good one.

Measured again on the 2026-08-25 batch — *Going Ape*, *The Old Castle's Secret*,
*Spoil the Rod*, 664 groups:

```
speaker corrections                22 / 664  =  3.3%   whole batch
    of which in the nephew domain  17 / 291  =  5.8%   Huey/Dewey/Louie/nephews
images read                        58 / 52 pages = 1.12 per page
```

Split by title the whole-title rate runs **4.8% / 3.9% / 0.0%**, and the cheapest
title was also the most accurate. *Spoil the Rod* returned **0 corrections in 129
groups** for the opposite reason to *Wired*'s zero: not because nothing could be
read, but because the story **hands each boy a distinguishing project** — one is
inventing, one painting, one learning navigation — and then names him by it in
the dialogue two pages later. Cap, tail and dialogue all agreed on every one of
its ten named calls, and it cost 1.10 images per page.

The batch's own error class was not caps at all. Six of *The Old Castle's
Secret*'s sixteen corrections were **lines given to Donald or Scrooge that belong
to the boys**, every one resting on an adult head span estimated by eye while the
boys' spans in the same panel came measured from `caphead`. An adult's span costs
one `heads2.py` call and the tool is already open; not making it turned a free
measurement into the batch's largest single fault.

Cost held at **1.12 per page against a target of 3**, the lowest of the four
batches measured here, on the largest page count. Nothing was traded for it: the
correction rate is also the lowest of the four.

Measured again on the 2026-08-27 batch — *The Sunken Yacht*, *Race to the South
Seas!*, *Managing the Echo System*, 613 groups:

```
speaker corrections                60 / 613  =  9.8%   whole batch
    of which in the nephew domain  51 / 208  = 24.5%   Huey/Dewey/Louie/nephews
images read                        76 / 42 pages = 1.81 per page
```

The batch figure is the worst recorded here and the cost is among the lowest, so
it is worth being precise about what the 60 are. **None of them is a nephew
misidentified.** All 25 names the pass proposed survived review — every one made
by reading a cap hex off the art and bracketing it against a balloon. Sorted by
what actually went wrong:

```
24  wrong character         Donald against a nephew, almost entirely
23  under-named             `nephews` the review sharpened to a name
13  given to nobody         `none` on a noise a character was making
 0  nephew misidentified
```

Only the first is an error of reading. The second is the pass declining a call
the art supported; the third is a field misuse, thirteen instances of one
mistake. Split by title the whole-title rate runs **0.7% / 8.7% / 21.1%**, and
the spread is the finding.

*The Sunken Yacht* returned **1 correction in 143 — 0 of 140 high-confidence
calls** — the best result in this file. It is the title whose nephews wear plain
undyed sailor caps, so every nephew call was forced to the collective and there
was nothing to get wrong. Compare *Wired*'s zero above: the same mechanism.

*Managing the Echo System* returned 21.1%, and 31 of its 31 corrections are the
second and third classes above — 18 collectives sharpened, 13 noises handed to
nobody. Its caps read on 36 groups and every name held. A title can therefore
post the worst rate in the batch without a single wrong identification.

**The binding constraint is no longer accuracy per image, it is confidence
calibration.** Across the batch:

```
high     45 / 549  =  8.2%
medium   13 /  55  = 23.6%
low       1 /   3  = 33.3%
```

Medium is three times worse than high, and was five times worse on the one title
where it was used at scale — matching the 31% against 7.3% recorded on the
2026-08-19 batch. Medium is not "slightly less sure": it is where nearly all the
readable-page error lives, and it is almost entirely one guess, the long-shot
Donald-against-nephew. **A medium call costs the reviewer exactly the same
keystroke as a wrong high one and tells them nothing extra.** The cheap fix is
not an image — it is a better default: on a long shot with no figure drawn at
readable size, the line is Donald's unless it is addressed *to* him. That single
rule accounts for 15 of this batch's 24 wrong-character corrections.

The corollary for this file: **no image would have prevented any of the 60.**
The wrong-character ones were long shots with nothing to enlarge; the
under-named ones were caps the pass had already measured into its own notes and
then declined to use; the `none` ones were a rule misread, not a picture
misread. Cost held at 1.81 per page against a target of 3 and buying more would
have changed nothing.

## Images do not buy accuracy

Fourteen vision sessions, from the Claude Code transcripts, joined to runs by
the `vision-apply --out-dir` slug with page counts from the `result.json` files
on disk. `read` is images actually sent to the model.

```
img/pg date       pages  read   out_k/pg   turns/pg
   2.1 2026-08-17    28    60       27.6       19.1
   2.3 2026-08-17    48   110       13.9       13.5
   2.5 2026-08-18    28    71       17.4       15.2
   2.7 2026-08-19    51   136       18.4       14.5     <- 2.1% corrections
   3.2 2026-08-17    10    32       26.0       25.8
   3.8 2026-08-14    10    38       39.1       34.2
   4.9 2026-08-14    30   146       25.0       20.2     <- median
   5.0 2026-08-13    10    50       36.7       27.7
   5.4 2026-08-18    30   163       23.4       24.3
   6.8 2026-08-12    29   196       26.6       21.8
   7.8 2026-08-12    18   140       43.3       36.1
   8.9 2026-08-12    31   276       25.7       23.7
   9.0 2026-08-18    10    90       59.6       54.5
   9.4 2026-08-19    27   255       19.8       29.4     <- 4.3% corrections
```

The cheapest run in the set had the best correction rate and the dearest had
twice the errors. Different titles differ in difficulty and this is not a
controlled comparison — but it is enough to kill the claim that looking harder
reads better.

There is a mechanism behind that, not just noise. On the 9.4 run, **13 of the
17 corrections were calls made at `high` confidence and only 4 of 21 `medium`
calls were wrong.** The crops were not being spent on the calls that were
actually in doubt. They were being spent to put a pixel margin into a note on
calls already believed — and four of the five name swaps quoted a margin
measured against the wrong landmark (see the head-span rule in `roster.txt`).
Precision theatre: expensive, and wrong in the same direction as the cheap
answer would have been.

## The budget

**Target 3 images read per page. Treat 5 as the ceiling for a cap-dense title
and say so in the report if you go over.**

Per page, in order:

1. **One montage of every panel** (`montage.py <page-dir> out.png 250`). This
   is the default view and for most pages it is the only one. Bold, balloon
   shape, who is in frame, whether anyone wears a cap at all — all legible at
   250px.
2. **One whole-panel view at 0.55–0.62x**, only for a panel that has **two or
   more figures who could be speaking AND at least one readable cap**. If no
   cap in the panel prints red, blue or the story's green, the answer is
   `nephews` whichever head the tail lands on, and the view buys nothing.
3. **A crop**, only when the tips are within a head-width of each other and a
   name still hangs on it. 1.3–2.2x to separate tails; 3x+ only for a letter.

Read the prep's own `page.png` and `panel-NN.png` **straight off disk** rather
than manufacturing a scaled copy. The good sessions did: the 51-page run read
136 images off ~25 helper invocations. The 9.4 run generated 229. Each
manufactured crop costs a Bash turn *and* an image read, and then sits in
context for the rest of the session.

## What to stop looking at

These accounted for most of the overspend on the 2026-08-19 batch. None of them
can change an answer.

- **Helmets, bee veils, silhouettes, bare heads.** No cap ink means no name.
  Establish it once from the scan — `capscan.py` reports every blob and its
  hex — and write `nephews` without opening the panel. Whole pages of *Posy
  Patch* are GI helmets and bee veils; whole pages of *Magical Misery* are
  bare-headed indoors.
- **Tail positions on a group that is already `nephews`.** Do not crop to put
  "the tip is 40px past his head" into the note of a collective. The number
  cannot be acted on and the reviewer does not read it.
- **Bold, one balloon at a time.** Read weight off the montage. Emphasis errors
  are cheap — the markup is right there in the queue — and a wrong `[b]` has
  never cost a correction.
- **Re-crops after a coordinate miss.** Roughly eight crops on the 2026-08-19
  batch were re-dos because a panel coordinate was estimated off a 0.6x view.
  Scale from the scan's blob boxes, which are already in panel pixels, not from
  a view you are eyeballing.

## What is still worth an image

- The **cap-reference panel**, once per title, before page 1. Getting the
  palette wrong costs a rewrite of every page read before it.
- A panel where **two or more caps print and a name hangs on which tail is
  whose**. This is the one case where a crop earns its cost.
- Anything where the **type** is in doubt on the drawing — cloud edge plus
  bubble trail against a pointed tail. Cheap to check, and a type correction
  travels to both engines.

## Report the cost

Say the image count and the per-page rate in the close-out, next to the
correction counts. It is the only way the next run knows whether the budget
held, and the number is free to collect:

```bash
ls <scratchpad>/*.png | wc -l          # generated
```

Images read has to be counted from the session transcript; the census script
used to build the table above is worth keeping if this needs auditing again.

## Related

- `vision-pass` skill — the procedure and its traps
- `roster.txt` (generated from `vision_schema.py`) — the reading rules
- `docs/vision-pass-run-prompt.md` — the per-batch review findings

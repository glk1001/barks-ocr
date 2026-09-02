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

1. **One montage of every panel**
   (`uv run --offline python scripts/vision/montage.py <page-dir> out.png 250`). This
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
  Establish it once from the scan — `scripts/vision/capscan.py` reports every blob and its
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

Measured again on *Voodoo Hoodoo* (Vol. 7, 32 pages, 402 groups), the first
title in this file whose caps print as a **black crown carrying one coloured
wedge** rather than a full coloured crown:

```
speaker corrections            30 / 402  =  7.5%
cap colours overturned         15 / 402          (previous batch: 0 / 613)
images read                    74 / 32 pages = 2.31 per page
```

The cost went **up** from 1.81 to 2.31 and the correction rate went **down**
from 9.8% to 7.5%, which is the first batch where spending more helped. But
the composition changed in a way the previous entry did not predict:

```
 9  under-named          `nephews` the review sharpened to a name
 8  wrong nephew         Huey/Dewey/Louie swapped for each other
 4  over-named           a name the review withdrew to `nephews`
 4  -> Donald
 5  adults / other
```

The previous batch recorded **zero nephews misidentified in 613 groups** and
**zero cap colours overturned**. This one posts 8 and 15. Every call in it was
high confidence, so confidence was not the discriminator — **cap area was**. A
wedge contributes 130-1800px against a crown that reads achromatic, and
scenery in the same inks (red curtains, red brick, an armchair, Scrooge's
green collar) sits at head height all through the title.

Two mechanisms, both verified against the art afterwards:

- **Reading two balloons as joined.** On 100 p7 the pass wrote "joined along a
  shared edge, one tail between them" and gave both balloons to one boy. They
  are two balloons with two tails. That single call cost one wrong name and
  one name never made, and the same slide on 100 p6 shifted the rest of the
  panel by one. A "joined" call is a claim about the drawing and needs a crop
  of the neck, exactly as a tail does.
- **Naming off a sliver seen at contact-sheet scale.** The 15 colour moves have
  no direction — red->blue x3, red->green x2, blue->green x2, green->blue,
  blue->red — which is noise, not bias. Under a few hundred saturated pixels,
  probe the head and crop that one cap at 4-6x before writing the colour down.

The corollary is **not** to decline more. Under-naming still outnumbers
over-naming 9 to 4, and on 090 p8 a boy whose crown probes with no chromatic
ink at any zoom was named by the review and held through two rechecks. The
wedge is for **checking** a name, not for licensing one; when it will not read,
fall back to the tail and the scene rather than to the collective.

Cheap wins that did hold: `scripts/vision/probe.py` (new here) settled every
"is there ink on this head at all" question in-process for nothing, and
stitching 2-5 crops into one contact sheet meant 74 image reads carried roughly
three times that many crops.

Measured again on the 2026-08-31 batch — *New Toys*, *Donald's Love Letters*,
*Rip Van Donald* (Vol. 8, 28 pages, 361 groups), all three fully reviewed on
both engines:

```
speaker corrections                29 / 361  =  8.0%   whole batch
    of which in the nephew domain  27 / 159  = 17.0%   Huey/Dewey/Louie/nephews
images read                        44 / 28 pages = 1.57 per page
by title                     14.8% / 1.9% / 6.7%
```

Cost is not the story here — 1.57 against a target of 3, and the cheapest title
was also the most accurate. **The error has one cause and it is a refusal to
spend an image.** Seventeen of the 29 are under-namings, and **twelve of those
sit on panels the pass declared bare or unreadable off a census zero without
cropping**: *New Toys* 104 and 105, where the note reads *"heads2 finds no roster
ink on any nephew head in panels 1-8"*, and *Rip Van Donald* 154 p1 (figures in
shadow), 155 p2 (a flat silhouette panel) and 159 p2 (a green cap the census
merged into foliage one hue-degree away).

Everything that WAS cropped survived: **32 red, 22 blue and 21 green cap colours
untouched**, and the only colour overturned in the batch, 153 g3, is the one
where the census had merged the tab into a hedge of the same ink. So the rule in
*What to stop looking at* — establish a bare head once from the scan and move on
— has a hard boundary. It holds for a title with **no cap key at all** (*Wired*,
*The Sunken Yacht*, and here *New Toys* 099, where the boys are plainly
bare-headed at 1.6x). It does **not** hold for a title whose cap is a 130-400px
sliver that alternates on and off: there a whole-page zero is a reason to spend
one tiled crop of the three heads, not a verdict. One image on *New Toys* 104
would have converted eight collectives into names.

Two things worth carrying forward. **Every one of the batch's 20 medium calls was
confirmed at high with no change of value** — medium used for *thin evidence
behind a believed value* (a tip stopping short, an elimination, a balloon with no
tail) is a useful provenance marker, not the coin flip it was in Vol. 7, where it
carried the long-shot Donald guess. And **tiling still pays**: 44 image reads
carried about 110 separate crops, and the two spent fixing the palette per title
were the best-value images in the batch.

Measured again on the 2026-08-31 review of *Trail of the Unicorn* (Vol. 8, 24
pages, 278 groups), one title read on its own:

```
speaker corrections                14 / 278  =  5.0%
    of which in the nephew domain  12 /  57  = 21.1%   Huey/Dewey/Louie/nephews
images read                        51 / 24 pages = 2.13 per page
cap colours: 33 of 38 survived, 5 overturned
medium: 17 of 21 held, 4 reversed
```

The cost went up from 1.57 to 2.13 and the whole-title rate came down from 8.0%
to 5.0%, which is what the previous entry asked for: the spend went on the thing
that batch identified. **Every page called bare or unreadable was cropped
first** - 007, 029 p5, and the flat two-colour silhouette panels where `capscan`
returns one background field and nothing else - and none of those calls was
overturned. The `heads2`-zero error class from the previous batch does not
appear here at all.

Where the 14 went instead:

```
 4  Donald against a nephew      two of them Donald wearing the roster colour
 3  over-named                   a name the review withdrew to `nephews`
 2  wrong nephew                 one swapped pair, from a crossing I invented
 2  chorus                       `other:Donald and the nephews`, see the memory
 2  silhouette guesses           Donald<->nephews, both directions, both wrong
 1  caption voice                a quoted caption stays `narrator`
```

None of these is an image the pass declined to spend. Two were a cap probe
overruling a beak I had already read correctly, and two were guesses on
all-silhouette panels where no image could have helped. The lesson for the
budget is the same as 2026-08-27's: at 2.13 per page against a target of 3,
cost is not what is limiting this.

Measured again on the 2026-09-01 batch — *Land of the Totem Poles*, *Serum to
Codfish Cove* (Vol. 8) and *In Ancient Persia* (Vol. 9), 58 pages, 735 groups,
all three fully reviewed on both engines:

```
speaker corrections                68 / 735  =  9.3%   whole batch
    of which in the nephew domain  44 / 268  = 16.4%   Huey/Dewey/Louie/nephews
images read                       164 / 58 pages = 2.83 per page
cap colours overturned             23
by title                     6.6% / 8.7% / 12.1%
```

Cost went up from *Trail of the Unicorn*'s 2.13 to 2.83 and the rate went the
wrong way, 5.0% to 9.3%. **The extra spend was not wasted — it was spent on the
wrong half of the page.** Sorted by what actually went wrong:

```
22  under-named          `nephews` the review sharpened to a name
17  wrong nephew         Huey/Dewey/Louie swapped for each other
16  Donald against another
 5  over-named           a name the review withdrew to `nephews`
 8  adults / other / none
```

The previous batch's lesson was *crop the pages you would otherwise call bare*,
and that held: **not one page called bare or unreadable was overturned**, and
under-naming fell from 17-of-29 to 22-of-68 as a share. What replaced it is
**wrong nephew, up from 2 to 17**, and it is concentrated in the one title with
the biggest, most legible caps in the corpus so far. *In Ancient Persia* posts 11
wrong-nephew swaps and 13 overturned colours; the two Vol. 8 titles, whose caps
are a small sliver, post 6 and 10 between them.

That inversion is the finding. **A cap that is legible at contact-sheet scale
invites you to name it from the contact sheet, and the Vol. 9 band is exactly
big enough to do that with.** The Vol. 8 sliver is so small it forces a crop and
the crop gets it right; the Vol. 9 band looks readable in the montage and is not.
The colour moves have no direction — red->green, green->red, red->blue,
blue->red, blue->green, green->blue — which is the Vol. 7 noise signature, not a
bias. **Size of cap is not the discriminator. Size of the image you read it in
is.**

One cheap habit came out badly enough to name. On 060 p6 all three crowns were
probed in-process, two came back greenish, and the third was assigned *by
elimination* — the review overturned it. `probe.py` tells you what ink is on a
head; it cannot tell you that the panel holds three different boys. Elimination
across a panel is a claim about who is in it, and needs the same crop a tail
does.

What did work, all of it cheap: the beak-before-cap rule (16 Donald corrections
and not one of them a capscan overruling a beak the way Vol. 8's did), flagging
an art-vs-dialogue conflict rather than silently picking (045 g2 went to the
reviewer's reading, 044 g4 held at mine), and marking a genuinely undecidable
pair medium instead of guessing (the 052-055 costume collision, where all four
corrections landed on flagged groups). Medium was 46 calls across the batch and
every one was resolved rather than left; **0 of 46 survived as medium**, which is
what medium is for.

Measured again on the 2026-09-01 batch — *Wild about Flowers* (10 pages) and
*Vacation Time* (33 pages), both Vol. 9, 43 pages, 440 groups, both reviewed
the next day:

```
speaker corrections                19 / 440  =  4.3%   whole batch
    of which in the nephew domain  16 / 113  = 14.2%   Huey/Dewey/Louie/nephews
images read                        84 / 43 pages = 1.95 per page
cap colours: 76 of 85 survived, 9 overturned
by title                     2.6% / 4.9%
high 16/416 = 3.8%   medium 3/24 = 12.5%   (0 survived as medium)
```

Cost came down from the previous batch's 2.83 to **1.95** and the rate came down
with it, 9.3% to 4.3%. That is not a trade — it is the previous entry's own
prescription working. The 2.83 run was spending images to *see* the Vol. 9 cap
and then naming it from the montage anyway; here every nephew name was cropped
or probed, and the extra looking was cheaper because it was aimed.

Three habits carried the reduction, all of them free:

- **Hue arithmetic instead of a second image.** These are forest stories and the
  background green (`#009e49`, H148) sits directly behind the crowns, one
  degree-band away from the cap green (`#4da33f`, H112). `probe.py` separates
  them for nothing, and doing that first meant a crop was only ever spent on a
  crown that had already shown chromatic ink.
- **Tiling by panel rather than by page.** 84 images carried about 130 separate
  crops. The binding constraint on a contact sheet is that the long side must
  stay under ~1500px or the whole sheet is downsampled and the magnification is
  thrown away — three 2.5x crowns fit; three whole panels at 2.5x do not.
- **Reading the montage for layout and nothing else.** Who is in frame, how many
  balloons, which panels are silhouettes. Every name came from a crop, a probe
  or `tailtip.py`.

The one image class that did not pay: the first cap sheet on the reference panel
of *Wild about Flowers* (029) was cropped too tight and had to be re-shot wider.
Crop the head **and the shoulders** on a reference panel — a crown alone gives
no scale and no neighbour to rank against.

What the 19 corrections were, and none of them is an image that was declined:

```
 6  wrong nephew          Huey/Dewey/Louie swapped for each other
 4  Donald -> a nephew    3 of them off-panel lines in a monologue stretch
 3  under-named           `nephews` the review sharpened to a name
 2  a nephew -> Donald
 4  other / none / over-named
```

The 4 `Donald -> nephews` are the finding. All three off-panel ones sit in the
drive sequence, where Donald has been narrating for four pages and the panel
holds nothing but scenery; the pass gave him the next line by momentum. That is
a reasoning default, not a resolution problem.

Measured again on the 2026-09-02 review of *The Magic Hourglass* (Vol. 9, 28
pages, 339 groups), the first of a two-title batch:

```
speaker corrections                27 / 339  =  8.0%
    of which in the nephew domain  26 /  70  = 37.1%   Huey/Dewey/Louie/nephews
images read                        49 / 28 pages = 1.75 per page
high 25/310 = 8.1%   medium 2/29 = 6.9%
```

Cost held and the rate did not, and the 27 have one cause: **nine are
`Donald` -> a boy on ducks whose crown the pass never probed**, because the
figure was big, alone or at the front of a line. Vol. 9 prints Donald's hat
in the cap blue, so the census cannot separate him from Dewey; a red or green
line can, and four of the nine came back red. The probe is free and was not
run. Two more went the other way (a "boy" with 503px of blue was Donald).
No image was declined on any of them.

And on the second title of the batch, *Big-Top Bedlam* (Vol. 9, 28 pages, 303
groups), reviewed the same day:

```
speaker corrections                21 / 303  =  6.9%
    of which in the nephew domain  12 /  63  = 19.0%   Huey/Dewey/Louie/nephews
images read                        38 / 28 pages = 1.36 per page
high 16/265 = 6.0%   medium 5/38 = 13.2%
batch                              48 / 642  =  7.5%   at 1.55 images per page
```

Nine of the twelve are Dewey and Louie exchanged on crowns whose ink the pass
had measured, which is a palette question for the next Vol. 9 title, not an
image that was declined. The rest are costume names in a quick-change plot.

Measured again on the 2026-09-02 batch -- *You Can't Guess!* (Vol. 9, 25
pages), *Dangerous Disguise* and *No Such Varmint* (Vol. 10, 28 pages each),
81 pages, 1015 groups; only the first reviewed so far:

```
speaker corrections  (You Can't Guess!)   12 / 357  =  3.4%   after excluding
                                                              6 reviewer-added
                                                              plate groups
    of which in the nephew domain         12 / 114  = 10.5%
images read                              109 / 81 pages = 1.35 per page
    by title                              41/25 = 1.64, 37/28 = 1.32, 31/28 = 1.11
high 11/355 = 3.1%   medium 2/2 = 100%

speaker corrections  (Dangerous Disguise)  25 / 324  =  7.7%   after excluding
                                                              4 reviewer-added
                                                              groups, 1 rename
    of which in the nephew domain         25 /  72  = 34.7%
high 26/316 = 8.2%   medium 2/8 = 25%

speaker corrections  (No Such Varmint)     69 / 335  = 20.6%
    of which in the nephew domain         67 / 184  = 36.4%
    of which collectives named            50
high 58/304 = 19.1%   medium 10/30 = 33.3%
```

*No Such Varmint* posts the worst rate in this file at the lowest cost in this
file, 1.11 images a page, and the two facts are one fact: fifty of its sixty-nine
corrections are collectives the pass declined on a `probe.py` zero, on a title
whose cap is a dozen pixels of ink on one side of a black crown. The reviewer
named every one. The cheapest run is not the best run when the cheapness is
images the page needed: a 3x tiled crop of every speaking boy's head, one image
a page, would have converted most of the fifty and left the title under 2.5.

*Dangerous Disguise* is the worst nephew-domain figure in this file, and 12 of
its 25 are the same mechanism as *New Toys*: a probe zero on a tiny wedge cap
taken as a bare head. The other big class is the sea printing in the wedge
blue, which no census can separate. Both are crops the pass declined, at 1.32
images a page; the title had room for one more per page.

The Vol. 9 title's caps are big winter stocking caps, legible at contact-sheet
scale, and it cost 1.64 a page against 1.75 and 1.36 on the two Vol. 9 titles
before it; the error class is not caps at all but which of two boys a
gap-landing tail belongs to (4 swaps, all the lean, and 5 names withdrawn to
the collective). The two Vol. 10 titles are wedge-cap stories on blue water,
where a `heads.py` census cannot separate the blue wedge from the sea; the
saving there came from probing crowns in-process and cropping only where a
probe found ink, and from reading whole pages as a montage plus a report of
tail tips -- most pages cost exactly one image.

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

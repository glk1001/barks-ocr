# The corpus-run prompt

The prompt that starts a vision pass over the next titles. Recovered from the
session transcripts on 2026-08-09 after it went missing; keep it here rather
than in scrollback.

The procedure lives in the `vision-pass` skill, the reading rules in the
generated `roster.txt`, and the image budget in `docs/vision-pass-cost.md`.
**This file is only the part none of those can supply**: which titles, and what
the last review found.

**The skill now reads this file itself.** `/vision-pass <N>` takes the titles
from `barks-ocr-vision-status --titles --todo` and the findings from the most
recent `### Findings to paste into the next run` section below, so the prompt no
longer has to be written out by hand each time. The template is kept for the
occasions that need one — a batch with an unusual instruction, or a run started
somewhere without the skill.

What still needs a human is the other end of the loop: **after a review, write
the findings back here as a fresh dated section.** Nothing derives those.

## The prompt

```
Run the next <N> corpus titles. Crops are not prepped.

  1. <Title>   (vol <V>, <P> pages, <year>)
  2. <Title>   (vol <V>, <P> pages, <year>)
  3. <Title>   (vol <V>, <P> pages, <year>)

<total> pages, #1-<N> on --todo. Sanity-check any title that looks incomplete
against its zero-group count before re-running it.

The vision-pass skill has the procedure; roster.txt has the reading rules;
docs/vision-pass-cost.md has the image budget. Don't restate any of them
back at me.

COST. Target 3 images read per page, 5 as the ceiling. About 10% wrong on
nephew cap calls is fine -- every panel gets reviewed anyway -- so do NOT
spend images buying accuracy past that. Report the image count and the
per-page rate in the close-out next to the correction counts.

FROM THE LAST REVIEW (<N> corrections over <titles>)
- <what the corrections had in common>
- <the rule the pass broke, stated as a rule>
- <anything that overturned a cap colour — cap_colour_was, not just speaker_was>

Report per title. Stop after applying and building the queues; I'll tell
you when a review is done.
```

Fill the title block from the head of the work list:

```bash
barks-ocr-vision-status --titles --todo | head
```

Add a line when the batch stays inside a volume just done — *"same volume as
the two just done, so the cap palette should carry over"* — because the palette
is fixed per volume from a clean reference panel and re-deriving it is where a
run loses corrections.

## The review block is the whole point

Everything else in this prompt is now carried by the skill. The review findings
are not, and they are what stops the same class of error recurring. Write them
as **rules**, not as a list of what was wrong.

The 2026-08-06 batch is the worked example — 64 corrections over *Too Many
Pets* and *The Hard Loser* reduced to four lines:

- every one was under-naming or mis-attaching a balloon; when a call is wrong,
  suspect the attachment, not the palette
- five also overturned a recorded cap colour, hue right and attached to the
  wrong boy — `cap_colour` is **not** an independent check on the tail, both
  come from the same decision about which boy is which
- seven were a name swapped for another name, all reasoned from monotone tail
  order with large drift; **monotone-with-drift is not evidence** — if the
  drift is large, say `nephews`
- two were animal-vs-duck and went opposite ways, reasoned from the content of
  the noise to the species; read the drawing, not the onomatopoeia

### Findings to paste into the next run (2026-08-12)

17 corrections over *Pecking Order* and *Taming the Rapids*. **15 of the 17 were
collectives the review then named**; only 2 were a call the pass had actually
made. Every hedge held — all 52 medium calls were promoted to high.

- TWO CAPS THAT LOOK ALIKE ARE STILL TWO CAPS. This one family produced 9 of the
  17. Saturation is the discriminator, not blue-against-green: a blue segment
  stays saturated however small, so the muddier of two cool bands is the green.
  Rank the segments against each other inside the panel before calling any of
  them unreadable — with only three inks, a panel carrying a clean red always
  resolves. And if two sampling boxes return the **identical** hex, that is a
  sampling fault, not one ink: real ink on two caps differs by a few counts, so
  crop at 10x and look before concluding anything.
- "GATHERED TAILS" MEANS CONVERGING ON ONE FIGURE. Four names were lost by
  reading two tips ~70px apart, straddling two heads, as a cascade gathering.
  Before invoking the clause, name the single figure both tips land on; if you
  cannot, it does not apply and the tails name one boy each.
- COUNT THE TAILS BEFORE CALLING TWO BALLOONS A JOINED PAIR. Assuming a shared
  tail shifted a whole chain by one and cost two names.
- A NEPHEW'S OWN CAP IN HIS OWN HANDS STILL NAMES HIM. The prop rule is about
  scene property carried across a panel break, not a cap knocked off a head in
  the panel where it came off.

### Findings to paste into the next run (2026-08-12, second batch)

67 speaker corrections over *Days at the Lazy K*, *The Riddle of the Red Hat* and
*Eyes in the Dark* — 538 groups. **61 of the 67 were `nephews` promoted to a
name. Exactly one went the other way.** All 23 medium calls were promoted to
high and none demoted, the second review running to do so.

- A JOINED CASCADE'S LEFT-TO-RIGHT ORDER NAMES THEM. Three joined balloons,
  three tails all leaving the lowest one and fanning one per boy, three readable
  caps: that is one speaker per boy and the shared left-to-right order settles
  which. The pass measured the tips, recorded the caps, wrote *"left-to-right
  would make this one the red cap"* into the note and then recorded `nephews`
  anyway; the review took that mapping every single time. A uniform 50-90px
  offset is fine as long as order and spacing are preserved. `nephews` is for
  tails that genuinely gather on ONE figure, for bare or unreadable caps, and for
  a group whose box spans two balloons with different speakers.
- ON A NIGHT PAGE THE BACKGROUND IS THE SAME BLUE AS A CAP. The one true cap
  misread in 538 groups: a sampling box on a boy at a blue-lit fence returned
  `#01a2d3`, H194 at full saturation, and the pass called it Dewey. That was the
  fence. His band was the muted teal-green behind it. A cap hex that matches the
  panel's background exactly is a sampling fault, not a reading.
- SMALL FIGURES IN FRAME BEAT AN OFF-PANEL ADULT. Three balloons over a wide
  shot with the boys tiny at one edge were given to Donald off-panel; all three
  were nephews. Do not invent an off-panel speaker when the figures are drawn,
  however small.
- LETTERING INSIDE A THOUGHT CLOUD BELONGS TO THE FIGURE DRAWN INSIDE IT. `OINK!`
  in a cloud holding a pig is the pig, not the character whose bubble trail leads
  to the cloud.
- THE TYPE QUEUE ONLY SHOWS WHAT THE PASS TOUCHED. A `ZZZ` the pass corrected was
  re-corrected to `dialogue`; an identical `ZZZZZ` the pass left alone was never
  looked at and still reads `sound_effect`. The two now disagree on the same
  story. Snoring is a voice.

### Findings to paste into the next run (2026-08-13)

11 speaker corrections over *Thug Busters*, *The Great Ski Race* and *The
Firebug* — 552 groups, so **2.0% against the previous batch's 12.5%**. All 59
medium calls were promoted to high and none demoted, the third review running to
do so: the hedging is calibrated, and what is left is in the calls the pass made
confidently.

The batch also split cleanly into two classes, and the second is new.

- STILL UNDER-NAMING, 5 OF THE 11. Three were `?` marks, one hanging over each
  of three boys with clean caps, recorded as `nephews` because nobody utters a
  question mark; the review named all three off the cap beneath. One was a
  silhouette pile where the tail belonged to the tall figure and went to a small
  one — `nephews` where the answer was **Donald**. This rule is now in
  `vision_schema.py`; a device over ONE figure names him.
- A NAME SWAPPED FOR ANOTHER, 6 OF THE 11, AND THIS IS THE NEW ONE. Four were in
  a single pile-up panel — three boys diving on Donald, heads overlapping, tail
  tips within 40px of each other. The pass wrote *"the pile makes the tails
  crowd"* into its own note, hedged to medium, and then assigned by balloon order
  anyway; the review re-mapped all three to a different permutation. Two more
  went the same way in crowded panels, one of them to **Donald**. Order is not
  the tie-breaker when the tails crowd — crop at 6-10x and separate them, or say
  `nephews`. Also in `vision_schema.py` now.
- A COLOURING FAULT DID NOT STOP THE REVIEW NAMING THE BOY. On a panel printing
  two of the three caps in the identical green `#0d9855`, the pass applied "two
  caps the same colour name neither" and recorded `nephews`; the review named the
  left one **Louie**. One data point, so the roster rule stands — but hedge to
  medium and name rather than decline outright.
- THE SPEAKER REVIEW IS NOT THE TYPE REVIEW. Two of the three titles came back
  552/555 on speakers with **all 44 of their type corrections untouched**, while
  the third had every one confirmed. Hand the corrections queue back separately
  and say the count out loud; `vision-corrections --title` is the only thing that
  answers for it.
- DIFF THE ENGINES PER PAGE — IT PAID. On one page paddleocr had never created
  five of easyocr's groups, including three whole balloons. The missed-text audit
  saw two of them (only the two that happened to be in `visible_text`) and
  `vision-mirror` then reported the same five as having no counterpart. The check
  is `scripts/vision/engine_diff.py "Title"`, or bare for the whole corpus.

### Findings to paste into the next run (2026-08-13, third batch)

2 speaker corrections over *Ten-Dollar Dither* — 175 groups, **1.2%**, against
2.0% and 12.5% in the two batches before. All 20 medium calls were promoted to
high and none demoted, the fourth review running to do so. Both corrections were
the same pair in one panel, and both had already been hedged for the right
reason — so what follows is mostly about the close-out, which is where this
title's real damage was.

- TRACE A TAIL FROM THE TIP UP, NOT FROM THE BALLOON DOWN. The two corrections
  were a swapped pair in a panel where two tails **crossed** between the balloons
  and the boys. The pass assigned each tail to the balloon whose edge it seemed
  to leave; at that end both tails pass through the same few dozen pixels, so it
  is a coin flip dressed as a measurement. The tip end is reliable, the origin
  end is not. When two tails cross, left-to-right balloon order beats
  nearest-edge — Barks crosses tails to preserve reading order, not to break it.
- TWO CAPS IN THE IDENTICAL INK STILL NAME THEM. 135 p3 printed two caps the same
  `#0a9e9c`, confirmed over two **disjoint wide** samples (514px and 204px), so it
  was the printing and not a sampling box. The pass named them from the story's
  seating order with the third cap as anchor, at medium, with `cap_colour` left
  **null** so the call was not a tautology — the review promoted both. Do not
  decline to `nephews` for this. A *small* sample matching on two caps is still a
  bad box: crop at 10x and look.
- A CLEAN CAP AND TAIL BEAT A LOOSE THIRD-PERSON LINE. A red-capped boy says
  *"as soon as **Huey** finds another can opener"*. Recorded Huey/red at medium
  with the contradiction written into the note; the review promoted it to high.
  Barks writes the gag before he counts the caps.
- CHECK EVERY REVIEW-ADDED GROUP ON BOTH ENGINES BEFORE MIRRORING. Four groups
  added for missed text produced **five** faults: three arrived carrying the seed
  group's `ai_text`, `notes` and `vision_note` (the boxes were right — it is the
  text that comes across); one was written *into* an existing group and destroyed
  a whole balloon on one engine; one went to one engine only; one was added twice,
  identical in every field. Compare group counts per page **per engine** first,
  then dump each added group beside its seed and flag every byte-identical field.
  The missed-text audit reports zero once a group exists, whatever its text says,
  so it catches none of this.
- THE MISSED-TEXT AUDIT HAS A SECOND BLIND SPOT WORTH SAYING OUT LOUD. It only
  sees `visible_text`, which is non-speech by definition, so a missed *shout* never
  reaches it; and a missed string that already exists as a group elsewhere on the
  page is matched and suppressed. This title had one of each (`OW!` and a second
  `SPLAT`). Report those in prose — the tool will not.

### Findings to paste into the next run (2026-08-13, fourth batch)

18 speaker or cap corrections over *Donald Duck's Best Christmas*, *Silent
Night* and *Donald Tames His Temper* — 459 groups, **3.9%**, against 1.2% for
the batch before. All 41 medium calls were promoted to high and none demoted,
the seventh review running to do so. The rate went up because one panel family
went wrong three times over, not because the hedging drifted.

- **IN A JOINED CLUSTER, DO NOT DECIDE WHICH BALLOON OWNS A TAIL FROM WHERE IT
  LEAVES THE OUTLINE.** 6 of the 18. On 138 p2 the pass traced three tips
  correctly, then attached each to the balloon whose bottom edge the tail hung
  off — and got a clean rotation of the three names. The review used plain
  balloon reading order against the left-to-right tip order and reversed all of
  them. This extends "trace a tail from the tip up": the **tip** tells you the
  figure, **reading order** tells you the balloon. At the origin end the tails of
  a joined cluster all pass through the same few dozen pixels, so an attachment
  that looks unambiguous at 6x is still a coin flip.
- **A FAN THAT DOES NOT REACH EVERY BOY IS THE GATHERED CASE.** 3 of the 18. On
  138 p4 the pass measured three tips, found two landing on one boy and none on
  the third, wrote exactly that into its own note, and named them anyway at
  medium; all three came back `nephews`. The clause is not narrowly "several
  tails converging on one figure" — it is any fan that fails to give one tail per
  boy.
- **`other:everyone` IS THE VALUE FOR A CHORUS OF THE WHOLE PARTY.** 3 of the 18,
  and the pass did not know the value existed. Carol balloons with a spray of
  wavy trails across Donald *and* the boys were given to Donald at medium with a
  note saying it might be the whole party. It is. Do not pick the loudest figure
  out of a group that is plainly singing together.
- **A BARE WHITE DUCK HEAD IS A NEPHEW UNTIL YOU SEE THE CAP AND THE TIE.** The
  figure switching on the electric fan was read as Donald; indoors he still wears
  the sailor cap and the bow tie, and this one had neither. Check for them before
  naming him, especially on a small figure in the middle distance.
- **A CAPTION-SHAPED BOX CAN BELONG TO A FIGURE DRAWN UNDER IT.** *Temper*'s
  closing caption, "ALL QUIET ON OAK STREET…", is the policeman's line, not the
  narrator's. And on the other side of the same coin, 148's framed resolution
  went `none` -> **Donald**: lettering a character composed is theirs, unlike a
  shop sign or a label.

And three things from the close-out, which is where this batch's real damage was:

- **A ONE-ENGINE GROUP CAN PASS BOTH CHECKS.** *Temper* 147 carried a `?` on
  paddleocr only. `engine_diff.py` did not flag it — a single character is too
  short for its filter — and the missed-text audit cannot see a drawn device,
  which is never in `visible_text`. Only comparing group counts **per page per
  engine** found it. Do that first, before the tools.
- **`vision-mirror` repairs that case by itself.** It matched the group on its
  box and copied the reviewed speaker across from the other engine. No hand
  editing, no `added_groups`.
- **SEED RESIDUE HAS MOVED TO THE REASONING FIELDS.** The two groups added on
  *Silent Night* 250 had the right `ai_text` and the right boxes — and carried
  the seed's Gemini `notes` ("This is a thought bubble, indicated by the cloud
  shape", on a book cover), the pass's `vision_note` for an unrelated group
  verbatim, and an `identified_by` on a `none` speaker. Grep the notes, not just
  the text.

One transcription error of the pass's own: *Silent Night* 250's book spine reads
**ANTE BELLUM BROMIDES**, and the pass recorded BROADSIDES in `visible_text` off
the page overview. Crop before transcribing anything into `visible_text`, exactly
as for a `corrected_text`.

### Findings to paste into the next run (2026-08-14, fifth batch)

9 speaker corrections over *Singapore Joe*, *Master Ice Fisher* and *Jet Rescue*
— 468 groups, **1.9%**, against 3.9% for the batch before. All 68 medium calls
were promoted to high and none demoted, the eighth review running to do so.

- **A PANEL THAT PRINTS TWO CAPS IN ONE INK IS STILL AN IDENTIFICATION. 5 of the
  9, and this is the whole story of the batch.** Vol. 3 did it in five panels
  across the three titles — 158 p6 `#13a1cb` on two of three, 171 p5 `#2f9383`,
  175 p3 `#139a7b`, 177 p4 `#0e9649`, 184 p2 `#139c82` — every one confirmed at
  5-6x, so the printing and not a sampling box. The pass declined on three of
  them and the review named **both boys on 158 p6, both on 175 p3, and the one on
  184 p2**. Where the pass instead named them off the panel next door (171 p5 and
  177 p4, both consecutive panels of the same scene with the caps unambiguous
  there), the review kept the call. So the cross-panel chain is the right move and
  the roster's "two nephews printed the same colour tells you nothing about
  either" is about the COLOUR, not about the panel: it retires `cap_colour`, not
  the identification. Look for the chain, and if there is none, name from seating
  order at medium with `cap_colour` null rather than declining.
- **A LINE THAT NAMES A NEPHEW CAN OWN THE NEXT BALLOON.** 159 p4: one boy says
  *"IT'S HUEY, UNCA' DONALD! HE DOES IMITATIONS!"* and the next balloon is the
  imitation itself, delivered by a boy with a clean green cap. The pass recorded
  Louie off the cap and the tail; the review made it **Huey and left `cap_colour`
  green**, a deliberate recorded disagreement. This does not overturn Ten-Dollar
  Dither's "a clean cap and tail beat a loose third-person line" — the difference
  is that this line introduces the speaker of the balloon that follows it, which
  is an identification and not an aside.
- **DO NOT OVERRIDE A MEASURED TIP WITH "ONE TAIL PER BOY".** 168 p1: the pass
  wrote *"the tip at x415 falls inside the red boy's head span"* into its own
  note and then gave the balloon to the next boy along anyway, to keep one tail
  per boy. The review took the tip. Worse, the cap it claimed for that boy was
  read off the panel image and never sampled — a targeted sample returns no
  chromatic pixel on him at all. **Both cap-colour reversals in this batch were on
  caps the pass did not sample**, out of about 135 colour reads that were.
- **THE ONLY OVER-NAMING WAS IN THE CLEANEST PANEL IN THE TITLE.** 176 p3 is *Jet
  Rescue*'s cap-reference panel — three big caps, red green and blue, unmissable —
  and the one call the review sent back to `nephews` was there. A panel being easy
  to read colour in does not make its tails easy to attach.
- **THE ONE-ENGINE GROUPS ARE STILL THE CLOSE-OUT'S REAL WORK.** Five across the
  three titles, all shouts or display lettering: 157 `OW!`, 162 `OWOO!`, 169
  `OW!`, 173 `WHOOM!` (paddleocr only) and 171 `GOODBYE, CRUEL WORLD!` (easyocr
  only, which is why that title mirrors 127 of 128). `engine_diff` caught two of
  the five and the missed-text audit one; **per-page per-engine counts caught all
  five**. Annotate them by hand — but do it BEFORE building the corrections queue,
  not after: the two annotated late on *Singapore Joe* missed that title's queue
  and were still outstanding after the review.
- And the usual straggler: two groups came back unreviewed out of 468, 173 g12 and
  184 g4. Count `speaker_reviewed` on both engines before calling a review done.

### Findings to paste into the next run (2026-08-15, sixth batch)

6 speaker corrections over *Donald's Monster Kite* alone — 129 groups, **4.7%**,
against 1.9% for the batch before. All 7 medium calls were promoted to high and
none demoted, the ninth review running to do so, and 5 of the 7 kept the pass's
name. **5 of the 6 corrections were on one page, 188, and both are attachment
faults in a fan of three balloons over three boys.** One was a vocabulary change.

- **A ROW OF BOYS WITH ONE TAIL EACH IS NAMED BY POSITION OFF ONE READABLE CAP.
  The other caps do not have to print at all.** 188 p2: three nephews strung out
  along a log, a balloon and a tail apiece, and only the leading boy's cap carries
  ink — two red slivers, `#c04828`. The pass scanned the whole panel, found no
  chromatic pixel on the other two, and recorded `nephews` twice. The review named
  them **Louie** and **Dewey** off the leading boy's red and the left-to-right
  order. Re-measured afterwards at every threshold down to S≥0.25: those two cap
  bands really are colourless, both reading the same washed-out olive `#546352`
  H113 S0.17 / `#789371` H108 S0.23. So the naming did not come from colour and
  was never going to. **"No cap ink on this boy" is not a reason to decline when
  the row has one anchor cap and one tail per boy** — that is the same
  left-to-right mapping as a joined cascade, applied to figures instead of
  balloons.
- **WHEN A FAN'S TIPS ARE OFFSET BY ONE BALLOON, READING ORDER WINS — AND THE
  GIVEAWAY IS THE TAIL THAT LANDS ON NOBODY.** 188 p6, 3 of the 6, a clean
  rotation reversed. Three balloons left to right over three boys left to right
  (red `#dd1920`, blue `#19a2b3`, green `#228e54`). The pass measured the tips:
  balloon 2's tip fell inside the red boy's cap span and balloon 3's inside the
  blue boy's, so it assigned 2→Huey, 3→Dewey and gave balloon 1 to Louie by
  elimination — **having written into its own note that balloon 1's tail reaches
  x=373 at head height, which is empty sky over the trees**. The review used plain
  reading order: 1→red, 2→blue, 3→green. Every measured tip was one boy to the
  left of its balloon.
  This does not retire "a measured tip beats one-tail-per-boy" (*Jet Rescue* 168
  p1), it bounds it. Reconciling the two: **if every boy gets exactly one tip, the
  tip is the answer. If the tips are spread out and in order but one boy is
  skipped, the whole attachment is drawing slop and reading order is the answer.
  If the tips converge on ONE figure, decline to `nephews`.** Never resolve the
  leftover balloon by elimination — a fan that fails to reach a boy has already
  told you the tips cannot be trusted individually.
- **THE PASS ONLY EVER SEES ONE ENGINE'S `type`, AND `type_other_engine` DID NOT
  FIRE ONCE.** The pass proposed 7 type corrections and the review confirmed all
  7, including all four of 194's `thought -> dialogue` calls. But the review then
  settled **6 more the pass never flagged**, four of them groups where *paddleocr
  alone* held `thought` while easyocr held `dialogue`. Not one group in the title
  carried `type_other_engine`, so the roster's "always supply `type` on such a
  group" rule never fired — the field is simply not populated here. Add a
  per-group `type` diff between the two engines to the close-out; it is a plain
  dict comparison and it would have caught all four.
- **THE `other:` VALUES DRIFTED, BUT DELIBERATELY.** The review changed exactly
  one of four free-text speakers, `other:a banquet guest` -> `other:banquet
  guests` on 194 g11, leaving the other three alone — a chorus against three
  single voices, not a typo. Left as the reviewer set it. Still worth grepping
  the counts: a 1-against-3 split is what an accidental near-duplicate looks like
  too.

### Findings to paste into the next run (2026-08-17, seventh batch)

15 speaker corrections and 4 cap corrections over *The Terror of the River!!*,
*Seals Are So Smart!* and *Biceps Blues* — 710 groups, **2.1%**, against 4.7% for
the batch before. 20 of 23 medium calls were promoted and 3 corrected, none
demoted. But **12 of the 15 landed on calls the pass made at `high`**, and the
rate is wildly uneven: 1.5% on *Terror*, 6.2% on *Seals*, **0% on *Biceps
Blues***, which came back 153/153 untouched.

- **A CHROMATIC BLOB IS ONLY A CAP IF IT SITS ON A HEAD. ALL FOUR CAP REVERSALS
  WERE BLOB-TO-FIGURE ERRORS, NOT HUE ERRORS.** Every hex the pass sampled was
  correct; what it got wrong was which figure the ink belonged to. *Seals* 039 p3:
  a `#0d9a84` H171 blob at x516-546 was the **five-dollar bill in a boy's hand** —
  the same ink as the cap green, cap-sized, at head height, and it passed every
  size and aspect filter. 040 p5: the pass read the *higher* red blob as the
  waving boy in front and dismissed the green at y407-470 as "a mitt or a collar";
  the green was his cap, and he reads lower because he is **nearer**. 036 p8: two
  `#06a07d` H166 blobs written off as "grass tufts well above their heads" were
  the cap wedges on the foreground boy — the y was compared against the wrong
  figure. The connected-component scan finds INK, not caps, and Barks props share
  the cap inks: banknotes, grass, mittens, balls. Confirm the blob sits on a head
  before naming from it. One 4-5x crop covered all three of these.
- **A ROTATED ROW IS THE SIGNATURE OF ONE MIS-ASSIGNED BLOB.** 039 p3 came back as
  a clean 3-cycle, blue/red/green -> green/blue/red. That is not three bad
  attachments; it is one prop mistaken for a cap shifting the whole left-to-right
  mapping by one boy. When a review rotates a row, re-check the blobs before
  re-checking the tails.
- **A STRAIGHT-SIDED WHITE BOX CAN STILL BE A BALLOON.** *Terror* 067 g5, a
  rectangular caption-shaped box with no visible tail reporting the wrecked yacht
  club, went `narrator` -> `other:man at the yacht club`. The pass had called it a
  caption precisely because the tailed balloon two panels later (067 g7) looked
  different. Straight sides are not the test; look for the tail.
- **AN ADDED GROUP NOW ARRIVES ON BOTH ENGINES WEARING THE SEED'S `speaker_was`.**
  The two groups the review added for the 313 number plate on *Terror* 048 came
  through carrying `type: dialogue`, the seed's Gemini `notes`, the seed's
  `vision_note` verbatim, an `identified_by` on a `none` speaker, and phantom
  `speaker_was` / `cap_colour_was`. Left alone they would have read as two more
  speaker corrections and one more cap correction — 17/5 instead of 15/4. Strip
  them, set the real `type`, and mark `vision_added` to match the corpus shape.
- **THE ENGINES NUMBER GROUPS INDEPENDENTLY, SO A STRAGGLER ID CAN LOOK DONE.**
  *Biceps Blues* 075 g13 is a different balloon on each engine; paddleocr's g13 was
  already reviewed while easyocr's was not. `vision-mirror` matches on text and box
  and put the flag on the right one, but do not read a straggler queue as if the id
  meant the same group on both sides.
- And the type work needs no new rule: 31 type corrections across the three titles
  were **all** confirmed, no text correction was reversed, and the per-group type
  diff between the engines came back 0 on all three after the apply. The
  close-out check added last batch is doing its job.

### Findings to paste into the next run (2026-08-17, eighth batch)

6 speaker corrections over *The Smugsnorkle Squattie* alone — 140 groups, **4.3%**,
against 2.1% for the batch before. Five of the six also overturned a cap colour.
All 6 medium hedges were promoted to high and 5 of them kept the pass's name, so
**5 of the 6 corrections again landed on calls made at `high`**. Every type
correction was confirmed, no text correction was proposed or made, and the review
added no groups.

- **A TAIL LEAVING A BALLOON'S OWN OUTLINE BELONGS TO THAT BALLOON.** 2 of the 6,
  and they are one move. On the splash, 083, a tail runs down-left from under the
  `HUH?` balloon onto the red-capped boy. The pass saw it, decided `HUH?` had to be
  Donald's because the boys had just asked him a question, and re-attributed the
  tail to the balloon *above* it — which then made `MAY WE HAVE HIM?` the red boy
  and left Donald with a tailless balloon. The review took the plain reading: `HUH?`
  is **Huey** off that tail, and `MAY WE HAVE HIM?` is **Dewey**, the boy under its
  own tail. Narrative fit is not evidence against a drawn tail; a nephew can say
  `HUH?` too.
- **WHEN THE ADULT WEARS THE SAME INK AS A CAP, THE FIGURE IS DECIDED BY SIZE AND
  BILL, NOT BY COLOUR.** Donald wears a blue workman's cap for most of 085-087, the
  same `#00a4d4` H194 as Dewey's band. On 086 p7 the pass read the duck holding the
  mirror as Donald *because of the blue*; it is **Dewey**. This is the blob-to-figure
  error the seventh batch found, one level up: the ink was right, the head it was
  sitting on was a nephew's. Check the head's size and bill length before letting a
  cap ink name an adult.
- **A BLACK SILHOUETTE CAN STILL BE NAMED FROM THE PANEL BEFORE IT.** 088's kidnap
  sequence: panel 3's dialogue names the boy Donald has hold of (*HE'S KIDNAPING
  LOUIE!*), and panel 4 draws the same struggle as flat silhouettes. The pass
  recorded `nephews` for all four shouts because no cap reads on a silhouette; the
  review named the carried boy **Louie** in panel 4 as well. Absence of colour is
  not absence of identification when the scene continues.
- **WHERE TWO BOYS OVERLAP IN X, THE NEARER ONE OWNS THE TIP.** 089 p5, the last 2
  of the 6, a clean swap: the pass measured one long tail to x368, gave it to the
  blue-capped boy behind, and took the green-capped foreground boy by elimination.
  Both were wrong way round. The foreground boy sits LOWER and further left than his
  cap suggests, and "never resolve the leftover balloon by elimination" applies to
  figures that overlap, not only to fans.
- **A PANEL CAN PRINT A NEPHEW IN ANOTHER NEPHEW'S INK, AND THE DIALOGUE OUTRANKS
  IT.** 088 p3 prints a **red** band on the boy the same panel's dialogue calls
  Louie. The pass named him Louie from the line, recorded `cap_colour: red` as
  printed rather than filling it in from the name, and hedged the other two boys of
  that panel to medium; the review confirmed all three. Record the disagreement, do
  not smooth it away — and do not let one mis-coloured panel spread doubt over the
  rest of the title, which used the convention throughout.
- And the close-out again: the review renumbered 088's easyocr ids into reading
  order — `OW!` moved from g14 to g10 and everything above it shifted — without
  adding or deleting a group. Counts stayed 15/15, `vision-mirror` matched on text
  and box, and nothing was lost; but a stored `result.json` or a queue built before
  the review would now point at the wrong groups.
- One straggler again, the eighth title running: 088 g7, the last of a page's four
  silhouette shouts. Count `speaker_reviewed` on both engines before calling a
  review done.

### Findings to paste into the next run (2026-08-18, ninth batch)

45 speaker corrections and 28 cap corrections over *Santa's Stormy Visit*,
*Swimming Swindlers* and *Playin' Hookey* — 428 groups, **10.5%**, against 4.3%
for the batch before and the worst since the 12.5% of 2026-08-12. All 72 medium
hedges were promoted and none demoted, the eleventh review running to do so, so
the hedging is still calibrated and the damage is somewhere else. The rate is
uneven — 6.6% on *Swimming Swindlers*, 12.1% on *Santa's*, **13.1% on *Playin'
Hookey*** — and one cause accounts for most of the gap.

- **NEVER WRITE "NO INK" INTO A NOTE ON THE STRENGTH OF A FILTERED SCAN. 17 of
  the 22 corrections on *Playin' Hookey* landed on groups whose notes said
  exactly that.** "no chromatic blob", "no cap ink resolves", "carries no
  chromatic pixel at S>=0.6" — and the ink was there the whole time. On 113 p4
  the scan at the *same* thresholds reports **40 blobs**, including blue caps at
  `#019ac7` and `#009cca`, both H194. What hid them was a shell filter: the scan
  padded its size column, so `n=  308` and `n=30097` split into different awk
  fields and an `$3 ~ /n=/` guard matched nothing at all. An empty pipe read as
  an empty panel. The rule: an absence claim is only allowed when the scan's own
  `N blob(s)` header says zero, and the note should quote that count. Do the size
  windowing inside the script (`--min` / `--max`), never in a pipe.
- **A ROW WITH NO CAP INK AT ALL IS STILL NAMED FROM POSITION.** 093 p3 is the
  honest version of the same call and it went the same way. Re-measured at
  min 8px / S>=0.45 the panel really does print no cap ink — the only chromatic
  blobs are the lantern housing — and the review still named all three boys
  Huey/Louie/Dewey *with cap colours*, off the row order and the reference panel
  next door. So "absent, not declined" is not a defence. This extends *Monster
  Kite*'s "one anchor cap names the whole row" to **zero** anchor caps: three
  boys in a row with one balloon each get named whatever the colour does.
- **THE OFFSET FAN HELD 4 TIMES IN 5, AND THE EXCEPTION HAS A TELL.** Five fans
  in this batch showed the one-boy-left shift; 094 p4, 098 p6, 107 p3 and 115 p2
  were all confirmed with the names the reading-order rule gave. The one reversed
  was 093 p2, where the review took the measured tips instead — and the pass had
  already written the alternative into its own note. The difference is that on
  093 p2 the two boys the rule had to order **overlapped in x** (head centres 322
  and 327): there was no left-to-right order to read, so the fallback had nothing
  to fall back on. When the boys a fan spans overlap in x, prefer the tips and
  hedge; when they are strung out, the reading-order rule is good.
- **A PAIR CAN STILL BE SWAPPED AFTER TRACING THE TAILS AT SOURCE RESOLUTION.**
  093 p6 was read off the whole panel at native size, one tail per boy, each tip
  measured onto its own cap — and g13/g14 came back swapped anyway, with both cap
  colours moving. Loading the panel is not proof; it is one more measurement.
- **A WORDLESS NOISE BESIDE AN ANIMAL IS NOT AUTOMATICALLY THE ANIMAL.** Two of
  these, in opposite directions. On *Santa's* 096 the pass gave `SQUAWK! WHEEK!`
  and `SQUARK! WHEEK!` to `other:the albatross`; the review made all three
  `other:the radio`, noted "radio static", and left `GRAWK!` on the same page
  with the bird. On *Playin' Hookey* 117 the pass gave `GLEEP!`/`PLEEP!` to
  `other:the goats`; the review made them **Dewey and Louie**. Ask what the noise
  is *for* before assigning it to whatever is drawn nearest.
- **THE ADDED GROUP ARRIVED WEARING THE SEED AGAIN — FIFTH ROUND, AND NOW THE
  FULL SET.** *Playin' Hookey* 118 gained the car's `313` number plate in panel 7,
  correctly on both engines and appended as g11 so nothing renumbered. It carried
  the seed's Gemini `notes`, the pass's `vision_note` for the panel's balloon
  verbatim, an `identified_by` of `sole-figure`/`balloon-tail` on a `none`
  speaker, and phantom `speaker_was: Donald` / `type_was: thought` that would
  have read as one more speaker and one more type correction. Strip all five,
  write a real note, and set `vision_added` — Vol. 3 192 g13 is the same `313`
  plate and is the shape to copy.
  *Santa's* 099 then did it again for the `CAPTAIN` cap band the missed-text
  audit had been flagging, seeded from `SPLAT!` two groups away and carrying its
  Gemini `notes`, its `vision_note` verbatim and a phantom
  `type_was: sound_effect`. **But not everything inherited is residue**: that
  group's `style: angled` looks like the seed's display lettering and is in fact
  correct, because the cap is tumbling through the air and the word runs
  bottom-to-top — which is also why its box is taller than it is wide. Crop the
  box before stripping a field that might be right.
- **AND A FREE-TEXT SPEAKER SPLIT IN TWO.** *Santa's* now carries
  `other:the radio` (3) beside `other:the radio announcer` (1). It may well be
  deliberate — the announcer reading the bulletin against the set's static — but
  a 3-against-1 split is also what an accidental near-duplicate looks like, so
  say it out loud at close-out rather than leaving it to be found later.

### Findings to paste into the next run (2026-08-18, tenth batch)

25 speaker corrections and 13 cap corrections over *The Gold-Finder*, *The Bill
Collectors* and *Turkey Raffle* — 468 groups, **8.1%**, against 10.5% for the
batch before. All 50 medium hedges were promoted and none demoted, the twelfth
review running to do so. The rate is uneven — 5.2% on *Gold-Finder*, **12.7% on
*Bill Collectors***, 7.0% on *Turkey Raffle* — and the two ends of it failed in
opposite ways: on *Gold-Finder* six of the seven landed on `high` calls and on
*Bill Collectors* seven of the eleven landed on calls already hedged to medium,
which is the hedge doing its job.

- **THE COLOURIST IS A THIRD PARTY AND THIS VOLUME LETS HIM WIN.** *Gold-Finder*
  123 prints the second nephew's cap a clean `#029c47` H147 on every panel of the
  page and he is **Dewey**; the review kept `cap_colour: green` on all six groups,
  so the record now carries the fault instead of hiding it. Same shape on *Bill
  Collectors* 200 g5, where the crown was cropped at 3.6x and is unarguably green
  on a boy the review calls **Huey**. No reading of the ink could have produced
  either name. What produces them is tracking one boy through the scene — the boy
  who fetches the watch and then holds it, the boy who went in at the window one
  panel earlier — and letting that outrank a cap you have measured. Six of this
  batch's 25 speaker corrections are that single page.
- **A MUDDY COOL BAND IS THE HARDEST CALL IN THE VOLUME AND IT WENT WRONG IN BOTH
  DIRECTIONS.** *Bill Collectors* 196 g8 is a 20-23px band at `#216677` H192
  **S0.72**; it was read as blue off hue alone and is the **green** — the
  saturation test says a blue stays saturated however small, and p2 had already
  shown that boy going up the pole. *Turkey Raffle* 139 g17 is the inverse: a 55px
  `#388f62` H149 **S0.61** band read as a green cap and named, sent back to
  `nephews` with `cap_colour` null. So: below about S0.75 a cool band names
  nobody on its own. Rank it inside the panel, and if the panel has no clean
  companion to rank it against, decline the colour and name from the scene or not
  at all.
- **DO NOT PUSH A MAPPING SIDEWAYS TO SATISFY A LINE.** *Bill Collectors* 197
  g5/g6: the tip measured at x~178, inside the left boy's head span, and the whole
  three-boy mapping was then shifted one boy right so that *"OPEN THE BRIEF CASE,
  DEWEY!"* would not be spoken by Dewey. The measured tip was right and both
  groups came back. A line that addresses a nephew constrains ONE speaker; it is
  not a licence to rotate the row.
- **TWO BOXES STACKED IN ONE OUTLINE ARE A JOINED PAIR, NOT ONE BALLOON.**
  *Turkey Raffle* 133 g1/g2, *"IT'S"* and *"ALIVE!"*, were read as a single
  balloon and given a single speaker; the review kept g1 Dewey and made g2
  **Louie**. The same title has a dozen correctly-named cascades in it, so the
  test is mechanical: two group boxes stacked with their own outlines is two
  speakers unless a tail says otherwise.
- **BARE HEADS STILL GET NAMED.** *Turkey Raffle* 138 g5 went `nephews` ->
  **Dewey** on a boy swimming with his cap off. The batch recorded 33 collectives
  and defended most of them as absence rather than a declined cap — 20 of them in
  *Turkey Raffle* alone, where the boys are silhouettes, swimming or indoors for
  half the title — and the review took one of them anyway. Absence buys a hedge,
  not a pass.
- **CHECK THE ADULT BEFORE HANDING A LINE TO DONALD.** *Turkey Raffle* 137 g5,
  *"NO MAN LIVING HAS EVER HIT TWO!"*, is the shoot man conceding, not Donald
  boasting. In a two-hander where one of the pair is a bit player, read whose
  interest the line serves.
- **THE SPEAKER REVIEW IS STILL NOT THE TYPE REVIEW.** *Gold-Finder*'s 4 and *Bill
  Collectors*' 0 came back settled, and *Turkey Raffle*'s 3 (133 g15 `LATER`
  background -> narration, 139 g3/g4 `OW!` sound_effect -> dialogue) are still
  unconfirmed on both engines after a 172/172 speaker review. Hand the corrections
  queue back separately and say the count out loud.
- And the straggler, the **tenth title running** and now three in one batch:
  *Bill Collectors* 197 g8 and *Turkey Raffle* 136 g10, both the last group of a
  page, both confirmed unchanged once looked at. Count `speaker_reviewed` on both
  engines before calling a review done.

### Findings to paste into the next run (2026-08-18, eleventh batch)

20 speaker corrections and 6 cap reversals over *Maharajah Donald* alone — 388
groups, **5.2%**, against 8.1% for the batch before. All 44 medium hedges were
promoted to high and none demoted, the thirteenth review running to do so, and
**17 of the 20 landed on calls the pass made at `high`**. Everything else came
back clean for once: all five of the pass's type corrections confirmed on both
engines and `vision-corrections --title` reporting nothing outstanding, no text
correction proposed or made, and no group added, deleted, renumbered or re-boxed.

- **A CAP YOU CAN SAMPLE IS NOT EVIDENCE THAT THE SPEAKER IS A BOY.** 4 of the 20
  went to **Donald** (016 g12, 017 g7, 017 g10, 028 g14), and all six cap
  reversals are the same shape: every hex the pass sampled was right, and the head
  under it was not the speaker's. Through 013-019 Donald is bare-headed in a
  dinner jacket while the boys' beanies print cleanly, so the only measurable
  colour in the panel belongs to somebody who is not talking. This is
  *Smugsnorkle*'s blue-workman's-cap error with the colours reversed: check size
  and bill before letting a sampled wedge decide, and treat "there is a cap I can
  measure" as a reason to look harder, not as the answer.
- **A MEASURED TIP IS NOT A NAME. 6 of the 20 were tails the pass had traced at
  1-1.7x with the coordinates written into its own note** (009 g7, 015 g2, 017
  g10, 017 g11, 018 g1, 028 g14). Every one came back `nephews` or Donald. 017 p7
  is the offset fan again and the giveaway is the adult: Donald, red, blue, green
  strung out left to right, tips measured at x505 and x585 landing on the red and
  the blue boy, and the answers are **Donald** and **`nephews`** — one figure to
  the left, which is the Vol. 4 habit. When a row starts with an adult, count him
  as the first position before mapping anything.
- **A CAPTION NAMING A NEPHEW FOR AN OFF-PANEL ACTION DOES NOT TRANSFER TO THE
  PANELS AROUND IT.** 029's caption reads *DEWEY FAILS TO NOTICE THE TAG ABOVE THE
  FAUCET!* over a panel with no character in frame; the pass gave the bare-headed
  boy at the hose in the panel before AND the panel after to Dewey, and the review
  sent **both** back to `nephews`. It bounds *Singapore Joe* 159 p4 rather than
  contradicting it: there a character's line introduced the speaker of the next
  balloon, here a caption describes an action nobody is drawn performing.
- **THE REVIEW CONSOLIDATED THE CAST AND NEVER SPLIT IT. 5 of the 20 are free-text
  roles, and every one moved to a figure already on the page.** The pearl buyer is
  `other:a customer`, not the shop's clerk (009 g15 and 010 g3, and
  `other:the jewelry clerk` is now gone from the corpus); 024 g1's balcony line and
  025 g2's ladder line are both the compiler of the deficit rather than the
  messenger and the tax collector; and 020 g6's *(COUGH! COUGH!)* is
  `other:a palace servant`, not the Maharajah, whose cough it had been on 016 and
  017. Invent a role only when no drawn figure fits — and note that the review kept
  guard / servant / officer / herald / messenger as five distinct roles, so the
  distinction itself was sound.
- **THE ONE UNDER-NAMING CORRECTION IS THE SEAT, NOT THE FACE.** 022 g4 went
  `nephews` -> **Louie** on a page drawn entirely in silhouette. The boy at the
  elephant's neck is the mahout for the whole Indian sequence, so the seat names
  him even where the panel prints him as a black shape; the pass used exactly that
  rule on 023 and 025 and failed to apply it one page earlier.
- One straggler again, the **eleventh title running**: 029 g2, a narration caption,
  confirmed unchanged once looked at. Count `speaker_reviewed` on both engines
  before calling a review done — and note that `speaker-queue` exits 1 WITHOUT
  writing its file when nothing matches, so a stale queue from the previous run
  stays on disk looking current. Read the "No calls match those selectors" line,
  not the file.
- **A SPEAKER CORRECTION CAN LEAVE THE TYPE BEHIND, AND THAT PAIR IS WORTH
  GREPPING FOR AT CLOSE-OUT.** 012 g7, `SQUEECH!`, went `none` -> **nephews** in
  the review — the noise is a boy being squeezed inside the pineapple — while its
  `type` stayed `sound_effect`, which is exactly the legacy shape the type rule
  exists to catch. Reported and then retyped to `dialogue` on both engines. Any
  group whose speaker names a character while its type is `sound_effect` is the
  same case: the speaker review does not touch `type`, so nothing else will find
  it.

One process note worth keeping: a corpus-wide `barks-ocr-vision-corrections` run
now dies with `FileNotFoundError` on a missing Vol. 2 cover,
`Fantagraphics-original/Carl Barks Vol. 2 …/images/686.jpg`. Per-title runs are
unaffected.

### Findings to paste into the next run (2026-08-19, twelfth batch)

10 corrections over *The Cantankerous Cat* — 5 speaker and 5 cap over 142
groups, **7.0%**, against 5.2% the batch before. All 4 medium calls were promoted
to high and none demoted, so the hedging is still fine; **9 of the 10 landed on
two panels**, and both were fans.

- A TIP THAT LANDS ON A HEAD DOES NOT ANCHOR A FAN. 141 p5: three balloons, three
  boys, two tips on empty grass and the third **inside a boy's head span, on a cap
  sampled at `#e11b1f` H359**. I used the clean tip as an anchor, named that boy
  and left the other two `nephews`. The review shifted the whole fan one boy right
  and named all three off reading order — the anchor was itself the slipped tip.
  If ANY tip in a fan lands on nobody, no tip in that fan is trustworthy,
  including the one that looks measured. The tip-beats-order rule applies only
  when every tip in the fan lands on a figure.
- THE SAME OFF-BY-ONE HITS THE CAP READING, NOT JUST THE TAIL. 148 p5 kept both
  my speakers, which came from a naming line, and moved both cap colours one boy
  along — red→green and green→blue. Map caps to heads as its own measurement; do
  not inherit the boundaries you used for the tails.
- A NAMING LINE NAMES THE BOY EVEN WHEN THE CAP SAYS OTHERWISE. 149 g12: the
  line "LET'S WAKE LOUIE" leaves Huey and Dewey awake, the one readable cap in
  the panel is a clean green, and I recorded the colour and declined the name.
  The review named him **Dewey** and kept the green. The disagreement is the
  record; it is not a reason to retreat to a collective.
- DO NOT INVENT A SECOND VOICE FOR A ONE-FIGURE PANEL. 147 g1: two balloons over
  Donald in bed with an imagined vignette on the wall, read as Donald arguing
  with himself. The answering balloon is a nephew's. Reaching for
  conscience-and-self is the same error as reaching for an off-panel adult.
- And the type queue went untouched again: 25 type corrections, **zero
  disagreements** from the review, and `vision-corrections` still reporting all
  50 entries outstanding afterwards. Confirming a type is a separate action from
  confirming a speaker, and finishing the speakers says nothing about it.

**And from *Donald Duck's Atom Bomb*, 5 corrections over 134 groups (3.7%) —
four of them Donald against Professor Mollicule in a two-figure panel.**

- WITH TWO ADULTS IN FRAME THE ATTRIBUTION IS AS SHAKY AS A NEPHEW FAN, and the
  medium hedge found it: **4 of the 9 medium calls were corrected against 1 of
  the 125 highs**, about 44% against 0.8%. Two tails descending into one knot of
  figures is the same problem as a fan and gets the same treatment.
- A DRAWN FIGURE BEATS AN OFF-PANEL ONE EVEN WHEN THE TAIL FALLS SHORT. 155 g12
  is a close-up of Donald's face alone with the tail stopping well above his
  head; I promoted it to an off-panel professor and the review gave it to
  Donald. A tail ending in empty space over a head is still that head's.
- REGISTER IS NOT EVIDENCE. "The professors do not talk like this" lost twice.
- CHECK THE `other:` VALUES BEFORE MIRRORING, NOT AFTER. This review handed back
  `other:Professor Molicule`, one `l`, against 31 of the canonical spelling — a
  typo to fix on easyocr first so the mirror carries it. It also introduced
  `other:Donald and Professor Mollicule`, the only **compound** in 273 distinct
  `other:` values corpus-wide. That one is CORRECT and must not be collapsed:
  155 p5's balloon carries **two tails**, one to each of them. I missed the
  second twice — it runs parallel to the curtain's vertical strokes and reads as
  one more line of the background until the whole panel is in frame.
- COUNT EVERY TAIL ON A BALLOON, NOT JUST THE FIRST ONE THAT EXPLAINS THE LINE.
  Two tails means two speakers and a compound `other:` value. Crop the whole
  panel before tracing, and expect a tail crossing hatching, a curtain, rain or a
  fence to vanish into it.
- A TEXT CORRECTION CAN COME BACK HALF-APPLIED. 153 g6 proposed two words,
  `PECULIAR -> BECULIAR` and `PROFESSOR -> BROVESSOR`; the stored text now has
  the second and not the first, and `vision-corrections` correctly still reports
  it outstanding. Read the stored string, not the outstanding count.
- The type queue behaved this time: all 8 type corrections were confirmed, so
  the untouched-type-queue problem from title 1 is not universal.

**And the last two titles: 18 corrections over *Going Buggy*'s 134 groups
(13.4%) and ZERO over *The Peaceful Hills*' 28.** Batch total 33 corrections over
438 groups, 7.5%, against 5.2% the batch before.

- THE SPEAKER FIELD NAMES WHO MAKES A NOISE, EVEN WHEN THE TYPE STAYS
  `sound_effect`. Nine of *Going Buggy*'s fourteen were this one rule: six
  `CHOMP!`s → `nephews` (the boys chewing inside the bug suits) and three
  `CLACK!`s → `Donald` (his costume beak). I had set all nine to `none`, writing
  "a prop makes it, not a voice" into the notes, having quoted the opposite rule
  from `roster.txt` on the same page. *The Peaceful Hills* fixes the boundary by
  coming back clean: its ten `none` effects — THUD, CHUNK, RUMBLE, ROAR, BANG,
  BOOM, SNAP — all stood, because impacts, gunfire and weather have no maker.
  Expect the close-out grep for "speaker named while type is sound_effect" to
  fire on the first class; that is the correct end state, not a defect.
- NEVER `head` AN INK SCAN. Three more corrections came from 162 p3, where I
  piped the scan through `awk` and `head -12`, saw only wall and floor, and wrote
  *"a cap-ink scan of the panel finds nothing on any of them"* into three notes.
  Re-run unfiltered the caps are all there — red `#d01c1f` H359, blue `#059db6`
  H188, green `#069389` H176, at 99, 184 and 179 pixels. **The scan sorts by area
  descending and a cap is always among the smallest blobs**, so seven background
  regions filled the visible lines and `head` cut the list before the caps.
  Truncation removes exactly the class of blob being looked for. Window by size
  inside the script; a cap band is roughly 80-5000px.
- OVER-NAMING HAPPENS TOO, ONCE. 167 g1 went `Louie` → `nephews`, the batch's
  only demotion, against a tail I had measured onto a green cap. One reversal in
  33 corrections — the direction of travel is still overwhelmingly toward naming.
- AND CHECK YOUR OWN `other:` SPELLING AGAINST THE CORPUS, NOT JUST THE REVIEW'S.
  The drift on this title was mine: I wrote `other:the Mayor` where the corpus
  already had 11 groups of `other:the mayor`. Grep the corpus-wide counts for the
  value before inventing the capitalisation.

### Findings to paste into the next run (2026-08-23, thirteenth batch)

17 speaker corrections over *Donald's Posy Patch*, *Donald Mines His Own
Business* and *Magical Misery* — 393 groups, **4.3%**, and **9.2% inside the
nephew domain** (16 of 174 Huey/Dewey/Louie/`nephews` groups). The reviewer has
since set the tolerance at about 10% on nephew calls, so **that rate is at
target and accuracy is no longer the binding constraint — cost is.** See
`docs/vision-pass-cost.md`, which this batch caused.

The shape is new and worth stating plainly: **13 of the 17 were calls made at
`high`, and only 4 of 21 `medium` calls were wrong.** Twelve reviews running,
the hedging has been calibrated; what is left is entirely in the confident
calls. Three demotions too, after batches of none.

- MEASURE A TIP TO A HEAD, NOT TO A CAP. Four of the five name swaps quoted a
  confident pixel margin, and every one was measured to a cap edge. A duck in
  three-quarter view has a beak reaching far past his cap: on *Donald Mines*
  045 p4 the green cap ends at x=793 and its wearer's beak reaches back to
  x=573, so a tip at x=589 was written up as *"10px past the red cap and 68px
  short of the green"* while sitting on the green boy's face. Now in
  `vision_schema.py`. **A margin measured to the wrong landmark is worse than
  no margin — it reads as measurement and promotes the call to high.**
- A CLEAN CAP NAMES ITS WEARER WHEN HE IS THE ONLY NEPHEW IN FRAME. A sole boy
  wearing 3319px of clean `#03a4d5` was recorded `nephews`, the note reasoning
  that *"he is the only nephew in the panel, so the colour is recorded rather
  than used to pick between boys"*. The note contradicted its own call. The
  convention is not a tie-breaker that needs a rival. Now in
  `vision_schema.py`.
- THE FURNITURE CAN BE THE CAP INK, AND VALUE IS WHAT SEPARATES THEM. All three
  titles print the nephew green as a leaf green at H110-112 `#4da33d` — **not**
  the Vol. 5 roster green — and *Magical Misery* prints its sofa and its hedge
  at H109.7 `#54b041`. Same hue to within a degree; the caps sit at V=0.64 and
  the furniture at V=0.69. Hue alone merges a cap into a 95,000px hedge blob.
- A CAP-SIZED BLOB ON NOBODY'S HEAD. *Magical Misery* 087 p3 has Donald's
  magician's hat in mid-air as a 3271px blob in exactly the cap green. It was
  the first candidate reference panel and it was wrong. The rule is already in
  the schema; this is the cleanest example of it yet.
- THE REVIEW FILLED A CAP COLOUR IN FROM THE NAME, ONCE. *Posy Patch* 030 g12
  went `nephews` → `Huey` with `cap_colour: red` on a panel that prints **no
  red at any threshold** — a full unfiltered colour census returns sand, cream,
  lavender, black, brown, orange and a pale blue. The speaker call stands, but
  the colour is now unfalsifiable. Worth a census rather than a scan whenever a
  correction adds a colour the pass reported absent.
- A LABEL WITH AN ARROW IS NARRATION, NOT BACKGROUND. `DOOR STOP` pointing at
  the door stop is the author annotating his own drawing, not lettering in the
  scene.
- A ROTATED CAPTION READS AS A WORD. *Magical Misery* 079 g15 stores `JAW`,
  which is the grouper taking the vertical caption `LATER!` on its side. The box
  is right and only the text is wrong, so the missed-text audit reports `LATER!`
  as grouped-by-neither until the correction is confirmed — **not** a group to
  add. Check any three-or-four-letter background group against a vertical box.
- A TYPE CORRECTION CAN BE REFUSED SILENTLY. `vision_apply` reported 5 type
  corrections where 6 were supplied; the missing one carried `type_reviewed`
  from a fortnight earlier and was correctly left alone. Nothing said so.
  **Reconcile the count the tool prints against the count you supplied**, and
  hand the difference to the reviewer — the page was left internally
  inconsistent, one balloon `thought` and its twin `dialogue`, until they fixed
  it by hand.
- CHECK THE TREE BEFORE RE-APPLYING A COMMITTED TITLE. A review had started
  between the commit and the re-apply, and Vol. 20 had 179 unrelated
  uncommitted files. `vision_apply` protected the reviewed speakers, which was
  luck rather than care; the skill says use `vision-mirror` after a review.

### Findings to paste into the next run (2026-08-25, fourteenth batch)

*Christmas on Bear Mountain*, *The Terrible Turkey*, *Wintertime Wager* — 532
groups, 22 speaker corrections (4.1%), 18 of them in the nephew domain (9.1%).
Split by title the nephew domain runs 6.5% / 12.8% / 12.0%: the batch average
only holds because the twenty-page title is capless indoors for most of its
length. Both ten-page titles went over.

**Nearly every correction was evidence already written into the note and then
not used.** That is one finding, and it has four faces:

- *Wintertime Wager* 042: the note reads "left to right their caps are green,
  red and yellow-white", and on the next group "the second boy, the one in the
  red cap. I am not naming him from that alone — see the note on 044, where the
  red cap is anchored to Huey by name." Cap, tail and anchor, all three in
  writing, and the answer given was the collective. **A late anchor applies
  backwards to every panel it implicates**, and citing it is not applying it.
- Two calls set out both readings and picked the weaker — "this throws
  Gladstone's own greeting back at him, which is Donald's gag rather than a
  boy's", answered `nephews`; "OH, MY! is Gladstone's own refrain earlier on this
  page", answered Donald. **A note that argues against its own call is the single
  best predictor of a correction in this corpus.** Re-read the note before
  writing the speaker.
- Four declines said "no readable cap" where a `capscan` at a **20px floor**
  shows it plainly. `capsum` is a locator: its 15px dilation merges a cap into
  neighbouring ink and its size cap then drops the cluster. It never answers
  "there is no cap". Neither does a crop aimed at the wrong y band — one decline
  came from cropping the *houses* above the boys and concluding from that.
- A cap in a **non-roster colour is not a dead end**. Where the third boy's
  knitted cap is yellow-white, his mittens and scarf carry 5144px of clean
  `#00a5d7`; the review named him on `costume`, with `cap_colour` left null.

Three smaller ones:

- **A tip that lands between two heads does not go to the nearer one.** Two
  corrections were 11px-against-39px and 39px-against-132px calls that both went
  the other way. Rank by the spur's own d-vector — one of them pointed
  down-*left* at the further boy and the vector was in the note — and by what the
  figures are drawn doing; the second boy had his hand cupped to his beak in a
  crop already taken. A margin decides it only when the tip is *inside* a span.
- **A wordless `SIGH!` belongs to the sleeper**, not to the duck pressed against
  the sleeping bear. Two corrections, same panel shape.
- Words coming from all four ducks at once take **`other:Donald and the
  nephews`** — with the definite article, which is the corpus spelling.

One verification trap, no correction attached: **pair the two engines on
normalised `ai_text`, never on group id, when checking a mirror.** Two pages of
one title list an out-of-reading-order group last on easyocr where paddleocr has
it in place, so an id-keyed check reports fourteen mismatches on a mirror that is
in fact perfect. `vision_mirror` itself pairs on text and is right.

### Findings to paste into the next run (2026-08-25, fifteenth batch)

*Watching the Watchman*, *Darkest Africa*, *Wired* — 24 corrections over 567
groups, 21 of them in the nephew domain. Written as rules:

- **Where nobody wears a distinguishing hat, the error moves to Donald against
  nephew.** 12 of *Darkest Africa*'s 15 corrections were that pair under
  identical pith helmets — not nephew against nephew, which the cap rules are
  built for. Head size fails (a wide shot scales both down, and Barks draws a
  crouching Donald small) and so does register ("that line sounds like an order").
  What works: **scan for Donald's red bow tie.** It survives under any hat and a
  `capscan` at a 20px floor finds it in shadow — an 87px `#983227` pair placed
  him second from the left among four identical helmets. Sample for it before
  arguing from size.
- **A negative cap sweep is a result, not a hedge.** *Wired* returned **0
  corrections in 144 groups**: bare heads, then the same red messenger cap on all
  four ducks. Say the sweep came back empty and stop looking.
- **A naming line beats the cap the story prints.** 057 says "HUEY AND LOUIE HAVE
  PASSED OUT, BUT I'M STILL ON THE JOB" and the speaker's cap prints **red** on
  all six panels he is in — while 058 prints the two who *did* collapse as blue
  and red. Following the line at medium, with `cap_colour` recorded as printed,
  stood: none of that title's 9 corrections was on that page.
- **Measure the story's tail offset once, then use it.** *Watching the Watchman*
  runs its tails ~20px LEFT of the boy's head span (055 p4's three land 12/3/10px
  left); *Darkest Africa* 083 runs them right. A gap that size is the story's
  habit, not a fan — but derive it from a panel where the mapping is unambiguous
  before leaning on it.
- **Crop the side the tail points at, not the figures.** 089 p8 draws two figures
  at the right; I cropped `(400,200)-(948,655)`, read both correctly, and gave the
  balloon to the wrong one. Its tail runs down-LEFT into a third of the panel my
  crop began after — empty water with a canoe prow, and the speaker off-frame in
  it. Read the tip and d-vector first and make the crop span that direction.
- **Who is drawn and who speaks are separate questions.** The same panel's page
  capture said "McFiendy catches Van Tulip", and that stayed true when the speaker
  moved to Donald. A review changing a speaker does not by itself falsify a beat.
- **Not every bare device is `thought`.** A lone `!` in a musing balloon is; a
  lone `!` on a sleeper jerking awake is a vocalised gasp and was corrected to
  `dialogue`. Look at what the figure is doing.

Two process notes, no correction attached. **A full speaker count says nothing
about the type queue** — one title finished 148/148 on speakers with all 14 type
corrections untouched. And **a review that adds a group hands back Copy In
residue**: both added groups here arrived carrying the seed group's `vision_note`,
one also its `identified_by: ["caption"]`. Check added groups against their own
crop *and* their metadata before mirroring, or the residue is copied to both
engines.

### Findings to paste into the next run (2026-08-26, sixteenth batch)

*Links Hijinks*, *Pizen Spring*, and the Vol. 6 1948 titles. **Reconstructed on
2026-09-02 from the memory notes of the time, not written at review.** The rules
are the notes' own; the correction counts are only quoted where a note recorded
one.

- **A teal-drifted cap band is as often the BLUE as the green.** In *Links
  Hijinks* the H149-168 band was blue, and reading it green cost the pair. Rank
  within the panel against a clean reference, and never carry a hue reading from
  one page to the next.
- **Below about S0.75 a cool band names nobody on its own.** It failed in *both*
  directions in one title. Say so and take the tail instead.
- **Five of eight corrections in one title were caps I declined and the reviewer
  read.** Declining is not the safe option; it is the error. Probe the head's
  pixel histogram before writing "no readable cap".
- **`capsum` is a locator, not a decider.** Its 15px dilation and 150px floor
  swallow real caps — never decline off `capsum` alone; `capscan` decides.
- **Knowing Donald wears Dewey's blue makes you decline blue rather than check
  it.** The crown SHAPE separates a sailor cap from a beanie; Dewey's blue
  outnumbers Donald's.
- **Gladstone wears the roster inks** — his fedora is the cap green and his bow
  tie Dewey's blue — and *Pizen Spring*'s sky is `#01a3d3`, the same ink again.
  A blob is only a cap if it sits on a head.
- **A balloon with no tail is its own speaker.** Place the panel's tailed
  balloons first, then give the tailless one what is left. Never inherit.
- **On a `sound_effect` the speaker names WHO MAKES the noise**, and `none` means
  nobody does.

### Findings to paste into the next run (2026-08-27, seventeenth batch)

*Lost in the Andes!* — **40 speaker corrections over 456 groups (8.8%)**, and
32 of 128 nephew-domain calls (25%).

- **Medium is where the error lives: 31.0% of what was written at medium was
  corrected, against 7.3% of what was written at high.** A medium is not a
  safe hedge; it is a coin-flip that reads as caution.
- **`capscan`'s hue bands have one-degree cracks** at H182/183 and H12/340, and
  its `green` band is not where the cap green lives. It reported `red: 0 /
  green: 0 / blue: 0` for three plainly coloured caps. When a band comes back
  empty and a name hangs on it, re-run `capwide.py` and then crop.
- **A black crown with a small coloured wedge is misread about 4% of the time** —
  15 `cap_colour_was` in 402 groups against 0 in the previous 613. Probe, then
  crop at 4-6x. A wholly black crown still names its boy from the tail; it is not
  a reason to fall back to `nephews`.
- **`tailtip.py` returns the strongest spur, never the tail COUNT.** Reading one
  returned spur as "one tail" merges two balloons and loses a name.
- **Calling two balloons joined when each carries a tail loses a name** and
  slides the whole cascade by one.
- **A drawn device the engines missed reaches nobody unless the pass records it
  in `visible_text`.**
- **The editor can re-sort a page into reading order and renumber with no add and
  no delete**, so compare id->ai_text when diffing a review, never the id set.

### Findings to paste into the next run (2026-08-28, eighteenth batch)

*Super Snooper*, *Frog-Jumping*, *Dowsing Ducks*, *The Goldilocks Gambit* —
**22 corrections over 429 groups (5.1%)**, split very unevenly: 1.4%, 3.6% and
**10.1%**.

- **Desaturated pages invert an in-panel hue ranking rather than blurring it.**
  Almost all of *Dowsing Ducks*' error is its desert half, where the ink washes
  toward one teal: blue/red became green/red twice, and 14 `cap_colour` values
  moved with the names. An eight-degree gap is noise. Crop instead of ranking.
- **Never extrapolate a tail past its drawn tip.** All three nephew errors in
  *The Goldilocks Gambit* were that one move: a slope projected ~100px to head
  height **swapped the pair** both times. Quote the tip coordinate and the head
  spans and stop. A computed landing point reads as measurement and wrongly
  promotes the call to high.
- **On an unreadable long shot the default is Donald**, 15 corrections to 5 the
  other way — but only where nobody is legible at all.
- **Two caps printing the identical ink still name their boys** from seating
  order at medium with `cap_colour` null. Two disjoint wide samples returning the
  same value is the printing, not a bad box.
- **A coloured parka hood belongs in `cap_colour`**, not only in `costume`.
- **Copy In keeps the seed's `ai_text`, `notes`, `acknowledged_issues` and
  `style`** — check every group a review added against its own crop.

### Findings to paste into the next run (2026-08-31, nineteenth batch)

*New Toys*, *Donald's Love Letters*, *Rip Van Donald*, *Trail of the Unicorn*.
*New Toys* ran **18 corrections in 122 groups (14.8%)**; *Love Letters* 2 in 104
(1.9%) the same day with the same tools.

- **A census zero on a sliver-cap title means CROP, not bare.** 13 of *New Toys*'
  18 corrections were `nephews` -> a name on the two pages where a `heads2` zero
  was taken as proof of bare heads and no crop was spent. The control title,
  read the same day, came back 1.9%.
- **Cap AREA is the discriminator, not confidence.** 25 of 25 names off full
  crowns survived; a wedge cap overturned 15 colours and 8 names.
- **Trace a crossing tail from the TIP upwards.** Picking the nearer balloon edge
  inverted both names — the only 2 corrections in 171 groups.
- **A story can print a PERMUTED palette.** *High-wire Daredevils* colours Louie
  red on 3 of 10 pages. Let dialogue outrank the roster convention and hand back
  a retouch list.
- **Every group a review inserts strands exactly one already-annotated group.**
  Match old to new by (text, occurrence) — never by id, never by text alone.
- **Count `speaker_reviewed` on BOTH engines before calling a review done.** Six
  titles running each finished exactly one group short.
- **A chorus of all four is `other:Donald and the nephews`** — neither `Donald`
  nor `nephews` was accepted.
- **A long droopy beak makes the figure Donald whatever sits on its head**, and a
  capscan zero for blue does not mean Donald is absent.

### Findings to paste into the next run (2026-09-02, twentieth batch)

*Serum to Codfish Cove*, *In Ancient Persia*, *Wild about Flowers*, *Vacation
Time*, *The Pixilated Parrot*. **This is the batch that matters most for the
next Vol. 9 run.**

- **The Vol. 9 cap is a coloured crown with a black band, so its apparent width
  is the VIEWING ANGLE.** Broad from the side (1252px of `#05a4d6`, a 4449px red
  band), a 100-400px rim from above or behind. The same title gives both — do not
  conclude a palette from a sliver. Cap green is H109-121; foliage green H146-150.
- **Vacation Time's cap ink is unreliable and the story proves it.** The same
  clean `#4da33f` H112 crown is Dewey on 078 and Huey on 087/092, both settled by
  Donald using the name. Take the name, record the printed colour.
- **Register is not evidence when the art is readable.** The largest single error
  cluster of the batch: four balloons given to Donald on *Pixilated Parrot* 026
  on grounds of "spokesman" and "only duck at readable size" — with a boy's red
  cap measurable at (353..474). Net **5 `Donald` -> a nephew against 2 back**.
  Run the cap census before writing `Donald` on an untraced balloon.
- **An off-panel line in a monologue is not automatically his.** Three of
  *Vacation Time*'s corrections are balloons over pure scenery in a stretch where
  Donald had been lecturing for four pages. "He had the last line" is momentum.
- **A running motif does not own every instance of itself.** 63 of *Pixilated
  Parrot*'s 334 groups are the parrot's tally, and the one that was not is handed
  over **two balloons earlier**: "MAYBE POLLY WILL HEAR US AND START COUNTING,
  TOO!". Read the previous balloon before assigning the motif.
- **Crop the HEADS, not the balloons.** The only wasted image of the run was a
  four-tile sheet framed on balloons already transcribed; the heads the tails
  point at were below the crop. Take the tip's y from `tailtip.py` and crop
  downwards from it, wide enough for every candidate head plus shoulders.
- **A missed-text finding can already have a box on it** — the group's text is a
  duplicate of its neighbour's, so the fix is a retype, not a new group.
- **`vision_added` means added by hand, not by the pass.** Never strip it, and do
  not exclude those groups when counting corrections.
- **`type_reviewed` silently declines a type proposal**: apply drops it and
  reports a lower count. Say so in the close-out or it is lost.

### Findings to paste into the next run (2026-09-02, twenty-first batch)

*The Magic Hourglass* (Vol. 9, 28 pages, 339 groups), reviewed the same day:
**27 speaker corrections, 8.0%** -- 26 of them in the nephew domain (37.1% of
70). High 25 of 310 (8.1%), medium 2 of 29 (6.9%): the mediums held, the
highs did not. Cost 1.75 images per page. *Big-Top Bedlam* is still under
review.

- **A red or green crown is never Donald, and a blue one is Donald only when
  the head is the biggest in the panel.** Nine corrections, a third of the
  title, are `Donald` -> a boy, and every one came back WITH a cap colour: a
  close-up "of Donald" holding the hourglass (124 g7, blue), "Donald firing
  from the camel" (133 g8, red), "Donald at the liner's rail" (145 g2, red),
  the tallest figure in a line (141 g6, blue). The pass wrote `sole-figure`
  and `balloon-tail` Donald without probing the crown, because the duck was
  big or alone. Vol. 9 prints Donald's sailor hat in Dewey's `#00a5d7`, so a
  blue census line proves nothing either way; a red or green one settles it.
  Never write Donald on a duck whose crown has not been probed.
- **The collision cuts the other way too.** 144 g13, "the boy holding the
  water bag" with 503px of `#08a4d4`, was Donald, and 138 g6 was Donald; the
  blue was his hat. Size the head before naming a blue cap Dewey.
- **Caps come off indoors and are held.** In Scrooge's office (120 p10) the
  boys stand bare-headed with their caps in their hands; the review named all
  three from the held caps ("holding cap") and the red the pass measured on
  one crown belonged to the neighbour's hand. A cap in a hand names its
  holder; a blob at head height beside a bare crown is probably a held cap.
- **Tips on a head boundary went to the collective 4 times and were named
  the other way 5 times** -- a wash, so keep naming, but the frosty unison
  balloon over two scowling boys (121 g7) and a tail 50px short of the
  nearest head on a splash (118 g1) were withdrawn to `nephews`.
- **Six type corrections the pass never proposed**: Scrooge's kitchen
  soliloquy (119) and two others were speech balloons stored as `thought`,
  and two `dialogue` were thought balloons (128 g4, 143 g10). The cloud edge
  is not legible on a 250px montage; check `type` on any balloon whose edge
  you did not see at panel resolution.
- **The reviewer swapped Donald and Scrooge on 129 p8** (g8 -> Scrooge, g9
  -> Donald) against two clean tail readings, and sent 144 g4 "TA TA TA TA!"
  to Scrooge. Worth a second look from the reviewer before those rules are
  believed.
- **A free-text name can carry a typo**: `other:a radier` came back on 140
  g9 and was fixed before the mirror. Grep the `other:` counts for
  singletons every time.
- **`uv run` from the prelim directory silently runs nothing.** The mirror
  was launched with the prelim repo as cwd, printed nothing under the grep,
  and wrote nothing; the verify step caught it. Run every `barks-ocr-*`
  command from the barks-ocr checkout.

### Findings to paste into the next run (2026-09-02, twenty-first batch, second title)

*Big-Top Bedlam* (Vol. 9, 28 pages, 303 groups), reviewed the same day:
**21 speaker corrections, 6.9%** -- 12 in the nephew domain (19.0% of 63).
High 16 of 265 (6.0%), medium 5 of 38 (13.2%). Cost 1.36 images per page.
The batch as a whole: 48 of 642, 7.5%.

- **Nine of the twelve nephew corrections are Dewey and Louie swapped, and
  every one of them had a cap colour measured and recorded the pass's way.**
  Green -> blue five times, blue -> green twice (147 g0/g1, 155 g10, 158
  g1/g2, 165 g0). The pass read `#4da33e` and `#00a5d7` off the crowns, so
  either the colourist swaps those two boys in this title or the reviewer
  reads the pair the other way; two crowns in one row cannot both be right.
  The next Vol. 9 title should crop one clean blue-and-green pair at 4x and
  say which ink the review calls Dewey before naming any of them.
- **The disguises are not all Zippo.** The review moved four `other:Zippo`
  to `other:a clown` (the hoop clown on 161, the pie clown on 162-163) and
  one clown back to Zippo (159 g8), while the bathrobe man's `I SMELL
  SARDINES!` and one ZIP went to Donald. A quick-change plot does not
  license naming every costume after the artist; name the costume unless
  the story shows the change.
- **Sixteen type corrections, twelve the pass never proposed**: the
  ringmaster's off-panel patter over the acts was stored `narration` and is
  `dialogue` (155 g0/g1/g5), `SHOW TIME!` is `narration` not `background`,
  and four thought/dialogue flips. An off-panel voice in a box with no tail
  still needs its type read from the drawing, not from the box.
- **The free-text case trap again**: two `other:zippo` came back beside 46
  `other:Zippo` and were folded before the mirror.
- **A review can retype a group's text**: 165 g7 came back as `FIRE!\nOW!`
  with g8 `FIRE!`, both unreviewed and both engines the same, so g8 now
  duplicates its neighbour's word over the `OW!` box. Check `ai_text` on the
  stragglers before trusting the queue.

### Findings to paste into the next run (2026-09-02, twenty-second batch)

*You Can't Guess!* (Vol. 9, 25 pages, 363 groups after the review added six),
reviewed the same day: **18 speaker corrections, 5.0%**, of which 6 are the
reviewer's own added licence-plate groups moving from `unknown` to `none`, so
the pass's real count is **12 of 357, 3.4%** -- 12 in the nephew domain (10.5%
of 114). High 11 of 355 (3.1%), medium 2 of 2 (100%). Cost 1.64 images per
page. *Dangerous Disguise* and *No Such Varmint* (Vol. 10) are still under
review.

- **A clean tail onto a clean cap was withdrawn to `nephews` five times, and
  the pass's note was right each time.** 178 g0, 184 g1, 184 g8, 189 g11 and
  191 g3 all had a tail measured onto one boy and a big winter stocking cap
  measured on him (2318px of `#02a4d6` on 191 g3), and every one came back
  `nephews` with the cap cleared. Against that the review also NAMED two
  collectives (187 g5, 191 g11), so the reviewer is not applying a bare-head
  rule; the five look like tails the reviewer read differently. Worth a second
  look from the reviewer before this is believed as a rule, because taken at
  face value it says a stocking cap is not a name.
- **Both medium calls were corrected, and both were the tip-versus-lean case.**
  177 g9 (tip 4px inside the blue boy, leaning to the red one) and 178 g8 (the
  upper of two joined balloons, given to the blue boy by balloon order) both
  went to the boy the tail LEANED toward. With 176 g1 (a tail "straight down
  over the green cap" that the review sent to the red boy beside him) and 176
  g8 (the GULP! sent to the blue boy behind the red one), all four swaps are a
  tail between two boys where the pass took the nearer head. Where the tip sits
  in a gap, the lean beat the tip 4-0 here -- the opposite of what the Vol. 8
  batches found. Say `nephews` on a gap-landing tip rather than pick a side.
- **Scrooge's top hat names Scrooge even on a duck who is bleating.** 187 g11,
  the BAAAAA, was Donald in the pass because the story had just hypnotised
  Donald; the review made it Scrooge, and the figure wears Scrooge's top hat
  and pince-nez. A hat is evidence for an adult exactly as a cap is for a boy;
  the plot is not.
- **Twelve type corrections the pass never proposed**, on top of the nine it
  did: 185 g0 (Scrooge's cubic-acres line stored as dialogue is a thought),
  183 g4 (the CHRISTMAS TREES lot sign was `sound_effect`), 181 g9 (Daisy's
  BZZZT whisper, which the pass had already flipped, came back) and the like.
  A stored `sound_effect` on a sign is as wrong as one on a voice; check the
  type on every non-balloon group, not only the ones the roster's examples
  cover.
- **The reviewer grouped the four 313 licence plates the pass had put on the
  ignore list**, and the added groups were seeded from a neighbour: 181
  easyocr g6 arrived with `identified_by: ['caption']` and Daisy's note, and
  landed at id 6 on one engine and id 12 on the other. The mirror pairs by
  text so the id shift was harmless, but the residue had to be cleared by hand
  before the write. Do not put a prop number on the ignore list until the
  reviewer has said so; and after any review, diff the added groups' fields
  on both engines before mirroring.
- **The wedge cap is back in Vol. 10 (a black crown with one coloured side
  patch), and the water prints in the wedge blue.** *Dangerous Disguise* and
  *No Such Varmint* are beach and bay stories drawn on `#00a5d7` sea, the same
  ink as the blue wedge, so `heads.py` reports blue on every boy standing in
  front of water. A blue reading there is worthless without a crop; red and
  green are still reliable. The green wedge itself prints anywhere from
  `#4da33e` (H111) to `#40a264` (H142), one hue-band from the `#009e49`
  foliage.

### Findings to paste into the next run (2026-09-03, twenty-second batch, second title)

*Dangerous Disguise* (Vol. 10, 28 pages, 328 groups after the review added
four), reviewed the next day: **30 speaker corrections, 9.1%**, of which 4 are
the reviewer's added `!` and `? ? ?` groups and 1 is a free-text rename, so the
pass's real count is **25 of 324, 7.7%** -- 25 in the nephew domain (34.7% of
72). High 26 of 316 (8.2%), medium 2 of 8 (25%). Cost 1.32 images per page.
The first Vol. 10 title read, and the first with the wedge cap on blue water.

- **Twelve collectives were named, and every one had a note saying the wedge
  did not read.** 017 g3, 021 g0/g1 (three heads poking out of the SAND), 028
  g0/g1/g2 (three boys in the reeds, a chain of three balloons), 043 g11/g12
  -- all tiny figures where a probe of the crown found nothing, and the review
  named them red, green and blue regardless. Twelve of 25 is the whole
  under-naming class, and it is the wedge-cap title's version of the *New
  Toys* finding: **a probe zero on a wedge cap is a reason to crop at 3x, not a
  verdict.** The wedge is a few dozen pixels on a 60px head and sits on
  whichever side faces away as often as not.
- **Blue near water, hoses or sky is the sea, not a cap.** 036 g4 and 041 g7
  are the boy holding the cold-water hose, named Dewey off 900px and 2700px of
  `#06a4d5` on his head, and both came back Huey: the blue was the water
  spraying past his cap. 020 g8 and 021 g5 went to blue the other way. The
  Vol. 10 wedge blue and the Vol. 10 sea are the same `#00a5d7`, so on a beach
  page `heads.py` cannot tell one from the other. Red and green survived far
  better (023 g9 and 017 g11 are the two green/red reversals, both slivers
  under 600px).
- **A one-boy panel is still not a name when his wedge faces away.** 018 g0
  (Huey -> Dewey, reviewer: "next panel is Dewey") and 032 g5 (Donald -> Huey)
  were named from the figure in frame; the review used the adjacent panel's
  continuity. Read the page as a sequence: a boy who walks out of one panel is
  the boy who walks into the next.
- **Register beat the drawing three times, all adults.** 042 g2 ("...WILL HANG
  ZE MEDAL AROUND YOUR PRETTY NECK") is the bullfighter speaking TO Madame,
  not Madame; 025 g1 ("HAPPY LANDINGS, OPERATOR MINUS-X!") is the boys, not
  Donald; 024 g10 ("NOW SUPPOSE YOU JUMP, CHUM!") went to Huey. Read who is
  addressed before deciding who speaks: a second-person line about a pretty
  neck is not said by its owner.
- **Five thought balloons stored as dialogue went unflagged** (018 g5, 019
  g6/g7, 020 g0, 030 g1), on top of the eight type corrections the pass made.
  The pass corrected every sound_effect on a voice and missed every cloud
  edge, again. Check the balloon edge on every thought-shaped line, not the
  type field.
- **Two of the eight mediums were reversed, both the gap-landing tip** (020
  g8, 021 g5), which matches the *You Can't Guess!* finding above: where the
  tip sits between two boys the pass loses either way, so `nephews`.

### Findings to paste into the next run (2026-09-03, twenty-second batch, third title)

*No Such Varmint* (Vol. 10, 28 pages, 335 groups after the review added one),
reviewed the next day: **69 speaker corrections, 20.6%** -- 67 in the nephew
domain (36.4% of 184), the worst figure in this file. High 58 of 304 (19.1%),
medium 10 of 30 (33.3%). Cost 1.11 images per page, the cheapest of the three,
and that is the finding.

- **FIFTY collectives were named, and the pass had declined every one of them
  on a probe zero.** 26 are figures the note calls tiny (boys on a wall, in a
  boat, in the reeds, on a rock across the bay), 21 are boys at readable size
  whose crown probed no ink, 3 are the bare-headed boys on the sofa (071
  g0-g2) whom the review named from the caps lying beside them ("holding
  cap"). The reviewer read the wedge on all fifty. `probe.py` on a 60px head
  finds nothing because the wedge is a dozen pixels of ink on the far side of
  the crown; it is not evidence of absence. **On a wedge-cap title every boy
  who speaks gets a 3x crop of his head**, tiled three or four to a sheet --
  one image a page would have bought most of the fifty, and the title had two
  images a page to spare.
- **Twelve wedge colours were overturned, every one a sliver under 600px read
  from a census or a 0.8x crop**: green -> blue four times (077 g8, 079 g9,
  080 g8, 071 g14 red -> blue), red -> blue three times, red -> green and
  green -> red twice each. No direction, so noise, exactly the Vol. 7 wedge
  signature. Under a few hundred pixels the hue is not readable in-process;
  crop at 4x and look.
- **A cap on the sofa beside a bare head names the boy sitting nearest it.**
  071 g0-g2: the review wrote "holding cap" on all three. The *Magic
  Hourglass* rule (a cap in a hand names its holder) extends to a cap lying at
  a boy's side indoors.
- **Flute notes are dialogue.** The pass proposed `sound_effect` on the
  TWEETLE groups (073 g2/g4, 077 g4/g5), reasoning that a flute is not a voice
  like the whistled tune in the roster; the review put all four back to
  dialogue. Music a character makes on the panel is that character's line.
  The ROAR on 079 g3 went the other way, to `none` and `sound_effect`,
  because it is the outboard motor at the stern, not the serpent: the pass
  read the word's content into the nearest creature. The serpent's SNORF! and
  HIC! stayed dialogue, so the animal-voice rule holds; read the drawing under
  the lettering, not the onomatopoeia.
- **Two names were withdrawn (073 g9, 075 g10), both red slivers under 400px
  where a boy was pushing or pointing and the tail was long.** With the
  twelve swaps that is fourteen wedge reads wrong against fifty declined; the
  balance still says crop and name.
- **The text correction on 083 g5 (SNARF! -> SNORF!) was accepted after the
  mirror**, in a separate commit; a text correction has its own review state
  and the speaker count says nothing about it.

### Findings to paste into the next run (2026-09-03, twenty-third batch)

*A Financial Fable* (Vol. 10, 10 pages, 120 groups after the review added
one), reviewed the same day and mirrored clean: **5 speaker corrections,
4.2%**, of which 1 is the reviewer's own added CLOSED sign (100 g20, unknown
-> none), so the pass's real count is **4 of 119, 3.4%** -- all 4 in the
nephew domain (28.6% of 14). No mediums were written. Cost 1.8 images per
page. *Operation St. Bernard* and *The April Foolers* are still under review.

- **The boys lecture Donald, not the other way round.** 092 g6 (IF YOU'RE
  GONNA WEAR WARM WOOL JACKETS, YOU GOTTA WORK TO GET THE WOOL!) and 092 g9
  (...YOU GOTTA WORK TO GET THE EGGS!) went Donald -> Huey and Donald ->
  Louie. Donald has just said I HATE WORK, and YOU GOTTA WORK is said *to*
  the complainer; the pass read the panel as an adult lecturing a child and
  never traced either tail. Half the title's corrections. Read who is
  addressed before deciding who speaks, and trace the tail even when the
  register looks settled -- the caps were there to read (the census had the
  egg boy's green at 325px and the pass wrote it off as furniture).
- **A probe zero on a wedge is still not a verdict**, on the first title
  where the pass thought it had learned that. 096 g8: the note reads "at 2.5x
  his black crown shows no coloured wedge", and the review named Louie. The
  probe box was 100 pixels wide on a crown that turns away from the reader;
  one more crop at 4x would have found the wedge on the far side.
- **A gap-landing tip is named by its lean.** 096 g9: the tail "angles
  down-right and its tip lands in the gap between the middle boy (blue) and
  the right boy (red)", recorded as `nephews` under the twenty-second batch's
  rule, and the review gave it to the red boy the tail leaned toward. That
  makes the lean 5-0 over the tip across two batches and 1-0 over declining.
  Where the tip sits in a gap, take the boy the tail leans toward; do not
  pick the nearer head, and do not decline.
- **The added group arrived clean.** 100 g20 (a CLOSED sign on panel 5) came
  with `vision_added`, no `identified_by`, no `vision_note`, `none` on
  easyocr and `unknown`/`low` on paddleocr, which the mirror overwrote. No
  residue to clear -- the first added group in five titles that needed no
  hand edit.
- **`review_findings.py` lists every `type_was`, not only this review's.**
  It reported four type corrections; 093 g5/g6 and 099 g14 already carried
  their `type_was` at the pass commit, from an earlier sweep. Only 095 g0
  (the pass's own dialogue -> thought) belongs to this review. Check
  `git show <pass-commit>` before counting a type correction against a pass.
- **The licence plate 313 on 099 was not grouped.** The missed-text audit
  still reports it; the reviewer grouped the plates on *You Can't Guess!*
  and left this one, so a prop number is the reviewer's call each time and
  the audit line stays until they say ignore.

### Findings to paste into the next run (2026-09-03, twenty-third batch, second title)

*Operation St. Bernard* (Vol. 10, 10 pages, 135 groups after the review added
one), reviewed the same day and mirrored clean: **5 speaker corrections,
3.7%**, of which 1 is the reviewer's added `? ?` over Donald on 054 p7, so the
pass's real count is **4 of 134, 3.0%** -- 3 in the nephew domain (5.3% of
57). No mediums written. Cost 1.4 images per page. A winter title with no cap
ink anywhere, so every correction is about tails and register, not colour.

- **Two boys named by dialogue name the third.** 054 g2 (OH, BOY! OH, BOY!)
  was `nephews` because the boys are bare-headed indoors; the review made it
  Huey with the note "Not Dewey or Louie" -- the other two boys in the same
  panel are Dewey and Louie by the Colonel address chain. Elimination is
  accepted when all three are in frame and two carry a name from the
  dialogue. The pass had both names in its own notes on the neighbouring
  groups and did not use them.
- **THE KIDS is Donald's word.** 063 g4 (IT'S THE KIDS!) went to the chief
  because the balloon sat over him; the review gave it to Donald. The chief
  calls the boys Colonels in every one of his 25 lines and never anything
  else. Where two adults share a panel and a balloon sits between them, the
  vocabulary decides before the balloon position does.
- **Two tails read wrong on a 0.55x contact sheet, one each way.** 057 g9
  (ALL HE DOES IS HUDDLE ON THE WARM SIDE OF THE TREES!) Donald -> nephews,
  and 056 g2 (OR ELSE HE DOESN'T WANT TO GET HIS FEET WET!) nephews ->
  Donald. Both were adult-against-boys calls settled from a half-scale sheet
  of four panels, the cheapest view the run used. When the question is Donald
  against a boy and the panel holds both, the sheet tile needs to be 0.8x or
  the panel read on its own.
- **The pass missed a device it had already described.** The `? ?` over
  Donald on 054 p7 is in the pass's note for group 15 ("Donald ... stands
  between the two boys with a ? over him") and nowhere else: not grouped by
  either engine, not in `visible_text`, so the missed-text audit could not
  see it. A drawn device the note mentions belongs in `visible_text` too.
- **The added group arrived clean on both engines** (`identified_by`
  `balloon-tail`, no note, `speaker_reviewed` on both). Second clean add in
  a row since the editor started insisting on `identified_by`.
- **Two of the four type corrections predate the pass** (056 g0, 056 g11 --
  `type_was` already at the pass commit); the pass's own two (054 g5 DOGS
  book cover, 058 g4 PANT! PUFF!) were confirmed.

### Findings to paste into the next run (2026-09-03, twenty-third batch, third title)

*The April Foolers* (Vol. 10, 10 pages, 129 groups after the review added
one), reviewed the same day and mirrored clean: **14 speaker corrections,
10.9%**, of which 1 is the reviewer's added MEIN KAMPF book cover (103 g2)
and 1 a caption that is really a boy's line, so the pass's real count is
**12 of 128, 9.4%** -- all 12 in the nephew domain (16.4% of 73). No mediums
written. Cost 2.7 images per page, the dearest of the three, and the title
that bought the most crops still under-named the most.

- **TEN COLLECTIVES WERE NAMED, AND EVERY ONE HAS A NOTE SAYING THE WEDGE
  DID NOT READ.** 102 g9 ("only a dull olive patch"), 103 g3 ("no wedge at
  0.8x and a probe finds no cap ink"), 105 g12/g13 ("a dark olive patch at
  3x"), 106 g4 ("cropped at 2x his crown is wholly black"), 107 g10/g11,
  108 g4, 109 g10 ("only 45px of desaturated water blue"), 103 g9 (tiny
  figures). The reviewer read red, green and blue on all ten. Two things
  follow. A **dull olive patch on a black crown IS the green wedge in
  shadow** (105 g12, 106 g4, 108 g4 all went to Louie), so a desaturated
  patch is a colour, not an absence -- the *Cap slivers drift teal* rule for
  green. And a wedge sits on the far side of the crown from the reader as
  often as not, so a probe box on the visible side reads nothing; when the
  crown probes empty, the answer is the wedge on the OTHER side, which
  needs the full head at 4x, not a 100px box.
- **A probe can still name the wrong boy.** 107 g9 went Dewey -> Louie with
  325px of #06a5d5 on the probe, and 108 g8 Huey -> Dewey off a red sliver
  read at 0.6x. On 107 p7 the boy is lying on his back laughing with a blue
  fence rail behind his head; the blue was the rail. Rank the probe against
  what is behind the head (the Vol. 10 palette note), and a crown seen
  from an odd angle needs the crop, not the census.
- **A drop-capital box is not always the narrator.** 103 g12 (WHEN HE
  REACHES FOR THE WALLET, WE JERK IT AWAY AND YELL APRIL FOOL!) is a yellow
  box with a drop capital and a first-person plural; the review made it
  `nephews` and `dialogue`. WE is not the narrator's word. The Vol. 9
  finding (a yellow box with an arrow tail is the narrator) has its
  converse: a box with the boys' pronoun in it is a boy speaking.
- **The insert ate the page's tail again.** 103 gained one group at id 2,
  every later id shifted, and the last id (old g13, Donald's thought) came
  back unreviewed; a one-line queue fixed it. Count `speaker_reviewed`
  against the group count on any page that gained a group before calling
  the review done, as *Reviews finish one group short* says.
- **The pass's seven type proposals all held**: four bubble-trailed
  balloons of Donald's stored as dialogue and the three ZZZ snores plus one
  more moved to dialogue with the sleepers named. Three more `type_was`
  entries (105 g4, 106 g1, 107 g9) predate the pass.

**Batch summary, twenty-third batch (Vol. 10, 30 pages, 383 groups after
three adds):** 24 speaker corrections, of which 3 are reviewer-added groups,
so **21 of 380, 5.5%**; nephew domain **19 of 144, 13.2%**. Split by title
3.4% / 3.0% / 9.4%. Cost 1.97 images per page. Every correction in the
nephew domain on the wedge-cap title is an under-naming or a wedge misread;
the two titles with no readable cap came in under 3.5% on dialogue and tails
alone.

### Findings to paste into the next run (2026-09-03, twenty-fourth batch)

*In Old California!* (Vol. 10, 28 pages, 373 groups after the review added
one), reviewed the same day and mirrored clean: **32 speaker corrections,
8.6%**, of which 2 are the reviewer's added `? ? ?` and its neighbour, so
the pass's real count is **30 of 372, 8.1%** -- 28 in the nephew domain
(28.3% of 99). Cost 2.43 images per page. Confidence: **high 21 of 343,
6.1%; medium 9 of 28, 32.1%.** Four type corrections, two of them the
pass's own (both held), two the review's (129 g12 thought -> dialogue,
134 g20 the `$ $ $` balloon background -> dialogue, Donald).

- **A CLOSE-UP HEAD IS NOT DONALD BY DEFAULT.** 117 g4 (SURE! JUST LIKE
  INDIANS LIVED...), 120 g9 (HOLD IT! I SEE SMOKE!) and 121 g2 (I DON'T CARE
  WHO LIVES THERE!) were written `sole-figure` Donald on panels that hold
  one big duck head, and the review gave them to Louie, Louie and Huey. On
  117 p3 the census had 132px of cap green ON that head and the note called
  it "a boy's cap intruding at the left edge". A single big head earns one
  probe: Donald's cap prints `#016ca7`, a boy's wedge one of the three, and
  a beak-and-eye close-up hides the size cue. Three of the title's fourteen
  Donald -> a boy corrections were this one move.
- **Donald's lines went to the boys fourteen times and the boys' to Donald
  three.** Beyond the close-ups, 116 g0/g3, 117 g9, 118 g5, 119 g1, 120 g11
  and 137 g0 were adult-register lines on panels holding Donald AND boys,
  every one settled by register ("the lecture continues", "the leader's
  line") with the tail tip 50-120px from either head. On this title the
  boys lecture, decide and proclaim; register lost 14-3. Where the tip is
  within a head-width of a boy, the boy has it whatever the words sound
  like.
- **A row of three shifted by one, twice.** 134 g18/g19: the caps were
  measured red, blue, green left to right, the tips fell over the blue and
  green boys, and the review named the red and blue boys -- both tails one
  figure left of where the tip x said. The head spans came from beak boxes
  on running figures, whose heads lead the beak. When the census gives the
  spans, crop the row once before naming three from it.
- **The gap-lean rule went 0 for 2 here.** 113 g14 (tip in the gap, leaned
  right, named the red boy) came back `nephews`; 138 g0 (gap, leaned right,
  named green) came back Dewey, the boy on the OTHER side. With 2 for 2
  against after 5 for 0 for, the lean is a tie-break for a tip that stops
  short of two heads, not a rule that names one.
- **Brown-red wedges are not red.** 124 g8 (#8e542a, H19) and 137 g10 named
  Huey off a dull red-brown wedge came back `nephews`, and 135 g2's
  "red-brown wedge" was a blue one (Huey -> Dewey). Vol. 10's red in shade
  can print brown, but a hue under 25 with S under 0.7 is unreadable, not
  red: record the collective and say why.
- **A yellow caption box can be the boys'.** 126 g8 (TONS OF BARBECUED MEAT,
  AND FRIJOLES AND TAMALES...) was written `narrator` off the box; the review
  made it `nephews` and left the type narration. The April Foolers rule (WE
  is not the narrator's word) has a sibling: a menu recited with relish is a
  boy's.
- **The flagged conflicts split 1-1.** 122 g11 (PUT THE GUN AWAY!, the tail
  on Don Gaspar who holds the rifle) went to Don Gaspar: the tail won over
  the sense of the line. 132 g3 (SOME WALK!, flagged for the tail leaning
  toward the boys) held as Donald. Flag them; do not pre-empt them.
- **The review's add carried a false `vision_added`.** 127 gained `? ? ?`
  on both engines, and on easyocr the neighbouring AND THEN! caption came
  back as g19 with `vision_added: true` that the pass commit shows it never
  had; paddleocr's copy has no flag. The mirror is by text so nothing
  crossed wrongly, but the group audit now reports one hand-added group on
  one engine only, and it is this artefact, not a missing group. Left in
  place -- a `vision_added` is provenance until someone says otherwise.
- **A thought balloon stored on a speech balloon went unchecked.** 129 g12
  (I THINK THERE IS SOMETHING WE CAN DO! I'LL SEE!) is a pointed-tail balloon
  stored as `thought`; the pass read the speaker and never the type. The
  type rule is a drawing test and costs nothing on the montage.
- **The licence plate 313 on 112 was left ungrouped**, as on The April
  Foolers 099; the audit line stays.

### Findings to paste into the next run (2026-09-03, twenty-fourth batch, second title)

*Knightly Rivals* (Vol. 10, 10 pages, 137 groups after the review added
one), reviewed the same day and mirrored clean: **17 speaker corrections,
12.4%**, of which 1 is the reviewer's added ACT I label, so the pass's real
count is **16 of 136, 11.8%** -- 8 in the nephew domain (29.6% of 27). Cost
1.6 images per page, the cheapest title of the batch and the worst rate.
High 15 of 129, 11.6%; medium 2 of 7. Three type corrections, two of them
the pass's own SNORT! moves (held) and one the review's (142 g0, the
director's opening line stored as narration).

- **DAISY IS THE HAIR BOW, NOT THE DRESS.** 141 g11 and 142 g5 were given to
  `other:the drama-club director` because the speaker wore a blue dress and
  held the script; both were Daisy. The two women swap dress colours from
  panel to panel in this story, and the only constant is Daisy's red bow and
  the director's brown hair and spectacles. Name an adult woman off the
  feature Barks keeps fixed, not off the ink the colourist changes.
- **A CROWN CROP THAT STOPS AT THE BROW MISSES THE WEDGE.** All five of 140's
  collectives (p4 g4-g6, p7 g9-g10) were named by the review, one by
  elimination; the pass had cropped a strip across the crown fronts at 2.5x
  and called them black. The wedge sits at the top and back of the crown.
  Crop the whole head with air above it, as the April Foolers rule says, and
  a probe box the same. 140 g2, the one name the pass DID make off a 551px
  census green, was withdrawn -- the hedge behind the boys is green too.
- **The close-up rule did not survive one title.** 147 g14 (YOU JOKERS KNOW
  VERY WELL WHO IS GOING TO WIN THAT DUEL! SHUT UP!) is one big head at the
  left with 401px of red on its crown in the census, written Donald; the
  review made it Huey. Written the same day as the In Old California! finding
  that says exactly this. One big head, one probe, before Donald.
- **Track who is inside the armour panel by panel.** 145 g4 (I'M THE GUY THAT
  CAN PUT THE CHIV IN CHIVALRY!) went Donald -> Gladstone: on 145 the armoured
  knight is Gladstone, with Donald in his sailor suit calling him a tinhorn
  show-off on the same page. The pass carried "Donald is the one in armour"
  over from 142-143.
- **A balloon over two brawlers is a chorus of two.** 142 g4 (THAT LETS HIM
  OUT!, each pointing a thumb at the other) and 144 g9 (OH, YEAH? WELL, WE'LL
  DECIDE THAT RIGHT NOW!) both became `other:Donald and Gladstone`; the pass
  had picked the one whose beak was open.
- **Do not build a plot to name a costume.** The pass reasoned that the
  magnetised pair must be inside the ogre suit on 149 and gave the ogre's
  four lines to `other:Donald and Gladstone`. The review made the ogre
  `other:another actor` (149 g4, g7), gave OUCH! AIN'T I SUPPOSED TO BE
  PADDED to the `nephews` in the knight suit who take the blow, and the
  closing CHIVALRY, PHOOEY! to Daisy, whose hennin is the tall silhouette
  chasing the three small knights. Where a figure is a costume and nothing
  on the page says who wears it, `other:` the costume and let the reviewer
  decide.
- **The reviewer's `other:` value is `other:another actor`**, now on 2 groups;
  reuse it rather than inventing a synonym.
- **The added group arrived clean** (144 g7 ACT I, `none`, reviewed, flagged
  on both engines) and the last id on the page came back unreviewed, as
  *Reviews finish one group short* predicts; one queue line fixed it. ACT I
  was lettering the pass never put in `visible_text`, which is the gap the
  skill now closes.

**Batch summary, twenty-fourth batch (Vol. 10, 38 pages, 510 groups after
two adds):** 49 speaker corrections, of which 3 are reviewer-added groups or
their neighbours, so **46 of 508, 9.1%**; nephew domain **36 of 126, 28.6%**.
Split by title 8.1% / 11.8%. Cost 2.2 images per page. Neither title's error
is a wedge left uncropped: it is Donald taking lines that belong to the boys
(17 of the 46), one big head read as Donald three times on each title, and
two costume or dress-colour identities carried across panels.

## Per-volume cap palette

Not in the skill, because it is per volume. Vol. 2, from the reference panel at
p117 panel 3 (the boys hold their caps at Daisy's door):

| | |
|---|---|
| green (Louie) | `#009d44` |
| red (Huey) | `#e41920` |
| blue (Dewey) | `#00a5d5` |
| shaded reds seen | `#9f2e1d`, `#86351c` |
| shaded teals seen | `#1a9c8f`, `#29948b` |

Paste these into a prompt that continues the same volume. Match dim crowns
against the hexes, not against an idea of red.

Vol. 3, from *Mystery of the Swamp* 016 panel 8, and re-measured on four more
titles 2026-08-11/13:

| | |
|---|---|
| red (Huey) | `#e71a21` |
| blue (Dewey) | `#04a4d6` |
| green (Louie) | `#039d45` |
| solid winter caps, *Pumpkinburg* 044 p7 | `#e71a21` `#01a2d3` `#009d43` |
| black-cap segments, *Icebox Robber* 072 p2 | `#e41921` `#06a4d0` `#019d42` |
| thin slivers, *Icebox Robber* 072 p3 | `#db3131` `#159cad` `#2f8780` |
| small figures, *Pumpkinburg* 047 p8 | `#da1e25` `#0da2cf` `#109592` |
| tiny figures, *Pumpkinburg* 053 p4 | `#de1749` `#219a94` `#3d7d4e` |
| black-cap segments, *Pecking Order* 075 p2 | `#d72b2f` `#0f9fa7` `#039e4f` |
| large caps, *Pecking Order* 083 p2 | `#de1a21` `#09a1d5` `#099b46` |
| backs to reader, *Days at the Lazy K* 093 p4 | `#e21723` `#0ca1d2` `#039c44` |
| caps lifted off, *Days at the Lazy K* 094 p11 | `#e4181f` `#09a2d4` `#029d43` |
| caps knocked off, *Days at the Lazy K* 099 p11 | `#e5191f` `#01a3d3` `#019d43` |
| wide side band, *Eyes in the Dark* 101 p4 | `#e41920` `#08a3ce` `#089c6a` |
| solid deerstalkers, *Thug Busters* 113 p1 | `#e71a21` `#01a2d4` `#009d46` |
| segmented swim caps, *The Great Ski Race* 127 p8 | `#e71a21` `#05a2d4` `#039b43` |
| banded black caps, *The Firebug* 208 p10 | `#e61b1e` `#089fc4` `#019d46` |
| wedged black caps, *Ten-Dollar Dither* 128 p2 | `#e51720` `#01a3d4` `#009d46` |
| band + mittens, *Donald Duck's Best Christmas* 138 p2 | `#e41c24` `#04a4d4` `#049c8c` |
| stocking caps, *Silent Night* 251 p8 | `#e41c1c` `#04a4d4` `#049c44` |
| caps + mittens, *Donald Tames His Temper* 147 p3 | `#e41c24` `#04a4d4` `#049c44` |
| banded black caps, *Singapore Joe* 165 p5 | `#e41a1d` `#04a2d5` `#079b45` |
| banded black caps, *Master Ice Fisher* 166 p5 | `#d91a20` `#08a3cc` `#089a46` |
| banded black caps, *Jet Rescue* 176 p3 | `#e61921` `#0ea2c6` `#049b43` |
| banded black caps, *Donald's Monster Kite* 189 p4 | `#d91c24` `#07a3d1` `#278079` |

**Three more banded-black-cap titles, and between them five panels that print
two caps in ONE ink.** All three use the black crown with a coloured band, the
same construction as *Pecking Order* and *The Firebug*, and all three print the
canonical three inks when they print them cleanly. What they add is the failure
mode: `#13a1cb` on two of three caps (*Singapore Joe* 158 p6), `#2f9383` (*Master
Ice Fisher* 171 p5), `#139a7b` (175 p3), `#0e9649` (*Jet Rescue* 177 p4) and
`#139c82` (184 p2), each confirmed at 5-6x over disjoint boxes. Two of the three
titles also shuffle the boys' left-to-right order from panel to panel — *Master
Ice Fisher* 166 p5 seats them red/GREEN/blue, *Jet Rescue* 177 p1 blue/red/green —
so seating is no anchor in any of them, and the panel next door is.

Their green also drifts further than the volume's usual H145: *Singapore Joe*
runs H145-H179 and *Master Ice Fisher* H140-H170, so the blue is repeatedly the
muddier-looking cap and must be ranked inside its own panel every time.

*Donald's Monster Kite* is the same banded black cap, and its green drifts as
far as anything in the volume: H146 when it prints cleanly but H157, H175, H177,
H180 and H181 on thin slivers, so on that title **hue alone does not separate the
two cool caps** and value does — its greens sit at V0.55-0.61 against the blues'
V0.72-0.83. It also prints two caps in one ink four times (189 p7 two greens,
189 p8 both `#208878`, 191 p3 both `#109898`), and takes every cap off for the
three panels set indoors at home on 195.

**A third construction, and it flips the reading rule.** *Eyes in the Dark* puts
one large coloured band down the side of the cap, about a third of the crown —
it reads at a glance and is used on every page. But its green prints at **H160**,
not the H145 above, and both cool caps come out at S0.9+. On that title **hue is
the discriminator and saturation is not**, which is the reverse of the thin-sliver
rule below. Say in the note which one you used.

*Days at the Lazy K* is the segmented black cap throughout, and gave a
colouring fault worth knowing about: 098 p12 prints two of the three caps in the
same green, identical at 10x, with the third a clean red. Two caps the same
colour name neither.

Vol. 3 also has titles with no nephews in them at all. *The Riddle of the Red
Hat* is the Mickey Mouse back-of-book strip — no caps anywhere, and `Black Pete`
arrives as a bare roster value the database supplies for that story.

**A fourth and a fifth construction, and one title with no caps for a whole
page.** *Thug Busters* puts the boys in big solid single-colour deerstalkers,
worn on every page and readable at a glance — the easiest cap in the volume, and
the story checks the convention itself: 110 p9 names the blue-capped boy
Inspector Dewey, and on 115 p7 the red cap speaks and the next balloon answers
him as Inspector Huey. *The Great Ski Race* uses a segmented swim cap, black
crown with one coloured band, but only in the boat and beach panels; the boys are
bare-headed through most of 118, 119 and 125, which is why a third of that
title's calls are collectives. *The Firebug* uses a broad band across a black
crown and confirms the convention in its own captions — 200 p1 reads "DEWEY SPIES
SMOKE" over a boy in the blue band.

**A teal band that is either ink, and only its own panel decides.** *The Firebug*
prints the blue at H168-176 in about a third of its panels — muddy enough to look
green, saturated enough not to be. It is the BLUE where the panel's other cool
cap is a clean green (198 p6 `#0ea58c` beside `#069952`; 201 p7 `#0ea285` beside
`#0a9c51`) and the GREEN where the other is a clean blue (205 p10 `#10968c`
beside `#09a3d4`). The same printed colour, opposite answers. Do not carry a
reading of it from one panel to the next: rank the two cool caps against each
other inside the panel, exactly as for the thin slivers, and say in the note that
the call was made by elimination.

**And a page where the shirts carry the colour instead.** *The Firebug* 197 has
no caps at all: the boys wear coloured shirts, green `#0a9846` (H145) and blue
`#14a5c3` (H190), which are the cap inks to within a few counts — but the third
shirt is ORANGE `#ec681d`, not the red ink, so that boy is named by elimination
and not by matching. No panel in the title shows a coloured shirt and a cap
together, so the whole page rests on that one inference; it was read at medium
throughout and the review promoted all of it. Look for the bridging panel first,
and hedge the page if there is none.

**A sixth and a seventh construction, and both put the colour on the HANDS.**
*Donald Duck's Best Christmas* gives the boys a thin band across the black
crown plus **matching mittens**, and the mittens are the readable half: on 143
the caps are gone entirely and only the mittens name anyone, and on 143 p4/p5/p8
there is neither. Its green drifts H145-H176 across the title, so hue **and
value** separate it from the blue (both sit at S0.97) — saturation does not.
*Silent Night* and *Donald Tames His Temper* both use big solid single-colour
stocking caps with a pompom, the easiest cap in the volume, and *Temper* adds
the matching mittens again. Both print the identical three inks, `#e41c24` /
`#04a4d4` (H194 V0.83) / `#049c44` (H145 V0.61).

**But all three are winter stories where the caps come off indoors.** That is
the thing to plan for, not the hue: *Silent Night* is bare-headed for 250 and
the first four panels of 251, and *Temper* from 149 p3 to the end, which is 107
of its 161 groups. Both titles finish on 59 and 27 `nephews` collectives — not
because a readable cap was declined, but because nothing is printed. Say which
it is in the note; the two look identical in a queue and only one of them is an
error worth correcting.

**Vol. 3 uses seven cap constructions and sometimes none at all**, so do not
assume from one title what the next one shows. *Pumpkinburg* is a winter story
with big solid stocking caps that read at a glance; *The Icebox Robber* uses
the black cap with coloured segments, and only on one of its ten pages;
*Webfooted Wrangler* has the boys in identical brown ten-gallon hats from the
splash on and offers no colour anywhere in the title. *Pecking Order* uses the
black cap with segments too, but throughout, not on one page — so "which
construction" is per title and "how many pages carry it" is a separate question.

**A dark, muddy segment beside a clean bright one is the GREEN, not a second
blue** — and "the two of them look alike, so neither counts" is a trap that has
now cost seven names across three sessions. In *Pecking Order* the pass measured
`#21949a` next to `#3f737e` on 076 p4, and `#29969f` next to `#335f68` on 077 p8,
called each pair "the same hue at two lightnesses, B above G in all four", and
recorded both as unreadable. The review named the darker one **green** every
time — 3 for 3, plus three more collectives it named outright.

B against G is **not** the discriminator when the segment is small. Saturation
is: a blue segment stays saturated however tiny, so one that has gone muddy at
all is a thinned green whatever B is doing. `#3f737e` and `#335f68` are both
about 50% saturated; the blues beside them are 95%.

And rank the segments **against each other inside the panel** before asking
whether any is ambiguous. Three caps that are always red, blue and green mean
the ordering resolves itself: brightest-and-most-saturated of the two cool
segments is the blue, the duller one is the green. Snap first, then ask about
ties — a tie you created by snapping both toward blue is circular, and it is the
specific move to distrust.

The hardest case measured so far is *Pumpkinburg* 053 p4, where the boys are
about 25px tall and the blue prints `#219a94` — G154 against B148, further
toward cyan than any recorded green drift and less blue than any recorded blue.
It is only resolvable by elimination: the other two caps in the panel read
unambiguously red and green, so the third is the blue however it printed. Say
so in the note when a colour is settled that way.

Vol. 4, from *The Terror of the River!!* 048 panel 8 (the three caps in a row,
big and lit), and re-measured on two more titles 2026-08-17:

| | red | blue | green |
|---|---|---|---|
| large coloured front panel, *The Terror of the River!!* 048 p8 | `#e21b1f` H359 | `#03a2d0` H193 | `#019d47` H147 |
| segmented beanie, *Seals Are So Smart!* 035 p3 | `#e41b1f` H359 | `#04a5d2` H193 | `#009d47` H147 |
| segmented beanie, *Biceps Blues* 080 p6 | `#e11b1f` H359 | `#00a3d3` H194 | `#009c49` H148 |
| segmented beanie, *The Smugsnorkle Squattie* 083 p4 | `#de1b1f` H359 | `#00a2d2` H194 | `#009d49` H148 |
| segmented beanie, *Santa's Stormy Visit* 093 p6 | `#e01c1f` H359 | `#04a4d3` H194 | `#039b49` H148 |
| segmented beanie, *Playin' Hookey* 111 p7 | `#d51a1f` H358 | `#00a4d5` H194 | `#009d47` H147 |
| segmented beanie, *The Gold-Finder* 121 p3 | `#d2191d` H359 | `#05a3b0` H185 | `#019c46` H147 |
| segmented beanie, *The Bill Collectors* 193 p6 | `#e21a1e` H359 | `#03a4d4` H194 | `#019b4f` H150 |
| segmented beanie, *Turkey Raffle* 131 p5 | `#e31a1f` H359 | `#01a4d2` H193 | `#009d49` H148 |
| segmented beanie, *Maharajah Donald* 008 p1 | `#d41c20` H358 | `#019ebf` H190 | `#009545` H147 |
| segmented beanie, *The Cantankerous Cat* 141 p7 | `#e11b1f` H359 | `#04a4d3` H194 | `#019a48` H148 |
| nightshirts, *The Cantankerous Cat* 147 p8 | `#e41a1e` H359 | `#00a2d1` H193 | `#019a47` H147 |
| segmented beanie, *Donald Duck's Atom Bomb* 152 p5 | `#e11a1f` H358 | `#02a4d4` H194 | `#009b45` H147 |
| segmented beanie, *Going Buggy* 165 p7 | `#d41c1e` H359 | `#07a4cf` H193 | `#049952` H151 |

**And a fourth thing Vol. 4 does with the colour: it puts it on Donald.** *The
Cantankerous Cat* from 148 p4, *Going Buggy* on every page and *The Peaceful
Hills* on every page all give Donald a cap printed in Dewey's exact blue —
`#02a4d3`, `#02a4d4`, `#069bc8`, all H193-194 — joining *Smugsnorkle* and
*Santa's Stormy Visit*. That is five titles, and it means the largest cap-blue
blob in a Vol. 4 panel is routinely his: 4541px in *Going Buggy* 161 p7 and
1207px in *The Cantankerous Cat* 148 p4 against Dewey's 142px in the same panel.
Read the blob's AREA before naming anyone from it.

**And a title where the caps come off and the nightshirts take over.** *The
Cantankerous Cat* wears the beanie only on its four outdoor pages; 144 and 147
are bedroom pages and the colour moves to nightshirts, with 147 p8 printing all
three at once — green `#019a47` H147, red `#e41a1e` H359, blue `#00a2d1` H193 —
which is the bridging panel that makes the costume readable as the cap key. That
title also states its nap rotation in dialogue on 148 g9, 149 g7 and 149 g13, and
149 p7 then prints a clean green on a boy the line says is asleep. Follow the
line, record the colour as printed, and leave the pair collective.

**And the three 1946 titles at 121-140 and 193-201 add the failure the palette
cannot describe: the colourist himself.** All three use the segmented beanie and
all three print the canonical inks when they print them at all, but *The
Gold-Finder* 123 gives Dewey a clean green crown for a whole page, *The Bill
Collectors* 200 p1 and 201 p5 shuffle the three inks against the story's own
names, and *Turkey Raffle* 133 and 136 do it in small figures. In every one of
those the review named the boy from the scene and left `cap_colour` as printed.
Read the caps, record what they print, and do not let a measured hex override a
boy you have followed across the page.

Red and blue are stable — H358-359 and H184-194 — and **the green is the one that
moves**: H147 when it prints cleanly but H155, H159, H160, H163, H167, H171, H179
on thin slivers. Twice (*Seals* 043 p3, 044 p7) both cool caps landed green-side of
H160 in the same panel; both were settled by ranking the two against each other
inside the panel and chaining to the panel next door, with `cap_colour` left null.

**But the palette is the smaller half of the problem in this volume, because two
of the three titles take the caps away.** *The Terror of the River!!* puts the
boys in identical blue sailor caps aboard the houseboat — `#017fb5` H198 on all
three, and on Donald — for 23 of its 28 pages, and *Biceps Blues* has them
bare-headed for the whole indoor half and drawn as flat black silhouettes twice
more. Between them that is 173 of the batch's 178 collectives: absence, not a
declined cap. The three names *Terror* does record all come from **dialogue** —
Louie from 055 g9 back-propagated to 054, Huey from 060 g3/g4 and confirmed by
060's own caption, Louie again from 063 g8. Plan for the construction, then ask
separately how many pages actually carry it.

*The Smugsnorkle Squattie* is the counter-case and the one to expect next: the
same segmented beanie, worn on **all ten pages**, with only two silhouette panels
and one cap knocked off its wearer's head — 4 collectives in 140 groups. What it
adds instead is two hazards of its own. **Donald wears a blue workman's cap**
through 085-087, printing the same `#00a4d4` H194 as Dewey's band, so a cap-blue
blob at head height is his half the time; the coloured alphabet blocks on 089 and
the painted doghouse on 085 are in the three cap inks as well. And **088 p3 prints
Louie's cap RED**, in the one panel whose dialogue names him (*HE'S KIDNAPING
LOUIE!*) — a permuted panel the review confirmed, in a title that otherwise keeps
the convention on every page.

**And in two titles the colour leaves the cap altogether.** *Santa's Stormy
Visit* prints the beanie on only four panels of its eight pages; everywhere else
the boys are bare-headed, in **nightshirts** (097 p3: green `#009d48`, blue
`#039ecc`, red `#db1920`) or **pyjama collars** (100 p5: red `#d81a21`, blue
`#06a4d4`, green `#049948`). It also puts Donald in a blue keeper's cap in the
same `#01a3d3` H194 as Dewey's band for most of the title, so a cap-blue blob at
head height is his as often as not — decide the figure by size and bill, as on
*Smugsnorkle*. Its one usable check is that 097 p2 and p3 print the same three
boys in **opposite** left-to-right order, so the colour tracks the boy and not
the seat.

*Swimming Swindlers* is the harder case: **swim trunks for eight of ten pages,
and the set is red / black-and-teal striped / plain black, which is not the
roster's red-blue-green**. Do not assume the convention on a garment that is not
a cap. The key has to come from the dialogue and it arrives late — 110 p7 has
Donald address the boy in the red trunks as *HONEST HUEY*, and 103 p7/p8 pin the
striped suit on Louie, leaving plain black for Dewey — so read the title through
first and back-propagate. The review confirmed the key and left a note on 101 g3
saying so: blue-for-Louie is a colouring error that runs through the whole story
and the plot depends on it. The key **deliberately stops working** for the relay
on 104-105, where the other two dress to match Louie, and it **starts working
again** on 107-108 for the second race — the pass retired it three pages early
and lost three names that way. The beanies come back for 106 p4 onward.

**And one title changes costume halfway through and hands you a key for it.**
*Maharajah Donald* prints the segmented beanie on only 10 of its 28 pages
(007-011 and 015-019, reference panel 008 p1); the boys are drawn bare-headed for
the stowaway sequence on 013-014 and from 028 to the end, and in India they wear
**turbans** — two identical blue-and-white striped ones and a **RED** one. The
red turban is a real identification and worth looking for early: 022 p5 shows
that boy swinging the mahout's pole and p6 answers *"YOU KNOCKED HIM OUT,
LOUIE!"*, and 027 g7 summons *"MAHOUT LOUIE, AND THE SAHIBS, HUEY AND DEWEY"* —
the same boy, in the same seat on the elephant's neck, which then names him on
silhouette pages too. Donald wears a green robe and a gold-plumed yellow turban
from 020, so a big red or yellow shape at head height is a costume and not a cap.
Its grass and hedges also print at `#009c48` H147, the exact green of the cap
wedge, so every green blob needs a head under it.

Vol. 5, from *Volcano Valley* 048 panel 2 — the three boys at the model-shop
counter, each showing a cap **peak sliver only**, 86-161px:

| | red (Huey) | blue (Dewey) | green (Louie) |
|---|---|---|---|
| peak slivers, *Volcano Valley* 048 p2 | `#e61b1f` H358.8 | `#00a5d7` H194.0 | `#0b9750` H149.6 |
| caps whole, front-on, 053 p1 | `#e51a1f` H358.5 | `#02a4d6` H194.2 | — |
| backs to reader, 063 p8 | `#e51a20` H358.2 | `#00a5d7` H194.0 | `#009e49` H147.7 |
| dark sliver, 058 p2 | `#b0271a` H5.2 | `#05a5d4` H193.6 | black, unreadable |

Red and blue sit still at H358-359 and H193-194. The green is `#009e49` H147.7
when it prints and `#018345` H151.4 in shadow.

**The construction alternates inside a single story**, which is what makes area
useless here: 30-160px slivers on 048, 057 and 058, and caps drawn whole at
1500-5000px on 051 p4, 053 p1, 063 p8, 067 p4 and 076 p3. **Donald wears a flying
cap in the same `#00a5d7` in nearly every panel**, so the largest blue blob is his
about as often as it is Dewey's — 053 p1 has a 5094px blue that is a *nephew's*,
with Donald not in the panel at all. Check the head, not the area.

**And the green hides in the hedge.** `#018345` H151.4 is also the story's foliage,
so where a boy stands against greenery the connected-component scan merges cap and
hedge into one huge blob and reports no cap-sized green at all — 048 p4 looks
capless and the middle boy is plainly green when you sample panel (730-810,
270-320) directly. When red and blue are found and green is not, suspect the merge
before concluding the boy is bare.

**Scan this volume at a 25px floor.** A first pass at 60 dropped the reference caps
themselves.

Vol. 6, from *Wintertime Wager* — a **winter** story, and the first title read in
the volume:

- Indoors the boys are **bare-headed**, which is six of its ten pages. Outdoors
  they wear knitted caps: red `#e61b1f`, leafgreen `#3bac42` at **H124**, and a
  third that is **white with a yellow band** and so not a roster colour at all.
- **The third boy is named by costume, not cap.** His mittens and scarf are
  `#00a5d7`; `identified_by: ["balloon-tail", "costume"]`, `cap_colour` null.
- **The red cap is anchored by name, not by convention.** On 044 panel 3 one of
  them shouts "WE'VE GOT HIM, HUEY!" at the boy driving the tractor, and that boy
  wears red in panels 2, 6 and 8 of the same page.
- Scenery to keep out of the bands: the living-room rug is the **same** `#3bac42`
  as the cap green, and `#6eb53d` (H95, V0.71) is the outdoor shrubbery.

The volume's other titles are not winter stories, so none of the above should be
assumed to carry — sweep before page 1 as usual.

Vol. 6, from the three 1947 titles read on 2026-08-25 — and note the construction
differs from *Wintertime Wager*'s knitted caps:

- *Watching the Watchman* and *Darkest Africa* both build the cap as a **coloured
  side panel on a black crown**, split into two blobs by the brim, so `heads2.py`
  is the right tool. Watchman: blue `#03a4d5`, red `#e51a20`, green `#4da240`
  (H111), reference panel 055 p7. Darkest Africa: blue `#07a4d4`, red `#e61b1f`,
  green `#4da33e` (H110.6), reference panel 080 p3.
- **In Darkest Africa the cap green and the foliage are the same ink.** In the
  reference panel itself the green band and the bush behind the boys are both
  `#4da33d`/`#4da33e`. Colour cannot separate them at all — only whether the blob
  sits on a head. Both greens report under capscan's `leafgrn` band, not `green`.
- Neither is *Wintertime Wager*'s `#3bac42` (H124), so the volume uses at least
  two cap greens. Fix the palette from a reference panel every time.
- **Where the caps stop matters more than their hex.** Darkest Africa prints cap
  ink on 080-084 only; from 085 the party is in brown pith helmets and 100-101 in
  white sailor hats. *Wired* has no cap key on any page.

Vol. 6, from the second three 1947 titles read on 2026-08-25 — the construction
above holds on all three, so `heads2.py`/`caphead` remain the right tools:

- *Going Ape*: blue `#00a4d6`, red `#e61b1f`, green `#4da33e` (H110.6), reference
  panel 070 p1. Cap ink prints in **that panel only** — from panel 2 the boys are
  bare-headed for the rest of the story, so nine of its ten pages are collectives.
- *The Old Castle's Secret*: blue `#05a4d3`, red `#e21a1f`, green `#4da23f`
  (H110.5), reference panels 015 p8 and 014 p6. Caps print outdoors and through
  the armour halls; they come **off** for the middle of the story, first under
  borrowed helmets (020-023) and then not at all once the helmets are lost in the
  moat (027 on), which is why pages 020, 021, 028, 029 and 031 are collectives
  end to end.
- *Spoil the Rod*: blue `#06a4d0`, red `#e21a1e`, green `#53a345`, reference panel
  104 p5. Caps print **outdoors only**; from 106 the story moves indoors and the
  boys are bare-headed, so the names come from the dialogue instead.
- **Two greens to keep apart in this volume.** The grass is `#56b03f`/`#59b140`
  (H107, V0.69) and the cap green is `#4da23e` (H110.6, V0.64): four degrees of
  hue apart, separated reliably only by the exact hex, and V0.68 is the usable
  cut. *Scrooge's own tam* in the Scottish scenes is a third green, `#70b53e`
  (H95, V0.71), and does not collide with either.
- **Donald wears a nephew colour in two of the three.** He is in a one-piece blue
  tam through the castle scenes of *The Old Castle's Secret* and a purple helmet
  with a red crest from 024, and *Going Ape* puts him in a blue cap for the
  hypnotist sequence. The segmented crown is what separates them: two or three
  abutting pieces of one hex is a boy, one solid piece is Donald.

Vol. 8, from the three 1949 titles read on 2026-08-28 — the volume's own
construction is a **black crown with a small coloured sliver**, and it held on
*The Goldilocks Gambit*: red `#e61b1f` (H358.8), blue `#03a4d5`/`#08a5d5`
(H193-194), green `#009e49`/`#4da23f` (H110-148), reference panel 089 p7, all
three readable at 2.2x.

- **The Goldilocks Gambit's cap green is the same ink as the foliage**
  (`#009e49`), so `capwide` reports the cap as scenery and a green cap beside a
  tree reads as zero. 089 p5 needed a 3x crop of the crown to find two slivers
  the census had swallowed. Probe the crown or crop it; never take a capwide
  zero for a bare head.
- **The other two titles do not use the volume palette at all**, so do not
  assume it. *Letter to Santa* dresses the boys in **winter knits** — red
  `#e61b1f`, blue `#00a5d7`, green `#50a241` stocking caps with matching
  scarves, huge and unmistakable — and takes them off the moment the story goes
  indoors at 063, which is most of it. *Luck of the North* puts them in
  **parka hoods** in the same three colours from 118 outdoors, off indoors and
  on the ship. Both are absence, not under-naming.
- **A parka hood goes in `cap_colour`.** The pass left the field null and
  recorded the colour as `costume`; the review filled it in on six groups. Cite
  `cap-colour` and `costume` together.
- **Two red-parka collisions to watch.** In *Luck of the North* Gladstone wears
  a red parka for the whole Arctic sequence, the same red as Huey's hood — he is
  told apart by his green hat brim and green shoes against the boys' plain
  orange feet, and 135 g5 turned on exactly that. In *Letter to Santa* the two
  uncles spend nine pages in identical Santa suits and are separated by the face
  alone: Scrooge has feathery white cheek tufts and, from 071, spectacles;
  Donald is smooth-cheeked with the longer beak. Reference panels 074 p1 and
  075 p3.
- **The long-shot Donald default inverts here.** *Luck of the North* travels as
  a party of four for twenty pages, so a long shot nearly always holds three
  boys as well as Donald; ten of its seventeen corrections were `Donald` going
  to a boy. Default to Donald only where he is alone or nearly so.


Vol. 8, from the three 1949 titles read on 2026-08-31 — *New Toys*, *Donald's
Love Letters*, *Rip Van Donald*, all three fully reviewed. The volume
construction holds where it is used, but **the red prints dull once the sliver
is small**: `#ad301a`, `#ba291c`, `#903616`, `#da1f1f`, `#e31d21`, H4-16 at
S=0.85-0.89, against a clean `#04a4d5` blue and a `#43a350`/`#4da33e` green.
Do not expect `#e61b1f` on a tab.

- **The cap goes on and off panel by panel, not scene by scene.** *New Toys* has
  the boys bare-headed for all of 099 and all of 104, capped on 100 p6-p8, 101,
  102 p8, 103, 105 and 106 p1 — including outdoors on both sides of the switch.
  Establish it per panel; a page that was bare two pages ago is not evidence.
- **This is where the batch lost its corrections.** Twelve of seventeen
  under-namings sit on panels called bare off a `heads2`/`capsum` zero with no
  crop spent — *New Toys* 104 and 105, *Rip Van Donald* 154 p1 (shadow), 155 p2
  (flat silhouette), 159 p2 (a green cap the census merged into foliage one
  hue-degree away). Every cap that WAS cropped survived: 75 colours untouched.
  On this volume a whole-page census zero means **crop that page**, not "bare".
- ***Rip Van Donald* runs two keys and the second inverts the first.** 153-155
  and 162 p6-p8 are the winter cap with the ordinary convention. 156-161 dress
  the boys as old men in coloured **top hats** whose colours the colourist got
  erratically wrong: 157 p2 is dialogue-proven Huey in a **blue** hat (he names
  Dewey and Louie in the third person), and the review kept Huey while noting
  *"Colorist error: shoud be red"*. Red stayed Dewey on 157 p3 and 160 p4, but
  156 p5 was swapped back to blue=Dewey, red=Huey. **Do not promote one
  dialogue-proven panel into a story-wide permuted key** — check whether the
  anomaly holds over consecutive pages first, which is what separates this from
  *High-wire Daredevils*. Costume hats go in `identified_by: hat` with
  `cap_colour` null; a parka hood still goes in `cap_colour`.
- **Two colour collisions.** Donald's sailor cap is the same `#00a5d7` as a blue
  top hat, and the foliage `#54b041` is one hue-degree from the hat green
  `#4da33e`. Rank within the panel and check what the blob sits on.
- **Medium was right 20 times out of 20.** Used for a believed value with thin
  evidence — a tip stopping short, an elimination, a balloon with no tail — the
  review promotes it rather than fixing it. Do not avoid it, and do not use it
  for the long-shot Donald guess, which is where it went wrong in Vol. 7.

Vol. 8, from *Trail of the Unicorn* read on 2026-08-31 and reviewed the same
day — 24 pages, 278 groups, 14 corrections (5.0%). The volume construction holds
in the Duckburg and Shangri-Lala pages, but this title **changes cap in the
middle**: from 021, once the party is climbing, the boys are in winter caps with
a BIG coloured earflap that reads at contact-sheet scale, and the small black-
crown wedge is gone. Bare-headed on 007 and indoors on 029.

- **The fakir is Gladstone.** "Mustapha Handout", who takes ten dollars off
  Donald on 014 and sells him the painted donkey on 018, is Gladstone in a red
  turban, green robe and a false white beard. 019 p5 has the boys addressing the
  turbaned figure as COUSIN GLADSTONE GANDER, 019 p8 knocks the beard off, and
  020 has him admitting the ten dollars. File the lines under `Gladstone`, not
  under a free-text alias.
- **A LONG DROOPY BEAK BEATS ANY CAP COLOUR.** Two of the 14 corrections are a
  nephew named off ink that was on Donald's head — his own `#00a5d7` sailor cap
  on 015 p5, and a green cap on 025 p6 where `capscan` returned no blue in the
  panel at all and I concluded he was not in it. Fix which figure is Donald from
  the beak before reading a single cap; a capscan zero for blue is not evidence
  that Donald is absent.
- **Do not invent a crossing.** 013 p5: I wrote "the two tails cross" off tips
  landing 20-30px past a head span, which is inside the error of the tip reading
  itself. They do not cross, and the review swapped both names and both colours.
- **A flat silhouette panel is not automatically a collective.** 026 p2 is black
  shapes against one flat colour and the review still named Dewey. But 028 p8,
  also silhouettes, had my Donald and my `nephews` swapped in both directions —
  so on silhouettes decline the Donald-against-nephew guess rather than the name.
- **A chorus of all four takes `other:Donald and the nephews`.** Neither
  `Donald` (010 p5, where a real tail lands on him) nor `nephews` (029 p5) was
  accepted for a line the whole family shouts.
- **Medium did not hold this time**: 4 of 21 reversed, against 0 of 20 the week
  before. Keep using it — the value is honest and the reviewer promotes most of
  it — but the 20-of-20 above was one title's luck, not a recalibration.
- **Type**: three unicorn whinnies and a snort moved `sound_effect -> dialogue`
  and all four were confirmed. An animal's own voice is dialogue; its hooves,
  jaws and the rope it parts are not.

Vol. 9, from *In Ancient Persia* read on 2026-09-01 and reviewed the same
day — the first title read in this volume, so the palette below is new.
**CORRECTED 2026-09-01 from *Wild about Flowers* and *Vacation Time*.** This
entry originally read "a black crown carrying a WIDE coloured band", which is one
viewing angle rather than the construction. The cap is the classic **coloured
crown with a black band round it**: seen from the side the colour is broad
(1252px of `#05a4d6` on *Vacation Time* 075 p6, a 4449px red band on *Wild about
Flowers* 029 p6) and legible at contact-sheet scale; seen from above or behind
the black band faces the reader and the colour survives only as a rim of 100-400px.
**The same title gives both, so never conclude a palette from a sliver.**

Inks: red `#e61b1f`, blue `#06a6d4`, green `#4da23f`; cap green sits at H109-121
against foliage green at H146-150. Reference panel 038 p2 (three boys in a row
along a wall).

**And the ink does not always name the boy.** *Vacation Time* gives the same
clean `#4da33f` H112 crown to Dewey on 078 and to Huey on 087/092, each settled
by Donald using the name out loud. Where a line names somebody, take the name and
record the printed colour.

- **The band shades badly and the two ends of the range collide.** Blue comes
  back as `#1fa3a0`, `#24a28f`, `#4da39e` (H171-178) in torchlight and desert
  light, and green as `#34a372` (H153). Rank the three crowns **within the
  panel** and never against absolute hue.
- **And ranking within the panel is not enough on its own.** On 060 p6 I probed
  all three crowns, found `#34a372` (H153.5), a clean red, and `#5fa25d`
  (H118.3), reasoned that the H118 was the green and the H153 therefore the blue
  *by elimination* — and the review made it red. The elimination is only as good
  as the assumption that all three boys are present and each wears a different
  ink. **13 cap colours were overturned in 297 groups here, against 5 in 288 on
  the Vol. 8 title read the same week**, and the moves have no direction
  (red->green, green->red, red->blue, blue->red, blue->green, green->blue), which
  is the Vol. 7 signature for reading too small. A band that is legible at
  contact-sheet scale is legible enough to *see*; it is not legible enough to
  *name*. Crop it.
- **A costume can be issued twice.** Donald is dressed in Prince Cad Ali Cad's
  own wedding finery on 052, so for three pages two ducks wear an identical blue
  conical hat and red ruff — including a panel where they point at each other and
  both answer `I AM!`. Those calls have to rest on the dialogue. Flagging the
  collision and marking the pairs medium worked: the review fixed 052 g0/g1 (a
  clean swap), 053 g1 and 055 g5/g6 without any of them going unnoticed. It
  resolves on 055 p2, where Donald is bare-headed and Cad keeps the hat.
- **The dialogue beat the tail on a silhouette.** 045 p3: the balloon's tail
  lands on a small figure 45px short of Donald's head, but SUFFERIN' HOPTOADS is
  his idiom; I took the tail, flagged the conflict, and the review took the
  idiom. On an all-black panel the register outranks a tip reading.
- **A yellow rectangular box with an arrow tail is the narrator.** 052 g11 was
  stored `dialogue`; the type correction to `narration` was confirmed. The same
  words are ordinary speech balloons in the very next panel, which is what makes
  the device worth checking rather than assuming.

Read again on 2026-09-01 with *Wild about Flowers* (10 pages) and *Vacation
Time* (33 pages), 440 groups, both reviewed the next day. **19 corrections,
4.3%** — 2.6% and 4.9% by title, against In Ancient Persia's 12.1%. The two
things that changed are worth keeping.

- **THE WIDE BAND IS A VIEWING ANGLE, NOT THE CONSTRUCTION.** The cap is a
  coloured crown with a black band round it. Side-on the colour is broad —
  4449px of `#e61b1f` on *Wild about Flowers* 029 p6, 1252px of `#05a4d6` on
  *Vacation Time* 075 p6. From above or behind, the black band faces the reader
  and the same cap survives as a rim of 100-400px. **Both appear in the same
  title, often on the same page**, so neither reading licenses the other: crop
  either way. 76 of 85 cap colours survived here, against 13 overturned in 297
  groups last time.
- **CAP GREEN IS H109-121; FOLIAGE GREEN IS H146-150.** `#4da33f`, `#4ca23e`,
  `#51a353` against `#009e49`, `#3b9a62`. Both these titles are forest stories
  and the background green sits directly behind the crowns, so a green patch at
  H148 on a head is usually the wall of trees showing past the cap. The hue gap
  is the whole discriminator and it is free from `probe.py`.
- **THE COLOURIST DOES NOT TRACK THE BROTHERS IN *VACATION TIME*, AND THE STORY
  PROVES IT TWICE.** A clean `#4da33f` H112 crown is called **DEWEY** by Donald
  on 078 and **HUEY** by Donald on 087, confirmed by the chief on 093; the
  camera-carrier is coloured red on 074, blue on 086 and green on 087/092.
  Taking the vocative, recording the printed colour anyway and saying so in the
  note was accepted on every one of those groups. Where nothing names anybody,
  the convention plus `medium` is the right fallback — see below.
- **MEDIUM IS STILL THE RIGHT MARKER AND STILL THE EXPENSIVE HALF.** 3 of 24
  medium calls were corrected (12.5%) against 16 of 416 high (3.8%), and 0
  survived as medium. Both the flagged art-versus-dialogue conflicts held.
- **DONALD'S RUNNING COMMENTARY IS NOT AUTOMATICALLY DONALD.** 3 of *Vacation
  Time*'s 16 are `Donald -> nephews` on off-panel lines in the drive sequence
  (064 g0, 065 g3, 065 g11), where the panel holds only scenery and the line
  reads like the lecture Donald has been giving for four pages. It is the boys.
  An off-panel line in a monologue stretch still needs a reason beyond "he was
  talking last".
- **A DRAWN `?` OVER A BYSTANDER IS NOT HIS.** 092 g9, a question mark over the
  tough guy while the boys produce the camera, went to `none`. The roster's
  device rule names the figure a device hangs over; a `?` floating over a
  reaction shot is punctuation on the panel, not on the man.
- **A SONG WITH NO SINGER CAN BE THE FURNITURE.** *Wild about Flowers* 035 g9,
  the only high-confidence call reversed in that title: a song coming out of the
  drifting gondola is the boat's radio, which the dialogue installed two pages
  earlier ("IT HAS A RADIO AND PLUSH SEATS!"). The review made it `other:radio`.

Vol. 10, from *A Financial Fable* 097 p5 (three boys seen from behind, red,
green and blue wedges in a row) read on 2026-09-03, and confirmed on *The April
Foolers* the same day. The cap is the **black crown carrying coloured wedges**
that *Voodoo Hoodoo* and *No Such Varmint* had, not the Vol. 9 coloured crown:

| | |
|---|---|
| red (Huey) | `#e61b1f` |
| blue (Dewey) | `#06a4d4` |
| green (Louie) | `#4da23f` (H111), shaded to `#2ea04a` (H135) |
| foliage green | `#009e49` (H148) |
| fence rail and water | `#00a5d7`, the wedge blue exactly |

- **Even from behind a wedge is about 500px.** On the reference panel the
  three crowns fill the frame and capscan still finds 491, 512 and 723px of
  ink. From the front the same wedge is a 50-400px sliver at one side of the
  crown, `heads.py` reports nothing on most of them, and only a 2-3x crop
  reads it. Budget one crop sheet a page on a nephew-dense title; *The April
  Foolers* named 45 of 73 nephew lines that way at 2.7 images a page.
- **The scenery prints in two of the three inks.** The fence rail and the
  river are `#00a5d7`, the bushes `#009e49`; a probe box that touches either
  reports a cap that is not there (*The April Foolers* 111 p1 probed 897px of
  "green" that was the bank behind the boy). Red has no look-alike. Rank a
  probe against what is behind the head before writing the colour down.
- **Cap green is H111-135, foliage H148**, the Vol. 9 rule again; `capscan`
  files the cap under `leafgrn` and the bushes under `green`.
- **The red wedge in shade prints brown, and the same teal can be Donald's
  cap.** *In Old California!* (2026-09-03): a red wedge turned away from the
  light reads `#8e542a`-`#b07d44` (H19-26, S0.6-0.77), and two of three such
  reads were withdrawn by the review while a third was blue. Donald's sailor
  cap prints `#016ca7` in most panels but `#369a8a` (H170) on 114 p1, the
  identical teal to a boy's wedge in the same panel, so a teal on a big head
  is Donald before it is Dewey. Lit crowns from behind are full colour:
  red `#e21b20`, blue `#00a4d5`, green `#44b16d` (H142).
- **Winter titles put no colour on the boys at all.** *Operation St. Bernard*
  dresses them in identical brown fur hats outdoors and bare heads indoors, so
  every nephew name in it came from the "Colonel X" address chain and nothing
  from the art. And the boys go bare-headed indoors in ordinary stories too
  (*The April Foolers* 102 p2-p6, breakfast) and lose their caps in the river
  on 111.

## The long form is retired

Runs up to 2026-08-05 pasted a ~120-line prompt carrying every rule inline —
workflow, cap colour, speakers, text, committing, queues, the mtime gate. The
last one is the *Too Many Pets* + *The Hard Loser* prompt of 2026-08-06 01:56.
It was dropped once the `vision-pass` skill existed, and everything in it
except the palette above is in the skill or `roster.txt`.

Do not reconstruct it. A rule that lives in a pasted prompt is a rule that
stops being applied the moment the prompt is shortened — which is exactly the
failure recorded twice in `docs/vision-pass.md`, where a rule lived only in
prose and never reached the pass. New rules go in `vision_schema.py`, which
generates `roster.txt`, which `vision_apply` validates against.

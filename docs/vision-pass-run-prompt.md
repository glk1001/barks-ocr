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

### Findings to paste into the next run (2026-09-04, twenty-fifth batch)

*Pool Sharks* (Vol. 10, 10 pages, 126 groups), reviewed the same day and
mirrored clean: **4 speaker corrections, 3.2%**, 3 of them in the nephew
domain (23.1% of 13). Confidence: **high 4 of 112, 3.6%; medium 0 of 14,
0.0%** -- every hedge the pass made was right, which is the first title in
this run of six where the medium rate beat the high rate. Cost 4.4 images
per page, well over budget and concentrated on two pages. All four of the
pass's type corrections were confirmed and the review added six more
`dialogue -> thought` moves of its own.

- **A WEDGE CAN SURVIVE AS A 40px SLIVER AT S0.3, AND EVERY CENSUS MISSES
  IT.** 159 g12/g13 were written `nephews` on the strength of "capscan and
  capwide report red 0, green 0, blue 0 and leafgrn 0 at a 20px floor, and a
  probe of each crown at S>=0.06 returns only the pale sky"; the review named
  Louie and Dewey and recorded green and blue. Re-checked afterwards:
  `capwide` at a floor of **8 pixels** still returns 0 blobs in all three
  bands, and a 3x crop shows all three wedges plainly -- a grey-green sliver
  on the left crown, a brown-ochre one on the middle, a teal one on the
  right, each 20-60px at the crown's right edge. The failure is `MIN_SAT`,
  not the band edges, so `capwide` does not rescue it. `probe.py` DID show
  it and the pass read past it: the boxes came back `green 133-176px
  #5d7876 H167.8 S 0.07/0.10/0.30`, and a chromatic band with **>100px and a
  max saturation of 0.30 inside a crown box is a shaded wedge, not noise**.
  A census of zero across every band on a panel that plainly holds three
  nephews is a reason to crop at 3x, never a reason to write `nephews`.
- **A tip inside a head span is only as good as the span.** 159 g6's tail tip
  was measured at panel x=524 and called "inside the middle boy's head span
  (515-660), 59px clear of the left boy, who ends at 465"; the review gave it
  to the left boy. The spans were eyeballed off the panel image rather than
  taken from a head census, and being wrong about where a head ends turns a
  measured tip into a confident wrong name. Take the spans from `heads.py`
  before quoting a margin against them.
- **Read what the gag is doing before naming the sole figure.** 156 g2 (`? ?
  YEWOUCH! OWOO!! I'M FREEZING! BRRRR! LEMME OUTA HERE!`) was written Donald
  as "alone, buried in the truckload of ice that has been dumped in the
  pool". Donald ordered the ice to freeze the children out, and the next
  panel is `THEY'RE GONE! NOW... I'LL TAKE MY DIP!` -- so the figure in the
  ice is the children, and the review made it `other:neighbourhood kids`.
  The panel was read off the 250px montage and never opened.
- **The reviewer's collective for a crowd of children is
  `other:neighbourhood kids`.** The title now carries that on 1 group and the
  pass's `other:the neighbourhood children` on 1 other (155 g6, the shouts
  from the pool). Two values for one crowd; worth settling on one.
- **A prop colour can be a real per-boy key when a panel bridges it.**
  151 p1 has the three boys bare-crowned with red, blue and green suitcases;
  151 p2 and 159 p5 show the same three boys with the case beside the
  matching cap. Six names were made that way and none was corrected.

*The Trouble With Dimes* (Vol. 10, 10 pages, 131 groups) and *Gladstone's
Luck* (Vol. 10, 10 pages, 125 groups) were passed the same day and are not
yet reviewed. Cost 2.3 and 1.8 images per page. What they add:

- **A STORY CAN TAKE THE CAPS OFF FOR HALF ITS LENGTH.** *The Trouble With
  Dimes* draws the nephews bare-headed from 160 to 162 -- no cap at all, and
  a probe of each crown returns only the wall behind -- and *Gladstone's
  Luck* does the same indoors on 171, 172 and 179 p7-p8 while capping them on
  the golf course. Establish per PAGE, not per title: the same story that
  gives you nothing on page 2 can seat all three in clean bands on page 4.
- **Pyjamas are a costume key and they print the roster inks exactly.**
  *The Trouble With Dimes* 168 puts the boys in red `#e61b1f`, blue
  `#04a4d5` and green `#4da23f` (H111) pyjama tops -- the three cap inks to
  the digit -- and 169 p7 shows the same three on their caps. Six names, all
  at high with `costume` in the evidence.
- **`NOW BACK TO UNCLE SCROOGE'S!` is stored as narration and is not.** The
  same six words appear four times in *The Trouble With Dimes*: a spoken
  balloon with a pointed tail on 164 p5, a thought cloud with a bubble trail
  on 164 p8 and 166 p6, and a real caption box with a drop capital on 164 p6.
  Two of the four were stored `narration`. A short line that reads like a
  scene-change caption still has to be looked at.
- **The name scan cannot see a nephew named once with a dictionary word.**
  *Gladstone's Luck* 174 g5 is `THE BALL'S SAILING INTO THE ROUGH, LOUIE!` --
  the only direct address in the story, and `barks-ocr-name-grep` lists
  neither LOUIE (it is in the dictionary) nor the phrase (it occurs once).
  It also names the boy who is NOT speaking, which is what made the speaker
  identifiable by elimination.
- **A red blob above a head can be the flagstick.** *Gladstone's Luck* 174 p8
  gives `heads.py` a 457px `#e31b1f` reading as CAP-INK on the boy at the
  green; he is holding a red flagstick that passes through that band. The
  name was left at medium on continuity and `cap_colour` null.

**Batch summary, twenty-fifth batch (Vol. 10, 30 pages, 382 groups):** one
title reviewed, 4 of 126 (3.2%). Cost 2.8 images per page across the batch,
but 4.4 on the reviewed title. Its whole error was one panel read off the
montage and two nephew calls where a measurement was quoted against a
landmark that had not itself been measured.

### Findings to paste into the next run (2026-09-04, twenty-fifth batch, second title)

*The Trouble With Dimes* (Vol. 10, 10 pages, 131 groups), reviewed the same
day and mirrored clean, no group added or deleted: **5 speaker corrections,
3.8%**, every one of them in the nephew domain (20.8% of 24) and every one of
them on page 168. The pass's single medium was not corrected; high 5 of 130.
All three of its type corrections were confirmed. Cost 2.3 images per page.

- **A TAIL TIP THAT STOPS IN A GAP BELONGS TO THE HEAD ON ITS LEFT.** Measured
  twice in two days, and the "nearer head" rule was wrong both times. 168 g6:
  tip at panel x=815, `heads.py` gives the three heads as (339..516),
  (587..763), (844..1034) -- so the tip is 52px past the middle boy and 29px
  short of the right one. The pass gave it to the nearer, right-hand boy; the
  review gave it to the middle one. Pool Sharks 159 g6 the day before: tip at
  x=524, heads at (232..454), (534..660), (740..879) -- 70px past the left boy
  and 10px short of the middle. Same move, same reversal. In both titles the
  tails overshoot to the RIGHT of their own speaker, which is the Vol. 4
  offset fan inverted; go one head left of the tip, or say `nephews`.
- **AND THE SPANS THE PASS QUOTED WERE NOT MEASURED.** Both notes carried a
  confident margin -- "inside the middle boy's head span (515-660)", "on the
  left edge of the rightmost boy's head, which begins at 819" -- and both
  spans were read off the panel image by eye. The census says 534 and 844.
  A tip coordinate is worthless against a span that was guessed: run
  `heads.py` on the panel and quote `head+beak x=(a..b)`.
- **`capwide` says the ink exists; `heads.py` says it is on a head.** 168 g3
  was written `nephews` because "no boy is drawn clearly enough to separate";
  the review named Huey and recorded red. The pass had run `capwide` on that
  panel and seen `red 207px x512-518` and `152px x466-488` at `#e61b1f`, and
  could not place them. `heads.py` on the same panel reports
  `head+beak x=(293..510) CAP-INK: red(512,362,519,405) a=137 #e61b1f` -- the
  same sliver, attached to a head. One extra command, and the only one of the
  four census tools that answers the question that matters.
- **Carry a page's seating across its panels.** 168 g7 and g8 were declined as
  "both buried in the bedding with no collar showing at all"; the review named
  Louie and Dewey. The panel two before it seats the same three boys in bed
  green, blue, red and the panel two after seats them the same way. Where a
  page establishes the order by colour once, the panels between inherit it.
- **A STACKED CONTACT STRIP CANNOT NAME AN ADULT.** 168 g12 (`WHAT ARE YOU
  KIDS DOIN' IN MY DIMES?`) went to Scrooge, off a 0.72-scale strip where the
  figure read as a white head in a green nightshirt; it is Donald, and a 2.2x
  crop shows a smooth head with no side-whiskers and no spectacles. At that
  scale Donald and Scrooge are the same silhouette. The strip is triage --
  balloon shape, who is in frame, whether a crown carries a band. Naming an
  adult needs the face.
- **A text correction can be marked reviewed and not applied.** 165 g8's sign
  reads COLLECTORS in the art and the story's two other copies of it are
  stored that way; the group came back `vision_text_reviewed: true` on both
  engines with `ai_text` still reading COLECTORS and the proposal still
  sitting in `vision_corrected_text`. `vision-corrections` then reports
  nothing outstanding. Same shape as the `type_reviewed` silent decline:
  after a review, diff the proposals against the stored text rather than
  trusting the outstanding count.

**Batch summary, twenty-fifth batch (Vol. 10, 30 pages, 382 groups; two of
three titles reviewed, 257 groups):** **9 speaker corrections, 3.5%**; nephew
domain **8 of 37, 21.6%**; **0 of 15 mediums corrected**. Split by title
3.2% / 3.8%. Cost 2.8 images per page. Seven of the nine corrections are one
of two moves: a tip in a gap given to the nearer head, or a boy declined on a
panel where a census the pass did not run puts colour on his head.

### Findings to paste into the next run (2026-09-04, twenty-fifth batch, third title)

*Gladstone's Luck* (Vol. 10, 10 pages, 125 groups), reviewed the same day and
mirrored clean, no group added, deleted or renumbered: **7 speaker
corrections, 5.6%**, 6 of them in the nephew domain (16.2% of 37). Neither of
the pass's two mediums was corrected; high 7 of 123. Its one type correction
was confirmed. Cost 1.8 images per page, the cheapest title of the batch.

- **A COLOURIST ERROR CAN PUT THE WRONG CAP ON A BOY, AND A CHAIN BUILT ON IT
  BREAKS ONE BALLOON AWAY.** 174 g6 came back Huey -> Louie with the
  reviewer's own note, *"Colorist error: should be Louie"*, and the printed
  red left in `cap_colour`. That single mis-colouring cost a second call as
  well: 174 g5 (`THE BALL'S SAILING INTO THE ROUGH, LOUIE!`) had been reasoned
  out as "the addressee is in the rough, so the speaker is the other boy, the
  red-capped one" -- formally right, and wrong because the red-capped boy IS
  Louie. It came back `nephews`. When a direct address and a cap disagree
  about which boy is which, the ADDRESS wins, the printed colour still goes in
  `cap_colour`, and every other call in that panel that leant on the cap has
  to be re-derived or withdrawn. Third instance in the corpus after the
  permuted palette of *High-wire Daredevils* and *Vacation Time*.
- **TWO NAMED LEAVES THE THIRD BY ELIMINATION -- APPLY IT EVERY TIME.** 173
  g2/g3 were declined as "the two on the left wear plain black caps with no
  band showing at this angle"; the review named Dewey and Huey. The pass had
  already named the right-hand boy Louie in the same panel off a green band,
  and `heads.py` -- which it never ran on that panel -- reports the middle
  boy's cap as `CAP-INK: red(406,335,429,361) a=178 #b42e28` on the head at
  x=(353..487). With green and red placed, the left boy is Dewey and no blue
  needs to print: `capwide` finds 0 blue blobs at a floor of 10 and the crown
  probe returns only sky. The pass made exactly this call on 175 p3 and it
  stood; not making it here cost two names.
- **A drawn device names the figure under it -- so identify the figure.** 171
  g6/g7, the two `?` marks, were both given to Donald as "hanging over Donald"
  and "the inset close-up of Donald's face". The panel holds both ducks: the
  vase is landing on Donald at the lower left, and the circular inset at the
  right is GLADSTONE, tan hat and green suit, with the `?` beside his head.
  Both went to Gladstone. The narratively obvious owner of a `?` is the one
  it happened TO; the drawing gives it to the one who is baffled.
- **A free-text `other:` can be the wrong sex.** 171 g8 went from
  `other:the woman at the window` to `other:the man at the window`; the pass
  wrote "a woman leaning out of the upstairs window in a blue dress" off a
  0.72-scale contact strip. The value carries no closed-set check, so nothing
  catches it but a crop.

**Batch summary, twenty-fifth batch (Vol. 10, 30 pages, 382 groups, all three
titles reviewed):** **16 speaker corrections, 4.2%**; nephew domain **14 of
74, 18.9%**; **0 of 17 mediums corrected** against 16 of 365 highs (4.4%).
Split by title 3.2% / 3.8% / 5.6%. All 8 type corrections the batch proposed
were confirmed, and its one text correction was applied. Cost 2.8 images per
page. Against the twenty-fourth batch's 9.1% this is less than half the rate,
and the residue is concentrated: of the 16, five are a cap or a device the
pass declined to read on a panel where a census it did not run puts the answer
on a head, three are a tip in a gap given to the nearer head, and two are an
adult named off a contact strip without the face being looked at.

**The batch's one added group arrived clean, and both of its hazards held
off.** *Gladstone's Luck* 174 gained the flagstick numeral on BOTH engines,
appended as the last id, so nothing was renumbered and every existing group's
`ai_text` is byte-identical to the pass commit; there was no Copy-In residue
and no straggler. That is the good case, and it is worth diffing per-engine
`ai_text` against the pass commit to establish it rather than assuming it.

Then the missed-text audit went on reporting the item, because `visible_text`
still held the PROSE form the pass uses for an ungrouped device and the audit
matches by substring. One line back to the bare lettering and the title audits
clean. The rule already existed and the batch still hit it: **check the audit
again AFTER a review adds a group, not only before.**

### Findings to paste into the next run (2026-09-04, twenty-sixth batch)

Three titles passed, none reviewed yet: *Ten-Star Generals* (Vol. 10, 10 pages,
117 groups), *A Christmas for Shacktown* (Vol. 11, 32 pages, 401 groups) and
*The Truant Nephews* (Vol. 10, 10 pages, 172 groups). 690 groups over 52 pages,
**2.0 images per page** (23 / 54 / 27). Confidence 671 high, 19 medium, 0 low.

- **A TITLE CAN PRINT NO CAP COLOUR AT ALL, AND THE SCENERY CAN PRINT ALL
  THREE.** *Ten-Star Generals* puts every nephew in the brown Junior Woodchuck
  coonskin cap for all ten pages, so `cap_colour` is null throughout. Worse,
  `heads.py` reports CAP-INK on nearly every head in it and every reading is
  scenery: the barn wall behind them is `#e61b1f`, the *exact* Vol. 10 cap red,
  and the sky and pond are `#00a5d7`, the exact wedge blue. Rank a CAP-INK hit
  against what is behind the figure before believing it, and on a title like
  this stop running the census at all -- it produces only false positives.
- **When the ink is gone, the story's own key replaces it.** *Ten-Star
  Generals* assigns one merit badge per boy in dialogue on its first page --
  bow and arrow Huey, canoe Dewey, life-saving Louie -- and then uses it to the
  end. That named 28 of 42 nephew-domain groups with `cap_colour` null on every
  one. 182 confirms the key independently: the boy in the pond is bare-headed
  for swimming and names the other two. Read the first page for a per-boy key
  before deciding a colourless title is unnameable.
- **THE BALLOON OVER A CHARACTER IS NOT HIS.** Two calls in *Ten-Star Generals*
  would have gone the wrong way on placement alone. 186 g6 sits squarely over
  Donald and its tail runs the other way, into the Marshal's shoulder at panel
  (452,155). 188 g11 ("NOW HE'S DRIFTED INTO THE TERRIBLE DEMONS' WHIRLPOOL!")
  reads like a nephew's line, and a long spur sweeps left out of the balloon to
  end 24px off the Marshal's face at his eye level, with the three boys
  clustered 100px below. Both were caught only by cropping the tail.
- **THIS BULLET WAS WRONG AND THE REVIEW OVERTURNED IT; SEE THE 2026-09-04
  REVIEW SECTION BELOW.** It claimed that *A Christmas for Shacktown* 019 p4's
  balloon had "three rounded lobes" that only looked like tails, and gave the
  line to Donald alone off the one spur at the right. At 2.4x the bottom edge
  is four SHARP POINTS, one aimed at each figure, and the review made the
  speaker `other:Donald, Daisy, and the nephews`. A shape that looks like one
  tail per figure usually IS one tail per figure. Do not distrust it; zoom it.
- **A tip in a gap went one head LEFT again, and a measured tip beat the rule.**
  *Ten-Star Generals* 180 g9 and *Shacktown* 036 g15 are both gap tips resolved
  one head left, per the twenty-fifth batch. But *Shacktown* 006 g11 was a gap
  tip read off a 0.65 sheet that would have gone to the green boy, and a 3x
  crop put the tip at panel (417,418), exactly on the red cap's leading edge.
  The rule is the fallback for a tip you have actually measured and that still
  lands between two heads -- not a substitute for the crop.
- **Two of the three engines' devices need a type, and `allbold` under-reports
  on short groups.** *Shacktown* 035 p5 splits one cluster of drawn question
  marks into two groups and labels one `background` and one `sound_effect`;
  both are the same device over Scrooge and both were set to `thought`, which
  is what 008 g9 already stores for the identical thing. And `allbold` scored
  *Ten-Star Generals* 180 g5's "HAVE" at 1.07 when a 5x crop shows it plainly
  bold: a four-word group's own baseline is dragged up by its one bold word, so
  the 1.3 threshold under-reports there. The 250px montage is the sanctioned
  view for emphasis; the tool is a screen.
- **A WORDLESS DEVICE MUST NOT GO IN `visible_text`.** Recording "a red diamond
  badge is drawn on the Woodchuck cap" as prose put a false missed-text finding
  on all ten pages of *Ten-Star Generals*. The audit matches `visible_text` by
  substring against the groups' text, so prose about a device that carries no
  letters can never match anything. Prose belongs there only when the device IS
  lettering and is genuinely ungrouped -- which is how *The Truant Nephews* 203
  panel 8's three drawn "!" marks were surfaced, correctly, as the batch's one
  real missed-text item.
- **A MANGLED UNICODE ESCAPE IS A TEXT CORRECTION.** *Ten-Star Generals* 189 g6
  ends with the literal characters `u2014` where the art has an em dash, and
  the caption on the same page stores its dash correctly. Decode before
  grepping: a raw grep for `u2014` hits every legitimate `\u2014` escape in an
  ASCII-escaped file and tells you nothing. One occurrence in 690 groups.
- **A TITLE'S FILLER PAGES CARRY GROUPS AND REACH NOBODY.** `vision-apply` on
  *A Christmas for Shacktown* logs "35 page(s)" against 32 prepped. The three
  are 208 (FRONT_MATTER) and 209/210 (BACK_MATTER) -- one-page gag strips bound
  with the story, carrying **21, 12 and 14 grouped balloons** on both engines,
  none of them annotated, none in any queue. Read that log line: the mismatch
  is the only thing that says so.
- **The collectives can be the story rather than a failure.** *The Truant
  Nephews* finishes on 88 of 129 nephew-domain groups collective, and that is
  what the art gives: the boys are under a truck tilt, inside a packing crate,
  or drawn as three pairs of eyes in a solid black panel for most of it, and
  where they are on the page their black crowns are usually turned so no wedge
  shows. Every panel that printed two or three wedges was named. Say which kind
  of collective it is in the note -- absence looks identical to under-naming in
  a queue, and only one of them is worth a reviewer's time.
- **`identified_by` will not accept `cap-colour` with a null colour.** Three
  elimination calls -- name the third boy because the other two caps in the
  panel are readable -- were refused by validation for claiming cap-colour on a
  boy whose own crown printed nothing. The evidence there is the tail plus the
  OTHER caps, so the list is `balloon-tail` and the elimination goes in the note.

### Findings to paste into the next run (2026-09-04, twenty-sixth batch, two titles reviewed)

*Ten-Star Generals* (Vol. 10, 117 groups) and *The Truant Nephews* (Vol. 10,
176 groups after the review added five and deleted one) both reviewed and
mirrored clean the same day. **51 speaker corrections over 288 groups**, and the
two titles could not be further apart: 4 of 117 (3.4%) against 47 of 171
(27.5%). The whole difference is one habit.

- **A NULL CAP CENSUS IS NOT EVIDENCE OF ABSENCE, AND `heads.py` CANNOT SEE A
  VOL. 10 WEDGE.** 40 of *The Truant Nephews*' 47 corrections are a nephew the
  pass declined on a cap it had called unreadable, every one of them coming back
  with a colour the reviewer simply read. The mechanism is now measured: on 198
  p7 the pass wrote "their caps turned to the reader as plain black crowns --
  heads.py finds no cap ink at all on the panel", and a 3.6x crop of that exact
  panel shows red, green and teal wedges on the three crowns. They are 30-60px
  slivers riding the TOP EDGE of the crown, under `heads.py`'s 120px `MIN_CAP`
  floor and above the white-skull band it anchors on, so it is structurally
  blind to them. Re-running it as `heads.py <panel> 40` finds them.
  **Never write `nephews` off a silent census. Drop the floor, then crop at
  3-4x, and only then decline.** The twenty-fifth batch already said a zero
  census is a reason to crop; this is the same finding costing 40 names.
- **The per-page split says it outright.** Pages where the pass cropped the
  wedges came back at **0%** (199, 207). Pages where it stopped at the census
  output came back at **37-71%** (200 71.4%, 206 66.7%, 202 60.0%, 205 37.5%).
  Nothing else about those pages differs.
- **A MEDIUM WAS NOT SAFER THIS TIME.** 2 of 7 mediums corrected (28.6%) against
  44 of 164 highs (26.8%) -- the first title in the corpus where the two rates
  match. Both corrected mediums were gap tips the pass named anyway (200 g7,
  202 g9, both `Dewey` -> `nephews`). Hedging a gap tip to medium did not make
  the name any more survivable; the roster's answer for a tip you cannot place
  is the collective, not a name at lower confidence.
- **THE VOL. 10 RIGHT-OVERSHOOT IS NOT CONFINED TO TIPS THAT LAND IN A GAP.**
  All three of *The Truant Nephews*' name-to-name swaps are on 206, and all
  three are the same move: the pass named the boy the tip sat on, and the answer
  was the boy one place to his LEFT. 206 p4 g8 went to the red boy at head
  (652..837) and belongs to the middle boy; 206 p5 g9 and g10 each slid one boy
  right in the same way. This is the offset fan the pass DID diagnose on 207 p7,
  where the leftmost tip landed on nobody and gave the drift away -- on 206 every
  tip landed on a head, so nothing flagged it and the whole row went out by one.
  On a Vol. 10 three-boy row, place the fan and then ask whether shifting it one
  boy left fits better, even when every tip is sitting on a face.
- **And do not read a wedge colour off a 0.6-scale sheet.** The pass recorded the
  leftmost boy of 206 p5 as having "a dark cap with a hint of green". A census at
  a 40px floor finds no chromatic ink on that head at all. A colour that was
  eyeballed rather than sampled is worth less than no colour, because it gets
  written into `cap_colour` as evidence.

*Ten-Star Generals*, by contrast, corrected 4 of 117 with 0 of its 4 mediums
touched, and its three lessons are small:

- **THE EVIDENCE WAS IN THE PASS'S OWN NOTE, AGAIN.** 180 g7 and g9 both came
  back as one nephew swapped for another. The pass had written the correct
  reading into its note as the alternative -- "in p4 the left boy is Dewey
  pointing at Huey; in p5 the left boy is Huey pointing at Dewey" -- and voted
  against it because both tails landed on the boy in the same position on the
  page. The boys take turns introducing each other: the boy POINTED AT in one
  panel is the one SPEAKING in the next. Where a story has a boy name his
  brother, read the next panel before assuming a single spokesman.
- **A per-boy key works on the DRAWING as well as the words.** 181 g8 was
  declined because "no boy is drawn clearly enough"; the reviewer named Huey
  because he is the one making the bow. The pass had built the whole title on a
  badge key -- bow Huey, canoe Dewey, life-saving Louie -- and applied it only
  to what a boy SAID, never to what he was doing with his hands.
- **A label pointed at an object in the author's voice is `narration`.** 185 g11,
  the "DONALD'S BOW!" tag, went `none`/`background` -> `narrator`/`narration`.
  It is Barks labelling the giveaway for the reader, not lettering inside the
  scene, and the test is whose voice it is rather than whether it sits in the art.

**And two things the review did to the data, both worth checking for.** It added
five groups and deleted one. 203 gained the three drawn "!" marks the pass had
reported as missed text **plus a `TOOLS` crate stencil in the same panel that the
pass had not reported** -- the audit cannot find what `visible_text` does not
hold, so an incomplete capture reads as a clean audit. And the pass's `visible_text`
entry there was PROSE, which never matches a group by substring, so the audit went
on reporting the item after the review had grouped it; one line back to the bare
lettering and it goes quiet. 204 gained a second `TOOLS` overlapping the one
hand-added on 2026-08-29 by 96%, which was deleted again -- and that deletion left
id 15 as a GAP rather than renumbering the page, identically on both engines.
Gaps are tolerated: 32 of 5557 pages in the corpus already have one.

### Findings to paste into the next run (2026-09-04, twenty-sixth batch, third title)

*A Christmas for Shacktown* (Vol. 11, 32 pages, 401 groups) reviewed and
mirrored clean, no group added, deleted or renumbered: **19 speaker corrections,
4.7%**, 12 of them in the nephew domain (19.4% of 62). High 18 of 393 (4.6%),
medium 1 of 8. **All 6 of the pass's type corrections were confirmed** and the
review made 4 more of its own. One text edit the pass had not proposed: 016 g9's
`. . . .` tightened to `....`, which is spacing rather than a word, so leaving
it was within the roster -- but the reviewer wanted it.

**Batch total: 70 corrections over 690 groups across the three titles, 10.1%,
and the spread is 3.4% / 4.7% / 27.5%.** The outlier is entirely the wedge-census
failure recorded in the previous section.

- **THE BIGGEST CLASS HERE IS NOT NEPHEWS AT ALL -- IT IS WHICH ADULT, AND WHAT
  TO CALL A GROUP.** 6 of the 19 are an `other:` role, and they split three ways.
  (a) The reviewer's collective for a crowd of one kind is **plural and bare**:
  `other:one of the engineers` came back twice as **`other:the engineers`**.
  Use the plural form for an unnamed group from the start. (b) A mixed group of
  named characters gets all of them: 019 g6 Donald -> **`other:Donald, Daisy, and
  the nephews`**. (c) And an unnamed adult must not be given a name that fits:
  037 g5 Daisy -> **`other:a woman`**, 029 g7 Scrooge -> `other:one of the
  engineers`, 030 g13 the reverse.
- **DO NOT NAME AN ADULT FROM A PROP THAT IS NOT UNIQUE.** 029 g7 ("MY SPECTACLES
  FELL IN, AND I HAVEN'T HEARD 'EM HIT BOTTOM!") was given to Scrooge on the
  reasoning that "he is the only character in the story who wears them". He is
  not -- the engineers wear them too. A prop only identifies when you have
  checked every other figure in the panel for it, and a panel full of
  interchangeable bearded men is exactly where that check fails.
- **A BLUE SAILOR CAP IS NOT ALWAYS DONALD'S, AND A TAIL POINTING AWAY IS NOT AN
  OFF-PANEL SPEAKER.** Both Donald -> Scrooge corrections are this. 031 g4: the
  hand drawing the tunnel on the chart was read as "the duck in the blue sailor
  cap"; it is Scrooge. 017 g12: the pass traced the tail as pointing down-LEFT,
  away from the only figure in frame, and concluded an off-panel Donald -- the
  line is Scrooge's. A tail leaving the frame is a reason to widen the crop, not
  to award the line to whoever is off-panel.
- **THE PASS OVER-READ CAPS HERE AS BADLY AS IT UNDER-READ THEM ON THE OTHER
  TITLE.** 4 of the 19 are a named boy going back to `nephews` with the colour
  stripped (007 g3, 007 g6, 013 g0, 031 g8), against only 2 the other way. On a
  title whose stocking caps are big and clean, the failure flips direction: the
  cap is legible, so the temptation is to trust a tail you have not actually
  traced and let the nearby cap supply the name. Cap legibility is not tail
  evidence.
- **A CAPTION BOX IS NOT ALWAYS THE NARRATOR.** 035 g7 went `narrator` ->
  `Louie`, with a green cap recorded. The pass called it "caption box across the
  top of panel 4" on shape alone. A box at the top of a panel in a character's
  voice is still that character; read whose voice it is before reading the frame
  around it.
- **A SILHOUETTE PANEL IS NOT AUTOMATICALLY THE BOYS.** 033 g11 and 034 g1 both
  went `nephews` -> `Donald`. The pass wrote "the party in silhouette; nothing
  separates the figures at that scale" -- but the party contains Donald and
  Scrooge as well as three boys, and silhouettes still differ in HEIGHT. Measure
  the outline before falling back to the collective.

### Findings to paste into the next run (2026-09-04, the Vol. 11 one-pagers)

All nine Vol. 11 one-pagers passed, reviewed and mirrored: 125/125 on both
engines after the review added two groups. **1 speaker correction in 123
pass-written groups, 0.8%** -- the best rate of the day against 3.4% / 4.7% /
27.5% for the three full titles, and *The Gilded Man*'s three pages came back
0 of 52 highs corrected. A one-pager is the easiest unit in the corpus: seven
or eight panels, a cast of two or three, and every panel legible on one montage.

- **ONE TAIL SETTLES BOTH THE SPEAKER AND THE TYPE, AND THE PASS SPLIT THEM.**
  *Awash in Success* 142 g1, `BZZT! BZZT! BZZT!`, took the batch's only speaker
  correction AND had its type correction rejected -- and the two are one error.
  The pass read the noise as the buzzer box the three boys are crouched over,
  wrote `nephews`, and proposed `dialogue -> sound_effect`. The review made it
  **Huey** with red recorded and put the type back to **dialogue**: the boys are
  making the buzzing noise themselves.
  The tell was in the drawing the whole time. The balloon carries an ordinary
  pointed tail landing on the red-capped boy. A balloon with a tail on a
  character is that character's VOICE -- so the same tail that names Huey also
  says the sound is not a machine. The pass used the tail to name the maker of
  what it had already decided was a machine noise, instead of letting the tail
  decide whether it was a machine noise at all. **Read the tail before the
  prop.** A device in the panel is not evidence about the type; a tail on a head
  is evidence about both.
  It had also already seen the cap -- its own note says "the left boy carries a
  red segment and the right a green one" -- and declined it because "the balloon
  serves the device the three of them are operating together". Same
  use-the-evidence-you-already-wrote shape as *Ten-Star Generals* 181 g8.
- **THE REVIEWER'S LINE ON DRAWN DEVICES IS NOTATION.** Three ungrouped devices
  turned up in these nine pages and were settled three different ways, which
  together give the rule. Drawn punctuation gets a group: 143 `? ? ?` over
  Donald went in as **thought / Donald**, 196 `! ! !` over the boys as
  **dialogue / nephews** -- so the type follows whether a voice makes the sound,
  exactly as for words, and the speaker is whoever the device hangs over. Drawn
  MUSIC does not: the balloon of notes over Donald whistling on 197 p4 was left
  ungrouped and is now in `missed-text-ignore.txt`. Notation carries no lettering
  for the OCR to hold.
- **RECORD EVERY DEVICE ON THE PAGE, NOT THE ONE THAT CAUGHT YOUR EYE.** The pass
  reported 143's `? ? ?` and MISSED 196's `! ! !` two pages later, because it
  never put that one in `visible_text` -- and the audit can only find what the
  capture holds, so it reported a clean page. That is the second time in one day:
  *The Truant Nephews* 203 lost a `TOOLS` stencil the same way while its `!`
  marks were reported. Sweep the page for devices as a step, the way the cap
  census is a step.
- **THE PHANTOM `type_was` IS NOT INERT.** `vision_apply` wrote
  `"type_was": "background"` onto 109 g0, whose type is `title` before and after
  and for which the pass supplied no type at all. `vision-corrections` does not
  see it, because the type never changed -- but `review_findings.py` DOES, and
  reports it as a real `background -> title` type correction, inflating the
  count and crediting the pass with an overrule it never made. Check a type
  correction against the previous commit before believing the tally.
- **The one-pager apply route is per PAGE, not per volume.** Vol. 11's nine split
  three ways: 208/209/210 resolve through *A Christmas for Shacktown*, 108/109/142
  through *The Golden Helmet*, 143/196/197 through *The Gilded Man* -- each
  through the story it is physically bound inside. The queue names the owning
  title per page. Checking that SOME configured title in the volume reaches the
  page is the right feasibility test, but it does not tell you which one to name.
- **And the stopgap prep's panel numbers are not the pipeline's.** The hand-built
  out-dir numbers panels from the panel-segments file, which does not match the
  prelim's `panel_id`: on 143 the logo is `panel_id` 0 but panel 1 here, and the
  two drift apart mid-page. Group data is unaffected -- the panel references in
  notes and `panels_of_note` are not. Say which numbering a note uses.

**Vol. 11's one-pagers do NOT use the volume's feature-story cap.** *A Christmas
for Shacktown* puts the boys in solid pompom stocking caps; all nine one-pagers
use the SEGMENTED BEANIE, a black crown with coloured segments, in the same three
inks. Construction is per story, not per volume -- and on the one-pagers it is
usually turned away, so 8 of 23 nephew-domain groups are named and the rest are
pages where the boys are bare-headed, established at a 30px cap floor.

### Findings to paste into the next run (2026-09-04, twenty-seventh batch, two titles reviewed)

*Terror of the Beagle Boys* and *Gladstone's Usual Very Good Year* reviewed and
mirrored. **12 speaker corrections in 262 pass-written groups, 4.6%** -- but the
two titles could hardly be further apart, and the split is the whole story:

```
Terror of the Beagle Boys    0 of 122   0.0%   no nephews in the story at all
Gladstone's Usual...        12 of 140   8.6%   7 of 29 in the nephew domain (24.1%)
                                               highs 10/129 (7.8%), mediums 2/11 (18.2%)
```

**A TWO-HANDER WITH NO NEPHEWS IS THE CHEAPEST UNIT IN THE CORPUS.** *Terror* is
Scrooge and Donald for ten pages and came back **0 of 122**, beating even the
Vol. 11 one-pagers' 0.8%. Every call rested on a traced tail, on a costume key
that never varies (Donald in the black jacket and red bow tie, Scrooge in the
blue coat) or on what the line says, and all 122 went at high. When a title has
no cap to read, do not spend the cap budget on it -- read the tails and go.

- **THE CAP-REFERENCE PANEL IS ALSO A PANEL YOU HAVE TO NAME PEOPLE IN.** Four
  of *Gladstone's* seven nephew corrections are one panel, **050 p1 -- the very
  panel the pass used to fix the title's palette.** It measured green `#519d3e`,
  blue `#00a5d7` and red `#e51b20` on three badges in a row, wrote all three
  hexes into its own note, and then recorded every balloon in the panel as
  `nephews` because "the three heads overlap". The review named all four off
  those measurements. Deriving the palette from a panel and then declining to
  apply it *there* is the purest form of the use-the-evidence-you-already-wrote
  error: the panel you chose as the reference is by construction the one where
  the caps read best.
- **A PER-TITLE COLOUR RULE BUILT ONLY FROM LIT BADGES WILL FAIL ON THE SHADED
  ONE, AND IT COST TWO NAMES.** The pass observed that *Gladstone's* blue prints
  `#00a5d7` H194.0 S1.00 V0.84 in every panel it measured, and turned that into
  "a cool badge that is not exactly the blue is the green". 054 g9's `#1da39e`
  (H177.8 S0.82 V0.64) is a **shaded blue**, and the review made it Dewey. The
  value rule that worked on *The Screaming Cowboy* -- green at V0.64, blue never
  below V0.74 -- would have given the same wrong answer here.
  What actually separates them in this title is the GREEN's range, not the
  blue's: the green badges run **H117-130** (`#4e9c51`, `#50984d`, `#4da33e`) and
  never leave it, so **anything cooler than about H140 is the blue, however
  muddy it looks.** That is [[project_teal_band_was_blue_not_green]] again, and
  the pass had that memory and reasoned past it.
- **AND THE ELIMINATION INHERITS THE ERROR.** 054 g11 was named Dewey by
  "two named leaves the third" -- correct reasoning on top of the wrong first
  read, so the review had to flip it to Louie as well. One misread badge cost
  **both** names in the row. Elimination is only as good as the cap it
  eliminates from; sample the third badge before leaning on it.
- **A DUCK IN DONALD'S OUTFIT WITHOUT THE HAT IS NOT DONALD.** 057 g1: the pass
  read the figure beside the tipping bowl as Donald "who has lost his beret in
  the fall", on the strength of the black-and-white striped sleeves. The review
  made it **Huey**, red recorded. In this title the nephews wear black jackets
  too, so the sleeve is not a Donald key -- the beret is, and its absence should
  have forced a cap probe rather than an explanation for why it is missing.
- **A STARTLE IS A STARTLE WHETHER OR NOT THE BEAK IS OPEN.** 056 g7, the single
  red exclamation mark over Gladstone as he takes in the size of the bowl, was
  typed `thought` on the reasoning that he is startled *silently*. The review
  made it **dialogue**. That is not a new rule -- the corpus split is already
  "a musing device is `thought`, a startle is a vocalised gasp and so
  `dialogue`" (Vol. 6 088 g12 against 081 g7) -- it is the same rule applied to
  a figure whose mouth is not drawn open. The "silently" was an inference, and
  the art did not supply it. Running score for a lone `!`: dialogue 3, thought 1.
  Do NOT reduce this to the glyph: `!` is not automatically dialogue, and 081 g7
  is a lone `!` the reviewer kept at `thought`.
  The pass's other two type proposals (054 g14 `BZZT!` and 057 g5 the ticket
  number in its own balloon, both to `dialogue`) stand as written.
- **THE PHANTOM `type_was` INFLATED THE TALLY AGAIN, THREE TO ONE.**
  `review_findings.py` reported 6 type corrections for *Gladstone's*; 048 g12,
  051 g12 and 053 g12 already carried `type_was` at the pass commit and are not
  review work at all. **One** type correction was actually made. Diff `type_was`
  against the pass commit before quoting the number -- this is the third batch
  in a row where it has misled.
- **A REVIEW CAN HAND BACK A ROLE NAME THAT DUPLICATES AN ESTABLISHED ONE.**
  `other:Holsworthy Hog` became `other:Woodchucks chief` (6 groups after
  mirroring), and the corpus already carries **50** groups on
  `other:the Junior Woodchucks chief`. Grep the corpus for the new value's
  neighbours the moment a review renames a free-text role, and raise it before
  it spreads.
- **A four-dot ellipsis and a four-dash run are the same thing at 300px.** The
  pass marked 057 g4 `text_ok` true off the montage; the art reads
  `NUMBER! ----`, not `NUMBER!...`, and the reviewer hand-edited both engines.
  A run of small marks inside a balloon is not a `text_ok` you can grant from a
  contact sheet.
- **Missed text handed back is not done until it is on disk.** *Terror*'s two
  additions (011 p6's burst-cloud `! !`, 015 p6's fifth `BEAGLE BOYS`) are still
  not there -- group counts are unchanged on both engines -- so the title is
  122/122 on speakers and still owes two boxes. Check the counts, not the
  hand-back.

### Findings to paste into the next run (2026-09-04, twenty-seventh batch, third title)

*The Screaming Cowboy* reviewed and mirrored, 141/141. **26 speaker corrections
in 141 groups, 18.4%, and 20 of 60 in the nephew domain -- 33.3%.** The worst
title of the run by a factor of three, and it closes the batch at:

```
Terror of the Beagle Boys     0 of 122   0.0%    no nephews in the story
Gladstone's Usual...         12 of 140   8.6%    7 of 29 nephew (24.1%)
The Screaming Cowboy         26 of 141  18.4%   20 of 60 nephew (33.3%)
batch                        38 of 403   9.4%   27 of 89 nephew (30.3%)
   highs 18/119 (15.1%) against mediums 7/21 (33.3%) on the third title
```

- **THE TEAL BAND IS THE BLUE. I GOT THIS WRONG TWICE IN ONE BATCH, IN OPPOSITE
  DIRECTIONS, AFTER BUILDING A RULE THAT SAID SO.** In *Gladstone's* I anchored
  on the blue ("it always prints exactly `#00a5d7`, so a cool badge that is not
  that is the green") and a shaded blue at H177.8 came back Dewey. In *The
  Screaming Cowboy* I anchored on VALUE instead ("green at V0.64, blue never
  below V0.74") and **four** shaded blues came back Dewey: 063 g11 `#2ca487`,
  064 g0 `#2da49c`, 065 g2 `#3ba487`, 067 g7 `#3d967a`, every one of them
  H160-178 at V0.59-0.64.
  Both rules were built from the LIT badges in the title and then applied to the
  shaded ones, which is the one place they cannot hold: shading moves a blue
  down into the green's value and across into the green's hue.
  **Anchor on the green instead. It is the stable ink in both titles --
  H108-130 in *Gladstone's*, H108-112 here -- and anything cooler than about
  H140 is the blue however muddy it looks.** This is
  [[project_teal_band_was_blue_not_green]], which I quoted and then reasoned
  past.
- **AND I NAMED A PINE TREE AS A CAP.** 061 g7's `#4da140` at H112.7 is the tree
  green I had written into that title's own commit message as a look-alike --
  "the cap green to two decimal places, so a green blob has to be shown sitting
  on a head before it names anybody". I then took a blob at (769,451) and named
  the boy under it without checking. The reviewer made it Huey. A `capscan` hit
  is ink, not a cap; put the crop up and see the head.
- **ROLE REASONING LOST TWICE ON WIDE SHOTS.** 061 g11 ("Donald is the one who
  would rent the cabin") and 062 g3 ("Donald leads the hunt, and he speaks in
  the panels either side") both went to **nephews**. On a wide shot where no
  figure is readable, a line about what the party is going to do next belongs to
  the boys -- they are the detectives in this story and Donald is the one being
  managed. "Who would say this" is not evidence; it lost both times it was used.
- **A DIALOGUE CHAIN NAMES ACROSS ONE PANEL, NOT ACROSS AN INTERRUPTION.** The
  one over-naming, 063 g5, was named Huey because the objection two panels later
  is answered by a boy whose cap reads red -- so, I argued, the opening line was
  his too. The review made it `nephews`. Contrast 067 g12, where the same
  reasoning was NOT corrected: there the question and its answer are adjacent
  panels with nothing between them. When another boy speaks in between, the
  chain is broken.
- **A SECOND COPY OF A GROUPED STRING NEEDS ITS OWN `visible_text` LINE.** The
  review added 058 g17, the `313` licence plate in panel 4. The pass had grouped
  the same plate in panel 7 and written **one** `313` into `visible_text`, so the
  audit matched it against the panel-7 group and reported the page clean --
  [[project_vision_audit_nearmiss_gap]] exactly.
  There is no `visible_text` spelling that fixes this, and it is worth being
  exact about why: the audit matches on containment after normalising to letters
  and digits, so a second bare `313` dedupes against the first and a located
  form ("313 on the licence plate, panel 4") matches no group's text and would
  report the page dirty for ever. **The only thing that finds a second copy is
  counting the copies in the art against the groups on the page**, which is the
  same check the *Terror* 015 jersey needed -- five `BEAGLE BOYS` in one panel
  against four groups. Do that count on any panel that repeats a string.
  Corollary, learned by tripping over it: **once such a copy IS grouped, take
  the descriptive form back out of `visible_text`.** Left in, it is a finding
  the audit can never clear.
- **Under-naming is still the biggest single class: 9 of 26.** Most were panels
  where the note says "no cap stripe readable at this size" -- 065 g0/g1, 066
  g1, 067 g0/g1/g4. The reviewer's own note on 067 g0 is the method: **"Not
  Dewey or Huey"** -- elimination against the *other balloons in the scene*, not
  just against the other caps in the panel. If two of three boys in a
  three-balloon exchange are named, the third is named too, whatever his cap is
  doing.
- **The free-text role name drifted inside a single batch.** The review renamed
  the same role two ways: `other:Junior Woodchuck` in *Gladstone's* and
  `other:a Junior Woodchuck` here, 4 and 8 groups. And `other:Woodchucks chief`
  (6) sits beside the corpus's established `other:the Junior Woodchucks chief`
  (50). Grep the family whenever a review renames a role, and raise it.

### Findings to paste into the next run (2026-09-04, twenty-eighth batch, three titles reviewed)

*Statuesque Spendthrifts*, *Rocket Wing Saves the Day* and *Gladstone's
Terrible Secret*, all Vol. 11, reviewed and mirrored together.

```
Statuesque Spendthrifts       4 of 138   2.9%    1 of  5 nephew (20.0%)
Rocket Wing Saves the Day    14 of 160   8.8%   14 of 65 nephew (21.5%)
Gladstone's Terrible Secret   5 of 120   4.2%    5 of 15 nephew (33.3%)
batch                        23 of 418   5.5%   20 of 85 nephew (23.5%)
   highs 15/387 (3.9%) against mediums 9/31 (29.0%) -- a 7.4x ratio
```

- **A COSTUME KEY DOES NOT TRAVEL OUT OF THE PANEL THAT DEFINES IT. Three of
  *Statuesque*'s four corrections were this one move.** The title turns on
  telling the mayor from the park commissioner, and 069 g7 settles it by direct
  address -- one official calls the other "MAYOR!" -- so I fixed RED bow tie =
  commissioner, BLUE = mayor, and 076 g14 then hands over a figure in a yellow
  sash lettered MAYOR wearing the blue tie, which looked like independent
  proof.
  The review KEPT every call I made in a panel holding BOTH officials (068 g3,
  g5, g7, g8, g9, g10; 069 g7, g8; 072 g1, g2) and OVERTURNED every call I made
  in a panel holding ONE, all three to the mayor (071 g13, 074 g1, 074 g2).
  074 g2 is the one that matters: I measured a 250px `#e61b1f` bow tie at head
  height, on a lone official, and called it high.
  So the tie separates two figures standing next to each other; it does not
  name a character across the story. **A lone official in this title is the
  mayor.** Generalised: a key derived from contrast -- this one is red, so that
  one is blue -- is only ever valid where the contrast is visible. Carrying it
  into a solo panel is inventing a fact.
- **THE BIGGEST CLASS IS A RULE I HAD, USED CORRECTLY THREE TIMES, AND THEN
  DECLINED TO USE EIGHT TIMES.** All eight of *Rocket Wing*'s under-namings are
  a boy whose crown capscan reported blank, and my note in every case says so
  and stops -- "his crown carries no chromatic ink", "no cap ink at a 15px
  floor". The reviewer named all eight and supplied a colour for each, and the
  method is written into their own note on 078 g8: **"Not Louie or Huey"**.
  That is elimination against the other boys in the panel, not a reading of his
  cap. I applied exactly that reasoning on 080 g5, 085 g4 and 095 g6 -- and all
  three were kept.
  **Where three boys are in frame and two carry measurable bands, the third is
  named, and cap_colour stays null.** This is not a new rule; it is
  [[feedback_two_named_leaves_the_third]], and the failure was applying it
  inconsistently inside a single title.
- **A MEASURED BAND IS NOT ENOUGH -- THE TAIL HAS TO LAND ON THE HEAD THAT
  WEARS IT.** Three of the five name-for-name swaps were mediums with the tip
  in a gap, which is the expected cost. The two that should not have happened
  were HIGH and had a band quoted to the pixel: 085 g14 (Dewey -> Huey) and
  086 g16 (Huey -> Dewey). On 086 g16 I wrote "tail comes down onto the
  RIGHT-hand boy, whose band is capscan #e51920 1104px at (473,390,523,498)"
  -- two separate claims welded into one sentence, and I checked neither
  against the other. Say which boy the tail lands on, then say which boy the
  blob sits on, and only then join them.
- **IN A STORY WHERE DONALD IS ONE OF THE SNOOPERS, HE TAKES THE BOYISH LINES
  TOO.** Two of *Gladstone's* five corrections are `nephews` -> `Donald`:
  094 g9 "AW, WE ARE NOT!" and 096 g9 "HOORAY FOR UNCLE SCROOGE!". I read both
  as a boy's register. 091 g11 went the other way -- I traced a short tail onto
  Gladstone and it was the hidden watchers -- so the register test failed in
  both directions in one title. Where Donald is crouching in the hedge with the
  kids, register is worth nothing and only the tail counts.
- **`review_findings.py --since <sha>` lists every group that CARRIES
  `type_was`, not only the ones changed since that sha.** Thirteen of the
  nineteen "type corrections" it reported for this batch predate the batch
  entirely -- 081 g12-g14, 082 g2/g9/g14, 084 g11, 085 g0, 091 g8, 094 g7,
  095 g1, 073 g9, 079 g10 all already had the field at `b8af9d7c~1`. Check
  `git show <base>:<file>` before crediting a type change to the review, or the
  findings section records work nobody did.
- **The review rewrote `speaker_confidence` to high on all 420 groups**, as
  usual, so `--since` is not optional if the medium-against-high split is
  wanted -- and on this batch that split is the most useful number in the
  review.
- **The two review-added groups arrived CLEAN this time.** 075 g6
  (CORNELIUS COOT) and 076 g15 (MAYOR) both landed on both engines with
  matching ids, `speaker: none`, `type: background`, `vision_added: true` and
  no trace of the seed group's ai_text, note or identified_by -- the Copy In
  residue trap did not fire. Two things still worth checking on any added
  group: both carry `vision_text_ok: null`, so the transcription has never been
  confirmed by anyone, and 075 g6's `panel_id` says 4 while its box lies inside
  panel 3.
- **WRITE `visible_text` AS THE BARE LETTERING. A LOCATOR MAKES THE FINDING
  PERMANENTLY UNCLEARABLE, INCLUDING AGAINST THE GROUP THAT LATER COVERS IT.**
  I recorded the two missed items as `"CORNELIUS COOT -- on the cap course of
  the pedestal in panel 3, above the dedication plate and outside every group's
  box"` and `"MAYOR -- lettered down the yellow sash across the mayor's chest in
  panel 7; no group covers it"`. The locators were meant to help the reviewer
  find them, and they did — but the audit matches on letters and digits, so
  after the groups were added **both entries still reported "grouped by NEITHER
  engine"**, and the second one's "no group covers it" had become a lie sitting
  in the record. Rewritten to `CORNELIUS COOT` and `MAYOR`, both cleared at
  once.
  The twenty-seventh batch found half of this for a SECOND copy of an
  already-grouped string; the general rule is stronger. **`visible_text` is a
  transcription field: put the lettering in it and nothing else.** Where to look
  belongs in `queue-missed.txt`, which is prose by design and which the audit
  never reads.
  The exception that has no fix: lettering that is a bare glyph. 068 g14's
  group text is `$`, which reduces to nothing, so no wording of `visible_text`
  can ever match it — those go to `missed-text-ignore.txt` even after they are
  grouped.
- **One straggler, and it was a TEXT edit that skipped the speaker stamp.**
  074 g3 ('AH!') came back as the single group of 420 never `speaker_reviewed`.
  Its text had been corrected in the same session (my `AH,` -> the drawn `AH!`),
  and the text-correction path evidently does not stamp the speaker. Handed
  back, stamped and re-mirrored, so the batch closed at 420 of 420 -- but count
  `speaker_reviewed` after every review, and look first at the groups whose text
  changed.

### Findings to paste into the next run (2026-09-05, twenty-ninth batch, one title reviewed)

*The Think Box Bollix*, Vol. 11, reviewed and mirrored. *Only a Poor Old Man*
was passed in the same batch and is not reviewed yet.

```
The Think Box Bollix   13 of 119   10.9%   13 of 38 nephew (34.2%)
   highs 13/118 (11.0%) against the one medium 0/1 -- the medium was KEPT
```

**The confidence split inverted, and that is the story of the batch.** The one
call hedged to medium survived and thirteen highs did not, because the failure
was not uncertainty -- it was a systematic move, reading cap slivers by eye off
a contact sheet, and a systematic move is written at high every time. A
confidence figure only measures what the pass knew it was unsure of.

- **A PLURAL PRONOUN IS NOT A CHORUS. Three of the five under-namings were
  balloons made collective because the words said WE'RE.** 100 g8 "WE'RE
  WORKING FOR MR. GEARLOOSE!", 100 g9 "WE'RE HIS ASSISTANTS!" and 102 g12
  "A WOLF! A WOLF!" all went `nephews` -> a name. A boy answering for the group
  still speaks alone, and the words never say how many mouths are open.
  The construction itself is real and the reviewer left it alone where it was
  drawn -- 107 g7's two tails stayed `nephews` -- so the test is the TAILS and
  only the tails. Count them, and let the pronoun say nothing.

- **THE VOLUME'S OWN HUE RULE, APPLIED TWICE AND DROPPED ONCE -- ON THE ONE
  SLIVER THAT WAS NEVER PROBED.** Vol. 11's rule is that the cap green holds
  H108-112 and anything cooler than about H140 is the blue however muddy it
  looks. The pass used it correctly on 106 p5 (`#27a395` H173.2 -> blue) and
  103 p8 (`#3b986f` H153.5 -> blue), and then called 106 p2 green by eye off a
  0.95-scale stack. It measures **139px of `#3a947a` H162.7 S0.61, with red 0
  and blue 0 elsewhere in the panel** -- the blue, by the same rule, and the
  review made it Dewey.
  Every sliver this pass PROBED survived the review; the ones it eyeballed off
  a contact sheet ran 2 right and 2 wrong. In a title whose foliage sits at
  H90-101 and whose cap green sits at H111-112, naming a cap green by eye is a
  coin flip. **The contact sheet says which boy has ink on him; it never says
  which ink.**

- **DEWEY IS THE BOY THAT GOES MISSING.** Seven of the thirteen corrections
  end at Dewey. The pass wrote Huey 5 / Dewey 5 / Louie 5 and the review closed
  at Huey 5 / **Dewey 10** / Louie 4. Where a sliver is cool and small, the
  answer has been Dewey far more often than not.

- **A DRAWN DEVICE WITH NO LETTERS IN IT CAN ONLY REACH THE REVIEWER THROUGH
  `queue-missed.txt`.** The review added three groups for the three `!` marks
  over the boys in 105 panel 7. The pass recorded them nowhere: not as groups,
  because `added_groups` is unusable, and not in `visible_text`, because a bare
  `!` normalises to nothing and the audit could never have cleared it. The
  missed-text hand-back is prose by design and is the only channel that works.
  Write "three drawn exclamation marks, one over each boy, 105 panel 7" there.
  The three arrived CLEAN on both engines -- matching ids and boxes, empty
  `ocr_text` and `notes`, no inherited note or ai_text, `identified_by` set --
  but all three carry no `vision_text_ok`, so nobody has confirmed the
  transcription.

- **WHEN A PANEL HOLDS AN ANIMAL THE STORY IS ABOUT TO REVEAL AS A TALKER,
  CHECK THE ANIMAL BEFORE THE BOYS.** 105 g8 "YEAH! A WOLF GOT HIM! A REAL
  WOLF!" was traced to the first nephew and belongs to the rabbit. The boxes
  settle it after the fact: the balloon sits at x226-650, the left of panel 7
  where the rabbit is, and the three added `!` marks at x671-1025 over the
  boys. That IS the gag -- the rabbit speaks, the boys react, and panel 8 pays
  it off with "Y-YOU'RE TALKING!". A speaking animal reads as scenery right up
  to the moment the story turns it over.

- **QUERY BACK TO THE REVIEWER: 105 g7's `cap_colour`.** It came back
  `Huey` with `cap_colour: red`. `capwide` over the whole of 105 panel 6 at a
  15px floor returns **red 0 blob(s) and blue 0 blob(s)**, and `heads.py` puts
  1,562px of `#4ea23e` H112.2 -- the volume's cap green to a decimal place --
  on the third boy, which is the boy the pass's tail landed on. Whatever
  settles the name, red is not printed anywhere in that panel, so the field is
  recording a colour the art does not carry.

- **`review_findings.py --since` over-reported the types AGAIN.** It listed
  103 g1 (`background` -> `dialogue`) and 106 g1 (`thought` -> `dialogue`) for
  this batch; a text-keyed diff against the pass commit shows neither type
  changed during the review, so both `type_was` values predate it. **Zero**
  type corrections this batch. Diff against the pass commit before crediting a
  type change -- and key that diff on `ai_text`, not on id, because a review
  that adds a group renumbers the page underneath it.

- **The review handed back a duplicate free-text name**, `other:a rabbit`
  against the three existing `other:the rabbit`. Normalised before mirroring,
  as the skill asks.

- **Two stragglers, and they are the page's tail again.** 105 gained three
  groups and its last two ids were the two never stamped -- the same shape as
  every other insertion. Count `speaker_reviewed` on both engines and look at
  the end of any page that grew.

### Findings to paste into the next run (2026-09-05, twenty-ninth batch, second title)

*Only a Poor Old Man*, Vol. 12, reviewed and mirrored. Same batch as *The
Think Box Bollix* above, and the two titles fail in the same place.

```
Only a Poor Old Man   10 of 400   2.5%    5 of 26 nephew (19.2%)
   highs 10/397 (2.5%) against mediums 0/3 -- all three mediums KEPT
   plus 8 text corrections and 2 added groups, none of it speaker work
```

- **A CAPTION BOX IS THE NARRATOR EVEN WHEN IT IS SET IN QUOTATION MARKS AND
  SPEAKS IN THE FIRST PERSON. Four of the ten corrections are this one call.**
  014 g11 `"FROZE MY FINGERS TO THE BONE..."`, 015 g1, 015 g3 and 020 g1 are
  Scrooge's Klondike, Montana and Spanish Main flashbacks, every one of them
  quoted and every one of them saying I and ME. The pass reasoned from exactly
  that -- "the narrator does not say me" -- gave all four to `Scrooge`, and was
  wrong four times out of four.
  The roster already says it: `narrator` is *a caption box, not a character*.
  It is a statement about the BOX. **The narrator can quote a character; the
  field still records the box and not the voice inside it.** Do not argue past
  it from the pronouns.

- **`text_ok: true` IS A CLAIM ABOUT LETTERING READ AT SIZE, AND ALL EIGHT
  TEXT CORRECTIONS WERE SMALL BACKGROUND LABELS CONFIRMED OFF A CONTACT
  SHEET.** 021 g10, 029 g1, 030 g2/g3/g8, 034 g4/g12 and 037 g9 are all Beagle
  Boy shirt labels, and every one was short -- a dropped `INC.`, a dropped
  prison number. The pass marked each `text_ok: true` having seen it only at
  250px in a montage, where the eye fills in a familiar shape it has already
  read correctly six times.
  This is the SAME root cause as *The Think Box Bollix*'s cap findings one
  title earlier, and it is worth stating once for both: **the contact sheet is
  for triage. Anything the pass is going to ASSERT -- a colour, a
  transcription -- has to be cropped first.** One title it cost cap colours,
  the next it cost eight transcriptions.

- **BOTH ADDED GROUPS ARE LETTERING THE PASS NEVER RECORDED, AND THEY FAIL IN
  TWO DIFFERENT WAYS.** 022 g11 is a Beagle Boy prison number `176-831`: the
  pass wrote `BEAGLE BOYS INC.` into `visible_text` for that page and left the
  number beside it out, so the audit had nothing to diff and reported clean.
  029 g12 is a drawn `?` over Donald -- a bare glyph, which normalises to
  nothing, so `visible_text` could never have carried it at all.
  With the three `!` marks from the previous title that is **four** missed
  devices in two titles. **Put every background label in `visible_text`,
  prison numbers included, and put every wordless drawn device in
  `queue-missed.txt` as prose, because that is the only channel that can
  carry it.**

- **THE MEDIUMS SURVIVED AGAIN.** All three of this title's mediums were kept
  and ten highs were corrected; across both titles of the batch that is 4
  mediums kept against 23 highs corrected. Two titles running, the confidence
  field has pointed the wrong way -- because both titles' errors were
  systematic moves the pass was sure of, not close calls. **A low correction
  rate among mediums is not reassurance; it means the damage is somewhere the
  pass never doubted itself.**

- **QUERY BACK TO THE REVIEWER: 027 g9 now claims `cap-colour` as evidence
  with `cap_colour: null`.** The review moved it `Dewey` -> `Huey`, set the
  colour to null and left `cap-colour` in `identified_by`, and the mirror
  copied that onto both engines. It is the exact combination `vision_apply`
  REFUSES from a pass -- "identified_by claims cap-colour but cap_colour is
  null. Record the colour that was read." **The validation that guards the
  pass does not guard the editor**, so a review can write a state the pass
  cannot. Either the colour wants recording or `cap-colour` wants dropping,
  and only the reviewer knows which. (The pass had measured 1,099px of
  `#03a4d5` on that head, so there IS a colour to record.)

- **A REVIEW CAN BE 400 OF 400 ON SPEAKERS AND HAVE TOUCHED NEITHER THE
  CORRECTIONS QUEUE NOR THE MISSED TEXT.** This one was, and it had not: the
  ten text and type corrections the pass proposed are still outstanding, and
  the `BOOM` on 027 that neither engine grouped is still ungrouped. They are
  separate review states and the speaker count says nothing about them. Run
  `vision-corrections` and the missed-text audit at the review close-out, not
  just at the apply.

- **AN OUTSTANDING-CORRECTIONS COUNT OF ZERO DOES NOT SAY THE PROPOSALS WERE
  ACCEPTED.** `vision-corrections` drops a group once `type_reviewed` is
  stamped, whether the reviewer took the proposed type or put the old one back,
  so "Nothing outstanding" reads the same either way. Read the STORED values:
  on this title all four came back `type` = the proposed value with `type_was`
  preserved and `type_reviewed: true` on both engines, so all four were
  accepted -- 008 g6 `sound_effect`->`dialogue`, and 020 g1, 025 g9 and 031 g7
  to `narration`. The text fix landed too. Check `type` against `type_was`
  before reporting a proposal as taken.

- **AN ADDED GROUP IS SOMETIMES APPENDED AND SOMETIMES INSERTED, AND THE TWO
  FAIL IN OPPOSITE WAYS.** *The Think Box Bollix* 105 re-sorted on save: ids
  shifted and the page's last two groups were stranded unreviewed, the familiar
  pattern. All three *Only a Poor Old Man* adds were APPENDED as the page's
  last id instead: nothing renumbered, nothing was stranded -- and the page's
  ids no longer follow the page. 027 now runs panel `1,1,2,2,3,3,4,4,6,7,8,5`,
  and 029 puts a panel-3 question mark after its panel-8 groups.
  So do not assume either behaviour. **After any add, check BOTH: count
  `speaker_reviewed` for stragglers, and list the page's `panel_num` by id to
  see whether reading order survived.** Do not renumber to fix the order --
  that is the one operation that invalidates everything keyed to the ids.

- **THE MIRROR MATCHES ON `ai_text`, SO ONE DROPPED CHARACTER STRANDS A
  GROUP.** The review typed 037 g9's label with a trailing period on easyocr
  and without it on paddleocr; the mirror could not pair them and the title sat
  at 401 of 402 reviewed with everything else clean. The tell is a mirror
  reporting one fewer copied than annotated. Diff the two engines' `ai_text`
  for the page and look for a one-character difference before assuming
  anything worse.

### Findings to paste into the next run (2026-09-05, thirtieth batch, two titles reviewed)

*The Golden Helmet* and *Houseboat Holiday*, both Vol. 11, reviewed and
mirrored together. Both mirrors clean: distributions identical on both
engines, zero per-group field mismatches.

```
The Golden Helmet   28 of 385   7.3%    highs 20/361 (5.5%)  mediums 8/24 (33.3%)
Houseboat Holiday   25 of 130  19.2%    highs 25/130 (19.2%) mediums 0/1
   GH: 5 of 5 type proposals accepted, 1 text fix landed, 3 groups added
   HH: nothing added, nothing outstanding -- every correction a speaker
```

- **A COLOURED GARMENT CARRIES THE CAP CONVENTION, AND NO BRIDGING PANEL IS
  REQUIRED. Twenty-four of Houseboat Holiday's twenty-five corrections are
  this one refusal.** From 147 p5 the boys swim for the rest of the story
  with their caps off, in trunks striped red, plain and blue. The pass
  recorded `nephews` on all of it and wrote the reason into every note: *"no
  panel shows a boy in both his cap and his trunks, so there is no bridge
  from the stripes to a name and the costume names nobody."* The review names
  them from the trunks anyway -- `identified_by: ['balloon-tail','costume']`,
  roster colour in `cap_colour` -- and the colours are the ones capscan had
  ALREADY MEASURED on those trunks: 147 p6 red `#d81e1f` on the left boy ->
  Huey, blue `#459aa6` on the right -> Dewey.
  The pass measured the ink that names them and then argued itself out of it.
  The rule: **the three inks name the boy wherever they are printed on him --
  cap, shirt, mittens, swimming trunks. Do not require a panel showing the
  cap and the garment together.** [[feedback_shirt_colour_names_them_too]]
  said this already; what is new is that the bridge is not a precondition.
- **ON A WIDE SHOT WITH NO READABLE FIGURE, THE LINE IS THE BOYS' -- five of
  the seven `Donald` -> `nephews` corrections.** 124 g13 "SMART IDEA! START
  YELLING!", 125 g4 "HELLO!", 126 g13 "IT'S THE FOREDECK...", 127 g11 "DO YOU
  SEE A HEADLAND...", 127 g13 "OLAF THE BLUE MUST HAVE FELT THE SAME WAY!".
  Every one was a MEDIUM where the pass wrote "given to Donald because he is
  the one giving orders / because he has the map" -- register reasoning, with
  the note itself conceding the drawing did not say.
  But it is **not** a blanket rule, and the counter-example is in the same
  title: 121 g13 "SEA BIRDS FLYING FOR COVER!" the pass DID give to `nephews`
  on that rule, and the review moved it to Donald. So: 5 wrong one way, 1
  wrong the other. Prefer the boys on a wide shot, and expect the nautical
  observations to stay Donald's.
- **THE CONFIDENCE FLAG WORKED IN ONE TITLE AND WAS USELESS IN THE OTHER, FOR
  A REASON WORTH KNOWING.** Golden Helmet's mediums corrected at 33.3%
  against its highs' 5.5% -- six times the rate, the first batch in three
  where the flag pointed the right way. Houseboat's corrected 25 highs and 0
  of its 1 medium. The difference is the KIND of error: Golden Helmet's were
  genuine close calls the pass knew it was guessing at, Houseboat's were one
  systematic rule the pass was certain of. **A medium is worth writing when
  the uncertainty is real; it cannot catch a wrong rule, because a wrong rule
  never feels uncertain.**
- **QUERY BACK TO THE REVIEWER: six Golden Helmet calls gained a `cap_colour`
  on panels where NO cap ink is printed at any floor.** 126 g0 -> Dewey/blue,
  127 g3 -> Louie/green, 127 g4 -> Dewey/blue, 128 g3 -> Louie/green, 129 g3
  -> Louie/green, 131 g6 -> Dewey/blue. Re-scanned after the review at a
  **15px** floor to check whether the pass had simply screened them out: 127
  p3 has no cap-green and no cap-blue at all (its only green is sea spray at
  `#51988f` H172.4 S0.47), and 128 p2's only blue is Donald's own 1,126px
  cap. So the names are not coming from ink on those panels, and the recorded
  colour is the convention read backwards -- which is exactly the tautology
  `cap_colour` exists to prevent. **What is the mechanism -- seating order,
  scene continuity from a nearby panel that does print, or the costume rule
  above?** Whichever it is, the pass should be applying it too, and cannot
  until it is named.
- **A REVIEW CAN HAND BACK BOTH A MISSPELLING AND A ROSTER COLLISION, AND THE
  MIRROR WILL DOUBLE THEM.** Golden Helmet came back with `other:Sharkey` on
  four groups against `other:Sharky` on thirty-four -- the art letters SHARKY
  (116 g6, 128 g12, 139 g0) -- and with `other:Azure Blue` on 116 g7, where
  **Azure Blue is a database roster value for that story and takes no
  `other:` prefix at all.** The second is new: check singletons not just
  against each other but against the ROSTER. Both were normalised before
  mirroring, so paddleocr never saw them. Grep the `other:` counts every time,
  and do it BEFORE the mirror.
- **AN ADDED GROUP IS SOMETIMES APPENDED AND SOMETIMES INSERTED, IN THE SAME
  REVIEW.** Golden Helmet gained three: 115 g9 and 119 g16 were APPENDED as
  the page's last id and stranded nobody, while 125 g10 was INSERTED and
  shifted every id from 10 up by one -- leaving 125 g17, the page's tail,
  unreviewed on both engines. Nothing was destroyed (17 texts in, 18 out,
  none lost), but the straggler is real. **After any add, check both: count
  `speaker_reviewed` per engine, and diff id -> ai_text rather than the id
  set.** Houseboat added nothing and still left 150 g4 unreviewed, so a
  straggler does not require an insertion to explain it.
- **A BACKGROUND LABEL MISSING FROM `visible_text` IS INVISIBLE TO THE AUDIT,
  AND THE REVIEWER FOUND ONE THE PASS NEVER SAW.** 119 g16 is an `ATLAS`
  label in panel 7 that the pass did not record; because it never reached
  that page's `visible_text`, the missed-text audit reported the page clean.
  Same root cause as the previous batch's prison number. **Sweep every panel
  for lettering before writing the capture, not just the panels that look
  like they have signs in them.**
- **THREE QUEUED MISSED-TEXT ITEMS WERE NOT ADDED AND ARE STILL OPEN.**
  Golden Helmet 118 `SEC 1` (wall plate, truncated by the panel border) and
  122 `33` (warship hull number); Houseboat 152 panel 8, the grawlix cursing
  balloon whose caption says the comments cannot be printed. A finding the
  reviewer decides against still needs their word before it can go in
  `missed-text-ignore.txt`, so these are carried, not dropped.
- **ALL THREE MISSED-TEXT ITEMS WERE THEN GROUPED, AND THE CLOSE-OUT IS GREEN.**
  118 `SEC` was APPENDED as the page's last id and shifted nothing; 122 `33`
  was INSERTED in reading order and shifted g8-g11 up by one; 152's grawlix
  balloon was APPENDED as the new last id on both engines. Both titles now
  pass every gating check, with the missed-text audit clean in all three
  classes.
- **HOW TO GROUP A BALLOON THAT HAS NO LETTERS IN IT.** The corpus already
  holds **815 symbol-only groups** across 280 distinct strings, so there is a
  settled convention and it does not need inventing: **the literal glyphs in
  `ai_text`, space-separated, `\n` for a line break.** Precedents: `? ?`,
  `! ? !`, `$ $ $`, `♪`/`♫`/`🎵`, and the closest analogue for a multi-glyph
  device, Vol. 24 180 g7 `'$ # $ #\n# $ # $'`. Non-ASCII is fine -- the file
  is `ensure_ascii`, so it stores as `\u` escapes and round-trips.
  A grawlix is SPEECH, not a device: Houseboat 152's caption says *"his
  comments cannot be printed here"*, so the balloon IS the comments --
  `type: dialogue`, speaker Donald, `off-panel` because he is inside the
  barrel. Contrast the bare `?`, which is a device and takes the type it is
  drawn as. And append it as the page's new LAST id rather than routing it
  through `vision_apply`'s `added_groups`, which renumbers before the
  annotations land.
- **DO NOT VERIFY A MIRROR BY GROUP ID -- IT MANUFACTURES PHANTOMS.** After
  the final mirror an id-keyed check reported six field mismatches on Golden
  Helmet 122 g5/g6. Nothing was wrong: the editor had re-sorted easyocr's
  panel 5 into reading order and paddleocr kept the old order, so the same
  two groups sit on swapped ids with correct values on both. **Keyed on
  normalised `ai_text` -- the way apply and mirror actually match -- there
  were zero mismatches.** The tell is distributions that are identical while
  per-id fields disagree in mirrored pairs.
- **A STROKE CUT BY THE PANEL BORDER IS NOT A CHARACTER.** The pass wrote
  `SEC 1` into 118's `visible_text`; the review grouped it as `SEC`, and the
  audit's third class -- *nearly a grouped text* -- caught the disagreement.
  Re-cropped at 8x, the plate reads SEC followed by a partial vertical stroke
  running into the border, so the group was right and the capture had
  overclaimed. **Transcribe what is fully legible and let the audit find the
  rest**; that class exists precisely for this and it earned its keep here.


### Findings to paste into the next run (2026-09-05, thirty-first batch, Gemstone Hunters reviewed)

*Gemstone Hunters*, Vol. 11, reviewed and mirrored. The mirror is clean:
126 groups both engines, 125 reviewed, 114 with `identified_by`, identical
speaker / cap_colour / confidence distributions, and **zero** per-group field
mismatches keyed on normalised `ai_text`.

```
Gemstone Hunters   5 of 125   4.0%    nephew domain 4 of 29 (13.8%)
   3 one nephew -> another, 1 nephew -> Donald, 1 the added group's default
   0 type corrections; 1 text correction still outstanding (158 g9)
   confidence gave no signal -- the pass wrote 125 of 125 high
```

- **THE FOUR SPEAKER CORRECTIONS ARE ALL TAIL-READING, AND NOT ONE OF THEM IS A
  COLOUR ERROR.** Every cap hex the pass recorded was right; the reviewer
  changed `cap_colour` only because the speaker changed, and each new colour is
  a band the pass had already measured in that same panel. The colour census is
  sound. What failed is where the tail was said to land.
- **NEVER QUOTE A TIP COORDINATE READ OFF A `stack.py` COMPOSITE.** Two of the
  four (158 g4 Dewey -> Huey, 160 g6 Huey -> Louie) came from converting a
  position in a *stacked* image back to panel pixels by guessing the per-crop
  y-offset the stack had introduced. Re-measured on single `pcrop.py` crops:
  158's tip is at about (309,296), on the red band, against the `(226,282)`
  the note claimed -- 80px out. 160's is at about (339,277), on the green
  band, against the claimed `(395,235)` -- 55px out. **The errors have no
  direction**; they are conversion noise, and they are worse than no number
  because `(226,282)` reads as measurement and promoted both calls to high.
  Measure a tip only on a crop whose origin you passed to `pcrop.py`, or quote
  no number at all.
- **A `head+beak x=(...)` SPAN CAN BE TWO BOYS MERGED, AND USING IT WIDENS ONE
  BOY BY A WHOLE NEIGHBOUR.** 163 g9 (Louie -> Huey) cited "inside the green
  boy's head span 120-370". heads.py had merged two touching heads into that
  one span: the green boy actually stops near x=227 and the red boy's cap
  begins at 268, and the tip at 264 is on the red cap, 4px in. **Cross-check
  any head span against the per-boy cap-ink boxes before quoting it** -- those
  are never merged. In a three-boy close-up a span wider than about 150px is
  the tell.
- **READ WHICH WAY THE SPUR POINTS, NOT WHICH SIDE OF THE BALLOON IT HANGS
  FROM.** 156 g1 (Louie -> Donald) was given to the green-capped boy because
  "the tail comes down the balloon's right side onto him". The spur is on the
  balloon's right and points down-LEFT: its tip sits at about (439,555), 21px
  off Donald's head and 54px off the boy's, and the direction settles it for
  Donald. This is [[feedback_tip_in_a_gap_use_the_direction]] missed for the
  third time; the position of a tail's ROOT says nothing.
- **A PAGE WITH NO `visible_text` IS A PAGE THE MISSED-TEXT AUDIT NEVER
  SWEEPS.** The audit reported this title clean in all three classes, and the
  review then added a group the pass had missed: the `313` licence plate on
  158 panel 2. The audit could not see it because 158's capture carried no
  `visible_text` at all -- it swept 6 of 10 pages, and 155, 156, 158 and 163
  were skipped for the same reason. The pass had recorded the very same plate
  on 160 g3, on the very same car. **Fill `visible_text` on every page, or the
  audit's "clean" means only "not checked".**
- **THE ADD WAS INSERTED, NOT APPENDED, AND COST ONE STRAGGLER AND ONE STALE
  QUEUE ENTRY.** `313` went in at 158 g2 on both engines and shifted every
  later id up by one. The page's last group, now 158 g11, fell off the end of
  a queue built before the insert and is the title's only unreviewed group; and
  the outstanding text correction moved from g8 to g9, so the corrections queue
  had to be regenerated before it would address the right group. **After any
  add: regenerate every queue that still has entries on that page.**
- **`review_findings --since` REPORTED A TYPE CORRECTION THAT PREDATES THE
  BATCH BY THREE WEEKS.** 163 g3 `sound_effect -> dialogue` carries
  `type_reviewed_date: 2026-08-12`. The real count for this batch is zero.
  Check the date on every `type_was` before believing the tool's total.


### Findings to paste into the next run (2026-09-05, thirty-first batch, second title)

*The Gilded Man*, Vol. 11, 32 pages, reviewed and mirrored. Mirror clean: 391
groups both engines, 390 reviewed, 352 with `identified_by`, 126 carrying
emphasis, zero per-group field mismatches keyed on normalised `ai_text`.

```
The Gilded Man   25 of 389   6.4%    nephew domain 22 (of 110, 20%)
   11 nephews -> a name      5 one nephew -> another
    3 Donald -> a nephew     3 a nephew -> Donald     3 an other: role
   high 25/435 (5.7%)   medium 2/8 (25.0%)   4 type corrections
```

- **UNDER-NAMING IS AGAIN THE LARGEST CLASS: 11 OF 25.** Second batch running.
  Nothing new in the rule; what is new is the evidence about *why* the pass
  cannot close the gap — below.
- **THE QUERY IS ANSWERED, AND THE ANSWER IS THAT THE PASS WAS WRONG.** This
  section first claimed the reviewer was colouring crowns that print nothing.
  GLK, 2026-09-05: *"I try as hard as I can to identify the nephews using
  color and in the cases you miss I usually find a very tiny color
  identifier."* Checked against the three cases the claim rested on, and the
  claim does not survive:
  * **180 p3** (Huey/red) — the note called the crown's only red "the
    branch's `#a23f21` bark". Probed tight, the mark on the crown is 88px of
    `#b23521` at **S0.81**, and the branch probed away from the head carries
    **no red at all**. A clean cap band, found by the pass's own census and
    then argued away as scenery.
  * **190 p7** (Louie/green) and **186 p6** (Huey/red) — the identifier is a
    wedge of a few dozen pixels at about **S0.08** on a black cap. `capscan`
    reports nothing even with `MIN_SAT` dropped to 0.05 and `probe` calls it
    grey; at 3.2x it is plainly a coloured wedge. **The tooling cannot see
    these at any setting. The eye at 3x can.**
- **SO: CROP THE CROWN AT 3x AND LOOK BEFORE YOU DECLINE.** The census is a
  screen, not a verdict — `capscan.py` says so in its own docstring and this
  is what it means. One stacked image covers three boys and it is the
  difference between eleven corrections and none. And never call a chromatic
  blob on a crown scenery without probing the scenery: if the branch has no
  red in it, the red is not the branch.
- **DO NOT GOLD-PLATE IT.** GLK, same message: *"The whole nephew
  identification is hard and I'm happy to continue with your best effort with
  my reviews being the final arbiter."* One look at the crown is the cost, not
  five. `feedback_cost_per_page_beats_accuracy` still stands.
- **THE ONE CORRECTION CARRYING A REVIEWER NOTE IS THE OTHER MECHANISM.** 174
  g0 — *"Huey had the castor oil from last panel"* — names from scene
  continuity, and it is the one under-naming where `cap_colour` was correctly
  left **null**. Colour when you can see colour; continuity names the boy but
  leaves the field empty.
- **AN IDIOM IS NOT A VOICE-PRINT, AND THE PILOT PAIR WAS EXACTLY INVERTED.**
  The pass gave the charter pilot 176 g8 (*"QUITE A COLORFUL ERRAND, ME
  HEARTIES!"*) because that is how the pilot talks on 177 g8, and gave Donald
  177 g2 (*"THE SAVANNAHS!"*). Both are backwards: ME HEARTIES is Donald doing
  a nautical turn, and the pilot's own line is the flat geographical answer.
  These were the pass's only two mediums and both were corrected -- the flag
  worked because the uncertainty was real and the note said the drawing did
  not say. **Medium 2 of 8 against high 25 of 435: 4.4x. A medium written for
  a reason still earns its place.**
- **A BOX IN CAPTION COLOURS CAN BE A SIGN.** 173 g3, *YES, WE HAVE NO MAGENTA
  STAMPS!*, was recorded `narration` because it is a pink box in the same
  colour the page uses for MEANWHILE!. The review retyped it `background`: at
  1.7x it is squared to the post office wall with the wall colour showing
  round it and its own black border, and it has no drop capital, which every
  real caption on these pages does. **Test a caption by its drop capital and
  by whether it sits flush in a panel corner, not by its fill colour.**
  Note the review left `speaker: narrator` and `identified_by: ['caption']` on
  it -- the only type/speaker inconsistency in 517 groups across both titles,
  and handed back rather than changed here.
- **A DIVIDED BALLOON'S RULE IS LETTERING.** 195 g6 came back with a line of
  16 dashes inside its `ai_text`. It is not corruption: the balloon really is
  divided by a drawn dashed rule between *IT'S UNCA DONALD!* and *HE'S OUT AT
  THE CITY LIMITS!*. Check the art before "fixing" a stray-looking run of
  punctuation; the corpus's only other long dash runs are trailing ones for an
  interrupted line.
- **AN APPENDED ADD STRANDS NOBODY; AN INSERTED ONE STRANDS EXACTLY ONE.** Same
  reviewer, same sitting: Gemstone's `313` was *inserted* at 158 g2 and pushed
  the page's tail off a queue built before it, while this title's two adds --
  `313` at 189 g15 and the bare `!` at 195 g10 -- were *appended* as the new
  highest id and shifted nothing. Both were on both engines and both were free
  of copy-in residue (`ocr_text` and `notes` empty, `speaker_was: unknown`).
  **Diff the id set, not the count, to tell which kind you have.**
- **THE STRAGGLER WAS NOT THE PAGE TAIL THIS TIME.** 195 g3 (`STAMP ALBUM`,
  background, speaker `none`) is the group immediately *before* the appended
  one. Do not assume the unreviewed group is the last id.
- **AN IGNORE-FILE LINE MUST MATCH `visible_text` VERBATIM, NOT DESCRIBE IT.**
  The first attempt at declining 169's music notes wrote a full description
  into `missed-text-ignore.txt` while `visible_text` held the two words
  `musical notes`; the audit went on reporting it, because both sides are
  normalised to letters and digits and the two strings no longer agreed. They
  have to be the same string. And 195's `!` cleared only once `visible_text`
  went back from the prose to the bare glyph, which is
  [[project_devices_must_go_in_visible_text]] working exactly as recorded.


### Findings to paste into the next run (2026-09-06, thirty-second batch, Spending Money reviewed)

*Spending Money*, Vol. 11, 10 pages, reviewed and mirrored. Mirror clean: 139
groups both engines, 139 reviewed, 119 with `identified_by`, 30 carrying
emphasis, identical speaker / cap_colour / confidence distributions and **zero**
per-group field mismatches keyed on normalised `ai_text`.

```
Spending Money   1 of 139   0.7%    nephew domain 1 of 4 (25.0%)
   1 unknown -> Donald.  0 nephew corrections, 0 cap_colour corrections
   1 type correction (the pass's own proposal, accepted); 1 text correction
   high 0/138 (0.0%)   medium 1/1 (100.0%)
```

- **THE LOWEST CORRECTION RATE ON RECORD, AND IT IS NOT A REASON TO RELAX.** The
  title is a Scrooge-and-Donald two-hander: only 4 of its 139 groups are in the
  nephew domain, which is where every batch's corrections live. Read the 0.7%
  as "this story had almost no nephew work in it", not as "the method got
  better". *Gemstone Hunters* was 4.0% and *The Gilded Man* 6.4% on the same
  volume, and both were nephew-dense.
- **THE ONE CORRECTION WAS THE PASS'S ONLY MEDIUM, AND THE FLAG WORKED
  PERFECTLY.** medium 1 of 1 against high 0 of 138. Third batch running in which
  the mediums are corrected at many times the rate of the highs (*Pixilated
  Parrot* 41.2 vs 6.0, *The Gilded Man* 25.0 vs 5.7, now 100 vs 0). A medium
  written for a stated reason is the single most useful signal this pass emits;
  keep writing them and keep them rare.
- **WHEN THE ART CANNOT PLACE A LINE, THE STORY'S PREMISE CAN, AND `unknown` IS
  ALMOST NEVER THE ANSWER.** 203 g4, *THAT'S THE WAY WE'RE GOING TO EAT FROM NOW
  ON!*, was recorded `unknown` because the balloon's tail stops in open sky about
  40px above the car roof and no occupant is drawn readably. The reviewer made it
  Donald, and -- asked directly whether that came from the geometry or the story
  -- answered **from the story**: GLK, 2026-09-06, *"the dialogue fitted with
  Donald being in charge of spending money."* So the rule is NOT "the tip lands
  over the cabin, so it is whoever is at the wheel"; the first draft of this
  section guessed that and it was wrong.
  What the line actually is, is a **decision about the arrangement**, and this
  story has installed exactly one character with the authority to make it --
  Donald is hired on 200 to do the spending and does every choosing from there.
  The pass's note floated "register suggests a nephew", reading the enthusiasm
  as childlike; it is a declaration of policy, not delight.
  This does NOT reinstate role reasoning in general --
  [[feedback-role-reasoning-loses-on-wide-shots]] still stands, and "who would
  say this" cost two Donalds that were the boys. The difference is what is being
  reasoned from: a *premise the story has established on the page* places a
  line, a *guess about who is the sort of person to say it* does not. Where the
  art is silent, ask which character the story has put in charge of the thing
  the line decides, and only fall back to `unknown` when nothing has been
  established.
- **A REVIEW CAN CARRY A TEXT CORRECTION THAT NO QUEUE EVER REPORTS.** 206 g11
  came back `$ McDUCK BLDG $` -> `McDUCK BLDG`, edited straight into `ai_text`
  on both engines. `vision-corrections` says "nothing outstanding" for it,
  because a correction typed directly is already applied and was never a
  proposal. **Diff `ai_text` per engine against the pass's own commit after
  every review** -- that is the only thing that surfaces these, and it is the
  same per-engine `ai_text` diff that catches an added group corrupting
  easyocr.
- **A DOLLAR SIGN ON A MEDALLION IS ARCHITECTURE, NOT LETTERING.** That is what
  the retype was about. At 4x the McDuck Building sign is a lettered panel
  reading `McDUCK BLDG`, with a dollar emblem on a disc at each end **outside**
  the panel and a third worked into the scrollwork above. The pass folded all
  three into the sign's text. Same class as the Vol. 10 014 emblem already in
  `missed-text-ignore.txt`; the page's `visible_text` is corrected and the
  ornament recorded separately. **Test a sign by its lettered panel, not by
  everything inside the group's box.**
- **`review_findings --since` OVER-REPORTED TYPES AGAIN, SECOND BATCH RUNNING.**
  It listed two type corrections; 206 g7 `dialogue -> narration` carries
  `type_reviewed_date: 2026-08-12` and is present in the commit *before* the
  pass. The real count is one -- the pass's own 198 g1 `dialogue -> thought`,
  accepted on both engines. **FIXED 2026-09-06** -- see the next section.
- **BOX CHURN IS NOT A FINDING.** The review moved **45** `text_box` values, 22
  on easyocr and 23 on paddleocr, and the two sets are not the same groups --
  the editor tightens boxes per engine. Largest corner displacement 157px on a
  balloon several hundred px wide, and only one of the 45 came with a text
  change. Measure the displacement before reading a moved box as a relocation
  onto different lettering.
- **THE COLLECTIVES ALL STOOD.** Two `nephews`, one `other:Scrooge and the
  nephews` (a four-tail balloon) and both named nephews (205 g17 Dewey by a
  60px blue chip, g18 Huey by a red one) were accepted unchanged, as were all
  eight `other:` roles. Under-naming has been the dominant error class for two
  batches; it did not appear here, and the four-tail chorus and the tiny-chip
  cap readings are both confirmed good.
- **The missed-text item is still open.** 205's illegible roadside billboard was
  queued and the review did not rule on it, so it is deliberately still out of
  `missed-text-ignore.txt` and the audit still reports the title dirty.


### Findings to paste into the next run (2026-09-06, thirty-second batch, second title)

*The Hypno-Gun*, Vol. 13, 10 pages, reviewed and mirrored. Mirror clean: 125
groups both engines, 125 reviewed, 114 with `identified_by`, 36 carrying
emphasis, identical distributions and **zero** per-group field mismatches keyed
on normalised `ai_text`. No text corrections, and no type corrections.

```
The Hypno-Gun   2 of 125   1.6%    nephew domain 2 of 16 (12.5%)
   057 g12 nephews -> Donald,  057 g14 Huey -> Donald (cap red -> null)
   high 0/123 (0.0%)   medium 2/2 (100.0%)
```

- **BOTH CORRECTIONS WERE THE PASS'S ONLY TWO MEDIUMS, AGAIN.** Second title
  running in this batch where every medium was corrected and no high was:
  Spending Money 1/1 against 0/138, this 2/2 against 0/123. Across the batch
  that is **3 of 3 mediums and 0 of 261 highs**. The flag is now the most
  reliable thing the pass produces — but note what it means: a medium is not
  "probably right", it is "probably wrong". Write one only where the call would
  genuinely go either way, and expect the reviewer to overturn it.
- **BOTH CORRECTIONS ARE ONE MISREAD PRONOUN.** 057 g10-g14 are a **single
  Donald monologue** and every "HE" in it is *Scrooge*: he reports Scrooge's
  account (*FROM UNCLE SCROOGE! / HE GAVE IT TO ME AS A REWARD...*), undercuts
  it (*SO HE SAYS! / BUT HE ISN'T FOOLING ME! HE MUST HAVE DREAMED THAT...*)
  and closes with the moral (*WHICH JUST GOES TO SHOW WHAT THAT THING WILL DO
  TO SOMEBODY WITH A GULLIBLE MIND!*). The pass read the "HE" in g12 as Donald,
  concluded a nephew must be doubting him, and then handed the closing line to
  a nephew as well. **Before assigning a run of balloons in one panel, settle
  who each pronoun refers to and check whether the run is one speaker.** The
  gag only works if Donald says it — he is the gullible one and does not know
  it, and giving the punchline to a nephew destroys it.
- **A CURVING TAIL'S BEND IS NOT ITS TIP.** 057 g14's tail is long and curves:
  it leaves the balloon heading down-left, turns at about (505,168) in panel
  coordinates, and then runs down-RIGHT to end on Donald's head at about
  (626,293), just left of his blue cap. The pass quoted **(504,212)** as "the
  tip", which is that bend, then matched the false tip's x against the cap
  columns below and named the red-capped boy. Two compounding errors: stopping
  at the first direction change, and then treating an x-coordinate over a cap
  as evidence across a 275px vertical gap — which the note itself flagged as
  the reason for the medium. **Follow a tail to where the line stops, not to
  where it changes direction**, and if a quoted tip needs a 275px extrapolation
  to reach anybody, it is not a measurement.
- **IN BOTH CASES THE TAIL WAS RIGHT AND THE READING OF THE WORDS WAS WRONG.**
  g12's tail landed on Donald and the pass argued it away on content grounds;
  g14's content pointed at a nephew and a mis-traced tail agreed. So the error
  class here is not tracing at all — it is the story reading overruling, or
  corrupting, a correct trace. Compare the other title in this batch, where the
  story reading was what the reviewer used. **The words place a line the art
  leaves open; they do not overrule a tail that lands.**
- **`review_findings --since` OVER-REPORTED TYPES FOR THE THIRD BATCH RUNNING,
  AND THIS TIME IT TURNED 0 INTO 4.** It listed 048 g0, 051 g3, 052 g3 and
  055 g5; all four carry `type_reviewed_date: 2026-08-13` and all four are
  present in the commit *before* the pass. The real count is **zero**.
  **FIXED the same day.** `review_findings.py` now gates the type list on
  `--since` as well: a row counts only when the group was NOT already
  `type_reviewed` in that commit's blob, which keeps a pass's own proposal that
  the review then confirmed and drops the rest into a separate
  `type_was PREDATING <ref>` block with each date shown. Checked against four
  hand-verified counts -- Gemstone Hunters 0 real / 1 stale, Spending Money
  1 / 1, The Gilded Man 4 / 5, The Hypno-Gun 0 / 4.
  **So: pass `--since` and read the headline number. Without `--since` the
  distinction cannot be drawn and the type list is still every group carrying
  the field -- the report now says so, but it cannot fix it.**
- **THE CAP PALETTE THIS TITLE PRODUCED NAMED NOBODY IN IT.** The title now
  carries **no `cap_colour` at all** — the one value the pass wrote was cleared
  with g14. The boys are bare-headed on 048 and 049, and 057, the only page
  that prints caps, ended up with no nephew speaker. All three surviving nephew
  names (Huey 7 groups, Louie 1, Dewey 1) come from the direct-address chain on
  048, and every one stood. The palette derived from 057 p5 and p8 is still
  worth having for the volume, but record honestly that it decided nothing
  here.
- **The 056 impact stars are still open** — a drawn device carrying no
  characters, queued and not ruled on, so still out of `missed-text-ignore.txt`.


### Findings to paste into the next run (2026-09-06, thirty-third batch, all three titles reviewed)

*Trick or Treat* (32pp, 329 groups), *Hobblin' Goblins* (9pp, 115) and
*Omelet* (10pp, 163), all read and all reviewed the same day, all mirrored.

```
                    real corrections        mediums      highs
Trick or Treat      13 of 329   4.0%        3 of 4       10 of 325  3.1%
Hobblin' Goblins     8 of 115   7.0%        0 of 2        8 of 113  7.1%
Omelet               5 of 163   3.1%        0 of 2        5 of 161  3.1%
   batch            26 of 607   4.3%        3 of 8       23 of 599  3.8%
```

- **COUNT BY TEXT, NOT BY ID, ON ANY TITLE WHOSE REVIEW ADDED A GROUP.**
  `review_findings --since` reported 15 / 10 / 8; the true counts are
  **13 / 8 / 5**. Every one of the seven surplus rows is an `unknown -> none`
  on an id that an insertion moved -- the tool compares old id N against the
  newly inserted group. Re-match on (normalised `ai_text`, occurrence). Across
  the batch the tool over-reported by 39%, and it over-reported most on the
  title with fewest real corrections. [[project_review_adds_shift_ids_and_strand_a_group]]
- **OVER-NAMING WAS HALF OF ALL CORRECTIONS -- 13 OF 26 -- AND IT IS NOT A
  COSTUME-TITLE EFFECT.** 7 on *Trick or Treat*, 3 on *Hobblin' Goblins*,
  3 on *Omelet*; the last six are on titles where the boys wear ordinary caps
  and I had a hex on a head. This reverses the standing under-naming rule for
  this kind of panel, and the boundary is the same one all three reviews drew:
    - **a set of balloons with one tail each names them all** -- three-tail
      chorus balloons, cascades, `NOT ME!` pairs, the silhouette fans. Not one
      of these was touched in 607 groups.
    - **a single balloon over a bunched trio is `nephews`**, even with a
      measured tip and a clean cap under it. 039 g5, 043 g9, 046 g9, 058 g6,
      065 g5, 065 g7 all had both and all came back collective.
  So the tail names a boy when the panel's other balloons have already claimed
  the other two. On its own, against three heads in a bunch, it does not.
- **THE MEDIUM FLAG WENT 3 OF 8 THIS BATCH, NOT 3 OF 3.** Still 10x the high
  rate (37.5% against 3.8%), and all three that fell were on the same title --
  but the four-batch run of "every medium is wrong" is over. Read it as: a
  medium is a request for a second pair of eyes, not a prediction. Keep
  writing them, keep writing what the other reading is; the three that were
  corrected were all corrected *to the alternative the note named*.
- **A COLOURIST ERROR, CALLED BY THE REVIEWER IN SO MANY WORDS.**
  *Hobblin' Goblins* 045 g3, `Dewey -> Huey`, reviewer's note *"Colorist error:
  should be red cap"*. I had sampled `#429aae` H191.1 S0.62 and read it as a
  shaded blue, which it is -- the cap is simply printed the wrong colour.
  [[feedback_colourist_error_breaks_the_chain]] again: record the printed ink,
  take the name from everything else.
- **A CAPSCAN ZERO IS NOT PROOF OF NO CAP.** 045 g4, `nephews -> Louie`,
  reviewer's note *"Can just see green"*. I declined because capscan returned
  red 0 and leafgrn 0 at an 8px floor and wrote that only one of the three
  carried readable ink. The green was visible in the crop I already had. The
  census screens; the crop decides.
- **AN ADULT WHOSE HEAD ABUTS THE BALLOON IS A LIVE CANDIDATE.**
  *Hobblin' Goblins* 040 g5, `nephews -> Gyro`. My note explicitly ruled him
  out -- "not on Gyro, who is at x 620-940 with the balloon merely abutting his
  cap" -- and the line is *THE GOBLINS WILL BE HEXED!*, in his own coinage two
  pages after he says *hex-rays*. Where a balloon runs up against an adult's
  head and the diction is his, abutting is not the same as unrelated.
- **A SECOND COPY OF AN ALREADY-GROUPED STRING IS INVISIBLE TO THE AUDIT, AND
  IT HAPPENED TWICE.** Both reviews found lettering the missed-text audit could
  not: a second `RAY SHAPER` tag (*Hobblin' Goblins* 039, panel 2, distinct
  from the panel-1 one) and a second `313` number plate (*Omelet* 058, panel 7,
  distinct from the panel-1 one). Both were in `visible_text` -- once -- so the
  diff matched them against the existing group and reported nothing.
  [[project_vision_audit_nearmiss_gap]] confirmed twice in one batch.
  **Fix: when the same lettering appears more than once on a page, record it
  once per occurrence in `visible_text`, not once per string.**
- **A ROLE VALUE CAN BE SHARPENED.** *Omelet* 064 g11,
  `other:a townswoman -> other:the baker's wife`. Using a generic
  `other:a townsman` / `other:a townswoman` for a crowd of extras kept the
  namespace clean across 23 uses and no near-duplicates drifted, which was the
  right call -- but where a figure has an actual role in the scene, name the
  role.
- **CLOSED.** All three titles finished at 613 groups across 51 pages, every
  group reviewed on both engines, zero per-group mismatches on any mirrored
  field. Two stragglers had to be chased first, both created by an insertion:
  *Hobblin' Goblins* 039 g15 (stranded when `RAY SHAPER` went in at g7) and
  *Omelet* 065 g14. **Count `speaker_reviewed` on BOTH engines before calling a
  review done** -- neither straggler was visible from the correction list, and
  the type corrections are a separate review state again: *Trick or Treat* sat
  at 330/330 speakers with 017 g6 and 033 g8 still unconfirmed for two rounds.
  With them in, `vision-corrections` with no `--title` reports *Nothing
  outstanding across 460 title(s)*.

### Findings to paste into the next run (2026-09-06, thirty-fourth batch, first title reviewed)

*A Charitable Chore* (10pp, 152 groups) read, reviewed and mirrored.
*Turkey with All the Schemings* (10pp, 152) and *Flip Decision* (10pp, 154)
are read and applied, review in progress.

```
                        real corrections      mediums      highs
A Charitable Chore      1 of 152   0.7%       0 of 5       1 of 147  0.7%
```

- **COUNT BY TEXT AGAIN: `review_findings` said 2, the real figure is 1.** The
  second row, 074 g13 `unknown -> none`, is the group the REVIEW added -- its
  `speaker_was` defaults to `unknown`, so it books as a correction of a call the
  pass never made. Subtract every added group before quoting a rate.
  [[project_review_adds_shift_ids_and_strand_a_group]] once more, in its milder
  form: this insertion appended at g13 and renumbered nothing, so no straggler
  was created and both engines finished at 153/153.
- **THE ONE ERROR WAS A CAP GREEN SHADED BELOW EVERY CENSUS FLOOR, AND THE HUE
  WAS RIGHT ALL ALONG.** 071 g10, `nephews -> Louie`, `cap_colour null ->
  green`. My note said "that cap is solid black: capscan at an 8px floor puts no
  red, blue or leafgrn blob anywhere on his head". The ink is there: **516px at
  `#627360` H113.7**, dead inside the Vol. 13 cap-green band (H103-132), printed
  over a black crown at **S0.12-0.27**. `capscan` and `capwide` both carry
  `MIN_SAT = 0.40`, so both return `green: 0` for that panel at any area floor,
  and `capwide`'s widened bands do not help because the miss is in saturation,
  not hue. So:
    - **A shaded gore falls BELOW the cap band, not between the cap and the
      foliage band.** The Vol. 13 rule "caps sit at S0.4-0.6 and foliage at
      S0.94-1.00" screens foliage OUT; it does not put a floor under a cap.
    - **`probe.py` had already printed it and I read the wrong column.** Its row
      was `green 516px #627360 H113.7 S 0.12/0.17/0.27`. On a black crown the
      HUE column decides. Never write "no cap ink" off a blob census -- probe the
      crown and read the hue.
    - **Probe the CROWN STRIP, not the skull.** My box was `(14,234)-(150,380)`,
      which is the white skull `heads.py` reports; the cap sits ABOVE it and the
      gore was at y<234. [[feedback_ink_above_the_white_skull_is_the_cap]].
  This same error was then made at scale on *Flip Decision* -- a 30px area floor
  hid gores of 60-250px on four pages -- and caught mid-title only by cropping.
- **THE MEDIUM FLAG WENT 0 OF 5, AND ALL FIVE WERE PROMOTED UNCHANGED.** Second
  batch running that it has caught nothing (3 of 8 last time, 0 of 5 now)
  against 1 of 147 highs. The four-batch run where every medium was wrong is
  well and truly over: read a medium as a request for a second look, not as a
  prediction, and keep writing what the alternative reading is -- that is what
  makes it cheap for the reviewer to promote.
- **THE OFFSET-FAN READING HELD, ON A VOL. 13 TITLE.** 071 panel 5: three
  balloons over three boys, every tip 60-130px LEFT of the boy reading order
  gives it, the leftmost landing on open pavement. I assigned by the uniform
  drift rather than by nearest head, flagged all three medium, and the review
  promoted all three unchanged. [[project_offset_fan_reading_order_wins]] is now
  confirmed outside Vol. 4. A tip landing on NOBODY is the signal; when it fires,
  the whole fan has moved and reading order wins.
- **TWO RETYPES I DECLINED AS "STYLE" WERE MADE ANYWAY.** 068 g14 `BYE!` ->
  `'BYE!` and 075 g8 `So-` -> `SO —`, both typed straight into `ai_text` in the
  editor and both applied to BOTH engines. So, for this corpus:
    - **an elision apostrophe is transcribed**, not style;
    - **a drop-capital caption is normalised to caps with an em-dash** -- `SO —`,
      the form 069 g0 already carried, not the drawn mixed case `So-`.
  Neither reached `vision-corrections`, because a retype is already applied
  [[project_review_retype_reaches_no_queue]]; they were found by diffing
  `ai_text` against the pass commit, which is the only way to see them.
- **QUEUEING AN AUDIT-INVISIBLE DUPLICATE WORKS.** The `$98` tag on 074 panel 5
  is a second copy of a string that already has a group, so
  `audit_missed_text.py` matched it against the `$98.00` display card and
  reported nothing. It reached the reviewer only because it went into
  `queue-missed.txt` by hand with a line saying the audit could not see it, and
  it came back as a properly boxed group. Keep writing those rows.
- **THE ADDED GROUP CARRIED NO SEED RESIDUE.** 074 g13 arrived with its own box,
  `ai_text` `$98`, `type` `background`, `speaker` `none`, `vision_added: true`,
  and no `vision_note`, `identified_by` or `acknowledged_issues` copied from a
  neighbour -- so [[project_editor_copy_in_residue]] did not fire this time.
  Still check it: the check is two lines and the failure is silent.
- **CLOSED.** 153 groups on 10 pages, 153 `speaker_reviewed` and 128
  `identified_by` on both engines, identical speaker / `cap_colour` / confidence
  distributions, zero per-group mismatches, and `vision-corrections --title`
  reports nothing outstanding.

### Findings to paste into the next run (2026-09-06, thirty-fourth batch, second title)

*Turkey with All the Schemings* (10pp, 152 groups read) reviewed and mirrored.
The review ADDED 8 groups, taking the title to 160.

```
                            real corrections      mediums      highs
A Charitable Chore          1 of 152   0.7%       0 of 5       1 of 147  0.7%
Turkey with All the Sch.    3 of 152   2.0%       1 of 2       2 of 150  1.3%
```

- **`review_findings` said 11 at 6.9%; the truth is 3 at 2.0%.** Eight of its
  rows are the eight groups the review added, every one an `unknown -> X` on a
  `speaker_was` default. On a title with adds the tool's headline is unusable —
  subtract them, and do it by matching stripped `ai_text` and occurrence, not by
  id. [[project_review_adds_shift_ids_and_strand_a_group]].
- **A DRAWN DEVICE OVER A CHARACTER IS A `thought` GROUP WITH THAT CHARACTER AS
  ITS SPEAKER.** Four of the eight adds: `$ $ $` -> **Scrooge, thought** on 082
  and 083, `$ $ $ $ $ $ $ $` -> **Scrooge, thought** on 084, and `!` ->
  **Donald, thought** on 083. I had put all four into `visible_text` as prose
  ("drawn dollar signs floating around Scrooge's head") and described them as
  background lettering. Recording them is what got them boxed — keep doing that
  — but **describe them as the thought of the figure they hang over**, because
  that is what they become. The roster already says so for a `?`
  ("A DRAWN DEVICE OVER ONE FIGURE NAMES THAT FIGURE"); it applies to floating
  `$` clusters and bare exclamation marks too. Only lettering that is genuinely
  in the scene — the `R` monogram, `TELEPHONE`, `600`, `$9.73` — came back
  `background` / `none`.
- **THE ARROW LABEL IS `narration`, NOT `background`.** 082 g4 `WASHERS`,
  `none/background -> narrator/narration` with `identified_by: ["caption"]`. I
  had flagged in the close-out that the corpus stored this device inconsistently
  (`WASHERS` as background, `TAILS` on 096 g9 as narration) and declined to pick;
  the review picked. **An author's arrow label pointing into the art is the
  narrator.** Type it `narration`, speaker `narrator`, `identified_by`
  `["caption"]`.
- **WHEN BALLOONS CANNOT BE PAIRED TO TAILS, NO BALLOON IN THE STACK IS
  NAMEABLE — INCLUDING THE ONE WHOSE TAIL YOU CAN TRACE.** 079 panel 2, the
  three-balloon cascade: `Huey -> nephews` and `Louie -> nephews`, both
  `cap_colour` nulled. The gores were real and correctly measured (`#e51b20` on
  the left boy, `#4ea240` H111.4 S0.60 on the middle) and I traced all three
  TIPS to all three boys. What I could not do was say which BALLOON owned which
  tail: two of the three emerged from under g4's bottom edge, so one of them was
  g1's, drawn behind the stack. I wrote exactly that into the note and then
  named the one balloon whose tail left its own edge — **at high**. That is the
  call that was reversed. Tracing a tail to a boy tells you a boy is speaking;
  it does not tell you WHICH BALLOON he is speaking, and the words are the whole
  point. Three balloons, three tails, unresolved ownership: `nephews` x3.
  Note the confidence was inverted too — the `high` was wrong and one of the
  two `medium`s was right.
- **DO NOT LET A PROP'S SEMANTICS DRIVE A TRANSCRIPTION.** I queued the 081
  greasepaint jar as `GOO` off a 5x crop, reasoning that a costume trunk would
  hold goo; the reviewer typed `600`, and at **7x** the first glyph is plainly a
  6 — a curved stroke into a closed lower loop with **no horizontal crossbar**,
  where this hand's capital G has one. 5x was not enough for a three-character
  label. The roster's "crop and upscale before proposing a correction" covers
  what the lettering *looks* like; extend it to what the prop *ought* to say.
- **`review_findings --since` TRANSPOSED TWO IDS ON A RENUMBERED PAGE.** It
  listed 086 g17 `dialogue -> thought` as a current type correction and 086 g15
  `sound_effect -> dialogue` as PREDATING. On disk it is the other way round:
  g15 is `ZZZ`, corrected today, and g17 is `SUFFERING SAWFISH`, adjudicated
  2026-08-13. The counts were right and only the ids crossed. On any title whose
  review renumbered, **check the type lists by text**.
  Same class as [[project_queue_ids_go_stale_on_renumber]].
- **THE INSERTS RENUMBERED FOUR PAGES AND COST NOTHING.** 082, 083, 084 and 086
  were re-sorted into reading order, moving up to 17 ids on one page — and no
  text was lost, no annotation was stranded, and both engines renumbered
  identically. None of the eight added groups carried seed residue
  (`vision_note`, `notes` and `acknowledged_issues` all empty).
  [[project_editor_resorts_and_renumbers]] is still true and still harmless when
  the diff is keyed on text.
- **CLOSED.** 160 groups on 10 pages, 160 `speaker_reviewed` and 132
  `identified_by` on both engines, `cap_colour` null on all 160, zero per-group
  mismatches, nothing outstanding in `vision-corrections`.

### Findings to paste into the next run (2026-09-06, thirty-fourth batch, third title and batch close)

*Flip Decision* (10pp, 154 groups read) reviewed and mirrored; 3 groups added,
title closed at 157. All three titles of the batch are now closed.

```
                            real corrections      mediums      highs
A Charitable Chore          1 of 152   0.7%       0 of 5       1 of 147  0.7%
Turkey with All the Sch.    3 of 152   2.0%       1 of 2       2 of 150  1.3%
Flip Decision               8 of 154   5.2%       0 of 2       8 of 152  5.3%
   batch                   12 of 458   2.6%       1 of 9      11 of 449  2.4%
```

- **ALL EIGHT OF FLIP DECISION'S CORRECTIONS WERE CAP READINGS, AND THE ROOT WAS
  REASONING ABOUT THE PANEL'S PALETTE INSTEAD OF ASKING WHICH BLOB SITS ON A
  HEAD.** Seven `nephews -> a name`, one `Dewey -> Huey`. Two opposite failures,
  one cause:
    - **A decoy in the exact cap ink does not disqualify the band.** This title
      prints a red car at `#e61b1f` and a green fence at `#009e49` — the cap red
      and (near) the cap green. I wrote "its greens are the fence at S1.00, its
      only blue is Donald's cap" and moved on. On 094 panel 7 a **1172px red
      gore at S0.88 was sitting on the leftmost boy's head**, in the same band I
      had just written off. Identify the decoy and then *still* ask which
      remaining blobs land on a head. [[project_cap_blob_must_sit_on_a_head]].
    - **Colour on a cap's OUTLINE is print bleed, not a gore.** 093 g0: I named
      Dewey from ~100px of `#00a4d5` in three slivers at a 5px floor and marked
      it **high**. At 3.4x those flecks sit on the boundary between the black cap
      and the pale-blue sky — bleed at the edge. The reviewer read the boy as
      Huey. A gore sits *inside* the crown, not along the line where it meets
      the background.
  The same census error cost one correction on *A Charitable Chore* (071 g10,
  a gore at S0.12-0.27) and was caught mid-title on this one. Three separate
  shapes of the same mistake in one batch: too low an area floor, too high a
  saturation floor, and a palette argument that skipped the head test.
- **RETRACT "A SINGLE BALLOON OVER A BUNCHED TRIO IS `nephews`".** That was the
  thirty-third batch's rule and I applied it faithfully. The reviewer named
  every instance of it here: 095 g14 and 097 g11/g12 are one balloon over three
  overlapping boys and came back Dewey, Dewey and Louie, each with a
  `cap_colour` set — so a specific gore was read for each. **Bunching is not a
  reason to decline; it is a reason to crop.** What the old rule was really
  about is the *previous* batch's panels, where no gore was readable at all.
  Where the gores print, name them however bunched they are.
- **THE MEDIUM FLAG IS NOT A PREDICTOR ANY MORE.** Across the batch: **1 of 9
  mediums** corrected against **11 of 449 highs**, and every one of the batch's
  error clusters was a `high` — the 079 cascade, the 093 sky-bleed, all seven
  Flip Decision collectives. Two batches ago every medium was wrong; now the
  flag catches almost nothing. Keep writing mediums for the reviewer's benefit,
  but **stop treating a `high` as settled** — that is where the errors live.
- **AN INSERT DISPLACED A GROUP OUT OF THE QUEUE AGAIN.** 097's apartment `1`
  went in at g8 and shifted every later id by one; the panel-7 caption, old g12
  and now g13, never reached the reviewer and the title sat at 156/157. It is
  not always the page's last id — g18 was reviewed and g13 was not.
  **Count `speaker_reviewed` on both engines before mirroring, every time.**
  Chased separately, it came back confirming the pass's `narrator` unchanged.
  [[project_added_group_shifts_queue_tail]].
- **THE CAPTION RETYPE IS A HOUSE CONVENTION, CONFIRMED TWICE.** `So-` -> `SO —`
  on 075 in the first title and again on 097 here, plus `GO?...` -> `GO? ...` on
  089. A drop-capital caption normalises to caps with an em-dash, and an ellipsis
  takes a leading space. None of these reach `vision-corrections` — a retype is
  already applied — so diff `ai_text` against the pass commit or they are
  invisible. [[project_review_retype_reaches_no_queue]].
- **SWITCH `visible_text` BACK TO THE GLYPH THE MOMENT A DEVICE IS GROUPED.**
  At the review-stage close-out *Flip Decision* audited clean while the other
  two still reported findings — every one of *Turkey*'s seven was a device the
  review HAD grouped, still described in `visible_text` as prose ("drawn dollar
  signs floating around Scrooge's head" against a group whose `ai_text` is
  `$ $ $`). The prose form is only for lettering nobody has grouped yet.
  **Re-run the audit after a review, not only before it**, and fix the field to
  match the new groups. [[project_devices_must_go_in_visible_text]] already says
  so; this is the first batch where it cost a failing close-out on two titles.
- **CLOSED.** 470 groups across 30 pages and three titles, every group reviewed
  and mirrored on both engines, zero per-group mismatches anywhere, and
  `vision-corrections` with no `--title` reports *Nothing outstanding across 460
  title(s)*.


### Findings to paste into the next run (2026-09-06, thirty-fifth batch, first title reviewed)

*My Lucky Valentine* (10pp, 130 groups read) reviewed and mirrored; no groups
added or deleted, title closed at 130 on both engines.

```
                            real corrections      mediums      highs
My Lucky Valentine          6 of 130   4.6%       0 of 1       6 of 129  4.7%
   nephew domain            6 of  25  24.0%
```

- **A SCALLOPED BALLOON BOTTOM FAKES A TAIL, AND IT COST FIVE NAMES OUT OF SIX
  CORRECTIONS.** Every over-naming in the title was the same move: the balloon
  bottom is a chain of rounded lobes, the cusp where two lobes meet makes a
  downward point, and over a row of three boys one of those cusps always sits
  above a head. Five times that cusp was written up as a tail and the boy under
  it named; the reviewer sent all five back to `nephews` and cleared
  `cap_colour`. **The tell is in the pass's own prose** -- two of the five notes
  open with *"the balloon's bottom edge is scalloped, but one lobe comes to a
  point"*. The scalloping had been seen and argued past. If you write
  "scalloped, but", stop.
  At 2.6x the two are not close: a real tail reaches well BELOW the outline, is
  much narrower than a lobe, has straight sides converging on one sharp point,
  and stands alone against an evenly spaced run of lobes. A cusp is two curves
  meeting, the same width as its neighbours, and part of the run.
- **BUT DO NOT READ THAT AS "DECLINE THE SCALLOPED ONES".** The sixth correction
  is the opposite error: 106 g6 *does* have a real tail, longer and narrower
  than the lobes, landing on the green-tied boy -- and the pass took a scallop
  two boys to its left and named Dewey. The rule is **find the long narrow spike
  first; only if there is not one is the group `nephews`.** Every call that
  rested on a real tail stood, and so did the offset-fan reading on 107 p6,
  where three balloons over three boys were named from the fan rather than from
  any single lobe.
- **THE HIGH FLAG IS STILL WHERE THE ERRORS LIVE.** 6 of 129 highs corrected
  against 0 of 1 medium -- the third batch running in which the medium flag
  catches nothing and every error cluster is a `high`. All six of these were
  written at high with a pixel margin in the note, which is exactly the
  failure the roster warns about: *a margin quoted against the wrong landmark
  reads as measurement and promotes the call to high*. Here the wrong landmark
  was not a cap instead of a head -- it was a balloon outline instead of a tail.
- **THE DIRECTION INVERTED, AND THAT IS ABOUT MECHANISM, NOT APPETITE.** Five of
  six were OVER-naming, against a corpus record that says under-naming is the
  whole error class. The counter-lesson is narrow: nothing here says name fewer
  boys, it says stop manufacturing tails. 19 of the title's 25 nephew-domain
  calls stood, names included.
- **The missed text was not worked.** Both items the pass handed back -- `LAW`
  on 098 panel 1 and `STA` on 099 panel 6, neither of which
  `audit_missed_text.py` can raise because containment swallows a short needle
  -- are still ungrouped, and so is the drawn pain star on 100. Group counts are
  identical to the prep on both engines, so nothing was renumbered and the
  mirror was safe; but a queue file handed back at the TOP of a report still
  went unworked, which is worth knowing about the hand-back format.
- **Everything else came back clean.** All five type corrections and the one
  text correction (`BRAVE` -> `BRASS MONKEY`) were confirmed, the only ai_text
  change in the title is that retype, and the engine diff, group audit and
  mirror verification are all clean.


### Findings to paste into the next run (2026-09-07, thirty-sixth batch, all six titles reviewed and mirrored)

*The Easter Election*, *The Talking Dog*, *Worm Weary*, *Much Ado about Quackly
Hall*, *Some Heir Over the Rainbow* and *The Master Rainmaker* (60pp, 745
groups) reviewed and mirrored, both engines identical on every mirrored field,
and `closeout.sh --stage review` clean on all six. The correction table below
covers the five titles reviewed in the first pass of the hand-back; *Some Heir*
closed a day later at 129 of 129 with its two stragglers confirmed unchanged, so
it contributes no corrections.

```
                              real corrections      nephew domain      mediums        highs
The Easter Election            4 of 132   3.0%      2 of 17  11.8%     1 of  1      3 of 130  2.3%
The Talking Dog                2 of 127   1.6%      2 of 25   8.0%     0 of  3      2 of 124  1.6%
Worm Weary                     3 of 106   2.8%      3 of  9  33.3%     0 of  1      3 of 105  2.9%
Much Ado about Quackly Hall   33 of 123  26.8%     32 of 42  76.2%     1 of  6     32 of 117 27.4%
The Master Rainmaker           2 of 128   1.6%      1 of  5  20.0%     2 of  4      0 of 124  0.0%
    batch                     44 of 616   7.1%     40 of 98  40.8%     4 of 15     40 of 600  6.7%
    batch without Quackly     11 of 493   2.2%      8 of 56  14.3%     3 of  9      8 of 483  1.7%
```

- **A COSTUME IS A CAP, AND REFUSING TO READ ONE COST 30 NAMES IN A SINGLE
  TITLE.** *Quackly Hall* dresses the three boys in a pirate tricorn, a red
  bandana with an eyepatch and a gold paper crown, and keeps them in costume for
  all ten pages. The pass found that the pirate's blue cap shows as a band inside
  the hat brim, named him Dewey wherever it printed -- and then declined every
  other boy on the grounds that the bandana and the crown "cover the crowns".
  The review named all three, on a mapping that is fixed for the whole story:

  | costume | boy | cap_colour the review recorded |
  |---|---|---|
  | red bandana and eyepatch | Huey | `red` |
  | black pirate tricorn | Dewey | `blue` |
  | gold paper crown | Louie | `null` |

  It holds on every sole-figure panel in the title: 140 p1 and 145 p1/p4 are the
  bandana boy alone and all three came back Huey; 140 p4 and 141 p2 are the crown
  boy alone and both came back Louie. **The bandana is treated as showing the red
  ink** -- the review put `cap_colour: red` on it -- and the crown shows nothing,
  so Louie is the elimination. This is the *Trick or Treat* precedent (devil
  hood / witch hat / ghost sheet, same volume) and the pass had it in front of it
  and did not apply it. **Fix a costume mapping from the sole-figure panels
  before page 1, exactly as you would fix a cap palette.**
- **AND THE TELL IS IN THE PASS'S OWN PROSE AGAIN.** Six of the thirty notes say
  some version of *"the bandana and the crown hide their wearers' crowns
  entirely"*. Having written the pirate/blue link down, the pass never asked
  whether the other two costumes were equally fixed. If you find yourself
  identifying one boy by his costume and declining the other two, you have
  already found the convention -- finish it.
- **A MEASURED TIP BEATS A DIALOGUE CHAIN, AND THIS TIME THE CHAIN WON AND WAS
  WRONG.** *The Easter Election* 114 g8: the tip was measured at local x747
  against a head span beginning at x746 -- literally on the green-capped boy --
  and the pass then argued past it, because the next panel has the green-capped
  boy answering that very line and "so the green boy did not say it". The review
  restored Louie. A character contradicting or answering his own previous line is
  ordinary Barks; it is not evidence about a tail. **Never use the next panel to
  overrule a tip you have already measured onto a head.**
- **AN `other:` ROLE CAN BE A NEPHEW IN COSTUME.** 115 g9, the bearded delivery
  man in the blue uniform who brings Gladstone the perfume, came back `nephews` --
  the boys sent the parcel and one of them delivered it. The pass read the
  uniform as a role and stopped. Where a story has the boys running a scheme,
  check whether a walk-on is one of them before opening an `other:`.
- **THE MEDIUM FLAG DISCRIMINATED THIS BATCH, for the first time in four.**
  4 of 15 mediums corrected against 40 of 600 highs; strip Quackly Hall out and
  it is 3 of 9 (33.3%) against 8 of 483 (1.7%), a twentyfold difference. Both
  *Master Rainmaker* corrections were mediums and neither of its 124 highs moved.
  Keep writing them.
- **THREE OVER-NAMINGS, ALL THE SAME MOVE.** 138 g10, 135 g9 and 167 g14 each
  read a cap sliver and named a boy the tail did not reach. 167 g14 is the
  muddy `#2a9f8f` H171.8 at S0.74 -- below the S0.75 floor with no clean cool
  companion in the panel, which the corpus already says names nobody. The rule
  held; the pass named him anyway.
- **ALL 18 TYPE CORRECTIONS CONFIRMED**, and `vision-corrections` with no
  `--title` reports *Nothing outstanding across 460 title(s)*. The productive
  ones were the caption boxes stored as dialogue (5 across the batch), a squawk
  and a yell of pain stored as sound effects, a whale's hiccup likewise, and a
  voice arriving out of a telephone receiver stored as a thought.
- **THE STANDING RULING ON DRAWN DEVICES, GIVEN 2026-09-07: A DEVICE IS NOT A
  GROUP.** Nine missed-text items were handed back; the review grouped the two
  that carry readable text -- 111's cut-off fascia (as `GROCERY`, correcting the
  pass's `CERY`) and 157's dollar signs -- and GLK then declined all six drawn
  devices at once ("skip the drawn devices"): the musical notes, the quaver, the
  seeing-stars, the pain stars, the hearts and the anger star. All six are now in
  `missed-text-ignore.txt`, scoped to their pages, with the strings pasted from
  each page's `visible_text`.
  **The line is whether a reader could read it.** Text a reader could read goes
  in a box; a device carrying no characters does not, and belongs in
  `visible_text` and the ignore list. Keep recording every device in
  `visible_text` -- that is what makes the audit find it and what the ignore
  entry is matched against -- but expect the ignore list, not a group, and say so
  in the hand-back so the reviewer can decline the set in one word rather than
  one at a time. This retires the error class that ran two batches.
  The ninth item was ruled on separately the same day and went the same way:
  131's `LA`, the two letters the panel edge leaves of a LABORATORY sign, is real
  lettering rather than a device but "just too truncated" to be worth a box. So
  the second half of the line is **how much of it is left** -- a fragment too
  short to read is no more a group than a device is. Note it could never have
  been raised by the audit anyway (`LA` is contained in the same page's `LATER!`
  caption, and containment swallows a short needle), so it existed only in the
  hand-back; the ignore entry is the record of the decision rather than
  something the audit needs.
- **AN INSERT STRANDED TWO GROUPS, NOT ONE.** *Some Heir* 157 gained the dollar
  signs at g9 and every later id shifted by one; g8 and g13 came back unreviewed
  on the first pass and were caught by counting `speaker_reviewed` before
  mirroring. Both were then confirmed unchanged, so the cost was a day rather
  than a wrong name -- but the title would have been committed at 127 of 129 and
  called done. **Count `speaker_reviewed` on both engines before mirroring, every
  time**, and hold the mirror on a title that is short even by one.

### Findings to paste into the next run (2026-09-07, thirty-seventh batch, all three titles reviewed)

*The Money Stairs* (Vol. 13), *The Horseradish Story* and *The Round Money Bin*
(Vol. 12) reviewed and mirrored, all three clean on every gating check of
`closeout.sh --stage review`, and both engines identical on group count,
`speaker_reviewed`, `identified_by` and the speaker / cap_colour / confidence
distributions.

```
                       real corrections   touching nephews   mediums     highs
The Money Stairs         1 of  98   1.0%   0 of  1    0.0%   (none)    1 of  97  1.0%
The Horseradish Story    3 of 255   1.2%   2 of 36    5.6%   1 of 4    2 of 250  0.8%
The Round Money Bin      4 of 142   2.8%   2 of  4   50.0%   (none)    4 of 141  2.8%
    batch                8 of 495   1.6%   4 of 41    9.8%   1 of 4    7 of 488  1.4%
```

"touching nephews" counts a correction with `Huey`/`Dewey`/`Louie`/`nephews` on
either side, against the number of groups the title finally has in that domain.
It is not `review_findings`' own nephew figure, which counts the review's added
groups as corrections and reported *Round Money Bin* as 4 of 4. Note the
denominators: 1 and 4 on two of the three titles, so read those rows as counts.

**Not one nephew was misidentified in 495 groups.** Every name the pass wrote --
including all four it took from the one direct address in *Horseradish* -- came
back untouched. The whole nephew-domain error is one DECLINE the review
sharpened, which is the corpus's standing shape and it held again here.

The counts above exclude the three groups the review ADDED and then finished
itself -- *Money Stairs* 172 g10, *Horseradish* 088 g12 and *Round Money Bin*
109 g2 -- which `review_findings` reports as `unknown ->` corrections but which
correct nothing the pass wrote. *Round Money Bin*'s nephew denominator is 4, so
read its 75% as three groups, not as a rate.

- **THREE OF THE BATCH'S FOUR READING REVERSALS WERE ONE MOVE: A DRAWN FEATURE
  ASSERTED FROM THE 250px MONTAGE AND NEVER CHECKED AT PANEL RESOLUTION.**
  *Money Stairs* 170 g7, the pass wrote *"a bordered caption box at the top
  left, not a balloon"* and gave it to `narrator`; at source resolution it is a
  plain speech balloon with a tail running down to Scrooge, who is drinking from
  the bottle. *Horseradish* 098 g7, the pass wrote *"the figure wears the white
  captain's cap with the black band"* and gave it to Scrooge; at source
  resolution the figure is a nephew in a plain white gob cap with no band, a
  hair tuft and no whiskers. *Horseradish* 097 g3, the pass wrote *"the sea
  striking the hull, lettered across the panel"* and typed `SMACKO!` as a
  `sound_effect` with speaker `none`; at source resolution it is lettered in a
  BALLOON with a pointed tail, which is why the reviewer made it `dialogue`
  (see the `sound_effect` bullet below). All three notes name a specific
  feature as the evidence, and in all three the feature is not in the drawing.
  **The rule: a montage settles who is in frame and roughly where the balloons
  sit. It does not settle a box border, a cap band, or anything else a note
  offers as its reason.** If the note is going to name a drawn feature, that
  feature has to have been seen at panel resolution or better -- and the panel
  is free, it is already on disk. This is the cheap half of the cost doc's
  "precision theatre" warning inverted: not an expensive crop propping up a call
  already believed, but a confident note written on a view that could not carry
  it. Note also what this does NOT overturn: 170 g7 was never a caption box, so
  **"a caption box is the narrator" stands untouched**, and *Money Stairs* 174
  g7 -- a genuine pink caption reading `Scrooge: "..."` -- remains `narrator`.
- **THE MEDIUM FLAG DISCRIMINATED AGAIN, AND THE NOTE MADE THE FIX A KEYSTROKE.**
  1 of 4 mediums corrected (25.0%) against 2 of 250 highs (0.8%), a thirtyfold
  gap, and the one that moved was *Horseradish* 104 g5 -- one of four `YES!`
  balloons answering Donald from off-panel in a close-up where he is the only
  figure drawn. The pass could not map any of the four tails, recorded all four
  as the collective at medium, and wrote into each note *"ONE OF THESE FOUR IS
  SCROOGE'S and the art does not say which"*. The review named exactly one.
  **When an ambiguity is N-way and closed, say so in the note and flag the whole
  set at medium**: it converts an unrecoverable guess into one keystroke.
- **ONE DIRECT ADDRESS CAN CARRY A WHOLE TITLE WITH NO CAP INK IN IT.**
  *Horseradish* puts all three boys in identical plain WHITE gob caps for
  twenty-two pages -- `cap_colour` is null on all 255 groups and **0 cap colours
  were overturned**. Scrooge names DEWEY once, on 095 p5, sending him to the
  radio; the radio headphones then identify the same boy on 095 p7, 095 p8 and
  098 p8. Four named nephew calls in a title with nothing to sample, and all
  four survived review. **A prop a story hands to one boy and lets him keep is
  as good as a cap for as long as he keeps it** -- and unlike a cap it does not
  need a clean print.
- **A SOUND EFFECT IN A BALLOON IS DIALOGUE. CHECK THE SHAPE BEFORE TYPING ONE
  `sound_effect`.** *Horseradish* 097 g3, `SMACKO!`, came back `sound_effect ->
  dialogue` with the speaker `none -> unknown`, and it is the only one of the
  title's THIRTEEN effects that moved. The reason is visible the moment the
  panel is opened: `SMACKO!` sits in a **speech balloon with a pointed tail**,
  while `SNAP!`, `POP!`, `WAM!`, `BLAM!`, `BIFF!`, `BOP!`, `SOCK!`, `BAM!`,
  `ROAR!`, `POW BOOM! BAM!` and both `S.O.S!` are **display lettering painted
  into the art** -- and all twelve of those correctly stayed `none`.
  The roster's rule that *"UNBOXED words are not settled by the drawing"* has a
  converse it does not spell out: **a BOXED one is.** A balloon means a voice
  utters it, whatever the word imitates -- so the type is `dialogue`, and where
  the panel is a long shot with nobody drawn at readable size the speaker is
  **`unknown`, not `none`**. `none` is for lettering nobody utters; it is not
  the default for anything that reads like a noise.
  I first reported this to the reviewer as a probable slip, on the grounds that
  twelve of thirteen had gone the other way. Counting the class was right; the
  conclusion was wrong, because I had counted the words and not looked at their
  shapes. **When one member of a uniform class moves, open it before calling it
  a slip** -- the thing that makes it the exception is usually visible.
- **A FILLER PAGE BOUND TO A TITLE REACHES NO QUEUE, AND BACK_MATTER DOES IT
  TOO.** *Horseradish* spans Vol. 12 083-107, but prep only takes `BODY`: 083 is
  `FRONT_MATTER` and **106 and 107 are `BACK_MATTER`**, three complete one-page
  Uncle Scrooge gag strips carrying **37 easyocr groups** between them, grouped
  by OCR and annotated by nobody. The tell is the mirror's page count against
  prep's -- `25 page(s)` against `Prepared 22 page(s)` -- and `review_findings`
  reporting 292 groups where the pass wrote 255. The corpus note for this only
  mentioned FRONT_MATTER and a single page; check both ends of a title's range.
- **THE MISSED-TEXT AUDIT CANNOT SEE A DEVICE IT ALREADY HAS.** *Money Stairs*
  172's four drawn dollar signs were handed back as missed text, the review
  grouped them as g10 `'$ $ $ $'` -- and the audit still reports them, because a
  bare glyph normalises to nothing and cannot match the prose entry that raised
  it. The same shape hides two already-grouped question marks on *Round Money
  Bin* 112 g8 and 114 g6, and *Round Money Bin* 109 g2 once the review boxed
  the coin picture's five dollar signs. **A device finding does not clear itself
  when the device is boxed** -- and the fix is not a hand-back note but a
  one-string edit the corpus already documents: `visible_text` carries prose
  only while the lettering is UNGROUPED, and the exact glyph once somebody has
  boxed it. Putting the glyph back cleared all four titles-worth of phantoms and
  took the batch to 0 findings in all three classes.
  And the dollar signs settle the standing question the other way from the
  drawn-device ruling: **the review boxes dollar signs**, as it did on *Some
  Heir* 157, while musical notes, pain stars and arrows stay in the ignore list.

- **A 21px SLIVER `heads.py` REFUSED TO ATTACH WAS STILL THE CAP.** The batch's
  one under-naming, *Round Money Bin* 109 g8: a wide bridge shot, three boys
  fishing, small in frame. `capscan` at a **4px** floor found exactly two
  chromatic blobs on the figures -- Donald's own sailor cap and his bow tie --
  plus a **21px red at `#d92124` (H359, S0.85)** sitting on the left boy's
  crown, the boy the tail reaches. `heads.py` did not attach it to any head, so
  the pass wrote `nephews` and put the measurement in the note. The review
  named **Huey**, `cap_colour: red`.
  **`heads.py` not attaching a blob is not evidence the blob is not a cap.**
  It finds the white skull from the beak, and on a small figure that region is
  tiny, so a crown sliver sitting above it falls outside. Where the hex is a
  clean roster ink, the blob sits where the crown would be, and the tail already
  reaches that boy, the sliver names him -- 21px is enough. This is
  `feedback_declined_caps_that_do_print` again, and the pass had every number it
  needed in its own note before declining.
- **ONE INSERT AND ONE MERGE CANCELLED IN THE TOTAL AND HID BOTH.**
  *Round Money Bin* finished at 142 groups, exactly what the pass wrote -- but
  109 **gained** one (the coin picture's dollar signs, inserted at **g2**, which
  shifted all thirteen later ids on that page) and 113 **lost** one (the review
  merged the number plate and the shirt legend into `176-071 BEAGLE BOYS INC.`).
  A title-level count would have shown 142 = 142 and reported nothing.
  **Diff group counts PER PAGE against the prep, not per title**, and when a
  page has moved, match old to new by (text, occurrence) rather than by id --
  the ids from g2 down are all one out. Nothing was lost here: the merge keeps
  both strings and the review standardised `INC.` onto all three Beagle Boy
  legends in the title, but only a per-page diff shows that.

### Findings to paste into the next run (2026-09-07, thirty-eighth batch, all four titles reviewed)

*Bee Bumbles* (Vol. 13), *Wispy Willie*, *The Hammy Camel* and *Fix-up
Mix-up* (Vol. 15), all four reviewed and mirrored, every mirror clean on
group count, `speaker_reviewed`, `identified_by` and the three distributions.

```
                    real corrections   under-naming   over-naming        highs
Bee Bumbles        10 of 126   7.9%      6 of 10          -        10 of 124  8.1%
Wispy Willie       18 of 137  13.1%      1 of 18          -        17 of 136 12.5%
The Hammy Camel    14 of 124  11.3%     12 of 14          -        14 of 123 11.4%
Fix-up Mix-up      12 of 106  11.3%      3 of 12       8 of 12     10 of 104  9.6%
    batch          54 of 493  11.0%     22 of 54       8 of 54     51 of 487 10.5%
```

**11.0% against the thirty-seventh batch's 1.6%.** The worst batch on record,
and it is two opposite errors made in sequence, not a spread of unrelated
slips: under-naming from a false premise on the first three titles, then
over-naming on the fourth after that feedback arrived.

**Every medium in the batch was corrected -- 3 of 3 -- against 51 of 487
highs (10.5%).** Third batch running. The flag is doing more work than any
other single signal available to the pass.

- **THE ERROR IS A TITLE-WIDE PREMISE BUILT FROM A TWO-PANEL SAMPLE, AND IT
  PROPAGATES INTO EVERY NOTE IN THE DOMAIN.** The pass read two panels of
  *Wispy Willie* -- 023 p5 and 025 p8, **both interiors** -- found the boys
  bare-headed, and wrote *"the nephews are drawn BARE-HEADED throughout this
  title"* into **all 26** of its nephew notes. The same sentence went into all
  49 of *The Hammy Camel*'s. Both claims are false: 021 p7 puts all three
  *Wispy Willie* boys in clean blue, red and green bands, and *Hammy Camel*
  032 p4 and 031 p5 do the same. Twelve of *Hammy Camel*'s fourteen
  corrections are nephews the review named off a band the pass had declared
  absent, and every one of those twelve notes opens with that sentence.
  **A cap fact is a per-panel fact.** Write it in the note for the panel it
  was measured on and nowhere else. If a title-wide claim is worth making at
  all it needs a sweep, not two panels -- and the two panels the pass happened
  to open were the two where the caps were off.
- **THE SAMPLE WAS BIASED AND THE PASS COULD HAVE SEEN IT.** Both *Wispy
  Willie* panels were interiors. `caps off indoors, on outdoors` is already a
  standing corpus note, and the pass had it available and did not apply it.
  Where a cap seems absent, **check an outdoor panel and an indoor one before
  generalising at all**, and say in the note which you checked.
- **THE SAME PREMISE ALSO COST NINE CALLS THAT WERE NOT ABOUT CAPS.** Nine
  *Wispy Willie* groups went `nephews -> Donald`: Donald is in the marsh and
  laboratory sequence and the pass took every small duck there for a nephew.
  022 p3 shows him plainly at panel resolution, blue cap and red bow tie, one
  nephew beside him. Having decided the boys were capless the pass stopped
  reading heads in that whole sequence. **A wrong premise does not just
  produce wrong collectives; it stops you looking.**
- **A DISGUISE IS NOT REFUTED BY A COSTUME.** Six groups went `other:the rat
  inspector -> Scrooge`. The inspector IS Scrooge, and *018 p3 is a
  single-figure close-up showing his own face and pince-nez under a false
  beard* -- the cheapest possible check, one panel already on disk. The pass
  read the 250px montage instead and wrote a confident note: *"He is a hired
  man, not Scrooge in disguise -- Scrooge is thin, in a maroon coat and top
  hat, and appears in his own office two panels earlier."* Appearing in his
  own office two panels earlier is not an alibi, and a costume difference is
  not evidence against a disguise **in a story whose plot is the villain
  putting on costumes**. This is the thirty-seventh batch's montage rule
  recurring: a note that names a drawn feature as its reason must have seen
  that feature at panel resolution.
- **THE MEDIUM FLAG WORKED AGAIN, AND SO DID ITS ABSENCE.** *Wispy Willie*
  025 g11, the `! ! !` device, was flagged medium precisely because the
  silhouette carried neither of Scrooge's props -- 1 of 1 medium corrected,
  against 17 of 136 highs. But *Hammy Camel* 035 g13 was given to Donald at
  HIGH with the doubt written into its own note (*"`YEAH!` reads as a reply"*)
  and came back `nephews`. **If the note contains the objection, the call is
  not high.** Writing the doubt down is not a substitute for flagging it.
- **THE CORRECTION FOR UNDER-NAMING OVERSHOT, AND THE FOURTH TITLE PAID FOR
  IT. THIS IS THE MOST IMPORTANT LINE IN THIS SECTION.** *Fix-up Mix-up* was
  re-read before review on the strength of the three findings above: 5 of its
  13 collectives were named, taking it from 9 named to 14 in about ten images.
  **Four of those five were wrong.** The review put the title back to 9 named
  and 13 collectives -- 8 of its 12 corrections are `a name -> nephews`, and
  it is the only title of the batch where review NET-REDUCED naming.
  What makes it worth writing down is that the pass had **already recorded the
  reason each one was unsafe, in the note, and named anyway**: 038 g9 says
  *"about 120px clear of the GREEN boy's head"*, 040 g0 says *"about 55px
  clear"*, 038 g3 says the tail is *"the one scallop that extends well below
  its neighbours"* -- i.e. not certainly a tail at all. Three measurements
  written down and three names given against them.
  **A tail tip that stops in open space above a crown is not a tail landing on
  that boy, however clean his band is.** The band tells you who a figure IS;
  it does not make an ambiguous tip unambiguous. And note the shape of the
  mistake: a correction arriving from review is a correction to ONE error
  class, not a licence to lower the bar generally. The right response to
  "you under-named" is to re-examine the DECLINES whose evidence was never
  measured -- not to promote the ones already measured and found short.
  The three genuine under-namings the review did find here (036 g6, 037 g12,
  038 g1) were all groups where the pass had recorded the crown as turned away
  or the probe as too weak, which is the opposite situation.
- **TWO REVIEW ADDS, AND ONE OF THEM SHOWS THE COPY IN RESIDUE TRAP INTACT.**
  *Bee Bumbles* 181 gained `GROCERY` -- the reviewer's resolution of the
  truncated `GROC` the pass handed back -- and 180 gained a group whose box
  sits exactly on the `CRASH!` lettering (panel (42,20)-(518,329) against ink
  measured at (51,34)-(497,318)) but whose `ai_text` is still `?`, the seed
  group's text. The box was dragged onto the right lettering and the text was
  never changed, which is why the missed-text audit still reports CRASH! as
  ungrouped. *Hammy Camel* 030 gained `313`, Donald's number plate, which the
  pass had not recorded in `visible_text` at all -- a licence plate is in the
  roster's own list of examples.
- **STRAGGLERS AGAIN, ON TWO OF THE THREE.** *Bee Bumbles* finished 122 of 126
  and *The Hammy Camel* 123 of 124. Count `speaker_reviewed` on both engines
  before mirroring; neither title could be mirrored on the day.

### Findings to paste into the next run (2026-09-08, thirty-ninth batch, both titles reviewed)

*Turkey Trot at One Whistle* (Vol. 15) and *The Menehune Mystery* (Vol. 12).
Turkey Trot reviewed and mirrored, clean on group count, `speaker_reviewed`,
`identified_by` and all three distributions. Menehune read and handed back.

```
                        real corrections   under-naming   over-naming        highs
Turkey Trot        6 of 113   5.3%       4 of 6        2 of 6      6 of 113  5.3%
    nephew domain  6 of  24  25.0%
```

**5.3% overall but 25.0% of the nephew domain** -- every correction the review
made was a nephew call. The pass wrote no mediums at all, so there is no
medium-against-high split to report this time; that is itself worth noting,
because the flag has been the single most useful signal in the last three
batches and this pass gave the reviewer none of it.

- **A CROP FRAMED ON THE FACE CANNOT CONTAIN A CAP, AND WILL ALWAYS READ
  BARE-HEADED.** This is the whole of the under-naming in this batch. 053 g5
  was declared bare-headed off a 5x crop whose top edge sat at panel **y=432**
  when the black crown and its red band run **y=365-420** -- the cap was
  entirely above the window. Re-cropped afterwards with headroom it is
  unmistakable. The crown sits ON TOP of the white skull, so the crop has to
  extend roughly a head-height above it; `heads.py`'s own docstring says as
  much about its crown strip, and the pass had that warning and cropped as if
  it did not. **Before writing `bare-headed`, check that the crop contains sky
  above the skull.**
- **`heads.py` SAYING `no cap ink` IS NOT AN ABSENCE CLAIM.** 054 g4 and g6
  were declined on exactly that, and the review named Huey and Dewey off a red
  and a blue band. That line is a per-head result at a 100px floor, not the
  census's own `N blob(s) total`; the roster's absence rule wants the second,
  and the honest response to the first is to crop.
- **RELATIVE HEAD SIZE IS NOT A DONALD TEST -- CROWN SHAPE IS.** 048 g2 was
  given to Donald because the left figure's head looked full-size beside a
  smaller one; it is Louie. Two things in the pass's own crop said so and were
  not used: the figure has a **hair tuft**, and his cap is the SAME
  construction as the red-banded boy's beside him. Donald's in that story is a
  green kepi with a black brim, a different object. The other figure was
  smaller because it was turned away, not because it was a child. 050 g0 is
  the same confusion inverted, `nephews` where Donald was in frame.
- **AND THAT REVERSAL CORRECTS A PALETTE CLAIM THIS FILE WOULD OTHERWISE HAVE
  CARRIED FORWARD.** On the strength of 048 g2 the pass wrote that Donald's cap
  green and Louie's band are the same ink darkened. They are not: **Donald
  `#4f753b`/`#4d743b` H99-103 S0.47-0.50 V0.45; Louie `#4da33e`/`#4ea340`
  H110-112 S0.61-0.62 V0.63.** Hue and value both separate them cleanly. The
  pass had measured exactly that on 047 p6 first and then talked itself out of
  it on the strength of the misidentified figure. **A measurement overturned by
  an identification is worth re-checking before the identification is trusted.**
- **A TITLE-WIDE CAP CLAIM WAS MADE AND CAUGHT MID-PASS.** On *Menehune* the
  first three panels opened -- 120 p5 (office), 131 (ship's brig), 143 (island)
  -- all showed bare heads, and `the boys wear no caps in this story` went into
  the notes. **122 p8 disproves it**: all three crowns carry bands, probed on
  the heads at `#e22721` H1.9 S0.85 and `#06a4d4` H193.4 S0.97, the third bare
  and therefore Louie by elimination. Every affected note was rewritten as a
  per-panel fact. The thirty-eighth batch's rule held, but only because the
  sample was extended; three panels is not a sweep either.
- **A BOLD CUT IS PER TITLE AND NEEDS TWO CALIBRATION CROPS, NOT ONE.**
  *Turkey Trot* sits at 1.15 (GOOD 1.16 bold, MISTAKE 1.04 not). *Menehune*
  looked like 1.30 off one crop -- 120 g1, where FOR SAFEKEEPING! at 1.24 is
  genuinely not bold -- and a second crop at 143 g10 showed KNOW at **1.28
  plainly bold**, putting the real cut near 1.26. One crop gives an upper
  bound, not a threshold. Take a second on a balloon whose hits straddle the
  gap.
- **allbold's ROW LABELS GO OUT BY ONE, AND ITS EDGE BLOBS ARE OUTLINE.** Seen
  repeatedly this batch: on 053 g5 it prints L2-L5 for four drawn rows so its
  "HIM WITH" hit is really FIGHT; on 053 g2 two hits at 1.49 and 1.70 both END
  at x=693 and are the balloon's right edge, not words. **Ranges that share an
  end x, or that sit past the last word, are outline.** Check the x-range
  before marking, and re-check any line whose blob count does not match its
  word count.
- **THE EMPHASIS FIELD MUST COPY THE STORED LINE BREAKS.** Six groups in
  *Menehune* failed validation because the markup was retyped with the pass's
  own line breaks. `vision_apply` catches it, but only after all the reading is
  done; strip-and-compare locally first, which takes seconds.

**One group added that neither engine had**: *Menehune* 127 panel 5 carries
`SLAP!` lettered across the whole frame and had no group at all on either side.
Panels holding nothing but display lettering are where this happens -- the
panel had no other text for the engines to anchor on.


**Menehune came back at 1.8%, the best rate on record, and the contrast with
Turkey Trot's 25.0% nephew domain is the useful part.**

```
                        real corrections   nephew domain            highs
Turkey Trot        6 of 113   5.3%      6 of  24  25.0%     6 of 113  5.3%
Menehune           7 of 398   1.8%      4 of  72   5.6%     7 of 398  1.8%
    batch         13 of 511   2.5%     10 of  96  10.4%    13 of 511  2.5%
```

Menehune is 32 pages against Turkey Trot's 10 and took 1.75 images per page
against 3.7, and it still corrected less than a third as often per group.
The difference is not care, it is **what the art offered**: Menehune has no
cap to misread on 31 of its 32 pages, so the pass mostly had to choose between
adults, which it does well. Turkey Trot had readable bands and the pass got
four of them wrong by cropping badly. **The error rate tracks how much cap
reading a title demands, not how long it is.**

- **A CHAIN BUILT ON ONE TRACED TIP FAILS WHOLE.** *Menehune* 141 p7/p8 came
  back INVERTED END TO END -- three groups, all three wrong. The pass traced
  one tail ("down to a tip on Donald's head, blue sailor cap"), assigned the
  other balloon by elimination from it, and then assigned the next panel from
  that. One measurement, three calls, and when the measurement went the wrong
  way all three followed. **Where a panel has two balloons, trace BOTH before
  chaining a third off either.** Elimination is only as good as the single
  reading it eliminates from.
- **A NAME DERIVED AND THEN ARGUED AWAY IS THE CHEAPEST CORRECTION THERE IS.**
  *Menehune* 122 g9 went `Donald -> Louie`. The pass's own note had already
  worked out that the left boy is Louie -- red and blue bands probed on the
  other two, so the third is his by elimination -- and then declared the tail
  off-panel because it "ended against a blank green wall with no figure near
  it". It reaches him. This is the thirty-eighth batch's *use the evidence you
  wrote* finding again, and it is now the second batch running where the single
  most expensive nephew error was a name the pass had already assembled.
- **TRANSCRIBE THE WHOLE OF A COSTUME LABEL, NUMBER AND ALL.** Five of the
  review's seven added groups on *Menehune* are Beagle Boy number plates the
  pass never noticed, and two more are corrections of plates it DID group but
  transcribed as bare `BEAGLE BOYS` when the art reads `176-761 BEAGLE BOYS,
  INC.`. The digits sit in a separate yellow tab above the jersey word, so they
  read as a different object and get dropped. On a Beagle Boys title the plates
  are the most numerous piece of background lettering on the page -- twenty-odd
  groups in this one -- and they are searchable text.
- **ALL NINE PROPOSED TYPE CORRECTIONS WERE CONFIRMED**, including the five
  bird cries on 138 and the boys' whispered `BZZT BZZT` on 149. The
  voice-versus-machine test is holding; what still needs saying is the reverse
  direction, `142 g2 dialogue -> background`, a chest number plate stored as
  speech. **Both directions are worth proposing.**
- **TURKEY TROT'S SIX TYPE CORRECTIONS WERE NOT WORKED AND ARE STILL OPEN**
  while Menehune's nine were all confirmed in the same sitting. The speaker
  queue and the corrections queue are separate files and a title can finish
  113/113 on one with the other untouched -- which is exactly what happened.
  Hand back the corrections queue path in the same message as the speaker one.

### Findings to paste into the next run (2026-09-08, fortieth batch, both titles reviewed and mirrored)

*Raffle Reversal* (Vol. 15) and *The Secret of Atlantis* (Vol. 12), both
reviewed and mirrored. Raffle Reversal clean on every gating check at 142/142;
Atlantis first mirrored at 395/397, then finished at **397/397** once the two
groups the review had not reached, 171 g0 and 173 g9, came back confirmed as
the pass wrote them. Both titles end clean on every gating check.

```
                       real corrections    nephew domain          highs        mediums
Raffle Reversal    3 of 142   2.1%      2 of 16  12.5%     3 of 139  2.2%   0 of  3   0.0%
Atlantis          35 of 432   8.1%     23 of 78  29.5%    23 of 375  6.1%   8 of 18  44.4%
    batch         38 of 574   6.6%     25 of 94  26.6%    26 of 514  5.1%   8 of 21  38.1%
```

**The medium flag earned its keep: 38.1% of mediums corrected against 5.1% of
highs, the widest split on record.** Where the pass hedged it was right to.
That is the argument for writing mediums at all -- the thirty-ninth batch had
none and the reviewer said so.

- **A LEFT/RIGHT RULE DERIVED FROM THREE PANELS AND APPLIED ACROSS SIXTY GROUPS
  IS THIS BATCH'S WHOLE STORY.** Fifteen of Atlantis's 35 corrections are
  Donald and Scrooge swapped inside identical grey diving suits -- nine
  `Scrooge -> Donald` and six the other way. The pass cropped 172 p1, 173 p1 and
  174 p6 at 1.7x, found Donald smooth-headed on the LEFT and Scrooge with
  muttonchops on the RIGHT in all three, wrote that into sixty notes, and then
  leaned on the SEATING wherever the faces were too small to re-check. The face
  test was sound; the seating was a coincidence in three panels. **Three panels
  agreeing is not a rule. Re-read the face in each panel, or write the
  collective.** This is the thirty-ninth batch's *a chain built on one traced
  tip fails whole* at title scale, and it cost more than every cap error in the
  batch put together.
- **TWO ADULTS IN IDENTICAL COSTUME IS A HARDER PROBLEM THAN THREE NEPHEWS IN
  CAPS.** Only four of Atlantis's corrections are one nephew for another or a
  nephew named or declined. The 8.1% is adult-against-adult, and the previous
  batch's rule -- *the error rate tracks how much cap reading a title demands* --
  needs the other half added: **it tracks how much ADULT separating a title
  demands too, and that is the more expensive kind.** A story that puts its two
  adults in the same suit for twenty pages should be read expecting it.
- **THE REFERENCE PANEL'S OWN TAIL WAS MIS-TRACED.** 164 g8 went
  `Dewey -> Louie`, cap `blue -> green`. The pass named 164 p8 the title's cap
  reference, measured all three bands correctly off it, and then read the one
  balloon's tail onto the wrong boy. **Getting the palette right off a panel
  does not get that panel's tail right; they are two separate readings and the
  first one flatters the second.**
- **A WHOLE-PANEL CENSUS ZERO WAS OVERTURNED TWICE IN ONE PANEL.** 168 g4 and
  g5 went `nephews -> Dewey` and `nephews -> Huey`, on a panel whose note read
  "capscan finds only an 86px `#238fb5` in the whole panel, which is the sea".
  The census header was quoted honestly and the bands were there anyway, at
  middle distance on a headland. **A census zero on a panel where the figures
  are small is a reason to crop, not an absence.** The roster already says a
  zero is a threshold; this is the third batch running where it was written up
  as a bare head instead.
- **A MACHINE PLAYING A RECORDED VOICE IS A SPEAKER.** The pass put the four
  juke-box songs on Atlantis 182 down as `sound_effect` with speaker `none`,
  citing *played by a machine, `none`*. The review made all four **dialogue**
  and gave them `other:the jukebox`. Same correction on 160 g7, the
  advertisement on the television screen: `background` / `none` became
  **dialogue** / `other:radio announcer`. **Recorded and broadcast speech is
  speech.** The `none` rule is for a noise no voice makes -- an impact, a door,
  a whistle -- not for a voice arriving through a speaker. The existing note
  about a jagged tail into a radio was right and the pass did not apply it to a
  juke box.
- **THE TYPE PROPOSALS WERE ALL CONFIRMED, AND THE REVIEW FOUND FIVE MORE.**
  Every one of the pass's six type corrections on Atlantis and its one on Raffle
  Reversal stood, including `SOB!` and a pigeon's `HIC!` going
  `sound_effect -> dialogue`, `1313` going `sound_effect -> background`, and two
  pink time captions going `dialogue -> narration`. **Keep proposing both
  directions** -- the five the review added were all ones the pass had looked at
  and left alone.
- **BUT THE SPEAKER ON A CONFIRMED TYPE CAN STILL BE WRONG.** 166 g8: the pass
  moved the pigeon's `HIC!` to dialogue, which was right, and gave it
  `other:the pigeon`, which was not -- the review made it **Scrooge**. Getting
  the type argument right is not evidence about whose voice it is.
- **DRAWN `$` AND `?` DEVICES ARE LETTERING, AND THE AUDIT CANNOT FIND THEM FOR
  YOU.** The pass added six ungrouped devices (a `!` on 157 p7, where the panel
  had no text at all; a winged `$` and a `!` on 178; `DINER` and `CAFE` on the
  178 arcade; a `!` on 180 p8) and the review then added **four more** the pass
  had walked past -- `$ $ $ $ $ $ $` on 158 p6 and 183 p8, `$ $ $` on 159 p2,
  `?` on 173 p8. `audit_missed_text.py` only ever sees what `visible_text`
  holds, so a device the pass never noticed is invisible to it twice over.
  **Sweep each page for bare devices while writing the capture, not afterwards.**
- **AND THE CORPUS IS NOW CLEAN, WHICH TOOK TWO BATCHES IT SHOULD NOT HAVE.**
  A corpus-wide `vision-corrections` run at the end of this batch returned
  exactly six outstanding across 460 titles, and all six were *Turkey Trot at
  One Whistle*'s type corrections from the thirty-ninth batch -- proposed,
  handed back in a queue file, reported again in the close-out, and still not
  worked. They were finished in this batch and the corpus now reports **nothing
  outstanding across 460 titles**.
- **THE INSTRUMENT FOR THAT IS `vision-corrections --type --confirm-all`, AND
  IT IS WHY THE BACKLOG EXISTED.** Agreeing with a proposed type changes no
  value, so unless the editor's type popup is opened and saved on every entry a
  whole review can be walked and leave nothing on disk -- the tool's own
  docstring records 52 corrections checked and 0 stamped. **A reviewer who
  agrees with the whole queue should be told that flag exists**, scoped with
  `--title`; it is the only bulk path and it is deliberately type-only.
- **AND A CONFIRMED SPEAKER DOES NOT CARRY THE TYPE WITH IT.** All three Turkey
  Trot groups already had `speaker_reviewed` on `other:the turkeys` -- a human
  had agreed turkeys make the noise -- while `type_reviewed` stayed absent for
  two batches. The two review states are independent in both directions, and
  the speaker being signed off is the reason nobody noticed.

**On the cheap side, two levers did work and are worth reaching for first.**
Atlantis's `UNCA SCROOGE` / `UNCLE SCROOGE` split held on all 19 occurrences and
settled every off-panel adult line for nothing; the review corrected none of the
calls that rested on it. And a title-wide `heads.py` census run in one process
(about 90 seconds for 242 panels) is what found that the caps come and go by
setting -- worth the wait on any title where the boys drift in and out.

**A process note against the pass, not the reading.** The first title-wide
census on Atlantis was piped through `tail -140` and silently lost its first 21
pages, which made eleven pages look like the only ones carrying cap ink. It was
caught and re-run unfiltered before any absence claim was written, but it is the
same filtered-view trap the roster names, arrived at from a different direction:
not a shell filter dropping a band, but an output limit dropping the beginning.
**Write a long census to a file and read the file.**


### Findings to paste into the next run (2026-09-08, forty-first batch, all three titles reviewed and mirrored)

*Flour Follies*, *The Price of Fame* and *Midgets Madness*, all Vol. 15, all
three reviewed and mirrored, all three at **every group reviewed on both
engines**. One type proposal is still unconfirmed on Midgets Madness (093 g7,
`narration -> sound_effect`), which is a review decision and not a pass one.

```
                       real corrections    nephew domain          highs
Flour Follies       0 of 122   0.0%     0 of   9   0.0%    0 of 122   0.0%
The Price of Fame   2 of 137   1.5%     2 of  60   3.3%    2 of 137   1.5%
Midgets Madness    14 of 152   9.2%     9 of  35  25.7%   14 of 152   9.2%
    batch          16 of 411   3.9%    11 of 104  10.6%   16 of 411   3.9%
```

**Every call in the batch was written `high`, so there is no medium-against-high
split at all.** The fortieth batch measured 38.1% of mediums corrected against
5.1% of highs and called the flag's keep earned; this batch threw that signal
away. A pass that hedges nothing gives the reviewer no ranking to work down.

- **THE OFFSET FAN WAS SPOTTED, NAMED IN THE PASS'S OWN REASONING, AND THEN
  VOTED AGAINST.** *Midgets Madness* 092 p3: three balloons over three boys. The
  pass traced all three tails, found the leftmost landing 43px clear of the
  leftmost boy's head+beak span (163-316) and on a crowd figure instead, wrote
  out `project_offset_fan_reading_order_wins` -- *a tail landing on nobody means
  the whole fan drifted one boy left* -- and then rejected it because the other
  two tails looked clean. The review moved all three exactly one boy right:
  `other:a spectator -> Dewey`, `Dewey -> Huey`, `Huey -> Louie`. **Three of the
  batch's sixteen corrections are that single decision.** A tail landing on
  nobody is the tell, and the other tails in the same fan looking clean is what
  the offset does -- it is not evidence against it. Apply the shift and flag the
  fan as a set so a reviewer can flip it in one go.
- **A COOL CAP CAN PRINT INSIDE THE HEDGE'S OWN HUE BAND, AND THE PROBE WILL NOT
  SAY SO.** *The Price of Fame* 077 g2, `nephews -> Dewey`: the band is
  `#23a16b` **H154.3 S0.78** at 38px, six degrees from the hedge's `#009e49`
  H147.7 **S1.00** and inside the same capscan band. `probe.py` reported
  `green 4389px #009e49` for the crown strip and the pass wrote *no cap ink at
  all*; `capwide` returns **`blue: 0 blob(s)` for the whole panel**, so the cool
  cap was never going to appear in the blue band. **Rank saturation inside the
  band. The band label is not the answer, and on a Vol. 15 title the cap is
  routinely the desaturated member of a band the scenery also occupies.**
- **AND ONE SWAMPED PROBE COST BOTH OF THAT TITLE'S CORRECTIONS.** Having
  written the absence on 077 g2, the pass used the same kind of probe on 077 g5
  to name the third boy *by elimination* -- `Louie`, cap null. The review made it
  `Huey`, cap red: the tail tip sits 12px from each of two heads and the wedge
  points down-LEFT at the red-banded one, which a 3x crop shows plainly. **An
  absence claim is not just a declined name; it silently becomes the premise of
  every elimination on the panel.**
- **A PROBE OVER A BOX YOU CHOSE IS A VIEW, NOT THE SCAN'S ANSWER.** The roster
  already says a filtered census is not the census. This batch is the same
  failure one level down: both Price of Fame probes were run honestly and quoted
  honestly, and simply did not contain the band. Before writing an absence,
  re-run `capwide` over the WHOLE panel and quote its per-band `N blob(s)` line,
  which is the thing that would have said `blue: 0` and prompted a crop.
- **THE MISSED-TEXT AUDIT CANNOT SEE A REPEATED LABEL.** All three titles
  returned **0 findings in all three classes**, and the review then added
  **eleven groups**: ten background labels in *Midgets Madness* -- nine `49` car
  numbers, the `JUDGE` badge on 094 p5, the `O-U2` licence plate on the truck in
  093 p3 -- and a `? ?` device pair in *Flour Follies* 071 p8. `49` and `JUDGE`
  were both in the pass's `visible_text`, but **once each**: the audit matches
  that one occurrence against the first group carrying it and reports nothing,
  so the second and third `49` on a page are invisible. **Write the repeats in,
  or an audit zero means only that one of them is grouped.**
- **THE BARE DEVICES WERE MISSED AGAIN, ONE BATCH AFTER THE RULE WAS WRITTEN.**
  The fortieth batch's *sweep each page for bare devices while writing the
  capture, not afterwards* was carried into this pass and still lost the `? ?`
  either side of Mrs. Heartless's head on *Flour Follies* 071 p8 -- on the panel
  whose whole joke is her reaction. Devices are invisible to the audit twice
  over, so the sweep is the only thing that finds them.
- **A CAPTION BOX CAN BE A CHARACTER CONTINUING ACROSS THE PANEL BREAK.**
  *Midgets Madness* 089 g4, `narrator -> Louie`, the reviewer's note reading
  *Louie continuing from previous panel*. On its own the box is author's-voice
  narration and reads that way; what settles it is the sentence it finishes from
  the panel before. Read the previous balloon before typing a caption `narrator`.
- **AN ENGINE NOISE IN A BALLOON IS STILL SOMEBODY'S.** *Midgets Madness* 095
  g10, `none -> Dewey`. The pass cropped at 1.2x, read the marks between the
  balloon and the figure as sweat rather than a bubble trail, noted the beak was
  shut, and gave `CHUG! CHUG! CHUG! CHUG!` to the machine. It is a nephew
  mimicking the engine as he pedals past. The existing rule -- *a balloon means
  a voice* -- outranks a judgement about which figure looks like it is making
  the noise.
- **THREE CROWD CALLS WERE OVERTURNED, TWO OF THEM TO NEPHEWS.**
  `other:a spectator in the crowd` went to `nephews` twice and to `Dewey` once.
  A tail running into a black silhouette is not automatically a spectator when
  the nephews are in the same frame; on a fairground title the crowd is the
  default background and the boys keep being drawn against it.
- **ADDS RENUMBER MID-PAGE AND STRAND THE REVIEW'S OWN STAMPS.** Six of the ten
  *Midgets Madness* inserts landed mid-page, shifting every later id by one, and
  ten of the pass's groups came out of the review with no `speaker_reviewed` at
  all -- the last entries of each grown page. The skill warns that an add
  strands later queue entries; this is the first batch to see it at scale.
  **After a review that added groups, count `speaker_reviewed` against the NEW
  total, never the pass's, and re-issue a straggler queue before calling the
  title done.** Worth doing rather than waving through: the ten looked like
  pure artefact -- every one still carried the pass's own value -- and when the
  queue was worked, eight were confirmed as written and **two were a swap**, the
  095 pair below. A straggler queue is not a formality.
- **THE SKY BETWEEN A BALLOON AND THE HEADS UNDER IT MAKES WEDGES THAT LOOK
  EXACTLY LIKE TAILS.** *Midgets Madness* 095 g13 and g14 came back as a clean
  swap, `Huey <-> Louie` and `red <-> green`, and both are one misread. On 095
  p8 the balloon sits directly above two boys, and the background shows through
  either side of the real tail as two clean downward wedges; the pass traced one
  of THOSE, which moved the tip 20-30px left, out of the red boy's head+beak
  span (starting x347) and into the gap, and the gap then got resolved by
  direction to the green boy. **The tail is the wedge that is BALLOON-coloured
  and continuous with the balloon fill; the decoys are sky-coloured.** That
  costs nothing to check and it is decisive at 2-3x.
- **AND ON THE FACING PANEL, THE TIP WAS RIGHT AND THE DIRECTION WAS READ
  BACKWARDS.** 095 p7's tail is a long wedge pointing down-LEFT at the
  green-banded boy; the pass put the tip in about the right place and then gave
  it to the head sitting under it. That is the same mechanism as *The Price of
  Fame* 077 g5, where the wedge points down-left at the red boy and the pass
  took the head beneath the tip. **Three of this batch's sixteen corrections are
  a tip in a gap given to the nearer head instead of the head the wedge points
  at** -- the roster rule already says the nearer head is not the answer, and it
  was broken three times in one batch.
- **THE `other:` VALUES HELD ACROSS 411 GROUPS.** No drift, no near-duplicates
  and no new singletons; the review added none of its own. The one to watch on
  a re-read is *Midgets Madness*'s `other:the judge` against
  `other:a second race judge` -- two men in identical brown jackets and JUDGE
  badges on 094 p5, separated only by the yellow cap.

**And the zero is worth as much as the 9.2%.** *Flour Follies* returned **0 of
122** because it has nine nephew groups in the whole title and dresses its
adults apart -- a bald moustached man in tails, a blonde in a green skirt,
Scrooge in red -- so every call rests on a tail into an unambiguous figure.
*Midgets Madness* put three boys, four separately-costumed adults and a
silhouetted crowd into the same frames and posted 9.2% with a 25.7% nephew
domain. **The rate tracks how much SEPARATING a title demands -- of nephews from
each other, of adults from adults, and now of nephews from the crowd behind
them.**

**Cost: 74 images over 30 pages, 2.5 per page**, against a target of 3 -- 3.1,
1.7 and 2.6 by title. Two of Flour Follies' were re-dos after coordinates were
eyeballed off a stacked strip rather than scaled from a census box.

### Findings to paste into the next run (2026-09-09, forty-second batch, all four titles reviewed and mirrored)

*Salmon Derby* and *Cheltenham's Choice* (Vol. 15), *Tralla La* and *Outfoxed
Fox* (Vol. 12). All four reviewed, mirrored, and at **every group reviewed on
both engines** -- the three one-group stragglers left open after the first
three reviews were all reviewed later and the reviewer **agreed with all
three**, changing nothing but the stamp.

```
                        real corrections      nephew domain          highs         mediums
Salmon Derby           2 of 122   1.6%      2 of  34   5.9%    2 of 119  1.7%    0 of  3
Tralla La             14 of 270   5.2%     12 of  38  31.6%   12 of 257  4.7%    2 of 13
Outfoxed Fox           8 of 119   6.7%      8 of  19  42.1%    8 of 119  6.7%    0 of  0
Cheltenham's Choice   19 of 144  13.2%     18 of  47  38.3%   18 of 141 12.8%    1 of  3
     batch            43 of 655   6.6%     40 of 138  29.0%   40 of 636  6.3%    3 of 19
```

**32 of the 43 are one class: a collective the review named.** Three run the
other way. The flag still ranks -- 15.8% of mediums corrected against 6.3% of
highs -- but 636 highs against 19 mediums means the pass hedged almost nothing,
and every one of the 32 under-namings was written `high`.

- **THE PRINTED BLOB LIST IS NOT THE ABSENCE TEST. THE COUNT IN THE BAND HEADER
  IS.** *Salmon Derby* 097 g13 was written `nephews` on an explicit "no red on
  any head" -- read off a `tail -18` of the census. The band header on that same
  run said `red: 18 blob(s)`, and the boy's band was 54px, below `capwide.py`'s
  **top-8-per-band print limit**. The absence was never in the data; it was in
  the view. `capwide` prints eight blobs and counts all of them: quote the
  `N blob(s)` header for every band, per panel, and never write an absence from
  a piped or truncated list.

- **`title_heads.py` IS A FLOOR ON THE FIGURES, NOT A CENSUS.** *Tralla La* 207
  g7 was given to Louie because "only one boy is in the panel" -- from
  `title_heads`, which needs a white skull and so cannot see a duck in
  silhouette. `capwide` on that panel returns `red: 3 blob(s)`, the largest 586px
  of clean `#e61b1f`. The review made it Huey. A head count that comes back
  low is a statement about skull pixels.

- **THE CORRECTIONS ARE ON THE PANELS THAT WERE NOT OPENED.** *Outfoxed Fox*
  is the clean experiment: **all 9 of its corrections fell on panels the pass
  never opened, and all 7 groups on panels it did open survived review.** It had
  the batch's lowest image spend and, of the first three titles, its highest
  correction rate. The image that is not spent is not saved; it is deferred to
  the reviewer.

- **ON THE FOURTH TITLE THE CAP INK WAS RIGHT IN BOTH DIRECTIONS AND THE TAIL
  REASONING WAS WRONG IN BOTH.** *Cheltenham's Choice* posted the batch's worst
  rate at 13.2%, and it splits cleanly: **12 of its 14 under-namings had a
  measurable band on a head that the pass declined** as too small, too far, or
  unseparated by a tail -- and **both of its over-namings named a boy off a clean
  band under a balloon with no tail at all**. The colour was never the thing
  that failed. What failed was treating a balloon's span as a tail, in both
  directions.

- **A SELF-CONTRADICTING NOTE IS A CORRECTION WAITING TO HAPPEN.** Three times
  in this batch the pass wrote the disqualifying sentence into its own note and
  then made the call anyway, and all three were reversed: *Tralla La* 194 g1
  ("a box over a figure is not a tail"), *Cheltenham's Choice* 115 g1 ("a
  balloon sitting over a figure is not a tail, which is why this is medium"),
  and *Tralla La* 204 g3, which cited a precedent giving `YE CATS` to Donald and
  then gave it to Scrooge. **If the note contains the reason the call is wrong,
  the call is wrong.**

- **THE H165-180 TEAL DOES NAME SOMEBODY -- AMEND THE PREVIOUS ENTRY.** The
  section committed the day before recorded a recurring teal at H165-180 as ink
  that "names nobody". *Cheltenham's Choice* 113 g5 has exactly two bands, red
  `#e51a20` H358.2 and teal **`#07a29f` H178.8**, and the review named **Dewey**
  off the teal. On 115 g1 the left boy's **`#2fa37c` H159.8** stood against a
  clean `#4da33f` H111.6 and the review declined to take the green, making the
  group collective. **The cool band is a shaded roster cap, not a decoy.** Treat
  H160-180 on a crown as a desaturated Dewey blue or Louie green to be resolved
  by a crop -- not as ink belonging to nobody.

- **ONE TITLE PRINTED LOUIE'S BAND ACROSS FOUR DIFFERENT GREENS.**
  *Cheltenham's Choice*: H128 on 107 p4, H123 on 108 p4, H111 on 110 p7, and
  **H147.7** on 111 p7 -- the last being the volume's own foliage green, and
  still unmistakably a broad band on a black crown. A per-title green measured
  once from a reference panel is a starting point, not a filter.

- **WORTH A RE-READ: *Cheltenham's Choice* 112 p8.** The panel carries two
  bands, green `#4da33f` H111.6 at 139px and blue `#07a4d4` H194.0 at 133px. The
  review named **Dewey** -- the blue boy -- but stamped `cap_colour: green`. The
  name and the recorded ink disagree under the volume's own convention.

- **REGISTER REASONING LOST AGAIN, TO AN ANIMAL.** *Cheltenham's Choice* 113
  g13, `Donald -> other:the mynah bird`. The note argued the insult was
  "affectionate and it is his own thought that follows" -- about a talking bird
  that has its own balloons on five other groups in the same title.

- **A COSTUME KEY WAS OFFERED AND REJECTED, AND IT WAS REAL.** *Tralla La*
  198/199: the pass considered red/green/yellow flying suits as a per-boy key
  and rejected it. The reviewer's note reads **"Yellow costume for Dewey"**.

- **MISSED TEXT: 3 items in 52 pages**, and two of them are bare punctuation
  devices over a figure -- *Salmon Derby* 102 g14 `! ! !` over three boys in a
  panel never opened, and *Outfoxed Fox* 214 g12 `$ $ $` over Donald digging.
  The third is *Tralla La* 200, where the review split one group into its two
  sentences and gave the second to Louie. **The missed-text audit sweeps
  `visible_text` the pass itself wrote, so it cannot catch a device the pass
  never listed.** A wordless panel still needs the panel opened.

- **TEXT CORRECTIONS REACH NO QUEUE.** All 4 were written straight into
  `ai_text` with `text_ok` and `corrected_text` both null: `So-` -> `SO —`
  (*Salmon Derby* 097 g11), `---` -> `...` (105 g1), `So!` -> `SO!` (*Tralla La*
  190 g7), and `MILLIONS OF SHEKELS'` -> `MILLIONS OF SHEEP'S` (205 g13). Two of
  the four are the same fault: a lowercase-plus-hyphen rendering of a shouted
  capital and a dash. Diff `ai_text` against the pass commit at close-out;
  `vision-corrections` will report nothing.

- **TYPE: 0 CORRECTIONS, AND THE TOOL SAYS 13.** Every group carrying
  `type_was` in this batch was the pass's *own* retype, ratified by the review
  -- `type` unchanged, only `type_reviewed_date` stamped.
  `review_findings.py --since` filters on that date, so an agreement and a
  correction look identical in its "type corrections" list. **Read `type`
  against the pass commit before quoting that number.**

- **`barks-ocr-name-grep` CANNOT SEE A NEPHEW NAME**, reconfirmed: it reports
  only non-dictionary tokens, so `QUICK, DEWEY!` (*Tralla La* 196 g5) never
  surfaces. Read the addresses by eye at prep. The Vol. 12 `UNCA SCROOGE`
  (a nephew) against `UNCLE SCROOGE` (Donald) split held on every occurrence in
  both Vol. 12 titles.

**Three kinds of call should stop being written `high`:** one backed by an
absence, one made collective because no tail separated boys whose bands were
measured, and any call on a panel that was not opened. All three are
represented above, all three were reversed, and all three were `high`.

### Findings to paste into the next run (2026-09-09, forty-third batch, three of four titles reviewed)

All four titles are now reviewed and mirrored. *Travelling Truants* 5
corrections in 138 (3.6%), *Rants About Ants* 9 in 120 (7.5%), *The Seven
Cities of Cibola* 52 in 446 (11.6%), *Million Dollar Pigeon* **0 in 42**.

**Medium is not a hedge, for the third batch running.** By the confidence the
pass wrote: Truants 25.0% of mediums corrected against 3.0% of highs, Cibola
34.4% against 7.3%. Rants About Ants is the exception that proves it -- 0 of 5
mediums, 7.0% of highs -- and it had only five. A medium is a coin flip on
Cibola. Spend the crop instead of writing one. Cibola's last remaining medium,
012 g12, was corrected too, in the straggler pass: `nephews` -> Donald on a
panel whose own note says heads.py found two overlapping red-carrying heads.
**On an unreadable panel the collective is not the safe answer either** -- the
hedge was wrong in the direction of naming no nephew at all.

**Count the review's own added groups out before reading a correction rate.**
Eleven of Cibola's 52 are a group whose `speaker_was` is `unknown` -- a group
the REVIEW added, going to its real value (four `$` devices to Scrooge, shirt
plates to `none`, 012 g10 to Louie). Those are not pass errors. Thirteen of the
52 sit on a `vision_added` group. The real figure is **41 genuine pass errors
in 446, 9.2%**.

**Million Dollar Pigeon is the control.** Forty-two high-confidence speaker
calls, none overturned, on a four-page title with no nephews in it and two
speakers drawn as humans. Its one correction is the review's own added group.
The titles that cost corrections are the ones with three identical boys in
them, not the ones with unusual casts.

- **AN ADDRESS OUTRANKS A CAP, AND THE `UNCA` / `UNCLE` SPLIT IS AN ADDRESS.**
  See the Vol. 14 palette entry below: the split held 11 for 11 on Cibola, and
  the one group the previous run cited as a counter-example, 012 g1, was the
  pass's own error. Grepping `ai_text` for UNCA and UNCLE before page 1 would
  have caught it for free. **The rule the previous run wrote down was inferred
  from a correction it had not yet had reviewed** -- do not write a palette
  entry off a single unreviewed group.
- **PRESENCE IS NOT ATTRIBUTION: DONALD'S SAILOR CAP TOOK SEVEN LINES OFF THE
  BOYS.** Cibola corrected `Donald` -> the nephew domain seven times, five of
  them to Dewey, and the pass note on nearly every one names the sailor cap
  hex as the reason -- `#04a3d6` on 011 g2, `#01a5d6` on 013 g2, `#02a4d5` on
  014 g11. Finding Donald in the panel is not evidence that the balloon is his.
  Every one of those notes describes locating Donald and none of them describes
  tracing the tail to him.
- **THE LONG-SHOT DEFAULT IS DONALD, AND ROLE REASONING STILL BEAT IT FIVE
  TIMES.** Cibola corrected `Scrooge` -> `Donald` on 011 g1, 011 g3, 014 g11,
  023 g2 and 024 g7, and `nephews` -> `Donald` on five more. The pass notes say
  things like "given to Scrooge -- the ship is his find and the bafflement is
  his": that is who-would-say-this, on a panel where the art was not readable.
  On an unreadable long shot in a Scrooge story the answer is still Donald.
- **A CAPSCAN ZERO DID NOT STOP THE REVIEWER NAMING THE BOY.** Seventeen
  `nephews` -> a name across the two nephew titles (10 Cibola, 7 Ants), every
  one of them `cap_colour` null -> a colour, and the pass note on most says the
  scan found nothing: "heads.py finds no cap ink", "title_bands gives red=0".
  Ants 128 g0/g1/g2 are the sharpest case -- the pass wrote "the boys are
  BARE-HEADED again on this page" and declined all three; the review named all
  three. **Bare-headed is a fact about the ink, not about the boy.** Place them
  by tail and reading order and name them.
- **A NOISE IN A BALLOON IS `dialogue` EVEN WHEN THE MAKER IS A SWARM.** The
  review retyped all five of Rants About Ants' `ZZT!` groups (129 g5, g6, g7,
  g11 and 134 g4) from `sound_effect` to `dialogue`. The pass had already given
  them `other:the ants` as speaker and then left the type alone, reasoning that
  the noise is one their own bodies make. The speaker rule and the type rule
  are independent: a tailed balloon is a voice, whatever is making it.
- **A THREE-BALLOON CASCADE CAN SLIDE BY ONE, AND THE CAP ROW WILL NOT SAY SO.**
  Truants 124 is the whole title's error: the pass read the caps in the truck
  interior "left to right blue / red / green" and named g8 Huey, g9 Louie,
  g17 Louie; the review made them Dewey, Huey and `nephews`. Three of the
  title's five corrections are that one panel, offset by exactly one. This is
  the Vol. 4 offset fan in another volume -- when a cascade's names come from a
  row of caps rather than from traced tails, flag the whole fan as a set.
- **THE REVIEWER ADDS BARE DEVICES, AND THE PASS NEVER DOES.** Six groups
  added across this batch are a lone `$`, `?` or `? ?` in its own balloon --
  four on Cibola, one on Million Dollar Pigeon 037, one on The Strange
  Shipwrecks 033. Neither engine groups them and the pass did not propose one
  of the six. They are speech: a device in a tailed balloon takes the thinker
  and the `thought` type. Look for them on any panel where a character reacts
  without words.
- **A REVIEW CAN LEAVE A GROUP IT ADDED HALF-ANNOTATED.** Cibola 018 g21
  arrived at `unknown` / `low` with no `identified_by` and no note, while its
  three sibling Beagle Boy shirt plates were `none` / high. It was caught only
  because it showed up in the unreviewed queue. **List every `vision_added`
  group with an empty note before mirroring** -- the mirror copies those fields
  onto the other engine.
- **THE OFF-BY-ONE STRAGGLER IS CORPUS-WIDE, NOT PER-TITLE.** A sweep with
  `barks-ocr-speaker-queue --unreviewed` and no `--title` found seven groups
  across six titles that had each been called review-complete, in Vols. 2, 4,
  6, 9, 12 and 22. Six of the seven were confirmations -- the calls were right
  and the stamp was never applied -- so the cost is provenance, not accuracy.
  Run that sweep at the end of a batch, not the per-title check.
- **SPEAKER VALUES OUTSIDE THE CLOSED SET ARE IN THE CORPUS AT SCALE.** 936
  groups carry a bare character name with no `other:` prefix -- `The Beagle
  Boys` 306, `Gneezles` 102, `Neighbor Jones` 98, `Goldie O'Gilt` 72 and
  thirteen more, across nine volumes. `roster.txt` says anyone outside the
  closed set goes behind the prefix, and `vision_apply` enforces that on what a
  PASS proposes; nothing enforces it on what a review writes. This is not from
  this batch and it is not a thing to sweep on sight -- it needs a decision
  about which side is right first.
- **THE MISSED-TEXT AUDIT CANNOT SEE A MISSED BALLOON.** The review added a
  whole spoken group to Cibola 012 -- Louie's "AND THIRSTY, TOO! HOW I WISH WE
  HAD THAT CANTEEN OF WATER!... (GASP!)" -- that neither engine grouped and the
  pass never noticed. The audit diffs `visible_text`, which by definition holds
  only NON-speech lettering, so a balloon nobody boxed is invisible to it and
  to every count in the close-out. The only thing that finds one is reading the
  page and counting balloons against groups.



### Findings to paste into the next run (2026-09-09, forty-fourth batch, ALL FOUR REVIEWED AND MIRRORED)

Replaces the pass-only numbers in the section below it. Four Vol. 15 titles,
40 pages, 500 groups after four review adds. **35 genuine speaker corrections
in 500 = 7.0%** -- but **33 of the 35 are in the nephew domain, which is 33 of
151 = 21.9%**, twice the reviewer's stated tolerance:

| title | groups | nephew domain | named | corrections | rate |
|---|---|---|---|---|---|
| Too Safe Safe | 116 | 3 | 0 | 2 | 1.7% |
| Search for the Cuspidoria | 125 | 30 | 19 | 9 | 7.2% |
| New Year's Revolutions | 134 | 77 | 46 | 17 | 12.7% |
| Iceboat to Beaver Island | 125 | 41 | 25 | 7 | 5.6% |

**The rate is a function of nephew density and nothing else** -- 3, 30, 77 and
41 nephew groups against 1.7%, 7.2%, 12.7% and 5.6%. Everything outside that
domain was right: two corrections in 349 non-nephew groups.

- **WRITING EVERYTHING `high` WAS A MISTAKE, AND NOT THE ONE THE LAST THREE
  BATCHES WARNED ABOUT.** Acting on "medium is not a hedge", this batch wrote
  **no medium or low anywhere in 500 groups** -- and then 21.9% of the nephew
  domain was wrong. Confidence carried no information at all, so a reviewer
  could not triage by it and had to check every call. The finding those
  batches actually support is *spend the crop instead of writing a medium*,
  not *write high regardless of what the crop showed*. **A tip that lands in a
  gap, a tail-less balloon resolved by ordering, and a fan read against
  reading order are all still `medium`** -- they are exactly the three shapes
  that were reversed here.
- **THE TIP IS NOT WORTH WHAT THIS BATCH PUT ON IT.** Of the 35, **eleven** are
  a name the pass measured a tail onto: 6 over-namings (a name -> `nephews`)
  and 5 of the 7 attribution swaps. Every one has a pixel margin written into
  its note. Against that, 14 are under-namings the review named off the cap row
  with no tail at all. **The cap row outperformed the traced tip in both
  directions in this batch.** When a panel's caps read cleanly left to right,
  rank the balloons against the caps FIRST and use the tip only to break a tie.
- **A FAN IS EVERY BALLOON IN THE PANEL, NOT THE ONES THAT LOOK LIKE A SET.**
  Cuspidoria 151 p3 has five balloons over three boys; the pass treated the
  three cry balloons as a closed fan, found one tip in a gap, invoked the
  offset-fan rule and used reading order. The review used the measured tips --
  which is what the pass's own crop had already said -- and the two upper
  balloons took the remaining boys, so nobody was skipped. **Count the
  balloons before deciding a boy has been skipped.** Four of that page's five
  groups were corrected.
- **"NO CAP INK IN THE PANEL" IS NOT A REASON TO DECLINE.** Ten of the 14
  under-namings are New Year's Revolutions, seven of them on page 159 alone,
  where the pass wrote *three specks in the distance*, *the head census finds
  no cap ink in the panel at all*, and *the boys are packed at the left*. The
  review named all seven. On a title whose caps are the easiest in the volume,
  a census miss is a threshold, not an absence -- probe the crowns.
- **A LONE BLUE-CAPPED DUCK IS NOT DONALD, TWICE IN ONE BATCH.** Cuspidoria
  147 g9 and Iceboat 167 g5 both went `Donald` -> `Dewey`. Both notes say
  "Donald alone" / "Donald pointing", and both titles' own palette entries --
  written by the same pass -- say Donald's cap prints the nephews' blue. Size
  the head before writing the name; the ink cannot do it.
- **THE PASS MISSED THREE PIECES OF LETTERING OUTRIGHT, AND THE AUDIT COULD
  NOT HELP.** The review added `WINK WINK` inside the signal-lamp flash
  (Cuspidoria 154), `POOF` lettered in flame shapes (Iceboat 173) and `ZOW` in
  the snow spray (Iceboat 174). None was in any page's `visible_text`, so the
  diff had nothing to compare. **Sound effects drawn INTO the art -- inside a
  flash, a flame or a spray, in the shape of the thing -- are the class the
  pass reads past.** Look for them wherever a panel has a burst.
- **AND IT MISSED TWO MORE DEVICES OF A CLASS ALREADY IN THE FINDINGS.**
  Cuspidoria 152 g3 is thirteen drawn dollar signs round Scrooge's head; the
  pass described them in the neighbouring group's note and did not box them.
  That is the third batch running for "the reviewer adds bare devices and the
  pass never does". The one the pass DID add -- Too Safe Safe 141's bare `?` --
  was confirmed unchanged, so the fix works when it is applied.
- **`review_findings --since` OVER-REPORTS THREE DIFFERENT WAYS.** Raw output
  said 13 / 17 / 9 / 3; the true figures are 9 / 17 / 7 / 2. Three causes,
  all worth knowing:
  1. **A review's own added groups** count as corrections, `unknown` -> their
     value. Six across the batch.
  2. **An added group renumbers the page**, and `--since` diffs by id, so a
     stale field on a shifted group reads as fresh. Cuspidoria 152's single
     "type correction" was a 2026-08-15 adjudication that moved from g5 to g6.
  3. **A ratification looks exactly like a correction.** Iceboat 169 g13/g14
     were already `dialogue` at the pass commit; the review only stamped
     `type_reviewed_date`. Same shape as the forty-third batch's 13.
  **Real type corrections across the whole batch: zero.** Check `type` against
  the pass commit before quoting any type number.
- **THE OFF-BY-ONE STRAGGLER IS CAUSED BY THE ADD.** Two titles finished one
  group short, and in both the straggler was the last id on the one page that
  had gained a group -- Cuspidoria 152 g9, Too Safe Safe 145 g10. Titles with
  no adds (New Year's Revolutions, Iceboat) finished complete. Check the pages
  that grew, not the whole title.
- **A `text_ok: true` WITH THE PROBLEM IN ITS OWN NOTE.** New Year's
  Revolutions 157 g10 stored `CAT RAT`; the pass cropped it, wrote *"the final
  T of RAT is partly hidden behind an arm"* into the note, and marked
  `text_ok` true instead of proposing `corrected_text`. The review retyped it
  `CAT RA`, which then raised a near-miss the ignore list cannot suppress,
  because the page's `visible_text` still claimed the T. Both are fixed. The
  measure-then-vote-against error is not confined to the speaker field.
- **CORPUS SWEEPS AFTER ALL FOUR MIRRORS.** `vision-corrections` with no
  title: **2 outstanding across 460**, both the forty-third batch's `CAFE` ->
  `CAFÉ` on Cibola 017. `speaker-queue --unreviewed --confidence low,medium`
  with no title: **9 across three already-reviewed titles**, unchanged --
  Sheriff of Bullet Valley 5, The Big Bin on Killmotor Hill 2, The Victory
  Garden 2, in `~/barks-vision/queue-corpus-lowmed-2026-09-09.txt`.


### Findings to paste into the next run (2026-09-09, forty-fourth batch, PASS ONLY -- not yet reviewed)

Four Vol. 15 titles, 40 pages, **493 groups**: *Too Safe Safe* 116, *Search for
the Cuspidoria* 121, *New Year's Revolutions* 134, *Iceboat to Beaver Island*
123. Every speaker call is `high`; **not one medium or low was written in the
whole batch**, which is the previous three batches' finding acted on. The
review will say whether that was earned.

Nephew domain and how much of it got named:

| title | nephew groups | named | collectives |
|---|---|---|---|
| Too Safe Safe | 3 | 1 (33%) | 2 |
| Search for the Cuspidoria | 29 | 14 (48%) | 15 |
| New Year's Revolutions | 77 | 40 (52%) | 37 |
| Iceboat to Beaver Island | 40 | 26 (65%) | 14 |

- **THE CHEAPEST THING IN THIS BATCH WAS A STACKED TAIL-BAND CROP.** Nearly
  every name above came from one `stack.py` image carrying three or four
  narrow strips -- the band between a panel's balloons and its heads, at
  1.5-1.7x -- read against the head spans `title_heads.py` had already
  printed. One image settled a whole page. The batch ran **2.6 images per
  page** and named 81 of 149 nephew groups. Crop the BAND, not the panel:
  a strip from the balloon bottoms to the tops of the caps is where every
  tail lives and it costs a fifth of a panel view.
- **COUNT THE TAILS BEFORE NAMING, BECAUSE A "WE" LINE USUALLY HAS THREE.**
  Every `WE`/`OUR` line in this batch that I checked turned out to hang one
  tail per boy: *New Year's Revolutions* 157 p1, p4 and p5, *Cuspidoria* 147
  p1, *Iceboat* 171 p7, 173 p4, 175 p5 and 168 p8. Those are choruses and
  stay `nephews` -- but the same crop is what names the single-tail balloons
  beside them, so it is never wasted. **A three-tail balloon is not the same
  finding as a crowded fan**; it is the art saying all three.
- **A FAN OFFSET BY A CONSTANT IS STILL READABLE.** Twice the tips landed
  short of their boys by the SAME amount -- *New Year's Revolutions* 158 p2
  (66px and 61px left) and *Iceboat* 174 p2 (50px and 46px left) -- and in
  both the offsets matching to within 5px is what made the mapping safe.
  Measure every tip in the fan before deciding it has slipped: a consistent
  offset names them, a ragged one does not.
- **DONALD WORE A NEPHEW INK IN THREE OF THE FOUR TITLES.** His sailor cap is
  `#00a5d7`/`#02a5d5` -- Dewey's exact band -- in *Too Safe Safe* and
  *Cuspidoria*, he wears a blue winter cap in *New Year's Revolutions*, and in
  *Iceboat* he wears a **maroon `#a04453` coat**, which is the ink Scrooge's
  coat prints elsewhere in the volume and is the largest red on most of those
  pages. Scrooge's top-hat band is `#04a4d5` in *Cuspidoria*. **On this volume
  the largest blob of a roster colour is an adult's about as often as a
  nephew's** -- size the head first, every time.
- **TWO BLUE CAPS IN ONE PANEL IS A REAL CONFIGURATION.** *New Year's
  Revolutions* 162 p2 has a blue-capped nephew in the foreground and a small
  blue-capped figure on the slope, and the story's own logic (Louie is away
  all afternoon) is the only thing that makes the second one Donald. Flagged
  in the note; it is the batch's most likely wrong call.
- **`leafgrn: 0` MEANT NOTHING ON ANY OF THE FOUR.** *Cuspidoria*'s band sweep
  returns leafgrn 0 on 72 of 77 panels and the head census still finds clean
  `#4da23f` H111 caps on 147 p5 and 150 p8. Probe the crown; do not read the
  band totals as an absence.
- **ONE TITLE PRINTS ITS CAP GREEN AT TWO HUES.** *Cuspidoria* gives `#4da23f`
  H111 on 147 p5 and 150 p8 but `#3c907b` **H165.0 S0.58** on the splash --
  inside the H165-180 dead band the Salmon Derby entry says to give up on. It
  was resolvable only by elimination against the clean blue and red beside it
  in the same row. Record the printed hex and say the call was made that way.
- **THE CAPS COME OFF INDOORS, AND THAT IS MOST OF THE COLLECTIVES.** All 37
  of *New Year's Revolutions*' collectives are indoor pages (160 entire, 161
  p1-p3, 164 p2-p8, 165) plus two silhouette panels; *Iceboat* 168 p3-p7 is
  the same. Say in the note which it is -- nothing printed, versus a cap
  declined -- because the two look identical in a queue.
- **A TITLE CAN NAME THE BOYS IN ITS OWN CAPTION.** *New Year's Revolutions*
  161 p5 reads **"HUEY AND DEWEY GO TO WORK!"** over the pair doing the ski
  tricks, and 161 p3 / 164 p2 name Louie in dialogue. That settled about
  fifteen groups for nothing. Grep the narration boxes for HUEY/DEWEY/LOUIE
  at prep alongside `name-grep`, which still cannot see them.
- **A DEVICE OVER A GROUP IS STILL COLLECTIVE, AND THE PASS SHOULD ADD IT.**
  Added one group this batch -- a bare `?` in a thought bubble over Donald on
  *Too Safe Safe* 141 p1, which neither engine had. The reviewer-adds-devices
  finding from the forty-third batch is acted on; keep looking on any panel
  where somebody reacts without words.
- **THE MISSED-TEXT AUDIT MISSED BOTH OF THIS BATCH'S REAL FINDINGS.** The
  mailbox on *Too Safe Safe* 140 p1 reads `DON` / `DU`, cut off by the panel
  frame, and `DON` is a substring of the DONALD already grouped on that page,
  so the diff cleared it. `CUSPIDORIA` lettered along the wreck's hull on 155
  p7 is the second-copy blind spot -- the same string is in the caption above
  it. **Both are in the hand-back by hand.** A short or duplicated string is
  invisible to the audit by construction; read the panel.
- **`CUSPIDORIA` IS SET IN ITALIC EVERY TIME IT APPEARS** (149 g8, 152 g2/g6,
  153 g1, 155 g0/g13). `allbold.py` measures stroke width and cannot see
  slant at all, so a story's italicised proper noun has to be caught by eye
  off the montage and then confirmed with one crop.
- **THE BOLD CUT ON THIS VOLUME IS ABOUT 1.15, NOT 1.3.** Confirmed by crop
  three times: `JOBS!` measured **1.16**, `TOO` **1.28** and `FIFTY` **1.30**
  and all three are plainly bold. And `allbold`'s word-to-blob pairing is
  wrong often enough to matter even on a line it marks `=`: on *Too Safe Safe*
  140 g10 it put 1.47 on STRONGER when the crop shows **WAX** is the bold word
  and STRONGER is not.
- **A SHIVER IS A VOICE.** Two type corrections, *Iceboat* 169 g13/g14 `BRR!`
  from `sound_effect` to `dialogue`, because the identical lettering on 170 is
  already stored as dialogue and because a shiver comes out of a body. The
  rats take it as speaker; their `CHOMP!`/`GNAW` stay `sound_effect` with the
  rats named, which is the Going Buggy boundary.
- **CORPUS SWEEPS, RUN AT THE END OF THE BATCH.** `vision-corrections` with no
  title: **6 outstanding across 460 titles** -- this batch's 4 (169 g13/g14 on
  both engines) plus 2 from the forty-third, `CAFE` -> `CAFÉ` on *The Seven
  Cities of Cibola* 017 g1. `speaker-queue --unreviewed --confidence low,medium`
  with no title: **9 groups across three already-reviewed titles** -- *Sheriff
  of Bullet Valley* 5, *The Big Bin on Killmotor Hill* 2, *The Victory Garden*
  2 -- written to `~/barks-vision/queue-corpus-lowmed-2026-09-09.txt`.


### Findings to paste into the next run (2026-09-10, forty-fifth batch, ONE OF FOUR REVIEWED -- *The Tuckered Tiger*)

Replaces that title's numbers in the pass-only section below; Stone Ray,
Campaign of Note and Daffy Taffy Pull are still unreviewed. **15 genuine
speaker corrections in 125 passed groups = 12.0%**, and **14 of them are in
the 23-group nephew domain = 60.9%** -- nearly three times the forty-fourth
batch's 21.9%, and in the opposite direction.

| direction | n | what it was |
|---|---|---|
| `nephews` -> a name | **12** | collectives the review named, every one with a cap_colour it filled in |
| nephew domain -> Donald | 2 | 098 g13, 100 g11 |
| `nephews` -> `other:` | 1 | 101 g6, a bystander |

- **THE ERROR CLASS FLIPPED, AND OVER-CORRECTING IS HOW.** The forty-fourth
  batch was punished for naming too much at high; this pass was punished for
  naming too little. **Twelve of fifteen corrections are under-namings**, and
  ten of those twelve carry the same sentence in the pass's own note -- *"his
  wedge does not read in this panel"*, *"neither wedge reads here"*, *"their
  wedges do not separate at this size"*. The review filled in a cap_colour for
  **every one of them**. The wedge did read; the pass ran the per-panel census,
  got nothing at that head, and declined instead of cropping. **A census miss
  on a small-cap construction is an instruction to spend a crop, not a reason
  to write `nephews`.**
- **THE IMAGE BUDGET HAS A FLOOR AS WELL AS A CEILING, AND THIS IS THE
  MEASUREMENT.** The title ran **1.1 images per page** against a target of 3,
  on a construction whose readable ink is 130-720px and with 27 nephew groups
  in ten pages. That underspend bought twelve wrong collectives. `docs/vision-pass-cost.md`
  is about not exceeding 3; the other half is that a cap-dense title read at
  1.1 has not been read. **Budget by nephew density, not by page count.**
- **`nephews` IS NOT A SAFE HEDGE EITHER.** The confidence field carried almost
  nothing again -- high 13 of 118 corrected (11.0%), medium 1 of 6 (16.7%) --
  but the reason is new: the pass avoided a wrong name by writing a collective,
  which is not a confidence at all and which the review then had to redo
  twelve times. A `nephews` on a panel whose caps are actually readable costs
  the reviewer exactly what a wrong name does.
- **AN ELIMINATION CHAIN CAN BE INTERNALLY SOUND AND REST ON A WRONG FIRST
  LINK.** 103 g1 was declined with the reasoning *the outer two boys read blue
  and green, so the middle one -- the one holding the open book the line is
  read from -- is Huey*. The review named it **Louie**: the speaker is the
  right-hand green boy, not the book-holder. The elimination was fine; the
  premise about who was speaking was not. **Check the premise of an elimination
  before checking its arithmetic.**
- **A 1557px RED BLOB ON A BENT-OVER FIGURE WAS DONALD'S BOW TIE.** 100 g11 was
  named Huey at medium off *a cap seen from above with the RED wedge*; the
  review says Donald. Donald's bow tie is roster red and about that size, and a
  duck bent over a stall plate puts it exactly where a crown would be. This is
  the blob-must-sit-on-a-head error with a new disguise -- and it is the one
  correction the medium flag actually earned.
- **DONALD WAS IN THE PANEL AND THE PASS DID NOT COUNT HIM.** 098 g13 went
  `nephews` -> Donald on a line that is plainly an adult's (*WHY DON'T YOU GO
  OVER TO THE COMMITTEE ROOM AND BUILD THIS UP BIG?*). Count the adults in
  frame before assigning a balloon to the boys.
- **TWO STACKED BALLOONS OVER TWO BOYS WERE MAPPABLE AFTER ALL.** 098 g10/g11
  were declined because *neither tail could be traced*, with both wedges
  already read as blue (near, left) and red (behind, right). The review mapped
  upper -> the near blue boy and lower -> the far red one. Recorded as an
  outcome, not promoted to a rule: reading order is still not evidence, but
  declining a pair whose caps you have already read costs two names.
- **ZERO REAL TYPE CORRECTIONS, AND `review_findings` REPORTED FIVE.** All five
  -- 099 g3 and 106 g1/g3/g7/g8 -- are the pass's own, **ratified**: the type
  value is byte-identical before and after and only `type_reviewed_date`
  moved to 2026-09-10. The sixteenth "speaker correction" is likewise the
  review's own added group, `unknown` -> Scrooge. That is the forty-fourth
  batch's over-report, twice, on the same title. **Diff the type against the
  pass commit before quoting any type number**, and subtract the review's adds
  from the speaker count.
- **THE MISSED-TEXT HAND-BACK WAS ACTED ON AND THE AUDIT IS NOW CLEAN.** The
  reviewer added 098 g15 `$ $ $ $` on both engines -- the drawn dollar signs
  the audit could not see, listed by hand in the hand-back. It came in with its
  own text and an empty `notes`, no seeded residue, and was appended at the
  page's last id so nothing renumbered. **Listing a bare device by hand works;
  keep doing it.**
- **MIRROR AND CLOSE-OUT.** The reviewer worked easyocr only (126/126 there,
  1/126 on paddleocr, the one being the add). `vision-mirror --write` copied
  126 groups and 55 emphasis runs across; both engines then match on group
  count, reviewed count, `identified_by` count and the speaker, `cap_colour`
  and confidence distributions. `vision-corrections --title`: nothing
  outstanding. `closeout.sh --stage review`: all gating checks clean.
- **ONE `other:` VALUE TO WATCH.** The review introduced `other:a bystander`
  (101 g6) alongside the pass's `other:the crowd` (102 p6). They are different
  -- a single silhouette beside Scrooge against a row of named faces -- but
  they are the kind of pair that drifts into duplicates. Grep the singletons
  before the next mirror on this volume.


### Findings to paste into the next run (2026-09-10, forty-fifth batch, SECOND OF FOUR REVIEWED -- *The Daffy Taffy Pull*)

Replaces that title's numbers in the pass-only section below; Stone Ray and
Campaign of Note are still unreviewed. **12 speaker corrections in 129 passed
groups = 9.3%** -- and all twelve are the same mistake, on a class that was
therefore **100% wrong**. Nothing else was corrected: no types, no cap_colours,
one text fix (`DOC!....` -> `DOC! ....`), and seven text_boxes tightened.

| class | groups | corrected |
|---|---|---|
| quoted flashback captions | 12 | **12 (100%)** |
| nephew domain (Huey/Dewey/Louie/`nephews`) | 18 | **0** |
| everything else | 99 | 0 |

- **A QUOTED FIRST-PERSON CAPTION IS STILL THE NARRATOR.** The whole story is a
  framed flashback: Donald in a psychiatrist's office on 176 and 185, the tale
  in between. Every flashback caption is Donald's own voice in quotation marks
  -- `"I STARTED THE KIDS ON THEIR WAY!"`, `"THE TOWN CRANK HAD BOUGHT IT!"` --
  and I wrote `Donald` on all twelve. The field records **the box**, not the
  voice quoted inside it. This rule was already written down and I broke it
  twelve times in one title, because first-person quoted text reads as speech
  in a way third-person narration never does.
- **THE TELL IS THE FRAMING DEVICE, AND IT IS VISIBLE ON PAGE 1.** A story that
  opens on a character recounting events and closes back in the same room is
  narrating the middle. Check the last page at prep: if it returns to the
  opening scene, every caption between them is `narrator` no matter whose voice
  it quotes. That single check would have caught all twelve here for one image.
- **THE NEPHEW DOMAIN TOOK ZERO CORRECTIONS**, 18 groups including 7 held as
  the `nephews` collective. Vol. 15's palette held: `#e51a20` / `#4da33d` /
  `#00a5d7`, clean bands, and the two collectives that stayed collective were
  right to. The forty-fifth batch's *Tuckered Tiger* section above was punished
  60.9% in this domain on a wedge-cap title at 1.1 images per page; this title
  is the control, and the difference is that its caps are legible.
- **THE SPEAKER FIX LEFT THREE TYPES BEHIND, AND TYPE IS A SEPARATE QUEUE.** 176
  g8, 176 g11 and 182 g1 were moved to `narrator` while keeping the pass's
  `dialogue`/`dialogue`/`thought`, because a review corrects speakers and types
  through different paths and this one corrected no types. Resolved the same day:
  all three are now `narration`, so all twelve agree. **The lesson is for the
  pass, not the review** -- mistyping a caption box and misattributing it are the
  same error surfacing in two fields, so a `narrator` correction should always
  prompt a look at the type. Nine of the twelve were already `narration`, which
  is exactly why the three stood out only on a cross-field check.
- **A HAND-TWEAKED BOX BREAKS THE `--fix-boxes` INVARIANT.** After `--fix-boxes`
  all 129 pairs held identical boxes on both engines; the review tightened seven
  and they now differ again, at IoU 0.898-0.996. None is reportable and nothing
  downstream cares, but a later `--fix-boxes` run will merge them back to the
  union of the two hand edits, which is slightly larger than either.

### Findings to paste into the next run (2026-09-10, forty-fifth batch, THIRD OF FOUR REVIEWED -- *A Campaign of Note*)

Replaces that title's numbers in the pass-only section below; only *The
Mysterious Stone Ray* is still unreviewed. **1 speaker correction in 53 passed
groups = 1.9%**, the cleanest title of the batch by a wide margin, and the whole
of it is one balloon.

| | |
|---|---|
| 070 g2 `AND THE ELECTION IS TOMORROW!` | `Louie` / `cap_colour: green` / medium -> **`Huey` / `red` / high** |

- **I WROTE `balloon-tail` IN `identified_by` AND THEN USED THE BALLOON'S SPAN.**
  Three nephews walk left to right across 070 panel 1 wearing blue, red and
  green. The balloon hangs at the top right, its x-span squarely over the green
  boy -- and its tail runs down and to the **left**, to the red one. I recorded
  both `balloon-tail` and `cap-colour` as the evidence, then named the cap that
  sat under the balloon. The review made it Huey and raised it from medium to
  **high**, so the tail was not ambiguous; I simply did not follow it.
- **MEDIUM WAS THE HONEST PART.** Every other call in the title was high and
  every one held. The one group I was unsure about is the one that was wrong,
  which is the confidence field working -- but the fix is to trace the tail, not
  to hedge. A `cap_colour` recorded off the balloon's span is worse than no
  `cap_colour`, because it dresses a guess as a measurement.
- **THE TITLE IS OTHERWISE A GOOD SIGN FOR SHORT ONES.** 53 groups over 4 pages,
  25 of them Scrooge, 7 held as the `nephews` collective and all 7 correct.
  Nothing was under-named and nothing over-named, which is the balance the
  forty-fifth batch's other two titles both missed in opposite directions.
- **ONE MISSED-TEXT FINDING, DECLINED.** 069's campaign banner is cut by the
  panel frame into CAN / CIT / WILL SP. Now in `missed-text-ignore.txt` with its
  reasoning, alongside Too Safe Safe 140's DON / DU: a truncated fragment has
  nothing for a searchable box to hold. It stays in 069's `visible_text`.

### Findings to paste into the next run (2026-09-10, forty-fifth batch, FOURTH OF FOUR -- *The Mysterious Stone Ray*, batch closed)

The batch's biggest title and its worst result. **40 speaker corrections in 365
groups = 11.0%**, and **30 of them fall in the 71-group nephew domain = 42.3%**.
Counted from the editor's own `speaker_was`, not from a text diff -- a diff keyed
on text collapses the duplicate Beagle Boy placards and undercounted this by ten.

| direction | n |
|---|---|
| `nephews` -> a name | **25** |
| `unknown` -> `none` / a name | 9 |
| `Huey` -> `nephews` | 2 |
| other single moves | 4 |

18 `cap_colour`s were filled in where the pass left them null.

- **THE BATCH RAN 42.3% AND 60.9% WRONG IN THE NEPHEW DOMAIN ON ITS TWO BIG
  TITLES.** *The Tuckered Tiger* was 60.9%, this is 42.3%, and both are the same
  direction: a collective the review resolved. Meanwhile *A Campaign of Note*
  took ONE correction in 53 groups and *The Daffy Taffy Pull* took none at all in
  its 18 nephew groups. The difference is not care, it is whether the caps are
  legible -- and 18 filled-in `cap_colour`s here say they were.
- **AN ADJUDICATED CONFLICT IS NOT A LICENCE TO DECLINE EVERYWHERE.** This is the
  title whose dialogue contradicted its printed caps, ruled mid-batch as *dialogue
  wins, record the ink*. That ruling covered a handful of groups. What actually
  happened is that the doubt spread: 25 collectives across 28 pages, on a title
  where the review could name them. Worse, the four `cap_colour`s it overturned
  were three `red`/Huey calls and one `blue`, two of which it pushed BACK to
  `nephews` -- so the same title was both over- and under-named. **Quarantine a
  palette conflict to the pages that show it.**
- **THE `unknown` GROUPS WERE THE OTHER NINE.** Six became `none` and three took a
  name. `unknown` was doing duty for "I did not look", which is what `none` and a
  named speaker are for; see the sound-effect entries above.
- **A SPLIT BOX SURVIVES BOTH TOOLS, AND THE IDS ARE A RED HERRING.** The review
  split 063 panel 8 into `CHEAP! CHEAP!` and `WITH THIS RAY...`; both engines got
  both halves with identical boxes, but on opposite ids (easyocr g14/g16,
  paddleocr g16/g14). Nothing broke: `ocr_check` pairs positionally within the
  panel and matched easyocr 16 to paddleocr 14, and `vision_mirror` keys on
  normalised `ai_text`, not on id. Had it keyed on id it would have written each
  half's annotations onto the other. `--fix-groups-order` afterwards lands both
  halves on g14 and the discrepancy disappears.
- **THE REVIEW'S OWN TRANSCRIPTIONS NEED THE AUDIT TOO.** It boxed the Beagle Boy
  placards on 050, 057 and 059 -- lettering neither engine had grouped -- and
  typed `176-671` on all three. The art reads `176-761`, the same glyphs as 052
  and 055 which it typed and stored as 761. A transposition across three
  near-identical placards in a row, caught only because the missed-text audit
  compares `visible_text` against the grouped text. 065's digits are behind a
  head and stay as typed.
- **THE QUEUE FILE HID A `text_does_not_fit` FOR THE SECOND TIME.** 043's six
  floating dollar signs were flagged all along, behind `groups_out_of_order` --
  the queue collapses to one entry per group and the most urgent issue wins. It
  only surfaced once the renumber cleared the entry above it. When a fix clears
  one issue, re-run the console listing rather than trusting the queue to be the
  whole story.

### Findings to paste into the next run (2026-09-10, forty-fifth batch, PASS ONLY -- not yet reviewed)

**ALL FOUR ARE NOW REVIEWED AND MIRRORED -- the four sections above replace every
number in this one.** Batch total: **40 + 12 + 1 + 15 = 68 speaker corrections**,
and the spread between titles is the finding: 1.9% on *A Campaign of Note* against
11.0% here, with the nephew domain running 0% and 42.3% on the two extremes.

Four titles, 52 pages, **663 groups**: *The Mysterious Stone Ray* (Vol. 14) 356,
*A Campaign of Note* (Vol. 14) 53, *The Daffy Taffy Pull* (Vol. 15) 129, *The
Tuckered Tiger* (Vol. 14) 125. **The Tuckered Tiger has since been reviewed --
see the section above, which replaces its numbers here.** **1.5 images per page**, against a target of 3
and a ceiling of 5; only one page went over, 042, at 6, and it is the title's
cap-reference page. Nephew domain and how much of it got named:

| title | nephew groups | named | collectives |
|---|---|---|---|
| The Mysterious Stone Ray | 96 | 34 (35%) | 62 |
| A Campaign of Note | 11 | 1 (9%) | 10 |
| The Daffy Taffy Pull | 26 | 14 (54%) | 12 |
| The Tuckered Tiger | 27 | 8 (30%) | 19 |

- **A TITLE CAN PAINT THE WRONG BOY, AND ONLY DIALOGUE CATCHES IT.** *The
  Mysterious Stone Ray* names its cast twice -- 053 g3 `STAY HERE AND GUARD
  THIS CROOK, HUEY!` leaves Huey on the beach, and 055 g3 has Scrooge call
  `DONALD! DEWEY! LOUIE!` over exactly three petrified figures -- and the art
  then gives the SURVIVING boy a clean H112 green band on 055/056 and a 1786px
  roster blue on 057 p5, and gives roster red to boys who by dialogue are Dewey
  or Louie. Three different inks on one boy in three consecutive pages. The
  reviewer's ruling was **dialogue wins, cap_colour records the printed ink,
  those calls sit at medium, and the disagreements go back as a retouch list**.
  Where a title has no naming line and its ink has already been shown to drift,
  `nephews` is the honest answer rather than the convention.
- **CHECK THE CONVENTION BEFORE TRUSTING IT, EVEN INSIDE A VOLUME.** Stone Ray
  and *The Tuckered Tiger* are the same volume and the same reference palette,
  and one tracks it and one does not. On Tuckered Tiger 098 p5 the three boys
  read blue, red, green in a row and every later panel agrees; on Stone Ray 042
  p3 they read red, blue, green in a row and the story then contradicts it. One
  clean reference panel is not a guarantee for the title -- it is a guarantee
  for that panel.
- **`leafgrn: 0` ON ALL 77 PANELS OF A TITLE STILL MEANT NOTHING.** *The Daffy
  Taffy Pull*'s whole-title `bands.txt` reads leafgrn 0 everywhere and I nearly
  wrote the title off as printing no cap green. `title_heads` finds 136px,
  163px and 181px of **#4ea340 H112** on Louie's crown on 182 p5, and Donald
  names him in the same panel. The band column's floor is simply above a wedge
  of a few hundred pixels. Quote `N blob(s) total` from the per-panel census,
  never the whole-title band sweep.
- **BARE-HEADED INDOORS IS A REAL, CHECKABLE FACT.** On Daffy Taffy the boys
  genuinely wear nothing on 176-179, which are all interiors, and put the bands
  back on outdoors from 181. That made every nephew group on the indoor pages a
  measured collective rather than a declined one, and it is the difference
  between "no band prints" and "I could not read the band".
- **THE CAP CONSTRUCTION IS PER TITLE AND IT CHANGES THE BUDGET.** Tuckered
  Tiger draws a black cap with a small coloured WEDGE at the side, so the
  readable ink is 130-720px even in close-up and only a stacked crop separates
  it. Stone Ray draws a narrow band that reads 35-700px. Neither is the broad
  crown band the Vol. 15 titles wear. Establish which one a title uses off the
  reference panel before deciding what a small blob means.
- **AN ADULT'S COAT COLOUR IS WORTH MEASURING ONCE PER TITLE.** Scrooge's coat
  is `#a04453` H350.2 maroon on *The Tuckered Tiger* and on *A Campaign of
  Note*, not the volume's roster red -- which is the opposite of the Vol. 14
  entry below and makes a clean `#e61b1f` blob on those two titles a nephew's
  wedge rather than his coat. On Stone Ray it IS the roster red, at 5,000-21,000px.
- **THE SEA CAN BE THE ROSTER BLUE.** On Stone Ray the water prints `#00a5d5`
  H193.5 S1.00 in blobs of 13,000px and up, the same ink as Dewey's band,
  Donald's sailor cap and Scrooge's hat band. Four things share one hex on that
  title; only area and position separate them.
- **THE UNCA/UNCLE SPLIT HELD 3 FOR 3.** Stone Ray 14 UNCA against 4 UNCLE,
  Tuckered Tiger 6 against 6, Campaign of Note 2 against 3 -- and in every case
  the nephews take UNCA and Donald takes UNCLE. It settled about thirty groups
  across the batch for nothing. Grep it before page 1.
- **A NAMING LINE IN A CAPTION IS AS GOOD AS ONE IN A BALLOON.** Daffy Taffy's
  184 g2 is a caption reading `"I FOUND DEWEY WITH ALL OF HIS CANDY STILL
  UNSOLD!"`, and 060's caption on Campaign of Note is `HUEY, LOUIE, AND DEWEY
  ESCAPE!`. Grep the narration boxes as well as the dialogue.
- **ELIMINATION ACROSS PAGES WORKS, BUT COUNT THE INFERENCES.** Daffy Taffy
  names Louie on 182 and Dewey on 184, and 182's `YOU'VE SOLD ALL OF YOUR
  CANDY, TOO?` makes 181's seller a third boy -- Huey, corroborated by 243px of
  roster red. That is one inference and it was taken. Tuckered Tiger 103 g1 would
  have needed two stacked ones (the speaker is the book-holder, and the
  book-holder is the unread third) and was left collective.
- **`visible_text` IS A LIST OF STRINGS, WHICH `roster.txt` DOES NOT SAY.** The
  page-2 dry-run caught it on the first two pages; without that dry-run it
  would have aborted after 28 pages of reading. Keep doing it at page 2.
- **NINE TYPE CORRECTIONS, AND FOUR OF THEM ARE ONE CLASS.** *The Tuckered
  Tiger* 106 g1/g3/g7/g8 are the track announcer's loudspeaker balloons stored
  as `narration`; they are drawn as balloons, one carries a tail to the judges'
  stand, and the same page's two genuine caption boxes are slanted coloured
  boxes with drop caps. A relayed voice is dialogue. The other five: two bare
  drawn devices out of `background`/`dialogue` into `thought` (099 g3, 181 g3),
  a tut and a yelp out of `sound_effect` into `dialogue` (062 g8, 183 g1), and
  three drawn question marks over one Beagle Boy into `thought` (065 g9).
- **A DROP CAP READS AS A BOLD WORD AND IS NOT ONE.** allbold put 1.36-1.68 on
  the first word of nine caption boxes across the batch -- DONALD, THEY, ABOARD,
  SOON, HUEY, SO -- every one of them the oversized initial. And its
  word-to-blob pairing failed on at least a dozen lines: 054 g4's 1.26 is a
  question mark, 049 g9's 1.51 is the single letter I, 065 g12's 1.35 a 34px
  blob. **Compare word against word WITHIN a line, not against the group base**,
  and treat a base above about 4.0 as the whole group being bold -- that
  signature appeared five times (040 g2, 044 g7, 045 g4, 052 g4, 065 g3) and a
  crop confirmed it every time.
- **MISSED TEXT: 8 ITEMS, AND 2 OF THEM THE AUDIT COULD NOT SEE.** The audit
  found 6 on Stone Ray and 1 on Campaign of Note. It found nothing on Tuckered
  Tiger, where 098 p8 has drawn dollar signs round Scrooge's head that no engine
  grouped -- a bare device has nothing to diff against, exactly as the
  forty-fourth batch found. Four of the Stone Ray six are the Beagle Boy's
  prison number `176-761`, which IS grouped on 052/063/064/066 and is not on
  050/055/057/059.
- **CORPUS SWEEPS, RUN AT THE END OF THE BATCH.** `vision-corrections` with no
  title: **18 outstanding across 460 titles**, all of them this batch's nine
  type corrections on both engines; the forty-fourth batch's `CAFÉ` and `BRR!`
  entries are gone, so they were worked. `speaker-queue --unreviewed
  --confidence low,medium` with no title: **41 groups, every one of them from
  this batch** -- Stone Ray 33, Tuckered Tiger 6, Daffy Taffy 1, Campaign of
  Note 1 -- written to `~/barks-vision/queue-corpus-lowmed-2026-09-10.txt`. The
  nine stragglers the forty-fourth batch left on *Sheriff of Bullet Valley*,
  *The Big Bin on Killmotor Hill* and *The Victory Garden* no longer appear.


### Findings to paste into the next run (2026-09-10, forty-sixth batch, FOURTH OF FOUR -- *A Descent Interval*, batch closed)

Replaces that title's numbers in the pass-only section below; *Ghost Sheriff*'s
straggler and the `CLANG` residue are fixed and it is 164/164. **10 speaker
corrections in 129 groups = 7.8%, 8 in the 34-group nephew domain = 23.5%.**
No type or text change since the pass commit 769fd620; the three type entries
listed are the pass's bubble-trail corrections, ratified. Mirror clean:
129/129 on both engines, every distribution identical.

**Batch total: 6 + 28 + 6 + 10 = 50 speaker corrections in 675 groups = 7.4%,
48 of them in the 214-group nephew domain = 22.4%.** Per title 5.4% / 10.3% /
3.7% / 7.8%, and the nephew rate ran 13.6% / 32.5% / 10.5% / 23.5% -- the two
patch-cap titles at two to three times the two big-hat or trimmed-cap ones.

| direction | n |
|---|---|
| a name -> `nephews` | 5 (195 g4, 196 g5, 197 g2, 203 g4, 203 g9) |
| one nephew -> another | 3 (197 g3, 197 g10, 203 g13) |
| `nephews` -> `other:Professor Quahog` | 1 (199 g6, the heeling ship) |
| one fisherman -> the other | 1 (202 g6) |

- **EIGHT OF TEN CORRECTIONS WERE MEDIUMS -- 8 of 19 (42.1%) against 1 of 108
  highs (0.9%).** The pass wrote medium on every gap tip and every small-patch
  read on this title, and the review overturned nearly half of them. The
  confidence field worked as a flag here; what it says about the pass is that
  a gap tip on a 120-300px patch is a coin toss, and the honest write is
  `nephews`. Across the batch: mediums 18 of 71 corrected (25.4%), highs 33 of
  600 (5.5%).
- **FIVE OVER-NAMINGS, ALL GAP TIPS OR TINY PATCHES.** 195 g4 and 203 g4 were
  tips in the gap between two boys with a direction; 197 g2 a split/thin
  disagreement resolved by which balloon hung over whom; 203 g9 a tip on a
  boy whose patch was read at page resolution; 196 g5 a 468px red beside a
  head that the reviewer notes `There is no cap` -- another blob-not-on-a-head.
  Same rule as *Ghost Sheriff*: **a gap tip is not a name.**
- **TWO SWAPS WENT BLUE -> GREEN ON 197 (g3, g10).** The pass read a
  120-150px blue patch (H188 S0.89, off the roster blue) on each; the review
  reads green, and on g10 adds `Louie is visibly speaking`. A dull off-hue
  patch under 200px is not a colour read; write the collective.
- **THE HEELING-SHIP BALLOON WAS THE PROFESSOR'S.** 199 g6 `LOOK OUT! WHAT
  HAPPENED?` from tiny figures at the winch, written `nephews` at low; the
  review makes it Quahog. Low was right to be low.
- **THE TWO FISHERMEN SWAPPED ONCE.** 202 g6 `MY EYES CAN'T BELIEVE WHAT THEY
  SEE!` went from the green-capped man to the bandana man; the pass placed it
  off which figure had his arms out. Two look-alike adults in one panel is
  the two-adults error class, and it happened on the one page they share.
- **MISSED TEXT: NONE.** All three drawn devices on the title were already
  groups.

**Batch close.** Four titles, 50 pages, 675 passed groups, 4 groups added by
the reviews (Lemming `BAM` and a fourth `AYE!`, Ghost Sheriff a drawn `?`,
and none on Kites or Descent), 1 real type change (Lemming 078 g6), 0 text
changes by the pass. Every title 100% reviewed on both engines, mirrors clean.
The rule that would have bought the most: **a census zero or a gap tip on a
small-patch construction is a crop, not a call** -- 15 under-namings on Lemming
and 8 gap-tip over-namings on Sheriff and Descent are the same failure read in
opposite directions.

### Findings to paste into the next run (2026-09-10, forty-sixth batch, THIRD OF FOUR REVIEWED -- *The Ghost Sheriff of Last Gasp*)

Replaces that title's numbers in the pass-only section below; *The Lemming
with the Locket*'s two stragglers have since been reviewed and it is 273/273
on both engines. **6 speaker corrections in 163 passed groups = 3.7%, all six
in the 57-group nephew domain = 10.5%.** `review_findings` says seven; the
seventh is the review's own add, 009 g17, the drawn `?` over the CLANG panel
(`other:Donald and the nephews`, `thought`). No type or text change since the
pass commit 93a86007 except the reviewer's punctuation on 010 g10; the sixteen
type entries listed are the pass's hiccups, ratified. Mirror clean on every
distribution, 164 groups both engines -- but **010 g10 is not yet
`speaker_reviewed`** and **the paddleocr copy of the added 009 g17 carries
`CLANG`, its seed's text, where easyocr has `?`**; both in
`queue-stragglers.txt`.

| direction | n |
|---|---|
| a name -> `nephews` | 3 (009 g8, 014 g12, 015 g5) |
| Donald -> the nephew domain | 2 (007 g11 the long shot, 008 g6) |
| one nephew -> another | 1 (013 g1 Louie -> Huey) |

- **THE EASIEST TITLE IN MONTHS, AND THE CAPS ARE WHY.** Cowboy hats of
  2,000-6,000px in three inks; 42 of 57 nephew groups named and 39 held.
  Compare *Lemming*'s 32.5% on a patch construction the same day. The
  construction, not the care, sets the rate.
- **THREE OVER-NAMINGS, ALL MEDIUM GAP TIPS.** 009 g8, 014 g12 and 015 g5
  were each a tailtip tip in the gap between two hats with a direction called
  for one of them, and each was written at medium. The review made all three
  collective. On a title where the hats are this legible a gap tip is not
  worth a name: **where the tip lands between two readable caps, write
  `nephews` and let the reviewer place it** -- it costs the same keystroke and
  cannot be wrong.
- **THE LONG-SHOT DEFAULT LOST ON 007 g11.** `IT COULD STAND SOME PAINT!`
  over a car a few dozen pixels wide went Donald -> `nephews`; the quip is a
  boy's. The default is for lines that could be anybody's, not for a wisecrack
  answering Donald's own line in the previous panel.
- **008 g6 WAS THE BOYS' ANSWER, NOT DONALD'S.** `ONLY SPIDERS AND MOTHS!`
  went Donald -> Louie. The pass had both balloons in the panel to Donald off
  two tailtip spurs and wrote "Donald answers his own question"; the review
  read it as the question-and-answer it looks like. When a panel's two
  balloons are a Q and an A, two tails to one figure is the reading to doubt.
- **013 g1 IS A TAIL DISAGREEMENT.** Louie -> Huey with cap green -> red; the
  pass's tip (669,242) was on the green hat on a 0.75x view. Recorded, not
  argued.
- **A DRAWN `?` IS A GROUP.** 009 p5's question mark over Donald's head in the
  CLANG panel was in neither engine and not in the pass's `visible_text`, so
  the audit could not see it; the review added it. Same class as *Tuckered
  Tiger*'s dollar signs: **list every drawn device in `visible_text`.**
- **COPY IN RESIDUE ON THE ADD, AGAIN.** The paddleocr side of the added group
  kept the seed group's `ai_text` (`CLANG`), and `vision-mirror` does not
  mirror text. The engine-diff check passed because it pairs positionally.
  Check any review-added group's text on BOTH engines before mirroring.
- **CONFIDENCE: 3 of 147 highs (2.0%), 3 of 16 mediums (18.8%).** Nine times
  worse at medium, the widest gap of the batch.

### Findings to paste into the next run (2026-09-10, forty-sixth batch, SECOND OF FOUR REVIEWED -- *The Lemming with the Locket*)

Replaces that title's numbers in the pass-only section below. **28 speaker
corrections in 271 passed groups = 10.3%, 26 of them in the 80-group nephew
domain = 32.5%.** `review_findings` reports 30, but two are the review's own
adds (084 g3 `BAM` seeded `unknown`, 089 g5 a fourth `AYE!`), subtracted here.
One real type change since the pass commit dc7c0c55 (078 g6, the quoted
telescope caption, to `narration` with speaker `narrator`); the other twelve it
lists are the pass's own, ratified. Mirror clean: 273 groups on both engines,
identical speaker, cap_colour and confidence distributions. **Two groups are
still not `speaker_reviewed`** -- 084 g10 and 089 g11, the last id on each page
that grew -- handed back in `queue-stragglers.txt`.

| direction | n |
|---|---|
| `nephews` -> a name | **15** |
| one nephew -> another | 5 |
| nephew domain -> Donald | 4 |
| a name -> `nephews` | 2 |
| Donald -> `nephews`, Scrooge -> narrator | 2 |

- **FIFTEEN UNDER-NAMINGS, AND THE NOTE ON EVERY ONE SAYS "CAP PRINTS
  NOTHING".** 075 g10/g11, 077 g5, 083 g5, 084 g7, 087 g8/g9/g12/g13, 088 g5,
  091 g5/g7 and three more: the pass ran the census, found no roster ink on
  that head, and wrote the collective. The review filled a cap_colour on every
  one. On this title the cap is a patch on the back of a black cap, often
  turned away, and the census floor hides it; the forty-fifth batch said the
  same about *Tuckered Tiger*'s wedge. **A census zero on a small-cap
  construction is an instruction to crop, not a licence for `nephews`** --
  written down twice now and still 15 groups in one title.
- **ONE OF THE FIVE SWAPS WAS THE PASS'S OWN MISATTRIBUTED BLOB.** 081 g5 was
  named Huey off `red 505px at (745,342) on head (767,348,856,445)`; a 1.3x
  crop shows the boy's cap is GREEN and the red is the ship's rail beside his
  head. The blob-must-sit-on-a-head error, again, from reading the census
  without the crop.
- **TWO SWAPS OVERTURN A TAIL, NOT AN INK.** 089 g8 (`Huey` -> `Louie`) and
  094 g7 (`Louie` -> `Huey`): on both the head the pass measured really does
  wear the colour the pass wrote (red on 089 p5, green on 094 p6, 1.3x crops),
  so the review has moved the balloon to the other boy. Both tails were
  tailtip readings across a gap. Flagged for a second look rather than
  argued; if they stand, the lesson is that a gap tip plus a ray is still a
  guess.
- **THE AYE! BALLOONS WENT TO DONALD.** 089 g2/g3/g4 (`nephews`, off-panel)
  are now `Donald`, and the fourth AYE! the review added is Donald too -- four
  AYE! around Donald's own `ALL IN FAVOR SAY AYE!`. Recorded as the review's
  call; it reads as the boys' chorus to the pass and is flagged with the two
  tail swaps.
- **`I DID NOT LOOK` DRESSED AS `nephews`, AGAIN.** 079 g13 the pass called
  Donald on a sailor collar and the review made `nephews`; 083 g7 the pass
  called Huey on two red slivers and the review made Donald. Both were
  0.55-0.7x views of two-figure panels. Two adults-versus-boy misreads on a
  title where the boy and Donald wear the same black shirt.
- **THE MISSED TEXT WAS ACTED ON, AND IT FOUND A SECOND.** The reviewer added
  084 `BAM` from the hand-back and, unprompted, a fourth `AYE!` on 089 that the
  pass had not listed in `visible_text` either -- the audit could not have
  seen it because the pass wrote three AYEs into the page record and there
  are four on the page. **Count the repeats when transcribing `visible_text`.**
- **CONFIDENCE: 26 of 250 highs corrected (10.4%), 4 of 19 mediums (21.1%),
  0 of 2 lows.** The medium flag doubled the rate again; the highs it did not
  cover were the fifteen collectives, which carry no confidence at all.

### Findings to paste into the next run (2026-09-10, forty-sixth batch, ONE OF FOUR REVIEWED -- *Donald Duck Tells About Kites*)

Replaces that title's numbers in the pass-only section below. **6 speaker
corrections in 112 groups = 5.4%, all six in the 44-group nephew domain =
13.6%.** No type or text changes since the pass commit (diffed against
7f741552); the six type entries `review_findings` lists are the pass's own
instruction-balloon corrections, ratified. Mirror clean: 112/112 on both
engines, 100 `identified_by`, identical speaker, cap_colour and confidence
distributions.

| direction | n | what it was |
|---|---|---|
| one nephew -> another | 3 | all on 189 p1 and p3 |
| `Donald` -> `nephews` | 1 | 186 g8 `I TOLD YOU, LOUIE!` |
| a name -> `nephews` | 1 | 189 g17 |
| `nephews` -> a name | 1 | 192 g5, the notebook writer read green |

- **THE PERMUTED KEY HELD WHERE THE ADDRESSES ARE, AND 189 IS WHERE IT DID
  NOT.** Every blue-Huey call made off a naming line survived. All three
  name-for-name swaps are on 189, the one page with three boys in a row and no
  address: 189 g5 went `Dewey / red` -> `Louie / green` (the review read the
  middle boy's cap as green where the pass measured 2021px of #e51a20), g8
  went `Huey` -> `Dewey / blue`, and g0 (the glue-covered boy) went `Louie` ->
  `Huey / blue`. **Note for the next Kites-style title: g8 and g0 apply
  different keys to the same blue** -- g0 reads blue as Huey (the story's key),
  g8 reads blue as Dewey (the volume's). One of them is a slip; flag to the
  reviewer rather than resolve. Where a story permutes its key, the pass's
  medium on every red and green call was the right hedge: 3 of 17 mediums were
  corrected against 3 of 95 highs.
- **`I TOLD YOU, LOUIE!` IS NOT DONALD'S.** 186 g8 went to `nephews`; the pile
  under the tree has three boys in it and the line is a brother's scold. The
  pass reasoned from the adult register and a tail into a heap of heads. A
  heap is a long shot's worth of ambiguity with none of its excuse.
- **THE ELIMINATION ON 189 g17 WAS REVERSED.** One tail onto the rightmost of
  three boys, green cap on a 0.7x crop, named Louie; the review made it
  `nephews`. Recorded as an outcome.
- **THE REVIEW FIXED TEXT THE PASS PASSED.** `notes` on 189 g5/g8 read
  `Corrected 'I WANTS' to 'I WANTA'`, on 192 g5 `Corrected 'THAIS' to
  'THAT'S' and added '6!'` -- but the stored `ai_text` is unchanged since the
  pass, so those notes describe Gemini-era fixes carried on the group, not
  this review. The pass's `text_ok: true` on every group stands.

### Findings to paste into the next run (2026-09-10, forty-sixth batch, PASS ONLY -- not yet reviewed)

Four titles, 50 pages, **675 groups**: *Donald Duck Tells About Kites* (Vol. 15)
112, *The Lemming with the Locket* (Vol. 14) 271, *The Ghost Sheriff of Last
Gasp* (Vol. 15) 163, *A Descent Interval* (Vol. 15) 129. **65 images read =
1.3 per page** against a target of 3; the highest title was Kites at 1.75,
where the cap key had to be re-derived from dialogue. Nephew domain:

| title | nephew groups | named | collectives | low/medium queue |
|---|---|---|---|---|
| Donald Duck Tells About Kites | 43 | 30 (70%) | 13 | 17 |
| The Lemming with the Locket | 80 | 45 (56%) | 35 | 21 |
| The Ghost Sheriff of Last Gasp | 57 | 42 (74%) | 15 | 16 |
| A Descent Interval | 34 | 23 (68%) | 11 | 21 |

- **A TITLE CAN PERMUTE THE WHOLE KEY, AND THE ADDRESSES SAY SO ON PAGE ONE.**
  Kites puts HUEY in the blue-trimmed cap: Donald names him on 186 p2, 191 p5,
  192 p1 and 192 p5 and the boy is blue every time, and 186 p3 names the
  red-capped boy DEWEY. Green is therefore Louie by elimination. The pass
  followed the story's own key, recorded the printed ink in `cap_colour`, and
  held every red and green call at medium (one address each) with the blue
  ones at high (five). This is not Stone Ray's drift -- the key is consistent
  across all eight pages -- so no retouch list; but a reviewer who reads
  `cap_colour: blue` next to `Huey` should know it is deliberate. **Grep the
  addresses before page 1 on every title, even one with a clean reference
  panel.**
- **THE VOL. 15 CAP CONSTRUCTION CHANGES PER TITLE AGAIN.** Kites: black cap
  with a small coloured trim at each side (266-601px). Ghost Sheriff: enormous
  cowboy hats (2,000-6,000px) in the three inks, the easiest title in months.
  Descent Interval: a small coloured patch on the back of a black cap
  (120-1,350px). All three pass through `capscan`'s default floor except the
  smallest Kites and Descent patches; the per-panel census caught those.
- **HICCUPS ARE A VOICE.** Ghost Sheriff stores fifteen `HIC` groups as
  `sound_effect`; every one is Wild Bill Trueshot hiccupping, so all fifteen
  went to `dialogue` with him as speaker, off-panel where he is unseen. Same
  reasoning for the Lemming's URP, ARK, GRR and SQUEAK on Lemming with the
  Locket (an animal's voice) and for the two YOW/OW cries Scrooge makes when
  bitten. CHOMP stays `sound_effect` but takes the lemming as maker.
- **SCROOGE'S BUBBLE-TRAIL BALLOONS ARE STORED AS DIALOGUE ON 074.** Four of
  the five balloons on Lemming 074 have a trail of circles to his head at 0.8x
  and were corrected to `thought`; the fifth has a pointed tail and stays
  speech. The same on Descent Interval 200 p5-p6 and 202 p5, Donald inside the
  globe. Check the underside of every solo-Scrooge balloon before trusting the
  stored type.
- **A CAPTION LETTERED LIKE A BALLOON.** Lemming 078 p6 `BUT --` is a
  drop-capital caption at the panel corner stored as `dialogue`; corrected to
  `narration`. Kites has the reverse six times: instruction balloons with
  tails to Donald's hands stored as `narration`, corrected to `dialogue`.
- **TAILTIP MERGES TOUCHING BALLOONS.** On Lemming 083 p5 and Ghost Sheriff
  008 p5 the tool returned the neighbour's tail or one shared spur for two
  balloons. A 0.7x view of the panel settled each in one image; when two
  balloons touch, read the crop, not the tool.
- **THE PRELIM VOLUME DIRECTORY IS NAMED FOR THE VOLUME'S LEAD STORY.**
  Descent Interval's pages live in the *Ghost Sheriff of Last Gasp* directory
  of Vol. 15. A staging assertion that looked for the title in the directory
  name matched nothing; assert on the volume prefix and the page numbers.
- **THE BARE-HEADED PAGES.** Kites has none. Lemming 095 p1-p5 (the inn),
  Ghost Sheriff 006 and 007 p1-p2 (indoors), Descent 194 (indoors) are all
  white-skull pages and every nephew group on them is a measured collective.
- **MISSED TEXT: ONE ITEM.** Lemming 084 p3 `BAM`, the crew pile-up, grouped
  by neither engine; in `queue-missed.txt` parked on g2. The other three
  titles came back clean.
- **CORPUS SWEEPS AT THE END OF THE BATCH.** `vision-corrections` with no
  title: **74 outstanding across 460 titles**, all this batch's type
  corrections (Kites 12, Lemming 24, Ghost Sheriff 32, Descent 6, both
  engines). `speaker-queue --unreviewed --confidence low,medium` with no
  title: **75 groups, every one from this batch**, written to
  `~/barks-vision/queue-corpus-lowmed-2026-09-10b.txt`. The forty-fifth
  batch's 41 no longer appear.

### Findings to paste into the next run (2026-09-10, forty-seventh batch, BOTH REVIEWED -- *Dogcatcher Duck*, batch closed)

Replaces that title's numbers in the pass-only section below. **12 speaker
corrections in 88 passed groups = 13.6%, 9 in the 13-group nephew domain =
69.2%.** `review_findings` counts 119 groups because the title's pages run to
039 (back matter the prep skips) and the review added one group, 034 g15,
the greyhound's blanket number `6` in panel 6 (`background`, `none`, clean
text on both engines). No type change since the pass commit eea781e0; the
ten type entries listed are the pass's own, ratified, and the ten it flags as
predating are August's thought-balloon adjudications. Mirror clean: 89/89 on
both engines, identical distributions.

| direction | n |
|---|---|
| `nephews` -> a name | 3 (031 g1, 031 g2, 036 g8) |
| a name -> `nephews` | 3 (031 g8, 032 g6, 036 g11) |
| Donald -> `nephews` | 3 (031 g10-g12, the `OHO!` laughs) |
| `other:` renamed | 2 (033 g8/g9 `the TV crew` -> `the audience`) |

**Batch total: 25 + 12 = 37 speaker corrections in 420 groups = 8.8%, 34 of
them in the 124-group nephew domain = 27.4%.** Mediums 11 of 30 corrected
(36.7%), highs 25 of 386 (6.5%).

- **THE GAP TIPS WERE NAMED AGAIN.** 031 g1, 031 g2 and 036 g8 were the
  pass's three gap or no-ink collectives on the car panels; the review named
  all three, as it named seven of nine on Hondorica. Across the batch the
  forty-sixth batch's gap rule ran **10 of 12 wrong**: on this volume's cap it
  is retired. Name a gap tip in the direction of its ray at medium.
- **THE EDGE TIPS ALL FELL HERE.** 031 g8, 032 g6 and 036 g11 -- every
  edge-of-span call on this title -- went collective; on Hondorica 7 of 10
  held. The edge tip is a coin toss on a two-boy back seat and a name on a
  three-boy row; write it medium and let the review place it.
- **`OHO!` FROM A SILHOUETTED CAR IS THE BOYS'.** Three laughs written Donald
  at medium went to `nephews`; the `dialogue` type held. A laugh from a car
  full of boys belongs to the boys unless the drawing says otherwise.
- **THE TOMATO-THROWERS ARE THE AUDIENCE, NOT THE CREW.** 033 g8/g9 were
  renamed `other:the audience`; the cameraman (g7) stayed `the TV crew`. A
  silhouette behind a camera is crew, a silhouette with a bucket is not.
- **MISSED TEXT THE AUDIT COULD NOT SEE.** The blanket number `6` on the
  netted greyhound (034 p6) was in neither engine and not in the pass's
  `visible_text`, so the audit had nothing to diff. **A number on a racing
  blanket, a jersey or a door is lettering: list it.**
- **CONFIDENCE: 6 of 7 mediums corrected (85.7%) against 5 of 81 highs
  (6.2%).** Every medium on this title was an edge tip or an off-screen laugh.

### Findings to paste into the next run (2026-09-10, forty-seventh batch, ONE OF TWO REVIEWED -- *Secret of Hondorica*)

Replaces that title's numbers in the pass-only section below. **25 speaker
corrections in 332 groups = 7.5%, all 25 in the 111-group nephew domain =
22.5%.** No text or type change since the pass commit 9e1ca774; the three type
entries listed are the pass's own, ratified (030 g0's `narration` predates the
pass). Mirror clean: 332/332 on both engines, 325 `identified_by`, identical
speaker, cap_colour and confidence distributions.

| direction | n |
|---|---|
| `nephews` -> a name | **12** (009 g1, 009 g8, 010 g9, 014 g1, 016 g7, 019 g4, 020 g6, 025 g11, 026 g9, 029 g7, 029 g13, 030 g16) |
| Donald -> the nephew domain | **6** (009 g2, 009 g6, 009 g9, 013 g11, 016 g8, 019 g3) |
| one nephew -> another | 3 (012 g5, 028 g3, 028 g7) |
| a name -> `nephews` | 3 (015 g4, 023 g12, 025 g5) |
| `nephews` -> Donald | 1 (018 g3) |

- **THE GAP-TIP RULE COST TWELVE NAMES ON THIS CONSTRUCTION.** Of the nine
  gap tips the pass wrote collective, the review named seven (009 g1, 009 g8,
  014 g1, 016 g7, 020 g6, 029 g7, 029 g13), every one in the direction the
  pass's own note recorded the ray pointing. Add the census-zero collectives
  (010 g9, 019 g4, 030 g16: a turned cap the review still read) and a chorus
  it split (025 g11), and the forty-sixth batch's "a gap tip is not a name"
  ran at 7 of 9 wrong here. **On a side-segment cap, a gap tip with a
  direction is a name at medium**; write the collective only when the ray
  enters nobody.
- **SIX DONALD CALLS WERE THE BOYS', AND THREE WERE SILHOUETTE PANELS.** 009
  g6, 009 g9 and 013 g11 had a tail the pass read to the big silhouette or to
  Donald beside the boys; the review gave all three to the boys. 009 g2, 016
  g8 and 019 g3 went to a named boy (Louie, Huey, Huey) off caps the pass
  had already measured in the same panel. The two-figure Donald-versus-boy
  panel is again the largest single error class outside the gap rule.
- **THE EDGE TIPS HELD 7 OF 10.** Of the edge-of-span calls written at medium,
  015 g4, 023 g12 and 025 g5 went collective and 028 g3/g7 swapped Huey ->
  Louie (the reviewer reads the middle boy's patch green); the rest stood.
  012 g5 swapped the other way on a tip the pass placed inside the green
  boy's span.
- **CONFIDENCE: 5 of 23 mediums (21.7%) against 20 of 305 highs (6.6%).** The
  highs that fell were the twelve collectives, which carry no confidence
  flag at all, and the six Donalds.
- **THE 015 g10 `OH, NO!` STAYED DIALOGUE.** The `type_reviewed` stamp from
  August outranks the pass, as the pass-only section said; the reviewer left
  it.

### Findings to paste into the next run (2026-09-10, forty-seventh batch, PASS ONLY -- not yet reviewed)

Two titles, 30 pages, **420 groups**: *Secret of Hondorica* (Vol. 17) 332,
*Dogcatcher Duck* (Vol. 17) 88. **51 images read = 1.7 per page** against a
target of 3: Hondorica 45 (1.9 per page, 21 of them crops of three-boy rows),
Dogcatcher 6 (the page views only). Nephew domain:

| title | nephew groups | named | collectives | low/medium queue |
|---|---|---|---|---|
| Secret of Hondorica | 106 | 69 (65%) | 37 | 27 |
| Dogcatcher Duck | 10 | 5 (50%) | 5 | 7 |

- **VOL. 17'S FIRST TITLES, AND THE CAPS ARE A SIDE SEGMENT ON A BLACK CAP.**
  Lit and turned toward the reader it prints 200-1,300px of clean ink (009 p2
  is the reference row: blue 672px, red 488px, green 244px); turned away it is
  a 60-200px sliver or nothing at all, and a boy with his cap turned sits
  beside two who are named (010 p7, 019 p3, 021 p8). **Two named leaves the
  third** was used on 010 p7; elsewhere the turned boy stayed collective.
  Both titles open indoors with the caps carried in hand (007-008, Scrooge's
  office) and every nephew group there is a measured collective.
- **THE BOYS' BALLOON TAILS LEAN TOWARD DONALD ON THIS TITLE.** 020 p5 `WHAT
  ABOUT THOSE INDIANS, UNCA DONALD?` sits over the one boy at left and its
  tail runs down-right, 50px past his head, toward Donald -- and the address
  proves it is the boy's. The same layout on 018 p4 (`GOLLY! HOW DO WE GET
  ACROSS?`), 025 p3 and 027 p1 was read the same way and written **medium**;
  the first of them had been written Donald off the tail alone before 020 was
  reached, and was rewritten. **A tail that leaves a boy's balloon and points
  at Donald is the boy's when the balloon sits over the boy** -- the same
  Q-and-A trap the forty-sixth batch recorded on Ghost Sheriff 008 g6.
- **EDGE-OF-SPAN TIPS, ~10 OF THEM, ALL WRITTEN AS THE BOY UNDER THE BALLOON
  AT MEDIUM.** On the three-boy rows (016 p3, 018 p7, 023 p2, 028 p3/p7/p8,
  031 p3, 032 p5, 036 p7) `tailtip` puts the tip at the LEFT edge of one
  boy's span with the ray leaning left into the gap. Each was written as the
  boy whose span the tip touches, medium. If the review holds them, an edge
  tip is a name on this construction; if it flips them, the forty-sixth
  batch's gap rule extends to edges.
- **NINE GAP TIPS WRITTEN COLLECTIVE** under the forty-sixth batch's rule (009
  p1, 009 p4, 014 p1, 016 p5, 020 p4, 026 p5, 029 p5, 029 p8, 034 p8). Every
  note records the direction; on 029 p5 and p8 the ray enters one boy's head.
  If the review names most of them off the direction, the rule cost more than
  it saved on this construction.
- **THREE GREENS, AND THE BAND NAMES LIE.** The reference panel's cap green is
  `#40a562` **H143** (the `green` band); every later cap green is `#4da33f`
  H111-114 (`leafgrn`); foliage, Scrooge's coat and the jungle are `#009e49`
  H147 (`green`). So `bands.txt`'s `green` column on this volume is mostly
  scenery and its `leafgrn` column is the caps -- read the hex, not the band.
  A crown probe that returns H147 next to a boy's head is a leaf.
- **DONALD IN THE CHU COSTUME IS STILL DONALD** (027-028): grass suit, red
  feather collar, no sailor cap. He recites the native phrases himself (027
  g4, g6 are his, the boys add the translations), and the census does not
  find his beak under the grass on every panel.
- **DOGCATCHER'S QUOTED CAPTION BOXES ARE THE NARRATOR**, six of them stored
  as dialogue and corrected; the one balloon WITH a tail (031 g9) is Donald's
  dialogue and was corrected the other way. The three `OHO!` laughs from the
  silhouetted car went to Donald at medium as dialogue.
- **ANIMAL NOISES.** Barks, yelps and yowps (034 g5, 035 g6-g8) went to
  `dialogue` with `other:the hounds`; the three `BZZZ` (013) stayed
  `sound_effect` with `other:the bumblebees` as maker -- a buzz is not a
  voice. The war drums are `other:the natives` and the bugle `other:the
  mayor` (named on 036 p8), both sound_effect.
- **OFF-PANEL VOICES OVER THE IDOL PANELS** (026 p2, three balloons with no
  duck in frame) were written low; 011 p1 and 012 p5 likewise medium/low.
  Those are the four lows in the batch.
- **BOTH `LOUIE` ADDRESSES WERE USED.** 028 g9 `YOUR SLINGSHOT, LOUIE!` names
  the silhouette and rules the blue speaker out; 029 g6 `IT WORKED!` then
  lands on the green boy by tail, which is the slingshot boy.
- **`other:` VALUES**: Don Pedro, the chief, a native (7), the natives (4), the
  bumblebees, the vulture, a fiesta guest, a woman guest; the mayor, the TV
  crew, the fire chief, the fire engine driver, the racing dogs, the hounds,
  the racetrack crowd, a fox hunter, the fox hunters.
- **ONE TYPE CORRECTION REACHED NO QUEUE.** Hondorica 015 g10 `OH, NO!` has a
  bubble trail to Gladstone's head and was written `thought`, but the group
  carries `type_reviewed` from 2026-08-16, so `vision_apply` left the stored
  `dialogue` alone and nothing lists it. The reviewer decides it from the
  crop; it is not in `queue-corrections.txt`.
- **MISSED TEXT: NONE** on either title; engine diff clean on both.
- **CORPUS SWEEP.** `vision-corrections` with no title: **26 outstanding
  across 460 titles**, all this batch's type corrections (Hondorica 3 groups,
  Dogcatcher 10, both engines).

### Findings to paste into the next run (2026-09-10, forty-eighth batch, FOURTH OF FOUR -- *Good Canoes and Bad Canoes*, batch closed)

Replaces that title's numbers in the pass-only section below. **7 speaker
corrections in 112 groups = 6.2%, 6 in the 33-group nephew domain = 18.2%.**
No group added. Mirror clean: 112/112 on both engines, 103 `identified_by`,
identical distributions. The straggler 054 g1 (`POP!`, `none`) and the
pass's four `dialogue -> thought` changes (054 g9, 055 g0, g2, g4, the cloud
balloons) were finished after the first commit; the review-stage close-out is
clean and the title is 112/112 on both engines.

| direction | n |
|---|---|
| one nephew -> another | 4 (056 g4 Dewey -> Louie, 057 g4 Huey -> Louie, 058 g14 Louie -> Huey, 058 g15 Huey -> Dewey) |
| a name -> `nephews` | 1 (056 g10) |
| a boy -> Donald | 1 (058 g10, the `?` device) |
| narrator -> an `other:` | 1 (054 g0, the announcer's tailless box) |

**Batch total: 32 + 0 + 4 + 7 = 43 speaker corrections in 638 groups = 6.7%,
37 of them in the 118-group nephew domain = 31.4%.** Mediums 29 of 65
corrected (44.6%), highs 14 of 573 (2.4%).

- **THE FOUR SWAPS ARE ALL GAP TIPS NAMED IN THE RAY'S DIRECTION, AND THE
  RAY WAS WRONG EVERY TIME.** 056 g4 (ray toward the blue boy: Louie), 057
  g4 (tip inside the red boy's span: Louie, the balloon's own side), 058 g14
  (gap between green and red: Huey), 058 g15 (gap toward Donald: Dewey by
  dialogue, held). With Philosopher's Stone's eleven, the forty-seventh
  batch's "name a gap tip in the direction of its ray" is now **0 for 15
  across this batch**. Retire it: on a gap tip, name the boy the BALLOON
  SITS OVER if that is unambiguous, else the collective.
- **056 g10 WAS THE EDGE TIP THAT WENT COLLECTIVE**, as every edge tip on the
  batch did (Philosopher's Stone 121 g3, 123 g14, Raucous Role 040 g10).
  Edge tips are `nephews` on this batch, 4 for 4.
- **THE `?` OVER THE CLOSE-UP BOY WENT TO DONALD.** 058 g10's question mark
  sits at the top-left corner of panel 5, above the ukulele, and the review
  read it as Donald's puzzlement (he is groggy in the next panels), not the
  boy's. A device at a panel corner is not "over" the nearest head.
- **A TAILLESS ROUNDED BOX THAT READS AS THE ANNOUNCER IS THE ANNOUNCER.** 054
  g0 stayed `narration` in type but went `other:the contest announcer` in
  speaker: the box carries his programme line. Speaker follows the voice
  even where the drawing is a caption.
- **CONFIDENCE ACROSS THE BATCH: mediums 44.6% corrected against highs
  2.4%.** The medium was where every gap and edge tip lived; nothing else
  was wrong at scale. Fewer mediums, more collectives.
- **`other:` VALUES ALL STOOD** on this title: the contest announcer, the
  prize presenter, the spectators, Porkmuscle J. Hamfat, the turtle, the
  hornets.

### Findings to paste into the next run (2026-09-10, forty-eighth batch, THREE OF FOUR REVIEWED -- *Donald's Raucous Role*)

Replaces that title's numbers in the pass-only section below. **4 speaker
corrections in 124 groups = 3.2%, all 4 in the 13-group nephew domain =
30.8%.** No group added; the pass's SCREEE (047 g6) and its seven type
changes (three cat noises to dialogue, four cloud balloons to thought) all
ratified; the five it flags as predating are August adjudications. Mirror
clean: 124/124 on both engines, identical distributions.

| direction | n |
|---|---|
| a name -> `nephews` | 3 (040 g10, 041 g0, 041 g4) |
| one nephew -> another | 1 (040 g7 Huey -> Louie) |

- **THE EDGE TIP WENT COLLECTIVE AGAIN, AND SO DID THE TWO GAP TIPS.** 040
  g10 (tip inside the left boy's span, ray into the middle boy), 041 g0 (tip
  15px outside the middle boy's span) and 041 g4 (tip above the left bed
  boy) were the title's three mediums and all three went to `nephews`:
  mediums 2 of 3, highs 2 of 121 (1.7%). Same verdict as Philosopher's
  Stone: on this batch a tip that is not squarely in a head is the
  collective.
- **040 g7 WAS THE BACK OF A CAP, AND THE 2,535px OF RED WAS NOT HUEY.** Two
  boys with their backs to the reader; the probe returned the whole back of
  the left cap red and the review named him Louie. A cap seen from behind
  shows its back panel, not its side segment, and the back panel is not the
  key on this title. Do not name off a rear view.
- **EVERY NOISE-MAKER CALL HELD**: Donald for the saw, hammer, chains,
  washboard, drum and siren (off-panel through the wall), the author for
  horn, shotgun and slipper-taps, the cheese-taster for the alpenhorn,
  `none` for the record player and the traffic. The maker-as-speaker
  convention on a sound-effect story is settled.
- **THE CAT NOISES ARE DIALOGUE**: MEOWRR, SPIT and FZT to
  `other:the alley cats` stood.

### Findings to paste into the next run (2026-09-10, forty-eighth batch, TWO OF FOUR REVIEWED -- *Heirloom Watch*)

Replaces that title's numbers in the pass-only section below. **0 speaker
corrections in 96 passed groups**, the fourth zero in this file and the first
with no nephews to force it: the cast is Scrooge, Donald, Gyro and five
barristers, and every tail landed. `review_findings` reports 98 because the
review added two `$` groups, the dollar signs on the safe in 137 p5 and 138
p5 (`background`, `none`, both engines). The one type change is the pass's
own (143 g9 narration -> dialogue, a tailed balloon to a hand), ratified; 140
g4 predates. Mirror clean: 98/98 on both engines, 88 `identified_by`,
identical distributions.

- **A DRAWN `$` ON A PROP IS LETTERING TO THE REVIEWER**, as the eye devices
  on Philosopher's Stone 110 were: the safe's dollar sign was in
  `visible_text` on both pages and neither engine had grouped it. When a
  page's `visible_text` carries a `$`, add the group in the pass rather than
  leaving it for the review.
- **`other:a barrister` (23) AND `other:the barristers` (1, the four-tailed
  chorus on 141 p1) BOTH STOOD.** The singular for one unnamed member of a
  named firm and the plural for the chorus is the pattern to reuse.
- **THE OFF-PANEL CALLS ALL HELD** (140 g8 Gyro's hand and pencil, 143 g2
  the eclipse sky, 143 g9 the hand with the tweezers): a hand in frame is
  an `off-panel` voice, not `unknown`.

### Findings to paste into the next run (2026-09-10, forty-eighth batch, ONE OF FOUR REVIEWED -- *The Fabulous Philosopher's Stone*)

Replaces that title's numbers in the pass-only section below. **32 speaker
corrections in 306 passed groups = 10.5%, 27 in the 72-group nephew domain =
37.5%.** `review_findings` counts 335 because the prep pages run to 144 (back
matter) and the review added two groups, 110 g16/g17, the dollar signs in
Scrooge's eyes on panel 3 (`thought`, Scrooge, hand-lettered text, both
engines). One type change, the pass's own (111 g12 `845 845 845` to thought),
ratified; the five it flags as predating are August adjudications. Mirror
clean: 308/308 on both engines, 295 `identified_by`, identical distributions.

| direction | n |
|---|---|
| a name -> `nephews` (over-naming) | **11** (118 g11, 119 g8, 121 g1, 121 g3, 123 g13, 123 g14, 126 g8, 127 g7, 127 g9, 130 g6, 131 g3) |
| one nephew -> another | 6 (118 g1, 122 g9, 122 g10, 130 g1, 131 g10, 131 g15) |
| Donald -> a boy | 3 (113 g1, 124 g2, 125 g2) |
| Scrooge -> Donald | 2 (115 g1, 116 g4) |
| Scrooge -> the nephew domain | 4 (118 g5, 127 g8, 122 g3, 126 g6) |
| the nephew domain -> Donald | 2 (112 g13, 122 g2) |
| `nephews` -> a name | 1 (120 g1) |
| `unknown` -> Scrooge, `other:Donald and the nephews` | 3 (the two adds, 116 g3) |

- **THE GAP-TIP RULE REVERSED ON THIS CAP: 11 OVER-NAMINGS, THE FIRST TITLE
  WHERE OVER-NAMING BEAT UNDER-NAMING 11 TO 1.** Every gap and edge tip the
  pass named in the ray's direction on the small side-tab cap went back to
  the collective: 118 g11, 119 g8, 121 g3, 123 g14, 126 g8, 127 g9, 131 g3
  are all "gap tip, named in the ray's direction, medium" notes, and 121 g1,
  123 g13, 127 g7, 130 g6 named on a 73-150px tab. **Where the tab is under
  200px and the tip is not inside a head span, write `nephews`.** The rule
  from the forty-seventh batch (side segment 200-1,300px) does not carry to
  a tab of a few dozen pixels.
- **MEDIUM WAS THE ERROR: 20 OF 41 MEDIUMS CORRECTED (48.8%) AGAINST 10 OF
  265 HIGHS (3.8%).** Worse than Pixilated Parrot's 41.2%. A medium on this
  title meant "the tail did not land"; the review's answer to that was the
  collective nearly every time.
- **SIX SWAPS, AND FOUR OF THEM HUEY -> LOUIE OR DEWEY.** 118 g1, 122 g9/g10,
  130 g1, 131 g10 were red tabs of 97-1,228px named Huey off a probe with a
  gap tip; the review read the other boy. On 122 the lantern-glow trio the
  pass split by beak went the other way entirely (the blue boy and the dark
  green boy, not the red one). The red tab is the one that prints big, so
  a red probe hit in a three-boy panel is not a name unless the tip is IN
  his span.
- **THREE DONALDS WERE BOYS AND TWO SCROOGES WERE DONALD.** 113 g1 (the
  magnifier in the vaulted room), 124 g2 and 125 g2 (the lantern-bearer and
  the boy in the red jewel chest) were read as Donald off a blue sailor cap
  -- on this volume Donald's cap and Dewey's tab are the same `#00a5d5` and
  the pass took the blue for Donald three times. Size the head; a blue tab
  on a small head is Dewey. 115 g1 and 116 g4 went Scrooge -> Donald on
  tailtip rays that reached Scrooge's hat.
- **THE SILHOUETTE PANELS WENT TO THE BOYS.** 118 g5 (harbour wall) and 127
  g8 (the Theseus question) were written Scrooge at medium off a silhouette
  and a leftward tail; both are the boys'. 122 g2 `I'M GETTING SCARED` went
  the other way, to Donald. Silhouette reads are 3 for 3 wrong here.
- **THE GUIDE-BOOK BOY IS NOT A KEY EITHER**: 118 g9 (the book-holder, kept
  Louie), 118 g11 and 119 g8 (tails on non-holders) went collective, not to
  the holder. Neither prop nor tail settles a Guide Book line on this title.
- **116 g3 `GROAN!` IS A CHORUS**: `other:Donald and the nephews`, the
  memory's form.
- **THE FIRST 110 SPLASH REVIEW ADDED THE `$ $ $` EYE DEVICES** as thought
  groups. A row of drawn dollar signs in a character's eyes is lettering to
  the reviewer; list it in `visible_text` and add it.

### Findings to paste into the next run (2026-09-10, forty-eighth batch, PASS ONLY -- not yet reviewed)

Four titles, 52 pages, **633 groups**: *The Fabulous Philosopher's Stone*
(Vol. 14) 303, *Heirloom Watch* (Vol. 14) 96, *Donald's Raucous Role* (Vol.
17) 123, *Good Canoes and Bad Canoes* (Vol. 17) 111. **61 images read = 1.17
per page** against a target of 3: 52 page views plus nine crops (three on
Philosopher's Stone 110 for the book spines, two on 112 for the cap
reference row, one each on 118, 121, 122 and 133 for tails). Nephew domain:

| title | nephew groups | named | collectives | mediums in domain | low/medium queue |
|---|---|---|---|---|---|
| The Fabulous Philosopher's Stone | 67 | 49 (73%) | 18 | 28 | 41 |
| Heirloom Watch | 0 | -- | -- | -- | 0 |
| Donald's Raucous Role | 13 | 5 (38%) | 8 | 3 | 3 |
| Good Canoes and Bad Canoes | 34 | 30 (88%) | 4 | 21 | 21 |

- **PHILOSOPHER'S STONE PRINTS A BLACK CAP WITH A SMALL SIDE TAB, 70-200px,
  UNDER THE CENSUS FLOOR.** The reference row 112 p4 (three boys, close)
  reads blue / red / dark-green left to right in a 2.5x crop; `title_heads`
  attaches cap ink to almost none of them and the `leafgrn` column is 0 on
  nearly every panel. Every name on the title came from a `probe.py` of the
  crown box, or from the census where the tab happened to face the reader
  (300-2,600px of `#e61b1f` then). **Its green tab prints TWO ways**: clean
  `#4da33d` H111 (115, 118 p1, 131) and a dark `#27865a`-`#35a46d` H150-152
  (112 p4, 118 p4, 120 p1). The dark one sits in capscan's `green` band with
  the foliage, so a `green` blob on a crown here is a cap, not a leaf -- the
  opposite of the Vol. 17 rule. Both were written `green` with the hex in
  the note.
- **THIRTY-FOUR MEDIUMS IN THE NEPHEW DOMAIN, ALMOST ALL GAP AND EDGE
  TIPS.** Following the forty-seventh batch, every gap tip was named in the
  direction of its ray at medium (118 g1, g11, 122 g8-g10, 124 g0-g1, 126
  g6, g8, 127 g9, 130 g1, 131 g5, g10, g15, 133 g3) and every edge tip as
  the boy whose span the tip sits in (121 g3, 123 g14, Raucous Role 040 g10,
  Good Canoes 056 g10). The review of these two rules on a small-tab cap is
  the thing this batch was for.
- **THE BOY HOLDING THE GUIDE BOOK IS NOT THE ONE THE TAIL LANDS ON.** Three
  times on Philosopher's Stone (118 g9, 118 g11, 119 g8) the balloon quotes
  the Junior Woodchucks' Guide Book and the tail lands on a boy other than
  the one holding it. All three were written from the tail at medium with
  the conflict in the note. If the review moves them to the book-holder,
  the prop outranks the tail on this title.
- **BOTH DONALD AND SCROOGE WERE NAMED FROM TAILS, NOT REGISTER.** Long-shot
  and silhouette Donald-versus-Scrooge calls (115 g9, 117 g1-g2, 118 g4-g5,
  123 g3-g4, 127 g10-g11) are medium; JEEPERS on 124 g1 went to Scrooge on
  the ray and is flagged. The one big-head test that mattered: 124 g0's
  rope-puller tip was equidistant from two groups and stayed with the boy
  doing the pulling.
- **GOOD CANOES' BOYS WEAR BIG SIDE SEGMENTS AND THE TAILS STILL CONVERGE ON
  THE RED BOY.** On 057 two-boy panels, four of five tips landed nearer the
  red boy; the two pairs were split by nearest head at medium (g0/g1, g4/g5,
  g9/g10). Two named leaves the third was used on 049 g8, 051 g3, 056 g3,
  058 g8 where one crown probed no ink at all.
- **INDOORS THE BOYS ARE BARE-HEADED ON BOTH VOL. 17 TITLES**: Raucous Role
  in bed and at the hospital (039, 045, 048), and every hotel-interior page
  of Philosopher's Stone (128). Those collectives are measured absence, with
  the bands totals quoted. Raucous Role 042 p8 prints the boys in red, green
  and blue PYJAMAS -- costume names them if a line ever lands there; none
  did.
- **RAUCOUS ROLE IS A SOUND-EFFECT STORY**: 30 of its 123 groups are noises,
  and each was given its MAKER as speaker with `sound_effect` kept -- Donald
  for the saw, hammer, chains, washboard, drum and siren (off-panel when
  heard through a wall), the author for his horn, shotgun and slipper-taps,
  the cheese-taster for the alpenhorn, `none` for the record player, the
  train and the streetcar. The three cat noises on 039 (MEOWRR, SPIT, FZT)
  went to `dialogue` / `other:the alley cats`; the hornets' BZAZZZZZ on Good
  Canoes 055 stayed `sound_effect` with the hornets as maker.
- **TWELVE DIALOGUE -> THOUGHT CORRECTIONS ON THE TWO VOL. 17 TITLES.**
  Gemini labelled cloud-edged balloons with bubble trails `dialogue` on
  Raucous Role 043 (3), 044 (2), 047, 048 (2) and Good Canoes 054 (3), 055
  (3), 057. Read the trail, not the words: every one is a private thought.
  Good Canoes also had five `narration` -> `dialogue` on 050-051 (the
  announcer's speech balloons stored as captions) and Heirloom Watch 143 g9
  (a tailed balloon to a hand).
- **MISSED TEXT, FIVE ITEMS, ALL ADDED BY THE PASS**: Philosopher's Stone 110
  `GOLD` and `HISTORIE GOLDE` (two book spines under the scroll), 114 p8 a
  drawn `?` over the middle boy, Raucous Role 047 p6 the siren's `SCREEE`,
  Good Canoes 058 p5 a `?` over the close-up boy. The audit is clean on all
  four titles after the apply.
- **`other:` VALUES**: Monsieur Mattressface (29), the librarian (4), the
  Bagdad scholar, the Damascus record-keeper, the history clerk, the
  ironworks foreman; a barrister (23), the barristers (chorus, 1), the
  cablegram messenger; the author (19), the author's wife, the
  cheese-taster (7), the alley cats (3), the nurse; the contest announcer
  (15), the prize presenter (a different man on 058 p6), the spectators
  (3), Porkmuscle J. Hamfat, the turtle, the hornets.
- **CORPUS SWEEP NOT RUN THIS BATCH**; the per-title `vision-corrections`
  shows 2 + 2 + 14 + 8 outstanding, of which the pass's own are 1 + 1 + 7 +
  4 (the rest are August thought-balloon adjudications carrying
  `type_was`).

### Findings to paste into the next run (2026-09-11, forty-ninth batch, THREE OF THREE -- *The Unorthodox Ox*, batch closed)

Replaces that title's numbers in the pass-only section below. **8 speaker
corrections in 123 groups = 6.5%, all 8 in the 34-group nephew domain =
23.5%.** All seven bull-voice type proposals confirmed, no group added by the
review. Mirror clean: 123/123 groups on both engines, 122 reviewed on each,
identical distributions; the one straggler, 084 g5 (the boy fitting the dark
glasses, Louie on a 1,936px `#019d46` cap), was finished after the first
commit and held, so the title is 123/123 on both engines. Highs 4 of 114 corrected (3.5%), mediums 4 of 9
(44.4%).

**Batch total: 2 + 8 + 8 = 18 speaker corrections in 355 groups = 5.1%, 17
of them in the 101-group nephew domain = 16.8%.** Mediums 6 of 23 corrected
(26.1%), highs 11 of 331 (3.3%).

| direction | n |
|---|---|
| a name -> `nephews` | 4 (083 g12, 084 g3, 084 g13, 086 g7) |
| `nephews` -> a name | 1 (085 g7 Louie) |
| one nephew -> another | 1 (088 g1 Dewey -> Huey) |
| Donald <-> Grandma Duck | 2 (081 g4, g5 exchanged) |

- **THE FOUR OVER-NAMES ARE THE BATCH'S ONLY ONES AND THREE OF THE FOUR WERE
  MEDIUMS ON SMALL OR OFF-HUE CAPS**: 084 g3 a 197px dull red, 084 g13 a
  shaded `#12a3b4` H186, 086 g7 a `#1e6c6e` H181 patch under a blue tent.
  The one high, 083 g12, was a 3,900px clean blue from BEHIND: the tip sat
  inside the right boy's span at its edge, but two boys seen from the back
  with the balloon over both is a chorus to the reviewer. So on this volume
  the OFF-HUE cap (H160-H190) is not a name at any size, and on Chickadee
  the same ink was the blue boy -- read it as `nephews` with the hex in the
  note and let the review decide.
- **085 g7 WAS THE GAP TIP THAT WENT LOUIE** (the collective the pass wrote
  by the forty-eighth rule; the two it named at medium against the rule,
  085 g9 and g12, both HELD). With Chickadee's five, gap tips named by the
  review are now 6 for 6 on this batch: name them at medium, never
  collective.
- **081 g4/g5 EXCHANGED DONALD AND GRANDMA.** `BUT HE'S SO SEEDY-LOOKING! I
  WISH I HAD TIME TO SLICK HIM UP A BIT!` is Grandma's, `OH, FORGET IT! HIS
  LOOKS WILL HELP! BYE! BYE!` is Donald's driving off. The pass placed both
  by which figure each balloon sat over; the register (who wants the bull
  seedy for the contest) says the reverse. Two adults, a tail each, and the
  drawing won over the words in the note -- the words were right.
- **088 g1 WENT DEWEY -> HUEY** on a 163px blue against a 413px red: the
  tip landed inside the middle boy's skull by both tailtip readings and the
  reviewer gave it to the red boy beside him. A sub-200px cap does not
  outrank the neighbour's.
- **THE BULL IS CONFIRMED A SPEAKER**: all seven SNORT/BAW `sound_effect ->
  dialogue` with `other:Johnny the bull` stood; BLINK stayed a sound effect.
- **`other:` values all stood**, and `Grandma Duck` is a plain roster value.

### Findings to paste into the next run (2026-09-11, forty-ninth batch, TWO OF THREE REVIEWED -- *The Chickadee Challenge*)

Replaces that title's numbers in the pass-only section below. **8 speaker
corrections in 117 groups = 6.8%, all 8 in the 61-group nephew domain =
13.1%.** No group added, no type outstanding. Mirror clean: 117/117 on both
engines, 111 `identified_by`, identical distributions. Highs 6 of 104
corrected (5.8%), mediums 2 of 13 (15.4%).

| direction | n |
|---|---|
| `nephews` -> a name | 5 (069 g10 Huey, 070 g1 Louie, g7 Dewey, g8 Huey, g11 Dewey) |
| one nephew -> another | 2 (070 g2 Louie -> Dewey, g4 Huey -> Louie) |
| a name -> `nephews` | 1 (069 g9) |

- **EVERY GAP TIP THE PASS LEFT COLLECTIVE WAS NAMED, 5 FOR 5.** The
  forty-eighth batch's rule ("a gap tip is the boy the balloon sits over or
  the collective") produced pure under-naming here: on the two picnic pages
  the reviewer named all five off the drawing. Neither proximity nor the ray
  predicts the answer (069 g10 went to the FARTHER skull, 070 g11 to the
  nearer, 070 g8 to the one 4px farther), so the pass cannot resolve them
  by measurement; but declining was still the wrong hedge. Name the gap tip
  at MEDIUM with both candidates in the note, so the reviewer's keystroke
  fixes it either way and a right guess is not thrown away.
- **070 g4 WENT HUEY -> LOUIE WITH THE REVIEWER'S NOTE "LOUIE HAS AN OPEN
  MOUTH".** The tip sat over the middle (red) boy's column; the right (green)
  boy is the one speaking. On a three-in-a-row panel the OPEN BEAK is
  evidence the pass never used; check it before the tip.
- **070 g1 AND g2 SWAPPED THE SEATING.** The pass read the table left to
  right as unreadable / red / teal and named the right boy Louie; the
  review has the g2 boy Dewey and the g1 line Louie. The `#519d88` H163
  ink the pass wrote `green` was blue in shade: on this volume an off-hue
  cap between H160 and H190 is the BLUE segment, not the green.
- **069 g9 `HA! ANOTHER CLUB! HA!` WENT COLLECTIVE**: the tip sat above the
  blue boy's cap but the line is a chorus of three laughing boys; a tail
  over one head does not make a three-voice jeer his.
- **The Woodchuck-cap pages (071-078) stood in full**: every address-named
  general, every signal count, the three continuity mediums and all the
  collectives. Naming by address is safe; the picnic pages with roster caps
  are where this title's errors lived.
- **`other:` values all stood.**

### Findings to paste into the next run (2026-09-11, forty-ninth batch, ONE OF THREE REVIEWED -- *Trouble Indemnity*)

Replaces that title's numbers in the pass-only section below. **2 speaker
corrections in 115 groups = 1.7%, 1 in the 6-group nephew domain.** One
group added (068 g13, the DONALD DUCK on the vaudeville contract, background /
none). Both type proposals confirmed. Mirror clean: 115/115 on both engines,
102 `identified_by`, identical distributions. Highs 1 of 113 corrected
(0.9%), the one medium (068 g8, the elimination call) held.

- **067 g3 `OOPS! I TRIPPED!` WENT SCROOGE -> DONALD.** The note read the tail
  to Scrooge on the platform while Donald is falling; the review gave the
  line to Donald. A two-adult panel at long shot, the error class the cost
  doc names: the tail was cited but not measured.
- **068 g13 IS A REVIEW ADD**: the contract lettering the pass had put only in
  `visible_text` as `DONALD DUCK`. The audit passed because the page-level
  text matched the story logo's echo suppression; a name that is also the
  title is invisible to it.
- **The nephew calls on 068 all stood**, including the two-tail chorus (g11)
  and the elimination (g8).

### Findings to paste into the next run (2026-09-10, forty-ninth batch, PASS ONLY -- not yet reviewed)

Three titles, 30 pages, **354 groups**, all Vol. 17: *Trouble Indemnity* 114,
*The Chickadee Challenge* 117, *The Unorthodox Ox* 123 (one added). **44 images
read = 1.47 per page** against a target of 3: 30 page views plus 14 crops and
panel views (four 0.6x panel views and one 2x tail crop on Trouble Indemnity
068; three 1x head crops, one 0.5x corner view and two 1x crops on Chickadee
069-070, one on 074; one tail crop and one sign crop on the Ox). Nephew domain:

| title | nephew groups | named | collectives | mediums in domain | low/medium queue |
|---|---|---|---|---|---|
| Trouble Indemnity | 6 | 5 (83%) | 1 | 1 | 1 |
| The Chickadee Challenge | 61 | 32 (52%) | 29 | 13 | 13 |
| The Unorthodox Ox | 34 | 16 (47%) | 18 | 9 | 9 |

- **GAP TIPS WENT COLLECTIVE, AS THE FORTY-EIGHTH BATCH SAID.** Every tip
  that landed between two skulls with the balloon over both was written
  `nephews` (Chickadee 069 g10, 070 g1, g7, g8, g11; Ox 085 g7), whatever the
  ray did. Two were named anyway at medium, with the reason in the note: Ox
  085 g9 (12px from one skull against 30px, and the boy has his finger up in
  the 'idea' pose) and 085 g12 (the tip touches the left boy's beak end, 62px
  from the next). The review of those two is what settles whether proximity
  inside a head-width is allowed to break the tie.
- **THE CHICKADEE CHALLENGE IS A WOODCHUCK-CAP STORY: 071-078 CARRY NO ROSTER
  INK AT ALL** and every name on those pages is an ADDRESS. `GENERAL DEWEY` /
  `YES, GENERAL HUEY!` name the measuring pair on 072 (six groups, high), the
  chisel boy's `GENERAL LOUIE` names the boy beside him on 074 p8, the
  troopers' `YES, GENERAL LOUIE! CALL THE SIGNALS!` on 076 p6 makes every
  numbered signal on 076-077 Louie's (five groups). Three continuity calls
  were made at medium (073 g0, g4 Huey from the graph he was computing; 075
  g0 and its two PONKs Louie from the chisel staying with the other boy across
  one panel). Everything else in Woodchuck caps is `nephews`.
- **069 p3 PRINTS TWO RED CAPS.** The letter-holder and the boy beside him
  both probe `#e61b1f` (248px against 265px), and no green anywhere on the
  panel. The letter-holder was named Huey from the letter he has carried
  since p1 (where he was the only red) and the other boy Louie by
  elimination, `cap_colour` recorded as the printed red, both medium. A
  colourist slip; the review says whether continuity may carry a name across
  one.
- **THE OX PRINTS ITS CAP GREEN IN CAPSCAN'S `green` BAND** (`#029d46` H146,
  S0.99), not `leafgrn` as the rest of Vol. 17: on this title a `green` blob
  on a skull IS the cap. Its blue drifts from `#00a5d7` to `#23a186` H167 in
  shade on one panel (085 p4) and `#12a3b4` H186 on another (084 p7); the
  seat and the other two caps carried those. The boys are bare-headed at
  breakfast (079-080, eleven collectives).
- **TROUBLE INDEMNITY 068 p7 HAS A BALLOON WITH TWO TAILS**, one to each of
  the first two boys, only visible in a 2x crop; `tailtip` gave the two
  readings 40px apart and that disagreement is what earned the crop. 068 g8
  is the batch's one elimination call (blue and a 140px red named the other
  two).
- **THE BULL IS A SPEAKER.** Seven `sound_effect -> dialogue` on the Ox for
  SNORT and BAW with `other:Johnny the bull`; BLINK stays a sound effect with
  the blinker as maker. Trouble Indemnity's RAHRRR went the same way for
  Mugger Jones's dog, and its three `dialogue -> thought` are cloud balloons
  (064 g1 a `?` device). The four bugle TA-RAs on Chickadee stayed
  `sound_effect` with `other:the Woodchuck bugler`, per the Masters of Melody
  ruling.
- **MISSED TEXT, ONE ITEM, ADDED BY THE PASS**: Ox 081 p7 the RR CROSSING
  crossbuck. The audit is clean on all three titles after the apply.
- **`other:` VALUES**: Mr. Brasshorn (22), the clerk (3), Mugger Jones (2),
  Mugger Jones's dog; the Chickadee nest leader (10), the Woodchuck bugler
  (4), the Junior Woodchuck observer (3), the Woodchuck troopers (2), a
  Woodchuck trooper (2), a Chickadee (2), the Chickadees; Johnny the bull (9),
  the spectators (4), the policeman (2), the arena announcer (2), the fair
  official (2), the Blue Angel balloonist, the jam exhibitor. Grandma Duck (7)
  was written `other:Grandma Duck` and the apply canonicalized it to the
  plain `Grandma Duck`, a name the schema already knows.
- **CORPUS SWEEP RUN**: `vision-corrections` with no title reports only this
  batch's own 18 type rows (9 groups x 2 engines) outstanding across 460
  titles.

### Findings to paste into the next run (2026-09-11, fiftieth batch, THREE OF THREE -- *The Custard Gun*, batch closed)

Replaces that title's numbers in the pass-only section below. **22 speaker
corrections in 136 groups = 16.2%, 21 in the 56-group nephew domain =
37.5%.** No group added or merged; all four type proposals confirmed.
Mirror clean: 136/136 on both engines, 122 `identified_by`, identical
distributions. Highs 18 of 120 corrected (15.0%), mediums 4 of 16 (25.0%).

**Batch total: 21 + 20 + 22 = 63 speaker corrections in 574 groups = 11.0%,
55 of them in the 140-group nephew domain = 39.3%.** Mediums 11 of 47
corrected (23.4%), highs 51 of 511 (10.0%). Under-naming was 32 of the 63.

| direction | n |
|---|---|
| `nephews` -> a name | 16 (089 g1 Huey, g6 Huey, g12 Louie; 090 g3 Louie, g4 Dewey, g9 Huey; 091 g11 Louie; 092 g1 Louie; 093 g3 Louie, g6 Louie, g7 Huey; 097 g10 Dewey, g13 Huey; 098 g0, g4, g6 Huey) |
| one nephew -> another | 4 (089 g4 Dewey -> Huey, 091 g13 Huey -> Dewey, 097 g2 Louie -> Dewey, 097 g6 Louie -> Dewey) |
| Donald -> Huey | 1 (090 g5, the silhouette with the gun) |
| Donald -> `other:the goat` | 1 (092 g8 `GRUNT?`) |

- **SIXTEEN UNDER-NAMES ON A TEN-PAGE TITLE, EVERY ONE A BOY THE PASS WROTE
  "NO INK" ON.** With Steamboat's 7 and Riches' 9 that is 32 in the batch,
  half of all corrections. The three titles draw black beanies with a patch
  at the back; front-on the patch is a sliver under the 25px floor, and the
  reviewer named every such boy off the drawing. The rule for beanie
  titles: probe each crown at S>=0.06 before writing collective, and name a
  single-hue sliver at medium. A `nephews` on a beanie title is now the
  most expensive thing the pass writes.
- **THE OPEN-BEAK RULE IS DEAD: 0 FOR 4 ACROSS THE BATCH.** 089 g4 went
  Dewey -> Huey (the tail's boy), 091 g11 went to Louie by cap, and Riches
  172 g4/g12 went the same way. Read the tail; an open beak on the other
  boy is not evidence.
- **TWO GREEN-PATCH LOUIES WERE DEWEY (097 g2, g6)** and one `#08a29d` teal
  (097 g4) held as Dewey: on this title the H140-150 patch is NOT reliably
  the green segment -- the reviewer read 097 g6's `#0da842` patch as blue.
  Record the hex, hold at medium, and let the elimination from a clean red
  do the work.
- **THE SILHOUETTE WITH THE GUN (090 g5) WAS A BOY**, not Donald: a sailor
  cap in outline is not enough when three boys are in the panel.
- **`GRUNT?` (092 g8) IS THE GOAT'S**: a balloon over the thicket with a
  question mark is still the animal's voice; the reviewer added
  `other:the goat`. The moose SNORTs and the `FUNG!` shots stood.
- **`other:` values**: `the moose`, `the second moose`, `the goat`.

### Findings to paste into the next run (2026-09-11, fiftieth batch, TWO OF THREE REVIEWED -- *Riches, Riches, Everywhere!*)

Replaces that title's numbers in the pass-only section below. **20 speaker
corrections in 222 groups = 9.0%, all 20 in the 49-group nephew domain =
40.8%.** No group added; 168 g8/g9 (one balloon the engines had split)
merged by the review. All three type proposals confirmed. Mirror clean:
221/221 on both engines, 215 `identified_by`, identical distributions.
Highs 18 of 206 corrected (8.7%), mediums 2 of 15 (13.3%).

| direction | n |
|---|---|
| `nephews` -> a name | 9 (164 g1 Huey, 167 g2 Huey, 169 g0 Louie, 171 g4 Louie, 172 g8 Dewey, 172 g14 Dewey, 173 g4 Louie, 173 g7 Louie, 179 g11 Louie) |
| Scrooge <-> Donald | 6 (165 g5/g6, 171 g10, 173 g9, 179 g3, 179 g7) |
| one nephew -> another | 3 (166 g6 Dewey -> Louie, 167 g14 Dewey -> Huey, 172 g12 Huey -> Louie) |
| Donald -> a name | 1 (169 g6 Huey) |
| a name -> `nephews` | 1 (172 g4) |

- **NINE UNDER-NAMES, EVERY ONE A BOY THE PASS CALLED "BLACK CAP, NO INK".**
  The reviewer named them off the drawing where the census had nothing
  above its 25px floor and probes found 65-160px slivers. On this title a
  sliver IS the name: the caps are black beanies with a patch at the back,
  and a boy seen from the front shows a few dozen pixels of it. When two
  boys in the panel are already named, name the third; when a probe finds a
  sliver of one roster hue, name him at medium rather than writing
  collective.
- **THE OPEN-BEAK RULE LOST 2 OF 3.** 172 g4 (open beak, red boy) went to
  `nephews` and 172 g12 (open beak, red boy) went to the tail's boy Louie;
  only 166 g6 was a tail-and-beak agreement and it still went Dewey -> Louie
  (the review read the crates boy's cap as green). Read the TAIL first; an
  open beak on the other boy is a reason for medium, not a reason to move
  the name.
- **SIX SCROOGE/DONALD SWAPS, ALL AT LONG SHOT OR WITH BOTH IN FRAME.** 165
  g5/g6 exchanged (the WHERE question is Donald's, PHOOEY is Scrooge's);
  171 g10 and 173 g9 and 179 g3/g7 are two-adult panels where the pass
  cited the tail without measuring it. This is the two-adult error class
  the cost doc names; measure the tip on any Scrooge/Donald panel with both
  in frame.
- **169 g6 WENT DONALD -> HUEY** with the reviewer's note "Not Dewey or
  Louie": the boy with the pick pointing at the water hole, not Donald
  above him, so a tail read to the wrong head at page scale.
- **Vol. 14 `UNCA` / `UNCLE` HELD**: no correction crossed it.
- **`other:` values all stood**: `Punter`, `Digger`, `the claim jumpers`,
  `the kookaburras`; the four `unknown` HALLO! specks stood as `unknown`.

### Findings to paste into the next run (2026-09-11, fiftieth batch, ONE OF THREE REVIEWED -- *The Great Steamboat Race*)

Replaces that title's numbers in the pass-only section below. **21 speaker
corrections in 216 groups = 9.7%, 14 in the 35-group nephew domain =
40.0%.** Four groups added by the review: two `$` devices as Scrooge's
thoughts (151 g9, 152 g13) and the two `CAPTAIN` badges the audit had
found (154 g10, 160 g8). Text correction `ZOWL!` -> `ZOW!` applied; the
five type proposals were NOT confirmed and are still outstanding on both
engines (150 g3, 157 g2, 157 g4, 158 g6, 160 g12). Mirror clean: 205/205
on both engines, 203 reviewed on each, 191 `identified_by`, identical
distributions; **151 g8 and g14 are still unreviewed** and are in
`queue-stragglers.txt`. The review typed `other:Horshoe Hogg` on two
groups (160 g5, g9); normalised to `Horseshoe Hogg` before the mirror.
Highs 15 of 185 corrected (8.1%), mediums 5 of 16 (31.2%).

| direction | n |
|---|---|
| `nephews` -> a name | 7 (151 g11 Louie, 154 g1 Louie, 154 g2 Dewey, 156 g1 Louie, 158 g1 Louie, 158 g9 Huey, 159 g11 Louie) |
| Donald -> `nephews` | 4 (147 g11, 148 g10, 161 g0, 161 g5) |
| `nephews` -> Donald | 2 (146 g12 the `?` device, 161 g1 Louie -> Donald) |
| `unknown` -> Scrooge / `none` | 4 (151 g9, 152 g13, 154 g10, 160 g8 -- the review's own adds) |
| `narrator` -> a voice | 2 (160 g5 Hogg, 160 g6 `unknown`) |
| a name -> `nephews` | 1 (153 g3) |

- **THE UNDER-NAMES ARE ALL INDOOR OR HELMET PAGES WHERE THE PASS WROTE
  "BLACK CAP".** 154 g1/g2 and 156-159 name boys whose caps the census
  never listed; the reviewer read them off the drawing at panel scale (156
  g1: "Not Dewey or Huey"). Same lesson as Riches: on a black-beanie title
  a sliver of ink names, so probe every crown before writing collective.
- **FOUR DONALDS WERE BOYS, TWO ON THE 161 TUBE RAFT AT SPECK SCALE.** The
  long-shot default to Donald went 0 for 4 here (147 g11 and 148 g10 are
  medium shots where the boy beside Donald had the beak open). The default
  is for a lone figure at long shot, not for a panel with a boy in it.
- **161 g1 WENT LOUIE -> DONALD**: the engineer-continuity call at medium was
  wrong; the maroon probe on g2 (Scrooge) held. Continuity from three pages
  back is not evidence at speck scale.
- **160 g5 AND g6 ARE NOT CAPTIONS TO THE REVIEWER**: the two yellow boxes
  over the racing boats went to Hogg and `unknown` as voices, with the type
  left `narration`. Say so to the reviewer; the type and the speaker now
  disagree on those two.
- **`other:` values otherwise stood**: `Horseshoe Hogg`, `the stewardess`,
  `a River Belle workman`.

### Findings to paste into the next run (2026-09-11, fiftieth batch, PASS ONLY -- not yet reviewed)

Three titles, 42 pages, **556 groups**: *The Great Steamboat Race* (Vol. 14)
200, *Riches, Riches, Everywhere!* (Vol. 14) 221, *The Custard Gun* (Vol. 17)
135. **78 images read = 1.86 per page** (29 / 29 / 20), under the 3-per-page
target; 4 crops generated, all for bare devices or a letter. Three groups
added (a `?` over the boys on Steamboat 146 p5, a `?` over the disguised
claim jumper on Riches 174 p8, a `!` over a boy on Custard 093 p3). Missed
text: **two `CAPTAIN` cap badges on Steamboat 154 p6 and 160 p6**, grouped
by neither engine (157 g11 is the same lettering grouped); none on the other
two. Type proposals 12 (5 / 3 / 4), one text correction (Steamboat 151
`ZOWL!` -> `ZOW!`). Mediums 46 of 556 (16 / 14 / 16).

- **CAPS COME OFF INDOORS ON BOTH Vol. 14 TITLES AND THE PASS FIRST WROTE
  THAT AS A TITLE-WIDE ABSENCE.** Steamboat 146-151 (office, bin, airliner)
  and Riches 164-165 (bin) are plain black caps with no ink in any census;
  the roster inks appear the moment the boys are outdoors (Steamboat 152,
  Riches 166). Three notes had `no roster ink on this title` written before
  152 was read and had to be rewritten. Write the absence for the PANEL and
  check an outdoor page before any wider claim.
- **THE OPEN BEAK AGAINST THE TAIL, FOUR TIMES.** On Riches 172 g4 and g12
  and Custard 089 g4 and 091 g11 the tail tip sat on or over one boy while
  the OTHER boy had the open beak and the gesture. The pass followed the
  Chickadee finding (070 g4) and named the open-beak boy at medium each
  time, with the tail's boy in the note. Whether that holds is the thing
  this review settles: if it does not, the four go back to the tail.
- **TWO-TAIL BALLOONS ARE COLLECTIVES**: Steamboat 153 g0 and Custard 091 g8
  each carry one balloon with two tails to two boys and were left `nephews`.
- **THE CUSTARD GUN'S CAPS ARE BLACK BEANIES WITH A COLOURED PATCH AT THE
  BACK, 60-400px,** and the green patch prints in the scenery ink
  (`#009d49`-`#0da842`, H140-150, the `green` band) rather than the H111
  `leafgrn` of the rest of Vol. 17. Every green-patch call there is Louie at
  medium with the hex in the note (090 g11, 092 g9, 097 g6). Riches prints
  its caps small too: 167 p5 and 169 p1 read only 160-340px of shaded ink
  per crown at S0.4-0.8, and on 169 p1 the two unnamed boys shared one hue
  (H157) and stayed collective.
- **RICHES 179 PRINTS DEWEY IN RED AND THEN IN GREEN**: the caption names
  DEWEY'S voice over a boy in a 385px `#e7191f` cap (g1) and Donald addresses
  the boy in a 183px `#4ba23e` cap as DEWEY (g5). Both named Dewey by the
  address with the printed colour recorded, per the colourist-error rule.
- **THE `UNCA` / `UNCLE` SPLIT HELD ON ALL THREE**: every UNCLE SCROOGE is
  Donald's, every UNCA a boy's; used as the anchor on every long shot and
  silhouette where Donald and a boy could both speak.
- **Sound effects that are voices**: five Scrooge sneezes (Steamboat 157-161),
  two kookaburra laughs (Riches 169-170) and two moose SNORTs (Custard 096)
  went `sound_effect -> dialogue`; a door-knock (Steamboat 150 g3) went the
  other way; `RIVER` on a wrecked hull (160 g11) went `dialogue ->
  background`. Custard gun shots (`FUNG!`) were left `sound_effect` with the
  shooter as maker (Donald, the moose, a boy).
- **`other:` values**: Steamboat `Horseshoe Hogg`, `the stewardess`, `a River
  Belle workman`; Riches `Punter`, `Digger`, `the claim jumpers` (one
  two-man whisper), `the kookaburras`; Custard `the moose`, `the second
  moose`. Riches 178 g12-15 (four `HALLO!` over specks) are `unknown`.

### Findings to paste into the next run (2026-09-11, fifty-first batch, REVIEWED -- *The Golden Fleecing*, batch closed)

Replaces the numbers in the pass-only section below. **31 speaker
corrections, 22 of them in the 122-group nephew domain = 18.0%**
(`review_findings.py` counts 499 groups because it sweeps two pages outside
the pass; on the 465 passed groups that is 6.7%). All 23 type proposals were
confirmed; 202 g18 went to `!` and 207 g6 to `POP`. The review added three
`$` devices as Scrooge's thoughts (186 p5, 191 p6, 208 p5). Mirror clean:
465/465 on both engines, 439 `identified_by`, identical distributions. Highs
23 of 430 corrected (5.3%), **mediums 8 of 32 (25.0%)**.

| direction | n |
|---|---|
| `nephews` -> a name | 10 (187 g1 Huey, 195 g11 Louie, 200 g8 Huey, 206 g3 Louie, 206 g4 Huey, 206 g6 Huey, 207 g11 Dewey, 208 g2 Dewey, 208 g12 Huey, 213 g5 Huey) |
| one nephew -> another | 6 (190 g0 Huey -> Louie, 195 g4 Huey -> Louie, 200 g1 Huey -> Dewey, 206 g10 Huey -> Dewey, 209 g1 Dewey -> Huey, 211 g9 Huey -> Dewey) |
| a name -> `nephews` | 3 (207 g2, 207 g20, 212 g14) |
| an `other:` role | 6 (189 g2, 189 g4, 193 g0 -> `Eiprah Ali`; 204 g9 -> `Harpie Agnes`; 204 g11 -> Donald; 196 g14 `nephews` -> `the helicopter pilot`) |
| silhouettes and specks | 3 (211 g2 `unknown` -> Donald, 211 g10 `nephews` -> Scrooge, 212 g13 Donald -> Scrooge) |
| the review's own `$` adds | 3 (`none` -> Scrooge) |

- **THE DIRECTION RULE FOR GAP TIPS IS DEAD: 0 FOR 6.** Every tip the pass
  found between two heads and named by where its ray pointed was moved: 190
  g0, 195 g4, 200 g1, 206 g10 and 209 g1 went to the boy on the tip's LEFT
  (the head it had just passed), and 207 g20 went to `nephews`. With 211 g9
  (a tip on the right boy's crown, moved to the middle boy) and 212 g13 (a
  tip on Donald's cap, moved to Scrooge on his left) that is **seven of the
  eight name-for-name swaps moving one figure LEFT**. The Vol. 10 finding
  (a gap tip goes one head left) holds on Vol. 14: Barks's tails on this
  title overshoot to the right. Name the left-hand head, at medium.
- **TEN UNDER-NAMES, AGAIN ON "NO INK" BEANIES.** 206 g3/g4/g6 and 208 g2
  were outdoor panels where the 15px census read 0 on all four bands, and
  the review named all four boys off the drawing; 213 g5 was an indoor pair
  the pass called bare-headed. Same lesson as the fiftieth batch: on a
  beanie title an all-zero census at 15px is the floor, not the cap. Probe
  every crown at 8px and S>=0.06, or crop, before writing collective.
- **THE TEAL-AS-BLUE CALLS STOOD; THE TAILS DID NOT.** No correction moved a
  name because its patch colour was misread -- the drifting olive, teal and
  brown-red patches were read correctly. Every nephew swap was a tail.
- **THE SALESMAN'S COSTUME KEY WAS WRONG.** The pass pinned Eiprah Ali to the
  green robe and purple turban and called the purple-robed, green-turbaned
  'brother' a different harpie; the review gave 189 g2, 189 g4 and 193 g0 to
  Ali. A disguise is a costume that can be swapped between panels; do not
  build a per-character key from one panel (the Vol. 4 costume-key finding
  again).
- **204 g11 `OH, CERTAINLY NOT! HEE! HEE! HEE!` IS DONALD'S**, sarcastic,
  not an off-panel harpie's -- the pass read the HEE as the harpies'
  signature laugh.
- **THE `$` DEVICES ARE SCROOGE'S THOUGHTS**, as on *The Great Steamboat
  Race*: the pass did not group them and the review added them.
- **`other:` values** after review: `Eiprah Ali`, `a harpie`, `Harpie
  Agnes`, `Harpie Fay`, `Harpie Bessie`, `Harpie Inez`, `the sleepless
  dragon`, `the tailor`, `the helicopter pilot` (one typed without `the`,
  normalised before the mirror), `the mice`, `Donald and Scrooge`.

### Findings to paste into the next run (2026-09-11, fifty-first batch, PASS ONLY -- not yet reviewed)

One title, 32 pages, **460 groups**: *The Golden Fleecing* (Vol. 14,
182-213). **43 images read = 1.34 per page** (32 `page.png`, 2 panel files,
9 generated crops or grids), under the 3-per-page target; every cap call was
sampled with `capscan`/`probe`, and most contested tips came from
`tailtip` rather than crops. Two groups added (a `?` thought over Scrooge's barrel on
184 p8, a `!!` balloon over Donald on 193 p2). Missed text: **one, 207 p3
`POP`** -- g6's box holds the POP lettering but its text duplicates g5's
`BOOM / BAM` on both engines (the pass wrongly marked it `text_ok`); it is
in `queue-missed.txt` as a text fix, not an add. One text correction (202
g18 `PARSNIP PUDDING!` -> `!`, the thought circle over Scrooge's flying
hat), 23 type corrections. Mediums 32 of 460.

- **NO NEPHEW IS NAMED IN ANY LINE OF THE STORY.** `name-grep` and a direct
  grep found no HUEY, DEWEY or LOUIE on any of the 32 pages, so every one
  of the 86 named nephew groups (Huey 42, Louie 28, Dewey 16) rests on a
  cap patch and a tail, and 38 stayed `nephews`. The review is the only
  check on the palette here.
- **THE CAPS ARE BLACK BEANIES WITH A SMALL PATCH, AND THE PATCH DRIFTS.**
  Clean on 195 p3 (see the palette entry); elsewhere the green boy prints an
  olive `#737148` H57 (186 p8), a shaded `#4b6d55` H130 S0.3 (190 p3), a
  `#6aa26b` H120 under the saturation floor (199 p8); the blue boy prints
  teal `#16a2a3` H180 (190 p2), `#4da4a8` H180-189 (199 p4) and `#16a1ab`
  H184 (207 p4); the red boy prints dull `#8e421c` H20 (188 p8), `#9c402c`
  H11 (200 p1), `#ad2d16` H9 (199 p8). Each was named against the clean
  inks of the other two boys in the same panel, at medium where the patch
  was the only evidence. Check the teal-as-blue calls first.
- **THREE BOYS NAMED BY ELIMINATION** where the third patch was unreadable
  and the other two were clean: 190 g4 (Louie, shaded green recorded), 208
  g10 and 211 g8 (Louie, `cap_colour` null).
- **SIX GAP TIPS NAMED BY THE TAIL'S DIRECTION AT MEDIUM**: 190 g0, 195 g4,
  200 g1, 206 g10, 207 g20, 209 g1. Each tip stopped between two heads and
  its ray ran into one of them; the pass named that boy rather than the
  nearer head. If the review moves these, the direction rule does not hold
  on this title.
- **BARE-HEADED INDOORS, CAPPED OUTDOORS**: the boys read without caps at
  home on 192 and 194 and at Scrooge's office on 213 p4; every group there
  is `nephews` with the census header quoted per panel. 206 p2-p3 and 208
  p2 are outdoor panels where all four bands read 0 at 15px -- the beanies
  print plain black at that distance.
- **ONE BOY CARRIES THE WHOLE OF 212**: the red-patched boy (Huey, five
  different reds from `#852b1e` to `#f1171a`) does the dragon sequence alone
  and is named on all eight groups, including three thoughts.
- **THE DRAGON'S NOISES WENT `sound_effect -> dialogue`**: ROAR, HISS,
  SNORF, WHEEZE, SNORT, the AH-AH-AAH before a sneeze (197 g15, 198 g2, 199
  g9/10/12/13, 205 g7, 210 g11), plus the harpies' EEK/YIPE/SCREECH/YELP and
  the mice's SQUEECH on 207, the salesman's SNIFF! SNIFF! (184 g8/g9) and
  Scrooge's two bare `!` marks (186 g3/g4). The dragon's CHOMP (209 g4) and
  SLAM (211 g5) and Scrooge's lip SMACK (202 g12) were left `sound_effect`
  with the maker named. The reversed echo `HARPIES!` (205 g3/g4) is `none`
  at medium; a reviewer may credit it to Donald and Scrooge.
- **THOUGHT/SPEECH OVERRULED ON THE DRAWING**: 183 g12 and 192 g1 are bubble
  trails stored as dialogue; 208 g9 is a pointed tail stored as thought; 207
  g0 is a caption stored as dialogue; 190 g13 `KEEP OUT` is a door sign
  stored as a sound effect.
- **`other:` values** (check for drift): `Eiprah Ali` (the disguised
  salesman, 26), `a harpie` (48), `Harpie Agnes` (25), `Harpie Fay`,
  `Harpie Bessie`, `Harpie Inez`, `the sleepless dragon` (15), `the
  tailor`, `the helicopter pilot`, `the mice`, `Donald and Scrooge` (205 g0,
  the SEIPRAH chorus). Three `unknown`: 211 g2 (specks) and g6/g7 (eyes in
  the dark).

### Findings to paste into the next run (2026-09-12, fifty-second batch, REVIEWED -- *Three Un-Ducks*, batch closed)

Replaces the numbers in the pass-only section below. **13 speaker
corrections in 127 groups = 10.2%, all 13 in the 56-group nephew domain =
23.2%.** All 6 type proposals confirmed; no group added, deleted or merged.
Mirror clean: 127/127 on both engines, **127 `speaker_reviewed`**, 116
`identified_by`, identical distributions. Highs 11 of 119 corrected (9.2%),
**mediums 2 of 8 (25.0%)**. The last two groups (103 g2, 107 g4) were
reviewed on 2026-09-12 and both CONFIRMED as `nephews` -- neither carries
`speaker_was` -- so the tally above is the title's final one.

| direction | n |
|---|---|
| `nephews` -> a name | 11 (099 g4 Huey, g5 Dewey, g6 Louie, g8 Dewey, g9 Louie; 100 g3 Dewey, g8 Huey; 108 g3 Dewey, g4 Louie, g6 Dewey, g7 Huey) |
| a name -> `nephews` | 1 (099 g14 Dewey, the HAW! gap tip) |
| one nephew -> another | 1 (107 g2 Louie -> Dewey, cap `green` -> `blue`) |

- **A WHOLE-PANEL ZERO AT A 6px FLOOR IS STILL NOT AN ABSENCE, AND PROBING
  IS NOT LOOKING.** Ten of the eleven under-names came back carrying a
  `cap_colour` the reviewer supplied where the pass had written null --
  099 p2 (three boys on a sled, every band `0 blob(s) total` at 6px, each
  crown probed), 100 p5 (indoors), 108 p4 (under cod liver oil). The pass
  did what the last two batches asked, dropped the floor to 6-10px and
  probed every crown, and it was still wrong every time: `probe.py` reports
  the *tint over a box*, so on a 30px crown under goo or shadow it returns
  the goo. The rule that actually holds: **crop the crowns at 8-12x before
  writing a collective on a beanie title.** With the fiftieth batch's 32 of
  63 and the fifty-first's 10, under-naming on "no ink" beanies is now the
  largest correction class three batches running.
- **ABOVE ~H140 A GREEN-BAND CROWN IS AS OFTEN DEWEY AS LOUIE.** Both
  name-level colour calls the review moved were mine reading a cyan-leaning
  green as Louie: 107 g2 `#0a9c60` H155 S0.94 -> Dewey/blue, and 108 g3
  `#099e57` H151 -> Dewey -- while 108 g4's `#0b974b` H147, the *same panel*,
  is Louie. Hue alone does not separate them up there. Below H140 nothing
  was corrected: every H108-139 call stood.
- **THE IDENTICAL-INK TIE WAS OVERRULED AGAIN, TWICE.** 099 g8/g9, the
  `#429f86` pair the pass declined because both boys printed it, came back
  Dewey then Louie. As on *The Purloined Putty*: a same-value tie is the
  sampler, not the printing.
- **THE GAP-TIP RULE HELD AS A TAIL TEST AND FAILED AS A NAME.** 099 g14
  went Dewey -> `nephews`: the tip between two heads was read one head left
  onto the teal boy, and the reviewer would not take the name -- though
  099 g8's teal boy IS Dewey. Where a cap backs the gap tip it survives;
  where the cap is the only evidence it does not. 100 g3, also a gap tip,
  was named Dewey -- the left-hand reading was right.
- **THE HEDGE LANDED ON THE RIGHT GROUPS.** Both corrected mediums are the
  two green-band colour calls above; the other six mediums stood, including
  107 g6, the tip that went *against* the gap-tip rule.
- **101 g1 IS STILL `dialogue`.** The pass's note argues thought off a
  bubble visible at 1.3x, but the group carries `type_reviewed` from
  2026-08-16 and the review did not revisit it. The disagreement is on
  record in `vision_note` and nowhere else.
- **`other:` values** after review: `Grandma Duck` only. Bernie is in the
  roster.

### Findings to paste into the next run (2026-09-11, fifty-second batch, PASS ONLY -- not yet reviewed)

One title, 10 pages, **127 groups**: *Three Un-Ducks* (Vol. 17, 099-108).
**15 images read = 1.5 per page** (10 `page.png`, 5 generated crops or
stacks), under the 3-per-page target; every cap call was sampled with
`capscan`/`probe`. No missed text (audit 0/0/0), no text corrections, **6
type corrections** (dialogue -> thought on 100 g6/g7/g12/g13 and 107
g9/g10, all Donald's bubble-trailed balloons). **Mediums 8 of 127.** Speaker
split: Donald 49, `nephews` 27, Louie 11, Huey 10, Dewey 8, narrator 9,
`none` 11, Bernie 1, `other:Grandma Duck` 1.

- **NO NEPHEW IS NAMED IN ANY LINE.** `name-grep` found no HUEY, DEWEY or
  LOUIE; the 29 named nephew groups rest on a cap patch and a tail, or on
  elimination.
- **THE 27 COLLECTIVES ARE MOSTLY NO-CAP PANELS, NOT DECLINES.** The boys
  are eyes in a chest (102 p3), scrubbed and bare-headed (102 p7-p8), indoors
  (100 p5, 103 p2), under cod liver oil (108 p4), or tiny on a sled (099 p2);
  each note quotes the panel's `0 blob(s) total` or a crown probe. The
  declines that are real: two boys printing the same ink (099 p3 `#429f86`
  twice, 108 p2 H147-151 twice), a gap tip over an H139 boy beside a clean
  H110 green (100 g3), and two-tail or chorus balloons (099 g3, 107 g7).
- **TEAL NAMED AS DEWEY TWICE**: 107 g5 (`#09a19a` H177, by elimination
  against clean red and H135 green, high) and 099 g14 (`#3c9f8c` H168, a gap
  tip, medium). Check the second first.
- **THREE BOYS NAMED BY ELIMINATION**: 099 g11 and 108 g9 (Dewey,
  `cap_colour` null), 106 g6 (Huey on a dark `#7a3e2c` patch, medium).
- **GAP TIPS**: 099 g11 and g14 went one head left, per the Vol. 10/14 rule.
  107 g6 did NOT: its tip ends 17px from the middle boy's beak and its ray
  runs on to the left boy, who had just spoken g5, so it was written Huey at
  medium. If the review moves it left, the rule holds even against nearness.
- **101 g1 IS A THOUGHT THE PASS COULD NOT CORRECT.** A 1.3x crop shows a
  bubble between the balloon and Donald's head, but both engines carry
  `type_reviewed` from 2026-08-16 as `dialogue`, so `vision_apply` kept the
  review's label and no queue shows it. The note says thought.
- **`other:` values**: `Grandma Duck` only (108 g16). Bernie is in the
  roster.

### Findings to paste into the next run (2026-09-12, the first two Vol. 5 one-pagers)

*Fashion in Flight* (026) and *Turn for the Worse* (027), passed and reviewed
the same day. **22 groups, 1 speaker correction -- and it belongs to a group
the review ADDED, not to any call the pass made.** Highs 0 of 9 and 0 of 12
corrected; no type corrections, no text corrections, no `other:` drift. **3
images for 2 pages** (one `page.png` each, one 2.6x crop).

- **A ONE-PAGER IS NOW PREPPED LIKE ANY OTHER TITLE.** `vision-prep --title
  "Fashion in Flight"` works as of 2026-09-12, so the hand-built out-dir the
  Vol. 11 nine needed is gone. Run them one title at a time: each then carries
  its OWN cast anchors, where Vol. 11's queue had to name *The Golden Helmet*
  and *The Gilded Man* and ran with `story_cast: []`. `vision-status` still
  leaves one-pagers out of the work list, so they are asked for by name and
  never offered by `--todo`.
- **THE DUPLICATE-STRING TRAP RECURRED, AND IT WAS AVOIDABLE.** 026 prints the
  `313` plate on panel 4 AND panel 5. The pass grouped the first, missed the
  second, and the missed-text audit called the page clean because
  `visible_text` held `313` once and that single string matched the single
  group -- so the reviewer had to add the group by hand. This is the known
  second-copy blind spot, and the zero-image caption-box sweep exists for
  exactly it and was not run. Record each occurrence separately (026's capture
  now lists `313` twice) and run that sweep before handing back.
- **A SEVEN-PANEL GAG IS THE CHEAPEST UNIT IN THE CORPUS.** Two or three
  characters, no nephews, no cap work at all, every call resting on a traced
  tail or on what the line says. Both pages went high across the board and
  both came back untouched. On a one-pager with no nephews, spend nothing on
  the cap tooling -- read the tails and go.
- **DAISY ANSWERS THE GAG.** 026 g8 `WELL?` is Daisy at her own house, named
  from the tail plus Donald's own thought two panels earlier ("ROAR PAST
  DAISY'S HOUSE"); a 2.6x crop settles the bow and dress. The visitor on 027
  is `other:the insurance man`, role-named after the corpus habit (`the ticket
  agent`, `the taxi driver`) rather than `the stranger`, which is only how
  Donald addresses him.
- **`other:` values**: `the insurance man` (027, 3 groups). Nothing else.

### Findings to paste into the next run (2026-09-12, twenty one-pagers Vols. 5-8, REVIEWED -- batch closed)

All twenty reviewed and mirrored, 290/290 on both engines. **13 speaker
corrections in 290 groups, 4.5%**; in the nephew domain **12 of 90, 13.3%**.
By the confidence the pass wrote: **high 13/284 = 4.6%, medium 0/6 = 0.0%**.
**Zero wrong-nephew swaps, zero over-namings, zero Donald-against-nephew.** All
25 type corrections were the pass's own proposals, confirmed; 0 text
corrections, 0 missed text. Cost was 1.6 images per page.

- **NINE OF THE THIRTEEN ARE ONE TITLE, AND ALL NINE ARE ONE SENTENCE I WROTE.**
  *Tied-Down Tools* came back **9 of 17 groups, 100% of its nephew domain**,
  every one `nephews` -> a name, and **the reviewer recorded a cap colour on all
  nine** -- red, green, blue, in three clean cascades of three. My note said
  *"Bare-headed throughout this story, so every nephew call here is a
  collective"*, written off one band row (`red=0 green=0 blue=10`) on panel 2
  and the pyjamas in the opening panels. The caps are there later in the story.
  This is exactly the failure `roster.txt` names -- **a cap fact is a per-panel
  fact** -- and a title-wide absence claim copies itself into every note in the
  domain and is wrong in every one of them.
- **THE CONTROL EXPERIMENT IS IN THE SAME BATCH.** *King-Size Cone* has the
  identical structure -- three cascades of three balloons over three boys -- and
  came back **0 corrections in 9 names**, because there I cropped each panel and
  read the bands. Same shape, opposite outcome, and the only difference is one
  tiled image. **A three-balloon cascade over three boys is where both the wins
  and the losses concentrate on a one-pager: crop it, every time, even when the
  page looks bare-headed.** The nine names in *King-Size Cone*, three in *Noise
  Nullifier*, three in *Horseshoe Luck* and two in *Tunnel Vision* all survived
  untouched -- eighteen names made, eighteen held.
- **A HUE GATE CAN BE TOO STRICT.** *Sleepy Sitters* 214 g1/g2 went `nephews` ->
  Dewey and Louie with blue and green recorded. I had measured those crowns at
  `#56943e` (H97) and `#49a34b` (H121) and rejected both for not being the
  Vol. 7 cap green at H111. The reviewer named them anyway. Treat the H111
  figure as the centre of a band, not a gate: an off-hue crown on a boy's head
  in a cascade is still a cap, and elimination across the three does the rest.
- **THE ONE NON-NEPHEW REVERSAL IS A TWO-HANDER TAIL.** *The True Test* 211 g6,
  `I HAVEN'T TOSSED ONE OF THESE BOOMERANGS SINCE I WAS A KID!`, went
  `other:the toy salesman` -> **Donald**. I gave it to the adult because the
  line reads as an adult reminiscing and he is the one who throws it. Register
  is not evidence: on a two-hander with both figures drawn, trace the tail.
- **A CENSUS ZERO ON A SKULL IS STILL NOT AN ABSENCE.** *Bean Taken* 102 g8 went
  `nephews` -> Huey with red recorded, against my note that the census put no
  CAP-INK on either skull it found in that panel.
- **THE LOGO IS ONE GROUP, NOT TWO -- SAY SO INSTEAD OF TYPE-CORRECTING BOTH
  HALVES.** The review merged `Donald / Duck` + `By / Walt Disney` into a single
  group on *Jumping to Conclusions* 210 and *Slippery Shine* 215, which is why
  the batch closed at 290 groups against the 292 applied. Both are titles where
  the engine split the logo and I proposed a type change on each half. When the
  logo arrives as two groups, flag the split in `note` and let the review merge
  it; correcting both halves just entrenches the split.
- **Medium was not the risk this time, but there were only six of them.** 0 of 6
  medium corrected against 13 of 284 high, which inverts the usual pattern
  (31.0% against 7.3% on *Lost in the Andes!*). On a one-pager the pass is
  mostly either certain or forced, so the medium sample is too small to read
  anything into.
- **Two tool notes.** `--since` earned its place again: two `type_was` rows
  dated 2026-08-10 (*Bean Taken* 102 g4, *Sorry to be Safe* 103 g8) are durable
  survivors of an older adjudication and were correctly excluded from this
  batch's count. And `review_findings.py` **cannot be run corpus-wide with
  `--since`**: it takes the first argument not starting with `-` as the title,
  so the flag's value is swallowed as a title name and the run dies with a
  `KeyError`. Run it per title.

### Findings to paste into the next run (2026-09-12, twenty one-pagers, Vols. 5-8, PASS ONLY -- not yet reviewed)

Twenty one-pagers in one batch, oldest first off the `ONE_PAGERS` work list:
Vol. 5 *Machine Mix-Up*; Vol. 6 *Bird Watching*, *Horseshoe Luck*, *Bean Taken*,
*Sorry to be Safe*, *Best Laid Plans*, *The Genuine Article*; Vol. 7 *Jumping to
Conclusions*, *The True Test*, *Ornaments on the Way*, *Too Fit to Fit*, *Tunnel
Vision*, *Sleepy Sitters*, *Slippery Shine*, *Fractious Fun*, *King-Size Cone*;
Vol. 8 *Toasty Toys*, *No Place to Hide*, *Tied-Down Tools*, *Noise Nullifier*.
**292 groups, 27 type corrections, 0 text corrections, 0 missed text.**
**32 images over 20 pages = 1.6 per page** (one `page.png` each plus 12 crops).

- **THE STORY LOGO IS TYPED THREE DIFFERENT WAYS AND IS WORTH CHECKING ON EVERY
  ONE-PAGER.** It came stored as `title` on most, as `background` on *Jumping to
  Conclusions* (both the logo and the byline, 2 groups), and as `narration` on
  *Too Fit to Fit* and on both halves of *Slippery Shine*. **6 of the batch's 27
  type corrections are the logo alone.** It costs nothing to look at g0 and g1
  before reading anything else.
- **A ONE-PAGER'S TYPE ERRORS CLUSTER ON THE SOLO-DONALD STRETCH, SO CHECK THE
  WHOLE STRETCH ON ONE CROP.** *Toasty Toys* panels 2, 3 and 4 are all stored
  `dialogue` and are all cloud-plus-bubble-trail thoughts; one 1.3x stack of the
  three necks overruled all three at once. *Machine Mix-Up* was the same shape
  (2 of its 3). When a page has four consecutive panels of Donald alone, read
  their balloon necks together rather than one at a time -- and note that the
  engine often gets ONE of the run right, which is the tell that the others are
  wrong.
- **CHARACTER-MADE NOISE IS THE OTHER HALF OF THE TYPE WORK: 15 OF 27.** `WAK!`,
  `GULP!`, `WHEE!`, `OUCH!`, `UMPH!`, snoring, and the boys' mouth-made aeroplane
  noises (`BZZAZZ!`, `RRAZZZ!`, `ROAR!`, `ZOOM!`, `ZOW!`) all went
  `sound_effect` -> `dialogue` with the maker named. **The clincher is usually in
  the dialogue, not the drawing**: *Noise Nullifier* g4 says `YOU KIDS ARE MAKING
  SO MUCH NOISE`, which settles five groups in one line. Impacts (`CLONK!`,
  `WHOP!`, `CRACK!`, `BAM!`, `THUD!`, `CLICK!`) stayed `sound_effect` / `none`.
- **VERIFY A TEXT CORRECTION AT 4x BEFORE PROPOSING IT -- THIS BATCH'S ONLY
  CANDIDATE WAS WRONG.** *Noise Nullifier* 141 g8 reads `WE'LL` on `page.png`
  and the stored text says `WELL`; at 4x the art has **no apostrophe** and the
  stored text is right. The batch closed at **0 text corrections**, and the one
  that looked certain off the overview would have been a false correction. This
  is the roster's own warning firing exactly as written.
- **RUN THE CAPTION SWEEP, BUT CROP ITS HIT BEFORE WRITING IT UP.** It fired once
  in twenty pages -- *Toasty Toys* 077 panel 3, `130x438 fill=0.82 border=3/4
  overlap=0% NO GROUP` -- and a 3x crop shows a plain yellow wall with doorframe
  hatching: no border box, no lettering. A false positive. The sweep is still
  worth its zero cost, but its output is a candidate, not a finding.
- **THE CHEAPEST NAMES IN THE CORPUS COME FROM THE DIALOGUE, NOT THE CAP.**
  *Tunnel Vision* names two groups **Louie** for no images at all: g1 addresses
  HUEY, g2 (the same speaker, continuing) addresses DEWEY, so elimination leaves
  Louie -- and g3 corroborates it independently with `LOUIE'S HOGGING THE VIEW`.
  The boys are bare-headed indoors and every band row in those panels is
  `red=0 green=0 blue=0`, so no cap could ever have done it.
- **A THREE-BALLOON CASCADE OVER THREE CAPPED BOYS IS THE BEST VALUE IMAGE ON A
  ONE-PAGER.** *King-Size Cone* turned **nine** would-be collectives into nine
  names off two stacked crops: panels 2, 4 and 6 each show three boys wearing
  clean blue, green and red bands, one tail each. **Crop each panel rather than
  carrying the left-to-right order across** -- panel 2 was cropped separately and
  only then found to match. *Noise Nullifier* panel 7 did the same for three more,
  where cap band AND shirt trim carry the same ink on each boy.
- **TWO TAILS ON ONE BALLOON IS A COLLECTIVE, NOT THE NEAREST CAP.** *Bird
  Watching* 038 g12 `ULP!` sits directly above a clean red cap, and the cheap
  read is Huey. At 3x the balloon has **two** pointed tails, landing on the
  red-capped and the blue-capped boy. Two boys share the utterance, so it is
  `nephews` -- and the clean cap under the balloon is a trap.
- **ONE-PAGERS ARE MOSTLY BARE-HEADED, SO MOST NEPHEW CALLS ARE FORCED.** Indoor
  domestic gags dominate: *Jumping to Conclusions*, *Tied-Down Tools*, *Tunnel
  Vision*, *Best Laid Plans*, *No Place to Hide*, *Fractious Fun* and *Toasty
  Toys* put the boys in pyjamas, bandages or bare heads throughout. Establish it
  once per panel from the band row and move on; do not spend crops hunting ink
  that is not printed.
- **`vision-status --titles --todo` STILL OMITS ONE-PAGERS**, so they have no work
  list of their own. **`scripts/vision/one_pager_todo.py`, added with this batch,
  rebuilds one** -- it walks `ONE_PAGERS`, resolves each through `title_pages`,
  and keeps `vision_status`'s own test for "read": any group carrying
  `vision_note`, never `speaker`. Run it instead of deriving the list again:

      uv run --offline python scripts/vision/one_pager_todo.py

  Of the 155 one-pagers, **50 resolve to no pages at all** and are not a backlog
  -- they are simply not in the restored volumes. After this batch **32 are read
  and 73 unread**; it was 12 and 93 before it, and the next batch comes off the
  `--` rows, oldest first.
- **`other:` values used** (8 distinct): `the doctor` (*Horseshoe Luck*, *Best
  Laid Plans*), `the antique dealer` and `the expressman` (*The Genuine
  Article*), `the toy salesman` (*The True Test*), `the tree salesman`, `the
  store clerk`, `a rival shopper` and `a shopper in the crowd` (*Ornaments on the
  Way*). The indefinite article on the last two is deliberate: they are two
  different shoppers in adjacent panels filling one role, and a crowd voice that
  cannot be pinned to a figure.
- **Two boxes flagged rather than changed**, both an engine merging two balloons
  into one group with correct text: *Ornaments on the Way* g17 and *Fractious
  Fun* g8. Said in `note`, not corrected.

### Findings to paste into the next run (2026-09-14, fifty-third batch, REVIEWED -- *Secret Resolutions*, batch closed)

*Secret Resolutions* (Vol. 17, 109-118), one title. **143 groups passed; the
review added 2 (145 on both engines). 0 speaker corrections to any call the
pass made** -- the two `unknown -> ...` rows `review_findings.py` prints are the
two added groups being given their first speaker, not overrulings. By the
confidence the pass wrote: **high 0/139, medium 0/4.** All 3 type proposals
(dialogue -> thought) confirmed; 0 text corrections. **13 images for 10 pages =
1.3 per page.**

- **A BUBBLE TRAIL WITH NO POINTED TAIL IS A THOUGHT, EVEN ON A SMOOTH-EDGED
  BALLOON.** All three type corrections were that shape: 111 g13 `HA!`, 115 g1
  (a cloud edge), and 116 g16 (Donald gloating at the window). Two older
  `type_was` rows on this title (114 g13, 116 g2, adjudicated 2026-08-16) are the
  same move, so the engine calls this construction `dialogue` habitually on
  this story. The 2x crop of 111 g13 was the one worth taking; the other two
  read off `page.png`.
- **THE DIALOGUE NAMES THE PHOTOGRAPHER, AND THE NAME CARRIES.** 17 Dewey calls,
  all held: 115 g15 answers `SIT DOWN, DEWEY`; the 116 p3 caption names him with
  the camera; 117 g12 `HA! DEWEY!`. Carrying "the detective" and "the camera's
  owner" across pages 116-118 held on every call, including the two left at
  medium (118 g2, g10). This is a DIALOGUE key, not a prop key -- the line says
  whose camera it is -- which is why it travelled where costume keys do not.
- **PYJAMAS NAME THEM (114).** Clean `#00a5d7` / `#e61b1f` / `#4fa43d` H110 on
  the three garments named six groups; all held. The 114 p2 silhouettes stayed
  `nephews` and were not changed.
- **A TIP ABOVE THE CROWNS WENT TO THE RAY, AND HELD.** 110 p7 g9: the tip stops
  30px above the crowns, inside the green boy's head span but pointing at the
  red cap's bill, with the green boy already holding g10. Huey at medium,
  confirmed. Evidence for the gap-tip-goes-LEFT rule on Vol. 17, one case.
- **DARK SLIVERS STILL NAME IN A SAME-SCENE ROW.** 110 p8 and 111 p1 print the
  middle boy's red as `#812813` H11.5 (111px) and `#873a1a` H17.6 (62px), and the
  right boy's green as teal `#449a87` H166.7. Named against a clean blue in the
  same panel; all held. 111 g2 (a crown with no roster ink, named Louie by
  elimination at medium) held too.
- **MISSED TEXT: A CALENDAR, AND A LONE `?` THE AUDIT CANNOT SEE.** The audit
  flagged 109's calendar lettering; the review added it. The drawn `?` over
  Donald on 113 p1 was NOT flagged -- a single character never matches -- and was
  found only by reading, then added. List a lone device in the missed-text queue
  by hand.
- **MY `visible_text` TRANSCRIPTION WAS WRONG, AND THE AUDIT KEPT FIRING ON IT.**
  I wrote `JANUARY 1st`; the reviewer read the art as `JANUARY 56` (the added
  group first arrived as OCR's `JANUARY 54`). Cramped calendar lettering is not
  a transcription to guess at: crop it at 4x, and if it will not read, say so in
  the capture rather than writing the date the story implies. The capture was
  corrected (a misreading, not a suppression).
- **A REVIEW ADD RENUMBERS AND STRANDS A SIGN-OFF.** The calendar group went in
  at 109 g4, which moved Donald's g4 to g5, and that group came back never
  `speaker_reviewed` -- a one-group straggler created by the add itself.
  Count stragglers after any review that added groups.
- **`other:` values**: none.

### Findings to paste into the next run (2026-09-14, fifty-fourth batch, BOTH REVIEWED AND MIRRORED -- batch closed)

*The Ice Taxis* (Vol. 17, 119-128) and *Searching for a Successor* (Vol. 17,
129-138). **Ice Taxis: 116 groups, 4 speaker corrections** (3 of the 21 in the
nephew domain); by the confidence the pass wrote, **high 2/106, medium 2/10**.
All 3 type proposals confirmed; 0 text corrections. **Searching: 138 groups
passed, the review added 2 (140), 7 speaker corrections; high 2/131, medium
0/4, low 3/3.** Both type proposals confirmed; 0 text corrections. **31 images
for 20 pages = 1.55 per page** (16 and 15).

- **A GAP TIP BETWEEN TWO CLOSE HEADS IS A COLLECTIVE (Ice Taxis 120 g11).**
  The tip sat 10px right of the blue-cap boy and 17px left of the green-cap
  boy, pointing left; the pass named Dewey at high off the gap-tip-goes-left
  rule and the review made it `nephews`. With two heads within ~20px of the
  tip, the direction did not decide it on this title.
- **A BALLOON WITH NO TAIL GOES TO THE BOY UNDER IT, BY ELIMINATION (120 g6).**
  The neighbouring balloon's tail had already named Dewey, and the green-cap
  boy stands directly under the tail-less one. The pass wrote "not named";
  the review named Louie. The eliminate rule was available and not applied.
- **CROP A BIG ADULT'S TAIL WHEN BOYS STAND BEHIND HIM (123 g6).** Called the
  mayor at high off `tailtip` alone, with no crop and no cap check; the tail
  goes past him to the red-pom boy behind the sofa. The review named Huey. It
  was the only adult call corrected in either title.
- **AN ART-AGAINST-DIALOGUE FLAG GOT RESOLVED, NOT OVERRULED (122 g0).**
  `ALL CLEAR, DEWEY! YANK THE STARTER`, with the tail on the blue-cap boy: the
  pass declined to name anyone and said why. The review named Huey and kept
  the printed blue, so the name came from the dialogue, not the cap. Flag the
  conflict rather than picking a side.
- **COUNT EVERY TAIL ON A BALLOON (Searching 129 g6).** `GET AWAY, CHISELER!
  I SAW THAT HAT FIRST!` -- the pass measured one tail onto Donald; the
  balloon has a second tail onto Gladstone, and the review made it
  `other:Donald and Gladstone`.
- **A VOICE INSIDE A BUILDING THE BOYS ARE IN IS `nephews`, NOT `unknown`
  (137 g12-g14).** Three tails run into the factory roof in a long shot with
  nobody drawn, after the page has shown Donald and the boys inside. All three
  were `unknown` at low; all three came back `nephews`.
- **SAMPLE A CAP BEFORE DECLINING TO NAME ITS WEARER (137 g9).** The note
  said the cap "was not sampled" and wrote `nephews`; the review named Louie
  off a green cap. One `capscan` would have settled it.
- **MISSED TEXT THE AUDIT CANNOT SEE: A REPEATED WORD AND A TAG NOBODY
  TRANSCRIBED.** The audit reported 0 on Searching. 133 p2's second
  `FEATHERS` sack was matched against the grouped `FEATHERS` on panel 8 of the
  same page, and 130 p1's price tag was never in `visible_text`. A crop stack
  found both, they went into `queue-missed.txt`, and the review added them. The
  tag reads `10.96`; the pass flagged the last digit as 8-or-6 at 3.5x rather
  than guessing, which was right.
- **TYPE: ALL FIVE PROPOSALS HELD.** Bare devices (`!`, `? ? ? ?`) and a
  bubble-trailed `OH, OH!` went to thought; a dog's `ROWF` and Donald's
  off-panel `TAXI! TAXI!` went to dialogue.
- **A STRAGGLER NEXT TO A CORRECTED GROUP (120 g7).** The review changed
  120 g6 and left its neighbour g7 without `speaker_reviewed`; it was signed
  off from a one-line queue before the mirror.
- **`other:` values**: `the mayor`, `the mayor's dog`, `a fish fry official`,
  `a fisherman`, `a householder`, `a passer-by`, `Mrs. Murphy`,
  `Donald and Gladstone`.

### Findings to paste into the next run (2026-09-14, fifty-fifth batch, ALL THREE REVIEWED AND MIRRORED -- batch closed)

*The Olympic Hopeful* (Vol. 17, 139-148), *Gopher Goof-Ups* (Vol. 17,
149-158) and *In the Swim* (Vol. 17, 159-168). **Gopher Goof-Ups: 131 groups
(129 passed, 2 added), 10 speaker corrections** (8 of the 45 in the nephew
domain, 17.8%); **high 7/127, medium 2/2**. All 3 type proposals held; 0 text
corrections; **20 images for 10 pages (2.0 per page)**. **Olympic Hopeful:
132 groups (130 passed, 2 added), 6 speaker corrections** (4 of the 36 in the
nephew domain, 11.1%); by the confidence the pass wrote, **high 5/122, medium
0/8**. All 13 type proposals held; 0 text corrections. **In the Swim: 122
groups (121 passed, 1 added), 12 speaker corrections** (11 of the 44 in the
nephew domain, 25.0%); **high 12/121**, no mediums. All 6 type proposals held
and one more was set by accident (below); the one text correction (159 g5
`SEA HORSES` -> `SEA HORSEMEN`) held. **Images: 18 for 10 pages (1.8 per page)
and 15 for 10 pages (1.5 per page).**

- **A GARMENT IN THE ROSTER INKS IS THE KEY, EVEN WHEN ONE PANEL PRINTS IT
  BADLY (In the Swim, 10 of 12 corrections).** The boys are bare-headed in
  swimsuits striped red, green and blue for almost the whole story. The pass
  declined the stripes as "a costume key that printed blue, red and black on
  160 p5" and wrote 42 collectives; the review named ten of them off the
  stripe (160 g5-g6, 161 g1, 162 g7, 164 g9-g11, 167 g1-g2, 168 g10), even
  on shaving-plastered boys. On 160 p5 the review named the blue- and
  red-striped boys and left the third, whose stripe reads black underwater,
  alone: one unreadable stripe does not void the other two. Read the stripe
  as the cap -- `cap_colour` takes
  any garment carrying the inks -- and decline only where no stripe shows.
- **A CLOSE-HEADS GAP TIP WAS NAMED THIS TIME, NOT MADE COLLECTIVE (162 g7,
  167 g2, Olympic 148 g5, Gopher 155 g11 and 157 g4).** The Ice Taxis rule
  (two heads within ~20px of the tip -> `nephews`) was applied five times and
  overturned five times: the
  review named the boy by his garment or cap, and on 167 g2 by elimination
  ("Not Huey or Louie"). Treat the collective as the fallback when nothing
  names either boy, not as the answer whenever the heads are close.
- **ELIMINATION BUILT ON A TEAL IS ELIMINATION BUILT ON A GUESS (Gopher 150
  g1, Dewey -> Louie).** The middle boy's `#08a678` H162.5 patch was taken as
  Louie's green, which left the capless first boy as Dewey at medium; the review
  named the first boy Louie. The teal was the blue, so the elimination ran the
  wrong way. Both Gopher mediums were corrected (the other, 151 g11, was a 6px
  bump read as a tail onto a boy; the line, `OH, MY BUGGIN' EYE BULBS!`, went
  to Donald).
- **OVER-NAMING ON BOYS MOVING TOGETHER (Gopher 149 g5, 155 g7).** A tip on
  the first of three boys walking in, and one inside the first of three boys
  holding Donald back, were both withdrawn to `nephews`. When the boys act as a
  group and the line speaks for them, a tip on the leading boy is not enough.
- **H140s TEAL ON VOL. 17 IS DEWEY'S BLUE (168 g14, Louie -> Dewey).** The
  ladder boy's crown probed `#3dae6b` H142.6 and the pass named Louie against a
  clean red. The review made him Dewey. This is the Three Un-Ducks split again
  (H147-177 goes either way, and now H142): without a clean green on another
  boy in the same panel, do not write Louie off a green-band hue above ~H140.
- **A RAIN-WASHED CROWN IS NOT A BARE ONE (Olympic 147 g13-g14, 148 g5).**
  In the rain the probes returned only the rain-grey sky (blue band S<=0.46)
  and the pass wrote three collectives; the review named Dewey (blue) and Huey
  twice (red). A probe box dominated by rain streaks hides a small patch --
  crop the crown at 3x instead of trusting the histogram.
- **A 'WE' LINE WITH ONE TAIL WAS WITHDRAWN TO THE COLLECTIVE (Olympic 140
  g1).** `WE STILL HAVE OUR DOUBTS!`, tip inside the green-cap boy's span, was
  named Louie at high; the review made it `nephews`. The only over-naming in
  either title.
- **A CAP COLOUR ADDED UNDER AN ADDRESS-NAMED BOY (Olympic 148 g6).** Named
  Huey at medium by elimination from `SHOVE HIM, LOUIE`, cap null; the review
  kept Huey and recorded the cap as green. Flag it: the printed ink and the
  address disagree.
- **A MISSED-TEXT ADD RENUMBERED A PAGE UNDER A QUEUE ALREADY BUILT (In the
  Swim 160).** The fish `?` from `queue-missed.txt` went in as g4 and every
  later id moved by one. The queued type confirm for the `?` device (old g5)
  landed on `WHAT'S THAT THING?` (new g5), which became `thought` and was then
  kept; the real `?` (new g6) stayed unconfirmed through a second pass of the
  queue; and old g9, now g10, was never reached. **Rebuild the speaker and
  corrections queues after the missed-text adds**, or deliver them only once
  the adds are in.
- **TWO EDITOR SEED TRAPS ON ONE PAGE (Olympic 148).** Copying in the cup
  inscription left a duplicate of g15 (`DOGGONE! YOU KIDS MAKE ME FEEL...`,
  same box, `vision_added`, reviewed) while the original stayed unreviewed, and
  the new cup group arrived with the balloon's quotes and markup. Both were
  fixed before the mirror. Check an added group's text, box and siblings
  against the page before mirroring.
- **MISSED TEXT: both single-character devices were real.** The `!` over
  Whirlman Dervish (145 p8) and the `?` over the fish (160 p4) were added as
  `other:Whirlman Dervish` and `other:a fish`; the audit could not see either.
  The review also added the cup's lettering on 148 p7, which the pass had put
  only in `visible_text`. On Gopher the two licence plates were added (150 p6
  reads `313` by the review; the pass transcribed `13`, so a plate read from a
  crop can drop a digit) and the 156 p2 price card went to `missed-text-ignore.txt`.
- **TYPE: all 22 proposals held** -- crowd `BOO`s and sneezes to dialogue, PA
  balloons and a window balloon stored as narration to dialogue, a pink
  caption box stored as dialogue to narration, bubble-trailed balloons and
  bare devices to thought, and the three story logos to `title`.
- **`other:` values**: `the announcer`, `the crowd`, `a spectator`, `a judge`,
  `the starter`, `the orator`, `the schoolteacher`, `Rocketflash's wife`,
  `Chief Bounding Rabbit`, `Fulldrip Pulpbugle`, `Whirlman Dervish`,
  `the submacycle owner`, `a fish`.

### Findings to paste into the next run (2026-09-14, fifty-sixth batch, PASS ONLY -- not yet reviewed)

*Land Beneath the Ground!* (Vol. 16, 028-056), *Trapped Lightning* (Vol. 20,
129-132) and *Camping Confusion* (Vol. 17, 169-178), all 1955. The name-grep
found no nephew name in any line of the first two; *Camping Confusion* names
Louie and Huey on 172 p7, which is where its palette comes from.

| title | groups | medium | nephew domain (named / collective) | type | text | missed text | images |
|---|---|---|---|---|---|---|---|
| *Land Beneath the Ground!* | 423 | 65 | 108 (81 / 27) | 9 | 1 | 1 | 48 / 29 = 1.66 |
| *Trapped Lightning* | 51 | 0 | 0 | 0 | 0 | 0 | 4 / 4 = 1.00 |
| *Camping Confusion* | 133 | 12 | 46 (32 / 14) | 4 | 0 | 1 | 14 / 10 = 1.40 |

**Batch: 607 groups, 66 images over 43 pages = 1.53 per page.** Missed text:
052 p3 `S GROC` (the strip of paint peeled off the grocery) and 169 p1 `ZZZZ`
(Donald snoring), both parked in the titles' `queue-missed.txt`.

- **TWO TAGGED CASTS, TOLD APART BY NECKWEAR (Land Beneath).** The roster tags
  `Fermies` and `Terries`, and 042 p4 states the key: Terries wear bow ties,
  Fermies four-in-hands. **Body colour is not the key** -- red, orange, green and
  blue creatures appear on both sides. 68 `Fermies` and 21 `Terries` calls; where
  the tie is too small or turned away, the call is medium and follows the guide
  by continuity. **The cheers are not a key either**: `RAH! RAH! RAH!` is cheered
  for the Fermies and `CHA! CHA! CHA!` for the Terries on 050, but 055 g3's
  `CHA! CHA! CHA!` comes from a necktied Fermy. A mixed crowd is
  `other:Terries and Fermies`.
- **OFF-PANEL YELPS FROM A CAR HOLDING TWO ADULTS WENT TO DONALD AT MEDIUM (032
  g2, g5; 036 g3, g5).** The runaway car carries Donald and Scrooge, both out of
  sight. Scrooge is as likely; expect the review to move some.
- **`identified_by` IS REQUIRED ON `unknown` TOO.** Five groups under the moss or
  among specks (049 g13-g14, 050 g6, g8, g9) were written `unknown` without it,
  and the dry run refused all five. The roster says omit it only for `none`.
- **THE VOL. 16 BLUE DRIFTS TEAL IN SHADE, AND THE PASS NAMED IT DEWEY AT MEDIUM**
  (033 g4 `#299b9a` H180.5, 048 g12 `#1e919c`, 055 g12 `#3aa368` H146, and 036 g2,
  041 g6, 052 g8 read off crops). The clean green on this title is H110 in
  `leafgrn`, so anything cooler than ~H140 was taken as the blue. Untested.
- **CAMPING CONFUSION'S KEY IS IN ITS DIALOGUE (172 p7-p8).** `RODMAN LOUIE`
  carries the rod and wears the green cap `#019d47` H147; `CHARTMAN HUEY` holds
  the chart board and wears red `#e52020`; the telescope boy is blue. The props
  held for 171-173 and broke on 175 p2, where the blue-teal boy holds the map --
  **name off the cap and cite a prop only as corroboration.**
- **TEAL CAPS ON CAMPING CONFUSION: ONE DECLINED, TWO RANKED.** 173 g0 `#0ba570`
  H159 sits between the title's green (H147) and blue (H184) with only a red boy
  beside it, and on Vol. 17 an H162.5 patch was Dewey (Gopher Goof-Ups) -- so
  `nephews`. 178 g14-g15 had a green (`#217a46` H141) and a teal (`#0ba593` H172)
  in one panel and were named Louie and Dewey by ranking, at medium.
- **A DIALOGUE-VS-CAP CONFLICT IS FLAGGED ON 173 g1.** The red-capped boy's tail
  says `I'LL GO SEE IF HE'S VISITING ONE OF THE OTHER CAMPERS!`, but the boy who
  comes back with the news on panel 2 wears the clean green cap. Recorded as
  Huey at medium with the conflict in the note.
- **CHECK A FIGURE AGAINST LATER LINES BEFORE WRITING ROLE NOTES.** The camper
  with the leashed children was first noted as a man; Donald calls her `THAT
  WOMAN` on 171 and `LADY` on 178. The notes were fixed before the apply;
  `other:a camper` was right either way.
- **ON CAMPING CONFUSION THE FOLIAGE AND THE URANIUM BUTTON SIT ON THE HEADS.**
  The forest green `#347e4c`/`#337f4d` H141 lands inside head spans on most
  outdoor panels and names nobody; every cap carries a pink button `#ea5551`
  S0.64 that the census reports as red. The cap red here is S0.8 and up.
- **BARE HEADS FORCED 9 COLLECTIVES (Camping Confusion 177 p4-p7).** The bears
  take the caps on 176; `title_bands` reads red 0, green 0, blue 0 blob(s) total
  on 177 p4, p5 and p6, quoted in each note.
- **TYPE: 13 proposals.** Land Beneath: the splash logo stored as narration to
  `title` (028 g0); a broadcast jingle, a shout lettered bare, `GRIPE! GRUMBLE!`
  and the crowd's `YES!` from sound_effect to dialogue (039 g12, 046 g3, 046 g11,
  055 g8); a boxed `So--` stored as dialogue to narration (043 g1); a tailed
  `IT'S ON!` stored as background to dialogue (045 g12); a pointed tail stored
  as thought to dialogue (046 g4); a bubble trail stored as dialogue to thought
  (047 g10). Camping Confusion: two bubble trails to thought (173 g12, 174 g7),
  a pointed tail to dialogue (176 g4), and the bear's `ROWR` to dialogue (177 g2).
- **TEXT: one proposal, Land Beneath 055 g7 `SURE` -> `SHORE`**, the creatures'
  cowboy dialect, read at 2x.
- **`other:` values**: Land Beneath `the foreman`, `a digger`, `the grocer`, `a
  grocery clerk`, `a policeman`, `a ferry passenger`, `a bellhop`, `a radio
  singer`, `a radio newsman`, `the professor`, `a Terry and a Fermy`, `Terries
  and Fermies`; Trapped Lightning `a kid`, `a racing driver`, `a housewife`, `a
  customer`; Camping Confusion `a camper`, `a bear`, `a bear cub`.

### Findings to paste into the next run (2026-09-15, fifty-sixth batch, ONE OF THREE REVIEWED -- *Land Beneath the Ground!*)

**423 groups, 24 speaker corrections (5.7%), 20 of the 107 in the nephew domain
(18.7%)**; by the confidence the pass wrote, **high 17/358 (4.7%), medium 7/65
(10.8%)**. All 9 type proposals and the one text correction held; no group was
added, and 052 p3 `S GROC` is still ungrouped. Mirrored clean onto paddleocr.

- **UNDER-NAMING IS HALF THE CORRECTIONS: 10 COLLECTIVES NAMED.** Three kinds,
  all of them evidence the pass had and declined:
  - **A desaturated cool sliver was Dewey's blue both times** (037 g12
    `#6ca5ab` S0.37, 042 g7 `#67a0a1` S0.36). The pass declined for want of a
    clean cool cap to rank against; on this volume the green is H110 and never
    that cool, so a grey-cyan sliver is the blue.
  - **A brown-orange patch was Huey's red** (037 g13 `#965c2e` H36). Read a
    muddy warm patch on a Vol. 16 crown as the red, not as "not a roster ink".
  - **Tiny heads, silhouettes and an identical shaded green were all named**
    (032 g15-g16 in the far car, 042 g8 the silhouette, 033 g12-g13 two boys both
    probing `#5f9665`, 039 g11 a tip where two heads meet). The review named them
    from the order in the car and the neighbouring panels; identical ink on two
    boys does not stop a name.
- **DONALD -> SCROOGE THREE TIMES, ON LINES DRAWN OVER DONALD (041 g1, g4; 036
  g5).** 041 g1's tip sat 22px from Donald's cap and 041 g4's on the middle
  silhouette, and both went to Scrooge; 036 g5 was one of the four runaway-car
  yelps given to Donald at medium, and the other three held. **Check the line's
  voice against Scrooge before taking a tail near both heads.**
- **FERMIES -> TERRIES THREE TIMES (041 g10, g12; 051 g4).** Every one was an
  orange creature the pass called "necktied" at page scale. **Crop the neck before
  naming a side**: the tie is the only key and it reads wrong at 1x.
- **A GAP TIP WENT TO THE NEARER HEAD, NOT ONE HEAD LEFT (032 g14, Dewey ->
  Huey).** The tip was 30px past the blue-capped boy and 10px short of the
  red-capped one; the review gave it to the nearer boy. The one-head-left rule
  came from Vols. 10 and 14 -- on this title it lost. (056 g3 also went one head
  left and came back **Donald**, not the other boy.)
- **TWO NAMES ON BOYS UNDER THE MOSS SLIDE WENT TO DONALD (049 g2 Huey -> Donald,
  056 g3 Huey -> Donald)**, one with the tip inside a clean red cap's span. Look
  for Donald cut off at the panel edge before naming the boy under the tip.
- **THE ONE OVER-NAMING IS A GULP (033 g16, Dewey -> nephews).** Tip inside a
  clean blue cap's span; the review made the shared `GULP!` a collective.
- **THE `unknown`s WERE RESOLVED**: 050 g8 to `nephews`, 050 g9 to Donald, and
  052 g17's tail-less `LOOKOUT ABOVE!` from Scrooge to Donald.
- **`other:` renamed once**: 051 g13 `a bellhop` -> `a waiter`.
- **MISSED TEXT: 052 p3 `S GROC` went to `missed-text-ignore.txt`** -- a torn
  fragment of the store name on the peeled paint strip, not worth a group.

### Findings to paste into the next run (2026-09-15, fifty-sixth batch, TWO OF THREE REVIEWED -- *Trapped Lightning*)

**51 groups, 11 speaker corrections (21.6%), every one the same relabel**; all
calls were high. No type, text or missed-text work; no group added. The review
also moved two paddleocr text boxes (130, 132). Mirrored clean.

- **NAME A RECURRING SUPPORTING CHARACTER, NOT A ROLE.** The two mouse children
  were written `other:a kid` on all 11 of their groups; the review made every one
  `other:Morty and Ferdie` (typed lowercase in the editor and capitalised after
  the mirror, 2026-09-15). They are Mickey's nephews, drawn in overalls with
  their names never spoken in this story -- a known pair is still named, even
  when the dialogue does not say it. On a Gyro or Grandma Duck filler, check the
  supporting cast against the house characters before reaching for a role.
- **A PAIR THAT SPEAKS TOGETHER IS ONE `other:` VALUE**, even where a single tail
  picks out one of the two: the review did not split the names by tail.

### Findings to paste into the next run (2026-09-15, fifty-sixth batch, THREE OF THREE -- *Camping Confusion*, batch closed)

**133 groups passed plus 1 added, 3 speaker corrections (2.3%), 2 of the 46 in
the nephew domain (4.3%)**; by the confidence the pass wrote, **high 3/121,
medium 0/12** -- every medium held, including the flagged 173 g1 conflict (Huey
stood). All 4 type proposals held; no text corrections. The missed `ZZZZ` on 169
p1 was added as g2, `dialogue`, Donald, which renumbers the page: the
`review_findings` row `169 g2: unknown -> Donald` is that add, not a correction.
**Batch: 38 speaker corrections over 607 groups (6.3%)** -- 24, 11 and 3 by title.

- **THE H159 TEAL WAS DEWEY'S BLUE, AGAIN (173 g0, nephews -> Dewey).** The pass
  declined `#0ba570` H159.4 between the title's green (H147) and blue (H184),
  citing Gopher Goof-Ups' H162.5 Dewey -- and then did not use it. **But the
  band is not one-way on Vol. 17**: Olympic Hopeful printed Louie's green at
  `#079464` H159.6 and `#1c8d70` H164.6. What separates them is the title's own
  clean inks: here the clean green is H147 and the blue drifts teal (H172-184),
  so H159 sits on the blue's side. **Rank a teal against the title's clean green
  and name it at medium, rather than declining** -- the decline is the one call
  guaranteed to be corrected.
- **A LIGHT-BLUE CAP READ AS SKY (173 g5, nephews -> Dewey).** The small boy
  peering from the bushes probed only `#b4d9df` (H188, S0.19), which the pass
  wrote off as the sky behind him and so called the cap "plain black". Zoomed in,
  the cap is light blue: Dewey. The foreground boy is Louie in clean green, which
  was the other half of the answer. **A pale cyan crown probe is not the sky until
  a crop shows sky there** -- on a title whose sky is that same pale blue, crop the
  crown at 3x before declining.
- **ONE BEAR, NOT A CUB (176 g6, `other:a bear cub` -> `other:a bear`).** The `?`
  over the cub wearing a cap went to the plain `other:a bear` the other three bear
  groups carry; the review keeps one value for the family.
- **THE CAMPING CONFUSION PALETTE HELD WHERE IT WAS DIALOGUE-ANCHORED**: every
  name on 172-178 resting on `RODMAN LOUIE` / `CHARTMAN HUEY`, the green
  `#019d47`, and the ranked teals on 178 stood.

### Findings to paste into the next run (2026-09-15, fifty-seventh batch, PASS ONLY -- not yet reviewed)

*The Master* (Vol. 18, 018-027), *A Whale of a Story* (Vol. 18, 028-037) and
*Smoke Writer in the Sky* (Vol. 18, 038-047), all 1955, and *Inventor of Anything*
(Vol. 20, 133-136). The name-grep's non-dictionary list carried no nephew name,
but *Whale* 035 names all three in dialogue (`HUEY AND DEWEY, GO OUT ON THE
ROCKS`, `LOUIE, STAY HERE`) -- dictionary words, the grep's known blind spot.

| title | groups | medium | nephew domain (named / collective) | type | text | missed text | images |
|---|---|---|---|---|---|---|---|
| *The Master* | 131 | 4 | 36 (17 / 19) | 4 | 0 | 1 | 19 / 10 = 1.90 |
| *A Whale of a Story* | 140 | 16 (+1 low) | 59 (31 / 28) | 3 | 0 | 0 | 16 / 10 = 1.60 |
| *Smoke Writer in the Sky* | 139 | 12 | 39 (29 / 10) | 9 | 0 | 0 | 15 / 10 = 1.50 |
| *Inventor of Anything* | 60 | 1 (+1 low) | 0 | 5 | 0 | 1 | 4 / 4 = 1.00 |

**Batch: 470 groups, 54 images over 34 pages = 1.59 per page.** Missed text:
*The Master* 019 p5 `MAN OH MAN` (the cover of Donald's book) and *Inventor of
Anything* 136 p2 `313` (the hot rod's licence plate), both parked in the titles'
`queue-missed.txt`.

- **THE VOL. 18 CAP GREEN IS A PER-TITLE FACT.** *The Master* prints it `#009d46`
  H147 in the `green` band (021 p8); *Whale* and *Smoke Writer* print `#4fa43e`
  H110 in `leafgrn` (028 p1, 038 p1). Red and blue are the same in all three.
  Read the reference panel for each title rather than carrying the volume's.
- **A DIALOGUE-VS-CAP CONFLICT IS FLAGGED TWICE (*Whale* 035 g12, 036 g9).**
  Donald sends `HUEY AND DEWEY` fishing and keeps Louie, whose cap is leafgrn.
  One fisher prints red; the other prints green `#529f65` H134.8 (035 p7) and a
  weak `#7bab63` (036 p7), never blue. Both named Dewey at medium by the order,
  with the printed colour recorded. The review settles whether order or ink wins.
- **TEAL SLIVERS WERE RANKED, NOT DECLINED.** `#19a896` H172 (*Whale* 028 g11)
  went to Dewey; `#009f70` H162, `#24877f` H175, `#346e5e` H163 and `#249071` H163
  (*The Master* 020 g4, 022 g4, 023 g3, 026 g7) went to Louie on G above B, at
  medium where the rim is thin. *Smoke Writer* 044 g11's `#35a567` H147 went to
  Louie at medium although the story's foliage prints that hue.
- **ELIMINATION NAMED A THIRD BOY WITH NO INK, AT MEDIUM** (*Whale* 037 g10;
  *Smoke Writer* 038 g6, 042 g14, 047 g10).
- **GAP TIPS WENT TO THE SIDE THE TAIL LEANS, AT MEDIUM** (*Whale* 029 g4, 030
  g12; *Smoke Writer* 040 g6, where the other head was a silhouette, and 046 g2).
- **A RADIO VOICE WAS NAMED FOR THE BOY HOLDING THE WALKIE-TALKIE** (*Smoke
  Writer* 040 g11, 041 g5, Huey, medium). Zigzags from off the panel edge are
  `nephews`.
- **THREE PAIRS OF EYES IN THE SMOG (*Smoke Writer* 047 g5-g7)** were called
  `nephews` at medium because the boys walk out of it on the next panel; they
  could as well be townspeople.
- **LOW, FOR REVIEW**: *Whale* 032 g1 (`YO, HO!` from a speck of a boat, Donald)
  and *Inventor of Anything* 135 g10 (an off-panel `OW` in a fight, `unknown`).
- **TYPE: 21 proposals.** Bubble trails on groups stored as dialogue, to thought:
  *The Master* 019 g17, 020 g16 (a `?`), 026 g5; *Whale* 030 g13; *Smoke Writer*
  041 g1, 041 g3, 046 g11; *Inventor* 133 g3, 133 g12. A pointed tail stored as
  thought, to dialogue: *The Master* 025 g5. A tailed balloon stored as narration,
  to dialogue: *Whale* 034 g11. Story logos stored as background, to title: *Whale*
  028 g0, *Smoke Writer* 038 g0, and the `INVENTOR OF ANYTHING` sign (133 g7).
  Voices stored as sound_effect, to dialogue: `BOO! BOO!` (042 g12), the geese's
  `HONK!` (043 g13-g15), the crowd's laughter (044 g8), `OW!` and the goat's `BAA!`
  (133 g4, g16).
- **TEXT: none.**
- **`other:` values**: *The Master* `the boss`, `the kingfisher`; *Whale* `the
  Humane Society man`, `the sheriff`; *Smoke Writer* `a voter`, `the crowd`, `the
  geese`, `the mailman`; *Inventor of Anything* `Speedy` (named in the dialogue),
  `the neighbour`, `the goat`, `the boys next door`.

### Findings to paste into the next run (2026-09-15, fifty-seventh batch, ONE OF FOUR REVIEWED -- *The Master*)

**131 groups passed plus 2 added, 0 speaker corrections**; by the confidence the
pass wrote, **high 0/127, medium 0/4**. `review_findings` prints two rows, `019
g13: unknown -> none` and `023 g11: unknown -> Donald`, but both are the groups the
review added, not overrules. All 4 type proposals held; no text corrections.
Mirrored clean onto paddleocr: 133/133 reviewed on both engines, distributions
identical.

- **MISSED TEXT ADDED: 019 p5 `MAN OH MAN`** (the cover of Donald's book) as g13,
  `background`, `none`. It renumbers 019 from g13 on, so the pass's g17 thought
  now reads as g18 in `review_findings`.
- **A DRAWN `?` THE AUDIT DID NOT LIST WAS ADDED TOO (023 g11, `thought`,
  Donald).** The `?` in its own cloud over Donald on 023 p2 was in the page's
  `visible_text`, yet `audit_missed_text` reported only `MAN OH MAN` for the
  title. A lone `?` in `visible_text` is not a guarantee it reaches the queue:
  park an ungrouped drawn device in `queue-missed.txt` by hand.
- **THE MASTER'S PALETTE AND ITS THIN RIMS HELD.** Every name resting on the H147
  `#009d46` green and on the teal rims ranked to Louie on G above B (020 g4 H162,
  022 g4 H175, 023 g3 H163, 026 g7 H163) stood, as did the dimmed reds named Huey
  (020 g6 `#893b25`, 022 g1 `#762c18`) and the medium gap tip on 020 g4.
- **THE COLLECTIVES HELD**: all 19, indoors on 018-019 and on the silhouettes
  (018 p3, 020 p4, 024 p4), were left as `nephews`.

### Findings to paste into the next run (2026-09-15, fifty-seventh batch, TWO OF FOUR REVIEWED -- *A Whale of a Story*)

**140 groups passed plus 1 added, 10 speaker corrections (7.1%), every one in the
nephew domain**; by the confidence the pass wrote, **high 9/123 (7.3%), medium
1/16 (6.2%), low 0/1**. `review_findings` prints 11 -- the eleventh, `034 g15:
unknown -> Donald`, is the group the review added. All 3 type proposals held; no
text corrections. Mirrored clean onto paddleocr: 141/141 reviewed on both engines,
distributions identical.

- **TWO BOYS WERE READ AS DONALD (031 g4, 034 g11 -> Dewey).** 031 g4's "Donald at
  right, sailor cap `#00a5d5` 1647px" was Dewey: on this title Donald's cap and
  Dewey's patch are the same blue, so a large blue cap is not Donald's until the
  crown shape and the beak say so. 034 g11, the figure knocked flat under THOONK
  with its cap flying, was the boy thrown off the spout on 034 p6, not Donald --
  follow who was just in the air before naming who lands.
- **OFF-PANEL AND LONG-SHOT LINES WENT TO THE BOYS (030 g0, g1; 031 g1 -> `nephews`).**
  Two tails curling off the edge of a scenery panel and a second tail into a boat
  of specks were given to Donald because the line sounded like his plan or his
  rallying cry. Register is not evidence; the Donald default is for a lone figure.
- **FIVE COLLECTIVES NAMED (029 g6, 031 g3, 033 g2 -> Louie; 033 g3, 036 g6 -> Huey).**
  Three boys whose caps showed no ink came back Louie: this title's cap green is
  the leafgrn `#4fa43e`, and it is the ink the scans lose on small or shaded caps.
  031 g3 also fell out of the 031 g4 error -- with the right-hand figure Dewey
  rather than Donald, the middle boy was the third by elimination. 033 g3 carries
  the review note "Not Dewey or Louie".
- **THE DIALOGUE ORDER BEAT THE INK (035 g12, 036 g9 held as Dewey).** The fisher
  Donald had sent out as one of HUEY AND DEWEY stayed Dewey although he printed a
  green `#529f65`. When a line assigns the pair, name from the order and record the
  printed colour.
- **A SECOND DRAWN `?` THE AUDIT DID NOT LIST (034 g15, `thought`, Donald).** The
  `?` over Donald on 034 p5 was in the page's `visible_text`, and the audit reported
  nothing for the title -- the same miss as *The Master* 023 g11. Park an ungrouped
  drawn device in `queue-missed.txt` by hand.
- **MEDIUMS HELD 15/16**, including the elimination on 037 g10, the gap tips on 029
  g4 and 030 g12, and the teal `#19a896` ranked to Dewey on 028 g11. The one medium
  corrected was 031 g1.

### Findings to paste into the next run (2026-09-15, fifty-seventh batch, THREE OF FOUR REVIEWED -- *Smoke Writer in the Sky*)

**139 groups, 5 speaker corrections (3.6%), every one in the nephew domain (5 of
39, 12.8%)**; by the confidence the pass wrote, **high 5/127 (3.9%), medium 0/12**.
No group was added. All 9 type proposals held -- the crowd's `BOO!` and laughter
and the geese's `HONK!` as dialogue, the bubble trails as thought, the logo as
title. No text corrections. Mirrored clean onto paddleocr: 139/139 reviewed on both
engines, distributions identical.

- **A RADIO VOICE BELONGS TO WHOEVER LAST HELD THE SET (040 g12, g14; 041 g0, g6,
  `nephews` -> Huey).** Four zigzag tails from specks on the ground or from below the
  panel edge were left collective; the review named all four Huey, noting "Huey was
  last holding the walkie talkie". The pass had already named Huey on the two panels
  where he is drawn holding it (040 g11, 041 g5) and then declined the same voice when
  the boys shrank to specks. Carry the holder forward until another boy is shown with
  the set.
- **ONE OVER-NAMING: 042 g16, Louie -> `nephews`.** The tail tip sat over the left boy
  (leafgrn cap, 860+817+622px) with a blue-capped boy beside him, but the line -- `THEN
  BRACE YOURSELF FOR BAD NEWS! YOU'RE IN TROUBLE!` -- went to the pair. A tip over one
  of two boys crowded together is not always a single speaker.
- **EVERY MEDIUM HELD, 12/12**: the eliminations (038 g6, 042 g14, 047 g10), the gap
  tip on 040 g6 against a silhouette, the walkie-talkie holders, the three pairs of
  eyes in the smog as `nephews` (047 g5-g7), and 044 g11's foliage-hued `#35a567` cap
  named Louie.

### Findings to paste into the next run (2026-09-15, fifty-seventh batch, FOUR OF FOUR -- *Inventor of Anything*, batch closed)

**60 groups passed plus 2 added, 0 speaker corrections**; by the confidence the
pass wrote, **high 0/58, medium 0/1, low 0/1** -- the `unknown` on the off-panel
`OW` (135 g10) stood. `review_findings` prints two speaker rows, `134 g14: unknown
-> other:the neighbour` and `136 g2: unknown -> none`, but both are the groups the
review added. All 5 type proposals held; no text corrections. It also lists `136
g4` and `136 g10` as dialogue -> thought: those are the pass's g3 and g9 (Speedy's
`SPICE` thought and Gyro's hammock thought), renumbered by the add, which the pass
saw stored as thought and did not propose. Mirrored clean onto paddleocr.
**Batch: 15 speaker corrections over 470 passed groups (3.2%)** -- 0, 10, 5 and 0
by title; 5 groups added -- the two audit findings (`MAN OH MAN`, `313`) and three
drawn `?` marks the audit did not list.

- **MISSED TEXT ADDED: 136 p2 `313`**, the hot rod's licence plate, as g2,
  `background`, `none`.
- **A THIRD DRAWN `?` THE AUDIT DID NOT LIST (134 g14, `thought`,
  `other:the neighbour`).** The `?` over the neighbour on 134 p4 was in the page's
  `visible_text`; the audit reported only `313`. Three titles of four this batch
  had the same miss (*The Master* 023 g11, *Whale* 034 g15). Until the audit reports
  them, every drawn `?` or device recorded in `visible_text` goes into
  `queue-missed.txt` by hand.
- **THE GYRO FILLER'S CAST HELD AS WRITTEN**: `other:Speedy`, named from the
  dialogue, and the unnamed `other:the neighbour`, `other:the goat` and
  `other:the boys next door` all stood.

### Findings to paste into the next run (2026-09-15, fifty-eighth batch, PASS ONLY -- not yet reviewed)

*The Lost Crown of Genghis Khan!* (Vol. 16, 008-026 plus the one-page gag 235) and
*Faulty Fortune* (Vol. 16, 060-067), *The Runaway Train* (Vol. 18, 048-057) and
*Statues of Limitations* (Vol. 18, 058-067), all 1955. The name-grep's
non-dictionary list carried no nephew name for *Genghis*, but 017 g12 addresses
`HUEY` -- the dictionary-word blind spot again; a grep of `ai_text` found it.

| title | groups | medium | nephew domain (named / collective) | type | text | missed text | images |
|---|---|---|---|---|---|---|---|
| *The Lost Crown of Genghis Khan!* | 269 | 26 (+4 low) | 49 (28 / 21) | 5 | 0 | 0 | 34 / 20 = 1.70 |
| *Faulty Fortune* | 120 | 7 (+2 low) | 23 (12 / 11) | 4 | 1 | 2 | 17 / 8 = 2.13 |
| *The Runaway Train* | 136 + 1 added | 4 | 50 (0 / 50) | 2 | 0 | 2 | 11 / 10 = 1.10 |
| *Statues of Limitations* | 128 | 22 | 60 (41 / 19) | 4 | 0 | 0 | 19 / 10 = 1.90 |

**Batch: 653 groups plus 1 added, 81 images over 48 pages = 1.69 per page.**
Missed text, parked in the titles' `queue-missed.txt`: *Faulty Fortune* 061 p4
`3 13` (the car's licence plate) and 066 p1 `CANNY BRANNIES` (the cereal-box
labels); *The Runaway Train* 053 p7 `171721` (the locomotive's number plate) and
055 p6 `AIR FREIGHT` (the crate). The pass itself added *Runaway Train* 048 p5
`CRASH`, which neither engine had grouped.

- **GENGHIS 017 p7 ADDRESSES A GREEN-CAPPED BOY AS HUEY.** `SUCH SHIVERING, HUEY!`
  goes to the only boy in view, leafgrn `#4ca23e` 2,088px, and his close-up answer
  on p8 prints `#4da33d` 9,122px. 017 g13 is named Huey from the address at medium
  with the green recorded; everywhere else the convention stood (red Huey, green
  Louie), and every red- or green-named group on 015-024 carries a note pointing
  at 017. It is the only nephew name in the title's dialogue. The review decides
  whether the story permutes red and green or the line is a slip; if permuted,
  those names swap as a set.
- **THE RUNAWAY TRAIN HAS NO CAP KEY: 50 COLLECTIVES, 0 NAMED.** The boys are
  bare-headed indoors on every page, and the only naming lines list all three
  (054 g9, 057 g7).
- **GAP TIPS WENT ONE HEAD LEFT, AT MEDIUM** (*Genghis* 013 g6, 015 g14, 024 g4,
  g5; *Faulty Fortune* 066 g8, g13; *Statues* 058 g9, 062 g4, 064 g8; 059 g11 at
  high, the boy gesturing with sound lines).
- **ELIMINATION NAMED AN UNMARKED THIRD BOY, AT MEDIUM** (*Statues* 058 g9, 066
  g5, `cap_colour` null).
- **A TAIL HIDDEN BEHIND ANOTHER BALLOON WAS NAMED ON ONE TAIL PER BOY, AT MEDIUM**
  (*Statues* 058 g1, 058 g10, 065 g2).
- **TWO TAILS ONTO ONE BOY WERE LEFT COLLECTIVE** (*Statues* 061 g0, g1, both on
  the red-capped boy); the review may name him Huey.
- **OFF-PALETTE GREENS WERE NAMED LOUIE**: *Statues* 058 g11 `#71a83a` H90, 059 g9
  `#6ca73a` H92.5, 065 g4 `#43ae47` H122, 062 g7 `#44a055` H131 (medium); *Faulty
  Fortune* 062 g7 on a rim plain in the crop but under the 0.40 saturation floor,
  unmeasured (medium). A teal rim was ranked to Dewey: *Statues* 060 g3 `#279299`
  H183.7 (medium).
- **SCROOGE BY THE TAIL WHERE THE LINE READS AS A JAB AT HIM** (*Faulty Fortune*
  061 g3 `ONE EACH YEAR!`, 061 g9 `YOU DON'T EXPECT ... FORT WORTH`), both medium:
  the art and the register disagree.
- **LOW, FOR REVIEW**: the long-shot Donald default on *Genghis* 011 g7 and 026
  g5; `unknown` on *Genghis* 020 g2 (a scenery panel) and 023 g14 (a silhouette
  behind bars), and *Faulty Fortune* 064 g7, g8 (the car in silhouette).
- **TYPE: 15 proposals.** Speech balloons stored as captions, to dialogue:
  *Genghis* 019 g0, 023 g9; *Runaway Train* 057 g6, g7. Bubble trails on groups
  stored as dialogue, to thought: *Genghis* 008 g1; *Faulty Fortune* 065 g1;
  *Statues* 060 g7, 060 g11, 062 g13. A pointed tail stored as thought, to
  dialogue: *Faulty Fortune* 067 g7. Voices stored as sound_effect, to dialogue:
  *Genghis* 019 g9 `EE-YEEK`; *Faulty Fortune* 063 g7 (the prairie dog's laugh),
  065 g7 `GROAN!`. Lettering on the plane stored as dialogue, to background:
  *Genghis* 010 g4 `ASIA`. The logo stored as background, to title: *Statues* 058 g0.
- **TEXT: one.** *Faulty Fortune* 060 g9 `CANNIE` -> `CANNY BRANNIES`, the cereal
  box label read at 4x on two panels.
- *Genghis* 235 is a one-page *Uncle Scrooge* gag (Grandma Duck at the Ritzmore
  Cafe) prepared under this title; it was read and applied with it.
- Single characters in `visible_text` the audit does not report: *Genghis* 009 `$`,
  010 `A`, 026 `A`. Not parked; the reviewer's call.
- **`other:` values**: *Genghis* `the messenger`, `the red-coated runner`, `the
  runner on the bridge`, `the guard`, `the newscaster`, `the snowman`, `the
  crowd`, `a reporter`, `Grandma Duck`; *Faulty Fortune* `the land office clerk`,
  `the prairie dog`, `the Cotton Sock grocer`, `the Florida grocer`, `the Alabama
  storekeeper`, `the stewardess`, `the drilling foreman`; *Runaway Train* `the TV
  announcer`, `Prof. Brainwhiz`, `the technician`, `the Limited's crew`, `the
  railroad official` (two officials share it), `the airport guard`; *Statues* `the
  mayor`, `the mayor's aide`, `the Umble boy`, `the Umble girl`, `Donald and the
  nephews`. Across titles, *Genghis*'s `the newscaster` and *Runaway Train*'s `the
  TV announcer` are the same role.

### Findings to paste into the next run (2026-09-15, fifty-eighth batch, ONE OF FOUR REVIEWED -- *The Lost Crown of Genghis Khan!*)

**269 groups, 9 speaker corrections (3.3%), 8 in the nephew domain (8 of 47,
17.0%)**; by the confidence the pass wrote, **high 4/239 (1.7%), medium 3/26
(11.5%), low 2/4**. No group was added. All 5 type proposals held; no text
corrections. Mirrored clean onto paddleocr: 269/269 reviewed on both engines,
distributions identical. `review_findings` counts 287 groups because it also reads
page 059, which is not this title's and was reviewed on 2026-08-16.

- **THE 017 HUEY ADDRESS STOOD, AND SO DID THE CONVENTION.** 017 g13 stayed Huey on
  a leafgrn cap, and every red Huey and green Louie on 015-024 stood. When a naming
  line lands on the "wrong" cap, name that panel from the line and keep the
  convention everywhere else.
- **A CASCADE WHOSE TAILS REACH CAPPED BOYS STILL NAMES THEM (010 g3 -> Louie, g5 ->
  Huey).** The pass left the boarding-stairs cascade collective: g3 fed into g5,
  g5 carried two tails, and the higher boy's cap was written off as "no chromatic
  ink". The review named the green boy and the red boy. A capscan zero on a small
  crown is not a bare head.
- **016 g12, a gap tip between two sleeping boys, went to Louie** -- the boy in the
  green sleeping bag. The review's reason: his is the only bag still open, so he is
  the one awake to speak, and the tail points at him approximately. The pass had
  refused the bags as a colour key (Scrooge sleeps in a green one on 017 p2) and
  that stands; what named him was the drawing -- who is awake -- plus the lean of
  the tail. On a gap tip, ask which figure the art shows able to speak.
- **THE LEAN BEAT THE TIP ON DONALD (013 g9 Louie -> Donald; 012 g9 nephews ->
  Donald).** On 013 g9 the tail leaned toward Donald while its tip touched the
  boy's beak; on 012 g9 a tip over the running silhouettes was Donald's.
- **DONALD WAS SCROOGE TWICE (024 g3, 026 g5).** 024 g3's tip, 31px above Donald's
  sailor cap and 57px from Scrooge's top hat, was Scrooge's. 026 g5, the low
  long-shot default, was the watch owner's line -- `LET'S TRY TO BE FAR AWAY WHEN
  THAT WATCH RUNS DOWN AGAIN!`.
- **A SILHOUETTE `THAT'S A DEAL!` WAS THE CHORUS (012 g12 -> `other:Donald and the
  nephews`)**, and 023 g14's silhouette behind the bars was a boy (`unknown` ->
  `nephews`). 020 g2 stayed `unknown`.
- **TWO STRAGGLERS**: 016 g1 `TICK TICK` and 023 g13 `CRACK!` were left without
  `speaker_reviewed` at first; both were signed off before the mirror.

### Findings to paste into the next run (2026-09-15, fifty-eighth batch, TWO OF FOUR REVIEWED -- *Faulty Fortune*)

**120 groups passed plus 1 added, 11 speaker corrections (9.2%), 10 in the nephew
domain (10 of 25, 40.0%)**; by the confidence the pass wrote, **high 8/111 (7.2%),
medium 1/7, low 2/2**. `review_findings` prints 12 rows and medium 2/7: the
twelfth, `061 g9: unknown -> none`, is the group the review added, which sits on
the pass's g9 id. The `CANNIE` -> `CANNY` text correction and all 4 type proposals
held. Mirrored clean onto paddleocr: 121/121 reviewed on both engines,
distributions identical.

- **AN UNMARKED BLACK CAP ON THIS TITLE WAS NOT BARE (063 g1, g2, g6, g10, 064 g1,
  067 g5 -> Louie; 067 g6 -> Dewey; 066 g17 -> Huey).** Eight collectives were
  written off a capwide zero at the S>=0.3 floor. The rims here are thin and dark,
  and the green in particular sits under the saturation floor -- the same rim was
  plain in the 062 g7 crop, which held. Where the scan finds nothing on a black
  cap, crop the rim at 3x before calling it unmarked.
- **THE REGISTER BEAT THE TIP (061 g3 Scrooge -> Louie).** `YES! YOU COULD RAISE
  CARROTS! ONE EACH YEAR!` is a jab at Scrooge, and a tip 16px from his top hat
  belonged to the green-capped boy beside it. The pass flagged the conflict at
  medium; the review took the line. 061 g10 (the pass's g9), `YOU DON'T EXPECT ...
  FORT WORTH`, stayed Scrooge.
- **THE SILHOUETTED CAR WAS SETTLED FROM THE LINES (064 g7 `unknown` -> `nephews`,
  064 g8 `unknown` -> Donald).**
- **MISSED TEXT ADDED: 061 p4 licence plate as g9 `313`**, `background`, `none`,
  renumbering 061 from g9. **066 p1 `CANNY BRANNIES`** (the cereal-box labels) was
  not added and is still reported by the audit.

### Findings to paste into the next run (2026-09-15, fifty-eighth batch, THREE OF FOUR REVIEWED -- *The Runaway Train*)

**136 groups passed plus 2 added, 0 speaker corrections**; by the confidence the
pass wrote, **high 0/133, medium 0/4**. The groups added are the pass's own 048 p5
`CRASH` and the review's 055 p6 `AIR FREIGHT`. `review_findings` prints one row,
`055 g13: unknown -> none`, and high 1/133, but that is the review's add sitting on
the pass's g13 id. Both type proposals held (057 g6, g7, the broadcast balloons
stored as captions). Mirrored clean onto paddleocr: 138/138 reviewed on both
engines, distributions identical.

- **A TITLE WITH NO CAP KEY HELD WHOLE.** All 50 collectives stood: the boys are
  bare-headed indoors on every page, and a line that names all three (054 g9,
  057 g7) names none of them.
- **EVERY MEDIUM HELD, 4/4**: 048 g8 between the boys and Donald, 053 g10 the
  technician drawn only as legs, and 054 g1, g2 from the silhouetted control tower.
- **THE PASS'S ADDED `CRASH` STOOD** as a sound effect with no speaker.
- **MISSED TEXT ADDED: 055 p6 `AIR FREIGHT`** as g13, `background`, `none`.
  **053 p7**, the locomotive's number plate, was added afterwards as g15 `171761`.
  The pass had transcribed it `171721` into `visible_text`; at 10x the fifth
  glyph is a 6, so the capture was corrected rather than the finding ignored. A
  number read off a plate at 4x is not settled -- crop it at 10x before writing it.

### Findings to paste into the next run (2026-09-15, fifty-eighth batch, FOUR OF FOUR -- *Statues of Limitations*, batch closed)

**128 groups, 10 speaker corrections (7.8%), every one in the nephew domain (10 of
60, 16.7%)**; by the confidence the pass wrote, **high 8/106 (7.5%), medium 2/22
(9.1%)**. No group was added. All 4 type proposals held; no text corrections.
Mirrored clean onto paddleocr: 128/128 reviewed on both engines, distributions
identical. **Batch: 30 speaker corrections over 653 passed groups (4.6%)** -- 9, 11,
0 and 10 by title; 4 groups added (the pass's `CRASH`, and the review's `313`,
`AIR FREIGHT` and `171761`). *Faulty Fortune* 066 `CANNY BRANNIES` went to the
ignore list on the reviewer's word.

- **A SCAN ZERO ON A THIN RIM WAS A NAME, AGAIN (059 g2 -> Dewey, 065 g1 -> Huey,
  067 g5 -> Dewey, 067 g6 -> Louie, 067 g7 -> Huey).** The same failure as *Faulty
  Fortune*'s eight, in the other volume: across the batch 13 collectives written
  off a capwide zero at S>=0.3, or off a sliver judged off-roster (065 g1's maroon
  `#a24351` was the red), were named by the review. On these 1955 caps with thin
  rims, **crop every speaking boy's rim at 3x before writing `nephews`**; the scan
  does not see them.
- **TAILS CROSSED: TRACE FROM THE ROOT, NOT THE TIP (058 g2 Huey -> Louie, 058 g3
  Louie -> Huey).** The long thin tail running down the right side of the g3
  balloon was g3's own and reached the red cap; g2's reached the green. The pass
  gave the long spike to g2 because it appeared to start above g3, and swapped
  the pair.
- **A TIP LEVEL WITH ONE HEAD BELONGS TO THAT HEAD (062 g4 Dewey -> Huey).** The tip
  sat inside the front boy's horizontal span but 31px above his cap, and level
  with the back boy's head 18px to the right; it was the back boy's. Measure the
  tip in y as well as x before calling it one boy's.
- **TWO TAILS ON ONE BALLOON WERE TWO BOYS (061 g0 -> Huey, 061 g1 -> Louie).** The
  pass read both tips as landing on the red-capped boy and left both collective;
  the review gave one to him and the other to the boy beside him ("Not Huey or
  Dewey", `cap_colour` null). Two tails on a balloon are two speakers until a crop
  proves they converge.
- **MEDIUMS HELD 20/22**, including the eliminations 058 g9 and 066 g5, the hidden
  tails 058 g1, 058 g10 and 065 g2, and the off-palette greens 058 g11 (H90), 059 g9,
  062 g7 (H131) and 065 g4. The two mediums corrected were 058 g2 and 062 g4.
- **THE ADULT CAST HELD AS WRITTEN**: `other:the mayor`, `other:the mayor's aide`,
  `other:the Umble boy`, `other:the Umble girl`, and the closing chorus as
  `other:Donald and the nephews`.

### Findings to paste into the next run (2026-09-16, fifty-ninth batch, ONE OF TWO REVIEWED -- *Borderline Hero*)

**137 groups, 2 speaker corrections (1.5%), both in the nephew domain (2 of 48,
4.2%)**; by the confidence the pass wrote, **high 2/125 (1.6%), medium 0/12**. No
group was added, no text correction was proposed, and all 5 type proposals held
(068 g0 the splash logo to `title`; 070 g14, g15, 073 g5, 074 g6 the bubble
trails to `thought`). `review_findings` also lists 4 `type_was` rows reviewed
2026-08-16, predating this pass and not counted. Mirrored clean onto paddleocr:
137/137 reviewed on both engines, `identified_by` 134, and the speaker,
`cap_colour` and confidence distributions identical.

- **BOTH CORRECTIONS WERE A CAP I HAD ALREADY READ AND DECLINED TO USE (072 g8 ->
  Huey `red`, 072 g12 -> Dewey `blue`).** Neither was a tail error: the tails were
  right and the names were left off.
- **A PROBE ZERO ON A SMALL LONE BOY IS NOT A BARE HEAD (072 g8).** The `TAXI!`
  boy: `capwide` returned red 0 / green 0 / blue 0 and a probe of his head
  (x540-620 y390-470) found no chromatic band at all, so the pass wrote
  `nephews` and quoted both. The review read a red cap. At that size the rim is a
  few dozen pixels against a night-blue field; **crop the cap at 4-6x before
  writing the collective**, exactly as the fifty-eighth batch said for thin rims,
  and do not treat a probe zero as the end of it.
- **BACK-PROPAGATE A NAME ONTO THE SAME BOY IN THE NEIGHBOURING PANEL (072 g12).**
  On 072 p8 the pass named the boy holding the binoculars Dewey, ranking his
  `#02956c` H163 cap as blue against the H131 green beside it. One panel earlier,
  on p7, the *same* boy with the *same* binoculars got `nephews`, because his cap
  there probes as a shaded green speck (H146, S0.12) matching the boy beside him.
  The review named him Dewey on p7 too. When a boy carries a prop across
  consecutive panels and one panel names him, carry the name back.
- **EVERY MEDIUM HELD, 12/12**: the gap tips (070 g7, 075 g2, 075 g8, 077 g14,
  077 g17), the eliminations where the boy's own cap printed nothing (072 g2,
  072 g6, 075 g1), the shaded-teal blues read by ranking (074 g1, 077 g17), the
  long-shot `GOLLY!` (069 g12) and the silhouette call.
- **THE ADULT CAST HELD AS WRITTEN**: `other:the border patrol chief`,
  `other:the photographer`, `other:the pickup man`, `other:the parakeet man`,
  `other:a smuggler`.

### Findings to paste into the next run (2026-09-16, fifty-ninth batch, TWO OF TWO -- *The Second-Richest Duck*, batch closed)

**274 groups passed plus 2 added, 17 speaker corrections (6.2% of the 274)**; by
the confidence the pass wrote, **high 12/258 (4.7%), medium 3/15 (20.0%), low
0/1**. `review_findings` prints 5.5% and a nephew domain of 14 of 45 because its
denominator is the whole 22-page title (308 groups): pages 090 and 091 carry 32
groups that prep skipped and this pass never read. All 8 type proposals held and
no text correction was proposed. Mirrored clean onto paddleocr: 276/276 reviewed
on both engines, `identified_by` 262, distributions identical. **Batch: 19
speaker corrections over 411 passed groups (4.6%)** -- 2 and 17 by title.

- **NINE UNDER-NAMINGS, AND FIVE WERE A `capwide` ZERO WRITTEN UP AS BARE-HEADED
  (074 g3, 074 g6, 080 g6, 083 g9, 083 g12 -> Louie).** The note in each says
  `bare-headed` or `shows no ink` and quotes the band totals; the review found a
  green cap every time. With *Borderline Hero*'s 072 g8 that is **six in one
  batch, the same failure as the fifty-eighth batch's thirteen**. The scan cannot
  see these rims: on a title whose caps are a coloured rim on black, **crop every
  speaking boy's head at 3-6x before writing `nephews`** -- a zero from `capwide`,
  `title_bands` *or* `probe` is not evidence of a bare head.
- **A FLAT BLACK SILHOUETTE WAS STILL NAMED (083 g10 -> Dewey).** The pass wrote
  `no cap colour can print on a silhouette`, which is true and still not a reason
  to decline: the other two boys in the panel were named, so the third was the
  remainder. Eliminate before falling back to the collective.
- **THE SILHOUETTE BRAWL PAIR WAS SWAPPED (077 g9 Scrooge -> Glomgold, 077 g10
  Glomgold -> Scrooge).** The pass split two identical silhouettes on the
  dialogue: `SHORTIE` is Glomgold's word for Scrooge (076 g12), so the speaker of
  `LONG TONS, SHORTIE!` was read as Glomgold. The review inverted both. **An
  insult does not name its speaker**; on identical silhouettes trace the tail
  roots or say so and leave the pair at medium.
- **SCROOGE TOOK THREE LINES THE PASS GAVE TO SOMEONE ELSE (075 g4, 076 g5 ->
  Scrooge from Donald; 077 g14 -> Scrooge from `nephews`).** 076 g5, `THE TIGHTWAD
  DOESN'T EVEN BUY NEWSPAPERS!`, is the trap: it reads as Donald's line about
  Scrooge, and it is Scrooge's about Glomgold. In a two-tycoon story the
  miser-baiting register belongs to both of them.
- **A DEVICE SITS OVER WHOEVER IS BENEATH IT, NOT OVER THE BOYS (089 g8
  `nephews` -> Flintheart Glomgold).** The pass probed both boys' caps, found the
  same red on each, and recorded the collective -- having never established that
  the `?` hangs over the boys at all.
- **BOTH ADDED GROUPS ARE LETTERING THE PASS LEFT OUT OF `visible_text` (085 g13
  `? ?`, 088 g3 `POP`).** Checked against their own crops at 4-5x before
  mirroring: the two question marks hang between the balloon tails over the boys'
  silhouettes, and `POP` is the string parting by Scrooge's hand, so `nephews`
  and `none` are right as the review wrote them. The missed-text audit could not
  find either, because it only diffs what `visible_text` holds. **Transcribe
  drawn devices and small impact effects on every page**, not just signs.
- **MEDIUMS RAN 3/15 CORRECTED (20.0%) AGAINST HIGH'S 4.7%**, the fourth batch in
  a row where medium is the worse bet.
- **The canonical speaker is `Flintheart Glomgold`, with no `other:` prefix** --
  the apply canonicalises it and reports `Canonicalized 69 speaker value(s)`.
  Write it bare when a character is in the story's own cast list in `roster.txt`.

### Findings to paste into the next run (2026-09-16, sixtieth batch, THREE OF FOUR REVIEWED -- *Migrating Millions*, *The Cat Box*, *Grandma's Present*)

**226 groups over 19 pages, ZERO speaker corrections and ZERO `cap_colour`
corrections**, and all 17 type proposals held. By the confidence the pass wrote:
*Migrating Millions* high 0/73, medium 0/3; *The Cat Box* high 0/40, medium
0/10; *Grandma's Present* high 0/100. All three mirrored clean onto paddleocr --
group, `speaker_reviewed` and `identified_by` counts and the speaker,
`cap_colour`, confidence and type distributions identical per title. No group was
added by the review and the missed-text audit stayed at zero on all 19 pages.

- **READ THE ZERO AS A DENOMINATOR, NOT AS A METHOD RESULT.** *Migrating
  Millions* has **7** groups in the nephew domain; *The Cat Box* and *Grandma's
  Present* have **none at all** -- both are solo-Gyro stories whose casts are an
  inventor, a goose, a duck and two cats. A batch can score 0.0% simply by not
  containing the work that goes wrong. The fourth title of this batch, *Knight in
  Shining Armor*, is where the nephew reading actually was, and it is still out.
  Do not carry "the last batch ran at zero" into a cap-dense title as confidence.
- **A CLOUD EDGE ALONE IS NOT A THOUGHT; THE BUBBLE TRAIL AND THE BEAK ARE.**
  Four groups stored `dialogue` were thoughts (*Migrating Millions* 095 g2, 096
  g2; *Grandma's Present* 141 g14, 146 g1) and all four held. What separates them
  at 1.3-1.5x is a trail of **separate round bubbles** running to a **shut beak**,
  against a **pointed tail** and an **open beak**. The counter-example is
  *Grandma's Present* 141 p6, where Barks draws excited speech with a bumpy,
  cloud-like outline -- pointed tail, open beak, and it is dialogue as stored.
  Three of the seven solo-speaker balloons I checked this way flipped and four did
  not, so check them rather than assuming either way.
- **`allbold.py` CANNOT SCREEN FOR THIS, OR FOR THIS BATCH'S EMPHASIS.** It
  measures stroke width, and all four titles set emphasis in an **italic** of the
  same weight: on *Migrating Millions* 092 g1 the plainly slanted `ALWAYS` scores
  0.98. Run it, but on a title lettered this way expect it to report nothing and
  read the slant off the page image instead.
- **ANIMAL AND CHARACTER NOISES: 13 MOVES TO `dialogue`, ALL HELD.** Cat yowls
  lettered bare and lettered in a balloon, two cats hissing, a translated
  serenade. This confirms the roster rule rather than extending it.
- **BUT `GULP` STAYED `sound_effect` WITH ITS MAKER NAMED, AND THE REVIEW
  AGREED** (*The Cat Box* 137 g10, `speaker` `other:the grey cat`). This is the
  useful counter-datum to the corpus's 100-to-1 `sound_effect` -> `dialogue`
  trend: a swallow is the **throat**, not the voice, and it falls under the same
  exception the roster makes for a whistled tune. The shape that worked is
  **name the maker in `speaker` and leave the type alone**, with the reasoning in
  the note so a reviewer can flip it in one key.
- **A RELAYED VOICE KEEPS ITS OWNER, IN BOTH DIRECTIONS.** Through one machine in
  one story: *The Cat Box* 138 g10 is the cat's serenade coming out of the
  translator's horn and takes the cat; 140 g7 and g8 are Gyro's own singing
  coming out of the same horn and take Gyro. Both held. The horn is never the
  speaker.
- **IN A THREE-HANDER, THE PERSON NAMED IN THE LINE IS USUALLY THE ONE NOT
  SAYING IT.** *Grandma's Present* 148 p3 has two balloons that cross over --
  `YOU SURE WOULD HAVE IT EASY, GUS!` is Grandma's and `AND YOU'D HAVE IT EVEN
  EASIER, GRANDMA!` is Gus's, each addressed to the other, traced at 2.6x on
  silhouettes. And 148 g3, `YES, GRANDMA, AND ALL I'D HAVE TO DO ALL DAY IS TOSS
  IN ONE SHOVELFUL!`, reads as Gyro and is Gus: **Gyro is not in the panel at
  all**. Check who is in frame before letting the register assign anything.
- **A FORM OF ADDRESS SEPARATES NOBODY.** *Grandma's Present* 143 g11's `HEY!
  HOLD ON, MR. GEARLOOSE!` reads as Grandma's register, and it is Gus, who uses
  both `MR. GEARLOOSE` and `GYRO` inside two pages. Separate them on the drawing:
  Gus is a white goose in a **green cap** and dark vest, Grandma a duck with
  **white hair, a black dress and a white apron** and no cap.
- **SCROOGE'S TOP HAT BAND PRINTS THE ROSTER BLUE.** On *Migrating Millions* it
  is `#01a4d6`-`#08a4d2` H193-194, which is why 094 p3, 094 p7 and 096 p3 all
  report blue with no nephew wearing any. Same trap as the standing
  `Donald wears Dewey's blue` note -- check the head the blob sits on.
- **A REVIEW OVERWRITES `speaker_confidence` TO `high`.** All 226 groups now read
  high; the `--since` split above is the only surviving record of what the pass
  wrote. And `--since` mattered for type too: without it these three titles would
  have reported 17 + **27** stale rows -- 16 on *The Cat Box* and 11 on
  *Grandma's Present*, adjudicated 2026-08-22 to 08-24 -- nearly tripling the
  headline count.
- **CORPUS DRIFT WORTH A SWEEP, NOT MINE:** the apply canonicalises
  `other:Grandma Duck` to a bare `Grandma Duck`, and the corpus still carries
  **8 rows of the prefixed form** from an earlier title.

### Findings to paste into the next run (2026-09-16, sixtieth batch, FOUR OF FOUR -- *Knight in Shining Armor*, batch closed)

**148 groups, 11 speaker corrections (7.4%), 9 of them in the nephew domain (9
of 40, 22.5%)**; by the confidence the pass wrote, **high 8/124 (6.5%), medium
3/24 (12.5%)**. All 11 type proposals held, no text correction was proposed and
no group was added. Mirrored clean onto paddleocr: 148/148 reviewed, 126
`identified_by`, distributions identical. **Batch: 374 groups over 29 pages, 11
speaker corrections (2.9%) all in this one title, and 28 type proposals of which
every single one held.** 45 images, 1.55 per page.

- **EVERY UNDER-NAMING WAS A SCAN ZERO WRITTEN UP AS AN ABSENT CAP -- THE THIRD
  BATCH RUNNING.** Five of them (078 g10, 081 g18/g19/g20, 087 g11), and the
  review found a cap on four. The worst is **081 p8**, where I wrote *"all three
  are BARE-HEADED here even though the scene is a street: capwide over the whole
  panel at min_area=25 returns a single chromatic blob of 64px, #982d18, at the
  panel edge, and nothing on any crown"* -- and the review named all three off
  **blue, green and red**. Note what that means: I did exactly what the roster
  demands, quoted the census's own header, and the header was still wrong.
  Thirteen of these in the fifty-eighth batch, six in the fifty-ninth, five here.
- **AND I HAD ALREADY MEASURED THE TOOL'S BLINDNESS ON THIS VERY TITLE.** Two
  pages earlier I found that `title_bands` reports 086 p2 as `red=3 green=2
  blue=0` on a panel where a 1.5x crop shows all three boys banded, wrote that
  finding into the hand-back -- and then trusted a `capwide` zero on 081 p8
  anyway. **On a construction of thin coloured rims on black caps, a whole-panel
  scan at min_area=25 is simply blind, and the only thing that works is a 3-6x
  crop of each crown.** If a crop has already contradicted the scan once in a
  title, the scan is finished as evidence for that title -- do not spend it again.
- **THE SAME ERROR RAN IN THE OPPOSITE DIRECTION TWICE: A BLOB THAT WAS NOT ON A
  HEAD.** 078 g8 (`Dewey` blue -> **Huey** red) rested on *"his cap prints blue
  #00a3d2 2,927px at x788-875 y144-239"*, and 084 g1 (`Louie` green -> **Huey**
  red) on *"a green blob of #4fa43e H110.0 2,187px sits at (34,366,92,433) where
  his crown is"*. In both the blob was scenery, and in both I promoted the call
  with **"only one nephew in the panel"**. The unified rule for both directions:
  **a census gives you ink, not caps. Place the blob on a head with a crop before
  you name a boy from it OR declare him bare.** `sole-figure` is not a substitute
  for that crop -- it is what made these two high and medium instead of
  collective.
- **A LINE THAT STATES A CONDITION CONTRARY TO A CHARACTER'S SITUATION EXCLUDES
  HIM** (078 g9, `Donald` -> **Huey**). The line is `I GET IT! IF I WERE INVITED,
  I'D GO AS AN ICE-CREAM MAN!` -- and the invitation is Donald's, so the one duck
  on the page who cannot say it is Donald. The dialogue ruled him out before the
  art was even consulted, and I gave it to him on a figure read. With 078 g10
  going the same way, **neither balloon on that panel is Donald's**: the boys are
  saying what *they* would go as.
- **THE GAP-TIP METHOD WORKED, 3 OF 4 -- I PREDICTED THE OPPOSITE.** I flagged
  four gap-tip mediums (078 g2, 082 g1, 083 g11, 085 g11) and said that if they
  all reversed the finding would be about gap tips in this volume. **082 g1, 083
  g11 and 085 g11 all held**; only 078 g2 reversed, and it went `Huey` ->
  `Dewey`, i.e. to the same name the other three carry. Direction-of-tail plus
  the one-head-left rule is doing real work -- keep using it, at medium.
- **THE TEAL-AS-BLUE RANKING HELD EVERYWHERE IT WAS USED.** `#25a48a` / `#22a590`
  / `#00a288` at H167-170 was read as this volume's blue on 082 g1, 084 g0 and
  086 g2 and **all three held**. That is now confirmed twice over -- *Borderline
  Hero*'s H162-163 in the fifty-ninth batch and these here.
- **11 OF THE 14 BOYS I NAMED HELD.** Naming is not the risk; declining is, and
  all three reversals are the blob/gap failures above rather than anything about
  tails.
- **MEDIUM IS THE WORSE BET FOR THE FIFTH BATCH RUNNING**: 12.5% against high's
  6.5%.
- Two non-nephew corrections: **083 g2** `other:the guest in the bear costume` ->
  `other:the guest in the clown costume` (a costume read off a small background
  figure), and **085 g8** `narrator` -> `other:a party guest`. On g8 I reasoned
  from the drawing -- *"a squared box with no tail"* -- and the past-tense report
  `REGGIE SLAMMED THE DOOR BEHIND HIM AND IT LOCKED!` is a guest's line, not the
  author's. **A boxed line in the past tense is not automatically narration.**

### Findings to paste into the next run (2026-09-18, sixty-sixth batch, ALL FOUR REVIEWED AND MIRRORED -- batch closed)

**1,122 groups over 56 pages, 74 speaker corrections (6.6%).** By title:
*Special Delivery* 18/148 (12.2%), *The Code of Duckburg* 14/144 (9.7%),
*Forbidden Valley* 35/342 (10.2%), *Sagmore Springs Hotel* 7/146 (4.8%, plus 4
`unknown -> none` on groups the review itself added). By the confidence the
pass wrote: **high 68 of 743 (9.2%), medium 7 of 33 (21.2%)** -- and unlike every batch before it, **the errors are
overwhelmingly at HIGH confidence**, because they are not cap calls at all.
All 23 type proposals confirmed; the one text correction confirmed. All four
mirrored clean: group, reviewed and identified_by counts and the speaker /
cap_colour / confidence distributions equal on both engines.

- **WHEN EVERY DUCK WEARS THE SAME HAT, SIZE AND BEAK DO NOT SEPARATE DONALD
  FROM A NEPHEW. THE SHIRT DOES.** *Forbidden Valley* puts all four in brown
  pith helmets from 032 on, and **32 of its 35 corrections are Donald against
  the nephew domain, 16 each way** -- a coin toss with a confident note
  attached. Two panels re-read at 0.62x after the review show what was
  available for free: **Donald wears the red BOW TIE and the sailor blouse
  with the white-banded collar and cuffs; the boys wear plain black shirts
  with no collar.** On 038 p2 the bow-tied duck is second from the LEFT, and
  the pass's note says "the duck with the bow tie at the right"; on 041 p1 the
  striped collar is on the left duck and the pass had the two balloons
  crossed. Read the shirt, then trace each tail -- and note that a 250px
  montage will not show a collar stripe, so a panel with two ducks and two
  balloons needs the 0.55-0.62x view the ladder already allows.
- **A PANEL WITH NO CAP INK IS STILL A PANEL WHERE THE REVIEWER NAMES BOYS.**
  Under-naming was 15 of 18 in *Special Delivery*, 11 of 14 in *The Code of
  Duckburg* and 5 of 7 in *Sagmore Springs Hotel*, and nearly every one of those
  notes is a correct absence claim --
  `green 0 / blue 0 / leafgrn 0 blobs total`, `crowns.py lists no head with
  ink`, silhouettes, boys drawn as specks on a clothes line. The scan was
  right and the CONCLUSION was wrong: the review named them anyway, from the
  tail and from who is doing what in the scene. **A clean tail to one boy is a
  name even when his cap prints nothing.** Quote the zero, then name him
  anyway if the tail is unambiguous; `nephews` is for a tail you cannot
  place, not for a cap you cannot read.
- **BUT A TIP ON THE BOUNDARY IS STILL NOT A NAME.** All three of *Special
  Delivery*'s over-namings (158 g15, 159 g12, 159 g14) are gap tips the pass
  resolved with the one-head-left rule against a clean rim; the review made
  all three `nephews`. So: unreadable cap + clean tail -> name him; readable
  cap + tip in the gap -> collective. The two rules point opposite ways and
  the discriminator is the TAIL, not the ink.
- **MEASURE THE RIM ON THE BOY THE TAIL LANDS ON, NOT ON THE BOY NEXT TO
  HIM.** *The Code of Duckburg* 168 g3 and 169 g12 both went `Huey`/red ->
  `Louie`/green: the pass quoted a real red rim and a real pixel margin, and
  both belonged to the neighbour in a row of three. Where a row is tight, the
  crop has to contain the tail tip AND the crown being quoted, in one image.
- **A COLOURIST CLASH GETS SETTLED PANEL BY PANEL, WHICH IS WHAT
  CONVENTION-FLAGGED BUYS.** *Forbidden Valley*'s dialogue names a red-capped
  boy Dewey (025) and a blue-capped boy Louie (029). Read on the convention
  with the clash in every note, the review moved exactly **two** groups (026
  g3 -- the reviewer's own note reads "GLK decides to make this Dewey" -- and
  027 g7) and left every other red call as Huey. A title-wide remap would
  have been wrong about eighteen groups; `project_per_story_cap_palette` holds.
- **A TEAL WITH NO COOL RIVAL IN THE PANEL: the declines stood.** `#1ca3a3`
  H180 taken as blue with only red beside it, `#017f7b` H178 declined
  outright, `#429db5` S0.63 declined under the cool-band floor -- none was
  corrected. The floor and the rank-inside-the-panel rule are earning their
  keep.
- Type corrections confirmed 20 of 20, and they keep coming from the same two
  places: a character's cry or an animal's roar stored as `sound_effect` (OW,
  OWOOCH, YEEK, WAK, RAWR, SNORT, ROAR), and a caption box stored as
  `dialogue` or `background` (`So-`, `Top Floor!`, `SOON!`, the story logo).
- **THE PAGE CAPTURE IS THE AUDIT'S ONLY EYES, AND IT MISSED FOUR SIGNS.** The
  *Sagmore* review ADDED four background groups the pass had never seen -- 052
  `FOR SALE` and `MAP`, 055 `BANK of DUCKBURG`, 060 `HOTEL` -- and the
  missed-text audit was silent on every one, because none of them was in any
  page's `visible_text`. The audit cannot find what the capture never wrote
  down: sweep the EDGES of each panel and every prop carrying letters, not just
  the obvious shop fronts. The adds were otherwise clean -- background/none, no
  Copy In residue -- but 060's landed at g4 and renumbered the page, which is
  why a stored result.json is only good until the first add.
- Outstanding at close: *Sagmore* 055 g11 and 060 g16 are unreviewed on both
  engines (both Donald, high, unchanged) -- `queue-straggler.txt`, two lines.
  The missed-text findings are unworked: CoD 172's two music notes (a real add)
  and *Forbidden Valley*'s four (025 HISS!/SNARL! and 030 SSFZT!/SNORT!, all
  four lettered INSIDE an existing group and recommended for
  `missed-text-ignore.txt`).

### Findings to paste into the next run (2026-09-23, eightieth batch, ALL THREE REVIEWED AND MIRRORED -- batch closed)

**Closed at 144/144, 144/144 and 134/134 over 30 pages, both engines identical on
every title.** **26 speaker corrections over 422 groups (6.2%)**, 18 of them in
the nephew domain. By title: *The Floating Island* 5/144 (3.5%), *The Black
Forest Rescue* 4/144 (2.8%), *The Good Deeds* 17/134 (12.7%). 69 images, 2.30
per page.

COUNTING NOTE, worth knowing before reading any of these rates: `review_findings.py`
reports 7 / 5 / 17, because it counts the review setting a speaker on a group the
review ITSELF added (`unknown -> ...` on 123 g20, 124 g2, 130 g3) as a correction.
`volume_summary.py` reports 5 / 4 / 17. The second is the number that measures the
pass. Net the adds out before comparing a batch against an older one.

- **THE TITLE THAT NAMED MOST WAS CORRECTED MOST, AND THE NAMING RATE PREDICTED
  IT ALMOST EXACTLY.** *The Good Deeds* named 78% of its nephew domain and came
  back **12.7% corrected, 38.2% of that domain**; *Black Forest Rescue* named 15%
  and came back **2.8%**. The seventy-ninth batch's lesson was that more images
  do not buy accuracy. This is the sharper version: **naming aggressively is what
  costs, and it costs in proportion.** A 30-600px sliver is enough to READ a cap
  and not enough to survive being attached to the wrong head.
- **THE SINGLE BIGGEST ERROR CLASS IS A TIP THAT LANDS INSIDE A HEAD AND BELONGS
  TO THE HEAD ON ITS LEFT.** Six of *The Good Deeds*' 17 corrections are one
  nephew swapped for another, and **four of the six are exactly this**:
  | group | my tip | head it landed in | the answer |
  |---|---|---|---|
  | 028 g4 | x640 | Louie 600-700 | **Huey** 440-550 |
  | 032 g14 | x587 | Dewey 570-670 | **Huey** 480-570 |
  | 033 g5 | x660 | Louie's sliver 655-715 | **Dewey** 560-660 |
  | 034 g0 | x282 | Dewey 275-360 | **Louie** 160-250 |
  I measured the title's house habit correctly -- the tails hang 6-44px RIGHT of
  their owner, and the three calls I made from it on the reference panel 027 p2
  all stand -- and then **applied it only to tips that fell in GAPS.** When a tip
  landed inside a head I simply took that head. **The rule to carry: once a
  title's tails are measured hanging right, a tip INSIDE a head is evidence for
  the head to its LEFT.** The one counter-example is 029 g8, where the tip was
  7px past Louie, I wrote "nearness, right-hang and one-head-left all agree", and
  it was Huey -- one head RIGHT.
- **OVER-NAMING IS A REAL CLASS NOW, AND THAT IS NEW.** Four of the 17 are a name
  reverted to `nephews`, every one with the cap colour cleared -- 027 g1 (the
  splash), 028 g1, 031 g9, 036 g8 -- against **one** under-naming the whole
  batch (035 g7 -> Huey/red, where I had written "capwide finds no roster sliver
  anywhere in it" and there was red ink). For eighty batches under-naming has
  been the largest class. In a title whose ink is a sliver it inverted. Do not
  carry "under-naming is the error" into a sliver title as if it were settled.
- **A NOTE I FLAGGED AND DECLINED TO CASH WAS RIGHT.** *Black Forest Rescue* 135
  g11: I recorded `narrator` and wrote "FLAGGED: it says 'we lose OUR hound',
  which is a Woodchuck's voice rather than a neutral narrator, but the standing
  rule records the BOX". The review made it `nephews`. **When the note names the
  alternative and the alternative is a speaker, take it** -- the standing
  caption rule is not a reason to write a call you have already argued against.
- **TWO SPECIES CALLS MADE AT STACK SCALE WERE WRONG.** *Black Forest* 132 g2 and
  135 g10 both went `nephews` -> `other:a Junior Woodchuck`: I read a duck where
  the reviewer read a pig. Both were the calls in that title I made off a
  0.6-0.7x contact strip rather than a panel crop. Duck-or-pig is legible at
  montage scale for a figure drawn large; it is NOT at 0.62x for one in a crowd.
- **THE CAPTURE IS STILL THE AUDIT'S ONLY EYES.** The review added **123 g20
  `BILL`**, a scrawled word on the tax collector's paper as he hands it to
  Scrooge. The missed-text audit was silent because page 123's `visible_text`
  held only its two `MAP` labels. Same failure as *Sagmore*'s four signs in the
  seventy-eighth batch: **sweep the props that carry letters, not just the shop
  fronts.** The pass's own two findings (124 g2 and 130 g3, both a drawn `!`)
  were added and both were typed and assigned exactly as proposed.
- **THE INSTRUMENT-NOISE QUESTION IS ANSWERED, AND THE ROSTER'S TEST WINS.** I
  left *Black Forest Rescue*'s ~15 bugle calls and drum messages as
  `sound_effect` and flagged it for a ruling. The reviewer left every one of
  them alone **while actively re-typing four other groups in the same title**,
  and confirmed all eight of my animal-voice corrections (133 g4/g6 the forest
  animals, 135 g2/g4/g6/g9/g12 the hound). So: **an animal's cry is dialogue; an
  instrument is not.** `project_instrument_noise_names_the_player` does not
  extend to bugles and drums.
- **AND A SNORE IS A VOICE.** *The Good Deeds* 032 g4 `ZZZZZ` went
  `sound_effect`/`none` -> `dialogue`/`other:the pilot`. I had it as the plain
  noise of a sleeping man.
- **THE ALVIS LESSLY REVERT HELD.** 030 g11 stayed `none`/`sound_effect` through
  the review and none of the five reverted siblings was re-corrected. The
  2026-09-18 call stands, and the general rule with it: **when a type ruling
  would cover a whole class of lettering, grep the title for a member of that
  class that is already reviewed before proposing it.**
- **A NEAR-DUPLICATE TO WATCH, INTRODUCED BY THE REVIEW.** *The Good Deeds* now
  carries both `other:the crop-duster pilot` (9) and `other:the pilot` (1), the
  latter from the 032 g4 correction above. Left as the reviewer set it -- a
  review outranks the pass -- but it wants merging.
- **CORRECTION RATE BY THE CONFIDENCE THE PASS WROTE.** *Floating Island* high
  2.3% (3/130) vs medium 25.0% (3/12); *Good Deeds* high 8.4% (9/107) vs medium
  29.6% (8/27); *Black Forest* high 3.3% vs medium 4.5% -- flat only because the
  uniform forced collectives that cannot be wrong. Medium is 3-11x worse wherever
  the art can actually separate anybody.
- **THE STRAGGLER WAS ONE PER TITLE, THREE FOR THREE, AND ALL THREE AGREED WITH
  THE PASS** -- 124 g13 (Scrooge), 132 g13 (Donald), 036 g4 (`other:the farmer`).
  132 g13 is the known pattern: a type change (dialogue -> thought) that leaves
  the speaker unticked. **They were also ticked WHILE THE MIRROR WAS RUNNING**,
  so the first mirror left paddleocr one short on all three titles and had to be
  re-run (910f01bb corrects 34f6accb). Re-read the reviewed counts off disk
  immediately before `--write`, not from a count taken earlier in the session.
- **`roster.txt` IS PER TITLE AND I READ ONLY THE FIRST ONE.** It carries, under
  "and, tagged in the database as appearing in THIS story", the cast the comics
  database already knows the story contains -- and `queue.json` carries the same
  thing as `story_cast` / `story_things`. *The Floating Island*'s cast section is
  EMPTY, so having read that one in full I wrote "same roster, I've read it" for
  the other two. They were not the same:
  - *The Black Forest Rescue*: **General Snozzie**, **Junior Woodchucks**
  - *The Good Deeds*: **Neighbor Jones**, and `airplanes` under notable things
  The skill's "read that file in full before page 1, every time" is not about the
  fixed vocabulary -- that part genuinely does not change. It is about these four
  or five lines, which are the only per-title content in the file. **Grep the new
  roster for the cast block even if nothing else in it can have moved.**
- **THE STORY'S OWN NAMING WINS OVER THE DATABASE TAG -- RULED 2026-09-23.** Both
  cases above were put to the reviewer and both were left as free text:
  - the bloodhound stays **`other:the official hound`**, not `General Snozzie`,
    even though Vol. 19 carries 11 groups of the same dog under the bare name.
    *The Black Forest Rescue* never speaks his name; it calls him "the official
    Junior Woodchuck bloodhound", so that is what the record says.
  - the neighbour stays **`other:Old Pupp`**, not `Neighbor Jones`, because the
    dialogue names him MR. PUPP twice on 027 while the tag is only the database's
    view of which recurring character appears.
  So the cast block is a **spelling aid for a character the story DOES name**,
  not an instruction to rename one it names differently or not at all. It stops
  `other:Magica de Spell` / `other:Magica` drift; it does not overrule the page.
- **`Junior Woodchucks` AND `other:a Junior Woodchuck` ARE BOTH RIGHT, AND THEY
  MEAN DIFFERENT THINGS.** The corpus already separates them and the distinction
  is the same shape as `nephews` against a named boy:
  - bare **`Junior Woodchucks`** = the troop speaking as ONE. Vol. 19 p130, 6
    groups: a hall reciting a rhyme, twenty-four singing from inside a pie.
  - **`other:a Junior Woodchuck`** = ONE unnamed member. Vol. 11 p52 and p63, 6
    groups, notes reading "the pig-faced club member at the right" and "alone on
    the porch, reading the flashes".
  All 25 in *The Black Forest Rescue* are individuals, so they stay. Bare
  `Junior Woodchucks` would also collide with the title's 33 `nephews` groups,
  since the nephews ARE Junior Woodchucks in this story.
- **AND THE NEAR-DUPLICATE THE REVIEW INTRODUCED IS FIXED.** *The Good Deeds* 032
  g4 came out of review as `other:the pilot` against nine `other:the crop-duster
  pilot`; normalised to the latter (569435c2). Worth running the `other:` census
  per title AFTER the review as well as after the pass -- this one did not exist
  until the review created it.
- `other:` after review, per title. *Floating Island*: `a tax collector` (7),
  `the TV announcer` (3), `the pilot` (2), `the ship's captain`. *Black Forest
  Rescue*: `a Junior Woodchuck` (25), `the official hound` (7), `the Woodchuck
  commander` (4), `Joe` (2), `the forest animals` (2). *The Good Deeds*: `the
  crop-duster pilot` (10), `a picnicker` (6), `the old man` (4), `Old Pupp` (3),
  `the bull` (3), `the bakery driver` (2), `a policeman` (2), `Gwendolyn`,
  `a motorist`, `the farmer`. (`the pilot` normalised away -- see above.)

### Findings to paste into the next run (2026-09-23, eightieth batch, NONE REVIEWED)

*The Floating Island* (Vol. 21, 10pp, 142 groups), *The Black Forest Rescue*
(Vol. 21, 10pp, 143), *The Good Deeds* (Vol. 23, 10pp, 134). **69 images over 30
pages, 2.30 per page**; per title 2.80 / 1.80 / 2.30. Every figure below is the
pass's own and none of it has been checked.

- **VOL. 23 IS OPEN, AND ITS CAP IS A SLIVER.** *The Good Deeds* is the first
  title ever read in the volume. The construction is a BLACK beanie whose ink
  survives only as a thin wedge at the cap/skull join -- **30 to 600px** --
  reference panel **027 panel 2**, blue `#00a6d9` x116-125 (Dewey), green
  `#009d45` x341-363 (Louie), red `#e61b1f` x566-578 (Huey), left to right; 035
  panel 4 is a second clean row. **Every decoy in the title is an order of
  magnitude bigger**: Donald's blue cap 400-900px, his red bow tie 600-1,700px,
  Old Pupp's red sweater 27,000-52,000px, the river 76,116px, and the grass
  shares the cap green's hue at 8,700-11,400px. A hue match alone names nobody
  here; the wedge has to be on a crown.
- **THE THREE TITLES SPLIT 78% / 45% / 15% ON NAMING, AND THE CAUSE IS THE
  COSTUME, NOT THE EFFORT.** *The Good Deeds* named 28 of 36 nephew-domain
  calls, *The Floating Island* 10 of 22, *The Black Forest Rescue* 6 of 40 --
  and Black Forest is the CHEAPEST title of the three at 1.80 images/page.
  There the boys are in **Junior Woodchuck uniform**, identical grey scout caps,
  so `cap_colour` is null on all 143 groups and no amount of cropping can help.
  This is the Pizarro lesson from the seventy-ninth batch arriving from the
  other side: when the cast is in uniform, stop buying images and write the
  collective.
- **A TITLE CAN HAVE A HOUSE HABIT FOR WHERE THE TAIL HANGS, AND IT IS WORTH
  MEASURING EARLY.** In *The Good Deeds* the tip lands a little to the RIGHT of
  its owner's head -- 6, 9, 20, 35, 37 and 44px across 027 p2, 036 p7 and 030
  p7. Establishing that on the reference panel settled five later tips that fell
  in gaps. Two tips still disagreed with it (030 g14 at 30px LEFT, 032 g10 at
  1px left of Dewey) and both are recorded medium.
- **THE VOCATIVE NAMES THE ADDRESSEE, AND IN A UNIFORM TITLE THAT IS THE ONLY
  KEY LEFT.** All six names in *Black Forest Rescue* come from four vocatives --
  "GENERAL DEWEY" once, "GENERAL HUEY" three times -- each spoken BY a non-duck
  Woodchuck TO a nephew. The second key is that the troop is MIXED: the nephews
  are the ducks and the other Woodchucks are pink-faced pigs and dogs, which
  separates `nephews` from `other:a Junior Woodchuck` in every panel and is
  legible at montage scale.
- **A SCALLOPED BOX WITH A JAGGED TAIL INTO A MACHINE IS NOT A CAPTION.**
  *Floating Island* 118 g10/g11/g12 were stored `narration` and are broadcast
  balloons coming out of the television -- the tail enters the screen frame on
  p7 and the cabinet on p8. Corrected to `dialogue` / `other:the TV announcer`.
  118 g11 is also lettered entirely in a slanted face and takes `[i]` over the
  whole group. The title's real narrator captions (118 g3 `AND SO!`, 119 g11
  `SOON!`) are plain rectangles and were left alone.
- **I OVERRULED A REVIEW WITHOUT SEEING IT, AND `vision_apply` IS WHAT CAUGHT
  ME.** In *The Good Deeds* I read the radio's song as Alvis Lessly's relayed
  singing voice -- 030 g7 names him -- and moved six groups from `sound_effect`
  to `dialogue`. One of the six, **030 g11, already carried `speaker_reviewed`
  and `type_reviewed` dated 2026-09-18**, settled by hand as `none` /
  `sound_effect`. The apply refused that one group and reported "left the
  speaker call on 2 already-reviewed group(s) alone", which is the only reason
  the conflict surfaced at all. **Reverted all five siblings to match**
  (commit c944fff9). Two lessons: read the apply's already-reviewed line as a
  FINDING, not as noise; and before proposing a type rule that covers a whole
  class of lettering, grep the title for a group of that class that is already
  reviewed.
- **THE SOUND-EFFECT TYPE RULE IS STILL UNSETTLED AND I DID NOT SWEEP IT.**
  *Black Forest Rescue* is ~15 groups of bugle calls and drum messages. The
  roster's own test (does a CHARACTER'S VOICE make the sound) keeps an
  instrument as `sound_effect`, while `project_instrument_noise_names_the_player`
  in memory says dialogue. I left the types alone and named the maker in the
  speaker field instead. **This needs a ruling**; it is the same question the
  Alvis Lessly revert just answered one way.
- **WHAT I DID CORRECT** in that title: the bloodhound's howls and sneezes (135
  g2/g4/g6/g9/g12) and the forest animals' cries (133 g4/g6) are voices, and 136
  g18 `GLUB!` is drawn as a thought cloud with a bubble trail. 135 g7, the same
  howl, was ALREADY stored as `dialogue`, which is what made the inconsistency
  visible.
- **MISSED TEXT: ONE ITEM PER VOL. 21 TITLE, NONE IN VOL. 23.** *Floating
  Island* 124 p2 and *Black Forest Rescue* 130 p3, both a lone drawn `!`. *The
  Good Deeds* returns 0 in all three audit classes. Both findings were spotted
  during the read and the audit then confirmed them, which is the first time the
  two have agreed exactly.
- **A STACK IS NOT A SET OF COORDINATES EITHER.** Twice in *The Good Deeds* I
  computed a panel's head positions from a stacked contact strip and cropped
  200-300px below the heads, wasting two image reads. The existing rule says a
  stack is not a MEASUREMENT; it is also not a source of crop boxes, because the
  per-crop offsets inside the strip have to be subtracted first.
- `other:` after the pass, per title. *Floating Island*: `a tax collector` (7),
  `the TV announcer` (3), `the pilot` (2), `the ship's captain`. *Black Forest
  Rescue*: `a Junior Woodchuck` (24), `the official hound` (7), `the Woodchuck
  commander` (3), `Joe` (2), `the forest animals` (2). *The Good Deeds*: `the
  crop-duster pilot` (9), `a picnicker` (6), `the old man` (4), `Old Pupp` (3),
  `the bull` (3), `the bakery driver` (2), `a motorist` (2), `Gwendolyn`, `the
  farmer`, `a policeman`. No near-duplicates; `a Junior Woodchuck` deliberately
  excludes the nephews, who are Junior Woodchucks too but are named `nephews`.
- Outstanding at hand-back: **11 type corrections** (*Floating Island* 3,
  *Black Forest Rescue* 8, *The Good Deeds* 0 -- 22 queue entries, since each is
  listed per engine), **no text corrections at all**, and **417 unreviewed
  speaker groups** (142 + 143 + 132; *The Good Deeds* carries 2 groups reviewed
  by hand on 2026-09-18 that the pass left alone).

### Findings to paste into the next run (2026-09-22, seventy-ninth batch, ALL FOUR REVIEWED AND MIRRORED -- batch closed)

**Closed at 487/487 reviewed over 38 pages, both engines identical on every
title.** 64 speaker corrections (13.1%), and 44 of the batch's 73 nephew-domain
calls (60%). By title: *His Handy Andy* 3/57 (5.3%), *The Firefly Tracker* 1/56
(1.8%), *The Prize of Pizarro* 48/243 (19.8%), *The Lovelorn Fireman* 12/131
(9.2%).

**90 images over 38 pages, 2.37 per page** -- 56 for the pass at 1.47, then 34
more re-reading Pizarro's unreviewed half and cropping all 47 of its flagged
emphasis balloons after the review caught it at page 156. **Pizarro alone cost
60 images over 20 pages, 3.00, and still came back 19.8% corrected.** That is
the most expensive title in the ledger and the worst corrected, in the same
row: past a point, more looking does not buy accuracy on a title whose cast is
in identical costume.

- **ONE TITLE IS THE WHOLE BATCH.** Pizarro alone is 48 of the 64 corrections
  and 34 of the 44 nephew-domain ones. The other three run 1.8-9.2%, which is
  the normal band. **What separates them is not length or cap ink -- it is that
  from page 155 Pizarro puts the entire five-duck cast in identical
  conquistador armour.** *The Firefly Tracker*, a Gyro solo, took ONE
  correction in 56 groups. The cost doc's line holds: the number to watch is
  live identity axes per panel, not pages or images.
- **UNDER-NAMING IS STILL THE LARGEST CLASS AND IT IS STILL THE SAME SENTENCE.**
  19 of the 64 are `nephews -> a name`, and nearly every one has a note saying
  some version of "no roster ink on this head". *Lovelorn Fireman* 109 g0/g1 and
  115 g12/g13 and 116 g3 all read that way and came back Louie, Dewey, Louie,
  Dewey, Huey. **The absence sentence is the most expensive thing in the
  vocabulary and it is still being written off the wrong tool** -- `title_heads`
  uses capscan's hard hue bands, and `capwide` spans them.
- **A CAPTION CAN CARRY A CHARACTER'S VOICE, AND THE REVIEW SAYS SO.**
  *Lovelorn Fireman* 110 g8 and 110 g11 stay typed `narration` but their
  speaker is now **Chief Feathergoose** and **Donald** -- caption boxes that
  complete the sentence a character started in the balloon above. The standing
  rule is that the speaker field records the BOX, so this is recorded and NOT
  generalised: ask the reviewer before applying it to a title's captions
  wholesale.
- **TWO CORRECTIONS CAME FROM MY OWN CROP BEING READ BACKWARDS.**
  *Lovelorn Fireman* 113 g6 was traced onto the red-capped boy of two and is the
  blue one; 115 g1's drawn `?` hangs over Gladstone, not Daisy. Cropping is not
  the end of the job -- the crop still has to be read left to right against the
  census, and on 113 the census had already said which head was which.
- **`other:` VOCABULARY IS A CHEAP CLASS TO STOP LOSING.** Across the batch 14
  corrections were an `other:` role rather than a face: four householders became
  `a villager`, `a mine guard` and `the Royal Guardian` were swapped in both
  directions, and three lines moved onto `Chief Feathergoose`. **Prefer the
  plainest role word, and re-use a value already in the title rather than
  inventing a finer one.**
- `other:` after review, per title. *His Handy Andy*: `a yachtsman` (6),
  `Lord Taffrail` (2), `Captain Seabug` (2), `the announcer` (2), `Cornwell
  Mushmore`, `Colonel Rawcuss Yellowpress`, `Commodore Leadpipe J. Cinch`,
  `a crewman`, `his lordship`, `her ladyship`. *Firefly Tracker*: `a merit
  judge` (3), `the merit judges`, `a banquet guest` (2), `the toastmaster`.
  *Pizarro*: `a mine guard` (35), `the Royal Guardian` (11), `a villager` (4),
  `the mayor` (2), `a city councilman`, `the city councilmen`, `the firemen and
  policemen`, `the mine guards`, `Donald and the nephews`. *Lovelorn Fireman*:
  `Chief Feathergoose` (11), `a Duckburg citizen` (3), `a cat` (3), `a magazine
  photographer` (3). No near-duplicates left; the singular/plural pairs are
  deliberate.
- **THE STRAGGLER WAS ONE PER TITLE, FOUR FOR FOUR, AND ALL FOUR AGREED WITH
  THE PASS.** A caption, a Gyro thought, a Scrooge-alone line and Daisy's
  `I LIKE THIS!`. Four batches, four different causes. Just run `--unreviewed`.

### Findings to paste into the next run (2026-09-22, seventy-ninth batch, THREE OF FOUR REVIEWED AND MIRRORED)

**His Handy Andy 57/57, The Firefly Tracker 56/56, The Prize of Pizarro
246/246**, every group reviewed on both engines and every cross-engine figure
identical. *The Lovelorn Fireman* is 16/131 and still being worked. Combined:
**55 speaker corrections over 359 groups (15.3%)**, and the whole of the damage
is in one title.

- *His Handy Andy* 3/57 (5.3%), *The Firefly Tracker* 1/56 (1.8%), *The Prize
  of Pizarro* **51/246 (20.7%), and 35 of its 42 nephew-domain calls (83.3%)**.
  By the confidence the pass wrote: **high 27 of 190 (14.2%), medium 21 of 53
  (39.6%)**.

- **THE MID-BATCH RE-READ BARELY WORKED, AND THAT IS THE FINDING.** The review
  caught the pass at page 156 and the whole unreviewed remainder was re-read
  with capwide per panel and a crop for every contested tail. Split at that
  line: pages 146-156, read the first way, came back **20.1% corrected, 75% of
  the nephew domain**; pages 157-165, re-read carefully first, came back
  **19.3% corrected, 57% of the nephew domain**. Cropping every contested tail
  bought 18 points in the nephew domain and nothing overall. **A title where the
  cast is in identical costume is not fixed by looking harder at the tails.**

- **I REPLACED ONE BIAS WITH ANOTHER AND IT COST FOUR CALLS.** The first read
  gave unresolvable party lines to Donald; the review moved eight of those to
  the nephew domain; so on the re-read I adopted "where the art cannot separate,
  record the collective, because the review moved eight Donalds and none the
  other way" and wrote that reasoning into the notes. Four of those collectives
  came back as ADULTS -- 157 g1 and 162 g2 to Scrooge, 158 g7 and 163 g1 to
  Donald. **Calibrating against the reviewer's last corrections is still a
  premise applied blind.** The one group I left `unknown` (164 g14) was resolved
  correctly by the review at no cost. Where the art genuinely cannot separate a
  speaker, `unknown` beats either bias.

- **A THIRD OF THE RE-READ'S CORRECTIONS WERE `other:` VOCABULARY, NOT ART.**
  Seven of 21. The four householders on 165 were written `a Duckburg citizen`
  x3 and `a gold dealer`; the review made all four **`other:a villager`**. And
  `a mine guard` against `the Royal Guardian` was swapped in both directions
  (158 g5, 159 g10, 163 g13) -- the Guardian is the one in the feathered
  headdress and cape and he gives orders; a guard appealing TO him is not him.
  This is the cheapest class of correction to stop making: **prefer the plainest
  role word, and re-use a value already in the title rather than inventing a
  finer one.**

- **THE STRAGGLERS WERE A CAPTION, A GYRO THOUGHT AND A SCROOGE-ALONE LINE**,
  one per title, all three agreed with the pass. That is a fourth distinct
  straggler cause in four batches, which confirms the standing advice: stop
  predicting which one it is and just run `--unreviewed` at close.

- `other:` after review. *Handy Andy*: `a yachtsman` (6), `Lord Taffrail` (2),
  `Captain Seabug` (2), `the announcer` (2), `Cornwell Mushmore`, `Colonel
  Rawcuss Yellowpress`, `Commodore Leadpipe J. Cinch`, `a crewman`, `his
  lordship`, `her ladyship` -- the lordship pair survived review, so they are
  NOT the Taffrails. *Firefly Tracker*: `a merit judge` (3), `the merit judges`,
  `a banquet guest` (2), `the toastmaster`. *Pizarro*: `a mine guard` (35), `the
  Royal Guardian` (11), `a villager` (4), `the mayor` (2), `a city councilman`,
  `the city councilmen`, `the firemen and policemen`, `the mine guards`,
  `Donald and the nephews`. The singular/plural pairs are deliberate in both
  titles and must not be merged.

### Findings to paste into the next run (2026-09-22, seventy-ninth batch, CORRECTIONS IN REVIEW)

Two things the review caught that the pass had wrong across all four titles.
Both are mine and both are now fixed at source.

- **THE CORPUS IS STILL SHORT AND A BACKFILL IS OWED.** The fix below is at
  source only. `docs/emphasis-backfill.md` has the evidence, the per-title
  commands and the three traps; `closeout.sh` prints a TODO row until it is
  done. Do NOT re-open the low rates in Vols. 1-3 -- those were checked
  against the art and they are correct.
- **A THRESHOLD I TOOK FROM A SENTENCE THAT WAS NOT ABOUT DETECTION.**
  `allbold.py` says "confirm anything under about 1.3x with a crop". That is a
  CONFIDENCE line. I used 1.30 as a detection floor and it discarded 115 bold
  words across the batch. Measured over 3,261 word ratios the distribution is
  cleanly bimodal -- plain lettering masses at 0.90-1.10, a trough at 1.10-1.20,
  bold rises from 1.20 and peaks at **1.30-1.35** -- so the cut sat inside the
  bold peak. `SHORT!` measures 1.25, `LOSING` 1.22, `TEN FEET` 1.12, and all are
  plainly bold-italic at 2.4x. **A fixed number cannot work anyway**, because
  `allbold` reports each word against its OWN GROUP's baseline: a balloon that is
  mostly bold pulls the baseline up and compresses every ratio in it.
  `emphasis_candidates.py` now splits each group at the widest gap in its own
  sorted ratios instead. Emphasis went 216 runs to 329 across the batch.
- **THE `??` LINES ARE WHERE THE EMPHASIS HIDES, AND THEY HAVE TO BE CROPPED.**
  `allbold` flags a line whose blob count disagrees with its word count; the
  generator prints those unmarked and they are easy to skip. I reasoned about
  twenty of them out by hand and then the assembly script read the auto-only JSON
  and shipped none of them. Of the 47 such balloons in *Pizarro*, cropping at 2x
  found **twelve runs missing entirely and four places already marked WRONG**.
  Budget the crops: 47 balloons is eight stacked images, which is cheap against a
  reviewer finding them one at a time.
- **CLEARING A TAG NEEDS THE UNTAGGED TEXT SENT EXPLICITLY.** An absent
  `emphasis_markup` means "this run said nothing about emphasis", so it KEEPS
  what is stored -- popping the key does not remove a tag. And `vision_mirror`
  does not carry a removal to the other engine, so a cleared group needs the
  paddleocr side done by hand. Both traps hit this batch.
- **A BLOB ON THE GROUP'S BOX EDGE IS THE BALLOON OUTLINE.** It is the single
  commonest false positive and it is always high -- 1.63 on *Firefly Tracker*
  185 g7, 2.04 on *Pizarro* 152 g7. The generator filters it, but only because it
  reads the PANEL-space boxes out of `<out-dir>/boxes.txt`; without that file the
  filter silently does nothing.

### Findings to paste into the next run (2026-09-22, seventy-ninth batch, NONE REVIEWED)

**Four titles, 38 pages, 487 groups, 56 images = 1.47 per page.** *His Handy
Andy* (Vol. 22, 4pp, 57 groups, 2.75/page), *The Firefly Tracker* (Vol. 22, 4pp,
56, 1.75), *The Prize of Pizarro* (Vol. 22, 20pp, 243, 1.30), *The Lovelorn
Fireman* (Vol. 21, 10pp, 131, 1.20). 7 type corrections, no text corrections,
1 missed-text finding. Nothing is reviewed yet, so there are no correction
rates in this section -- these are the reading findings only.

- **A CAP SCAN'S ZERO WAS A FLOOR, AND IT NEARLY COST A WHOLE TITLE'S NAMES.**
  On *Pizarro* the first montage read said flatly "the nephews are bare-headed
  in this title". They are not. The Vol. 22 quartered beanie prints a **12-660px
  sliver** where the cap meets the skull, and `title_heads.py`'s default 25px cap
  floor hid nearly all of it -- 147 p5 came back with nothing and, re-run at
  `title_heads.py <out-dir> 300 6`, names all three boys (green x142-283, blue
  x345-490, red x541-684 = Louie, Dewey, Huey left to right). **On a Vol. 22
  title, run the head census at a 6px cap floor before writing any absence
  claim**; the palette table has said "sweep at 6px or the title reads as
  capless" since *Pyramid Scheme* and I still had to be shown it by a crop.
- **AND A SCAN'S ZERO CAN BE A BAND EDGE, WHICH IS THE OTHER HALF.** *The
  Lovelorn Fireman* reports `green 0` in every one of its 77 panels. Louie's cap
  there prints **`#4ba43f` H112.9 S0.62** -- a leaf green outside capscan's
  `green` band (H140-182) AND outside the Vol. 21 roster green at H146-155. Only
  `capwide.py` finds it. **A title-wide green of exactly zero is a reason to run
  capwide, not a reason to say the boy has no cap.**
- **THE VOCATIVE SPLIT IS A REAL DISCRIMINATOR AND IT IS FREE.** Across
  *Pizarro*'s 20 pages Donald says **UNCLE SCROOGE** and the boys say **UNCA
  SCROOGE**, without exception. I checked it against three independently
  tail-traced calls (151 g8, 162 g14, 165 g9) and it held on all three, so I
  then used it on eight more groups that had no other evidence. It is register,
  which the roster warns about -- but this is a spelling the letterer chose, not
  a tone I inferred, and it is checkable. Say in the note that it is what the
  call rests on.
- **THE SAME JACKET ON TWO DUCKS: THE HAIR CURL IS THE TELL.** *The Lovelorn
  Fireman* 114 p6 onward draws **Gladstone** in a maroon jacket with a yellow bow
  tie, and I read the first four of those panels as Donald because Donald had
  worn a "new Hollywood jacket" earlier in the story. Donald is **bald**;
  Gladstone has the curl. Getting it wrong would have made the story's central
  gag unreadable -- the visitor promises "I'LL SAVE YOU, DAISY!", bolts through
  the door, and comes back only for his record collection. **Where two ducks are
  dressed alike, find the feature that cannot be swapped (hair, beak, whiskers)
  before assigning a single balloon.**
- **AN ADULT'S HAT BAND PRINTS THE ROSTER BLUE AS OFTEN AS A BOY'S CAP DOES.**
  Three of the four titles have this. Scrooge's blue skipper's cap in *His Handy
  Andy* runs 2,200-2,740px; his top-hat band in *Pizarro* runs 300-2,500px;
  Donald's sailor cap runs 600-7,200px. A nephew's sliver in the same volume is
  12-660px. **Area separates them only at the extremes** -- 151 p1's 1,233px blob
  was Scrooge's hat band and 148 p3's 661px blob could not be told from a boy's,
  so I declined to name Dewey there and said why.
- **A TYPE ALREADY REVIEWED IS NOT A TYPE TO PROPOSE.** *The Firefly Tracker*
  185 g10 is a red placard the chart marker plants in the ground, which reads to
  me as scene lettering. A **2026-09-17 type review had already moved it from
  background to narration**, and `_apply_type` refused my proposal on the
  `type_reviewed` guard rather than reversing a human. Check the stored group for
  review flags before writing a type field; the out-dir's `groups.json` does not
  carry them, so it has to be the prelim JSON.
- **AN ANIMAL'S CRY IS DIALOGUE, AND SO IS A YELL.** Five of the batch's seven
  type corrections are this: *Lovelorn Fireman* 107's three cat cries
  (SCREECH/SQUEECH/YOWL -- the "family" Donald is sent to save), 111 g14's YOW as
  the sockfoot kick goes through the skylight, and 107 g0, the story logo stored
  as `background` rather than `title`. The other two are *Pizarro* 152 g4, a
  scalloped cloud with a bubble trail stored as `dialogue`, and *Firefly Tracker*
  187 g9, a headline-shaped announcement that is a speech balloon with a tail
  onto the banquet toastmaster.
- **THE MISSED-TEXT AUDIT IS ONLY AS HONEST AS `visible_text`, BOTH WAYS.** It
  found the real thing -- a drawn `?` on *Pizarro* 149 panel 5 that neither engine
  grouped, queued as `queue-missed.txt`. It also reported two findings on
  *Lovelorn Fireman* that were **my own transcription slips**: the fire alarm is
  lettered `SKREEEEEE` (9 characters) on 110 and 115 and I had written eight E's
  into the capture. **Count the letters in a drawn sound effect against the
  stored group before filing it as visible_text**, or the audit manufactures work
  for the reviewer.
- **WHAT `nephews` IS STILL DOING HERE, AND THE RULE I USED.** *Pizarro* is 20
  pages with the boys in nearly every panel and I named exactly three of them
  (164 g1 Dewey, 165 g9 Huey, plus Dewey addressed but silent on 151 p1). The
  rule I applied, and the reviewer should hold me to it: **name a boy only where
  a vocative names him, or where a roster sliver sits on the head a traced tail
  lands on.** Under-naming is the standing error class, so if the review comes
  back naming a dozen of those collectives, the rule is too tight and the fix is
  a 2x crop of the crown, not a looser reading of the census.
- `other:` values, measured off disk after the apply. *His Handy Andy*:
  `Cornwell Mushmore`, `Colonel Rawcuss Yellowpress`, `Commodore Leadpipe J.
  Cinch`, `Lord Taffrail`, `a crewman`, `a yachtsman` (5), `Captain Seabug`.
  *Firefly Tracker*: `Gyro's Helper`, `a merit judge` (4), `the toastmaster`,
  `a banquet guest` (2). *Pizarro*: `a mine guard` (38), `the Royal Guardian`
  (9), `the mayor` (3), `the city councilmen`, `the firemen and policemen`,
  `a Duckburg citizen` (3), `a gold dealer`, `a spectator`, `the announcer` (2).
  *Lovelorn Fireman*: `Chief Feathergoose` (8), `a magazine photographer` (3),
  `a cat` (3), `a Duckburg citizen` (3). **Two pairs to look at**: `a crewman`
  against `a yachtsman` in *Handy Andy* (a hired hand at the rail against the
  racers, which I believe is a distinction and not drift), and `his lordship` /
  `her ladyship` on 144 against `Lord Taffrail` on 142 -- the couple in the
  tropics are NOT drawn as the 142 p6 pair, so I declined to name them, but if
  the reviewer reads them as the Taffrails those two should be merged.
- **ONE CORRECTION OUTSTANDING THAT PREDATES THIS BATCH.** A corpus-wide
  `vision-corrections` run reports 15 outstanding, 14 of which are this batch's
  seven type corrections across both engines. The fifteenth is **vol 23, *The
  Librarian*, 118 g19, `thought -> dialogue`**, and it is not mine.

### Findings to paste into the next run (2026-09-22, seventy-eighth batch, ALL FIVE REVIEWED AND MIRRORED -- batch closed)

**Closed at 599/599 reviewed over 42 pages.** 34 speaker corrections (5.7%),
no text corrections, all six of the pass's type corrections accepted, three
groups added by review. Every engine pair identical on group count, reviewed
count, `identified_by`, emphasis runs and the speaker / cap_colour /
confidence / type distributions. Corpus-wide corrections are down to one, in
vol 23, which predates this batch.

**24 speaker corrections over 327 groups (7.3%), counted by text. No groups
added, no text corrections, no cap-only changes, and all eight of the pass's own
type corrections survived.** By the confidence the pass wrote: **high 23 of 324
(7.1%), medium 1 of 3.** Batch total now 34 corrections over 540 groups (6.3%).

- **I READ A NAME IN A BALLOON AS THE SPEAKER'S OWN. IT IS THE PERSON BEING
  TALKED ABOUT.** Scrooge asks the boys if they can use a transit and they answer
  `DEWEY DOES!` / `HUEY DOES!` / `LOUIE DOES!`. I read each balloon as the boy
  identifying himself, called it the title's naming panel, and derived a
  title-wide colourist error from it. **Each boy is naming a BROTHER** -- that is
  the joke -- so the speaker of `DEWEY DOES!` is precisely the one duck it cannot
  be. After review the title pairs the caps the ordinary way in 18 of its 20
  capped groups (Dewey/blue 7, Louie/green 7, Huey/red 4), and the two
  off-convention rows are the naming panel itself. **There is no colourist error
  in *The Money Champ*, and the docs have been corrected.**
- **AND THAT ONE MISREADING IS THE ROOT OF MOST OF THE 24.** Having concluded
  red=Dewey and blue=Huey I applied it across 22 pages, so the corrections come
  back as a permutation rather than a scatter: `Huey -> Dewey` 5, `Dewey ->
  Louie` 3, `Dewey -> Huey` 2, `Louie -> Huey` 2, `Louie -> Dewey` 1. **A review
  whose name-to-name moves form a permutation is not fifteen separate misreadings
  -- it is one premise applied fifteen times.** Look for the premise first.
- **THE GENERAL RULE, WHICH IS NOT ABOUT COLOUR AT ALL: A NAME IN A BALLOON IS A
  VOCATIVE OR AN OBJECT, NEVER A SIGNATURE.** `UNCA SCROOGE` tells you who is
  being addressed. `DEWEY DOES!` tells you who is being discussed. Neither tells
  you who is speaking; only the tail does. This batch has both traps on the same
  title and I got the first right and the second exactly backwards.
- **THE ONE PLACE THE CONVENTION ACTUALLY EARNED ITS KEEP.** Three collectives
  became names off the cap alone -- 124 g2 `nephews -> Dewey` (blue), 124 g3
  `nephews -> Huey` (red), 125 g6 `nephews -> Louie` (green), plus 128 g18 and
  g19 `nephews -> Louie` (green). Five of the 24 are the review NAMING a boy I
  had declined to name, on caps I had measured and then not used because the
  panel was indoors. **The ink was in my own notes; I recorded it and did not
  cash it.** Under-naming is still the error class.
- **TWO ADULTS SWAPPED ON ONE PANEL, WHICH IS THE OTHER OLD ONE.** 129 g6 and g7
  came back `Donald -> Scrooge` and `Scrooge -> Donald` -- a clean transposition
  in a storm drain where both are drawn small and the only marks are a top hat
  and a blue cap. Adult-against-adult is as error-prone as boy-against-boy and it
  happens at high confidence.
- **I CALLED AN `other:` PAIR DRIFT AND IT IS A DISTINCTION. CORRECTED BY THE
  REVIEWER 2026-09-22.** 139 g2 is `other:the surveyors` while 138 g9 and 139 g6
  are `other:a surveyor`, and I flagged it for merging. It should not be merged:
  **139 g2 is several surveyors delivering the verdict together, and the other
  two are one man speaking.** Singular against plural is a real difference in who
  is talking, which is the one thing the speaker field exists to record. **A
  singular/plural pair in the `other:` list is a collective, not a near-duplicate
  -- check what the panel shows before proposing a merge.** The genuine drift to
  hunt for is two different WORDINGS for the same speaker, not two numbers of them.
- **THE MISSED-TEXT QUEUE WAS WRITTEN UNDER A NAME NOBODY WAS LOOKING FOR.** The
  skill tells the reviewer to expect `<out-dir>/queue-missed.txt`.
  `missed_text_queue.py` wrote only `queue-missed-<class>.txt`, and the hand-back
  named one of those, so the reviewer went looking for a file that had never been
  created. The findings were in the message and the work still reached them, but
  by a route the procedure does not describe. **Fixed at source on 2026-09-22**:
  the helper now also writes the combined `queue-missed.txt` the skill names, with
  the class after the kind field where the parser ignores it, and the per-class
  files stay for when the three jobs want separating. If a hand-back ever names a
  queue file, name the one the skill names.
- **THE STRAGGLER PATTERN CHANGED AGAIN -- AND THIS TIME IT IS A SIGN.** Both
  remaining stragglers are a `background` group with `speaker: none`:
  *Krankenstein Gyro* 180 g8 `DRUGS` and *The Money Champ* 139 g3 `CHAMP`. Neither
  carries a `type_was` or a `speaker_was`. In each title every OTHER sign was
  reviewed -- 8 of 9 and 47 of 48 -- so it is a plain off-by-one on the group that
  needs no decision, not a systematic skip. Three batches, three different
  straggler causes: retyped-then-agreed, stranded by a renumber, and now
  skipped-because-obvious. **Stop predicting which one it is and just run
  `--unreviewed` at close.**
- **WHAT THE PASS GOT RIGHT, FOR THE COST LINE.** *The Money Champ* ran 22 pages
  on 28 images (1.27 per page) and took 24 corrections; *The Wishing Well* ran 4
  pages on 5 images and took none. The difference is not the budget -- it is that
  one title had a five-duck cast with two look-alike adults and a premise I got
  wrong on page 11, and the other had Gyro on his own. **Cost per page is not the
  thing to tune; the number of live identity axes per panel is.**

### Findings to paste into the next run (2026-09-22, seventy-eighth batch, THREE OF FIVE REVIEWED AND MIRRORED)

**213 groups over 16 pages, 10 speaker corrections (4.7%), counted BY TEXT.**
Per title: *Pyramid Scheme* 4 of 69 (5.8%), *The Wishing Well* **0 of 49**,
*Return to Pizen Bluff* 6 of 95 (6.3%). All three mirrored clean -- both engines
identical on group count, reviewed count, `identified_by` and the speaker /
cap_colour / confidence / type distributions. *Krankenstein Gyro* and *The Money
Champ* are still in review and are held out of the commit.

**By the confidence the pass wrote:**

| | high | medium |
|---|---|---|
| *Pyramid Scheme* | 4 of 69 (5.8%) | -- (none written) |
| *The Wishing Well* | 0 of 49 | -- |
| *Return to Pizen Bluff* | 4 of 91 (4.4%) | **2 of 4 (50.0%)** |

Four mediums in the whole batch and half of them were wrong. That is the same
story as the last three batches and it is now unarguable: **medium is not a
hedge, it is a prediction that the call is wrong about half the time.**

- **COUNT THE REVIEW BY TEXT -- AND THIS TIME THE TOOL WAS WRONG BY THREE.**
  `review_findings.py --since 3a26738c` reported 9 speaker corrections on
  *Return to Pizen Bluff*; by text with markup stripped it is **6**. The review
  added two groups to 112 (the two `?` devices), every id after them shifted by
  two, and the tool -- which compares ids -- counted the two new groups as
  `unknown -> Donald` and `unknown -> nephews` corrections and mismapped a third.
  This is the second batch running where an add has corrupted the tool's count.
  **Diff by `ai_text` with `[b]`/`[i]` stripped, always, and treat the tool's
  number as an upper bound.**
- **AN ADD RENUMBERS THE PAGE AND STRANDS EVERY LATER QUEUE ENTRY -- IT HAPPENED
  HERE.** Both of *Pizen Bluff*'s stragglers are 112 g13 and g14, which are my
  old g11 and g12 after the +2 shift. They carry no `type_was` and no
  `speaker_was`: they are simply the two queue lines that pointed at ids which
  had moved by the time the reviewer reached them. **The missed-text adds must be
  worked BEFORE the speaker queue is generated, not before it is worked** -- the
  hand-back said the first and the queue was still built at apply time.
- **AND THE OTHER THREE STRAGGLERS ARE THE RETYPED-THEN-AGREED PATTERN AGAIN.**
  *Pyramid Scheme* 107 g8, g11 and g12 all carry `type_reviewed` with a
  `type_was` and no `speaker_was`. Third batch in a row, and the rule from the
  seventy-seventh holds exactly: expect one straggler per group that takes a type
  correction, and say what the keystroke is rather than asking for the review to
  be finished.
- **A QUOTED PASSAGE READ OFF A PAGE IS NOT AUTOMATICALLY SPEECH.** The review's
  own three type corrections are *Pyramid Scheme* 107 g8, g11 and g12, all
  `dialogue -> thought`: Scrooge reading the archeology book. I typed them
  dialogue because the quotation marks and the act of reading aloud say voice.
  They are thought clouds -- he is reading it to himself. **The clue was on the
  page and I walked past it:** 107 g10, four balloons away in the same run, was
  ALREADY stored `thought` from an earlier review. A run of balloons on one page
  where one is thought and three are dialogue is a run to re-read, not a mixed
  page. My own finding last time was "check the first and last balloon of a run";
  the correction is **check the whole run whenever one member disagrees with the
  others**, in both directions.
- **THE DECOY I DOCUMENTED BECAME THE ERROR. ALL THREE OF 115's REVERSALS ARE
  ONE MISTAKE.** I wrote into the palette that Donald wears the roster blue in
  *Return to Pizen Bluff* at 700-2,500px, larger than any nephew band -- and then
  read every blue cap in the title's last two panels as Donald. 115 g5, g6 and g7
  all came back `Donald -> Huey/Dewey`. Cropped at 4x after the review:
  - **115 p3**: my note says the tail touches "the blue cap of the standing
    figure at the centre of the car -- Donald, with his red bow tie visible
    below". At 4x that figure is **SCROOGE** -- black top hat with a blue band
    (`#00a5d5` ~1,300px at x352-464) over a **red coat** (~1,427px at x382-443),
    which is what I called a cap and a bow tie. The speaker is Huey.
  - **115 p4**: my note says "holds two figures only: Scrooge and the taller duck
    in the blue cap". At 4x the left figure is a **NEPHEW** -- small head, short
    beak, no bow tie, black cap with a blue band -- and he is **smaller** than
    Scrooge, not taller. Donald is not in the panel at all. The speaker is Dewey.
  **When a title puts the roster blue on an adult, blue stops being evidence and
  HEAD SCALE becomes the only discriminator.** I had the rule and stopped
  applying it the moment the rule itself gave me an answer I liked.
- **AND THE PANEL THAT COST THREE CORRECTIONS NEVER GOT AN IMAGE.** *Return to
  Pizen Bluff* took 12 images over 6 pages and **none of them was 115 p4**, which
  I read off the montage alone. One 4x crop -- the one I took after the review --
  settles it in a glance. The cheap titles in this batch were cheap because
  nothing was contested; this one was contested on the page I did not spend on.
  **Spend the image where the Donald-against-nephew axis is live, not where the
  cap ink is easy.**
- **TWO DIRECTIONS IN THE SAME SEQUENCE, WHICH IS THE SIGNATURE OF A BAD FRAME.**
  On 115 I put Donald where the boys were (g5, g6, g7) *and* the boys and Scrooge
  where Donald was (g0 `Scrooge -> Donald`, g4 `nephews -> Donald`). When a
  page's corrections run both ways, the error is not a slip on one tail -- it is
  that I had the cast of the scene wrong. **Name the figures in the panel before
  assigning any balloon, and if a page reverses in both directions at review,
  that is the panel to re-read first.**
- **WHAT CAME BACK CLEAN, AND WHY IT IS USEFUL.** *The Wishing Well*: 49 groups,
  0 corrections, on 5 images over 4 pages. Gyro alone for half the story, every
  balloon either a cloud with a bubble trail or a pointed tail, and a closed cast
  of four. The batch's cheapest title was also its most accurate -- cost and
  accuracy did not trade off here, because there was nothing to be uncertain
  about. All six of the pass's own type corrections survived review, including
  the hen's cluck on *Krankenstein Gyro* 181 g10 and both Glomgold clouds.
- **STILL OUTSTANDING AND NOT MINE TO CLOSE.** *Return to Pizen Bluff* 110's
  `NUGGET CAFE` -- the mirror-reversed cafe window lettering -- was not added and
  is not in `missed-text-ignore.txt`, so the audit still reports it. The two `?`
  devices on 112 were added and the audit is otherwise clean.

### Findings to paste into the next run (2026-09-22, seventy-eighth batch, NONE REVIEWED)

**Vol. 22, five titles, 42 pages, 596 groups: *Pyramid Scheme* (6pp, 69),
*The Wishing Well* (4pp, 49), *Return to Pizen Bluff* (6pp, 95),
*Krankenstein Gyro* (4pp, 51), *The Money Champ* (22pp, 332).** 68 images,
**1.62 per page**; per title 3.17 / 1.25 / 2.00 / 1.00 / 1.27. No text
corrections; 6 type corrections; 2 missed-text findings. Nothing here is
reviewed yet, so every rule below is the pass's own reading and not a verdict.

- **RUN THE NAME SCAN OVER THE ART, NOT ONLY OVER `name-grep`.** *The Money
  Champ* 128 panel 2 has the three boys answering in turn -- `DEWEY DOES!` /
  `HUEY DOES!` / `LOUIE DOES!` -- and `barks-ocr-name-grep` reported **none of
  the three**. Each name occurs once, so it misses the repeated-pair list, and
  all three are ordinary dictionary words, so they miss the non-dictionary list
  too. That is the name-grep blind spot in its purest form, and on this title it
  hid the naming panel for a 22-page story. **When a title has nephews and the
  grep comes back empty, that is not evidence of anything -- read the pages.**
- **AND I READ THE PANEL IT HID BACKWARDS. RETRACTED 2026-09-22 AFTER REVIEW.**
  I claimed each boy's balloon named HIMSELF, and therefore that red and blue were
  swapped for the whole title. **They are not. Each boy names a BROTHER** -- that
  is the gag -- so `DEWEY DOES!` is spoken by the boy who is not Dewey. After
  review the title pairs the caps the STANDARD way in 18 of its 20 capped groups
  (Dewey/blue 7, Louie/green 7, Huey/red 4), and the only two off-convention rows
  are the naming panel itself. **There is no colourist error in *The Money
  Champ*.** The wrong convention is the single root cause of most of that title's
  24 speaker corrections. The lesson is not about colour at all: **a balloon that
  contains a name tells you who is being TALKED ABOUT, and only the tail tells you
  who is talking.** I had that backwards for a 22-page title.
- **A TITLE CAN PRINT ITS CAP INK AN ORDER OF MAGNITUDE SMALLER THAN THE
  VOLUME'S.** *Pyramid Scheme* 104 p2 is the reference panel and its three inks
  measure **220px (green), 23px (red) and 27px (blue)** -- against 133-2,869px
  over the last three batches. `title_bands.py` reported that panel as
  `red=7 green=6 blue=15` blobs and printed none of the caps, because two of the
  three are **under capscan's 25px default floor**. A whole-title sweep at a
  **6px floor** found them in one call and cost no images. **Run the low-floor
  sweep before deciding a title has no readable caps**; the same sweep is what
  showed that the boys' caps in *Return to Pizen Bluff* run 100-400px while
  Donald's blue cap in that story runs 700-2,500.
- **DONALD WEARS A COLOURED CAP IN THREE OF THESE FIVE TITLES, AND IT IS THE
  ROSTER BLUE.** *Return to Pizen Bluff* (the whole modern half), *The Money
  Champ* and *Pyramid Scheme* (a blue tam) all put `#00a4d5` on Donald's head at
  500-2,500px -- bigger than any nephew band in those titles. Every blue call
  needed the head span as well as the ink. This is the `donald_wears_deweys_blue`
  trap arriving three titles in a row, so treat it as the Vol. 22 default rather
  than a surprise.
- **AND GLOMGOLD'S TAM IS THE NEPHEW GREEN.** `#009e47` at ~1,600px, in nearly
  every panel of *The Money Champ*. With the workmen's green overalls (118) and
  the managers' green robes (123-125) that is three separate green decoys in one
  title; the boys' green runs 400-800px.
- **SIX TYPE CORRECTIONS, FIVE OF THEM THE SAME DRAWING.** `dialogue -> thought`
  on *Return to Pizen Bluff* 110 g2 and *The Money Champ* 119 g0, 133 g12, 133
  g13 and 136 g12 -- every one a solo balloon with a **scalloped edge and a trail
  of separate bubbles**, sitting among neighbours already stored as `thought`.
  The engines get the cloud right most of the time and wrong on the first or last
  balloon of a run. **Where a character monologues across several panels, check
  the first and last balloon of the run, not a sample.** The sixth is the
  reverse: *Krankenstein Gyro* 181 g10, a hen's `CLUCK CLUCK` stored as
  `sound_effect` while the other seven clucks in the same title are `dialogue`.
- **TWO MISSED-TEXT FINDINGS, BOTH ON *RETURN TO PIZEN BLUFF*,** and both the
  kind the audit cannot find unless the capture is complete: `NUGGET CAFE`
  lettered MIRROR-REVERSED on a cafe window seen from inside (110 p7), and a
  drawn `?` over each of Donald and a nephew (112 p2, two instances, one row in
  the audit). `queue-missed-plain.txt` is written. The mirror-reversed sign is
  worth remembering: it reads as decoration until you turn it round.
- **A SIGNBOARD IN AN EXOTIC SETTING IS USUALLY NOT LETTERING.** Two signboards
  in *Return to Pizen Bluff* and one in *Pyramid Scheme* carry pseudo-Arabic
  squiggles, and the inscriptions all through *Pyramid Scheme* 108-109 are drawn
  hieroglyphs. Cropped at 4x they are not transcribable, so they stay out of
  `visible_text` -- but they have to be LOOKED at, because putting a guess in
  would have produced a phantom audit finding on every one.
- **`allbold` CAN BE DRIVEN PROGRAMMATICALLY AND SHOULD BE ON A LONG TITLE.**
  *The Money Champ*'s 173 emphasised groups were built by taking the measured
  word-matched (`=`) hits above 1.25, dropping any whose x-range touches the
  group's own `text_box` edge (those are the balloon outline, not lettering) and
  dropping the first word of a narration box (the drop capital). 43 hand anchors
  covered the `!` lines where the splitter disagreed with the text. Every result
  round-trips by construction. On a 332-group title that is minutes rather than
  an afternoon, and it does not eyeball anything.
- **A DROP CAPITAL MEASURES 1.5x-2.2x AND IS NEVER EMPHASIS.** `SO` 2.16,
  `BUT` 2.18, `MERE` 1.83, `AT` 1.72, `WHEN` 1.65 across this batch. Every one is
  the first word of a caption box. The guard is cheap and it is worth having in
  any scripted pass.
- `other:` values written by the pass, counted off disk, no near-duplicates:
  `a Duckburg citizen` (25 groups), `the Jivaro medicine man` (13), `a workman`,
  `a townsman` (3), `the ghosts` (2), `the judge` (3), `a surveyor` (3),
  `the oil field manager` (4), `the gold mine manager` (4), `Manager Coot` (5),
  `the cafe cook`,
  `the druggist` (2), `Cluckery Cluck` (8), `the turtle-shelled turkey duck`,
  `the lady customer` (5), `a rebel soldier` (3), `a rebel officer` (3),
  `Donald and the nephews` (1, the four-tail chorus on *Pyramid Scheme* 106 p8).
  The two rebel values are deliberately distinct (the men with epaulettes who
  hold Gyro's papers against the rank and file) and a reviewer who disagrees can
  merge them in one pass.
- **WHAT IS STILL OPEN.** Five groups at medium, all flagged for the queue and
  all the same shape -- a figure that could be Donald or a boy and no tail that
  separates them: *Return to Pizen Bluff* 112 g4 and g7 (the car and its
  occupants drawn at ~100px and in silhouette), 113 g6 (a night panel where both
  speakers are flat blue silhouettes), 115 g4; *The Money Champ* 119 g9 (a brawl
  drawn as four overlapping copies of the same two ducks), 123 g1 (off-panel with
  nobody drawn) and 130 g11 (the tail lands on a 40px figure whose body reads
  red, i.e. Scrooge, while the line -- the end of a sure thing -- is Glomgold's).
  That last one is a real art-against-dialogue conflict and is written up as one.

### Findings to paste into the next run (2026-09-22, seventy-seventh batch, ALL THREE REVIEWED AND MIRRORED -- batch closed)

**514 groups over 41 pages, 40 speaker corrections (7.8%), 32 of them in the
nephew domain.** Per title: *The Master Mover* 9 of 141 (6.4%), *Spring Fever*
6 of 107 (5.6%), *The Flying Dutchman* 25 of 257 (9.7%). 79 images, 1.93 per
page. All three mirrored clean at full review -- every engine pair identical on
groups, reviewed count, `identified_by`, emphasis runs and the speaker /
cap_colour / confidence / type distributions. Corpus-wide corrections are back
to the single one that predates the batch, vol 23 *The Librarian* 118 g19.

**By the confidence the pass wrote -- the clearest split yet recorded:**

| title | high | medium |
|---|---|---|
| *The Master Mover* | 5 of 136 (3.7%) | **4 of 5 (80.0%)** |
| *Spring Fever* | 5 of 104 (4.8%) | 1 of 3 (33.3%) |
| *The Flying Dutchman* | 16 of 228 (7.0%) | 9 of 29 (31.0%) |

Medium ran 6x to 22x worse than high in every title. 37 mediums across the
batch held 14 of the 40 corrections while being 7% of the groups.

- **COUNT A REVIEW BY TEXT, NOT BY ID -- `review_findings.py` DOES NOT.** The
  tool compares group ids, so the `ZIP` the review added to *The Flying
  Dutchman* 090 shifted every later id and it reported 27 speaker corrections
  and a phantom `thought -> dialogue` on 090 g18. Diffed by text with emphasis
  markup stripped, the true figures are 25 and none. Strip the markup too, or
  five of the review's own emphasis edits read as new groups. This is the
  group-ids-move-under-you rule applied to the tool that reports the review.
- **A STRAGGLER IS NOT A MISSED GROUP: IT IS A RETYPED GROUP WHOSE SPEAKER WAS
  AGREED WITH.** All 13 stragglers across the three titles were the same
  intersection -- `type_reviewed` set with a `type_was`, and no `speaker_was`.
  Changing a speaker stamps `speaker_reviewed` as a side effect; agreeing needs
  its own keystroke, and on a group that also wanted a type fix that is the
  keystroke that gets forgotten. `kivy_editor._confirm_speaker_as_is` says so in
  its own docstring. There is no `--confirm-all` for speakers. **Expect one
  straggler per group that takes a type correction, and say what the keystroke
  is rather than asking for the review to be finished -- it was finished.**
- **NEVER EDIT THE CAPTURE TO SILENCE THE MISSED-TEXT AUDIT. THREE TIMES IT WAS
  RIGHT.** The audit reported `ACE DIAMOND SHOP` / `JEWELS` / `GEMS` ungrouped on
  *The Master Mover* 078 and `DRAWBRIDGE` / `DANGER` on *Spring Fever* 105; the
  pass decided its own transcription was too granular and merged each into one
  `visible_text` entry. The review then split both signs into separate boxes,
  exactly as the audit had said. A third, *Spring Fever* 098's large red `RIP`,
  was never written into `visible_text` at all, so the audit could not see it and
  the reviewer found it by eye. **A sign painted on two boards is two pieces of
  lettering. If the audit and the capture disagree, crop the sign.**
- **DO NOT BUILD A DIALOGUE THREAD AND THEN SPEND IT.** The single most expensive
  error of the batch: Donald half-remembering the ship's name in *The Flying
  Dutchman* looked like a running gag, so the pass gave him 086 g9, 091 g8,
  091 g10 and 092 g1 -- the pay-off line included -- and cited the earlier calls
  as evidence for the later ones. All four are nephews. One narrative inference,
  four corrections, and no tail was traced for any of them.
- **AT 250px A WHITE DUCK HEAD IN A PORTHOLE IS DONALD BY DEFAULT, AND SCROOGE
  FOUR TIMES.** 085 g9, 086 g2, 086 g3 and 090 g14. The whiskers are the tell and
  at montage scale they merge into the cheek. Where a panel is one duck's head
  filling a porthole or a close-up, that is a 2x crop, not a montage read.
- **THE DECOY THE PASS NAMED, THE PASS THEN USED AS EVIDENCE.** *The Flying
  Dutchman* 095 g7/g8: the note says both boys' caps print the same red so
  neither can be named. They are red and blue, and the broad red band between
  them is the boat's RAIL -- identified as a rail decoy in three other panels'
  notes on the same title. A 500px-wide strip at neck height is never a cap band.
  This is the reverse of under-naming: a false absence-of-discrimination claim.
- **`dialogue -> thought`: 15 CORRECTIONS THE PASS DID NOT PROPOSE.** Nine on
  *Spring Fever*, six on *The Flying Dutchman*, on top of 20 adjudicated the same
  way in earlier rounds. *Spring Fever* closes at 25 `thought` against 54
  `dialogue`: Donald alone in that story thinks rather than speaks, `WAK!`
  included. The roster calls thought-vs-speech a DRAWING test, and the pass
  applied it only where the stored type was already `thought`, taking `dialogue`
  on trust everywhere else. **"Omit the field unless the stored type is wrong"
  is not "never check". On any solo balloon, read the outline.**
- **`allbold` HIDES EMPHASIS IN A SHORT, MOSTLY-BOLD GROUP.** The review added
  five runs the pass missed (*The Flying Dutchman* 083 g11 `GOLD BULLION!`,
  084 g12, 085 g3, 085 g7 `GOT`, 085 g9 `WAK!`), every one measured below 1.3.
  The ratio is against the group's own baseline, so when the emphasised words are
  most of the group they set that baseline and the ratio collapses toward 1.0.
  `WAK!` is the limit case: one word, wholly bold, nothing to compare against.
  **Any single-word group, and any group whose `base` runs high against its
  neighbours, needs an eye and not a ratio.**
- **WHAT THE PASS GOT RIGHT, FOR THE COST LINE.** *Spring Fever* at 1.50 images
  per page took 6 corrections; *The Flying Dutchman* at 1.71 took 25. The
  difference is not images, it is that a Scrooge story puts five ducks in a cabin
  and two of them are adults who look alike in a porthole. Where three boys share
  a panel the pass was strong -- 092 p4 and 093 p1 named six between them and the
  review reversed none of the six.
- `other:` values surviving review, none near-duplicate: `the mynah bird` 29,
  `the game warden` 15, `the naturalist` 8, `a naval officer` 7, `the mountain
  goat` 5, `an eagle` 5, `the moving customer` 4, `the ape` 4, `the diamond
  dealer` 3, and singletons for `the bear`, `a new customer`, `the newsboy`. The
  review removed `other:the drawbridge operator` (*Spring Fever* 105 g0 is
  Donald) and moved *The Master Mover* 081 g14 and 083 g3 between the goat and
  the mynah.
- **A REVIEW THAT MOVES A SPEAKER OFF A NEPHEW LEAVES THE `cap_colour` BEHIND,
  AND NOTHING LOOKS FOR IT.** Two here -- *The Master Mover* 083 g0
  (`other:the mynah bird`, cap `blue`) and *The Flying Dutchman* 083 g4 (`Donald`,
  cap `blue`) -- and a corpus sweep on 2026-09-22 found six in all, back to Vol. 11
  (cleared in prelim `5f01924b`). **`cap_mismatch.py` cannot see them**: it opens
  with `if speaker not in STD or not cap: continue`, so a colour on Donald or on a
  rabbit is skipped rather than reported. The damage is quiet -- stale evidence on
  a reviewed group, invisible to the one query that would care -- so it has to be
  swept for deliberately. The sweep is `cap_colour` set on a speaker not in
  {Huey, Dewey, Louie}, and it returns 92 rows of which only six are wrong: 70 are
  a `nephews` collective recording the ink it can see, and the rest are Donald in
  his own blue or a collective that names the boy whose colour it carries. **Read
  each group's `vision_note` before nulling anything** -- in all six real cases the
  note already put the band on a different figure.

### Findings to paste into the next run (2026-09-21, seventy-seventh batch, NONE REVIEWED)

**509 groups over 41 pages, 79 images, 1.93 per page.** *The Master Mover*
(Vol. 21, 10pp, 144 groups, 2.80/page), *Spring Fever* (Vol. 21, 10pp, 108
groups, 1.50/page), *The Flying Dutchman* (Vol. 22, 21pp, 257 groups,
1.71/page). Nine type corrections, no text corrections, and no missed text in
any of the three -- the audit came back `grouped by NEITHER engine: 0` on all
of them. Confidence written: 5 / 3 / 29 at low-or-medium against 144 / 108 /
257 total, so the medium-against-high split will be worth reading off
`review_findings.py --since 378c4ef4` (Vol. 21) and `--since 4c50585d` (Vol. 22).

- **THE FIRST PANEL IS WORTH FIVE IMAGES AND THE REST OF THE TITLE IS WORTH
  TWO.** *The Master Mover* cost 2.80 per page because 077 alone took five --
  montage, head row, two tail crops and the whole panel -- to fix that the
  construction is a quartered black beanie and that red sits at x1318-1393 on
  the LEFT boy. Everything after it ran at 2.3. *Spring Fever* cost 1.50
  because one 2.6x crop of 099 p6 did the same job in one image. **Hunt the
  reference panel with `title_bands` and `crowns.py` BEFORE opening anything**:
  in *Spring Fever* the panel that carried all three inks (099 p6, red 590px /
  green 1,080px / blue 123px) was findable from the census alone.
- **A CLOSE-UP NEPHEW CAP REACHES 2,500px, SO AREA ALONE WOULD HAVE CALLED IT
  DONALD.** *The Master Mover* 083 p1: the duck holding the prunes carries
  1,844+684px of `#00a4d6`, above the 43-1,200px the Vol. 21 palette note gives
  a boy and inside Donald's 1,400-6,800px. It is a NEPHEW -- the test that works
  is the CONSTRUCTION (a quartered beanie, two blobs on one crown) against
  Donald's single rounded sailor cap. Area is a per-distance figure, not a
  per-character one.
- **THE SAME RED ON TWO CROWNS NAMES NEITHER, AND THAT IS A FINDING AND NOT A
  FAILURE.** *The Flying Dutchman* 095 p8 puts a red band on both boys at the
  rail. The roster's rule -- two nephews printed the same colour tell you
  nothing about either -- is the whole answer, and writing `nephews` twice there
  took one scan rather than a crop.
- **A RED HORIZONTAL STRIP AT NECK HEIGHT IS THE BOAT'S RAIL.** Three panels of
  *The Flying Dutchman* (095 p8, 097 p6, 098 p7) hang 1,600-3,700px of `#e61b1f`
  on a head that `crowns.py` then reports as CAP-INK, because the rail runs
  across the panel just above the skulls. Check the blob's SHAPE: a cap band is
  20-40px tall and 30-120px wide, a rail is 20px tall and 500px wide.
- **"UNCA SCROOGE" NAMES A NEPHEW; "UNCLE SCROOGE" NAMES NOBODY.** Over the
  whole of *The Flying Dutchman* every traced `UNCA SCROOGE` is a boy, and
  Donald says `UNCLE SCROOGE` at 089 g0, 093 g11, 094 g2 and 095 g1 -- but a
  nephew says UNCLE too at 089 g8, which is traced to a 180px blue band. So the
  address is a one-way test: it rules Scrooge and usually Donald out, and it
  never rules a nephew in. It carried eight otherwise-unplaceable balloons on
  far-wides and silhouettes.
- **A SCROOGE STORY PUTS THE IMAGES WHERE THREE BOYS SHARE A PANEL.** 21 pages
  at 1.71 because most panels are two adults, either of whom is identifiable at
  montage scale from the coat, the whiskers and the top hat. Two panels earned
  six names between them: 092 p4 (three balloons, three boys, three tails each
  landing 5-25px LEFT of its own boy in step -- the offset is what makes the set
  readable rather than a guess from reading order) and 093 p1 (a red boy, a
  green boy, and a third drawn with both hands cupped round his beak, which is
  the identification for the shouted balloon).
- **AN ANIMAL'S VOICE IS `dialogue`, AND SEVEN OF THE NINE TYPE CORRECTIONS ARE
  THAT.** *The Master Mover* stores the bear's `RAR!`, the goat's three `BAA`
  groups and two eagle `GRAAK`s as `sound_effect` while storing the identical
  goat bleat at 081 g14 and the identical eagle cry at 085 g3/g6 as `dialogue`.
  The mynah's `CHOMP! CHOMP!` stays `sound_effect` with the bird named -- chewing
  is made by the animal but not by its voice. The other two corrections are
  story logos stored as `background` and `narration` and moved to `title`.
- **A RECURRING ADULT IS A HAT INK, AND CHECKING IT REVERSED SIX SPEAKERS.** The
  naturalist of *The Master Mover* wears `#c35349` H4.9 S0.63 in a wide brim;
  the customer of 077-078 wears `#c32328` H358 S0.82 in a small skullcap and is
  bald and moustached where the other is bearded. They read as the same man at
  montage scale and are not. One stacked image of three heads settled it.
- **ROLE REASONING LOST TWICE MORE.** *The Master Mover* 082 g0 (`HEY! THE GOAT
  IS GETTING STUBBORN!`, with Donald wrestling the goat two feet away) traces to
  a watching boy, and *The Flying Dutchman* 082 g3 (`COME AND GO FISHING WITH
  US, UNCLE SCROOGE!`, with three boys in the same panel) traces to Donald. In
  both the tail was a three-second check and the plausible reading was wrong.
- `other:` values across the three titles, counted off the corpus and none
  near-duplicate: `the mynah bird` 28, `the game warden` 15, `the naturalist` 8,
  `a naval officer` 7, `the mountain goat` 5, `an eagle` 5, `the moving customer`
  4, `the ape` 4, `the diamond dealer` 3, `the bear` 1, `a new customer` 1, `the
  drawbridge operator` 1, `the newsboy` 1. The one pair worth a second look is
  *The Master Mover*'s `the moving customer` (bald, moustached, red skullcap,
  077-078) against `a new customer` (ginger-haired, hatless, 086 p7) -- drawn
  differently, but they play the same part at the two ends of the story.
- **HANDED BACK:** nothing missed, nothing textual. Nine type corrections sit in
  the three `queue-corrections.txt` files (14 / 2 / 2 entries, two engines each),
  and they are the only outstanding items in the batch.

### Findings to paste into the next run (2026-09-21, seventy-sixth batch, ALL THREE REVIEWED AND MIRRORED -- batch closed)

**538 groups over 40 pages, 17 speaker corrections (3.2%), 13 of them in the
nephew domain (12.7% of 102).** Per title: *Christmas in Duckburg* 5 of 287
(1.7%), *The Beachcombers' Picnic* 5 of 120 (4.2%), *Rocket-Roasted Christmas
Turkey* 7 of 131 (5.3%). 96 images, 2.40 per page. **By the confidence the pass
wrote: high 10 of 508 (2.0%), medium 6 of 29 (20.7%) -- a 10x split**, and the
29 mediums held more than a third of the errors while being 5% of the groups.
All six type corrections confirmed, none reversed. Both groups the pass added
came back unchanged; the review added one of its own.

- **THE ADULT/BOY BOUNDARY IS THE ERROR SITE OF THE WHOLE BATCH -- 8 OF THE 17
  -- AND WHICH WAY IT FAILS IS DECIDED BY THE PANEL, NOT BY THE PASS.** In
  ordinary panels the pass put DONALD where a boy was (*Beachcombers'* 071 g3,
  074 g5, 074 g7). In wide shots and flat silhouettes it put a BOY where Donald
  was (*Christmas in Duckburg* 020 g2 and 021 g1, *Rocket-Roasted* 096 g9 --
  three for three, every silhouette or far-wide panel in the batch). **Rule:
  when a panel is silhouetted or the figures are under ~40px, place the ADULT
  first -- he is the largest shape -- and assign the remainder. When the panel
  is drawn normally, do not let an adult's habitual prop stand in for a
  measurement.**
- **AND THE SINGLE MOST EXPENSIVE MISREAD WAS A RED BLOB AT THE WRONG HEIGHT.**
  *Beachcombers'* 074 panel 3 seats Dewey, Huey, Louie, then DONALD ASTERN. The
  red at **x505-551 y297-356** sits ABOVE the white skulls -- it is Huey's cap.
  The pass read it as Donald's bow tie, which moved Donald into the middle of
  the kayak and cost all three of that page's corrections. **Donald's tie sits
  BELOW his skull; a red patch above one is a cap. Check the y before calling
  red a tie.**
- **A `text_ok: true` THE PASS NEVER CHECKED, AND THE ENGINE DIFF COULD NOT
  CATCH IT.** *Rocket-Roasted* 090 g12 is the car's FRONT number plate reading
  `313`. Both engines had grouped it as `RR-RR`, the pass marked `text_ok` true
  without cropping it, and the reviewer corrected the text. **Two engines
  agreeing is not a check** -- they share the same Gemini labelling, so the
  engine diff reported clean precisely because both were wrong the same way.
  The only thing that would have caught it is a crop, and it was a 62x44px box
  in a panel already being read.
- **LISTING A REPEATED SIGN ONCE MAKES ITS DUPLICATES INVISIBLE TO THE AUDIT,
  AND IT COST A REVIEWER-SIDE ADD.** The `313` plate appears three times on
  *Rocket-Roasted* 090 and the capture listed it once, so the audit counted one
  against one and reported clean. The reviewer added the second instance (090
  g15, panel 6) by hand. The roster already says *list a repeated sign once per
  instance*; this is what ignoring it looks like from the other end.
- **TWO NEAR-IDENTICAL UNIFORMED HUMANS NEED A NAMED RANK, NOT A FEATURE.** The
  pass built a general/major discriminator from one panel -- older, moustache,
  gold braid -- and applied it across *Rocket-Roasted*; 093 g5 and 094 g3 both
  went to the major. The only call that stood on its own was 093 g6, anchored by
  the speaker naming his listener (`TRY IT, MAJOR!`). **Where two officers wear
  the same uniform, the dialogue that names a rank is the only anchor; every
  other panel is a medium at best.** Same class as a per-character costume key,
  which the corpus already knows does not travel.
- **THE TWO-TAIL CHORUS RULE HELD 4 TIMES IN 5.** Five balloons across the batch
  carried two points on the bottom edge and were recorded as choruses;
  *Beachcombers'* 076 g3, *Christmas in Duckburg* 016 g2 and 020 g3 and
  *Rocket-Roasted* 090 g8 all stood, and only 089 g8 was named (`nephews ->
  Dewey`), its second point sitting at the very edge of the balloon. **Count the
  points, but satisfy yourself each one is a drawn TAIL and not a notch in the
  outline** -- a false second tail turns a name into a collective.
- **SMALL NUMBERS STAYED WRONG, AND THE PASS'S OWN MEDIUMS FOUND THEM.**
  *Rocket-Roasted* 091 g1 was named Louie off **84px** of green at x883-896 and
  is Dewey; *Christmas in Duckburg* 017 g9 was a 33px gap tip. Both were written
  medium and both were corrected. **Under about 100px on a crown, or a tip in a
  gap narrower than a head, write medium and expect to be wrong about one time
  in five.**
- **THE VOL. 21 PALETTE IS NOW SETTLED OVER SEVEN TITLES.** Red `#e51a1f`-`#e8181f`
  H358-359, blue `#00a5d5`-`#01a5d7` H193-194, and a green that runs **H111-124
  as often as H146-149** -- Louie is `#4ca33e` H111 in *Christmas in Duckburg*
  and `#009e46` H146 in the other two. No correction in this batch reversed a
  hue call. The decoys are the ones to carry forward: **the Christmas tree at
  `#009e49` H148 in 15,000-49,000px blocks, blue mittens on every duck in the
  northern scenes, Donald's orange winter cap, and his bow tie.**
- **CONSTRUCTION IS STILL PER TITLE, NOW OVER SEVEN.** A thin coloured RIM
  (*Noble Porpoises*), a QUARTERED beanie (*Tracking Sandy*, *Chicken Thief*,
  *Christmas in Duckburg*), a coloured FRONT PATCH (*Beachcombers'*), a knitted
  winter cap (*Christmas in Duckburg*'s Canadian half), and nothing at all
  (*Dramatic Donald*, and both Christmas stories indoors). **Derive it from the
  title's own reference panel every time; six titles in, carrying one over has
  never once been safe.**
- `other:` values surviving review, none near-duplicate: `a Beagle Boy` 30,
  `Ollie Eiderduck` 27, `the general` 13, `the major` 8, `the Duckburg crowd` 6,
  `the logging foreman` 5, `an army officer` 4, `the picnic announcer` 2, `the
  party crowd` 2, `a telegraph clerk` 2, `a senator` 2, and singletons for `a
  beachcomber in a blue hat`, `a beachcomber in a top hat`, `a beachcomber in a
  white shirt`, `the train engineer`, `a telegram messenger`, `a crane workman`,
  `a Mountie`, `a judge`, `the crane operator`, `a sentry`.
- **NOTHING OUTSTANDING.** All three titles close on every group reviewed on
  both engines -- *Beachcombers'* 120/120, *Christmas in Duckburg* 287/287,
  *Rocket-Roasted* 131/131 -- with every close-out check clean. The two items
  the pass handed back were both worked: 090 g13 (`AND AWAY I GO!`) was ticked
  and mirrored, and **090 g12's type went to `background`** once its text was
  corrected from `RR-RR` to `313`, which is the type the other two plates on
  that page already carried. Corpus-wide corrections are down to the single one
  that predates this batch, vol 23 *The Librarian* 118 g19.

### Findings to paste into the next run (2026-09-21, seventy-sixth batch, *Christmas in Duckburg* REVIEWED AND MIRRORED -- 286/287)

**5 speaker corrections out of 287 groups (1.7%), all five in the nephew domain
(10.6% of 47)** -- the lowest rate of the batch and of the last several. By the
confidence the pass wrote: **high 2 of 268 (0.7%), medium 3 of 19 (15.8%) -- a
23x split**, the widest yet recorded. All four type corrections confirmed, none
reversed; the group the pass added (020 g7, the `?` over the blue-capped boy)
came back unchanged.

- **THE MEDIUM FLAG EARNED ITS KEEP AT 23x, AND THREE OF THE FIVE CORRECTIONS
  WERE MEDIUMS THE PASS HAD ALREADY DOUBTED.** 19 mediums out of 287 and they
  held three of the five errors. This is what the field is for: where the panel
  was small, flat or gap-tipped, the pass said so, and that is exactly where the
  reviewer went. **Keep writing medium on a tip in a gap and on any figure under
  ~40px; do not round it up to high to look decisive.**
- **THE GAP-TIP-GOES-ONE-HEAD-LEFT RULE LOST TO THE DRAWING -- AND THE PASS'S
  OWN NOTE NAMED THE WINNER.** 017 g9 `Louie -> Huey`. The tip measured at panel
  (704,497), in the 33px gap between the green cap (x674-691) and the red
  (x724-734); the pass took green on the Vols. 10/14 gap rule and wrote *"the
  red-capped boy, drawn mid-leap to the right, is the alternative a reviewer
  should weigh"* into the note. The reviewer took red. Two things pointed that
  way and were not weighed: **the tail's own direction was down-RIGHT**, and the
  red boy is the one drawn leaping off to fetch the very tape line the line is
  about. **Where the gap rule and the drawing disagree, follow the drawing** --
  and the gap rule is a tie-breaker for when nothing else speaks, not an
  override.
- **BLUE MITTENS ARE UNIVERSAL IN THE NORTHERN SCENES, SO A BLUE BLOB BESIDE A
  HAND IDENTIFIES NOBODY.** 015 g9 `Dewey -> Huey`. The pass named the
  blue-capped boy because he was *"the one pointing a blue mitten at the camp"*
  -- but every duck in the Canadian half wears the same `#00a5d5` mittens,
  Donald included, and the figure actually pointing was the RED-capped one.
  **Only ink sitting on a crown is a cap read**; the mitten, like Donald's bow
  tie, is furniture in the same band.
- **TWO OF THE FIVE PUT A NEPHEW WHERE DONALD WAS, AND BOTH ARE
  LOW-RESOLUTION PANELS.** 020 g2 `Louie -> Donald` (a ~25px cluster in the wide
  shot down the logging road, where the tails stop 110px short of the heads over
  cream snow) and 021 g1 `nephews -> Donald` (a flat black silhouette night
  panel where size is the only cue). Set against *The Beachcombers' Picnic*,
  where three corrections ran the other way, **the adult/boy boundary is where
  this whole batch's errors live, and it fails in BOTH directions the moment the
  panel goes small or flat.** In a wide shot or a silhouette, count the figures
  and place the adult FIRST, then assign what is left.
- **A BALLOON'S X-SPAN IS STILL NOT A TAIL.** 022 g1 `Donald -> Dewey`. Both
  balloons on that panel sit at x335-908, well right of the two boys at x60-268,
  so the pass gave both to Donald without measuring either tail. The first is
  Dewey's. **Where two balloons sit over one figure, that is a reason to crop,
  not a reason to assign both.**
- **THE H111-113 CAP GREEN HELD.** Two corrections removed a green
  `cap_colour`, but neither was about the hue -- both were placement errors, and
  no correction anywhere reversed the palette. Reading Louie's cap at
  `#4ca33e` H111-113 while `#009e49` H148 is the Christmas tree was right, and
  it is now confirmed twice in Vol. 21.
- **THE REVIEWER REFINED SIX PADDLEOCR TEXTS AND THE MIRROR PRESERVED ALL SIX.**
  Line-break fixes on 011, 014 and 022 and one real content fix -- 018 g10
  `TELEGRAPH CABLE` -> `TELEGRAPH & CABLE`. Because markup is written INTO
  `ai_text`, a mirror can clobber exactly this kind of edit, so it was snapshotted
  before `--write` and diffed after. **Do that check every time a review has
  touched the other engine's text.**
- **ONE STRAGGLER: 018 g11**, the `WIRE HOME TODAY` poster -- `background`,
  speaker `none`, high, unchanged by the pass, never ticked on EITHER engine.
  `queue-straggler.txt` holds the easyocr line; ticking it and re-running
  `vision-mirror --write` closes the title at 287/287.

### Findings to paste into the next run (2026-09-21, seventy-sixth batch, *The Beachcombers' Picnic* REVIEWED AND MIRRORED -- 120/120)

**5 speaker corrections out of 120 groups (4.2%), 4 of them in the nephew
domain (12.1% of 33).** By the confidence the pass wrote: **high 4 of 115
(3.5%), medium 1 of 5 (20.0%)** -- the split points the right way on a small
sample. Mirror clean on every axis; no text or type corrections; the review
added no groups and made exactly one paddleocr edit, a text_box nudge on 076
g11 (`WINK`).

- **THE ERROR CLASS HERE IS THE OPPOSITE OF THE LAST TWO BATCHES: THIS PASS
  OVER-NAMED DONALD.** Three of the five are `Donald ->` something (071 g3 and
  074 g7 to `nephews`, 074 g5 to `Dewey`) against one collective sharpened to a
  name. Declining was not the problem on this title; putting the adult in a
  seat he was not in was.
- **AND ALL THREE OF 074'S CORRECTIONS COME FROM ONE MISREAD BLOB. A RED PATCH
  ABOVE THE WHITE SKULL IS A CAP; DONALD'S BOW TIE SITS BELOW HIS. CHECK THE
  Y.** 074 panel 3 puts four ducks in a kayak -- blue, red, green caps and then
  DONALD ASTERN. capwide gives red 237+178+159px `#e71a20` at **x505-551
  y297-356** and blue 728px `#00a6d5` at x673-709. The red is at CAP height,
  above the white heads; it is Huey's cap. The pass read it as Donald's bow tie,
  which moved Donald from the stern into the middle of the boat and shifted
  every speaker on the page. The rule is already in the notes as *ink above the
  white skull is the cap* -- it just was not applied to a RED blob, because red
  on Donald is habitually the tie.
- **IN A BOAT IN THIS TITLE DONALD SITS AT THE STERN, BEHIND ALL THREE BOYS**
  (074 p1 and p3 both). So the rightmost duck is the adult and the cap-coloured
  head next to him is a boy, not him. Where a panel seats a row of ducks, count
  from the far end before assigning.
- **"MEN!" DOES NOT MAKE THE SPEAKER AN ADULT.** 074 g7 `TO THE RESCUE, MEN!`
  was given to Donald on exactly that reasoning -- the line addresses the
  nephews, so the speaker must be the one in charge -- and went to `nephews`.
  This is the seventy-fifth batch's explaining-adult default wearing a
  different hat: **a form of address tells you who is being spoken TO and
  nothing about who is speaking.**
- **A CHARACTER IN FRAME BEATS AN OFF-PANEL CONTINUATION.** 067 g8 continues the
  picnic announcer's run of rules from panels 2 and 3 word for word, and panel 4
  draws only Daisy and Donald, so the pass made it off-panel. The review gave it
  to **Daisy**. Where a line could be an off-panel voice continuing or a drawn
  character starting, take the drawn one; the pass's own note already recorded
  that no tail placed it, which is the tell.
- **THE ONE COLLECTIVE THE REVIEW NAMED WAS NAMED WITH NO INK TO MEASURE.** 074
  g10 went `nephews -> Dewey`/blue on the full-page splash, where capwide over
  the whole kayak region (x950-1400, y200-800) at a **3px floor** returns no
  red, green or blue blob at all -- the only chromatic thing there is the sea at
  `#39b18d` H162 S0.68. Dewey had just been named two panels earlier in the same
  boat, so this is **scene continuity overriding a measured zero**. A clean 0
  blobs closes the question about the INK, not about the BOY: if the same boy
  was placed a panel or two before and the scene has not changed, carry him.
- Nothing outstanding: 120/120 reviewed on both engines, corrections sweep clean
  for this title, missed-text audit clean, engine diff clean.

### Findings to paste into the next run (2026-09-21, seventy-sixth batch, NONE REVIEWED)

*The Beachcombers' Picnic* (21, 10pp), *Christmas in Duckburg* (21, 20pp) and
*Rocket-Roasted Christmas Turkey* (21, 10pp). **537 groups on both engines
across 40 pages, 96 images, 2.40 per page** (3.50 / 2.10 / 1.90). 2 groups
added for ungrouped lettering, 5 type corrections proposed, no text
corrections, and the missed-text audit clean on all three.

- **THE ROSTER GREEN IS THE DECOY IN *CHRISTMAS IN DUCKBURG*, AND THE CAP GREEN
  IS THE ONE THAT LOOKS WRONG.** Louie's cap there is `#4ca33e`/`#4da33f`
  **H111-113 S0.62-0.69**, and `#009e46`-`#009e49` **H146-149 S1.00** -- which
  is the roster green everywhere else in this volume -- is the CHRISTMAS TREE,
  in 15,000-49,000px blocks in nearly every panel. Reading it the usual way
  round would have put a tree on every crown in the story. *Noble Porpoises*
  had already put Louie at H112 in the seventy-fifth batch, so **Vol. 21's
  green runs H111-124 as often as H146**; rank the crown against the panel, not
  against a remembered hue.
- **ALL THREE TITLES TAKE THE CAPS OFF INDOORS, AND ALL THREE PUT THEM BACK ON
  TO GO OUT.** *Christmas in Duckburg* 008 and 009 p1-p4 are bare-headed at the
  tree; 009 p5, the panel where the boys leave to tell their friends, is the
  first cap read in the story. *Rocket-Roasted* is bare-headed at the tree
  (087-088) and at the dinner table (096) and capped in the garage and yard
  (089 p6 onward). **A bare-headed sentence was written into 087-088's notes as
  "throughout this story" and had to be narrowed after 089 showed all three
  inks at once** -- the per-panel rule caught it, but only because the next
  page was scanned before the close-out.
- **TWO TAILS ON ONE BALLOON CAME UP FIVE TIMES IN FORTY PAGES**, and every one
  is a chorus rather than a name: *Beachcombers'* 076 g3, *Christmas in
  Duckburg* 016 g2 and 020 g3, *Rocket-Roasted* 089 g8 and 090 g8. The tell is
  a balloon whose bottom edge carries two separate points; at page scale they
  read as one wide tail. **Count the points on the edge before measuring a
  tip** -- on 089 g8 the two tips fell on two different boys 88px apart, and
  either one alone would have produced a confident wrong name.
- **`cap-colour` IN `identified_by` IS FOR NEPHEWS ONLY, AND 23 GROUPS WERE
  REFUSED FOR IT.** Donald's cap identifies him in most of these panels, and
  claiming `cap-colour` with `cap_colour` null aborts the apply with
  "identified_by claims cap-colour but cap_colour is null" on every such group.
  The roster's field for an adult's headgear is **`hat`**. Cheap to fix, but it
  is 23 lines of validation output after all the reading is done.
- **AN ADDED GROUP RENUMBERS THE PAGE AND KILLS THE STORED result.json.**
  *Christmas in Duckburg* 020's `?` landed at g7 and pushed the old g7-g12 to
  g8-g13 in the corpus, while the out-dir's `groups.json` still holds the
  pre-add ids. Two pages then needed a capture fix, and a blanket re-apply
  would have written 020's annotations onto the wrong six groups. **After an
  add, re-apply page by page or not at all** -- the fix was to move the other
  eighteen `result.json` aside and run the two.
- **THE AUDIT'S "NEARLY A GROUPED TEXT" ROW EARNED ITS KEEP.** It caught the
  burnt telegram on *Christmas in Duckburg* 019 read into `visible_text` as
  `TO NEED DUCKBURG` where the stored group says `WEED`; at 4x the W survives
  the burn and the GROUP is right. **The capture was the wrong one, not the
  group** -- which is the third of the three classes and the one easiest to act
  on backwards. Its other two rows were mine too: `SPUT`/`SZZT` and
  `HONK`/`HONK` listed as separate `visible_text` entries where one group holds
  both words. **List a multi-word sound effect the way the group holds it.**
- **THE NAME-GREP MISSED EVERY NEPHEW NAME AGAIN -- AND THE ONE THAT MATTERED
  RULES A BOY OUT RATHER THAN IN.** `barks-ocr-name-grep` reported zero on all
  three titles; a hand grep of stored `ai_text` for `HUEY|DEWEY|LOUIE` found
  *Rocket-Roasted* 087 g10, `GRANDMA GAVE DEWEY A CHEMISTRY SET!`. Third
  person, so the SPEAKER is not Dewey -- which narrows three candidates to two
  and still leaves a collective. **Run the grep at prep every time; it costs
  one command.** Its two other hits were Gemini boilerplate (`Spoken by Huey,
  Dewey, or Louie.` in a `notes` field), so grep `ai_text`, not the file.
- **QUOTED FRAMING CAPTIONS: the seventy-fifth batch's ruling held, and there
  was no plain one to test it against.** Seven caption boxes across the two
  Christmas stories are the narrator's under it. Two of them -- *Rocket-Roasted*
  089 g5 and 093 g8 -- carry printed quote marks the stored text omits, which
  is quote style and not a word-level correction, so they were noted rather
  than corrected. 089 g5 is also a **pink caption box stored as `dialogue`**,
  the one type correction on that title.
- **DONALD'S DISCRIMINATOR CHANGES MID-TITLE IN *CHRISTMAS IN DUCKBURG*.** In
  Duckburg he wears the roster blue as a sailor cap, so the shape test applies;
  in the northern half he wears a **non-roster ORANGE winter cap** and is the
  only figure in the panel carrying no roster ink at all. That inverts the
  usual trap -- there, a blue crown is a BOY.
- **NAMED AGAINST COLLECTIVE: 54 of 101 nephew groups named (53%).** By title
  22/30 (73%), 22/48 (45%), 10/23 (43%). The collectives are nearly all forced
  rather than declined: bare heads indoors, whole panels in flat silhouette
  (*Christmas in Duckburg* 021 p1-p5, *Rocket-Roasted* 091 p5 and 096 p8), and
  wide shots where the boys are 25px across and capwide returns 0 blobs at a
  5px floor. Where a cap was drawn at all, it was read.
- **IMAGE BUDGET: 2.40 per page over the batch, but three pages went over the
  ceiling** -- *Beachcombers'* 071 at 8, *Christmas in Duckburg* 017 and 020 at
  6. All three were the same shape: a page with four or more nephew balloons
  whose tails land in gaps between heads, so each name cost its own crop. The
  two cheap titles (1.90 and 2.10) were cheap because their casts are adults.
- `other:` values, none near-duplicate. *Beachcombers'*: `the picnic
  announcer`, `a beachcomber in a blue hat`, `a beachcomber in a top hat`, `a
  beachcomber in a white shirt`. *Christmas in Duckburg*: `Ollie Eiderduck`,
  `a Beagle Boy`, `the Duckburg crowd`, `the party crowd`, `the logging
  foreman`, `the train engineer`, `a telegraph clerk`, `a telegram messenger`,
  `a crane workman`, `a Mountie`, `a judge`, `the crane operator`.
  *Rocket-Roasted*: `the general`, `the major`, `an army officer`, `a senator`,
  `a sentry`. **`the Duckburg crowd` and `the party crowd` are deliberately
  distinct** -- the first is the present-day town square, the second the
  flashback banquet.
- **OUTSTANDING AT CLOSE:** the 10 type corrections (5 groups x 2 engines) are
  in `queue-corrections.txt` for the two Christmas titles and are the only
  thing the corrections sweep reports for Vol. 21. A corpus-wide run returns
  11, the eleventh being vol 23 *The Librarian* 118 g19, which predates this
  batch. Speaker queues: 5 / 19 / 5 low-and-medium, 120 / 287 / 130 full.
  **Session cost census: 800 API calls at 413K average context.**

### Findings to paste into the next run (2026-09-21, seventy-fifth batch, ALL FOUR REVIEWED AND MIRRORED -- batch closed)

**468 groups over 36 pages; 91 speaker corrections (19.4%), 87 of them in the
nephew domain -- 51.8% of 168.** Per title: *The Magic Ink* 1 of 79 (1.3%),
*Noble Porpoises* 10 of 118 (8.5%), *The Littlest Chicken Thief* 32 of 132
(24.2%), *Tracking Sandy* 48 of 139 (34.5%). 79 images, 2.19 per page.

- **AND THE COST TELLS YOU NOTHING.** 3.40 images a page bought 8.5%; 2.00
  bought 34.5%; 1.67 bought 1.3%; 1.50 bought 24.2%. **There is no relation at
  all between what a title cost and how wrong it was in this batch.** Do not
  respond to these numbers by looking harder.
- **THE ONE TOOL BUG, AND IT IS REAL: `vision_prep` WRITES PANEL CROPS AS
  256-COLOUR PNGs AND THE QUANTISER DELETES SMALL ROSTER INKS.**
  `_save_quantized` calls `Image.quantize(colors=256)`, whose default MEDIANCUT
  allocates palette entries by pixel volume -- so a 233px cap segment in a
  655,000px panel is folded into its nearest neighbour. Measured on *Tracking
  Sandy* 048 panel 8: the restored source carries **green 279px H148.9, blue
  233px H193.5 and red 269px H358.3** on the three crowns; the prepped crop
  carries **green 371px and nothing else** -- the blue and the red are gone, and
  both outer crowns probe as one ink, `#039e89` H171.9, the midpoint of the two.
  Swept across the batch that is **88 panel-bands** where the crop lost an ink
  the source has (Tracking Sandy 53, Chicken Thief 23, Magic Ink 12), many of
  them total losses of 200-500px.
  **The docstring's claim that a 256-colour palette is `visually lossless` on
  flat line art is false for exactly the ink the pass depends on** -- and
  changing the palette METHOD does not fix it. Over the same 407 panel-bands the
  default loses 53 (13.0%), MAXCOVERAGE 65 (16.0%) and FASTOCTREE 72 (17.7%), so
  the default is the best of the three and a one-panel test of any of them is
  worthless. **FIXED 2026-09-21 by not quantizing unless the file has to be**:
  panels are written in full RGB and fall back to the palette only over the
  500KB budget. Measured over the same 155 panels that is 0.5% of bands lost
  against 13.0%, the fallback fires on 3 panels (1.9%), and the largest file is
  343KB. Disk goes from 12.9MB to 34.9MB, which is the whole cost.
- **BUT IT IS NOT THE REASON THE PASS DECLINED.** Of the 45 groups the review
  moved from `nephews` to a name, **only 6 sit on a panel whose crop had lost
  that ink**; the other 39 had the colour present in the image the pass read.
  **The quantiser is worth fixing and it does not excuse the reading.**
- **DECLINING IS THE ERROR CLASS OF THE WHOLE BATCH: 45 OF THE 91 CORRECTIONS
  ARE `nephews` SHARPENED TO A NAME.** *Tracking Sandy* 22, *Chicken Thief* 23.
  Against them the pass over-named twice in the batch. **The collective is not
  the safe answer; it is the most expensive answer by a factor of twenty.**
- **AND THE TELL IS A SENTENCE THAT APPEARS MORE THAN TWICE.** Both Vol. 21
  titles carry the same boilerplate -- `front-on the crown reads black and the
  edge sliver names nobody` -- pasted into thirty-odd notes as the reason to
  decline. **A note written once and reused is a rule being applied instead of a
  panel being read.** Where the same sentence appears in more than two or three
  groups, that is the cohort to re-check before applying.
- **SCENE CONTINUITY IS A NAMING RULE AND THE ROSTER DOES NOT CARRY IT --
  CONFIRMED BY THE REVIEWER.** *Tracking Sandy* 051 g8 carries the review's own
  note `Huey from previous panel`. A boy identified in one panel keeps his
  identity through the run of panels that follows him, and that is evidence the
  pass never used once in 36 pages. **Track who was named in the previous panel
  and carry it forward until the scene changes.**
- **A CAP OFF THE HEAD BEATS A `bare-headed` CLAIM, AND IT COST THE ONLY ERROR
  IN THE BATCH'S BEST TITLE.** *The Magic Ink* 080 g11 went `nephews` ->
  `Huey`/red on the strength of a **red nephew cap lying on Scrooge's desk**.
  The pass had swept every crown in the story, found nothing, and written `the
  nephews are bare-headed in every panel of this title` into all 16 nephew
  notes. The roster already says it: **ask WHERE IS HIS CAP, not whether he is
  bare-headed**, and scan the whole panel, not the crowns.
- **QUOTED FRAMING CAPTIONS BELONG TO THE NARRATOR, NOT TO THE CHARACTER DOING
  THE FRAMING.** *Tracking Sandy* has five: the review put all four quoted ones
  -- 047 g4, 047 g10, 049 g12, 055 g12, including `"IT'S QUITE A STORY, DAISY!
  ..."` -- with **`narrator`**, and moved the one PLAIN caption, 048 g3 (`DREAD
  VALLEY SANDY! THE FABULOUS DESERT RAT ...`), to **`Donald`**. So the quotation
  marks mark the flashback frame and not a speaker. **A caption is a character's
  only when it continues that character's own speech across a panel break** --
  048 g3 answers Scrooge's `SEE THAT MAN?` from the panel before.
- **AN ANOMALOUS PAGE DOES NOT GET TO REWRITE THE CONVENTION ON THE OTHERS.**
  *Tracking Sandy*'s 15 wrong names all came from reading 051 panel 3's `RUN AND
  GET UNCA DONALD, LOUIE!` as a title-wide mapping. It is local to 051, and the
  address named a boy who never speaks, so it attached to no group and could not
  be checked. **When one page's dialogue disagrees with red/blue/green, flag that
  page and name the rest by the convention.** *Chicken Thief*, where the pass did
  exactly that, came back with the convention intact -- Huey/red 23, Louie/green
  8, Dewey/blue 6, no disagreement anywhere.
- **THE MEDIUM/HIGH SPLIT ONLY WORKS WHEN THE PASS IS OTHERWISE RIGHT.** *Noble
  Porpoises* 7.1% high against 40.0% medium; *Tracking Sandy* 30.2% against
  75.0%; but *Chicken Thief* **24.1% against 25.0%** -- no split at all. **A flat
  split means the confidence field is not tracking anything**, which on that
  title it was not: the errors were a habit applied uniformly, and a habit does
  not feel uncertain.
- **`other:` VALUES AFTER REVIEW, none near-duplicate:** *Noble Porpoises* `the
  aquarium keeper` 5; *The Magic Ink* `the ink salesman` 10, `the messenger` 1;
  *Tracking Sandy* `Dread Valley Sandy` 21, `James the chauffeur` 1; *Chicken
  Thief* `the coyote pup` 18, `the chickens` 2, and one chorus value the review
  introduced, **`other:Donald, Grandma Duck, and the nephews`** on 066 g13.
  **`Grandma Duck` is a roster value**, not an `other:` -- `vision_apply`
  canonicalises it silently and says so in one line.
- **ALL 16 OF THE PASS'S TYPE CORRECTIONS WERE ACCEPTED, AND THE REVIEW ADDED
  SEVEN MORE OF ITS OWN.** The pass's were two story logos stored as
  `background` and fourteen animal voices stored as `sound_effect`. The review
  added 040 g4 `narration -> dialogue`, 040 g7 and three on *The Magic Ink*
  `dialogue -> thought` (a character musing alone), and 062 g7. **A balloon over
  a character alone in the panel is worth opening before the stored type is left
  to stand.**
- **NOTHING OUTSTANDING.** *Chicken Thief* 057 g12 (`RRARR!`, the coyote) came
  back unchanged, so all four titles close at every group reviewed on both
  engines, and the corpus-wide corrections queue is down to one -- vol 23 *The
  Librarian* 118 g19, which predates this batch.

### Findings to paste into the next run (2026-09-21, seventy-fifth batch, *Tracking Sandy* REVIEWED AND MIRRORED)

**139 groups on both engines, every one reviewed; 48 speaker corrections (34.5%),
47 of them in the nephew domain -- 73.4% of 64.** By the confidence the pass
wrote, **high 38 of 126 (30.2%) against medium 9 of 12 (75.0%)**. This is the
worst-scoring title in the ledger and the two causes are separable: a mapping
that was inverted for the whole story, and a rule for declining that was far too
strict. 20 images, 2.00 per page -- **the cost was not the problem.**

- **THE PASS HAD DEWEY AND LOUIE SWAPPED FOR THE WHOLE TITLE, AND IT KNEW IT WAS
  DOING SOMETHING UNUSUAL.** The review's mapping is the corpus convention --
  **Dewey/blue 16, Louie/green 12, Huey/red 10** -- and the only recorded
  disagreement is on 051, where Dewey wears green on g4 and g6. The pass read
  051 panel 3's `RUN AND GET UNCA DONALD, LOUIE!` as putting Louie in the blue
  cap and then **propagated that mapping to every other page**, writing it into
  every note as a title-wide finding. **Every green and every blue call it made
  was wrong; all three of its red ones held.**
- **THE RULE THIS BREAKS IS THE ONE THE ROSTER ALREADY HAS, READ BACKWARDS.** A
  colourist error is `recorded as that disagreement, never by correcting the
  colour` -- and the corollary the pass missed is that **an anomalous page does
  not get to rewrite the convention on the other nine.** 051 is the anomaly; the
  pass made it the anchor. **When one page's dialogue disagrees with red/blue/
  green, the disagreement is local until a second page confirms it.** Naming the
  other nine pages by the convention and flagging 051 alone would have cost 2
  corrections instead of 15.
- **AND THE ADDRESS NEVER NAMED A SPEAKER.** `RUN AND GET UNCA DONALD, LOUIE!`
  names a boy who says nothing, so it attaches to no group and cannot be checked
  against anything. The pass built a title-wide mapping on an utterance with no
  speaker of its own. **An address only anchors a mapping when the boy it names
  then speaks.**
- **THE OTHER HALF IS UNDER-NAMING: 22 GROUPS WENT FROM `nephews` TO A NAME, AND
  21 CAME BACK CARRYING A CAP COLOUR.** The pass named 18 of 66 in the domain
  and left 48 collective; the review names 41 and leaves 23. The standing note
  -- `front-on the crown reads black and the 50-150px edge sliver names nobody`
  -- was written once and then pasted into thirty-odd groups as a reason to
  decline.
- **AND THE SCREEN IS WHY, NOT THE ART.** 054 panel 1: the pass wrote `only
  Donald's 6,765px sailor cap prints`, quoting `crowns.py`. Running `capwide` on
  that panel at a **5px floor** returns a **136px `#00a5d5` H193.5 S1.0 blob at
  x336-349**, clear of Donald's 15,035px cap at x677-844 -- a roster-blue segment
  on a boy's crown, which is what the review named. **`crowns.py` and the head
  census are a screen and they drop real caps. Run `capwide` at a low floor on
  every nephew panel before writing any collective.** That is the seventieth
  batch's finding arriving for the fourth time and it is now the most expensive
  habit in the loop.
- **ONE THING TO PUT BACK TO THE REVIEWER RATHER THAN INFER.** On 048 panel 8
  the three boys are front-on and the review named them `Dewey`/blue,
  `Huey`/red, `Louie`/green left to right. Probed one at a time, the OUTER TWO
  slivers are the **same ink to the pixel** -- `#039e89` H171.9 S0.98, 73px on
  the left boy and 220px on the right -- while the middle one is `#9e3613` H15.1
  S0.88. The red is unambiguous; the blue and the green cannot both come from an
  identical hex. One of the review's own notes, on 051 g8, reads **`Huey from
  previous panel`**, so **scene continuity looks like the missing rule** -- the
  same boy keeps his place across a run of panels -- and the roster carries
  nothing about it. **Worth confirming: if that is the rule, say so and it
  becomes cheap; if the two slivers really are distinguishable, the pass needs
  to know how.** (And where the ink is identical, `cap_colour` is then being
  filled in from the name, which the roster forbids for good reasons.)
- **FOUR `nephews` -> `Donald`, ALL ON 049, ALL OFF-PANEL OR PILE-UP.** g5 and
  g13 are panels where the pass wrote that the heads overlap or that no crown
  prints; g8 and g10 are balloons over a panel drawing only Sandy and his car,
  which the pass gave to the boys as `off-panel` because the two before them
  were theirs. **An off-panel voice over a panel with no ducks in it is Donald
  unless something says otherwise** -- he is driving, and the running commentary
  on that page is his.
- **THE FRAMING CAPTIONS SPLIT AND THE PASS GOT THE SPLIT EXACTLY WRONG.** The
  pass gave all four quoted captions to `Donald` on the reasoning that he is
  telling Daisy the story, and gave the plain expository one to `narrator`. The
  review keeps **047 g4** (`"IT'S QUITE A STORY, DAISY! ..."`) as Donald and
  moves **047 g10, 049 g12 and 055 g12** (`"BUT WE GOT A SURPRISE!"`, `"HOURS
  LATER WE WERE FAR OUT IN THE DESERT!"`, `"DID WE GET A SURPRISE!"`) to
  `narrator` -- while moving the PLAIN caption **048 g3** (`DREAD VALLEY SANDY!
  THE FABULOUS DESERT RAT ...`) the other way, to **Donald**. So quotation marks
  are not the discriminator and neither is first-person plural. **The one
  Donald-quoted caption that survived is the one that names Daisy and opens the
  flashback.** Worth a ruling: the rest of the corpus has framing devices in it.
- **AND THE REVIEW ADDED A GROUP THE PASS'S DEVICE SWEEP COULD NOT HAVE FOUND.**
  056 panel 7: a drawn **`$` on the face of Scrooge's Money Bin**, full-page box
  (989,2274)-(1041,2358), checked against its own crop before mirroring --
  correct box, text, type `background`, speaker `none`, and no seed residue. The
  pass's rule was to sweep panels where a character is delighted or dismayed
  about money; **this one is a building label with no character near it.** Sweep
  landmarks too -- the Money Bin, a bank, a safe, a vault door.
- **`other:` values after review: `Dread Valley Sandy` 21 and `James the
  chauffeur` 1, both unchanged.** No drift. The pass's one type correction
  (047 g0, the story logo stored as `background`) was accepted.

### Findings to paste into the next run (2026-09-21, seventy-fifth batch, *Noble Porpoises* REVIEWED AND MIRRORED -- 118/118)

**118 groups on both engines, every one reviewed; 10 speaker corrections (8.5%), all
ten of them in the nephew domain (22.7% of 44).** By the confidence the pass
wrote, **high 8 of 113 (7.1%) against medium 2 of 5 (40.0%)**, a 5.6x split. The
review also made two text corrections and two type corrections the pass had not
proposed, and added and deleted no groups. 34 images, 3.40 per page.

- **THE TAIL IS THE ERROR, NOT THE CAP. NINE OF THE TEN CORRECTIONS CITE
  `balloon-tail`, AND NOT ONE `sole-figure` CALL WAS WRONG.** By the evidence
  the pass listed: `sole-figure` **0 of 19**, `off-panel` 0 of 2, no-evidence
  (sound effects and signs) 0 of 15 -- against `balloon-tail` 9 of 72 (12.5%),
  `caption` 1 of 6, `dialogue` 1 of 6. Where one figure could possibly be
  speaking the pass was perfect over nineteen groups. **Every image spent on a
  panel with a single candidate is wasted; every one spent separating two tails
  is not.**
- **ALL THREE WRONG-BOY CALLS HAD THE TIP WITHIN 30px OF A HEAD BOUNDARY AND I
  SETTLED THEM WITH A MARGIN RULE INSTEAD OF A CROP.**
  037 g4: tip at panel x670 in the gap between heads ending 642 and beginning
  695; I applied one-head-LEFT and the answer is the RIGHT head (`Dewey`/blue ->
  `Louie`/green). 045 g7: tip at 616, four pixels inside a span ending 620, and
  the answer is the next head right at 640 (`Louie`/green -> `Huey`/red).
  039 g3: tip at 332, four pixels left of a head beginning 336; I took that head
  and the answer is the MIDDLE one (`Louie` -> `Dewey`/blue).
  **Two went right and one went left, so no margin rule would have got all
  three.** A tip inside half a head-width of a boundary is a 4-6x crop or a
  collective; it is not arithmetic.
- **AND `a gap tip goes one head LEFT` DOES NOT HOLD IN VOL. 21.** That rule was
  measured on Vols. 10 and 14 (nearness 0 for 2, direction 0 for 6). The one
  clean gap tip in this title went the other way, and quoting the rule is what
  made 037 g4 a `high`. **Treat it as a Vol. 10/14 finding until another volume
  reproduces it.**
- **BOTH UNDER-NAMINGS ARE EVIDENCE THE NOTE ALREADY RECORDED AND THEN VOTED
  AGAINST.** 037 g6 -> `Huey`/red: the note says the boy's crown probes with no
  chromatic ink, having also recorded a **43px `#e7191e` at S0.89 on his head's
  left edge** and called it inconclusive. 041 g13 -> `Louie`/green: the note
  quotes capwide at a **5px floor** returning `red: 0 blob(s), green: 0 blob(s)`
  across the whole panel -- and the reviewer found green on a crown inside it.
  **A whole-panel zero, at any floor, is a statement about the panel. Probe the
  crown.** This is the seventieth batch's finding arriving for the third time.
- **BOTH OVER-NAMINGS ARE MARGINS THE NOTE QUOTED AND THEN TRUSTED.** 040 g10
  -> `nephews`: named from a 435px `#3da252` H132.5 probe **with the tail never
  traced**, and the note says so. 044 g8 -> `nephews`: tip 12px off the head.
  **A name needs a readable cap AND a tail that lands on that boy. Either one
  alone is the collective** -- the pass got 26 of its 31 names right and every
  one of the five failures is missing one half of that pair.
- **BOTH MEDIUMS WERE WRONG AND BOTH NOTES NAMED THE ALTERNATIVE.** 046 g0 ->
  `nephews`: the note reads `Flagged as medium: it could be a nephew's`. 039 g3
  -> `Dewey`: named by elimination against two boys the pass had already
  mis-keyed. **A `medium` whose note spells out the other answer is the other
  answer.** 2 of 5 against 8 of 113 is the whole argument for cashing it.
- **A CAPTION BOX WAS A CHARACTER'S BALLOON, ONE BATCH AFTER THE LAST TIME.**
  040 g4 `IT WASN'T SAFE! BOAT HIT A REEF!` went `narrator` -> **`Donald`** and
  `narration` -> **`dialogue`**. The seventy-fourth batch's rule was `ask whose
  knowledge the caption carries`; this one does not even need that, because the
  panel draws the balloon. **Look at the box before typing `narrator`** -- the
  pass wrote `Caption box.` as its entire note and never opened the panel.
- **041 g2 WENT `Donald` -> `Dewey` ON REGISTER.** `(PUFF! PANT!) NOW WE'VE GOT
  TO PULL THE BIG BOAT OFF THE REEF!` is a work order in a bossy voice, which is
  why it read as Donald; the tail is over the dinghy. **Register is not evidence
  when the art is readable**, and the note cited `balloon-tail` for a tail it had
  not measured.
- **THE PALETTE HELD AND THE H160-180 TEAL DID NOT.** Three of the four
  `cap_colour` moves are rims the pass recorded in that band -- `#15a89d` H175
  (037 g4, blue -> green), `#457769` H163 (038 g9, blue -> green) and `#13a9a8`
  H179 (044 g8, withdrawn). **Every clean `#00a5d5`-`#01a5d7` H190-194 read
  held.** The founding read on 037 panel 2 called the middle boy's `#15a89d`
  `Dewey's shaded blue` and that assumption then travelled the whole title. **In
  this title H160-180 is unreadable, not Dewey.** After review the ink and the
  name disagree on exactly **one group in thirty-two** -- 038 g9, which keeps
  `Dewey` with a green cap -- so red/blue/green is otherwise intact here.
- **AND THE MONEY DID NOT GO WHERE THE ERRORS WERE.** 14 of the 34 images went
  on 037-039 establishing the construction, and **three of the ten corrections
  are on those same three pages**. What that spend bought was the palette, which
  held; what it did not buy was a single separated tail. **On a title whose caps
  are legible, budget the images for the two-boy panels, not for the reference
  panel.**
- **TWO TEXT AND TWO TYPE CORRECTIONS, NONE OF THEM PROPOSED BY THE PASS.**
  039 g1 `OVER-` to a soft hyphen and 046 g4 `AND SO-` to `AND SO —`, both
  applied by hand to both engines; 040 g4 `narration -> dialogue` and 040 g7
  `dialogue -> thought` (`GLUG! BLUB!` under water is a thought balloon).
  **Punctuation glyphs are not `corrected_text` territory for the pass -- the
  roster says so -- but they are worth a `note`, and neither of these got one.**
- **`other:` values after review: `the aquarium keeper` 5, unchanged and the
  only one in the title.** No drift.
- **THE TWO STRAGGLERS CAME BACK UNCHANGED, WHICH IS THE POINT.** 038 g4
  (`SOON!`, narrator) and 040 g7 (`GLUG! BLUB!`, Donald) were signed off with no
  change to either speaker, so the title closes at **118 of 118 reviewed on both
  engines** and the ten corrections above are the whole of it.

### Findings to paste into the next run (2026-09-21, seventy-fifth batch, NONE REVIEWED)

*Noble Porpoises* (21, 10pp), *The Magic Ink* (22, 6pp), *Tracking Sandy* (21,
10pp) and *The Littlest Chicken Thief* (21, 10pp). **424 groups on both engines
across 36 pages, 79 images, 2.19 per page** (3.40 / 1.67 / 2.00 / 1.50). 4
groups added for drawn devices, 16 type corrections proposed, no text
corrections, and the missed-text audit is clean on all four.

- **VOL. 21 HAS TWO CAP CONSTRUCTIONS AND THEY CHANGE FROM TITLE TO TITLE.**
  *Noble Porpoises* prints a **thin coloured RIM** on a black cap, 90-900px, a
  crescent at the back-left of the crown. *Tracking Sandy* and *The Littlest
  Chicken Thief*, both later in the same volume, print a **QUARTERED black
  beanie**, 400-2,100px, alternating black and colour. They are not the same
  thing to look for and the rim survives angles the quarters do not. **Derive
  the construction from a reference panel in every Vol. 21 title; carrying one
  over from the title before it would have cost the whole of this batch.**
- **A QUARTERED CAP SEEN FRONT-ON NAMES NOBODY, AND ITS EDGE SLIVER IS A TRAP.**
  Face-on the crown reads solid black and 40-160px of colour shows at the very
  edge -- and that sliver prints `#039e89` H172, `#00a171` H162, `#039c57` H158,
  all in the band BETWEEN this volume's green (H147) and blue (H194). Two boys
  in one row can both return it. **A sliver at a head's outer edge is an
  antialiasing artefact of the black outline, not a cap read.** It is why 48 of
  *Tracking Sandy*'s 66 nephew groups and 33 of *Chicken Thief*'s 46 are
  collectives forced by the art.
- **THE NAME-GREP MISSES `LOUIE` AND IT MATTERED TWICE.** `barks-ocr-name-grep`
  reported zero nephew names on all four titles. Both *Noble Porpoises* 042 g0
  (`WHAT ARE YOU TRYING TO TELL ME, LOUIE?`) and *Tracking Sandy* 051 g4 (`RUN
  AND GET UNCA DONALD, LOUIE!`) address him by name, and the second one settles
  a title-wide mapping. LOUIE is a dictionary word and so is invisible to the
  non-dictionary list. **Grep the stored `ai_text` for HUEY|DEWEY|LOUIE yourself
  at prep; it costs one command and the tool will not do it for you.**
- **TRACKING SANDY PUTS LOUIE IN THE BLUE CAP.** 051 panel 3 has all three boys
  in one frame: the GREEN-capped one says `RUN AND GET UNCA DONALD, LOUIE!`
  (tail tip at panel x200, on his own head), the RED-capped one says `WE'LL
  FOLLOW THAT DUDE!` (tip at x496, on his), and the BLUE-capped one -- the only
  one who says nothing -- is gone from panel 4, which draws only the green and
  red boys. Recorded as printed: blue Louie, red kept as Huey because nothing in
  the title contradicts it, green taken as Dewey by elimination. **One address
  is thin evidence for a title-wide mapping and this one is worth the reviewer's
  eye first.**
- **AND THE NEXT TITLE IN THE SAME VOLUME HAS NO TEST AT ALL.** *The Littlest
  Chicken Thief* runs 057-066, immediately after *Tracking Sandy*'s 047-056,
  with the same construction and the same three inks -- and names no nephew
  anywhere in its dialogue. Its 13 names were set on the corpus convention (red
  Huey, blue Dewey, green Louie) and every one of them carries that reasoning in
  its note. **If the reviewer confirms the swap on *Tracking Sandy*, this title
  is the one to re-check, and it is a one-line grep.**
- **CAPWIDE MISSED THREE RIMS THAT `probe.py` FOUND, AND THE NAMES CAME FROM THE
  PROBE.** *Noble Porpoises* 044 panel 7: capwide at a **3px** floor returns
  `blue: 0 blob(s)` and nothing in green but the sea, because the sea is
  `#23b08d` H165 at 24,000px and swallows the band. Probing each crown on its
  own gave 98px of red at S0.88 on the left boy, 137px at H170.0 on the middle
  one and 154px at H149.2 on the right -- three names on a panel the census
  called empty. **When a title's water or foliage shares the cap hue, the
  whole-panel scan is the wrong tool and `probe.py` on each crown is the right
  one. Rank the heads against each other, never against a floor.**
- **THE ROSTER BLUE IS THE SEA IN NOBLE PORPOISES.** `#00a5d5` H194 fills whole
  panels as water and sky, Donald wears it as a sailor cap at 1,400-4,500px, and
  Dewey's rim is the same ink at 43-600px when lit -- and `#15a89d` H175 /
  `#1ea176` H160 when shaded. **The cool rim in that title spans H160-194 and
  area is the only discriminator.** The dinghy is `#1ab08b` H165 at 13,700px and
  sits in the middle of that span.
- **DONALD'S SAILOR CAP AGAINST A NEPHEW'S BLUE QUARTER IS A SHAPE TEST, NOT A
  HUE TEST.** Identical `#00a5d5` in both Vol. 21 titles. His is ONE solid
  rounded blob of 2,000-6,800px; a boy's is 400-1,200px split across two or more
  segments, and the census prints them as separate blobs on one crown. That
  alone settled *Tracking Sandy* 052 panel 1, where the second figure has no bow
  tie, a 100px head against Donald's 160px, and two blue blobs.
- **A BARE-HEADED TITLE IS STILL A TITLE-WIDE CLAIM AND NEEDS THE WHOLE SWEEP.**
  *The Magic Ink* prints no nephew cap on any panel: capwide returns green 0 and
  blue 0 on every one of the boys' panels, indoors and out, and all 16 nephew
  groups are collectives forced by the art. That took one loop over the title,
  not two panels.
- **SIXTEEN TYPE CORRECTIONS, FIFTEEN OF THEM ONE CLASS.** *Chicken Thief* has a
  coyote, a henhouse and a hypnotised Donald, and the engines stored every
  growl, squawk, `OW!` and `BAA!` as `sound_effect`. They are a character's
  voice, so they go to `dialogue` with the animal named -- `other:the coyote
  pup`, `other:the chickens`. **The bare `SNAP` of jaws closing stays
  `sound_effect` and takes the maker as its speaker**; that is the line between
  the two. The sixteenth is *The Magic Ink* 076 g0, the story logo stored as
  `background` rather than `title`, which *Tracking Sandy* 047 g0 repeats.
- **FOUR DRAWN DEVICES ADDED, AND THREE OF THEM SIT WHERE THE LAST BATCH SAID TO
  LOOK.** *Noble Porpoises* 037 panel 5 (a cluster of four `$` round Donald's
  head as he grabs the fish) and 046 panels 5 and 6 (a `$` on each money bag);
  *The Magic Ink* 081 panel 9 (two `?` over the ink-splashed salesman); *Chicken
  Thief* 062 panel 4 (a `?` over the coyote being hypnotised). Sweeping every
  panel where somebody is delighted or dismayed about money found all three of
  the `$` on the first pass. The corpus convention for a cluster is ONE group
  with the signs space-separated, `"$ $ $ $"`, type `thought` for a bare device
  over one figure and `background` for a label painted on an object.
- **A `$` CLUSTER CAN OVERLAP THE BALLOON'S BOUNDING BOX AND BE REFUSED.** 037
  panel 5's four signs span x573-733 y32-168 and the balloon's box reaches
  x613 y143: the tight cluster box scores 20.4% against a 20% ceiling. Measure
  the glyphs with a dark-blob pass before choosing the box -- widening it to
  x578-740 y28-172 drops the overlap to 17% and still covers all four.
- **AND AN ADD RENUMBERS THE PAGE, SO A RE-APPLY REJECTS ITS OWN ADDITION.**
  Re-applying *The Magic Ink* after the SPLOOK fix was refused with `added_groups
  [0] overlaps existing group 13 by 100%`. Drop the `added_groups` key before any
  re-apply, and remember that the new group takes an id in READING ORDER (the
  `?` on *Chicken Thief* 062 became g6, not g13), so a stored `result.json`
  written before the add no longer maps onto the page.
- **THE AUDIT CAUGHT ONE TRANSCRIPTION ERROR AND IT WAS MINE, NOT THE ENGINE'S.**
  *The Magic Ink* 081 panel 8 is a tall narrow panel with the word drawn
  vertically bottom-to-top; the capture read `SPOOK` and the group has `SPLOOK`,
  which a 1.4x crop confirms. **`nearly a grouped text` is worth reading as a
  check on the pass before it is read as a check on the engine.**
- **`other:` VALUES, all singletons or small and none near-duplicate:**
  *Noble Porpoises* `the aquarium keeper` 5. *The Magic Ink* `the ink salesman`
  10, `the messenger` 1 (plus `Scrooge's clerk` and `the delivery men` as
  depicted-only). *Tracking Sandy* `Dread Valley Sandy` 21, `James the
  chauffeur` 1. *Chicken Thief* `the coyote pup` 17, `the chickens` 2.
  **`Grandma Duck` is a roster value, not an `other:`** -- `vision_apply`
  canonicalised 25 of them silently and said so in one line.
- **A DISGUISE IS RECORDED AS THE CHARACTER, NOT THE COSTUME.** *The Magic Ink*'s
  `Prof. Umbugg von Pfake` is Scrooge in a false beard -- he sets the hoax up on
  the telephone on 077 panel 3 and gloats over it on 077 panel 8, and the name
  reads as `humbug von fake`. All 11 of the professor's groups are `Scrooge`
  with `costume` in the evidence. *Tracking Sandy* does the same with Sandy's
  sombrero and his rabbit-foot shoes.
- **STILL OUTSTANDING AND NOT FROM THIS BATCH:** a corpus run of
  `barks-ocr-vision-corrections` with no `--title` reports 35, of which 34 are
  this batch's own proposals awaiting review. The 35th is **vol 23 *The
  Librarian* 118 g19, `thought -> dialogue`**, left over from an earlier pass.

### Findings to paste into the next run (2026-09-20, seventy-fourth batch, ALL THREE REVIEWED AND MIRRORED -- batch closed)

**443 groups reviewed across the three titles; 21 speaker corrections (4.7%).**
By title: *The Twenty-four Carat Moon* **19 of 269 (7.1%)**, *The Forbidium
Money Bin* **2 of 143 (1.4%)**, *The House on Cyclone Hill* **0 of 31 (0.0%)**.
Only *24-Carat* has nephews: 11 of 45 in that domain (24.4%). **By the
confidence the pass wrote, high 13 of 417 (3.1%) against medium 5 of 23
(21.7%) -- a 7x split, and the sixth batch running that medium is the worse
bet.** Both of the pass's type overrules held, its one text correction held,
and no cap colour was reversed anywhere in the batch.

- **THE ERROR IS ALMOST ENTIRELY IN ONE TITLE AND ONE SKILL.** *Forbidium* at
  1.4% and *Cyclone Hill* at 0.0% are two-hander and solo stories where costume
  settles everything -- Scrooge's top hat against Gyro's green vest on earth,
  the YELLOW against GREEN pressure suits on the moon. *24-Carat* is 7.1%
  because it puts four ducks in identical cream bubble helmets for fifteen
  pages. **A story that uniforms its cast is the expensive one, and the cost
  lands on adult-versus-boy, not on caps.**
- **CROPS AT 1.2x-1.6x ARE NOT ENOUGH TO NAME A HELMETED DUCK: 8 OF THE 21
  CORRECTIONS.** Donald -> Scrooge x3, Scrooge -> Donald x2, nephews -> Donald
  x2, Donald -> nephews x1, all on *24-Carat*, and every note quotes the same
  test -- `the wide adult beak and no whisker fringe`, `small round beak, no
  whiskers`. Inside a cream helmet at that scale the helmet flattens the
  silhouette and the whisker fringe reads as hatching. **2.5x or better, or
  name him from something that is not his face.**
- **A TRACED TAIL THAT ENDS ON NOTHING IS AN OFF-PANEL SPEAKER, AND I WROTE THE
  MEASUREMENT DOWN AND THEN OVERRULED IT.** *24-Carat* 011 g15 -> `other:rocket
  control`. The note says, in capitals, `ART AND SENSE DISAGREE HERE AND I HAVE
  GONE WITH SENSE`, having established at 5x that the tail runs into the open
  hatchway and lands on empty cream. **Name the off-panel role.** It also cost
  seven images on that page and six on the next, against a ceiling of five --
  the measurement was finished after two crops and the rest went on arguing.
- **CAPTIONS CARRY A CHARACTER'S KNOWLEDGE MORE OFTEN THAN THEY CARRY THE
  AUTHOR'S: 3 of the 5 `other:` corrections are `narrator` -> a named voice**
  (010 g19 the TV newscaster, 012 g8 a reporter, 022 g10 Muchkale). The roster's
  rule that the field records the BOX governs the TYPE, not the speaker. **Ask
  whose knowledge the caption carries** -- 022 g10 explains that on an airless
  moon only thoughts carry, which is Muchkale's own explanation of his own world.
- **NAMING A SIGNALLING MACHINE IS NOW SETTLED, IN BOTH DIRECTIONS.** The five
  `other:the cyclone warning bell` groups on *Cyclone Hill* and the one
  `other:the mineral detector bell` on *Forbidium* all held, as did the bell
  SPEAKING words (`ALL CLEAR!`, `dialogue`) off a device Barks draws with a
  face. Impacts, drills, engines, slams and explosions stayed `none` and none of
  those was touched either. **A machine that deliberately signals takes its
  maker as speaker; a machine that merely runs does not.**
- **WHERE THE INK IS READABLE, READING IT IS SAFE.** *24-Carat*'s two names --
  011 g8 Huey/red, 012 g2 Dewey/blue, each on a measured tip plus a clean flash
  -- both held, and **there is not one `cap_colour_was` entry in the whole
  batch.** 11 nephew-domain corrections and not one of them a cap read.
- **TWO MEDIUMS CALLED FROM REGISTER ALONE BOTH LOST.** *24-Carat* 016 g0
  `Scrooge` -> `other:the Rajah of Eyesore` (two ships fighting, no figures, and
  I never traced which hull the tail touched) and *Forbidium* 069 g6 `Scrooge`
  -> `Gyro` (`GREAT ASTEROIDS!`, which I grouped with his SUFFERIN' SATURN and
  HOWLING HOTRODS). **The alliterative oath is not a Scrooge tag in Vol. 22** --
  YE CATS went to Gyro on *Forbidium* 067 g2 and to a nephew on *24-Carat* 014
  g6. Stop using register to break a two-adult tie; trace the hull.
- **A COSTUME READ THAT STOPS AT THE COLOUR UNDER-NAMES.** *Forbidium* 072 g2
  `other:a passer-by` -> **`other:a policeman`**. My note says `the man in the
  blue coat and hat at the bottom left` -- the blue coat AND hat together are a
  uniform, and I described them without reading them. **If a background figure's
  clothes are consistent enough to describe, they are consistent enough to
  name.**
- **THE REVIEW ADDED THREE DRAWN `$` DEVICES AND THE PASS HAD FOUND ONE.**
  *24-Carat* 024 panel 8 was reported; **025 panels 3 and 4 never reached the
  capture at all**, so the audit was blind to them -- the seventy-third batch's
  "the capture is the audit's only eyes" repeating verbatim. Both panels are
  somebody rejoicing over money, which is exactly where Barks puts the device.
  **Sweep for drawn devices on every panel where a character is delighted or
  dismayed about money.** The two captures are reconciled to the adds.
- **RUN `audit_groups.py` BEFORE THE MIRROR.** It caught one `other:the tv
  newscaster` against fourteen `other:the TV newscaster` that the review had
  introduced; at that point the fix is one keystroke, and after the mirror it is
  a corpus-wide grep. The closeout does this at `--stage review`.
- **OUTSTANDING AT CLOSE, AND IT IS ALL ONE QUESTION.** *Forbidium*'s two
  missed-text items are unworked -- **059 panel 6's `$` painted on the frosted
  teller's window and 062 panel 5's display `ROAR`**, both grouped by neither
  engine, both real. And *24-Carat*'s audit still reports 22 capture-listing
  items awaiting a ruling: 16 Beagle Boy placard bundles (the pinned number and
  the sweater legend share one box), 5 instances of Muchkale's tunic `V`
  (grouped on 023 only), and 020's two drawn music notes. **Everything else in
  the batch is clean**: both engines match on every field in all three titles,
  no corrections outstanding, *Cyclone Hill* audits clean, and the prelim tree
  is empty.
- `other:` values after review. *24-Carat*: `Muchkale` 31, `the Rajah of
  Eyesore` 9, `the TV newscaster` 8, `the Texas cattle king` 8, `the radio
  newscaster` 4, `the rocket designer` 2, `a rocket workman` 2, `rocket control`
  1, `the launch announcer` 1, `a reporter` 1. *Forbidium*: `the tattooist` 2,
  `a reporter` 2, `the mineral detector bell` 1, `a policeman` 1. *Cyclone
  Hill*: `the cyclone warning bell` 5. The three announcer values on *24-Carat*
  look like drift and are not -- a TV set, a pad loudspeaker and a cabin radio.

### Findings to paste into the next run (2026-09-20, seventy-fourth batch, *The Twenty-four Carat Moon* REVIEWED AND MIRRORED)

**269 groups on both engines, every one reviewed; 19 speaker corrections (7.1%),
11 of them in the nephew domain (24.4%). By the confidence the pass wrote, high
12 of 250 (4.8%) against medium 4 of 16 (25.0%) -- a 5.2x split.** The review
added three groups and reversed no cap colour. The pass's one type overrule and
its one text correction both held.

- **THE TAIL WAS RIGHT AND I VOTED AGAINST IT, IN WRITING, AND IT COST SEVEN
  IMAGES.** 011 g15 `START THE COUNT DOWN!` went `Scrooge` -> **`other:rocket
  control`**. I traced that tail at 5x, established it runs into the open
  hatchway and lands on empty cream with Scrooge drawn at the far left with his
  own balloon, wrote **`ART AND SENSE DISAGREE HERE AND I HAVE GONE WITH
  SENSE`** into the note -- and then handed the line to the duck in frame. The
  reviewer named exactly the off-panel voice the tail pointed at. **A POINTED
  TAIL RUNNING INTO A DOORWAY, HATCH OR WINDOW AND ENDING ON NOTHING IS AN
  OFF-PANEL SPEAKER. Name the role -- ground crew, rocket control, the next room
  -- rather than giving the line to whoever is standing there.** The same group
  is why pages 011 and 012 cost 7 and 6 images against a ceiling of 5: the
  measurement was finished after two crops and the other five went on arguing
  with it.
- **CAPTIONS ARE CHARACTERS FAR MORE OFTEN THAN I ALLOWED: THREE OF THE FIVE
  `other:` CORRECTIONS ARE `narrator` -> A NAMED VOICE.** 010 g19 -> `other:the
  TV newscaster`, 012 g8 -> `other:a reporter`, 022 g10 -> `other:Muchkale`.
  Every one is a caption box whose CONTENT is a particular character's knowledge:
  022 g10 explains that on an airless moon only thoughts carry, which is
  Muchkale's own explanation, and 012 g8's `(COUGH! CHOKE!)` aside is a watcher
  at the launch. **Before writing `narrator`, ask whose knowledge the caption
  carries.** The roster's rule that the field records the BOX is about the TYPE;
  it does not make the speaker the author. On a story with a broadcast, a press
  frame or a talking alien, the boxes are worth reading twice.
- **THE ADULT/BOY CALL UNDER A BUBBLE HELMET FAILED IN BOTH DIRECTIONS -- 8 OF
  THE 19 CORRECTIONS.** Donald -> Scrooge three times (014 g7, 015 g9, 015 g10),
  Scrooge -> Donald twice (016 g13, 022 g8), nephews -> Donald twice (026 g1,
  026 g4), Donald -> nephews once (021 g8). **Every one of those notes quotes the
  same test** -- `the wide adult beak and no whisker fringe`, `small round beak,
  no whiskers` -- read off a crop at 1.2x to 1.6x. Inside a cream helmet at that
  scale the test does not work: the helmet flattens the silhouette and the
  whisker fringe reads as helmet hatching. **Crop a helmeted head at 2.5x or
  better before naming the duck inside it, or name him from something else --
  the pressure-suit colours did this perfectly on *The Forbidium Money Bin*
  (Scrooge yellow, Gyro green) and cost nothing.**
- **015 g9/g10 IS THE INSTRUCTIVE PAIR.** I reasoned that panel 7's close-up was
  the same duck as panel 6's because the binoculars are drawn flying out of his
  hands, cropped the head at 2x, read `no side-whiskers, wide beak, tongue out`
  and wrote Donald into both. Both are Scrooge. The continuity argument was
  sound and the identification inside it was wrong, which is the dangerous
  shape: **a correct chain of reasoning resting on one bad pixel read carries
  the error to every group downstream of it.**
- **THE CAPS WERE NEVER THE RISK ON THIS TITLE.** Both names held --
  011 g8 Huey/red and 012 g2 Dewey/blue, each on a measured tip plus a clean
  flash -- and **there is not one `cap_colour_was` entry in the whole title.**
  11 nephew-domain groups were corrected and not one of them was a cap read;
  they were all adult/boy confusions. Where the ink is readable, reading it is
  safe; it is the ducks that need the crop.
- **A MEDIUM CALLED FROM REGISTER ALONE LOST AGAIN.** 016 g0 `Scrooge` ->
  **`other:the Rajah of Eyesore`**. The panel is two ships fighting and the
  balloon comes off one of them; I wrote `every other exchange on this page is
  his against a nephew's` and never traced which hull the tail touched. **On a
  panel with two vehicles and no figures, the tail still picks the ship. Trace
  it -- it is one crop.**
- **THE REVIEW ADDED THREE DRAWN `$` DEVICES AND I HAD FOUND ONLY ONE.** 024
  panel 8 I reported; **025 panels 3 and 4 I never wrote into the capture at
  all**, so the audit was blind to them -- the seventy-third batch's finding
  about the capture being the audit's only eyes, repeating exactly. The tell was
  available: both panels are somebody rejoicing over money, which is where Barks
  puts the device. **Sweep for drawn devices on every panel where a character is
  delighted or dismayed about money, not only where the art looks unusual.** The
  two captures are now reconciled to the added groups.
- **THE GROUP AUDIT CAUGHT AN `other:` DRIFT THE REVIEW INTRODUCED, AND IT WOULD
  HAVE MIRRORED.** One group came back `other:the tv newscaster` against
  fourteen `other:the TV newscaster`. **Run `audit_groups.py` BEFORE the mirror,
  not after** -- the closeout does it, and the fix is one keystroke at that
  point and a corpus-wide grep later. `other:` values after review, once
  normalised: `Muchkale` 31, `the Rajah of Eyesore` 9, `the TV newscaster` 8,
  `the Texas cattle king` 8, `the radio newscaster` 4, `the rocket designer` 2,
  `a rocket workman` 2, `rocket control` 1, `the launch announcer` 1, `a
  reporter` 1. The three announcer values stay distinct and are correct: a TV
  set, a pad loudspeaker and a cabin radio.
- **STILL OUTSTANDING AND AWAITING A RULING, NOT A DEFECT:** the missed-text
  audit reports 22 on this title and every one is a capture-listing question --
  16 Beagle Boy placard bundles (the pinned number and the sweater legend share
  one box), 5 instances of Muchkale's tunic `V` (grouped on 023 only), and the
  two drawn music notes inside 020's `LUNA, THE MOONA` balloon. Split, group per
  page, or ignore-list; it wants deciding once for the volume.

### Findings to paste into the next run (2026-09-20, seventy-fourth batch, NONE REVIEWED)

**Vol. 22, three titles: *The Twenty-four Carat Moon* (20pp, 266 groups), *The
House on Cyclone Hill* (4pp, 31) and *The Forbidium Money Bin* (16pp, 143).**
40 pages, 440 groups, **96 images, 2.40 per page**; per title 3.45 / 1.75 /
1.25. 2 type corrections, 1 text correction, 3 missed-text items. Nothing
reviewed yet, so everything below is the pass's own account.

- **THE CAPS VANISH AT PAGE 013 AND NEVER COME BACK.** *The Twenty-four Carat
  Moon* has the three nephews in 15 of its 20 pages, but from 013 onward the
  whole crew is in bubble space helmets and `crowns.py` returns `NO INK ON
  CROWN` for **every head on every page from 013 to 027**. So the only pages
  where a cap can name anybody are 008-012, and only 011 and 012 actually print
  one. Every nephew call after 012 is a collective or comes from the dialogue.
  This is worth knowing at prep on any space or diving story: run
  `crowns.py <census> <pages>` over the whole title first and see where the
  readable window is, instead of scanning for ink page by page.
- **I NAMED TWO BOYS AND BOTH RESTED ON A MEASURED TIP PLUS A CLEAN FLASH.**
  011 g8 Huey (#e61b1f 1143px on the crown at the top of the ladder, one tail)
  and 012 g2 Dewey (tip at panel x648, 32px short of the blue boy's beak against
  122px to the red boy's). Everything else in the domain is `nephews`, and
  **five of those are genuine choruses** -- one balloon carrying two or three
  tails to two or three boys (011 g7 three tails, 012 g3 and g5 two each, 015 g8
  two, 021 g5/g6 across a row of three). Counting the tails before reaching for
  a name is what made those safe.
- **SCROOGE'S RED COAT IS THE ROSTER RED AT A HUNDRED TIMES THE AREA.** In this
  title his coat is `#e61b1f` -- *the exact cap red* -- at 5,000 to 25,000px,
  against a nephew band of 20 to 1,143px; his top-hat band and Donald's sailor
  cap are both `#00a4d5` at 1,300-3,500px against a boy's blue flash of 84-423px.
  The Vol. 22 area rule from the last batch holds exactly, and the cap
  CONSTRUCTION here is a black cap with a small coloured WEDGE at the front of
  the crown, not a band across it.
- **THE ONE GROUP THAT COST SEVEN IMAGES WAS A TAIL POINTING AT NOBODY.** 011
  g15 `START THE COUNT DOWN!`: traced at 5x, its ordinary pointed tail runs into
  the open hatchway and lands on empty cream, with Scrooge drawn at the far left
  with his own balloon. Page 011 ended at 7 images and 012 at 6 -- both over the
  ceiling -- for that one call, which I finally wrote `Scrooge` at medium with
  the disagreement spelled out. **A tail that lands on nothing is not worth more
  than two crops: write the conflict in the note and move on.** That single
  group is most of the gap between this title's 3.45 and the other two's 1.75
  and 1.25.
- **allbold RUNS LOW ON ALL THREE TITLES AND IS BLIND ON A WHOLLY-BOLD
  BALLOON.** Real emphasis came back at 1.10x-1.20x again and again (016 g2's
  GO BACK at 1.11x, 016 g12's STOP at 1.19x, 064 g0's CEILING at 1.10x, 068 g8's
  PURSE at 1.11x), every one confirmed by crop. And where the WHOLE balloon is
  set heavy it reports no hits at all, because the baseline rises with it --
  019 g2 (3.72), 024 g12 (4.05), 026 g6 (4.01). **The tell is the baseline: when
  a group's base is half a point above its neighbours', the balloon is bold and
  the ratios mean nothing.** Treat 1.10x as worth a crop on this volume.
- **TWO TYPE OVERRULES, BOTH THE SAME SHAPE THE SEVENTY-THIRD BATCH FOUND.**
  24-Carat 013 g7 `narration -> dialogue`: read at 1.15x it is a rounded balloon
  with a spiky BROADCAST tail running to the cabin radio, finishing the bulletin
  the previous panel broke off at a dash -- not a caption box. Forbidium 061 g1
  `dialogue -> narration`: the pink `SO!` box with a drop capital, which is
  literally the `SO —` caption the last batch reported twice. **Both directions
  are live; read the box's outline before trusting the stored label.**
- **THE JAGGED TAIL IS THIS BATCH'S MOST USEFUL DISCRIMINATOR.** A spiky or
  zigzag tail means a machine's voice and the speaker is off-panel: the TV on
  24-Carat 009 g3/g4, the launch PA loudspeaker on 012 g7, the cabin radio on
  013 g6/g7 and 018 g6/g7. A POINTED tail on the same page means a duck. It
  settled seven groups for one crop each.
- **ONE TEXT CORRECTION, AND IT WAS A DIGIT SWAP BETWEEN TWO SIGNS IN THE SAME
  PANEL.** 24-Carat 016 g4 is `176-761`, not `176-671` -- and `176-671` is the
  OTHER Beagle Boy's placard two feet away. The Beagle Boys wear six different
  numbers across this title (176-716, 176-671, 176-761, 176-617, 176-176,
  176-16?) and the engines transpose them. **Crop every placard; do not read one
  off a montage.** 017 g11's is genuinely unverifiable -- only `176-16` is drawn
  and his own arm covers the rest, so the stored last digit is a reconstruction.
- **THREE MISSED-TEXT ITEMS, ALL OF THEM DRAWN THINGS THE ENGINES CANNOT SEE.**
  24-Carat 024 panel 8: six drawn `$` discs orbiting Scrooge's head, ungrouped --
  and the IDENTICAL device on 010 panel 2 *is* grouped, as one `thought` group
  reading `$ $ $ $ $ $`, which is the model for the add. Forbidium 059 panel 6:
  a big `$` sign-painted on the frosted teller's window. Forbidium 062 panel 5:
  a display `ROAR` across the blast-off that no group covers at all. **The `ROAR`
  is the one to notice -- a full-size sound effect, the sort of thing the engines
  normally catch, simply missing.**
- **THE PLACARD FINDINGS ARE A BUNDLING ARTEFACT AND NEED THE REVIEWER'S WORD.**
  Sixteen of the audit's 23 hits on *The Twenty-four Carat Moon* are the same
  shape: each Beagle Boy's pinned NUMBER and the BEAGLE BOYS INC. legend on his
  sweater are two separate pieces of lettering that the engines put in one box,
  so listing them per instance (as the roster requires) reports them as
  ungrouped. Either split them, as the last review did with the *Shipwrecks*
  plates, or ignore-list the lot -- but it should be decided once.
- **MUCHKALE'S `V` IS GROUPED ON EXACTLY ONE PAGE OF FIVE.** The letter on his
  tunic is drawn on 021, 022, 023, 024, 025 and 026 and is a `background` group
  only on 023. Same call needed: one group a page, or the ignore list.
- **NAMING A SIGNALLING MACHINE IS A JUDGEMENT I MADE TWICE AND WOULD LIKE
  RULED.** *The House on Cyclone Hill*'s warning bell (5 groups) and *The
  Forbidium Money Bin*'s mineral detector (1) both get `other:the ... bell` as
  the speaker of their own `sound_effect`, on the grounds that a bell deliberately
  signalling has a maker in the way an impact does not; drills, engines, slams
  and explosions all stayed `none`. The bell also SPEAKS on *Cyclone Hill* 175
  g2 -- `ALL CLEAR!` in words, off a device Barks draws with a face -- which is
  `dialogue` for the same reason. **If the ruling is that machine noise is always
  `none`, six groups across two titles come out together.**
- **A GYRO STORY IS STILL FREE ACCURACY, AND A TWO-HANDER NEARLY SO.** *Cyclone
  Hill* is Gyro alone (plus the Helper and a turtle) across 4 pages and 31
  groups, every call high, 1.75 images per page. *Forbidium* is Scrooge and Gyro
  and almost nothing else: the pressure suits (Scrooge YELLOW, Gyro GREEN) make
  every moon panel a one-glance call, and it came in at 1.25 images per page --
  **the cheapest title of the batch by a wide margin, and the longest.**
- **SEVEN MEDIUMS ACROSS 143 GROUPS ON *FORBIDIUM* AND 16 ACROSS 266 ON
  *24-CARAT*.** Almost all of them are the same case: a balloon coming off a
  rocket hull with nobody drawn, where the register or the address is the only
  evidence. 061 g3 is the exception and the one to check first -- a traced tail
  that lands past Gyro on Scrooge's hat while the LINE reads as the engineer's.
- `other:` values written this batch. *24-Carat*: `the TV newscaster`, `the
  radio newscaster`, `the launch announcer`, `the Rajah of Eyesore`, `the Texas
  cattle king`, `the rocket designer`, `a rocket workman`, `Muchkale`. **The
  first three are near-duplicates by eye and are NOT the same voice** -- a TV set
  on 008-009, a loudspeaker on the launch pad on 012, a cabin radio on 013 and
  018 -- but they are the exact kind of drift that free text hides, so they want
  a look. *Cyclone Hill*: `Gyro's Helper`, `the turtle`, `the cyclone warning
  bell`. *Forbidium*: `the tattooist`, `a reporter` (used on both 062 and 073),
  `a passer-by`, `the mineral detector bell`, `Gyro's Helper`.
- **A FRAMING DEVICE OPENS AND CLOSES *THE FORBIDIUM MONEY BIN* AND THE CAPTURE
  RECORDS IT.** 058 g1 is the title's only QUOTED caption -- `"WELL, IT ALL
  STARTED WHEN UNCLE SCROOGE..."` -- and 073 panel 4 has a PRESS reporter asking
  what smashed the bin, answered in panel 6 with `WELL, I CAN TELL YOU ONE
  THING!`. The whole story is Scrooge telling it. The box still takes `narrator`,
  per the roster, but the frame is in both notes so the last page reads right.

### Findings to paste into the next run (2026-09-20, seventy-third batch, ALL THREE REVIEWED AND MIRRORED -- batch closed)

**438 groups reviewed across the three titles; 21 speaker corrections (4.8%).**
By title: *The Strange Shipwrecks* **16 of 326 (4.9%)**, *The Fabulous Tycoon*
**5 of 72 (6.9%)**, *Gyro Goes for a Dip* **0 of 40 (0.0%)**. In the nephew
domain, 9 of 71 (12.7%) -- only *Shipwrecks* has nephews. **All 14 of the
pass's applied type overrules held and not one was reversed.** The review added
five groups to *Shipwrecks* and corrected one text. **By the confidence the
pass wrote: high 12 of 387 (3.1%), medium 7 of 31 (22.6%) -- a 7.3x split.**

- **THE RED/GREEN SWAP WAS CONFIRMED, IN THE REVIEWER'S OWN WORDS.** `Colorist
  error: swap red and green` on 030 and `Continuing colorist error fix: green
  is Huey and red is Louie` on 042. Naming from the dialogue against a cap that
  disagreed consistently -- the roster's *Donald's Pet Service* worked example --
  was the right call, and it was worth the two pages of care it took to
  establish. **But 030 g11 was written Huey first and rewritten Louie only when
  042 settled it: do not name a nephew off a cap until the story has had a
  chance to name one in dialogue.**
- **AND THE SWAP IS NOW INCONSISTENT ON EXACTLY ONE PAGE, WHICH IS WORTH A
  SECOND LOOK.** Counting speaker against `cap_colour` over the finished title:
  **30 groups disagree with red=Huey/blue=Dewey/green=Louie and 12 agree**, but
  nine of the twelve are Dewey/blue, which the swap does not touch. **The only
  two groups in the whole title that follow the standard convention are 049 g6
  (Louie/green) and 049 g9 (Huey/red)** -- and both are corrections the review
  made against the pass, reversing the swap on that page alone. Either the
  colourist got 049 right and the error runs everywhere else, or the page was
  worked the other way round by hand. Whichever it is, the corpus-wide
  colourist-error query will now return 030-048 and skip 049.
- **MEDIUM WAS WRONG ALMOST ONE TIME IN FOUR, AND ON *TYCOON* FOUR OF FIVE.**
  22.6% against high's 3.1%. **Every single one of the Tycoon mediums was a
  Scrooge-versus-Donald call made from where the balloon SAT rather than from a
  traced tail** -- 053 g8, 054 g1, 055 g6, 055 g8, and three of the four went
  the way I had ruled out. A balloon whose box spans two ducks is not a
  placement; on a two-duck panel either trace the tail at source resolution or
  write the call at medium and expect to lose it.
- **THE SAME ERROR COST THE ONE DONALD CALL ON *SHIPWRECKS*.** 042 g9 went
  `Donald` -> **Huey**: I gave it to Donald because the balloon sat directly
  over his 1,322px sailor cap, and the speaker was the green-banded boy beside
  him. Being over a figure's cap is not a tail.
- **UNDER-NAMING IS STILL THE LARGEST NEPHEW CLASS: 5 of 9.** 030 g9 and g10,
  044 g0 and g3, 048 g15, all `nephews` sharpened to a name. **030 g9 is the
  instructive one**: I declined it because the only green in the panel was a
  17,640px wall panel the boy's head overlapped, so the scan could not separate
  his band from the scenery, and I cropped the crowns at 4x and still read the
  cap as plain black. The review named him Huey off that crown. **A band that is
  contiguous with same-hue scenery is not an absence -- it is a blob the scan
  cannot split, and the crop has to be tighter than the one that proves the
  crown is bare.**
- **A TRACED TAIL IS NOT PROOF EITHER.** 037 g1 went `Louie` -> **Scrooge**. I
  read the panel at source resolution and described a long spur running
  down-right to the boy by the barrel; the reviewer put it on Scrooge, who is
  between the two. The margin I quoted was against the boy's figure, not against
  a measured head span, which is the roster's standing warning in a new dress.
- **THE ENGINES STORE CAPTION BOXES AND ASIDES WRONGLY AND THE REVIEW AGREED
  EVERY TIME.** All 14 type overrules held: two `SO —` caption boxes stored as
  `dialogue` (034, 044), a story logo stored as `background` (052), five thought
  clouds stored as `dialogue` (037, 054 x3, 056), a thought stored as
  `narration` (047), and five animal or human cries stored as `sound_effect`.
  **The test that predicted every one of the thought clouds: an aside about a
  character who is standing in the panel has to be a thought.** 056 g4 is the
  control -- same joke, drawn pointed tail, Scrooge absent -- and its stored
  `dialogue` was correctly left alone.
- **AN EDITOR ADD CAN DUPLICATE A LOCKED GROUP.** 034 panel 5 ended the review
  with TWO identical `SO —` groups 2px apart on both engines: the pre-existing
  `vision_added` one, locked at speaker `none` by a 2026-08-28 review, and a new
  narration/narrator one added because the locked field could not be changed.
  `vision_apply` refuses an add overlapping an existing box by more than 20%,
  but the editor's own add path does not. Removed here by hand, keeper moved
  into the vacated slot so no other id shifted.
- **`vision_apply` DROPS A TYPE OVERRULE ON AN ALREADY-REVIEWED GROUP WITHOUT
  COUNTING IT.** `_apply_type` returns before it even sets `type_adjudicated`
  when `type_reviewed` is set, so nothing is recorded and the summary line
  reports only what it did change. Three collided this batch. **Check for the
  collision before applying** -- the arithmetic is the tell: 16 overrules
  proposed, 14 reported. The three that collided were all resolved by hand
  afterwards, but only because the hand-back named them: the summary line never
  would have.
- **THE MISSED-TEXT AUDIT'S "ONE GROUP, SEVERAL SIGNS" REPORTS ARE REAL AFTER
  ALL.** I called 041's three plate findings false positives because the plates
  *were* grouped, just bundled two and three to a box. **The reviewer split
  them, which is what the audit was asking for.** A group whose box swallows
  several identical signs is a grouping defect, not an audit artefact.
- **ONE CAPTURE ENTRY WAS MY OWN MISREADING.** 050 panel 3's leftmost plate does
  carry `176-716` above the lettering; I read it at montage scale and wrote
  three plain `BEAGLE BOYS INC.` The capture is corrected -- that is not
  suppressing a finding, it is making the record true, and it is the difference
  between an ignore-list entry and a fix.
- **A GYRO SOLO STORY IS FREE ACCURACY, THIRD TIME RUNNING.** 40 groups, 0
  speaker corrections, 1.75 images per page.
- **NOTHING OUTSTANDING. All three titles close with every gating check clean**
  -- missed-text audit 0 in neither and 0 in one only, engine diff clean, no
  text or type corrections open, and every group speaker_reviewed on both
  engines (312 / 72 / 40). Four items reported at first hand-back were worked
  afterwards: 030's second `$` device, 050's plate text carried across to
  paddleocr by hand (`ai_text` is not mirrored, so a text fix never travels on
  its own), *Gyro* 169 g10's `ROWF!`, and the five stragglers -- 034 g6, 037 g2,
  041 g25, 041 g26, 050 g8, the last three being plates split out of bundles
  during the review. **The one thing left as the review made it** is the 049
  swap exception in the bullet above.
- `other:` values after review: the pass's list stands. The review briefly
  introduced **`other:coastguard captain` on 049 g11**, a near-duplicate of the
  pass's own `other:the coast guard captain` used three times in the same
  page-range; it was folded back in at close. Free-text speaker values get no
  closed-set check, so the only thing that catches one is listing the distinct
  values at hand-back and reading them side by side.

### Findings to paste into the next run (2026-09-20, seventy-third batch, NONE REVIEWED)

**Vol. 22, first time read: *The Strange Shipwrecks* (21pp, 302 groups), *The
Fabulous Tycoon* (5pp, 72) and *Gyro Goes for a Dip* (4pp, 40).** 30 pages, 78
images, **2.60 per page**; per title 2.76 / 2.60 / 1.75. 14 type corrections, 4
groups added, no text corrections, no missed text on the two short titles and
five findings on *Shipwrecks*. Nothing reviewed yet, so everything below is the
pass's own account and the next review should be read against it.

- **THIS TITLE SWAPS RED AND GREEN, AND I HAVE NAMED FROM THE DIALOGUE
  THROUGHOUT.** *The Strange Shipwrecks* splits the cast on 034: g6 sends
  Donald north with HUEY AND DEWEY, g11 sends LOUIE with Scrooge, and g13 then
  addresses Scrooge's companion by name -- `THERE'S RAIDER NICK'S REEF
  LIGHTHOUSE, LOUIE!`. 044 g21 confirms it from the other side (`LOUIE WAS
  SUPPOSED TO SIGNAL US`). But that boy's cap prints RED on every page from 034
  to 042 -- 034 p8 four flashes of `#e61b1f`, 035 p4 and p5, 036 p1 605px, 042
  p2 four more -- and Donald's two print GREEN and BLUE (042 p8: `#009e56`
  270px and `#00a4d5` 264px). So green must be Huey here. Recorded as the
  roster's worked example prescribes: **dialogue names the boy, `cap_colour`
  records the ink**, red=Louie / green=Huey / blue=Dewey for the whole title.
  **030 g11 was written Huey first and rewritten Louie when 042 settled it** --
  which is the cost of naming from the cap before the dialogue has spoken.
- **`leafgrn` IS EMPTY IN VOL. 22 AND THE CAP GREEN IS IN `green`.** Every one
  of the batch's 229 panels reports `leafgrn=0`; the nephew band lives at
  H147-165 (`#009e46`, `#009f48`, `#00a87a`, `#00ab7c`), which is inside
  capscan's `green` window. The roster's standing warning -- that `green` holds
  almost nothing and the cap green lives in `leafgrn` -- is **backwards for this
  volume**. Read the `green` column.
- **THE BAND IS 20-900px AND THREE DECOYS ARE THE SAME INKS, BIGGER.** Scrooge's
  coat is `#e61b1f`, the exact roster red, at 4,000-10,000px; his top-hat band
  is the roster blue `#00a4d5` at 1,300-2,200px; Donald's sailor cap is that
  same blue at 1,300-3,500px. **Area is the whole discriminator**, and a thin
  horizontal blue stripe is a hat band where a rounded blue blob is a sailor
  cap -- that one distinction placed Scrooge against Donald on eight panels of
  *Tycoon* without opening an image.
- **THE HEAD CENSUS MISSED A BAND THAT WAS SITTING INSIDE THE SKULL BOX.** 030
  p4: the right-hand boy carries 88px and 84px of `#e61b1f` at (441,311) and
  (472,290), but `title_heads` reports **no CAP-INK on him at all**, because
  both blobs fall INSIDE the white region rather than above it. The seventy-
  second batch's finding was that the census misses ink ABOVE the skull; this is
  the same tool failing at the other edge. Neither absence is the census's to
  certify.
- **AND I MADE THE FILTERED-VIEW ERROR MYSELF, IN ONE COMMAND.** On 038 I ran
  capscan and grepped for `e61b1f|e61a1f`; it returned nothing and I was about
  to write the caps off. The census then showed `#e6191f` 203px sitting on his
  crown -- **one digit outside my own grep**. The ink was in the output the
  whole time. Quote the scan's own header, never a grep over it.
- **FOUR TYPE CORRECTIONS CAME OFF THE BUBBLE TRAIL, AND ALL FOUR WERE STORED AS
  `dialogue` BY BOTH ENGINES.** 037 g5, 054 g5, 054 g11, 054 g12 and 056 g1 all
  have a cloud edge and a run of separate bubbles. The test that predicted them:
  **an aside about a character who is standing in the panel has to be a
  thought.** 056 g4 is the control -- the same joke, a drawn pointed tail, and
  Scrooge not in the panel -- and its stored `dialogue` was left alone.
- **TWO CAPTION BOXES WERE STORED AS SPEECH.** 034 g5 and 044 g2, both the
  yellow `SO —` box with a drop capital, both `dialogue`; the identical device is
  stored `narration` on 034 g12, 044 g5 and 044 g18 of the same title. A third,
  on 050 panel 3, was grouped by neither engine and is added.
- **A BARE `?` IS ROUTINELY UNGROUPED, AND TWO OF THEM SAT IN ONE SPREAD.** 033
  panel 1 has a `?` cloud over a bare-headed nephew and panel 2 has a PAIR
  flanking Scrooge's head of which the engines grouped only the left one. Both
  added. When a panel shows one drawn device, look for its twin.
- **THREE PROPOSALS COLLIDE WITH AN EARLIER HUMAN REVIEW AND WERE DROPPED
  SILENTLY BY `vision_apply`.** `_apply_type` returns before it even sets
  `type_adjudicated` when `type_reviewed` is present, so nothing at all is
  recorded and only the note survives. They are *Shipwrecks* 046 g7 (`ZOW`,
  reviewed `background` 2026-09-15, read here as a motion streak crossing the
  hull's own lettering), *Gyro* 169 g10 (`ROWF!`, reviewed `sound_effect`
  2026-09-15, where the same dog's `YAP!` and `KI-YI!` on the same page are both
  stored `dialogue`), and *Shipwrecks* 034 g5, whose SPEAKER was reviewed `none`
  2026-08-28 against the pass's `narrator` -- so that group will come out
  `narration`/`none` while every other caption box in the batch is
  `narration`/`narrator`. **Check for this before applying, not after: the
  summary line counts the corrections it made, not the ones it refused.**
- **THE MISSED-TEXT AUDIT HAS A FALSE-POSITIVE CLASS: ONE GROUP COVERING SEVERAL
  IDENTICAL SIGNS.** Three of *Shipwrecks*' five findings are Beagle Boy chest
  plates on 041 that ARE grouped -- g2 covers two plates in one box and g10
  covers three -- so the roster's one-entry-per-instance rule in `visible_text`
  cannot match them and they report as `0 grouped`. Only two of the five are
  real: 030's two `$` devices and 038's third `CHOCOLATE` bar.
- **A GYRO SOLO STORY IS FREE ACCURACY AGAIN** -- 40 groups, 1.75 images per
  page, every speaker either Gyro or one of two dogs, and the helper lamp in
  nearly every panel never speaking. The only work was telling the small black
  dog of 168-169 from the big brown one of 169-170.
- `other:` values written by the pass: `Saltwind McSpray`, `a lighthouse
  helper`, `the lighthouse helpers`, `the detective and Captain Stalwart`,
  `Scrooge's detective`, `Captain Stalwart`, `the chief clerk`, `the office
  nurse`, `the bearded sailor`, `a Moneytubs crewman`, `the Moneytubs' crew`,
  `the Moneytubs' captain`, `a coast guard crewman`, `the coast guard captain`,
  `Longhorn Tallgrass`, `the black dog`, `the brown dog`. **Four
  singular/collective pairs are deliberate and near-duplicate by eye** -- `a
  lighthouse helper` against `the lighthouse helpers`, `a Moneytubs crewman`
  against `the Moneytubs' crew`, and the two dogs -- and want a reviewer's word
  on whether the pairs should be collapsed.

### Findings to paste into the next run (2026-09-20, seventy-second batch, ALL THREE REVIEWED AND MIRRORED -- batch closed)

**406 groups reviewed across all three titles; 39 speaker corrections (9.6%).**
By title: *Water Ski Race* **0 of 57 (0.0%)**, *The Golden River* **39 of 304
(12.8%)**, *The Know-It-All Machine* **0 of 44 (0.0%)**. All four type overrules
held. Four groups were added by the review, all clean, and two of them were the
pass's own missed-text findings. **By the confidence the pass wrote, on the one
title that was corrected: high 38 of 272 (14.0%) against medium 5 of 32
(15.6%)** -- a ratio of 1.1, against 3.6x to 9.3x last batch. **The mediums were
not the problem this time; the confident declines were.**

- **I SUBSTITUTED A HEAD-FILTERED CENSUS FOR A PANEL SCAN AND IT COST 27 OF THE
  39 CORRECTIONS.** Every one of them is a boy left collective under a note
  saying `capscan finds no roster ink anywhere in the panel` or `no band in
  view`, where the review cropped the crown and named him -- four each on 115,
  118 and 121. **The sentence was not true and I never ran capscan to support
  it.** What I actually read was a helper over `title_heads`, and `title_heads`
  only prints CAP-INK when a blob attaches to a white head region it found.
  Worked example, 115 p1: the census lists four beaks and **no cap-ink at all**,
  while `capscan <panel> 15 40000` on the same file returns **109px, 77px and
  73px of clean `#dc1e22` H358.7** at x630-662 and **59px of `#489582` H165** at
  x156-171 -- the two caps the review then named Huey and Louie. The ink sits
  ABOVE the white region the census found, which is exactly where a cap is.
  **A head census answers `is there ink on a head I detected`. It cannot answer
  `is there ink in this panel`, and quoting it as if it could is the same
  filtered-view error the roster already names, in a new dress.**
- **AND EVEN THE RIGHT SCAN WOULD NOT HAVE SETTLED HALF OF THEM.** On 118 p6,
  where the review named Dewey and Louie, a direct capscan at a 15px floor finds
  the blue band **0 in window on 70 blobs** and the green only as **57px and 23px
  of `#51a1a2` at H180.7** -- an off-roster teal, below any usable floor and 70
  degrees from the title's cap green. Nothing a panel scan can do reads that.
  **The seventy-first batch's rule was right and I replaced it with a cheaper
  tool: crop the crown at 3-6x before declining, and treat a scan -- any scan --
  as unable to license an absence on a small cap.**
- **THE SCALLOPED-UNDERSIDE CALL WAS RIGHT, AND I FLAGGED IT CORRECTLY.** The
  three groups I declined because one balloon over a row of boys showed several
  downward points fanning across two or three heads -- 102 g0, 103 g4, 105 g4 --
  **all three held**. The hand-back named them as the first thing to check and
  the check came back clean. A scalloped bottom edge really is not a fan of
  tails.
- **BUT A BALLOON WITH NO DRAWN TAIL AT ALL IS NOT A REASON TO DECLINE.** 098
  g10, where I cropped both ends and the middle and reported that the outline
  closes without a spur, came back **Louie**. Four images went into proving an
  absence that did not license anything. When the tail is not drawn, place the
  balloon against the heads and take the nearest -- do not spend crops proving a
  negative.
- **BOTH GAP-TIP NAMES WERE REVERSED, AND NOTHING WAS LOST BY THE CHORUS RULE.**
  098 g8 and 103 g2 both went `Dewey` -> `nephews`; both rested on a tip landing
  in a gap and the one-head-left rule. On this title the gap rule over-named
  twice and never under-named. **Drop a gap tip to `nephews` rather than to the
  head on its left when the gap is wider than about a quarter of a head.**
- **DONALD AGAINST A BOY WENT WRONG THREE TIMES, IN BOTH DIRECTIONS, AND TWO OF
  THE THREE HAD NO FIGURE DRAWN.** 100 g1 `nephews` -> **Donald**; 106 g2 and 120
  g5 `Donald` -> **nephews**. 120 g5 is a balloon over bare soap suds with nobody
  in frame, where I gave it to Donald because MEN! is his form of address for the
  boys -- and register lost to the reviewer's reading of who was buried where.
  **A voice with no figure under it is `nephews` unless the words name their own
  speaker.**
- **A CAPTION BOX INSIDE A READ-ALOUD SCENE IS THE READER'S VOICE.** 108 g0, the
  box narrating the storybook over the wide panel, went `narrator` -> **Dewey**
  with the type corrected narration -> dialogue: it is the boy reading the tale
  out loud, not the author. 120 g0, `AND BLOW THEY DID!`, went the same way to
  `nephews`. **Two of the eight narrator calls in the title were wrong, and both
  sit next to a character who has been reading or talking for pages.**
- **THE SILHOUETTE I READ AS A CROW IS A NEPHEW IMITATING ONE.** 121 g9
  `CROWK! CROWK!` went `other:a crow` -> **Dewey**, with the reviewer's own note
  `Not Huey or Louie`. The type overrule survived -- it IS dialogue -- but the
  black shape between the two boys is a boy. **Before coining an animal `other:`,
  count the ducks in the panel.**
- **THE FORM-OF-ADDRESS TEST WENT 3 FOR 3 ON DUCK-VERSUS-DUCK AND 0 FOR 1 ON
  WHICH BOY.** UNCA / UNCLE / OH, DONALD settled 172 g4 to Daisy, 114 g7 to a
  boy and 121 g1 to a boy, and all three held as to *whether* it was a nephew.
  121 g1 was still corrected `Huey` -> `Louie`: the test says a boy is speaking,
  never which one. Keep using it, and never let it carry a name.
- **THE TEXT CORRECTION WAS DECLINED AND THAT IS WORTH KNOWING.** 116 g7's
  `WIERD` was adjudicated and `ai_text` keeps the normalised WEIRD, so the
  emphasis markup keyed to the stored text still round trips and needed no
  rework. The precaution paid: had the markup been written against the corrected
  spelling it would have had to be undone.
- **Outstanding: NOTHING. All three titles audit 0 ungrouped.** The review added
  six groups in all: 097's two gauge scales, 105's bin shield, 184 p7's GLUE pail
  label, and -- once the hand-back was readable -- 119 p8's drawn `?` over a
  nephew's head. GLK then ruled the remaining six ignorable and they carry their
  reasons in `missed-text-ignore.txt`: two `$` devices (098's roundel under the
  McDUCK BLDG plate and 102's sun inside a framed painting) and four sets of
  music notes, every one of them a drawn device beside lettering that IS grouped.
- **THE AUDIT'S OWN QUEUE IS UNREADABLE AND THAT COST A ROUND TRIP.**
  `missed_text_queue.py` writes the page and the glyph and parks every line on
  group 0, so the hand-back read `20 102 easyocr 0 missed-text $` and the
  reviewer could not tell what or where it was. **Write the panel and the
  position after the `kind` field** -- `$ | panel 1 | the sun in the framed
  painting | ignore` -- where the parser ignores them, and put the same list in
  the message as a table. The five open items were worked in one pass once they
  were legible.
- **AND ONE OF THE ELEVEN FINDINGS WAS THE PASS INVENTING LETTERING.** 184's
  capture listed `GLUE` twice, for the pail in p7 and again for the one in p8;
  p8's pail is plain yellow with nothing on it. The label was carried over from
  the previous panel on an assumption, and the audit reported it as `2 in the
  art, 1 grouped` for two days. **A capture entry is a claim about the ink on
  the page: do not repeat a label across panels without looking at the second
  one.** That one is removed from the capture rather than ignored, because the
  ignore list is for lettering that is real and not worth a group.

### Findings to paste into the next run (2026-09-20, seventy-second batch, NONE REVIEWED)

**405 groups over 37 pages, 3 titles: *Water Ski Race* (Vol. 19, 6pp, 57),
*The Golden River* (Vol. 20, 27pp, 304) and *The Know-It-All Machine* (Vol. 20,
4pp, 44).** 80 images, **2.16 per page**. 32 groups at low or medium against 373
at high; 1 text correction, 4 type overrules, 11 missed-text findings.

- **THE FORM OF ADDRESS IS A HARD SPEAKER TEST IN BOTH VOLUMES, AND IT BROKE
  THREE NEAR-TIE TIPS.** The boys say **UNCA** Donald / **UNCA** Scrooge; Donald
  says **UNCLE** Scrooge; Daisy says **OH, DONALD** and never UNCA. On *Water Ski
  Race* 172 g4 the tail tips 9px past Daisy's bow and 21px inside a nephew's head
  -- a coin toss on nearness -- and OH, DONALD settles it for her. On *The Golden
  River* 114 g7 the tip lands exactly between Donald and a boy, 30px either way,
  and UNCA SCROOGE takes it to the boy; 121 g1 is the same shape. **Grep the
  title for UNCA before page 1 and the count is free** -- 28 hits on *The Golden
  River*, and every one of them excludes Donald.
- **A TITLE CAN PRINT NO NEPHEW CAP INK AT ALL, AND ONE PANEL SETTLES IT.**
  *Water Ski Race* puts the boys in swim gear under plain WHITE sailor caps for
  all six pages. `title_bands` shows blue at 0-138 blobs per panel and every
  clean ink in the title is the boat hull (#00a4d7 H194), Donald's own cap or the
  flying ski (#e61b1f H358). One panel read at source resolution proved it and
  all 12 nephew groups are collectives -- which is the *cheap* version of an
  absence claim, because the scan and the drawing agree.
- **A SCALLOPED BALLOON UNDERSIDE IS NOT A FAN OF TAILS, AND I CALLED FOUR
  GROUPS COLLECTIVE ON THAT BASIS.** *The Golden River* 102 g0, 103 g4 and 105
  g3 each put ONE balloon over a row of three boys with THREE downward points
  along its lower edge, spread across two or three heads. The roster's chorus
  rule covers exactly that shape, so all three went `nephews`. **If the review
  names them, the finding is that the leftmost point is the tail and the others
  are the balloon's own edge** -- and the leftmost-tail tie-break should be
  applied instead. This is the single biggest block of declines in the batch and
  it is worth checking first.
- **THE 098 ESTABLISHING PAGE COST 9 IMAGES AND FOUR WERE SPENT ON A TAIL THAT
  IS NOT DRAWN.** 098 g10's balloon spans the whole panel over four figures; I
  cropped the left end, then a wider left view, then the right end, before
  accepting that the outline closes without a spur at either. **Crop one wide
  view of a wide balloon's whole underside first.** The rest of that title ran at
  1.8 images per page, so the page is a third of its own overspend.
- **THE COLOURIST CLASH IN *THE GOLDEN RIVER* RUNS OPPOSITE TO LAST BATCH'S.**
  122 g2 and g4 have Scrooge call the firewood boy **LOUIE** twice while the boy
  wears a clean 413px `#e31b20`; six panels later 122 g8's boy, also in clean
  red, is called **DEWEY**. Both are recorded as the disagreement -- name from
  the dialogue, `cap_colour` red as printed. Unlike *Old Froggie Catapult*, the
  naming does NOT hold for a run of pages: 123 g1 and g2 have a clean green and a
  clean red side by side and were read by the convention.
- **VOL. 20 PRINTS A THIRD BAND ON REAL CROWNS THAT IS NEITHER ROSTER INK.**
  `#468173` H165.8 S0.46 (101 p5), `#18a2a5` H182 (110 p6), `#0aa4c5` H190 (111
  p3, 101 p8). It is 55 degrees off this title's cap green (`#4da240` H111) and
  10-15 off its cap blue. Every boy carrying it was named by **elimination
  against the two clean caps in the same panel**, at medium, with `cap_colour`
  left **null** rather than written in from the name.
- **THE CAPS COME OFF INTO THEIR HANDS THREE TIMES, AND THE SCAN STILL FINDS
  THEM.** *The Golden River* 102 p3, 103 p1 and 105 p3 all read as bare crowns
  and put the red, green and blue at chest or hip height (y460-586 on 105 p3)
  where the boys are carrying them. `capsum`-style output at 40-3000px makes this
  obvious in one line: ink low on the panel with white crowns above it is a HELD
  cap, not scenery. It named four groups that a crown-only read would have
  declined.
- **A MACHINE AND AN ANIMAL BOTH TAKE `other:`, AND THE TYPE FOLLOWS THE
  THROAT.** Four type overrules, all sound_effect -> dialogue except one: 121 g9
  `CROWK! CROWK!` (a crow), 186 g1 `WHEEK!` (the bird), 186 g7 `TWEET! TWEET!`
  (Gyro singing) -- and 185 g2 `GLUE`, which is the word lettered on the paint
  pail and is **background**, not a noise. The talking machines in *The Know-It-
  All Machine* are told apart by their tails: the purple answer machine and the
  green thought-reading machine both speak on a **lightning-bolt tail**, and 186
  g5 is the GREEN one relaying the bird's mind while 186 g10 is the purple one.
- **THE ONE TEXT CORRECTION IS A MISSPELLING THE OCR SILENTLY FIXED.** 116 g7's
  art reads **WIERD** at 5x; the stored text had normalised it to WEIRD. Two
  things follow. Barks's own misspellings belong in the searchable text, so it is
  a real correction -- and **`emphasis_markup` is checked against the STORED
  text**, so the markup on that group had to be written with WEIRD and will need
  re-applying once the correction is taken. Expect that whenever a text
  correction and emphasis land on the same group.
- **Missed text, 11 items, none of them a sign the pass overlooked.** Two gauge
  numbers (097 `98`/`97`), four `$` devices (a building plate, a framed painting,
  the bin's shield), three sets of drawn music notes, one drawn `?` (119 p8), and
  the `GLUE` pail label quoted aloud in 184 g8's balloon. The page captures found
  every one of them; the audit's job here was to prove the capture was complete
  rather than to catch an omission.
- **`other:` values written by the pass:** *Water Ski Race* -- `the festival
  announcer`, `a spectator`, `the Queen`. *The Golden River* -- `a McDuck clerk`,
  `Mr. Clerkmore`, `Tony`, `Jocko`, `the doctor`, `a crow`, `a passer-by`, `the
  Money Bin clerks`. *The Know-It-All Machine* -- `the know-it-all machine`, `the
  thought-reading machine`, `the bird`, `a passer-by`. No near-duplicates within
  a title; `a passer-by` is deliberately shared across two titles.

### Findings to paste into the next run (2026-09-19, seventy-first batch, ALL FOUR REVIEWED AND MIRRORED -- batch closed)

**551 groups reviewed across all four titles; 41 speaker corrections (7.4%).**
All 44 type corrections held, and nothing is outstanding. By title: *Milkman*
2/129 (1.6%, and one of those is a group the review added), *Mocking Bird
Ridge* **24/136 (17.6%)**, *Old Froggie Catapult* 8/140 (5.7%), *Dramatic
Donald* 7/146 (4.8%). **By the confidence the pass wrote:
*Mocking Bird Ridge* high 17/122 (13.9%) against medium 6/12 (50.0%);
*Old Froggie Catapult* high 6/130 (4.6%) against medium 2/10 (20.0%);
*Dramatic Donald* high 5/140 (3.6%) against medium 2/6 (33.3%).** Medium is the
worse bet in all three, by 3.6x, 4.3x and 9.3x.

- **I QUOTED THE CENSUS ZERO AND DECLINED, WHICH IS THE SEVENTIETH BATCH'S
  FINDING VERBATIM, IN A BATCH WHERE I HAD READ IT.** *Mocking Bird Ridge* 158
  g0, g1 and g12 carry the pass note `capscan 8-40000 over panel 1 finds no
  cap-sized roster ink on any of the three crowns`; the review named Dewey,
  Louie and Dewey and **set a cap colour on all three**. Same shape on 154 g8
  and g9, where my note quoted `blue 0 blob(s) total` and the review read green
  on both. That is 5 of the 8 under-namings. **The previous batch's rule -- crop
  the crown at 3x+ before declining, every time -- is not optional and quoting
  the header is not compliance with it.** A panel-wide scan and a crown are
  different measurements.
- **AND TWICE I MEASURED THE INK, THEN GAVE IT TO THE WRONG HEAD.** 153 g1's
  note reads `two 93/82px blue slivers at panel x496-540, which sit on the boy
  BEHIND the shouter, not on him` -- the review made the shouter Dewey on that
  very blue. 152 g12 is the same: Donald's cap position was measured, the boy's
  was not, and he came back Dewey. This is the *use the evidence you already
  wrote* class, and here the evidence was in the note being used to decline.
- **THE OVERLAPPING CLOSE-UP INVERTED A PAIR.** *Mocking Bird Ridge* 158 g2/g3
  are two balloons over two heads drawn on top of each other; I traced g2 to the
  red cap and g3 to the blue, and the review swapped both. All three attribution
  swaps in the batch (155 g2 as well) are red-against-blue on a crowded panel.
  The roster says crop at 6-10x when heads overlap; I cropped at 2.1x.
- **ECHOES ARE A ROLE, NOT A COLLECTIVE.** Five groups went `nephews` ->
  **`other:the echoes`** on *Mocking Bird Ridge* (153 g3, 156 g9, 157 g2, 157
  g4, 157 g10). The pass had split the same class inconsistently between
  `nephews` and `off-panel` reasoning. Where a balloon IS the returning echo and
  no figure is under it, the corpus value is now `other:the echoes`.
- **A DEVICE OVER A SILHOUETTE ROW IS NOT AUTOMATICALLY THE BOYS.** 160 g8, the
  drawn `?` over the watching figures, went `nephews` -> `other:Donald and
  Gladstone`. I read a row of small silhouettes as the nephews; they are the two
  adults at long-shot scale. Count the figures before assigning a device.
- **DO NOT COIN AN `other:` FOR A CHARACTER ALREADY ON THE ROSTER.** *Dramatic
  Donald* 032 g14 and 036 g7 were my `other:a drama club member` for the crowned
  figure playing Princess Morningstar; **she is DAISY**, who is a roster name and
  was in the title from 028. Two of the seven corrections are that one mistake.
  Check the roster list before inventing a role.
- **A TWO-HANDED EXCHANGE CAN BE ONE SPEAKER VALUE.** *Dramatic Donald* 029 g1
  and g4, the mutual insults while the two shove each other, both went to
  `other:Donald and Gladstone` -- the same value the *Mocking Bird Ridge* review
  used on 160 g8 and g13. Worth reaching for when a balloon covers a scuffling
  pair rather than picking one of them.
- **THE ONE OVER-NAMING IN *THE MILKMAN* WAS A TAIL I HAD ALREADY DOUBTED.** 149
  g3 (`Dewey`, cap blue) went back to `nephews`; my own note recorded a possible
  SECOND tail dipping toward the red-capped boy and then applied the
  leftmost-tail rule anyway. Where a balloon may carry two tails, the collective
  is the honest answer, not the rule's tie-break.
- **A COLOURIST CLASH DOES NOT TRAVEL ACROSS A CAST CHANGE, AND THAT COST SIX
  NAMES.** *Old Froggie Catapult*: the pass established at 165 g14 that the boy
  Donald sends down -- `GET DOWN THERE, LOUIE, WITH THE HAMBURGER` -- wears a
  RED cap, and then carried `Louie` onto every red cap for the rest of the
  title. The review **kept it on 165 g6/g10 and 166 g0/g5** and **changed 167
  g9/g11, 168 g0/g2 and 169 g4/g5 to Huey**. The break is exactly where the
  story moves from the local frog jump to the state championship at Cattail
  Slough **and a second boy joins the cast**. One boy in frame at 165-166 means
  the address pins him; two boys from 167 means the red cap reverts to the
  convention. **A dialogue naming binds the boy in that scene, not the ink for
  the rest of the title** -- the same shape as the costume and instrument keys
  that do not travel. All six of the pass's blue-cap Dewey calls held.
- **A PLAIN WHITE UPRIGHT BOX IS NOT AUTOMATICALLY NARRATION.** *Old Froggie
  Catapult* 168 g11 went `narrator` -> `other:the barge crowd` and 170 g10 went
  `narrator` -> `Donald`. The pass reasoned from the box style -- this title
  sets its captions in a slanted face with a drop capital, so it read the two
  upright white boxes as a different kind of caption. They are characters
  speaking. Read what the words claim to be before reading the box.
- **`other:` drift to reconcile:** *Dramatic Donald* now carries both
  `other:a drama club member` (3) and `other:another club member` (1, at 030
  g8). Everything else is clean: *Milkman* `the sleeper`, `the night boss`,
  `a dairy worker`; *Mocking Bird Ridge* `the echoes`, `the professor`,
  `Donald and Gladstone`; *Dramatic Donald* `the drama club director` (16),
  `the farmwife actress`, `the theatre orchestra`, `Donald and Gladstone`.
- **Both missed-text findings were real and both were added.** *Milkman* 141 g14
  is the clipped crate stack at the right edge of panel 5 -- lettering the pass
  saw and left out of `visible_text` as too cut off, which is the wrong call:
  transcribe it and let the audit decide. *Mocking Bird Ridge* 160 g13 is the
  drawn `!`, and 160 g0 splits the opening caption out of the merged box the
  pass had flagged in its note rather than fixed.
- **Outstanding: NOTHING.** All four titles are 100% reviewed on both engines
  and match on group count, reviewed count, identified_by count and the
  speaker, cap_colour and confidence distributions. Every type correction is
  confirmed and no text corrections were ever raised. Two loose ends closed on
  GLK's ruling: *The Milkman* 141's `DAISY DAIRY CO.` lines went to
  `missed-text-ignore.txt` -- every copy on the page IS boxed, and the audit
  reports 6 against 4 only because a group holding three copies of one sign
  never counts toward the single-instance tally -- and *Dramatic Donald* 030
  g8's `other:another club member` was normalised to `other:a drama club
  member`, which the review had introduced against the three groups already
  carrying it.

### Findings to paste into the next run (2026-09-19, seventy-first batch, NONE REVIEWED)

**548 groups over 40 pages, 4 titles: *The Milkman*, *Mocking Bird Ridge*,
*Old Froggie Catapult* (all Vol. 19) and *Dramatic Donald* (Vol. 21).**
44 type corrections and NO text corrections. 59 images over 40 pages, **1.48 per
page**; per title 2.20 / 1.40 / 1.30 / 1.00. Nothing else was outstanding
corpus-wide before this batch -- a no-`--title` run of `vision-corrections`
returned exactly these 44 across 460 titles.

- **THE INDOOR/OUTDOOR CAP SPLIT DECIDED THREE OF THE FOUR TITLES, AND I GOT IT
  WRONG ONCE BEFORE CATCHING IT.** On *Mocking Bird Ridge* I ran capscan over
  151 panel 2 -- three boys at a kitchen sink -- got `red 0, green 0, blue 0,
  leafgrn 0 blob(s) total` at window 8-40000, and was about to write a
  title-wide absence. The bush panels from 154 print red, leafgrn and clean blue
  on the same three crowns. **An indoor zero is a fact about the room.** The
  roster already says to check an indoor panel and an outdoor one; this batch is
  what that sentence is for. Same split in *Old Froggie Catapult* (bare-headed
  at home on 161-164 and 170, capped outdoors from 165) and in *Dramatic Donald*
  (bare-headed everywhere, which IS the whole-title answer there).
- **THE BIGGEST BLOB IN THE BLUE BAND WAS FURNITURE OR WEATHER IN THREE TITLES
  OUT OF FOUR.** *Dramatic Donald* 027-028 carry 1,600-4,800px of clean
  `#00a5d5` and every one of them is the LIVING-ROOM SOFA. *The Milkman* fills
  the blue band with a night wash -- `#2b7399`/`#337397`/`#277299` H201 S0.66,
  **123 blobs across the title** -- and the clean roster blue `#00a4d7` prints
  on only three panels in ten pages. *Mocking Bird Ridge* puts the roster blue
  on DONALD's cap in nearly every panel at 1,000-3,400px against a nephew's
  60-460px. Put the blob on a head before it means anything, and use Donald's
  RED BOW TIE to say which head is his.
- **A COLOURIST CLASH WORTH THE FLAG: *Old Froggie Catapult*.** 165 g14 is
  Donald saying `GET DOWN THERE, LOUIE, WITH THE HAMBURGER` to the only boy in
  the panel, and a 4x crop puts red `#e61b1f` 120+134px on that boy's crown. The
  same red-capped boy carries the hamburger, lights the fire and writes the
  S.O.S. across 166, 167, 168 and 169. Recorded as the disagreement on all nine
  groups: named Louie, `cap_colour` red. The second contest boy wears the clean
  roster blue and is Dewey, so only one of the three inks is displaced.
- **THE NAME-GREP MISSED BOTH DIALOGUE ANCHORS IN THIS BATCH.** *Mocking Bird
  Ridge* 154 g7/g9 spell out `HUEY, DEWEY, AND LOUIE` and *Dramatic Donald* 036
  g12 is `NO, LOUIE! IT'LL BE HUEY'S TURN!`; neither appeared in
  `barks-ocr-name-grep`, because the three names are in the dictionary. The
  scan is still worth running for the spellings, but **read the group text for
  addresses yourself** -- 036 g12 is the only individual nephew name in a
  146-group title and it is worth more than every scan put together.
- **A TITLE WITH NO CAP KEY IS NOT A TITLE WITH NO WORK.** *Dramatic Donald*
  came out 146 groups with every nephew collective, and all the effort went on
  telling five adults apart: Donald, Gladstone, Daisy, a human director in a
  blue dress, and the club members. Donald's red bow tie and Gladstone's green
  jacket did it in every panel where both are in costume.
- **THE STROKE-WIDTH SCREEN'S LAST BLOB ON A `!` LINE IS AN ARTEFACT.** Across
  the four titles, every hit of 1.5-2.2 sitting on the final blob of a line the
  screen marked `!` was the balloon outline, and a crop showed the plain weight
  each time (*The Milkman* 142 g4 `DREAMS!` at 1.83, 146 g4 at 2.21). The
  reliable hits are mid-line on `=` lines. Conversely a **baseline above about
  3.2 means the WHOLE group is in the heavy slanted face** -- that is what
  caught *Mocking Bird Ridge* 154 g7, 157 g5 and 159 g4, which take a
  whole-group `[i]`, and it is a cheaper test than looking.
- **CAPTION BOXES IN THESE FOUR TITLES ARE ALL SET IN A SLANTED FACE** with a
  drop capital, so narration takes a whole-group `[i]`. Two exceptions, both
  plain white upright boxes: *Old Froggie Catapult* 168 g11 and 170 g10.
- `other:` values across the batch, listed so the next run can reuse rather than
  coin: *The Milkman* `the sleeper`, `the night boss`, `a dairy worker`;
  *Mocking Bird Ridge* `the professor`; *Old Froggie Catapult* `Catapult`,
  `Comet Tail`, `Comet Tail's owner`, `the contest announcer`, `a rival frog
  owner`, `a Duckburg townsman`, `a Duckburg townswoman`, `the barge crowd`,
  `the tug captain`, `the gar`; *Dramatic Donald* `the drama club director`,
  `a drama club member`, `the farmwife actress`, `the theatre orchestra`. No
  near-duplicates within a title; `a Duckburg townsman` and `the barge crowd`
  are the singular and the mass and are used deliberately.
- **Outstanding at hand-back:** three missed-text items, all on Vol. 19 --
  *The Milkman* 141 g13 (one box over three crate stencils, a boxing question
  rather than missing lettering) and *Mocking Bird Ridge* 160 p5's drawn `!`
  over the watching ducks, grouped by neither engine. Both are in
  `queue-missed.txt` in their out-dirs. *Old Froggie Catapult* and *Dramatic
  Donald* audited clean.

### Findings to paste into the next run (2026-09-19, seventieth batch, ALL THREE REVIEWED AND MIRRORED)

**712 groups over 46 pages, 3 titles. 57 speaker corrections (8.0%)**, 38 of
them in the 134-group nephew domain (28.4%). By title: *The Half-Baked Baker*
15/160 (9.4%), *Dodging Miss Daisy* 12/122 (9.8%), *The Money Well* 30/442
(6.4%). **By the confidence the pass wrote: high 40 of 678 (5.9%), medium 6 of
33 (18.2%)** -- medium is the worse bet again, after one batch where it was not.
7 type corrections, of which 6 held. The review ADDED 13 groups and lengthened
20 more texts the pass had transcribed short.

- **UNDER-NAMING IS THE LARGEST CLASS FOR THE FIFTH BATCH RUNNING: 27 OF 57**,
  and this time it is not close -- 10 of 15 on *Baker*, 10 of 12 on *Daisy*, 7
  of 30 on *Money Well*. **AND THE REVIEWER SET A CAP COLOUR ON ALMOST EVERY
  ONE.** That is the finding. The pass declined those boys having quoted the
  census's own `N blob(s) total` zero -- *Baker* 122 g6 (`red 0 blob(s) total,
  green 0, blue 0`), 123 g6/g7, 128 g0/g1, *Daisy* 137 g1, 138 g7/g8, 140 g9,
  *Money Well* 081 g8/g10 -- and the reviewer then read red, blue or green on
  the same crowns. **A capscan zero over a WHOLE PANEL does not mean a zero on
  the crown: crop the crown at 3x+ before declining, every time.** Quoting the
  header protected the honesty of the note and not the accuracy of the call.
- **A MEASURED TIP IS STILL WORTH LESS THAN A CAP.** Both of *Baker*'s
  attribution swaps were tips the pass had measured at 4x and written into the
  note: 121 g10 (`tip at panel (545,231), INSIDE the right boy's head+beak span
  x528-663`) went Louie -> Dewey, and 124 g7 (`tip at panel (331,164)`) went
  Dewey -> Huey. Same on *Money Well* 075 g6, whose tip was `INSIDE the
  blue-capped boy's head span` and which went Dewey -> Louie. **Where a tip and a
  cap disagree, the cap won every time in this batch -- 5 of 6 attribution
  swaps.**
- **THE PASS'S TWO BIGGEST DECLINES WERE BOTH RIGHT TO BE FLAGGED AND BOTH
  NAMEABLE.** *Baker* 122 p1's offset fan, flagged as a set because two tails
  landed 42px apart over one boy, came back Huey and Dewey. *Daisy* 133 p8's
  wire-cart pile-up, declined because the heads overlap, came back Louie and
  Dewey. In both the pass wrote the geometry into the note and stopped one step
  short.
- **`unknown` IS NOT A VALUE THE PASS SHOULD EVER LEAVE**: 13 of the 57
  corrections are `unknown -> none` or `unknown -> narrator` on groups the pass
  never wrote at all -- background lettering the REVIEW added, which arrives
  with no speaker. Not the pass's error, but it inflates the correction count;
  read it as 44 real speaker corrections, 6.2%.
- **THE PASS TRANSCRIBED THE BEAGLE BOYS' SHIRT PLATES SHORT, TWENTY TIMES.**
  `176-716 BEAGLE BOYS` for `176-716 BEAGLE BOYS INC.`, and once `176-61` for
  `176-617`. The plates are read at montage scale and the last line falls off
  the bottom of the shirt. **A numbered plate needs its own crop like a cap
  does** -- and because the same short text went into `visible_text`, the audit
  reported 14 phantom missed-text items until the captures were corrected.
- **THIRTEEN ADDS THE PASS NEVER SAW, AND ELEVEN ARE SHIRT PLATES OR DRAWN
  DEVICES.** *Daisy* 140 p7 `GUARD` (the lettering on General Snozzie's own
  cap), *Money Well* 069 p1 `$` and 071 p5 `$` (both drawn devices the pass put
  in `objects` instead of `visible_text`), 082 p5 `SOON!`, and eight more
  plates. Every one arrived clean -- background/none, no Copy In residue -- but
  **a prop the pass lists in `objects` is invisible to the audit; if it carries
  letters it belongs in `visible_text`.**
- **AN ADD RENUMBERS THE PAGE AND STRANDS THE LAST QUEUE ENTRY.** All three
  stragglers are the same shape: *Daisy* 140 g11 and *Money Well* 088 g13 are
  the last group on a page that gained one, and *Money Well* 074 g15 is the
  OUCH! type correction whose id moved out from under the queue file, so it is
  still unconfirmed. Regenerate the queues after the reviewer's adds, not
  before.
- `other:` values at close. *Baker*: `a cooking fair judge` (6), `the biscuit
  customer` (3), `the lady customer` (1), `Huey and Louie` (1). *Daisy*: none --
  General Snozzie is canonical. *Money Well*: `a Beagle Boy` (78), `Grandpa
  Beagle` (10), `the tunnel contractor` (2), `a policeman` (1), plus the
  canonical `The Beagle Boys` (1). No near-duplicates; the singular/plural
  Beagle pair is one free-text value against one canonical one.
- **Outstanding at close: NOTHING.** All three titles are 100% reviewed on both
  engines -- 160/160, 122/122, 442/442 -- and match on group count,
  identified_by count and the speaker, cap_colour and confidence distributions.
  The last five items all closed: the three stragglers (*Daisy* 140 g11,
  *Money Well* 069 g3 and 088 g13), the unconfirmed `OUCH!` type correction
  (*Money Well* 074 g15), and the one text correction -- *Money Well* 085 g16's
  easyocr text was the truncated `176-617 BEAGLE` where paddleocr and a 3x crop
  both read `176-617 BEAGLE BOYS INC.`, and until it was lengthened the mirror
  had no counterpart to copy onto, which is why paddleocr sat at 439 against
  easyocr's 440. **The lesson is that a one-group text disagreement silently
  costs you a mirrored group**, and the mirror says so in a WARNING that is easy
  to read past. The two missed-text findings went to `missed-text-ignore.txt` on
  the reviewer's ruling: *Baker* 128's cut-off `JU` ribbon and *Daisy* 131's
  calendar grid. Corpus-wide, nothing outstanding across 460 titles.
- **THE ONE ASYMMETRY LEFT IS A FLAG, NOT A GROUP.** *Money Well* 082 reports
  `easyocr=4 paddleocr=3` hand-added groups: both engines carry the `SOON!`
  caption, but paddleocr had already grouped it, so only easyocr's copy is
  flagged `vision_added`. Group counts and every distribution match. Read that
  audit line as provenance, not as a missing box.

### Findings to paste into the next run (2026-09-19, seventieth batch, NONE REVIEWED)

**712 groups over 46 pages, 3 titles.** 85 images, **1.85 per page**; per title
3.10 / 1.80 / 1.38. 31 nephew names against 77 collectives. **17 of 712 written
at medium (2.4%)**, the rest high. 7 type corrections, 5 added groups, 2 missed-text
findings left for the reviewer. No text corrections anywhere in the batch.

- **THE SPLASH PAGE COST 6 IMAGES AND THE SECOND PAGE 7, AND THAT IS THE WHOLE
  OVERSPEND.** *The Half-Baked Baker* ran 3.10 images a page against 1.80 and
  1.38 for the other two, and 13 of its 31 images went on pages 121 and 122. The
  cause was ITERATION, not difficulty: montage, then a stack, then a re-crop of
  the same panel, then a re-crop of the re-crop. From page 123 the method was one
  montage plus ONE stack built to answer every open question on the page at
  once, and the rate fell to 2.0 and then below 1.5 without a single call
  getting worse. **Build the stack after listing the page's questions, not
  before.**
- **A GAP TIP AT MONTAGE SCALE REVERSED AT 4x.** Baker 121 g10 read as a tip
  leaning at Dewey from the 250px montage; the 4x crop put it at panel (545,231),
  INSIDE Louie's head+beak span x528-663, with Dewey's head ending 64px away.
  The montage is not a measurement of a tip -- it is only the cue to go and
  measure one.
- **A PART CROP MADE ONE BOY OUT OF TWO.** Baker 127 g11: a crop that started at
  panel x400 showed a red-capped boy under the balloon and the note named Huey.
  The whole panel shows TWO boys -- the speaker is bare-headed at x230-490 and
  the 4,154px red cap belongs to a second boy bent double behind him. The name
  came from the dialogue instead (129 g1: DEWEY JUST CAME IN WITH AN ORDER).
  **Crop the whole panel before naming, or crop from the balloon down.**
- **A CAP FACT IS A PER-PANEL FACT AND THE PASS BROKE THE RULE ONCE.** On *The
  Money Well* 072 the note first read "the nephews in this title are drawn
  BARE-HEADED", off two indoor panels. Page 74 draws them in clean red and blue
  outdoors. The note was corrected in place to the per-panel form before apply,
  but the error is the one the roster names: two panels are not a title.
- **RED IS NOT A NEPHEW IN A BEAGLE BOYS STORY.** *The Money Well*'s red band is
  full of the BEAGLE BOYS' red caps, and 074's own census puts clean #e61b1f on
  masked adults. Before reading a red blob as Huey in a Beagle title, check
  whether the head under it is a duck child's.
- **A NAMING LINE BEAT A CLEAN CAP: A CONFIRMED COLOURIST ERROR.** *Money Well*
  080 p5 -- the boy asks a question and Scrooge's reply in the SAME PANEL is
  THAT'S WHERE YOU'RE WRONG, DEWEY!, while the boy is drawn from behind in a
  clean red cap (772px of #e21b20, confirmed at 2.2x). Recorded as the
  disagreement the roster asks for: speaker Dewey, cap_colour red, neither
  corrected to match the other.
- **THE THREE TITLES' OWN KEYS, WORTH CARRYING FORWARD.** *Baker*: `UNCA DONALD`
  on every page and 129's HUEY AND LOUIE, GO RENT... , which with a two-tailed
  balloon named both. *Daisy*: the boys are BARE-HEADED indoors on 131-132 and
  put the caps back on outdoors from 133, and 134 p8 loses them again in the
  pond -- the blue band is empty over half the title for that reason alone.
  *Money Well*: `UNCLE SCROOGE` is Donald and `UNCA SCROOGE` a nephew, holding
  over all 26 pages.
- **TWO TAILS ON ONE BALLOON, MEASURED, ARE TWO SPEAKERS.** *Baker* 129 g6: one
  balloon, tails tipping at panel (588,288) and (683,289), inside the red-capped
  and green-capped boys' head spans, after Donald's previous balloon says HUEY
  AND LOUIE. Recorded as `other:Huey and Louie`. `cap_colour` had to be left
  null and `cap-colour` dropped from `identified_by`, because the field holds
  one colour and the group takes two boys -- **the apply refuses the
  combination, so put the hexes in the note.**
- **AN OFFSET FAN THAT NAMES NOBODY.** *Baker* 122 p1: two balloons, two tails,
  and at 3x BOTH tips land over the same green-capped boy, 42px apart against
  boys 120px apart. Flagged as a set rather than mapped in order.
- **A RECURRING TEAL IN VOL. 19 THAT IS NOT A ROSTER INK.** Measured four times
  across the two Vol. 19 titles on real crowns: #00a69b H176 (Baker 121 p5),
  #27a5ac H183 (Daisy 133 p8), #41a085 H163 (Baker 129 p6), #07a27d H166 (Daisy
  136 p2), all 15-25 degrees off both the cap green H147.7 and the cap blue
  H194. Every one was left as a collective. **A reviewer ruling on this ink
  would convert several collectives at a stroke.**
- **THE AUDIT FLAGGED ELEVEN ITEMS THAT WERE THE PASS'S OWN FORMATTING.** Writing
  `visible_text` as separate tokens for a sound effect the ENGINES hold as one
  group -- WHAM / BAM / BONG / BAM against a single `WHAM\nBAM\nBONG\nBAM` --
  makes the audit report every token as ungrouped. **One `visible_text` entry per
  GROUP as the art draws it, not per word.** Ten of the batch's twelve findings
  evaporated on that fix; the two that survived are real.
- **AN ADD RENUMBERS THE PAGE AND INVALIDATES THE STORED result.json.** Three
  titles, three re-applies, three times the same repair: after `added_groups`
  lands, the out-dir's `result.json` must be re-keyed to the NEW ids before it
  can be applied again. The roster says this about the editor; it is just as
  true of the pass's own adds.

### Findings to paste into the next run (2026-09-19, sixty-ninth batch, ALL THREE REVIEWED AND MIRRORED -- batch closed)

**561 groups over 50 pages, 3 titles.** 87 images, **1.74 per page**; per title
1.88 / 1.50 / 1.60. **24 speaker corrections (4.3%)**, 16 of them in the
54-group nephew domain (29.6%). By title: *City of Golden Roofs* 9/351 (2.5%),
*Getting Thor* 3/37 (8.1%), *The Titanic Ants!* 12/173 (6.9%). **20 of the 21
type corrections held**, and the review proposed none the pass had missed. No
text corrections in the whole batch. The review added **4 groups**, on top of
the 4 the pass added itself.

- **MEDIUM WAS 0 FOR 20, AND HIGH WAS 20 OF 537 (3.7%).** The first batch in
  nine where medium is not the worse bet -- *every* medium the pass wrote
  survived review, on all three titles (17, 0 and 3). **Do not read this as
  medium being safe**: 20 is a small sample and the pass only reached for it
  where it had already written the alternative into the note. What it does say
  is that CASH THE NOTE worked -- the mediums were honest, and the errors were
  all in calls written at high.
- **SIZE STILL DOES NOT SEPARATE THE ROSTER BLUE, AND IT COST 5 OF THE 24.**
  *City* 049 g6 and 060 g5, *Ants* 108 g6 and 109 g1 all went **Donald ->
  Dewey**, and *Ants* 108 g5 went **Huey -> Donald** the other way. On 060 g5
  the note gives the blob size AS the reason -- *"2632px of #01a4d5 -- Donald's
  sailor cap, much the biggest blue in the panel"* -- and it was a nephew's.
  This is the sixty-seventh and sixty-eighth batches' finding landing a THIRD
  time, now across three volumes. **Stop using blue area to tell Donald from a
  boy. The reliable marker in Vols. 19-20 is the RED BOW TIE**, 250-1,700px at
  his neck, present in every close drawing of him and absent from every nephew.
- **UNDER-NAMING IS THE LARGEST SINGLE CLASS FOR THE FOURTH BATCH RUNNING: 7 OF
  24.** *City* 050 g14 (-> Louie) and 058 g11 (-> Dewey); *Ants* 091 g7 (->
  Dewey), 098 g5 (-> Huey), 098 g8 and g10 (-> Dewey), 102 g2 (-> Huey). 058
  g11 is the sharpest: the note quotes **`RED: 0 blob(s) total`** and every
  green in the panel as jungle fill, then declines -- and the reviewer named him
  Dewey off a blue the whole-panel scan never reported. The scan was right about
  the scan and wrong about the boy, again.
- **THE REVIEWER'S OWN CORRECTION CAN CREATE A DUPLICATE NAME, AND NOTHING
  CHECKS FOR IT.** *Ants* 098 p4 came back with **two Louies**: g7 (the
  crouching boy, leafgrn `#4ea53d` 272px+169px) unchanged, and g8 (the
  right-hand boy, `#e61a1f` 195px+74px) corrected `nephews -> Louie` with the
  note *"Colorist error: this should be a green cap and therefore Louie"*.
  Raised before mirroring and settled as **Dewey by elimination**, with the
  printed red kept. **Add to the close-out: count the distinct nephew names per
  panel after a review and before the mirror**, because the mirror copies the
  clash onto the second engine.
- **THAT PANEL ALSO SETTLED THE TWO-REDS QUESTION, AND THE PASS'S CAUTION WAS
  WRONG.** The pass wrote `nephews` on 098 g5 and g8 citing the roster's *two
  nephews printed the same colour tells you nothing about either*. The reviewer
  named both, annotating **"Colorist error: two red caps"**. So the rule is
  narrower than it reads: **two boys in the same roster colour makes the COLOUR
  useless, not the panel** -- the tail still places each speaker, and the third
  boy's clean cap plus elimination still names them all.
- **A ROW OF `$` SIGNS IS LETTERING -- THIRD BATCH RUNNING, AND THE PASS PUT IT
  IN `objects` AGAIN.** The review added both: *Ants* **101 p2** (three signs)
  and **110 p6** (four), each `thought` / Scrooge. Verified against the art at
  1.7x before mirroring; the counts match. This was the sixty-seventh batch's
  finding and the sixty-eighth's, verbatim. **Write them as `added_groups` at
  read time** -- the pass proved on this batch that it can (4 of its own).
- **LIST A REPEATED SIGN ONCE PER INSTANCE, OR THE AUDIT CANNOT SEE IT.** Both
  *City* adds -- 054 p2 and 056 p3 -- are a SECOND and THIRD `HI-FI` crate
  stencil in frames where the pass listed the stencil once in `visible_text`.
  The audit therefore reported the pages as covered. The roster says this in as
  many words and the pass did not do it; 056's is half-hidden behind a boy's
  leg, which is presumably why neither engine grouped it either.
- **A LONE ANIMAL IN A STORY THAT NAMES ITS ANIMAL IS THAT ANIMAL.** *Getting
  Thor* 181 g0 and 182 g1 both went `other:a crow` -> **`other:Old Blackie`**.
  The pass flagged `a crow` against `the crows` as a deliberate singular/plural
  pair; the real answer is that the singular is never anonymous in a title whose
  dialogue names the bird three times. Two of Thor's three corrections are this.
- **A COLLECTIVE `other:` IS A LEGITIMATE VALUE.** *City* 053 g2 went
  `other:the Gung Ho villager` -> **`other:Donald and the Gung Ho villager`** --
  the `SHOELESS PASHLY!` greeting is the two of them shouting it together. The
  pass placed the balloon on the villager's head and never considered that both
  figures carry it, exactly as `other:Donald and the nephews` is used elsewhere.
- **THE ONE TYPE CALL THAT REVERSED WAS READ OFF A MONTAGE.** *Ants* 095 g1,
  the single-word `ANT!`, was moved `dialogue -> thought` on the strength of
  *"a cloud edge and a trail of separate bubbles"* seen at 250px; the review put
  it back. **A balloon-shape call is a drawing test and the montage is not the
  drawing** -- either open the panel or leave the stored type alone. Every other
  type move held, including all 13 machine-playing-a-record moves on *City*.
- **TWO MORE ON ADULT-AGAINST-ADULT AND LONG SHOTS.** *City* 048 g4 went
  `Scrooge -> nephews` (the pass reasoned *"the balloon sits over a shape that
  carries no head; the nearest speaker to its left is Scrooge"* -- nearest is
  not a tail), and 050 g9 went `nephews -> Donald` on the wide river panel where
  heads.py finds no beaks at all. Both are calls made from geometry after the
  art ran out; both would have been better as the collective and the name
  respectively.
- `other:` values at close. *City of Golden Roofs*: `the King of Tangkor Wat`
  (16), `Shoeless Pashly` (13), `a Tangkor Wat villager` (10), `the Gung Ho
  villager` (9), `the hiring agent` (8), `a hunter` (7), `a Tangkor Wat elder`
  (4), `the factory manager` (4), `an employer` (3), `the boy in the gold hat`
  (3), `a man in the job line` (2), `the royal dance master` (2), `Donald and
  the Gung Ho villager`, `the dock porter`, `the man at the sales office
  window`, `the man in the air pipe`. *Getting Thor*: `the crows` (3), `Old
  Blackie` (2). *Ants*: `Doctor Thinknoble` (23), `a picnic guest` (19), `the
  householder` (3), `the picnic steward` (2), `a giant ant`, `Mrs. Goldwad`.
  **The one near-duplicate pair the pass flagged was resolved by renaming, not
  by keeping both** -- `a crow` is gone. `the householder` survived review
  unchanged.
- **Outstanding at close: nothing.** *City* 056 g5, the one group that had never
  been `speaker_reviewed`, was signed off with the pass's call kept (Scrooge,
  `speaker_was` null, so a confirmation and not a correction) and mirrored,
  taking the title to **351/351 on both engines**. *City*'s five drawn music
  notes went to `missed-text-ignore.txt` on the reviewer's ruling -- the bongo
  LETTERING is all real groups and stays, only the wordless notes are
  suppressed -- so all three titles now audit at zero in all three classes.
  Nothing outstanding in corrections across all 460 titles, and all three
  titles match on group count, reviewed count, identified_by count and the
  speaker, cap_colour and confidence distributions.

### Findings to paste into the next run (2026-09-19, sixty-ninth batch, NONE REVIEWED)

**557 groups over 50 pages, 3 titles** -- *City of Golden Roofs* (Vol. 20, 26pp,
349 groups), *Getting Thor* (Vol. 20, 4pp, 37), *The Titanic Ants!* (Vol. 19,
20pp, 171). **87 images, 1.74 per page**; per title 1.88 / 1.50 / 1.60. 21 type
corrections, **0 text corrections**. The pass added **4 groups** itself. Written
at high on 537 of 557 and medium on 20.

- **THE CAP IS A PATCH ON A BLACK CROWN IN BOTH VOLUMES, AND IT IS SMALL.**
  Neither title wears the full coloured crown. *City of Golden Roofs*: a black
  cap with a wedge at the front-left, 8px to 900px -- the smallest that named a
  boy was **8px** (058 p8) and the next **39px** (098-style). *The Titanic Ants!*:
  a quartered cap whose coloured segment is 100-700px. **`title_heads`' default
  floor misses these entirely**: on 056 p1, 056 p6 and 098 p2 the census showed
  NOTHING and `capscan <panel> 8 40000` showed the wedge each time. On a
  patch-cap title, re-run capscan at an 8px floor before writing any absence.
- **AND THE COLOUR IS DULLED AT THAT SIZE.** The wedges that named boys came in
  at `#ca221f` H1.1 (056 p6), `#b93d28` H8.7 S0.78 (098 p2), `#3b96ae` H190
  S0.66 (058 p6), `#2c9f7c` H161.7 (055 p2) and `#d2181d` 8px (058 p8) -- every
  one off the clean band by 5-15 degrees or below the saturation floor, because
  a 2-3px edge is mostly antialiasing. Ranked inside its own panel against a
  clean rival each time. **Do not apply the S0.75 cool-band floor to a wedge of
  under 200px**; apply it to a broad patch with nothing to rank against.
- **A KNOCKED-OFF CAP NAMED A BOY THE CENSUS CALLED BARE-HEADED.** *Titanic Ants*
  102 p2: the boy is drawn bare, and 5214px of `#e61a1f` hangs in the air beside
  him -- his own cap, mid-flight. The scan reported it as an unplaced red blob
  and the head as empty. The roster's WHEREVER IT IS rule, paying out on the
  clearest case yet: **a large red blob beside a bare crown is the cap, not
  scenery**.
- **TWO BOYS IN ONE PANEL PRINTED THE SAME RED AND I DECLINED BOTH.** *Titanic
  Ants* 098 p4: the middle boy carries 174px of `#e8181f` and the far-right boy
  195px of `#e61a1f`, with the third in leafgrn. The tail places the speaker
  cleanly on the middle boy, and the roster's *two nephews printed the same
  colour tells you nothing about either* makes the colour useless, so it went
  `nephews` with `cap_colour: red`. **Flagged for the reviewer: if this is a
  colourist slip rather than a reading error, one of those two is Dewey and the
  call is nameable.** Same shape on the added `?` group in that panel.
- **THE BIGGEST BLUE ON A HEAD IS SCROOGE'S HAT BAND, NOT A CAP.** *City of
  Golden Roofs* puts 1,500-6,700px of `#01a4d5` on Scrooge's top hat in nearly
  every panel, and Donald's sailor cap another 2,000-4,000px -- against a boy's
  100-1,000px wedge. Blue on a head means nothing in this title until the blob
  is placed. Same in Vol. 19: `#01a4d6` H194 on Scrooge's band and Donald's cap.
- **THE DOMINANT RED IN BOTH TITLES IS SCROOGE'S COAT.** `#a04554` H350 S0.57 is
  731 blobs in *City of Golden Roofs* and 355 in *Titanic Ants* -- more than
  every other ink combined. It is a coat, and its saturation is what separates
  it from the cap red at S0.88.
- **THE `UNCLE`/`UNCA` SPLIT IS A CLEAN DISCRIMINATOR IN BOTH TITLES.** Donald
  says UNCLE SCROOGE, the boys say UNCA SCROOGE and UNCA DONALD, without
  exception across 46 pages. It settled *Titanic Ants* 097 p6 (two black
  silhouettes, no cap readable, one speaker each) and 101 g5, and it is worth
  checking at prep on any Vol. 19-20 title.
- **A MACHINE PLAYING A RECORD IS DIALOGUE, AND THAT IS WHERE MOST OF THE TYPE
  WORK WAS.** 13 of *City of Golden Roofs*' 14 type corrections are the hi-fi
  playing Shoeless Pashly's bongo record -- `BOM BOM`, `BOMMITY BOM`, `BOPPITY
  BONGO BONG` and the rest -- all stored `sound_effect` / implied none, all moved
  to `dialogue` with `other:Shoeless Pashly` at medium and `off-panel`. This is
  the juke-box branch of the machine rule, not the motorised-instrument branch.
  The crows' `CAW` and `WAWK` in *Getting Thor* are the same call for the animal
  reason, and *Titanic Ants* 107 p1's `EEK` is a human scream.
- **A CHARACTER DRUMMING ON AN OBJECT KEEPS `sound_effect` AND TAKES THE PLAYER.**
  *City of Golden Roofs* 058 p5: a villager taps his dough in time with the
  music, music notes drawn beside him. Speaker is the man, type unchanged. The
  split against the group above is *reproducing a performance* vs *making a
  noise*.
- **THE PASS ADDED FOUR GROUPS RATHER THAN HANDING THEM OVER.** `ZOW` on *Getting
  Thor* 182 p1 (checked against BOTH prelim files first -- 10 groups each, no
  ZOW) and three drawn `?` marks on *Titanic Ants* 098 p4. Both titles then
  audited at **zero in all three classes**. Worth doing: `added_groups` costs one
  result.json edit and saves the reviewer an add plus a renumber.
- **AND THE AUDIT WILL NOT MATCH PROSE AGAINST A GROUPED GLYPH.** *Titanic Ants*
  102 p4's `?` IS grouped, and writing `a drawn ? over the ant in panel 4` into
  `visible_text` made the audit report it as missing from both engines. Write the
  **exact glyph** for a device that is grouped and prose only for one that is
  not.
- **`crop.py` TAKES FULL-PAGE COORDINATES, NOT PANEL ONES.** Every blob box from
  `capscan` and every span from `title_heads` is in PANEL pixels, so a crop needs
  `origin + panel_xy`, and the origin is `(panel.x0 - pad, panel.y0 - pad)` out
  of the boxes JSON. Getting this wrong returns an empty or displaced crop
  silently; it cost two calls on 048 before the convention was checked.
- **Outstanding at close, and it is the first thing to work:** *City of Golden
  Roofs* has **5 missed-text findings, all drawn music notes** (055 p5, 058 p5,
  058 p8, 059 p3, 059 p6) -- `queue-missed.txt` in the out-dir, parked on
  neighbouring groups. Every one is the class the sixty-eighth batch's reviewer
  put in `missed-text-ignore.txt`; the recommendation is the ignore list, but it
  needs their word. The other two titles are at zero.
- **A DUPLICATE GROUP TO DELETE.** *Titanic Ants* 091 g1 and g2 are the same CAFE
  sign, boxes `x1527-1785 y173-271` and `x1528-1785 y170-271`. g1 was stored
  `dialogue` and has been corrected to `background`; one of the two should go.
- `other:` values written by the pass. *City of Golden Roofs*: `the King of
  Tangkor Wat` (16), `Shoeless Pashly` (13), `the Gung Ho villager` (10), `a
  Tangkor Wat villager` (10), `the hiring agent` (8), `a hunter` (7), `the
  factory manager` (4), `a Tangkor Wat elder` (4), `an employer` (3), `the boy in
  the gold hat` (3), `a man in the job line` (2), `the royal dance master` (2),
  `the man at the sales office window`, `the man in the air pipe`, `the dock
  porter`. *Getting Thor*: `the crows` (3), `a crow` (2). *Titanic Ants*: `Doctor
  Thinknoble` (23), `a picnic guest` (19), `the householder` (3), `the picnic
  steward` (2), `a giant ant`, `Mrs. Goldwad`. **Four pairs to watch, all
  deliberate**: `a crow` against `the crows` (one bird against the flock); `a
  Tangkor Wat elder` against `a Tangkor Wat villager` (the official who
  proclaims against the townspeople); `an employer` / `the hiring agent` / `the
  factory manager` (three separate hiring scenes in one title); and `the
  householder` against `a giant ant` -- the householder is the unseen voice on
  094-095 that sends Annie to the door, and the review may want it renamed once
  the ant household is on the page.

### Findings to paste into the next run (2026-09-19, sixty-eighth batch, ALL FOUR REVIEWED AND MIRRORED -- batch closed)

**597 groups over 48 pages, 4 titles, all Vol. 19.** 99 images, **2.06 per
page**; per title 3.33 / 1.90 / 1.00 / 1.00. **48 speaker corrections (8.1%)**,
38 of them in the nephew domain. By the confidence the pass wrote: **high 16 of
492 (3.3%), medium 29 of 99 (29.3%)** -- medium is the worse bet for the EIGHTH
batch running, and on *The Persistent Postman* it was 5 of 6. All 8 type
corrections confirmed, plus 3 the pass never proposed; no text corrections. The
review ADDED five groups. By title: *Tabu Yama* 14/172, *Wishing Stone Island*
11/129, *Rocket Race* 14/149, *The Persistent Postman* 9/146.

- **I WROTE A TITLE-WIDE ABSENCE AND IT WAS WRONG SEVEN TIMES OUT OF SEVEN.**
  Every one of *The Persistent Postman*'s corrections is `nephews -> a name`
  with a cap colour the reviewer read off the art -- 116 g10/g15/g16, 119 g7/g9,
  120 g13/g14, three reds, three blues and a green. The pass's capture says in
  as many words that **no nephew is named anywhere in this title** and that
  "every red in those panels is Donald's bow tie, the mail car or Rockdust's
  shirt". That sentence went into the notes of every boy on the page and was
  false in all of them. This is the roster's A CAP FACT IS A PER-PANEL FACT
  rule, broken in the most expensive way available: **never write a title-wide
  cap claim into a capture.** It cost seven names and it is the single largest
  finding of the batch.
- **UNDER-NAMING IS THE LARGEST CLASS FOR THE THIRD BATCH RUNNING: 19 of 48.**
  Postman's seven, *Rocket Race* six (073 g4/g5, 075 g11, 076 g13, 079 g3/g4 --
  all "capscan finds NO cap ink on any of the three" written against boys the
  reviewer could see), *Tabu Yama* five, *Wishing Stone Island* one. The scan
  was right every time and the conclusion was wrong every time, which is now
  confirmed across four consecutive batches. Quote the zero, then name him
  anyway if the tail is unambiguous.
- **A PLAIN CAPTION BOX CAN BE DIALOGUE, AND I READ TWO AS NARRATION.**
  *Rocket Race* 072 g0 and g4 are square boxes across the top of the panel with
  no tail, and the pass called both `narrator` with the type left alone. The
  review made both **`other:Professor Sliderule` speaking**, and corrected the
  type `narration -> dialogue` on each -- two of the three type corrections the
  pass never proposed. The workshop conversation runs straight through them.
  **A box with no tail is not automatically the author's voice**; check whether
  the panel's dialogue continues into it.
- **I SWAPPED A CROWD VOICE AND AN ANNOUNCER.** *Rocket Race* 073 g11 went
  `other:someone in the crowd` -> **Donald** and 073 g13 went Donald ->
  `other:the announcer`, in the same two panels. The pass gave the jagged
  loudspeaker balloon to the public-address voice and the plain one to the
  crowd, and had them the wrong way round. Trace which balloon carries the
  jagged edge before assigning either.
- **THE PASS'S OWN MEDIUMS WERE RIGHT ABOUT WHAT WAS UNCERTAIN.** 29 of 99
  mediums corrected against 16 of 492 highs -- a 9x gap, the widest recorded.
  Nine of the 13 medium corrections on *Tabu Yama* carry a note that already
  names the alternative the review took. CASH THE NOTE remains the cheapest
  rule in the roster and the pass is still not obeying it.

- **A TITLE WHERE THE CAP GREEN AND THE FOLIAGE SHARE A BAND COSTS DOUBLE.**
  *Tabu Yama* ran 3.33 images per page against 1.00 for the two titles after
  it, and the whole overrun is one fact: its cap green is leafgrn `#4fa43e`
  H110-119 and its PALMS print `#50943c` at H106.5, six panels in ten. Hue
  ranked nothing, so every green blob needed a head under it and the head
  needed a panel. `docs/cap-scanning.md`'s advice to read the leafgrn column
  is right and was not enough here. **Check the two hues against each other at
  prep**, on one outdoor panel, before budgeting the title.
- **VOL. 19 USES BOTH OF ITS GREENS, AND NOT IN THE SAME TITLE.** *Tabu Yama*
  is entirely the H110 leafgrn form; *Wishing Stone Island* is entirely the
  H147 `#009e46`-`#019e48` form with leafgrn at ZERO on nearly every panel.
  Carrying one title's green band into the next inside this volume will read
  every cap as absent. The palette table below splits them.
- **THE REFERENCE PANEL PAID FOR ITSELF TWICE.** *Tabu Yama* 012 panel 1 puts
  all five in the water in one row with only heads and caps showing, and it is
  what fixed the title: Scrooge's hat band 783px, Donald's cap 2796px and
  Dewey's cap 916px are all the SAME `#01a4d6`, differing only in size. That is
  the sixty-seventh batch's finding confirmed on a third volume -- **size never
  separates the roster blue** -- and having it measured on page 6 of 18 is why
  the later blue calls cost nothing.
- **A TOY HAT IS AN ELIMINATION, NOT AN ABSENCE.** *Wishing Stone Island* has
  one boy in a WHITE TOY SAILOR HAT with a blue toy telescope for the whole of
  081 and 082, so his own cap is not in the drawing at all. The other two print
  blue and green cleanly in the same frames, so he is Huey by elimination --
  and 082 panel 6, where the hat finally comes off, shows him RED. Ten calls
  came off that, with `cap_colour` null throughout because nothing was measured
  on him.
- **A `0 blob` PANEL CAN STILL BE A NAME.** *Tabu Yama* 013 g1 and 018 g5/g7
  are boys with a genuine zero on the crown, named from the other two boys
  printing in the SAME panel. Worth flagging that `identified_by` must NOT then
  claim `cap-colour`: the apply refuses it when `cap_colour` is null, which it
  did three times before this batch would validate. The evidence is the other
  caps, so the list is `balloon-tail` alone.
- **BOTH COLOURIST ODDITIES WERE READ THE OTHER WAY.** *Tabu Yama* 008 g3
  went Huey/red -> **Louie/green** and 024 g5 Dewey/blue -> **Louie/green**, so
  the two-green panel and the LOUIE AND I panel were both the pass mis-placing
  a tail rather than the colourist slipping. Recorded here because the pass
  reported them as printing oddities when they were reading errors.
- **THE ORIGINAL NOTE ON THE TWO ODDITIES, KEPT FOR THE RECORD.** *Tabu Yama* 014 panel 2 puts
  TWO of the three haulers in the same green (one wedge and two wedges, both
  `#4fa456` H124.9) with the third in red -- so the tip there names nobody and
  the group is a collective with `cap_colour` green. And 017 panel 4's speaker
  says **LOUIE AND I** while wearing BLUE, with the only other boy in frame in
  RED. Neither is reconciled; both are in the notes for the reviewer.
- **THE HANDS-CHANGING READING HELD.** *Tabu Yama* 018 g5 and g7 were not
  corrected, so following the two cropped tails against the Guide-Book thread
  was right. The original note:
- **THE EXPLAINING CHANGES HANDS MID-SCENE AND THE TAIL SAYS SO.** *Tabu Yama*
  018: the Junior Woodchucks' Guide Book reader is Dewey, named outright at 017
  g9/g10 and blue-capped through panels 1-4 -- and then panels 5 and 6 put the
  same steam argument on a boy whose crown is blank and on one measured at RED
  `#e8191f` 299px. Both tails were cropped at 5x rather than read at panel
  scale, and they agree with each other. Recorded as drawn. **A thread is not a
  tail**, and this is the case where following the thread would have been
  wrong twice.
- **A CAP ON THE GRASS IS STILL A CAP.** *Wishing Stone Island* 084 panel 5:
  three boys sit in the rain, the left one bare-headed with a RED quartered cap
  lying at his elbow (1853+1851px), the right one still wearing green, the
  middle bare with nothing beside him. That placed two of them and left the
  third by elimination. The roster's WHEREVER IT IS rule, paying out.
- **`YESSIR, UNCA DONALD! YESSIR! YESSIR!` IS A REAL CHORUS.** *The Persistent
  Postman* 115 g2 and 116 g13 are the same line, three times over, from three
  identically saluting boys under one tail. So is *Wishing Stone Island* 087 g7,
  where the single balloon carries THREE separate tails fanning to three
  cleanly-capped boys. The roster's chorus case is about the tails, and these
  are it -- against the stacked pairs on 084 panel 3 and 073 panel 2, which are
  two tails and two speakers.
- **AN ANIMAL'S NOISE IS DIALOGUE AND THAT IS WHERE THE TYPE WORK WAS.** 6 of
  the 8 type corrections are this: *Postman* 117 g7/g11 (the eagle's SNIFF),
  *Tabu Yama* 023 g12 (a lone `!` in a thought bubble over Scrooge, stored
  sound_effect), *Rocket Race* 088 g6 (Donald's YOWCH!, a cry of pain) and 077
  g5/g6 (the kookaburras' YEEK! and YAKK!). The corpus measurement holds: these
  all go sound_effect -> dialogue and none went the other way.
- **A DONALD-SOLO TITLE NAMES NO NEPHEW AT ALL.** *The Persistent Postman* has
  144 groups and not one nephew name: the boys appear only from 115, always as
  a trio, and every red in those panels is Donald's bow tie, the mail car or
  Rockdust's shirt. 1.00 image per page, 0 groups queued at low confidence. A
  title with no cap key and no per-boy line is cheap and should be budgeted so.
- **FOUR `other:` NEAR-DUPLICATE PAIRS OPENED AND WERE CLOSED BY HAND.** The
  review wrote `other:the announcer`, `other:the radio repairman` and
  `other:a Tuku Tiva villager` where the pass had already used a longer or
  shorter spelling for the same person, and the added `?` group arrived as
  `other:the Tuku Tiva medicine man` against the pass's `other:the Tuku medicine
  man`. Eight records were normalised to the spelling already used most in the
  same title. **Free-text names get no closed-set check** and four pairs in one
  batch is the most yet -- list them at close-out every time.
- **THE REVIEW ADDED FIVE GROUPS, FOUR OF THEM DRAWN DEVICES THE PASS HAD ONLY
  DESCRIBED.** The lone `!` on *Wishing Stone Island* 085, the lone `?` on 086,
  the row of `$` signs round Donald's head on 089, `SPUT` on *Postman* 118 and
  the `313` licence plate on 111. The `$` row is the sixty-seventh batch's
  finding repeated verbatim -- **a `$` row is lettering** -- and the pass put it
  in `objects` again. The devices the reviewer judged not worth a group (music
  notes, red impact stars) are now in `missed-text-ignore.txt`.
- `other:` values written by the pass: `Dick the radio repairman`,
  `the Tuku medicine man`, `the Tuku chief`, `a Tuku islander`, `the schooner
  skipper`, `Professor Sliderule`, `Professor Missilebug`, `the airport
  announcer`, `the television announcer`, `someone in the crowd`, `the
  kookaburras`, `a French Legionnaire`, `Mr. Rockdust`, `Mr. Birdmind`, `Miss
  Applecheeks Teengiggle`, `the giant eagle`, `the eaglets`, `a fisherman`, `a
  rustic wife`, `Mrs. Delore`, `a helicopter salesman`. **One near-duplicate
  pair to watch**: `the Tuku chief` against `a Tuku islander` -- the chief
  carries a staff and a green headdress and gives the tribe's ruling, the
  islanders throw the coconuts, so they are deliberately distinct.
- **A STRAGGLER HID BEHIND THE QUEUE TOOL AND THEN BEHIND A SECOND CHECKOUT.**
  *Wishing Stone Island* 085 g16 was unreviewed on BOTH engines and the
  speaker-queue tool reported only the easyocr half -- it writes one entry per
  group, so the second engine is invisible in it. **Check the reviewed COUNT per
  engine, not the queue's length.** The first attempt to clear it then landed in
  the `Prelim-wt` worktree, which sits on a branch predating the batch: that
  copy of 085 has 16 groups and no g16 at all, so the id pointed at a different
  group and the edit went to g0. Group ids move under you, and a second checkout
  on an older branch moves them further -- **confirm the group by its TEXT
  before signing it off, and confirm which checkout you are in.**
- **Outstanding at close: nothing.** 085 g16 was signed off with the pass's
  Huey/red kept (`speaker_was` null, so a confirmation not a correction), which
  closes the batch. Everything else is clean:
  nothing outstanding in corrections across all 460 titles, every missed-text
  audit at zero in all three classes, and all four titles matching on group
  count, reviewed count, identified_by count and the speaker, cap_colour and
  confidence distributions. The mirror wrote 0 pages -- the review was done on
  both engines, so they never diverged.

### Findings to paste into the next run (2026-09-18, sixty-seventh batch, ALL FIVE REVIEWED AND MIRRORED -- batch closed)

***The Mines of King Solomon*: 37 speaker corrections over 369 groups (10.0%), 27
of them in the nephew domain (24.8%).** By the confidence the pass wrote: **high
29 of 345 (8.4%), medium 5 of 15 (33.3%)** -- medium is the worse bet for the
seventh batch running. All 4 type corrections and the 1 text correction confirmed.

***The Tenderfoot Trap*: 7 real speaker corrections over 121 groups (5.8%)**, all
at high because the title has no mediums; a further 4 are the added groups
arriving as `unknown`. 4 of the 16 nephew-domain groups corrected (25.0%). Five
type corrections, one of them a miss the pass never proposed.

**The three one-pagers: 2 speaker corrections between them over 153 groups**, both
in *September Scrimmage* and both an adult role; *Gyro Builds a Better House* and
*August Accident* came back at zero.

**Batch totals: 643 groups, 50 speaker corrections (7.8%)** -- 41 of them real,
the other 9 being added groups arriving as `unknown` -- **and 34 type corrections,
every one confirmed.** 31 of the 137 nephew-domain groups corrected (22.6%). All
five mirrored clean on group count, reviewed count, identified_by count and the
speaker, cap_colour and confidence distributions.

- **A NEPHEW'S CAP IN THIS TITLE PRINTS THOUSANDS OF PIXELS, AND I USED SIZE TO
  CALL IT DONALD'S. SIX TIMES.** `Donald -> the nephew domain` is 7 of the 37 and
  every one of those notes says *"the duck in the blue sailor cap"* with a big
  number attached -- 014 g8 quotes **5686px of `#00a5d5`** and went to Louie; 016
  g0 (also a large blue) went to Dewey; 025 g4, 025 g9 and 015 g16 went to Louie
  and Dewey. The
  palette row I wrote at close of pass says a boy's band is 60-400px against
  Donald's 2,900-9,300px and **that is wrong** -- it was measured off the panels
  where Donald happened to be the only capped duck. **A blue blob of any size has
  to be put on a HEAD, and the head read for beak and body, before it is Donald.**
  The corrected row is in the palette section below.
- **UNDER-NAMING IS AGAIN THE LARGEST CLASS: 16 of 35**, and this time nearly all
  of them are where I quoted a correct zero and stopped. 022 g3's note reads
  `red 0 / green 0 / blue 0 / leafgrn 0 blob(s) total` and the review named Huey;
  015 g12 and g13 carry the same whole-panel zero and came back Louie and Huey;
  016 g7, 017 g8, 023 g4 the same. **The scan was right every time and the
  conclusion was wrong every time.** This is the sixty-sixth batch's finding
  repeated verbatim, so it is now confirmed across two batches: quote the zero,
  then name him anyway if the tail is unambiguous.
- **A GAP TIP IS A NAME MORE OFTEN THAN I ALLOWED.** 011 g13 and g15 were both
  declined on `the tip falls in the gap between` and both came back **Huey** --
  the head to the LEFT of the gap in each case. 010 g11 (gap tip, declined) came
  back Louie, also one head left. Against that, only ONE over-naming in the whole
  title (018 g8 `Huey` -> `nephews`). The sixty-sixth batch's rule -- readable cap
  plus a tip in the gap means collective -- is too strong here; **one head LEFT
  was right 3 times out of 3 and cost nothing the one time the collective held.**
- **TWO ATTRIBUTION SWAPS, BOTH WHERE I NAMED THE BOY WHO WAS READING THE CHART
  RATHER THAN THE BOY THE TAIL POINTED AT.** 011 g16 `Louie`/green -> `Huey`/red
  and 021 g12 `Huey`/red -> `Dewey`/blue. On 011 g16 my own note says the calls
  are *"lettered beside the green-capped boy of g14, who is the one reading the
  lesson chart"* -- I placed the lettering by who was holding the prop, not by
  the tail. Letter position is not a tail.
- **A CALL ANSWERED BY AN ANIMAL IS THE ANIMAL'S.** 008 g14 `Huey` ->
  `other:a gopher`: the `CHEE - CHEE CHEE` in the next panel is the gopher coming
  up, not the boy still blowing. I had read it as the same caller carrying on.
  Ask whether the noise has changed hands before inheriting a speaker across a
  panel break.
- **THE ROWS OF `$` SIGNS ROUND SCROOGE'S HEAD ARE LETTERING AND I PUT THEM IN
  `objects`.** All five groups the review added are that device -- 014 p5, 015 p6,
  016 p4, 019 p3, 024 p3 -- and the missed-text audit was silent on every one
  because `visible_text` never held them. I wrote *"dollar signs"* into `objects`
  on two of those pages, which the audit does not read. The roster already says
  to list drawn devices; **a `$` row is one, and so is every `!`, `?` and money
  device.** They arrived clean otherwise: own `ai_text`, no Copy In residue.
- **THREE ADULT ROLES CROSSED.** 014 g2 `other:a villager` -> `Scrooge` (I gave
  the villager both symbol balloons when the second is Scrooge answering in kind),
  015 g6 `Scrooge` -> `other:the chauffeur` (the `WHOA! HIT THE BRAKE!` shout out
  of the distant car is the driver's, not the passenger's), and 030 g0 `Scrooge`
  -> `other:El Jackal`. On 030 g0 my note says *"both balloons in this panel carry
  tails down-right to the duck"* -- I traced two tails to one figure and gave him
  both lines instead of reading the first as the other man's.
- **THE ONE I WROTE THE NAME INTO THE NOTE AND DECLINED ANYWAY.** *Tenderfoot*
  070 g8: one clean tail, tip at panel x416, landing on the MIDDLE boy of three on
  the fence. The note says so, says the middle boy is the blue-capped one in all
  four readable panels of the title, and then writes `nephews` because the line is
  `WE DON'T KNOW A THING!`. The review made it **Dewey/blue** -- exactly the name
  the note had spelled out. **A plural pronoun is not a chorus; the TAIL COUNT is.
  One tail is one speaker however many the words claim.** The roster's CASH THE
  NOTE rule caught this and I argued myself out of it in the note itself.
- **TWO CAPS PRINTING THE SAME COLOUR DOES NOT MAKE BOTH UNREADABLE.**
  *Tenderfoot* 063 g1 was declined on `two boys printing the same colour name
  neither` -- both rear boys showed blue specks, one 86px and one under the 25px
  floor. The review named **Louie/green**, i.e. the boy's cap was readable and I
  had lumped him in with his neighbour. Judge each cap on its own, which the
  roster already says; the rule about two matching caps is about two caps that
  actually match, not about one readable cap beside an unreadable one.
- **A TIP INSIDE A HEAD SPAN CAN STILL BE THE WRONG HEAD IF THE SPAN IS WRONG.**
  *Tenderfoot* 069 g4 went `Dewey`/blue -> **`Huey`/red**. The note quotes a tip
  at panel x283 and the middle boy's head span as x242-361 -- the tip was real and
  the span was one boy too wide. On a row of three, fix each head's span from the
  drawing BEFORE measuring the tip, and quote both numbers.
- **THE STORY LOGO IS `title`, NOT `background`, AND THE PASS LEFT IT ALONE.**
  *Tenderfoot* 061 g0 came back `background -> title` -- a type correction the pass
  never proposed. Gemini stores the logo either way across the corpus; check the
  splash panel's logo group on every title.
- **THREE ADULT ROLES AGAIN, AND ONE IS A COLLECTIVE.** *Tenderfoot* 062 g4
  `other:an old prospector` -> **`other:old prospectors`** (a huddle answering
  together -- an `other:` role can be plural, and the tail fanned into the group),
  062 g7 `other:an old prospector` -> `other:the contest judge` (the man slumped
  over the bar rail is the judge, not one of the crowd), and 070 g13 `Donald` ->
  `other:Donald and Scrooge`. Between this title and Mines, **8 of the batch's 48
  reviewed corrections are an adult role misread** -- as large a class as the
  nephew attribution swaps and much less looked at.
- **THE TWO GYRO SOLO ONE-PAGERS CAME BACK AT ZERO SPEAKER CORRECTIONS AND 25 OF
  25 TYPE CORRECTIONS CONFIRMED.** That is the sixty-fifth batch's "a Gyro solo
  story is free accuracy" rule holding for a second batch -- but it is only free
  on SPEAKERS. The balloon-drawing question cost 3.25 and 2.75 images per page,
  the two most expensive titles in the batch, and every one of those images was
  earned: all 25 thought/dialogue calls held. **Budget a Gyro one-pager as an
  expensive title with a cheap cast, not as a cheap title.**
- **SEPTEMBER SCRIMMAGE'S 8 NAMED NEPHEWS ALL HELD, WITH `cap_colour` NULL ON
  EVERY ONE.** The title dresses all three boys in identical red football helmets,
  so the names came from the dialogue (`ROUGH, DEWEY!`, the `LOUIE GRABS THE BALL`
  caption) and from scene continuity, and the cap field was left empty rather than
  filled in from the name. **A title with no cap key is not a title where nephews
  cannot be named** -- it is one where the colour field stays null and the
  dialogue does the work.
- **ADULT ROLES ARE THE BATCH'S SECOND-LARGEST ERROR CLASS: 10 of the 50.** Both
  of *September Scrimmage*'s corrections are one (037 g12 `Scrooge` ->
  `other:a spectator`, 040 g8 `other:the referee` -> `other:Jocko`), and with
  Mines' five and Tenderfoot's three that is a fifth of everything the reviews
  moved. Every one is a figure I placed by role or by position rather than by the
  drawing: an official in a striped shirt who is the gorilla, a man at a bar rail
  who is the contest judge, a villager who is Scrooge answering. **Read the figure
  the tail lands on before reading the role the line implies.**
- **`other:` NEAR-DUPLICATE TO WATCH.** The corpus now carries both
  `other:an old prospector` (1) and `other:old prospectors` (1) in
  *The Tenderfoot Trap* -- the review split a huddle answering together off the
  singular I had written. They are genuinely different groups, but the pair is
  exactly the free-text drift the close-out is supposed to catch, so it is
  recorded here rather than silently left.
- **THE COLOURIST CLASH HELD.** After review the title still carries **8**
  name/colour disagreements -- Louie/red 5, Dewey/green 2, Huey/blue 1 -- so the
  convention-flagged reading was kept and the title was NOT remapped.
  `project_per_story_cap_palette` holds for a second batch running.
- Outstanding at close: four of the five titles are fully reviewed with no
  stragglers; *Tenderfoot* is 124 of 125, **061 g0, the story logo, being the one
  group never speaker_reviewed on either engine**. **Mines 019's ungrouped
  foreign-language symbols are still unworked**, the only missed-text finding of
  the batch not resolved; the other four were added and every title's audit is
  clean.

### Findings to paste into the next run (2026-09-18, sixty-seventh batch, NONE REVIEWED)

**634 groups over 49 pages, 5 titles.** 88 images, **1.80 per page**; per title
1.80 / 1.41 / 3.25 / 2.75 / 2.00. 29 type corrections and 1 text correction
proposed; 4 missed-text findings covering 5 groups to add. Nephew calls: 25
named (23 high, 2 medium), 34 collective. Written by the pass, so the
percentages below are proposals, not corrections.

- **A COLOURIST CLASH CAN BE PINNED BY THE DIALOGUE FOUR TIMES AND STILL BE
  HANDLED AS CONVENTION-FLAGGED.** *The Mines of King Solomon* names a
  RED-capped boy LOUIE four independent times -- Scrooge addresses him at 026 g8
  and 027 g5, the 028 p5 caption names him, and 031 g16 greets him by name as he
  steps out of the tunnel drawn in colour with a red cap -- and the ink is clean
  roster red every time (976px `#e31a20` on 026 p6, 754px on 026 p8, 316px on
  027 p3, 1470px `#e51a1f` on 027 p5). Separately Donald calls a GREEN-capped boy
  DEWEY on 009 g2, on 2588px of `#4da33f`. Read on the sixty-sixth batch's
  standing instruction: name from the dialogue inside its own scene, name by
  convention everywhere else, record the printed ink, flag it on the group.
  **This is a stronger clash than *Forbidden Valley*'s and the reviewer may want
  to remap the title; if so, it is one line -- red is Louie, green is Dewey, blue
  is Huey by elimination.**
- **A GYRO SOLO STORY IS FREE ACCURACY ON SPEAKERS AND EXPENSIVE ON TYPE.** The
  sixty-fifth batch's rule held for speakers -- 0 nephew calls, no ambiguity --
  but the two one-pagers cost 3.25 and 2.75 images per page, the most in the
  batch, and produced 25 of its 29 type corrections. The reason is one drawing
  habit: **every Gyro-alone balloon in both titles is a thought cloud with a
  trail of separate bubbles, and Gemini stored a third of them as `dialogue`.**
  The trail is 2-3 circles about 15px across and does not survive page scale, so
  each one needs a 2x crop of the balloon's lower edge. Stack them: two stacks of
  4-5 crops settled ten balloons at a time. Do not take the first panel as the
  title's answer -- *August Accident* 173 p5 has a real POINTED tail on the
  countdown shout in the middle of six thought clouds.
- **WHEN THE STORY PUTS EVERY BOY IN THE SAME HELMET, THE CENSUS RED IS DONALD'S
  BOW TIE.** *September Scrimmage* dresses all the Quackers in identical red
  football helmets, so `title_bands` reports red on almost every panel and none
  of it names anybody. Three separate panels' largest red blobs (037 p8 1354px,
  065-style pairs at 008 p5/p7/p8) are Donald's bow tie, which prints the SAME
  `#e41a20` as a nephew's cap band and sits ~100px below the crown. Place every
  red blob against the head box before reading it as a cap; cap_colour stayed
  null for the whole title.
- **DONALD'S SAILOR CAP IS THE ROSTER BLUE IN BOTH VOLUMES AND IT IS THE LARGEST
  BLUE BLOB IN NEARLY EVERY PANEL.** Vol. 19 `#03a4d7`, Vol. 20 `#00a5d5` --
  identical to Dewey's. Scrooge's top-hat band is the same blue again. In *The
  Mines of King Solomon* the two of them account for 2,000-9,000px of blue in
  panel after panel while a boy's band is 60-400px, so a blue count alone is
  worthless; the discriminator is size and position, not hue.
- **THE COUNTED-INSTANCE CLASS OF MISSED TEXT IS WORTH THE TRANSCRIPTION EFFORT.**
  Listing the OATS sack once per panel in `visible_text` -- six times on
  *Tenderfoot Trap* 066, three on 067 -- is what made the audit report `6 in the
  art, 5 grouped` and `3 in the art, 1 grouped`. Written once per page it would
  have read as fully covered. The 313 licence plate on 061 p1 is the same class
  as Kakimaw 112 and In Old California! 139: a plate on Donald's car, never
  grouped by either engine, and it only reaches the audit because the capture
  wrote it down.
- **A SCAN THAT REPORTS EVERY BAND AT ZERO IS SOMETIMES JUST TRUE.**
  *Tenderfoot Trap* 015-style panels aside, seven of this batch's collectives
  rest on a whole-panel `red 0 / green 0 / blue 0 / leafgrn 0 blob(s) total` --
  061 p1's car interior, 013 p7's aircraft cabin, 015 p7, 022 p3, 023 p7. Where
  that happens the boys are lit by a torch or a cave and nothing chromatic
  survives at all; the tail is then the only evidence and it was usually enough
  to say `nephews` and no more.
- **EMPHASIS BY SLANT WITH NO WEIGHT STEP IS STILL EMPHASIS, AND IT TAKES [b].**
  Three groups this batch are set with a slanted run inside upright lettering and
  measure 0.94-1.02x on the distance transform: *Mines* 011 g14 and 012 g4
  (`CHUG-GLUK`), 016 g10 and 024 g0 (a whole quoted inscription). `[i]` is
  refused for a partial run at apply time -- it cost one validation round-trip on
  031 g11 -- so mark the slanted run `[b]` and say in the note that it is slant,
  not stroke.
- `other:` values written by the pass: `the customer`, `the customer's wife`,
  `Gyro's Helper`, `the mouse`, `the next-door neighbor`, `the cabbage farmer`,
  `the referee`, `Jocko`, `a spectator`, `the contest judge`, `an old
  prospector`, `a prospector`, `the wild burros`, `the burro`, `a clerk`, `the
  glassworks manager`, `a villager`, `the cannery foreman`, `the chauffeur`, `El
  Jackal`, `a Bedouin`, `the panthers and wild cats`. No near-duplicates; the
  two prospector values are deliberately distinct (the Pizen Valley crowd against
  the man who rents the burro).

## Per-volume cap palette

Vol. 21 and **Vol. 23**, three titles read 2026-09-23 (eightieth batch; **ALL
THREE REVIEWED AND MIRRORED**, so the inks below are corrected against the
review). 30 pages, 69 images, **2.30 per page**; per title 2.80 / 1.80 / 2.30.

**THE INKS HELD; THE HEADS THEY WERE PUT ON DID NOT.** Every one of the six
nephew-for-nephew swaps in *The Good Deeds* kept a readable sliver and moved it
to a different boy, so the Vol. 23 palette below is confirmed as printed -- what
failed was the tail-to-head step, which the findings section covers. Two
corrections DO change the reading of a panel: *The Floating Island* 122 g2 and
123 g5 came back Huey where the pass had "Donald alone", so a nephew is present
in two panels the pass read as adult-only -- when a title's boys are capped, a
panel is not "Donald alone" until the whole frame has been swept for a sliver.

**VOL. 23 IS NEW AND ITS INK IS THE SMALLEST YET.** Red `#e61b1f` H358.8, green
`#009d45`-`#009e49` H146-148, blue `#00a5d5`-`#00a6d9` H193-194 -- the same three
hues as Vol. 21 and 22 -- but the construction is a BLACK beanie with the colour
surviving only as a wedge at the cap/skull join, **30 to 600px**. Sweep at 25px
or the title reads as capless: capwide at the default floor found green on a head
and almost nothing else, and it was a 25px re-run that produced the red and blue.

**IN TWO OF THE THREE TITLES THE DECOYS ARE ON THE ADULTS, AND IN THE THIRD THERE
IS NO KEY AT ALL.** Donald wears a blue cap in both *The Floating Island* (from
p120, 1,000-5,100px) and *The Good Deeds* (400-900px) and a red bow tie in all
three; Scrooge's black top hat carries a blue band at 1,000-2,500px. Against
nephew ink of 30-720px that is a 5:1 to 170:1 area ratio -- **area, not hue, is
what separates them in these volumes**.

| title | reference | red | green | blue | construction |
|---|---|---|---|---|---|
| *The Floating Island* (21) | **122 panel 1** -- the three boys lying along the coral shelf, blue at x80-103, green at x225-262, red at x362-381 | `#e61b1f` H358.8, **400px** on a crown (122 p1), 722px at 123 p6, 662px at 126 p4. Decoy: **DONALD'S BOW TIE** at 400-900px in every panel he is in, and Scrooge's coat at 2,000-34,000px | `#009e46`-`#009e47` H146.6-147.0, **349-723px**. THE TRAP: on beach panels the sea prints `#39b18d` H162.0 and a probe box a few pixels too wide reads the cap as sea and returns a false zero -- 123 p6 did exactly that until the box was tightened to the wedge | `#00a5d5`/`#008cba` H193.5-194.8, **124-454px on a boy**. Decoys: **Donald's blue cap** 1,000-5,119px and **Scrooge's top-hat band** 1,000-2,500px | Quartered black beanie. **Indoors on 117-119 the boys are BARE-HEADED** -- capwide at min_area=100 returns 0 roster blobs on 117 p3/p4/p5 and no roster hit at all on 119 p6 -- and capped from 121 once they land. Cast adds `other:a tax collector` (7, three different men from three island groups), `other:the TV announcer` (3), `other:the pilot` (2), `other:the ship's captain` |
| *The Black Forest Rescue* (21) | **n/a -- the nephews are in UNIFORM** | -- | -- | -- | **Junior Woodchuck uniform: identical grey scout caps with a white diamond badge.** `cap_colour` is null on all 143 groups and no crop can help. All three roster hues appear and none is a cap: green `#009e49` H147.7 is the GRASS at 7,000-129,000px, blue `#00a5d5` is the creek (130 p1, 201,462px) and DONALD'S cap (1,000-13,867px), red is his bow tie and the drum lettering. The two keys are the **vocative** (four of them, naming the ADDRESSEE) and the **species split** -- nephews are ducks, the other Woodchucks are pink-faced pigs and dogs. Cast adds `other:a Junior Woodchuck` (24), `other:the official hound` (7), `other:the Woodchuck commander` (3), `other:Joe` (2), `other:the forest animals` (2) |
| *The Good Deeds* (23) | **027 panel 2** -- the three boys facing the reader over the fence, blue at x116-125, green at x341-363, red at x566-578; **035 panel 4** is a second clean row | `#e61a20`-`#e61b1f` H358.2-358.8, **148-573px**. Decoys: **Old Pupp's red sweater** at 27,000-52,000px and Donald's bow tie at 600-1,700px | `#009d45`-`#009f47` H146-148, **53-365px**, the smallest of the three. Decoy: **the grass is the same hue** at 8,700-11,400px, so a blob outside a crown says nothing | `#00a5d5`-`#00a6d9` H193.2-194.1, **108-475px**. Decoys: **Donald's blue cap** 400-900px and the river at 76,116px | **Black beanie, the ink a wedge at the cap/skull join only.** Sweep at 25px. Tails hang a little RIGHT of the speaker's head -- 6, 9, 20, 35, 37 and 44px measured -- which settles the tips that land in gaps. Cast adds `other:the crop-duster pilot` (9), `other:a picnicker` (6), `other:the old man` (4), `other:Old Pupp` (3), `other:the bull` (3), `other:the bakery driver` (2), `other:a motorist` (2), `other:Gwendolyn`, `other:the farmer`, `other:a policeman` |

## Per-volume cap palette

Vol. 21 and Vol. 22, four titles read 2026-09-22 (seventy-ninth batch; **NONE
REVIEWED**, so every figure below is the pass's own and none of it has been
checked). 38 pages, 56 images, **1.47 per page**; per title 2.75 / 1.75 / 1.30 /
1.20.

**THE THREE INKS ARE STILL THE VOLUMES', BUT ONE TITLE MOVES THE GREEN.** Red
`#e61b1f` H358.8 S0.88 and blue `#00a4d5`-`#01a6da` H193.6-194.9 hold in all
four. Green holds at `#009d46`-`#009e48` H146.6-147.5 in the three Vol. 22
titles -- and in *The Lovelorn Fireman* (Vol. 21) Louie's cap prints **`#4ba43f`
H112.9 S0.62**, which is outside capscan's `green` band AND outside the Vol. 21
roster green, so that title reports `green 0` in all 77 panels and only
`capwide.py` finds the cap at all.

**THE AREA STORY IS THE OPPOSITE OF THE USUAL ONE: THE ADULTS HAVE THE BIG INK.**
Every one of these titles puts a roster hue on an adult's head at five to two
hundred times a nephew's area. Scrooge's blue skipper's cap 2,200-2,740px
(*Handy Andy*), his top-hat band 300-2,500px (*Pizarro*), Donald's sailor cap
600-7,200px (*Pizarro*). A Vol. 22 nephew sliver is **12-660px**, and *Pizarro*'s
census had to be re-run at a 6px floor to see it at all.

| title | reference | red | green | blue | construction |
|---|---|---|---|---|---|
| *His Handy Andy* (22) | **n/a -- no nephew cap in the title** | Scrooge's coat and a boat hull; no nephew red anywhere | none | `#00a5d5` **2,209-2,740px, and it is SCROOGE'S**: a blue peaked skipper's cap with a gold badge and a black brim, on 142 p5/p7, 143 p2/p3/p7, 144 p2/p8, 145 p2/p6 | **The boys wear no beanie at all.** White sailor caps on 143 p2, white CHEF'S TOQUES on 145 p1, a soft blue crew cap on 145 p2 -- headgear is costume here and names nobody, so the title's one nephew identification is 143 g4's vocative naming **Louie**. Cast is mostly Barks' non-duck citizens: **`other:Lord Taffrail`**, **`other:Cornwell Mushmore`**, **`other:Colonel Rawcuss Yellowpress`**, **`other:Commodore Leadpipe J. Cinch`**, **`other:Captain Seabug`** |
| *The Firefly Tracker* (22) | **n/a -- Gyro solo** | -- | -- | -- | Gyro, his Little Helper and three merit judges. Every Gyro musing is a scalloped cloud with a bubble trail (184 p8 is the clean one) and the single spoken line, 184 g8, is a plain rounded balloon -- the drawing test carries the page. The trap is 187 p7, where a headline-shaped announcement is a **speech balloon with a tail** onto **`other:the toastmaster`**. Cast adds **`other:a merit judge`** and **`other:a banquet guest`** |
| *The Prize of Pizarro* (22) | **147 panel 5** -- the three boys facing the reader at the park fence, green at x142-283, blue at x345-490, red at x541-684 | `#e61b1f` H358.8, **38-200px on a crown** (147 p5's 38+89px, 165 p6's 205px). Decoys: Scrooge's coat at 2,000-12,400px and Donald's bow tie at 600-1,200 | `#009d46`-`#009e48`, **30-160px**, and the hardest of the three to separate from foliage -- 147 p5's 639px blob is half tree. Only two clean reads in twenty pages | `#00a4d5`/`#00a5d5`, **12-400px on a boy**. Decoys are everywhere: **Scrooge's TOP-HAT BAND** at 300-2,500px and **Donald's sailor cap** at 600-7,200px, both the same hue | **Quartered black beanie; the colour survives only as a sliver**, 12-660px, under the 25px default floor. Sweep at 6px. Cast adds a whole second company of **`other:a mine guard`** (38 groups, green tunics) and **`other:the Royal Guardian`** (9, feathered headdress and magenta cape), plus **`other:the mayor`**, **`other:the city councilmen`**, **`other:the firemen and policemen`**, **`other:a Duckburg citizen`** and **`other:a gold dealer`** |
| *The Lovelorn Fireman* (21) | **116 panel 1** -- the three boys at the wall by moonlight, green at x222-276, red at x366-416, blue at x556-601 | `#e61b1f` H358.8, **69-500px**. Decoy: **fire helmets**, the same red at 500-5,000px on Donald's head in half the panels | **`#4ba43f` H112.9 S0.62 -- NOT the roster green.** Invisible to capscan's bands; use `capwide.py`. Seen on 116 p1 only | `#01a5d6` H193.8, **85-480px** (113 p4/p5, 116 p1/p2) | Black cap with a coloured band. The boys are bare-headed INDOORS (113 p1) and capped outdoors. Cast adds **`other:Chief Feathergoose`** (8), **`other:a magazine photographer`** (3), **`other:a cat`** (3) and **`other:a Duckburg citizen`** (3) -- and **Gladstone**, who from 114 p6 wears a maroon jacket and yellow bow tie that read as Donald's until you find the hair curl |

## Per-volume cap palette

Vol. 22, five titles read 2026-09-22 (seventy-eighth batch; **ALL FIVE REVIEWED
AND MIRRORED**, so the row below is corrected against the review -- in particular
the colourist error claimed for *The Money Champ* does not exist).
42 pages, 68 images, **1.62 per page**; per title 3.17 / 1.25 / 2.00 / 1.00 / 1.27.

**THE THREE INKS ARE THE VOLUME'S AND HAVE NOT MOVED IN FIFTEEN TITLES.** Red
`#e61b1f`-`#e7191e` H358.6-358.8 S0.88, green `#009d46`-`#009e49` **H146-148**
(capscan's `green` band, not `leafgrn` -- `leafgrn` is 0 in every panel of the
batch), blue `#00a4d5`-`#01a6da` H193.8-194.9. What changes per title is the
AREA, and this batch is the widest spread yet recorded: 8px to 2,100px.

**~~NAMES FIRST, INK SECOND -- *THE MONEY CHAMP* SWAPS RED AND BLUE.~~ WRONG,
RETRACTED 2026-09-22 AFTER REVIEW.** 128 panel 2 has each boy answering in turn,
but each one names a BROTHER, not himself -- `DEWEY DOES!` is spoken by the boy
who is not Dewey. **The Vol. 22 convention holds in this title as everywhere
else: red = Huey, blue = Dewey, green = Louie**, confirmed in 18 of the 20 capped
groups after review. Read a name in a balloon as the person being talked about
and trace the tail for the speaker.

**THE DECOYS ARE ON DONALD'S HEAD AND GLOMGOLD'S.** Donald wears a coloured cap
in three of the five titles and it is the roster blue at 500-2,500px -- bigger
than any nephew band in those stories. Glomgold's tam is `#009e47` at ~1,600px,
the nephew green. Scrooge's top-hat band is `#00a4d5` at 300-2,000px throughout.
Add the workmen's green overalls (*The Money Champ* 118) and the managers' green
robes (123-125) and there is no panel in this volume where a hue match alone
names anybody.

| title | reference | red | green | blue | construction |
|---|---|---|---|---|---|
| *Pyramid Scheme* (22) | **104 panel 2** -- the three boys in a row behind Scrooge, green at x378-402, red at x565-572, blue at x613-631 | `#e7191e` H358.6, **23px** in the reference panel and 2,943px where a whole crown faces the reader (104 p5). Decoy: Scrooge's red coat at 4,800-6,600px in the same panels | `#009d46`/`#009d48` H146.8-147.3, **104+116px** in the reference panel, 344-2,714px seen from behind. Decoys: the striped awning at `#00986b` H162 in 3,800px fills, and the `#6fb43c` H112 foliage | `#01a6da` H194.9, **16px+11px** in the reference panel and 39-50px elsewhere -- the smallest nephew ink measured in this project. Decoys: DONALD'S BLUE TAM at 500-2,000px and Scrooge's hat band at 200-450px | **QUARTERED BLACK BEANIE**, the colour surviving only as a sliver where the cap meets the skull. TWO OF THE THREE INKS ARE UNDER CAPSCAN'S 25px DEFAULT FLOOR -- sweep at 6px or the title reads as capless. Readable on 104 and 106 only; 104 p7 is a full silhouette street shot with no ink anywhere. Cast adds nothing; 106 p8 is a FOUR-TAIL chorus of Donald and all three boys |
| *The Wishing Well* (22) | **n/a -- Gyro solo** | -- | -- | -- | Gyro, his Little Helper, a lady customer and a Latin-American revolution. The only thing to read is cloud-against-balloon, and the story turns on it: 178 g6 is a thought cloud and 178 g8 is the same wish shouted with a pointed tail. Cast adds **`other:the lady customer`**, **`other:a rebel soldier`** and **`other:a rebel officer`** |
| *Return to Pizen Bluff* (22) | **113 panel 2** -- the party filing down the hill, red band at x566-621 and green at x728-812 | `#e61b1f` H358.8, **100-1,000px on a crown** (114 p2's 114px is the smallest, 114 p3's ~1,005px the clearest). Decoys: Scrooge's coat at 2,000-2,400px in nearly every panel and Donald's bow tie at 300-800 | `#009e46`-`#009e47`, **200-600px**; 114 p8's 271+95px and 113 p2's 355+249px are the clean reads. Decoy: the green ROOF on 111 p2 at 2,067px | `#00a4d5`, **100-600px on a boy** -- and this is the title where blue is the dangerous one: **DONALD WEARS A BLUE CAP** through the whole modern half at 700-2,500px, with Scrooge's hat band at another 1,000-2,000 | Black cap with a coloured BAND across the front. The 1890s flashback (110-111) has NO nephews at all -- young Scrooge in a blue hat and red neckerchief -- and the caps only start on 112. Indoors at the dinner table (111 p3-p4) the boys are bare-headed and capscan returns nothing. Cast adds **`other:a townsman`**, **`other:the cafe cook`** and **`other:the ghosts`** |
| *Krankenstein Gyro* (22) | **n/a -- Gyro solo** | -- | -- | -- | Gyro, his Helper, a druggist and **`other:Cluckery Cluck`**, a red-combed brown hen who speaks eight times. Every Gyro-alone balloon is a cloud with a bubble trail and every hen noise is her voice, so the only type question in the title is one cluck stored as `sound_effect`. 182 p3 puts a SPEECH BALLOON INSIDE A THOUGHT CLOUD -- the imagined creature quacks -- which is recorded as `other:the turtle-shelled turkey duck` |
| *The Money Champ* (22) | **128 panel 2** -- the three boys answer in turn and NAME THEMSELVES; caps red at x590-595, blue at x673-710, green at x792-836 | `#e61b1f` H358.8, **43px in the naming panel**, 400-800px elsewhere (126 p5's 575px, 131 p4's 815px). **Red is HUEY here, as everywhere.** Decoy: Scrooge's coat, everywhere, at ten times the area | `#009e46`-`#009e47`, **420-813px**; 126 p4's 762px and 128 p2's 420px are the clean reads. Decoys: GLOMGOLD'S TAM at ~1,600px, the workmen's overalls on 118, and the managers' robes on 123-125 | `#00a4d5`/`#01a5d5`, **44+32px in the naming panel** and 100-400px elsewhere. **Blue is DEWEY here, as everywhere.** Decoys: Donald's blue cap and Scrooge's hat band, both larger than any boy's | Black cap with a small coloured flash. Unreadable INDOORS -- the courtroom rows on 120 p6 and the money-sack rows on 122 p2-p3 return no roster ink at an 8px floor, which is why the early nephew calls are all collectives. Cast adds **Flintheart Glomgold** (55 groups, black coat and a green tam with a red pompom), **`other:the Jivaro medicine man`** (13), **`other:a Duckburg citizen`** (25), **`other:the judge`**, **`other:Manager Coot`**, **`other:the oil field manager`**, **`other:the gold mine manager`** and **`other:a surveyor`** |

## Per-volume cap palette

Vol. 21 and Vol. 22, three titles read 2026-09-21 (seventy-seventh batch;
**ALL THREE REVIEWED AND MIRRORED**, so the corrections below are folded in).
41 pages, 79 images, **1.93 per page**; per title 2.80 / 1.50 / 1.71.

**THE ROW THE REVIEW CORRECTED IS *THE FLYING DUTCHMAN*, AND IT IS THE RAIL.**
The three inks all held and no hue call was reversed, but the pass's claim that
095 p8 prints the same red on both boys is wrong: they are red and BLUE, and the
broad band between them is the boat's red rail. 100 g13/g14 also came back with
blue and green swapped. After review the ink disagrees with the name on exactly
one group in 48, and that one (083 g4) is a stale `blue` left on Donald when the
review moved the speaker off a nephew.

**THE THREE INKS ARE THE VOLUME'S, AND THE CONSTRUCTION IS THE TITLE'S -- NOW
OVER TEN TITLES.** Red `#e51b1f`-`#e61b20` H358-359 S0.88, green
`#009a5a`-`#009f47` H146-155 S1.00, blue `#00a5d5`-`#00a7d8` H193-194 S1.00, in
all three titles across both volumes. What changed again is the shape: *The
Master Mover* and *Spring Fever* print a QUARTERED beanie (the *Tracking
Sandy* / *Littlest Chicken Thief* construction), and *The Flying Dutchman*
prints a BAND across the front of a black cap, which is neither the Vol. 22
wedge of *The Twenty-four Carat Moon* nor the quartered cap of its own volume
neighbours.

**AREA IS A PER-DISTANCE FIGURE AND NOT A PER-CHARACTER ONE.** A nephew's cap
ran 43-1,200px over the last two batches; in a close-up it reaches **2,528px**
(*The Master Mover* 083 p1) and **2,869px** (*Spring Fever* 101 p2), squarely
inside Donald's range. Read the construction: two blobs on one crown, or a band
20-40px tall, against Donald's single rounded sailor cap.

**AND THE DECOYS ARE STILL THE ADULTS, PLUS ONE NEW ONE.** Donald's bow tie is
the cap red at 400-1,500px and sits BELOW the skull; Scrooge's coat is the same
ink at 5,000-25,000px; his top-hat band and his sea-going peaked cap are the cap
blue at 1,200-5,600px. New in *The Flying Dutchman*: the **South African naval
officers wear `#00a5d5` uniforms**, so the census hangs cap-blue on every head
in the 090 arrest panels.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Master Mover* (21) | **077 panel 1** -- the three boys in a row under the billboard, red at x1318-1393, a thin blue sliver at x1532-1550, green at x1642-1687 | `#e61b1f` H358.8 S0.88, **145-800px on a crown** seen small, **2,064px** in the 082 p3 close-up. Decoy: Donald's bow tie, the same ink at 220-660px, always below the skull | `#009a5a` H155 at the reference panel, `#009d45`-`#009e47` H146-147 elsewhere, **56-3,142px** (082 p6 is the biggest). Decoys: the moving van's `#01986d` H163 at 47,241px and the grass at `#4faf41` H112 | `#00a5d5`/`#00a6d6` H193-194, **133-2,528px**. Decoys: Donald's sailor cap at 951-4,324px, the SKY at `#2ba8be` H190 in 8,000-9,000px fills on the splash, and the birdcage at `#0081b8` H198 | **QUARTERED BLACK BEANIE**, colour showing as a wedge at the front-right. Unreadable on every far-wide (080 p1 and 084 p8 return no roster ink at any floor) and on the whole of 081 p1, a full silhouette at `red: 0 / green: 0 / blue: 0`. Cast adds **`other:the mynah bird`** (31 groups -- it speaks goat, ape and eagle and is the story's real antagonist), **`other:the naturalist`**, **`other:the moving customer`**, **`other:the bear`**, **`other:the mountain goat`**, **`other:the ape`**, **`other:an eagle`**, **`other:the diamond dealer`**, **`other:a new customer`** |
| *Spring Fever* (21) | **099 panel 6** -- the three boys in the doorway with their kites, red 590px at x100-127, green 1,080px at x237-296, blue 123px at x439-451 | `#e51b20`-`#e61b1f` H358-359, **265-2,869px**; 101 p2 and 104 p1 are the clean reads. Decoy: Donald's bow tie at 130-660px | `#009e46`-`#009f47` H146-147, **116-2,869px** (104 p1's foreground boy is 2,463px across three blobs). Decoys: the trees at `#6fb43d` H95 and the creek bank | `#00a5d5`-`#00a7d8` H193-194, **123-455px on a boy**. Decoys: Donald's sailor cap at 460-2,738px in EVERY panel of the story, and the living-room rug at `#00aeb7` H183 in 7,000px fills | **QUARTERED BLACK BEANIE** as above. Indoors on 097-098 no cap reads at all: capwide returns `red: 2-6 / green: 0-7 / blue: 0-3` with nothing on a crown across five panels, which is why the first two pages are all collectives. Cast adds **`other:the game warden`** (14 groups, grey-green uniform and a badge, hatless from 102 p5 after Donald hooks his hat) and **`other:the drawbridge operator`**. 103 p5 NAMES Louie, and his green cap is measured one panel earlier at 103 p2 |
| *The Flying Dutchman* (22) | **082 panel 2** -- the whole cast on the pier, red / blue / green left to right with Donald at the right for scale | `#e61b1f` H358.8 S0.88, **133-1,000px on a crown**. Decoys: Scrooge's coat at 5,000-34,000px of the IDENTICAL ink, and a red deck rail that runs 500px wide at neck height through 095 p8, 097 p6 and 098 p7 | `#009e45`-`#009f47` H146-147, **120-2,476px** (093 p1's 1,687px is the clearest). Rare: the boys' green cap appears on only eight pages | `#00a4d5`-`#00a5d7` H193-194, **72-678px on a boy**. Decoys: Donald's sailor cap at 1,400-3,500px, Scrooge's top-hat band and his sea-going peaked cap at 1,200-5,600px, and the naval officers' uniforms at the same hue | Black cap with a coloured **BAND across the front**. Readable on about half the pages; the storm, fog and silhouette pages (090 p6-p7, 094 p4/p8, 096 p1/p4/p7, 098 p1, 099 p1) carry no readable cap at all, and there the ADDRESS is the tool: `UNCA SCROOGE` is always a boy, `UNCLE SCROOGE` names nobody. Cast adds **`other:a naval officer`** (7, human, blue uniform and peaked cap -- their `PREPOSTEROUS!` and `EVERYONE ELSE LOOKS FOR IT UP!` is the story's hinge) and **`other:the newsboy`** on the 140 one-pager |

## Per-volume cap palette

Vol. 21 and Vol. 22, four titles read 2026-09-21 (seventy-fifth batch; **ALL FOUR
REVIEWED AND MIRRORED**, so every row below is corrected against the review). 36 pages, 79 images, **2.19 per
page**; per title 3.40 / 1.67 / 2.00 / 1.50.

**THE ROW THE REVIEW CORRECTED IS *NOBLE PORPOISES*, AND IT IS THE TEAL.** The
clean `#00a5d5`-`#01a5d7` H190-194 reads all held; every rim the pass recorded
in the **H160-180** band was wrong about the boy or withdrawn -- `#15a89d` H175,
`#457769` H163 and `#13a9a8` H179. Read that band as UNREADABLE in this title,
not as Dewey's shaded blue. After review the ink disagrees with the name on
exactly one group in thirty-two.

**VOL. 21 DOES NOT HAVE ONE CAP CONSTRUCTION -- IT HAS ONE PER TITLE.** *Noble
Porpoises* prints a thin coloured RIM on a black cap; *Tracking Sandy* and *The
Littlest Chicken Thief*, later in the same volume, print a QUARTERED black
beanie. *Dramatic Donald* (seventy-first batch) prints nothing at all. Derive
the construction in each title from its own reference panel.

**THE THREE INKS ARE STABLE ACROSS THE VOLUME EVEN WHERE THE SHAPE IS NOT:** red
`#e61b1f` H358-359 S0.88, green `#009e46`-`#009f47` H146-149 S1.00, blue
`#00a5d5`-`#00a6d7` H193-194 S1.00. What changes is the AREA and whether the
angle shows any of it.

**AND THE TWO STANDING DECOYS ARE DONALD.** His sailor cap is the same
`#00a5d5` as a nephew's blue at 1,400-6,800px in ONE solid rounded blob, where a
boy's is 43-1,200px and, on the quartered cap, split into two or more blobs on
one crown. His bow tie is the cap red at 1,000-1,500px. Scrooge's coat is the
same red in the thousands.

| title | reference | red (Huey) | green | blue | construction |
|---|---|---|---|---|---|
| *Noble Porpoises* (21) | **037 panel 2** -- the three boys on the beach, red / teal / green rims left to right at head x213-341, x522-642, x724-855; **039 panel 2** repeats it with the third boy's cap turned away | `#e51a1f`-`#e61b1f` H358-359 S0.88-0.89, **130-700px on a rim** (037 p2 144+189px; 039 p7 379+260+95px; 045 p6 264+185+157px). Decoy: Donald's bow tie at 1,000-1,500px | **Louie**, `#4ba33d` H112 / `#47a543` H117.5 / `#3aac41` H124 / `#44a275` H151 S0.58 when shaded, 125-620px. Decoys: the foliage and the living-room wall on 037 p4 at `#3bac40` H123, **12,098px of the exact cap ink** -- a green sliver on any crown in that panel proves nothing | **Dewey**, and it spans H160-194: `#00a5d5`/`#01a5d7` H194 lit (43-600px), `#15a89d` H175 / `#1ea176` H160 / `#13a9a8` H179 shaded -- **and the review says that second set is not blue at all**: three of its four cap moves are rims in the H160-180 band, two of them re-read as GREEN, so treat H160-180 as unreadable here. Decoys: **the sea and sky are the roster blue** in huge fills, Donald's sailor cap is 1,400-4,500px, and the dinghy is `#1ab08b` H165 at 13,700px | Black cap with a thin coloured RIM, a crescent at the back-left of the crown. Readable on nearly every page. Cast adds **`other:the aquarium keeper`**, a human in a blue uniform and peaked cap |
| *The Magic Ink* (22) | **none -- and that is the finding** | -- | -- | -- | **NO NEPHEW CAP IS WORN ANYWHERE IN THIS TITLE -- BUT ONE IS LYING ON A DESK.** The boys are bare-headed in every panel and capwide returns `green: 0` and `blue: 0` on every crown, which is how the pass reached a title-wide collective. **The review named 080 g11 `Huey` off a red nephew cap on Scrooge's desk** (1,190px of saturated red at panel x711-769, y369-409, which the pass had listed and dismissed as furniture). Scan the whole panel for the inks, not the crowns. Scrooge wears a GREEN CHECKED COAT here, not the red one. Cast adds **`other:the ink salesman`** (a human in a black coat, striped tie and orange hat) and **`other:the messenger`**. The visiting `Prof. Umbugg von Pfake` is **Scrooge in a false beard** -- he sets the hoax up by telephone on 077 p3 and gloats on 077 p8 |
| *Tracking Sandy* (21) | **050 panel 8** -- two boys from behind, BLUE-quartered (995px) and GREEN-quartered (2,107px), the cleanest cap read in the volume; **051 panel 4** puts green and red side by side | `#e61b1f`-`#e51b1f` H358-359, **300-1,400px on a crown** (051 p4 616+805px; 052 p4 621+862px) | `#009e46`/`#009f47` H146-149 S1.00, **200-1,800px** (051 p4 654px; 054 p7 2,592px across four blobs). Decoys: the desert scenery at `#008945` H150 and `#00a96c` H158, both in the thousands | `#00a5d5`-`#00a6d7` H193-194, 400-2,400px, always split across segments | **QUARTERED BLACK BEANIE**, alternating black and colour, readable only from behind or in three-quarter. Front-on the crown is solid black with a 50-150px `#039e89` H172 sliver at the edge. **The pass read that as unnameable and the review named 21 such crowns**, so treat the sliver as a prompt to run `capwide` at a 5px floor on the panel, not as a reason to decline -- 054 p1 hides a 136px `#00a5d5` blob that `crowns.py` drops entirely. ~~LOUIE WEARS BLUE HERE~~ -- **THE REVIEW REVERSED THIS.** The mapping is the corpus convention, Dewey/blue 16, Louie/green 12, Huey/red 10, and the only disagreement is on **051 alone**, where Dewey wears green (g4 and g6). 051 p3's address names a boy who never speaks, so it anchored nothing; propagating it to the other nine pages cost 15 of the pass's 18 names. Cast adds **`other:Dread Valley Sandy`** (a human in a green shirt, later a sombrero and false moustache) and **`other:James the chauffeur`**. Donald says `UNCLE SCROOGE`, the nephews say `UNCA SCROOGE`, which separates them all through the title |
| *The Littlest Chicken Thief* (21) | **051 p3 of the title before it** -- this story prints the same construction and the same three inks but names no nephew in its dialogue, so it has no reference of its own | `#e61b1f`/`#d81b1e` H358-359, 272-3,791px (059 p2 is the biggest cap read in the batch) | `#009e46` H147, 325-713px on a crown. Decoys: the shade tree at 1,079-1,864px of the same ink | `#00a5d5`/`#00a6d6` H193-194, 1,051-1,793px across segments | Quartered beanie as above; the edge sliver here prints `#217a69` H168, `#42b3a5` H173 and `#039c57` H158. ~~The 13 names rest on the corpus convention alone~~ -- **THE REVIEW CONFIRMED THE CONVENTION HERE**: Huey/red 23, Louie/green 8, Dewey/blue 6, no disagreement anywhere. Applying the convention rather than the neighbouring title's swap was right; what cost this title was declining, 23 of its 32 corrections. Cast adds **`Grandma Duck`** (a roster value, not an `other:`), **`other:the coyote pup`** and **`other:the chickens`**; the coyote's growls and the hens' squawks are voices and take `dialogue`, while the bare `SNAP` of jaws stays `sound_effect` with the maker named |

## Per-volume cap palette

Vol. 22, three titles read 2026-09-20 (seventy-fourth batch; **none reviewed**).
40 pages, 96 images, **2.40 per page**; per title 3.45 / 1.75 / 1.25.

**THE READABLE WINDOW IS PAGES 008-012 AND THAT IS THE WHOLE STORY.** Only *The
Twenty-four Carat Moon* has nephews in this batch, and from 013 onward the crew
wear bubble space helmets: `crowns.py` returns `NO INK ON CROWN` for **every
head on every page from 013 to 027**, and the helmets are cream, not a roster
colour. Run `crowns.py` over the title at prep and find the window before
reading; on this title fifteen of the twenty pages carry nephews and only two of
them can name one from a cap.

**THE CONSTRUCTION IS A WEDGE, NOT A BAND.** The cap is black with a small
coloured FLASH at the front-left of the crown, 84-450px on a boy at cabin
distance and 1,143px in the one close view (011 p4). It is not the banded cap of
Vols. 5-9 and it does not survive a 60px floor.

**THE DECOYS ARE THE ROSTER INKS AT TEN TO A HUNDRED TIMES THE AREA, AND THE RED
ONE IS EXACT.** Scrooge wears a RED COAT in `#e61b1f` -- the cap red itself --
at 5,000-25,000px; his top-hat band and Donald's sailor cap are both `#00a4d5`
at 1,295-3,521px; the armchairs are `#349bc4` H200 and the boarding ladder
`#3fb07d` H153 S0.64, both close enough to matter. The rocket hull is `#008ab9`
H195, which fills whole panels. **Area is the entire discriminator and a hue
match proves nothing here.**

| title | reference | red | green | blue | construction |
|---|---|---|---|---|---|
| *The Twenty-four Carat Moon* (22) | **012 panel 2** -- two boys at the right of the cabin, blue flash on the near crown and red on the far one, with Scrooge's top-hat band in the same blue at the left for scale; **011 panel 3** is the three-boy check, blue at panel x415-455 and red at x538-580 | `#e61b1f` H358.8 S0.88, **190-1,143px on a crown** (011 p4 top of the ladder 693+450px; 011 p3 445px; 012 p2 1,226px). Decoy: Scrooge's coat, the SAME ink at 5,000-25,000px | `#258e79` **H165 S0.74**, only 111px and only once, on 012 p4's right-hand boy -- the green is nearly absent in this title. Decoy: the boarding ladder `#3fb07d` H153 S0.64 at 1,300-3,200px in tall thin boxes | `#00a4d5` **H194**, 84-423px on a boy (012 p2 84+93px, 011 p3 248+175px). Decoys: Scrooge's top-hat band 1,295px and Donald's sailor cap 2,590px, both the identical ink; the armchairs `#349bc4` H200 | Black cap with a small coloured WEDGE at the front of the crown. **Caps only readable on 011 and 012** -- bare-headed in the living room on 008 and 009, space helmets from 013. Cast adds **Muchkale**, the green Venusian in a blue V tunic, and the TV, radio and public-address voices, all of which carry a JAGGED broadcast tail where a duck gets a pointed one |
| *The House on Cyclone Hill* (22) | **n/a -- Gyro solo** | -- | -- | -- | Gyro, his Helper and a turtle, 4 pages. Thought balloons (cloud edge plus a trail of separate bubbles) against speech (a long pointed tail) is the only thing to read, and both appear on the same page: 172 g1/g2/g3/g5 are clouds and g4/g7 are balloons, all of them Gyro alone. The cyclone warning bell is drawn with a FACE and speaks `ALL CLEAR!` in words on 175 |
| *The Forbidium Money Bin* (22) | **n/a -- no nephews** | -- | -- | -- | Scrooge and Gyro throughout. On earth: Scrooge's black top hat and maroon or red coat against Gyro's green vest, white shirt and yellow hat. **On the moon it is the pressure suits -- Scrooge YELLOW, Gyro GREEN with a yellow-banded helmet** -- which makes 067 and 068 one-glance pages. Cast adds a tattooist, a reporter with a PRESS card, and a passer-by. The story is framed: 058's quoted caption and 073's press question are the same conversation |

## Per-volume cap palette

Vol. 22, three titles read 2026-09-20 (seventy-third batch; **ALL THREE
REVIEWED AND MIRRORED**, so the rows below are corrected against the review). 30 pages, 78 images, **2.60 per
page**; per title 2.76 / 2.60 / 1.75.

**VOL. 22'S CAP GREEN IS IN capscan's `green` BAND, NOT `leafgrn`.** Every panel
of the batch reports `leafgrn=0`. The nephew green runs H147-165 -- `#009e46`,
`#009f48`, `#009e56`, `#00a87a`, `#00ab7c` -- and the roster's usual warning
that `green` holds almost nothing is backwards here.

**THE THREE DECOYS ARE THE ROSTER'S OWN INKS AT TEN TIMES THE AREA.** Scrooge's
coat is `#e61b1f` at 4,000-10,000px against a red band of 80-900px; his top-hat
band is `#00a4d5` at 1,300-2,200px and Donald's sailor cap the same ink at
1,300-3,500px against a blue band of 45-750px. A hat band is a thin horizontal
stripe, often broken into two or three stacked strips; a sailor cap is one
rounded blob. That shape test alone separates Scrooge from Donald without an
image.

| title | reference | red | green | blue | construction |
|---|---|---|---|---|---|
| *The Strange Shipwrecks* (22) | **034 panel 5** -- the whole party on the airfield tarmac, one band each: red apart at left, green and blue saluting beside Donald; 030 panel 1's splash repeats it blue/green/red left to right | `#e61b1f`-`#e61a20` H358.8 S0.88, **80-900px on a crown**; dimmed to `#e6191f` and `#e71920` indoors, and `#d94f41` at 152px on 049 p3 | `#009e46`/`#009f48`/`#00a87a` **H147-165**, 45-900px -- and the `#00a96e` H159 at 17,000-22,000px is a WALL or the sea, never a cap | `#00a4d5`-`#00a5d5` **H194**, 45-750px on a boy; `#00a4b4` H187 is the same band dimmed | black sailor cap carrying small coloured flashes, usually two per crown. **RED AND GREEN ARE SWAPPED FOR THE WHOLE TITLE -- CONFIRMED BY THE REVIEW** (`Colorist error: swap red and green`), except on page 049, where the review applied the standard convention instead and which is the one page to re-check: 034 g6/g11 and g13 and 044 g21 send LOUIE with Scrooge and HUEY with Donald by name, while the art gives Scrooge's boy red on every page 034-042 and Donald's two green and blue. Named from the dialogue, ink recorded as printed. **The caps also come OFF**: the boys are bare-headed indoors at the Money Bin (033 panels 4 and 8, cropped at 3x) and one loses his cap in the brawl (041 p1). Sea decoys: `#349bc4` H200 and `#00a7a8` H180 (water), `#4d998d` H170 S0.50 and `#3fb17e` H153 S0.64 (the Beagle Boys' green jerseys). Cast adds **Saltwind McSpray** and his bearded helpers -- all Beagle Boys under false beards -- **Captain Stalwart**, Scrooge's detective, a chief clerk, an office nurse, and the Moneytubs' and coast guard crews |
| *The Fabulous Tycoon* (22) | **n/a -- no nephews in the title** | -- | -- | -- | Scrooge and Donald only, so the cap question is entirely Scrooge's top-hat band against Donald's sailor cap, both `#00a4d5`; the stripe-versus-blob shape test settles every panel. Cast adds **Longhorn Tallgrass**, a rancher in a green shirt and orange hat who says PODNER and GENTS. **Five thought clouds are stored as `dialogue`** (054 g5/g11/g12, 056 g1) and one genuine speech balloon of the same joke shape is not (056 g4) -- the discriminator is whether Scrooge is standing in the panel |
| *Gyro Goes for a Dip* (22) | **n/a -- no nephews in the title** | -- | -- | -- | Gyro solo. **TWO DIFFERENT DOGS**: a small BLACK one (168 p7, 169 p5 and p6 -- `YIKE!`, `YAP!`, `KI-YI!`) and a big BROWN one in a blue collar (169 p8 through 170 -- `ROWF!`, `KI-YOWL`). They are recorded as separate `other:` values. The helper lamp is in nearly every panel and never speaks. 169 g10's `ROWF!` carries an earlier `type_reviewed` as `sound_effect`, so the title ends up labelling the same animal's bark both ways |

## Per-volume cap palette

Vol. 19 and Vol. 20, three titles read 2026-09-20 (seventy-second batch; **ALL
THREE REVIEWED AND MIRRORED**, so the rows below are corrected against the
review). 37 pages, 80 images, **2.16 per page**; per title 3.33 / 2.07 / 1.00.

**THE ROW THE REVIEW CORRECTED IS *THE GOLDEN RIVER*, AND IT IS THE ABSENCE
CLAIM AGAIN -- 27 OF ITS 39 CORRECTIONS.** The inks below are right; what is
wrong is every sentence in that pass reading that said a panel carried no
roster ink. Those came from a head-filtered census, not from capscan, and on
115 p1 a direct scan at a 15px floor returns 109px of `#dc1e22` H358.7 and 59px
of `#489582` H165 where the census returned nothing. **Read this row as: the
bands are these, the caps are readable on far more panels than the pass
allowed, and no absence in it was ever established.** *Water Ski Race* and *The
Know-It-All Machine* came back with zero corrections and their rows stand as
written.

**THE REFERENCE PANEL FOR VOL. 20 IS *THE GOLDEN RIVER* 103 p3** and it is the
cleanest in the volume: three boys running left to right with one band each on
its own crown, GREEN `#4da240` H111 S0.61, RED `#e41a20` H358, BLUE `#03a4d3`
H194, on the quartered black cap with a coloured front band -- the same
construction *The Money Well* uses. The bands are SMALL, 130-650px on a crown,
so a 25px floor is fine but a 60px one is not.

**THE GREEN THAT IS NOT A CAP IN VOL. 20 IS `#5d963c` AT H98-99**, which fills
whole hillsides and the dollar-patterned wallpaper. It sits 12 degrees BELOW the
cap green rather than above it, which is the opposite side from the Vol. 7 trap,
so ranking hues without checking the area will pick it every time.

**AND THE BIG BLUE BLOB IS NEVER A NEPHEW IN EITHER TITLE.** In *The Golden
River* it is Scrooge's TOP-HAT BAND (700-3,100px) or Donald's sailor cap
(800-3,500px); a nephew's blue is 60-420px, 5-20x smaller. In *Water Ski Race*
it is the boat hull, up to 37,000px.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Water Ski Race* (19) | **none -- and that is the finding** | -- | -- | -- | **NO NEPHEW CAP INK IN THE TITLE.** The boys are in swim gear under plain WHITE sailor caps on all six pages, so all 12 nephew groups are collectives. `title_bands` gives blue 0-138 blobs per panel; every clean ink is the boat hull `#00a4d7` H194 S1.00 (up to 37,771px), Donald's own sailor cap, the flying ski `#e61b1f` H358 or shoreline foliage `#4fb04f` H120. Donald is bare-headed in swim trunks with TWO BLUE STRIPES, which is what separates him from a boy in a close-up (173 p4). Daisy carries the maroon `#a0466a`-`#a1476b` H336-340 S0.53 of the Vol. 19 row throughout. Cast adds the festival announcer, a spectator and the Queen of the Water Festival |
| *The Golden River* (20) | **103 p3** -- three boys in a row, green / red / blue, one clean band each; 111 p3 and 101 p5 repeat it | `#e41a20`-`#e61b1f` H358, **130-1,900px on a crown**; dimmed to `#bc2f36` H357 (109 p3) and `#9c2d18` H6 (119 p4) in shadow, and `#ac3a45` S0.66 at 130px (122 p2) | `#4da240`/`#4da33f`/`#4ca33f` **H111 S0.61**, 130-936px -- and the H98 `#5d963c` is scenery, never a cap | `#03a4d3`-`#00a5d5` **H194**, 60-420px on a boy; `#0aa4c5` H190 is the same cap dimmed | quartered black cap with a small coloured front band. **THREE TIMES THE CAPS ARE OFF AND HELD** (102 p3, 103 p1, 105 p3): the crowns read bare and the ink sits at chest or hip height. **A THIRD BAND ON REAL CROWNS IS NEITHER INK** -- `#468173` H166, `#18a2a5` H182 -- and those boys are named by elimination with `cap_colour` null. **COLOURIST CLASH ON 122**: Scrooge names a RED-capped boy Louie twice and another RED-capped boy Dewey. Scrooge's maroon coat `#a04554` H350 S0.57 fills the red band on most panels and his top-hat band is the roster blue. Cast adds **Mr. Clerkmore** (named at 101 g8), **Tony** the organ grinder and **Jocko** his monkey, a doctor, a crow and two passers-by |
| *The Know-It-All Machine* (20) | **n/a -- no nephews in the title** | -- | -- | -- | A Gyro one-pager set, 183-186. No ducks but Gyro and two human passers-by, so no cap question arises at all and every page cost one image. **THE TWO MACHINES BOTH TALK AND BOTH USE A LIGHTNING-BOLT TAIL**: the PURPLE answer machine (183 g5/g7/g10, 184 g6, 185 g6, 186 g10) and the GREEN thought-reading machine (186 g5, relaying the bird's mind). Tell them apart by the colour of the cabinet the bolt runs back to. Gyro's helper lamp is in nearly every panel and never speaks |

- **Vol. 20 is now well characterised** across *The Money Well*, *City of Golden
  Roofs*, *Getting Thor* and *The Golden River*: the same quartered black cap,
  the same three inks at H358 / H111 / H194, and the same two decoys, Scrooge's
  top-hat band and the H98 scenery green.

Vol. 19 and Vol. 21, four titles read 2026-09-19 (seventy-first batch; **THREE
OF FOUR REVIEWED AND MIRRORED** -- *Old Froggie Catapult* is 138/140 and still
open, so its row is uncorrected). 40 pages, 59 images, **1.48 per page**; per
title 2.20 / 1.40 / 1.30 / 1.00.

**THE ROW THE REVIEW CORRECTED IS *MOCKING BIRD RIDGE*, AND IT IS THE ABSENCE
CLAIM AGAIN.** The row below says the boys are bare-headed indoors on 151 and
cap up outdoors from 154. The first half holds; the second is too late and too
weak. The review named boys on **152 g12 and 153 g1**, and on **158 panel 1**,
where the pass note says no cap-sized roster ink sits on any of the three
crowns, it set blue, green and blue. Read the caps as readable from 152 onward,
and treat every `no ink on the crown` line in that row as a panel-scale scan
that was never followed by a crown crop.

**AND THE CROWNED FIGURE IN *DRAMATIC DONALD* IS DAISY**, not an unnamed club
member -- she plays Princess Morningstar from 032.

**THE CAPS COME OFF INDOORS IN THREE OF THESE FOUR TITLES**, and an absence
claim written off a domestic panel is wrong about the outdoor half of the same
story. Quote the panel, not the title.

**AND THE BLUE BAND'S BIGGEST BLOB IS NOT A CAP IN ANY OF THEM** -- it is a
night wash, a sofa, or Donald's own cap. His red bow tie is the marker that
separates him, exactly as the sixty-ninth batch found.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Milkman* (19) | **148 p2** -- leafgrn, red and clean blue on three crowns in one frame, and the cleanest key in the title; 147 p5 is the same three with the green degraded | `#e61a1f`-`#e71a1f` H358.5 S0.89, 300-1,300px; `#da1c1f` 258+238px at 147 p5 | leafgrn `#4fa43e`/`#51a53f` **H109-110** S0.62, 250-1,200px | clean `#04a5d5`/`#079ecd` **H193.8 S0.98**, 350-850px -- and it prints on only THREE panels in the title | **A NIGHT STORY.** A dark slate wash `#2b7399`/`#337397`/`#277299` H201 S0.66 fills the blue band on **123 blobs** and is the street, the walls and the shadows. A THIRD ink, `#30a77d`/`#2ba87f` **H158-160 S0.71-0.74**, sits on real crowns and is the Vol. 19 teal that is neither roster colour -- it was Louie once (147 p5) and Dewey once (148 p1), each time resolved by elimination against the two clean caps in the same panel. Donald wears a SALMON milkman's cap, not the roster blue, plus his red bow tie. Cast is Donald, the boys, **Mr. McSwine** (the pig in 505, named at 150 g2), a night boss and a dairy worker |
| *Mocking Bird Ridge* (19) | **157 p6** -- the three boys over a hedge, blue / red / green left to right, measured off a 2.3x crop; **156 p1** keys the same three in the bushes | `#e71a1f`/`#d0231e` H358-1.7, 270-570px on a crown | leafgrn `#60a355` H111.5 **S0.48**, 220-460px, and `#589f54` H116.8 S0.47 on 152 p7 | `#05a6ce`/`#02a8db` H192-194 S0.98, **60-280px on a boy** | **THE BOYS ARE BARE-HEADED INDOORS on 151** -- panel 2 reports red 0, green 0, blue 0, leafgrn 0 blob(s) total over three of them at a sink -- and wear the caps outdoors from 154. **DONALD'S OWN CAP IS THE ROSTER BLUE**, `#00a4d7`-`#04a5d6`, **1,000-3,400px**, in nearly every panel, with his red bow-tie pair 300-1,300px directly below it; a nephew's blue is 5-20x smaller. Gladstone is `#5d76aa` H220 **S0.45** (below the cool-band floor) with an orange-red hat `#bc2a19`; Scrooge is `#a04453` H350 S0.57. Scenery green is `#1f9e67`-`#2e9e6c` H153-165 in huge fills |
| *Old Froggie Catapult* (19) | **169 p4** -- a clean red band and a clean roster blue on two boys side by side, with Donald's bow tie between them | `#e61b1f`-`#e51b1f` H358-359 -- **and it is LOUIE's, see below**, 120-1,900px | not printed on any crown in the title | `#00a4d7`/`#03a5d6` H194, on the second contest boy at 400-1,200px | **COLOURIST CLASH, FLAGGED ON NINE GROUPS.** 165 g14 is Donald saying GET DOWN THERE, **LOUIE**, WITH THE HAMBURGER to the only boy in the panel, and that boy wears RED from 165 to 169 -- named from the dialogue, `cap_colour` red as printed. The other contest boy wears the roster blue and is Dewey. All three are bare-headed at home on 161-164 and 170. Donald's cap is the roster blue 650-3,300px plus the bow tie. Big reds in the band are display lettering (161 p4's ROAR, 157-style GONGs) and the fire. Cast adds **Grandma Duck** (tagged, 170 p5-p6), Catapult the bullfrog, a contest announcer, Comet Tail's owner and a bargeload of townsfolk |
| *Dramatic Donald* (21) | **none -- and that is the finding** | -- | -- | -- | **FIRST TITLE READ FROM VOL. 21, AND IT HAS NO CAP KEY AT ALL.** The nephews are bare-headed in every panel, at home and at the theatre, so all 30-odd nephew groups are collective. **THE TRAP IS THE SOFA**: 027 and 028 carry 1,600-4,800px of clean `#00a5d5` H194 and every blob of it is the living-room furniture; the `#00b3d7` H190 from 034 is the prince costume and the stage curtain. The one individual name in 146 groups is 036 g12, `NO, LOUIE! IT'LL BE HUEY'S TURN!`. Cast is Donald (red bow tie), **Gladstone** (green jacket, curly hair), **Daisy** (red hair-bow), a human drama-club director in a blue dress with a black bun, and assorted club members |

- **Vol. 21 is opened but not characterised.** One title is not a volume: all
  that is established is that *Dramatic Donald* prints no nephew cap and that
  its roster-blue objects are furniture and costume. The next Vol. 21 title
  should derive its own reference panel rather than carry this row over.

Vol. 19 and Vol. 20, three titles read 2026-09-19 (seventieth batch; **ALL
THREE REVIEWED AND MIRRORED**, so the rows below are corrected against the
review).

**THE ROW THE REVIEW CORRECTED IS EVERY 'no ink on the crown' CLAIM.** 27 of
the batch's 57 speaker corrections are boys the pass left collective after
quoting a whole-panel capscan zero, and the reviewer set red, blue or green on
almost all of them. The bands below are right about the inks and were read at
the wrong scale: crop the crown, do not scan the panel. 46 pages, 85 images, **1.85 per page**; per title 3.10 / 1.80 / 1.38.

**THE BEAGLE BOYS WEAR RED CAPS.** In *The Money Well* the red band is theirs,
not Huey's, on nearly every panel they appear in -- clean #e61b1f on masked
adult heads. Check the head under a red blob before reading it as a nephew in
any Beagle title.

**VOL. 19 PRINTS A TEAL THAT IS NEITHER INK**, on real crowns, four times across
these two titles: #00a69b H176, #27a5ac H183, #41a085 H163, #07a27d H166. It is
15-25 degrees off both roster bands and every boy carrying it was left a
collective.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Half-Baked Baker* (19) | **121 p3** -- the three boys in a row against the wall, red / blue / green left to right, and 122 p2 shows the same three from behind | `#e81b1f`-`#e61b1f` H358.8, 125-1,900px; dimmed to `#c12719` H5.0 (122 p5) and browned to `#89402e` H11.9 S0.66, 125px, in the smoke panels (122 p3) | `#009e49` H147.7, 100-900px -- the H147 form, NOT leafgrn, which is 0 on nearly every panel. `#019e59` H153.6 on 121 p4, where TWO boys carry it and the colour names neither | `#00a5d5`-`#03a5d6` H193.5, 120-800px. On 121 p1 the wedge is ~800px but breaks into sub-min-area fragments, so the blob list reports nothing and the pixels have to be counted directly | black cap with a coloured wedge at the front-left of the crown. The judges at the Duckburg Cooking Fair wear RED BOW TIES, 150-1,200px, which is what fills the red band on 128 and reads as caps in the census |
| *Dodging Miss Daisy* (19) | **133 p3** -- Donald and all three boys running in a row, blue / red / green, with Donald's own sailor cap in the same frame | `#e3191e`-`#e51a20` H358, 150-1,400px; dimmed to `#b32c15` H8.7 (139 p4) | **the LEAFGRN form, `#42a940`/`#4fa447` H115-123**, 130-690px -- this title's cap green is the leafgrn one and `#009e47` H147 in it is foliage. Washed to `#4e9d7f` H157 S0.50, 86px (135 p6) | `#01a4d7`-`#04a5d7` H194, 115-1,000px | quartered black cap. **THE BOYS ARE BARE-HEADED INDOORS** on 131 and 132 -- clean white crowns, no cap at all -- and put them on outdoors from 133; 134 p8 loses them again in the pond. Donald wears the roster blue on his sailor cap and a red bow tie. Daisy is `#a0476a` H336 S0.53 throughout, and General Snozzie is canonical, not an `other:` |
| *The Money Well* (20) | **075 p4** and **087 p1** -- all three boys in close-up, red / blue / third by elimination, and 087 p1 prints red, green and blue together | `#e41b20`-`#e51a1f` H358, 130-1,300px | almost never printed: `#439b6d` H149 on 087 p1 (65px) is the only clean cap green in 26 pages | `#00a4d4`-`#04a2d1` H194, 60-780px -- and the same ink is SCROOGE'S TOP-HAT BAND, 200-2,500px, and Donald's sailor cap | quartered black cap, small. Scrooge's maroon coat is `#a04554` H350 S0.57 and fills the red band on most panels; the BEAGLE BOYS' red caps fill the rest. Cast is Scrooge, Donald, the boys, the Beagle Boys (78 groups), **Grandpa Beagle** (10), a tunnel contractor and a policeman |

Vol. 20 and Vol. 19, three titles read 2026-09-19 (sixty-ninth batch; **ALL
THREE REVIEWED**, so the rows below are corrected against the review). 50 pages,
87 images, **1.74 per page**; per title 1.88 / 1.50 / 1.60.

**THE ROW BELOW THAT THE REVIEW CORRECTED IS THE BLUE ONE, IN BOTH TITLES.**
Five of the batch's 24 speaker corrections are Donald against a nephew decided
on how BIG the blue was. A nephew's wedge in these titles runs 100-2,600px and
Donald's cap 1,300-6,700px, and the ranges overlap -- so the blue column names
nobody on its own. His RED BOW TIE does.

**AND 098 p4 OF *THE TITANIC ANTS!* IS A CONFIRMED COLOURIST ERROR**: two boys
in one frame print the roster red, annotated as such by the reviewer. The middle
boy is Huey, the crouching one Louie on leafgrn, and the right-hand one Dewey by
elimination with the red kept on the group.

**THE CAP IS A PATCH ON A BLACK CROWN IN BOTH OF THESE TITLES, 8px TO 900px**,
and the census's default floor does not see it. Re-run `capscan <panel> 8 40000`
before writing any absence, and expect the hue to be 5-15 degrees off the clean
band at that size.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *City of Golden Roofs* (20) | **048 p1** and **048 p3** -- the three boys in a row at the quayside, green / blue / red cleanly, and 048 p6 again | `#e41a20`-`#e61b1f` H358.5, 90-900px; dimmed at a turned crown to `#ca221f` H1.1 (056 p6, 57px+33px), `#d2181d` 8px (058 p8) and `#b93d28` H8.7 S0.78 (098-style) | **`#3cab41`/`#49a347` H118-123, S0.56-0.66 -- the LEAFGRN band**, 95-900px; and `#4ea041`/`#4da33f` H117 (060 p4, 849px). Shaded to `#2c9f7c` H161.7, 43px (055 p2). **The H147 `#009e49` in this title is NOT a cap**: it is a plant or a garment, 4,000-8,000px | `#00a5d5`-`#01a4d5` H193.5, but a BOY's wedge is only 100-500px -- `#01a3d0` 409px (056 p1), `#3b96ae` H190 S0.66 167px (058 p6), `#01a2b8` 212px | black cap with a coloured wedge at the front-left of the crown, turned away in half the panels. **The dominant ink in the whole title is Scrooge's maroon coat, `#a04554` H350 S0.57, 731 blobs** -- more than every other ink combined -- and the biggest blue on any head is his TOP-HAT BAND at 1,500-6,700px, with Donald's sailor cap next at 2,000-4,000px. The scenery green is `#008c5b`-`#008e5c` H158.9 in 8,000-65,000px fills |
| *The Titanic Ants!* (19) | **091 p3** -- the three boys in a row on the street, green / red / blue; **109 p3** shows the same caps from BEHIND, which is the clearest view of the construction in the title | `#e61a1f`-`#e71a1f` H358.5, 150-2,000px; dulled to `#b62518` H4.9 at the reference (272px) and `#e6191f` 704px on a turned crown (108 p4) | `#62a560` H118.3 **S0.42** at the reference (286px) and `#4fa43e` H110 elsewhere (2,664px on 109 p3, 917px on 108 p5). The `#009e49` H147.7 and `#018345` H151 in this title are scenery and clothing, 2,000-27,000px | `#01a2b8` H187.2 at the reference (212px), `#02a5d6`/`#06a5d2` H194 elsewhere -- 221px (109 p3), 142px (105 p5), 1,073px (097 p5), 1,858px (102 p4) | a QUARTERED black cap with one coloured segment. Scrooge's coat is again `#a04453` H350 S0.57, 355 blobs. Cast is Donald, Scrooge, the boys, **Doctor Thinknoble** (a bald human in a green jacket, 23 groups), **Mrs. Goldwad**, a picnic steward in a blue suit, and a crowd of human picnic guests who carry 19 groups between them |
| *Getting Thor* (20) | none -- no nephews | -- | -- | -- | a Gyro solo story with his Helper, crows and two scarecrows. No cap key at all. Every one of Gyro's 14 groups is `sole-figure`; the only other voices are the crows |

- **`UNCLE SCROOGE` IS DONALD AND `UNCA SCROOGE` IS A NEPHEW**, without exception
  across all 46 pages of the two feature titles. It named the speakers on two
  all-silhouette panels where no cap existed to read.
- *City of Golden Roofs* prints a **second green at H158.9** (`#008e5c`) in huge
  fills -- jungle, temple, river -- and *The Titanic Ants!* prints **H147.7 and
  H151** the same way. In both titles the cap green is the LEAFGRN one and the
  saturated H147-159 green is scenery, which is the opposite of the
  sixty-eighth batch's *Wishing Stone Island*. Check the two against each other
  at prep on every Vol. 19-20 title.

Vol. 19, four titles read 2026-09-19 (sixty-eighth batch; **ALL FOUR REVIEWED**,
so the rows below are corrected against the review). 48 pages, 99 images,
**2.06 per page**; per title 3.33 / 1.90 / 1.00 / 1.00.

**THE PERSISTENT POSTMAN ROW IS CORRECTED AND WAS THE BATCH'S WORST CLAIM:**
the pass wrote that no nephew is nameable anywhere in the title and the review
named seven, in red, blue and green. A title with no usable REFERENCE panel is
not a title with no cap key.

**VOL. 19 USES BOTH OF ITS GREENS AND NOT IN THE SAME TITLE** -- carrying one
title's green band into the next inside this volume reads every cap as absent.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Black Pearls of Tabu Yama* | **012 p1** -- all five swimming in one row, only heads and caps clear of the water | `#e7191f`-`#e61a1f` H358, 60-2299px; dim `#bc161b` 4px and `#d51a20` 15px at long-shot scale (007 p1, 015 p4) | **leafgrn `#4fa43e` H110-119**, 60-4536px; also `#52a765` H133 (008 p3), `#46a568` H142 (010 p3), `#4fa34d` H118.6 (the reference). **THE PALMS PRINT `#50943c` AT H106.5** -- the same band, six panels in ten, which is what made this title cost 3.33 images a page | `#00a4d7`-`#01a4d6` H194 -- **the same ink on Donald's sailor cap, Scrooge's hat band AND Dewey's cap**, 91px to 8536px. The reference panel has all three at once: 783 / 2796 / 916px. Size separates nothing | quartered black cap. At long-shot scale ALL the blues collapse to a desaturated teal -- `#40a486` H162 (007 p1), `#1b9fa0` H180.5 (009 p6) -- so a distant panel names nobody from colour. Donald wears a RED BOW TIE in every close panel and it is the reliable marker that separates him from a blue-capped boy. 011 p3 is flat monochrome blue, every figure filled with `#02a4d6` |
| *Wishing Stone Island* | **084 p4** and **084 p7** -- the three in a row, red/blue/green cleanly | `#e61b1f`-`#e91927` H358, 120-1853px | **the H147 form, `#009e46`-`#019e48`**, 125-1100px; `#01a14f`-`#02a450` H149 on 090. **leafgrn is ZERO on nearly every panel of this title** | `#00a4d7`-`#04aad7` H193-194, 119-2459px | quartered black cap -- **except that one boy wears a WHITE TOY SAILOR HAT and carries a blue toy telescope through all of 081 and 082**, so his own cap is not in the drawing; the other two print cleanly in the same frames and 082 p6 shows him RED once the hat is off. 084 p5 has a red cap lying on the GRASS beside its bare-headed owner. 084 p6 and 085 p3 are silhouette or cropped so close that no cap exists to read |
| *Rocket Race Around the World* | 073 p4, 074 p4, 080 p3 | `#e51b20`-`#e61b1f`, 153-1213px | `#009e49` H147.7, 154-646px | `#00a4d7`-`#05a6d7`, 134-2827px | quartered black cap, read cleanly in the cockpit close-ups and not at all in the long shots -- most of this title is the rocket at a distance with the crew only heads in a canopy. Cast is Donald, the boys, **Gyro Gearloose** (the DUCK in the yellow straw boater, named by his toolbox at 071 p4), **Professor Sliderule** (the bald bearded HUMAN, black coat and green trousers, top hat outdoors), **Professor Missilebug** (wild hair, orange trousers) and **Gladstone** (tan hat, blue jacket) |
| *The Persistent Postman* | **no single clean row, but the caps ARE readable panel by panel** -- 116 p6, 119 p6 and 120 p7 each name a boy | read by the review on 116 g10/g16, 119 g9, 120 g13 | read on 120 g14 | read on 116 g15, 119 g7, 120 g13 | **THE PASS'S CLAIM THAT NO NEPHEW IS NAMEABLE HERE IS WRONG -- seven were named at review.** The boys appear only from 115 and always as a trio, and Donald's bow tie, the mail car and Rockdust's shirt do fill the red band, which is what the pass mistook for an absence. Donald works solo as a rural mailman; the cast is otherwise Mr. Rockdust, Mr. Birdmind, Miss Applecheeks Teengiggle and a family of giant eagles. 1.00 image per page |

- **Donald's sailor cap is the roster blue in all four titles**, and so is
  Scrooge's hat band in the two he appears in. His RED BOW TIE, 250-1500px of
  the cap red at his neck, is what actually separates him from a blue-capped
  boy in a close panel -- it is present in every close drawing of him across
  the batch and absent from every nephew.
- *Tabu Yama*'s palms and *Wishing Stone Island*'s sea are both in the green
  bands and neither is a cap: `#50943c` H106.5 and `#329670` H157 respectively.
  The banknotes on *Wishing Stone Island* 090 p7 print `#01a250` H149 -- the
  cap-green hex exactly -- across the whole panel.


Vol. 19 and Vol. 20, five titles read 2026-09-18 (sixty-seventh batch; **the Mines row is
CORRECTED against its review**, the other four are not yet reviewed).
49 pages, 88 images, **1.80 per page**; per title 1.80 / 1.41 / 3.25 / 2.75 / 2.00.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Tenderfoot Trap* (19) | **061 p2** (three boys in the car, caps cleanly quartered red/blue/green) and **069 p5** (the same three in a row, larger) | `#e61b1f` H358.8 154-2554px; dim `#ad3416` H11.9 133px (070 p5), `#e21c20`/`#e31a20` slivers 41-475px (065 p8, 067 p5) | `#009e46` H146.6 851-2002px (061 p2, 065 p8, 069 p5); `#048a55`/`#028946` H151-156 slivers under 25px (068 p3) | `#01a4d6`-`#03a4d7` H194 -- **the SAME blue as Donald's sailor cap**, which prints 1,600-3,800px in most panels against a boy's 27-936px; `#00a2d0` H193.3 100px (068 p3) | a quartered black cap worn throughout; the coloured quarter turns away from the reader on several panels (063 p1 boys 2-3, 009-style) and then prints 0-86px. Donald's cap and Scrooge's hat band are both the roster blue |
| *The Mines of King Solomon* (20) | **009 p6** (green, red and blue in a row), **011 p2** and **011 p8** | `#e41a20`-`#e61a20` H358 90-5377px; dim `#d81f20`/`#c6251d`/`#a52118` 130-250px; **Donald's BOW TIE is the same ink** ~600-1700px, and the red band is also full of brickwork at `#e9595c` S0.6 inside the temple | `#4da33f`-`#4ea240` **H111.6, the leafgrn band, not `green`**, 400-3724px; shaded `#61a361` H120 S0.40 (024 p1); `#55a04e` S0.51 (016 p7) | `#00a5d5`-`#02a4d4` H193.5 -- the same ink on Donald's cap, Scrooge's hat band AND a nephew's. **SIZE DOES NOT SEPARATE THEM AND THIS ROW SAID IT DID: the review turned seven of my `the duck in the blue sailor cap` calls into nephews, including 014 g8 on 5686px and 016 g0.** A nephew's band runs 60px to at least 5,700px here. Put the blob on a head and read the head. Teal `#1fa399` H175.5 S0.81 ranked blue against a clean green and red in the same panel (011 p2) -- that one held | a thin rim or side patch on a black cap, 60-400px when it prints at all. **COLOURIST CLASH: the dialogue names the RED-capped boy LOUIE four times (026 g8, 027 g5, 028 p5 caption, 031 g16) and a GREEN-capped boy DEWEY once (009 g2).** Read convention-flagged. Long stretches are unreadable by construction -- silhouette panels (010 p4, 011 p4, 014 p4/p6, 025 p4, 026 p4, 029 p5, 031 p6), flat-blue monochrome (023 p1, 032 p4, 033 p1), torch-lit tunnels, and one panel that is three pairs of eyes on black (028 p7, 031 p5) |
| *September Scrimmage* (20) | none usable | -- | -- | -- | the boys play for the Duckburg Quackers in **identical red football helmets** (`#e41a20`, the cap red) with black jerseys; the Dogdale Barkers wear green (`#009e49`). No cap key at all, and the census red on 037-040 is mostly helmets and Donald's bow tie. Two boys are named from dialogue instead: 037 g5 `ROUGH, DEWEY!` pins the bandaged boy in the stands, and the 037 p8 caption names Louie |
| *Gyro Builds a Better House*, *August Accident* (20) | none -- no nephews | -- | -- | -- | Gyro solo stories with his Helper, a black mouse, a pig customer and his wife, a neighbour and a cabbage farmer. No cap key. **Every Gyro-alone balloon is a thought cloud with a bubble trail**, which is where 25 of the batch's 29 type corrections come from |

- **Donald's sailor cap is the roster blue in both volumes** (`#03a4d7` in Vol. 19,
  `#00a5d5` in Vol. 20) and so is Scrooge's top-hat band. Between them they are
  the largest blue blob in most panels of both feature titles.
- *The Tenderfoot Trap*'s desert greens are `#009e46`/`#008943` H146-150 at S1.0 --
  the SAME hex as the cap green -- so a green blob has to be placed on a head
  before it means anything. The cactus at 065 p8 is 8 blobs of it.
- *The Mines of King Solomon*'s cap green sits in **leafgrn** at H111.6, while the
  `green` band on its outdoor pages is foliage at H146-162 and its temple interior
  fills the red band with `#e9595c` brick at S0.6. Filter by saturation, not hue.

Vol. 18 and Vol. 19, four titles read 2026-09-18 (sixty-sixth batch; none reviewed).
56 pages, 78 images, **1.39 per page**; per title 2.00 / 1.60 / 1.15 / 1.20.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Special Delivery* (18) | 158 p2 (green, teal and red boys at the counter) and 159 p2 (red, blue, green in a row) | `#e71c20`-`#e61a20` 57-3,106px throughout; dim `#de1d20` (158 p5), `#cb2b29` (161 p1), `#e01f21` (170 p5) | `#59a451` H114 (158 p2), `#4ea43e`-`#4fa43e` H110 (159, 160, 166), `#5ca06d` H135 S0.42 (158 p5), `#50a53f` (162 p6), `#4e8477` H166 S0.41 (161 p1, ranked green against a clean blue) | `#00a5d5`/`#01a4d5` H193 throughout; teal `#1ca49d` H177 ranked blue against a clean leafgrn green (158 p2); `#03a7dd` (161 p1); dull `#429db5` S0.63 declined (161 p5) | a quartered or rimmed black cap, worn throughout -- this is a street-and-garden story with no indoor stretch. Donald's own cap is the roster blue and prints 2,000-4,000px, which is what most of the blue in a band count is |
| *The Code of Duckburg* (18) | 169 p2 (red, green and blue boys round Gladstone) and 170 p5 | `#e61a1f`-`#e71c20` 87-1,245px; dim `#cb2b29` (171 p1), `#d12624` (171 p7), `#e01f21` | `#4fa43e`-`#50a33e` H110 (169 p2, 170 p5, 171 p7); `#4e8477` H166 S0.41 (171 p1); dull `#559f6e` H140 S0.47 declined (170 p8) | `#00a4d4`-`#01a4d5`; teal `#1ca3a3` H180 ranked blue with no green in the panel (168 p3); `#1aa5bf` H190 (171 p1); dull `#429db5` S0.63 declined (171 p5) | rim or quarter on a black cap OUTDOORS only. **Bare-headed indoors for five straight pages (172-176)**, which is most of the title -- and then 176 p7 and 177 put the boys in RED, BLUE and GREEN PYJAMAS (`#e71c20` 2,955px, `#00a5d5` 8,035px, `#4fa43e` 2,032px), which is a costume key and names three groups. Gladstone wears the roster blue hat; Donald's cap is blue |
| *Forbidden Valley* (19) | 027 p3 (red, blue and green boys at the cannery) and 029 p8 | `#e61a1f`-`#e8181f` 37-3,106px; dim `#cc2119` (057 p4), `#b12a1a` (167-style, 042 p5), `#eb191c` (029 p3) | `#50a33e` H110 (027 p2), `#56953b` (027 p3), `#009e46`-`#009f50` H147-150 (052-style), `#35a671` H166 ranked green beside a clean blue and red (029 p8), `#4e8477`-style dull greens | `#00a4d7` H194 throughout -- a slightly warmer blue than Vol. 18's `#00a5d5`; `#01a5d6`, `#03a4d6`; `#0aa5c2` (026 p3) | **caps only on 025-043.** From 032 every duck wears a brown PITH HELMET, so two thirds of the title has no cap key at all and the collective rate is high by construction. The foliage fills `green` and `leafgrn` on nearly every outdoor panel (`#009e47`-`#009e49` H147) |
| *Sagmore Springs Hotel* (19) | 052 p8 (green, blue and Donald's blue) and 060 p7 (red, blue, green in a row) | `#e71a1f`-`#e8171f` 37-434px, small throughout; `#c9261c` (059 p6) | `#009f50` H150 (052 p8), `#009e47`/`#028945` (058, 060); teal `#017f7b` H178 S0.99 declined with nothing to rank it against (053 p6), `#00a5a4` (058 p4), `#0ba26f` (057 p6), `#009a7a` (060 p7) | `#00a4d7`-`#04a4d6`; `#02a5d7` (052 p7); `#00a6bc` H189 (060 p6); Scrooge's derby in disguise is a darker `#0381b9` | the boys are barely in the story -- Donald plays every hotel role himself and Scrooge is the disguised guest. Caps appear outdoors on 052 and 060; indoors and in the kitchen the boys are bare-headed or in chef's hats. Donald's cap prints blue 700-4,900px and is most of each panel's blue |

- **A TEAL WITH NOTHING TO RANK IT AGAINST NAMES NOBODY, AND THAT IS MOST OF THIS
  BATCH'S DECLINES.** `#1ca49d` H177 (Special Delivery 158 p2) sits beside a clean
  leafgrn green and is Dewey's; `#1ca3a3` H180 (Code of Duckburg 168 p3) has no green
  in the panel and was taken as blue only because the other two boys print red and
  nothing; `#017f7b` H178 S0.99 (Sagmore 053 p6) is a lone boy in a room and was
  declined outright. The rule that held: rank inside the panel, and where the panel
  has one cool cap and no rival, decline the colour rather than guess the drift.
- **THE COOL-BAND SATURATION FLOOR EARNED ITS KEEP TWICE.** `#429db5` S0.63 on
  *Special Delivery* 161 p5 and *Code of Duckburg* 171 p5 is a dull blue-grey with no
  clean cool cap beside it; both went to `nephews`. `docs/cap-scanning.md`'s S0.75 rule
  is what stopped two guesses.
- **A COLOURIST CLASH CAN BE TITLE-WIDE AND STILL NOT BE A PERMUTED PALETTE.**
  *Forbidden Valley* names a RED-capped boy DEWEY (025 g7, a direct address to a lone
  boy) and puts the box knocked from LOUIE's hand in the BLUE-capped boy's hand
  (029 g2). GLK's instruction for this batch was **convention, flagged**: name red
  Huey and blue Dewey everywhere the dialogue does not pin a boy, record the printed
  ink, and put the clash in `vision_note` on every red/blue call so the reviewer sees
  it on the group in hand. That is the back-propagation
  `project_per_story_cap_palette` asks for, done at write time rather than after.
- **A STORY THAT PUTS EVERYONE IN THE SAME HAT COSTS NOTHING TO READ AND NAMES
  NOBODY.** *Forbidden Valley*'s pith helmets from 032 on, and *Sagmore*'s Donald
  playing bellboy, clerk, driver and doorman, mean the speaker question is
  Donald-against-a-boy, settled by SIZE AND BEAK rather than by any cap. 1.15 and 1.20
  images per page, the two cheapest titles in the batch.
- Devices ungrouped by both engines are the batch's whole added-group tally: `ZOW`
  (Special Delivery 162, speed lettering up a pole), `?` over the boys (166), `!` over
  the boy in red pyjamas (Code of Duckburg 177), `?` over Donald (Forbidden Valley 032,
  Sagmore 052) and two `ZIP!`s (Sagmore 054). Seven in 56 pages.
- Type corrections, 22 in all: 5 in *Special Delivery*, 0 in *Code of Duckburg*, 14 in
  *Forbidden Valley* and 3 in *Sagmore*. The recurring ones are a character's cry or an
  animal's roar stored as `sound_effect` (OW, OWOOCH, YEEK, RAWR, SNORT, WAK) and a
  caption box stored as `dialogue` or `background` (`So-`, `Top Floor!`, the story logo).

Vol. 16, Vol. 18 and Vol. 20, four titles read 2026-09-16 (sixtieth batch;
all four reviewed; the Vol. 18 row is CORRECTED against its review):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Migrating Millions* (16) | 096 p7, two boys beside Scrooge, caps big and lit | `#e01a1f` H358.5 520px (094 p6); `#e51a1f` 2,676px (096 p7); `#e31c1f` 510px (096 p8); dark sliver `#bb2e31` H358.7 26px (094 p7) | `#4fa43e` H110.0 3,153px (096 p7) | `#08a4d2` H193.7 485px (094 p6); `#16a3be` H189.6 360px (096 p8) | a band on a black cap outdoors; several panels print no cap ink at all (096 p3, 098 p2) |
| *Knight in Shining Armor* (18) | 086 p2 and 083 p7, three boys with their caps on | `#e71c20` H358.8 (078 p1, p3); rims `#b92e19` H7.9 325px (086 p2), `#b42c1a` H7.0 140px (087 p8), `#e61b20` 3,230px (083 p7); the review also read red on 078 p4, 078 p5, 081 p8 and 084 p2, where I measured none | `#50a43f`/`#009e49` 1,951px (083 p7); `#4ea43e` H110.6 858px (085 p8); shaded `#65a465` H120.0 S0.38 392px (086 p2); small `#68aa41` H97.7 110px (084 p1); the review also read green on 081 p8 and 087 p8 | `#00a5d5` H193.5 331-3,007px (078 p3; 083 p7; 085 p8); **teal** `#25a48a`/`#22a590`/`#00a288` H167-170, 146-225px, ranked blue and CONFIRMED (082 p1, 084 p1, 086 p2); the review also read blue on 081 p8 | a thin rim on a black cap; bare-headed indoors through 079 and 080, **but 081 p8 and 087 p8 DO carry caps that no whole-panel scan finds** |
| *The Cat Box*, *Grandma's Present* (20) | none -- no nephews in either | -- | -- | -- | Gyro solo stories: Gyro, Gus Goose, Grandma Duck and two cats. No cap key at all |

- *Migrating Millions*: **Scrooge's top hat band is the roster blue** `#01a4d6`-`#08a4d2`,
  and his coat is `#a04453` -- between them they account for nearly every blob
  `capwide` reports on that title. The valley greens are H147-151 at S0.94-1.0,
  well clear of the H110 cap green.
- *Knight in Shining Armor*: **TWO INKS IN THIS ROW WERE WRONG AND THE REVIEW
  REMOVED THEM.** `#00a3d2` 2,927px on 078 p4 and `#4fa43e` 2,187px on 084 p2
  were recorded as nephew caps and are scenery -- both boys are Huey in red. A
  blob is only a cap once a crop has put it on a head.
- *Knight in Shining Armor*: `title_bands` **under-reports this title badly** --
  it gives 086 p2 `red=3 green=2 blue=0` on a panel where all three boys are
  banded. Use `title_heads`' per-head `CAP-INK` and then probe each crown; two of
  my probes returned zero only because they were 40px too high. Donald's cap is
  the roster `#00a5d5` and so are the sky, the bus and the painted doorframe of
  078 p5, which is why that panel's blue is worthless. The orange plume is
  `#ed671e` H21-26 and the giant strawberry costume `#e71c20` -- both sit where a
  cap would be.

Vol. 18, one title read 2026-09-16 (fifty-ninth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Borderline Hero* | 070 p3, three boys running in black caps with thin rims | `#e51a20`-`#e61a20` 120-1,030px (070 p3, 072 p1-p3); dark `#7e1e16` H4.6 (072 p7); long-shot `#a82e20` H6.2 (072 p8), `#a33321` H8.3 (074 p1) | `#4fa43e` H110 180-3,200px (072 p4, p6; 077 p5, p6); shaded `#2e865b` H150.7 (070 p3), `#39ad48` H127.8 (075 p2), `#47a840` H116 (075 p7), `#359b60` H145 (077 p7) | `#00a5d5`-`#01a4d5` 80-3,400px (070 p3, 072, 074 p2, 077 p4); teal `#13a7a3`-`#019ea6` H177-183 (074 p1, 075 p7, 077 p5, p6); greener teal `#23a780`/`#02956c` H162-163, ranked blue against a greener cap beside it (072 p8, 077 p7) | a thin coloured rim on a black cap outdoors; bare-headed indoors (068, 069); some caps print no rim (072 p1 right boy, 072 p4 left boy, 075 p2 left boy) |

- Donald's campaign hat is the roster `#00a5d5`; the garden gate (072 p1, p4) prints
  the cap red at head height; the cacti are H146-163 at S1.0.

Vol. 16, one title read 2026-09-16 (fifty-ninth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Second-Richest Duck* | 074 p5, three boys at the ball in quartered caps | `#e31a20` 1,285px (074 p5 probe), `#e61a20` 835-1,491px (085 p5); rims `#e4191f` (075 p2), `#e21c20` (081 p3), `#e11d20`/`#c72528` (083 p5, p6), `#e61920` (084 p7), `#d52428` (089 p3); pinkish `#e73448` H353 (082 p8) | `#459e5f` H137.5 (074 p5), `#4aa344` H116 (075 p5), `#53a449` H113 (081 p2), `#4da33d` H111 (082 p4, 087 p6, 088 p2, p4); shaded `#6a973f` H90.7 (082 p6), `#619b37` H94.8 (082 p8), `#589b39` H101 (085 p5) | `#04a4d6`-`#06a5d4` 70-5,400px (074 p6-p8, 082 p2, 085 p5, 086 p3, 087 p3) | a coloured rim or quarter on a black cap; bare-headed through much of the voyage and Glomgold's bin (074 p2-p4, 075 p1, 078 p3-p6, 079 p3, 081 p4) |

- The one naming line, 082 g4 `DEWEY`, lands on the blue-rimmed boy of 082 p2. It is
  a dictionary word, so `name-grep` did not list it: grep the groups for all three
  names at prep.
- Scrooge's coat is `#a04453` and his hat band the roster blue; Glomgold's pompom
  prints the cap red at head height (082 p4, 087 p6), and the green stars on 077 p8
  print the cap green.
- A filtered capwide listing showed no red blob on a red cap plain in the crop
  (074 p5, 081 p2); the probe found `#e31a20` 1,285px on 074 p5. Probe the head.

Vol. 16, two titles read 2026-09-15 (fifty-eighth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Lost Crown of Genghis Khan!* | 010 p2, the ducks boarding at the airfield; the fur caps on 013 p1 and 014 p1-p5 | `#e41b20`-`#e51a20` 120-5,600px | `#4da33e`-`#4ca33f` H110-112, 170-9,100px -- the `leafgrn` band | `#00a5d5`-`#05a5d5` 290-7,600px | coloured trim on fur caps in the mountains; bare-headed on the airliner (011-012) and in the cage (022-023); the three silhouettes on 015 p2 print one identical teal `#038386` H181.8 |
| *Faulty Fortune* | 061 p2, three boys in quartered beanies in the car | `#e51a1f` 900-2,000px; thin rims `#d82123` (064 p2), dark `#bf1e22` (066 p6), `#c01f1e` (066 p7), `#d52223` 96px (067 p1) | `#4da33e` H111 1,300-1,900px; rims `#4fa341` (064 p2), `#4ca43e` (066 p8) | `#03a4d6` 850-3,200px; `#00a5d7` (066 p7) | quartered beanies on 061, then thin rims on black caps, and no rim at all on 063 and 064 p1 |

- *Genghis*: Scrooge's coat is `#a04453`, and on 012 p7 he wears a blue fur cap in
  `#00a5d7`, as Donald's sailor cap is. The one naming line (017 g12) lands on a
  leafgrn boy -- see the findings.
- *Faulty Fortune*: the Canny Brannies boxes print the roster blue `#00a5d7` in
  bulk at head height (066 p1), and the trees are `#009e49` H147.7.

Vol. 18, two more titles read 2026-09-15 (fifty-eighth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Runaway Train* | none | -- | -- | -- | bare-headed indoors throughout; no cap key at all |
| *Statues of Limitations* | 058 p1, three boys from behind in quartered caps | `#e71c20` 120-3,400px; dimmed `#b8251c` H3.5 (059 p5), `#ae2917` H7 (064 p7), `#d01f1f` (066 p5) | `#4fa43e` H110 50-2,000px, the `leafgrn` band; on small caps `#71a83a` H90 (058 p5), `#6ca73a` H92.5 (059 p6), `#43ae47` H122 (065 p2), `#44a055` H131 (062 p4) | `#00a5d5`-`#01a4d5` 60-1,600px; teal rims `#1ba5a4` H179.6 (059 p6), `#16a5aa` H182 (059 p7), `#279299` H183.7 (060 p2) | a coloured quarter or rim on a black cap; some caps print nothing (061 p1, 066 p5, 067 p4) |

- *Statues*: the boys' green mittens print the cap leafgrn `#4fa43e` (060 p3, 061
  p7) and are not a cap; the house door (059 p5) and the house's sill strip (064
  p8, where it merges with a cap) print the roster blue; the Umble boy's coat is
  `#3e7b54`/`#407c56` H142.
- Donald's cap is the roster `#00a5d5` in both titles.

Vol. 18, three titles read 2026-09-15 (fifty-seventh batch); Vol. 20's *Inventor
of Anything*, read in the same batch, has no nephews (Gyro, Speedy and a
neighbour):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Master* | 021 p8, three boys side by side in the freezer | `#e61a20`-`#e61b20` 60-1,240px; dimmed `#893b25` H13 (020 p3), `#762c18` (022 p1) | `#009d46` H147, the `green` band; thin rims `#009f70` H162, `#24877f` H175, `#249071` H163 | `#00a5d5`; `#08a2b2` H185.6 (022 p1), `#139da5` H183 (023 p4) | a coloured patch on a black cap; bare-headed indoors on 018-019 |
| *A Whale of a Story* | 028 p1, three boys on the cliff | `#e71c20` 60-700px; dimmed `#ae2b17` (035 p7), `#c3171b` (033 p6) | `#4fa43e` H110, the `leafgrn` band | `#00a5d5`; `#2894ad` H191, `#3caabe` H189, teal `#19a896` H172 (028 p4) | a coloured patch on a black cap; on 033 p6 two caps lie beside their owners |
| *Smoke Writer in the Sky* | 038 p1, three boys at the hangar in big checked caps | `#e71c20`, 2,085px at 038 p1; dimmed `#b13829` (047 p6) | `#4fa43e` H110 | `#00a5d5`; `#09a5c3` (047 p6) | checked caps at 038 p1, a coloured patch on a black cap elsewhere |

- Donald's cap is the roster `#00a5d5` in all three titles.
- *The Master*'s couch stripes print `#009d46`, its cap green. *Whale*'s thermos
  (`#3aac41` H123.7) and red bags sit beside the boys. *Smoke Writer*'s grass and
  foliage are `#009e46`/`#009e49`, not the cap green, and Scrooge's coat is
  `#a04553`.

Vol. 16, one title read 2026-09-14 (fifty-sixth batch); Vol. 20's *Trapped
Lightning*, read in the same batch, has no nephews (Gyro, two mouse kids and
Grandma Duck):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Land Beneath the Ground!* | 032 p3, three boys from behind at the tunnel mouth | `#e61b1f` 120-1,400px; dimmed `#a3321e` H9 (032 p6), `#b33841` S0.69 (041 p1) | `#4da33d`-`#4ea33f` H110-111, 250-3,500px -- the `leafgrn` band; shaded `#5aa23f` H104, `#569d5a` H123 | `#00a5d7`-`#06a5d5` 130-1,700px; teal in shade (see the findings) | a coloured patch at the side or back of a black cap; the boys are specks in the long shots of the shaft |

- Scrooge's coat is the `#a04453` maroon at 1,000-17,000px, so a clean `#e61b1f`
  blob is a boy's cap or Donald's bow tie; Donald's cap and Scrooge's hat band
  are the roster blue.
- The creatures print every roster ink on their bodies; a band hit on a creature
  is never a cap.

Vol. 17, one more title read 2026-09-14 (fifty-sixth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Camping Confusion* | 172 p7-p8, named by the dialogue (`RODMAN LOUIE`, `CHARTMAN HUEY`) | `#e41b20`-`#e61a20` 240-1,400px; dimmed `#b93321` (173 p4), `#bf2d1f` (172 p6) | `#019d47`-`#009e47` H147, 340-1,100px -- the `green` band | `#04a5d6`-`#07a3cf` 200-1,500px; teal `#09a2ae` H184 (172 p6), `#0ba593` H172 (178 p8), and `#0ba570` H159 (173 p1, named Dewey by the review); a pale `#b4d9df` S0.19 on a small cap (173 p3) that is the sky's own hex | a coloured patch at the side of a black cap with a pink uranium button on top; the bears take the caps on 176-177 |

- Donald's cap is the same `#04a5d6` as Dewey's patch, at up to 2,900px.

Vols. 5-8 one-pagers, read 2026-09-12 -- and the headline is that the
one-pagers mostly do NOT exercise the volume palettes at all:

| title | reference | what the caps do |
|---|---|---|
| *Machine Mix-Up* (5) | none | Donald alone in all 7 panels; every "CAP-INK" hit is a prop -- the blue `#00a5d7` is the logo lettering, the red `#e21c1f` his bow tie |
| *Horseshoe Luck* (6) | 039 p4, three boys in a row | green `#54ad41` / blue / red `#e61b1f` bands; p5's band row reads `red=0 green=0 blue=0` yet the census finds `#4ba340` 287px on the lone boy's crown |
| *Bean Taken* (6) | 102 p2 counter boy | cap green `#4da33f` (the Vol. 6 H110.6 ink) on one boy; red `#e61b1f` 133+186px in p6 |
| *King-Size Cone* (7) | 241 p2, p4 and p6 | the batch's cleanest: blue, green, red bands, big and lit, on three panels |
| *Noise Nullifier* (8) | 141 p7 outdoors | blue/red/green on BOTH cap band and shirt trim, agreeing on all three boys |
| *Sleepy Sitters* (7) | -- | greens read `#56943e` (H97) and `#49a34b` (H121), **neither is the Vol. 7 cap green at H111** -- unusable, do not name off them |

- **Vol. 6's grass `#59b140` is all over the one-pagers and is not a cap.** On
  *Bird Watching* it sits on all three of the small boys' crowns at 289/611/635px
  -- identical on three boys, which is the tell that it is foliage behind them.
- **Vol. 7's non-roster green trap recurs**: *Sleepy Sitters* above, and
  *King-Size Cone*'s `#70b53e` (H95) scenery, well clear of the H111 cap ink.

Vol. 17, three more titles read 2026-09-14 (fifty-fifth batch); the first
and third reviewed:

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Olympic Hopeful* | 141 p3, three boys on the bench | `#e61b1f`-`#e7191f` 120-1,800px | `#1c8d70` H164.6 and `#079464` H159.6 (139), `#029c4a` H148 (141), `#0da742` H140.6 (140 p1) -- the `green` band throughout | `#00a5d7` 100-1,000px | a coloured patch at the crown and side of a black cap; washed out in the rain on 147 p7-148 p4, where the review still named them |
| *In the Swim* | none -- bare-headed until 168 p8 | swimsuit stripes; cap `#e51c20` 1,423px on 168 p8 | swimsuit stripes | swimsuit stripes | bare heads in striped swimsuits, red/green/blue per boy: **the stripe is the key** (see the findings) |

- *Gopher Goof-Ups* (reviewed): reference 150 p7, green `#069b51` H150.2
  against the hedge `#0da842` H140.5; red `#e51a21`, blue `#00a5d7`; small
  patches at the back of a black cap. The `#08a678` H162.5 patch on 150 p2 was
  Dewey's blue, not the green.
- On *In the Swim* 168 p8 the ladder boy's `#3dae6b` H142.6 was Dewey.

Vol. 17, two more titles read 2026-09-14 (fifty-fourth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Ice Taxis* | 128 p6, three boys in a row on the sofa | red pom `#e41a21`-`#e41a20` 500-700px; `#da1a3a` 175px on 120 p7 | wanders by page: `#049d47` H148 (128 p6), `#059d61` and `#1e9164` H156 (120 p7, 123 p6), `#34853a` H124 (121 p4) | `#03a4d6`-`#05a4d4` 600-2,100px | winter knit caps with a pom: Huey black with a red pom, Dewey light blue, Louie green |
| *Searching for a Successor* | no clean row; 135 p3 and p5 | `#e31c20`-`#e51a20` 366-606px | `#0c9c49` 392px in two pieces (135 p4) | `#04a4d4` 1,200px (135 p3); `#07a4d5` only 110px (135 p1) | the same knit caps, small; bare-headed at the desk on 131 p4 and indoors on 133 p7 |

- On *The Ice Taxis* the sofa prints `#01b3d7`/`#0097b6`, the same family as
  Dewey's blue, and the boat's `#e71447` sits beside the cap red; the trees are
  `#338539`/`#348539`, which is where 124 p6's green cap disappears. Read the
  hex and place it on a crown, not the band count.

Vol. 17, one more title read 2026-09-14 (fifty-third batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Secret Resolutions* | 110 p7, three boys on the wall | `#e51a20` 313-550px; dark `#812813` H11.5 / `#873a1a` H17.6, 60-110px, on 110 p8 and 111 p1 | `#4fa773` H144.5 109-165px; teal `#449a87` H166.7 on 110 p8 | `#00a5d7` 380-1,300px | a coloured patch at the side or back of a black beanie; outdoors only on 110 p7-p8 and 111 p1, bare-headed indoors everywhere else |

- On 114 the pyjamas carry the inks instead: `#00a5d7` / `#e61b1f` /
  `#4fa43d` H110, clean enough to name all six groups (all held).
- From 115 p8 on, Dewey is named by the dialogue (the detective kit and the
  camera), not by any ink; the other two boys stay collective indoors.

Vol. 17, one more title read 2026-09-11 (fifty-second batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Three Un-Ducks* | 108 p1, three boys in close-up (also 107 p7 and 099 p1) | `#e51a20` 1,300-4,400px, dull `#ab311f`/`#c81c1e`, dark `#7a3e2c` H14 on 106 p6 | `#4fa43f`-`#5ea458` H108-115 clean, `#3da357`/`#40a360` H135-139, shaded `#618a68`-`#6fb06a` S0.30-0.40 | `#00a5d7` 200-1,400px, `#11a0b7` H188; **teal `#3c9f8c`-`#09a19a` H164-177** | a coloured patch at the side or back of a black beanie; bare-headed indoors (100 p5, 102 p7-p8, 103 p2) |

- The teal is Dewey's blue in shade: 107 p3 names it by elimination against
  a clean red and an H135 green. But 099 p3 prints the same `#429f86` on two
  boys, so a teal is not a name on its own.
- **Reviewed 2026-09-12: the split is at about H140.** H108-139 is the cap
  green (every such call stood); H147-177 is Dewey's blue as often as it is
  Louie's green -- `#0a9c60` H155 and `#099e57` H151 both came back Dewey,
  while `#0b974b` H147 in the same panel as the second is Louie. Do not
  write Louie off a green-band hue above H140 without a crop.
- The pinata and the foliage are `#009e47` H147 in the `green` band; two
  boys wearing an H147-151 crown ink (108 p2) are not named by it.
- Donald's bow tie is the roster red (106 p6 and 108 p6 at 600px).

Vol. 14, one more title read 2026-09-11 (fifty-first batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Golden Fleecing* | 195 p3, three boys from behind at the dock | `#e81c1e` 300-2,700px | `#4ea33e` H110.5 300-1,900px | `#00a5d5` 700-1,300px | a coloured patch at the side or back of a black beanie; drifts to olive, teal and brown-red (see the findings) |

- Scrooge's coat is the roster red exactly (`#e61b1f`, 5,000-13,000px), as
  on Cibola; so are the guidebook, the rockets and Donald's bow tie. His hat
  band and Donald's cap are the roster blue. Foliage, the Argo and the
  green sack are `#009e49` H147.7, in the `green` band -- the cap green is
  in `leafgrn`.
- Bare-headed indoors (192, 194, 213 p4); silhouettes on 187 p2, 192 p6,
  195 p2, 211 p7.

Vol. 14, two more titles read 2026-09-11 (fiftieth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Great Steamboat Race* | 152 p3, two boys from behind | `#e61a1f` 250-1,650px | `#4ca33e` H111 300-1,200px | not printed clean on any page read | coloured segment at the side or back of a black cap; plain black indoors on 146-151 |
| *Riches, Riches, Everywhere!* | 166 p4, two boys on the crates | `#e61b1f` 160-720px, `#b2331e` dull in shade | `#4ca33c` H111 in light, `#16844e`-`#467c5b` H143-150 in shade, 160-1,300px | `#03a4d5` 300-1,200px, `#3ca783` H160 in shade | the same; plain black in the bin on 164-165 |

- Scrooge's coat is the `#a04453` maroon on both (as on *The Tuckered
  Tiger*), so a clean `#e61b1f` blob is a boy's cap or Donald's tie; his hat
  band and Donald's sailor cap are the roster blue, and on Steamboat the
  river and sky print the same `#00a5d5`.
- On Steamboat the boys' green and red print on 152-153, 158-159 and 161
  only; every other nephew call rests on a tail or an address.

Vol. 17, one more title read 2026-09-11 (fiftieth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Custard Gun* | 091 p6, three boys running | `#e51a1f` 150-1,650px, dull `#962d1b`-`#b8332b` from the side | `#009d49`-`#0da842` **H140-150, the `green` band, the same ink as the bushes** | `#02a4d6` 100-1,200px, `#08a29d` H180 in shade | a coloured patch at the back of a black beanie, mostly 60-400px |

- The green patch is NOT in `leafgrn` on this title: read a `green` blob on
  a crown as the cap, and expect it to share its hex with the foliage.

Vol. 17, three more titles read 2026-09-10 (forty-ninth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Trouble Indemnity* | 068 p5, three boys facing Donald | `#e51a20` 2,151px | `#54a071` H143 S0.47 shaded on p5, `#4da440` H112 on p8 | `#00a5d7` 1,220px | side segment on a black cap; only 068 has the boys |
| *The Chickadee Challenge* | 069 p5, three boys in a row | `#e61b1f` 130-620px, `#b53126` dull on 070 | `#5c9f54` H114 / `#4fa43f` H110; `#519d88` H163 in shade | `#09a4d4` 60-1,700px | side segment, small; 071-078 are brown Woodchuck caps with NO roster ink |
| *The Unorthodox Ox* | 085 p6, three boys on the fence | `#e41a20` 250-3,300px | `#029d46` **H146 in the `green` band** | `#00a5d7`, shading to `#23a186` H167 and `#12a3b4` H186 | side segment on a black cap; bare-headed at breakfast 079-080 |

- On the Ox a `green` blob on a skull is the cap; on the other two it is
  the Vol. 17 rule (`leafgrn` for caps, `green` for scenery), except the
  shaded `#54a071` on Trouble Indemnity 068 p5.
- Chickadee 069 p3 prints two red caps on adjacent boys, a colourist slip.

Vol. 14, two more titles read 2026-09-10 (forty-eighth batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *The Fabulous Philosopher's Stone* | 112 p4, three boys in a row on deck | `#e61b1f` 73-2,600px | `#4da33d` H111 clean, or `#27865a`-`#35a46d` H150 dark | `#00a5d5` 150-3,700px | black cap with a small side TAB, 70-200px turned away, under the 25px-floor census on most panels |
| *Heirloom Watch* | no nephews in the story | -- | -- | -- | -- |

- Probe the crown box; the census attaches a tab only when it faces the
  reader. The dark green tab lands in capscan's `green` band -- on this
  title a `green` blob ON A CROWN is a cap.
- Scrooge's coat is the roster red at 1,000-10,000px and his hat band the
  roster blue, as on Cibola; Donald's sailor cap is the roster blue too.
- The boys are bare-headed indoors at the hotel (128).

Vol. 17, two more titles read 2026-09-10 (forty-eighth batch); the Hondorica
entry below holds:

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Donald's Raucous Role* | 040 p4, two boys' backs | `#e51a1f` 2,535px | `#4fa43e` H110 1,100-1,200px | `#00a5d7` 1,900-3,600px | side segment on a black cap; bare-headed indoors (039, 041 bed, 045, 048) |
| *Good Canoes and Bad Canoes* | 057 p1, two boys' backs | `#e41a1f` 940-2,400px | `#4fa43f` H110 1,100-1,600px | `#04a4d6` 900-1,600px | the same, drawn large from behind; a shaded green reads `#35904e` H145 S0.5 |

Vol. 17, first two titles read 2026-09-10 (forty-seventh batch):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Secret of Hondorica* | 009 p2, three boys in close-up | `#e31c20` 488px | `#40a562` **H143** 244px there; `#4da33f` H111-114, 150-1,000px on every later panel | `#06a4d4` 672px | coloured segment at the side or back of a black cap |
| *Dogcatcher Duck* | no clean row; 031 p3 and 034 p8 | `#e61b1f` 289-601px | never printed clean | `#00a5d7` 315-1,433px | the same |

- Donald's sailor cap is the same `#00a5d7` as Dewey's segment at
  1,000-10,000px; foliage, Scrooge's coat and the jungle are `#009e49` H147,
  in the `green` band, so on this volume the caps live in `leafgrn` and the
  `green` column is scenery.
- The caps come off indoors: 007-008 (Scrooge's office) are bare-headed with
  the caps in hand, and the boys are silhouettes on roughly a third of the
  jungle panels.
- The turned-away cap prints 60-200px or nothing; the census floor of 25px at
  panel scale keeps most of them, and a probe of the crown box settles the
  rest.

Vol. 15, three more titles read 2026-09-10 (forty-sixth batch), and the volume
now has three cap constructions in three stories:

| title | reference | red | green | blue | construction |
|---|---|---|---|---|---|
| *Donald Duck Tells About Kites* | 192 p5, three boys in a row | `#e51a20` 542px | `#4da23f` H111 511px | `#00a5d7` | side trim on a black cap, 266-601px |
| *The Ghost Sheriff of Last Gasp* | 013 p1, three boys in close-up | `#e61b1f` 6324px | `#4ca33e` H111 3969px | `#00a5d7` 6095px | full cowboy hats |
| *A Descent Interval* | 197 p8, three boys in close-up | `#e61b1f` 1354px | `#4ca33e` H112 165-263px | `#00a5d7` 518px | a patch at the back of a black cap |

- ***KITES PERMUTES THE KEY.*** Donald addresses the blue-trimmed boy as HUEY
  on 186, 191 and 192 (twice) and the red one as DEWEY on 186 p3; green is
  Louie by elimination. Consistent across all eight pages, so a per-story key
  rather than colourist drift. `cap_colour` records the printed ink.
- Ghost Sheriff's hats are the same blue as Donald's own hat, at adult size;
  the boys are bare-headed indoors on 006-007 p2.
- Descent's patches are small enough that `title_heads` lists them but a
  25px `capscan` floor at panel scale sometimes does not; the boys are
  bare-headed indoors on 194.

Vol. 14, *The Lemming with the Locket* read 2026-09-10: the volume entry holds
(`#e61b1f` / `#4ca33e` H111 / `#00a5d7`; Scrooge's coat `#a04453` maroon, his
hat band the roster blue). The boys carry their caps in their laps on 079 p8
and go bare-headed at the inn on 095. Reference panel 087 p1.



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

Vol. 11, from *A Christmas for Shacktown* 006 panel 4 (the three boys in a row,
caps AND matching mittens), confirmed on panels 2 and 5 of the same page:

| | |
|---|---|
| red (Huey) | `#e61b1f` H358.8 S0.88 V0.90 |
| blue (Dewey) | `#05a4d5` H194.1 S0.98 V0.84 |
| green (Louie) | `#4da23f` **H111** S0.61 V0.64 |

**Solid single-colour stocking caps with a pompom, the easiest construction in
the corpus** -- and the scarf and mittens are printed in the same ink, so most
panels carry the key twice. The green lands in capscan's `leafgrn` band, not
`green`: on the reference panel `green` reports 652 blobs and none in window
while `leafgrn` holds the cap. Its saturation is only 0.61, which clears
`heads.py`'s 0.55 floor but not by much, so a shaded green cap can drop out.

**But the story takes the caps off for a third of its length.** Indoors the boys
are bare-headed and carry no colour at all -- a census over every panel of 009,
010, 032 and 033 finds nothing on any of them -- and on 019 they are on Junior
Woodchuck duty in the brown coonskin cap instead, where the only roster ink left
is their MITTENS. That is where all 24 of the title's collectives come from;
every panel that printed a cap was named. Establish it per PAGE.

**Vol. 11 uses a DIFFERENT CAP CONSTRUCTION IN EVERY STORY, and the volume's
three inks are the only thing they share.** Four are now measured:

| story | construction | reference panel |
|---|---|---|
| *A Christmas for Shacktown* | solid pompom stocking cap, scarf and mittens to match | 006 p4 |
| the nine one-pagers | black crown with coloured segments | -- |
| *Gladstone's Usual Very Good Year* | grey fur winter cap with a coloured DIAMOND badge on the side | **050 p1** |
| *The Screaming Cowboy* | black skull-cap with a coloured STRIPE over the crown | **060 p8** |
| *Rocket Wing Saves the Day* | black crown with a coloured BAND showing as a curved side sliver | **078 p6** |
| *Gladstone's Terrible Secret* | the same banded black crown | **089 p2** |
| *The Think Box Bollix* | plain black skull cap with a small coloured SLIVER at the crown edge | **106 p1** |
| *The Golden Helmet* | black skull-cap with a coloured CRESCENT at the crown edge | **124 p1** |
| *Houseboat Holiday* | the same crescent -- but only for the first third of the story | **145 p6** |
| *Gemstone Hunters* | black skull-cap with a coloured BAND arching over the crown | **160 p3** |
| *The Gilded Man* | the same banded crown | **160 p3** (Gemstone) / **182 p2** |
| *Spending Money* | black skull-cap with a tiny coloured CHIP at the crown edge | **202 p2** |

Do not carry a construction across a story boundary; derive it from the
story's own clean panel before page 1.

- **THE TWELFTH CONSTRUCTION IS BELOW `capscan`'s DEFAULT FLOOR, AND THAT IS THE
  WHOLE FINDING.** *Spending Money*'s cap is a wholly black skull cap carrying a
  coloured chip of **10 to 60 pixels** at the crown edge -- a top chip plus a
  matching sliver down the cap's right side. `capscan.py` defaults to
  `MIN_AREA=25` and at that floor it finds ONE of the three boys on the
  reference panel; at **8** it finds all three. On 202 p2, blue `#07a5d5` 60px
  at (554,274), red `#b21e20` **10px** at (618,251), green `#4da544` **12px**
  at (734,264). Pass an explicit floor of 8 on this construction or the census
  says the caps are not printed when they are.
  Where the boys are drawn larger the same chip is 200px and reads easily --
  205 p8 gives 207px of blue, 198px of red and 206px of green, each with its
  side sliver, and `heads.py` places all three on their own heads without help.
- **THE FOLIAGE IS THE CAP GREEN TO THE DIGIT IN THAT TITLE.** *Spending Money*
  is a road-trip story and the roadside greenery prints `#4da33e` **H111.1
  S0.62 V0.64** -- Louie's ink exactly, in blobs of 1,000 to 7,000px on most
  outdoor panels. The car is `#e61b1f`, Huey's red, and it is the biggest red
  blob on the page for eight pages running; Donald's sailor cap and the sky are
  `#00a5d7`. All three inks have a full-size look-alike in this title, so
  nothing names a boy until `heads.py` has put the blob on a skull.
The inks themselves do hold: red `#e51b20`, blue `#00a5d7`,
green `#4da33f`/`#519d3e` (H108-112).

- **A SIXTH AND SEVENTH CONSTRUCTION, AND BOTH ARE THE SAME CRESCENT.**
  *The Golden Helmet* and *Houseboat Holiday* both use a black skull-cap
  carrying a small coloured crescent at the crown edge, and both print the
  volume's three inks cleanly when they print them at all: red `#e61b1f`
  H358.8 S0.88, green `#4da33f` H109-113 S0.61 V0.64, blue `#00a5d7` H194.0
  S1.00 V0.84. Their clean three-cap panels are *Golden Helmet* 124 p1 and
  *Houseboat* 145 p6 and 146 p4, each printing all three in one frame.
  Two things about that green. It lands in capscan's **`leafgrn`** band, never
  in `green` -- a `green: 0` line on either title means nothing. And on a
  crescent of a few hundred pixels ringed by black it **bleeds toward cyan**:
  the same cap reads H144-158 small and H109-113 large, with R and G holding
  to within a few counts and only B lifted. Rank it on S and V, which stay at
  0.6/0.6 where the blue sits at 1.00/0.84, rather than on hue.
  *Golden Helmet* also has an H168 `#37a28e` teal all over its sea pages --
  that one IS the water, and it is 55 degrees off the cap green.
- **Donald's own cap is the trap in both.** His sailor cap is a SOLID blue
  `#00a5d7` dome of 1,000-8,000px with no black crown, so it is the biggest
  blue blob in most panels; a nephew's blue crescent runs 180-2,100px and
  always has black around it. Read the construction, not just the hex.
- **Plan for the caps coming OFF.** *Houseboat Holiday* puts the boys in
  swimsuits from 147 p5 and they stay bare-headed to the end, so 148-153 carry
  no cap ink at all -- that is where nearly all of its collectives come from,
  and it is absence, not a declined reading. Their trunks are striped red,
  plain and blue, but NO panel shows a boy in both his cap and his trunks, so
  the stripes bridge to nothing. *Golden Helmet* does the same on a smaller
  scale: the boys are bare-headed for the whole of 119, indoors at home, and
  again in scattered later panels -- 122 p4, 125 p7, 130 p5, 131 p5.
- **A DIRECT ADDRESS CAN CONTRADICT A CLEAN CAP.** *Golden Helmet* 129 g12 is
  a boy with 1,730px of unambiguous `#4ea240` H111.4 green who predicts the cut
  headland, and 130 g0 answers him by name: "DEWEY, YOU'RE RIGHT!". It is the
  only line in 32 pages that names a single nephew. Recorded Dewey with
  `cap_colour: green` -- the name wins, the printed ink is kept. Whether that
  is one mis-coloured cap or a permuted palette is the reviewer's call, and
  every other green in the title is still recorded Louie on the convention.

- **IN THE TWO BANDED-CROWN TITLES THE FOLIAGE SITS INSIDE THE CAP GREEN'S
  HUE, AND ONLY SATURATION SEPARATES THEM.** *Rocket Wing* plays out in a back
  yard and *Gladstone's Terrible Secret* on lawns and hedges, and the greenery
  prints **H100-108 at S0.54-0.57** against caps at **H108-113 at S0.57-0.63**
  -- as little as three degrees apart on *Gladstone's* 089 p2, where a
  220,000px hedge swallowed a cap outright in a proximity-merged census. Key
  the census on hue AND saturation, never on `capscan`'s band names, which
  file both under `leafgrn`.
  Two blobs that passed every hue and saturation test and were still not caps:
  *Gladstone's* 094 p6, 5,329px `#4da33d` H110.6 S0.63 at head height, is the
  LAMP BASE; and 097 p5, 4,115px at S0.62, is on the FLOOR beside Gladstone's
  shoes. [[project_cap_blob_must_sit_on_a_head]] costs nothing to apply and
  caught both.
  Indoors the same caps drop below `capscan`'s saturation floor entirely --
  095 g6's green probes at `#536c4a` H104.1 **S0.31** with the floor dropped,
  and *Rocket Wing* 081's potato-cellar caps at `#6c9c70` S0.31 and `#a5352a`
  H5.4 -- so a cellar or an interior means probe, not scan.
- **The GREEN is the anchor in *Gladstone's Usual Very Good Year*, and reading
  it the other way
  round cost two names.** The pass argued that the blue prints `#00a5d7` H194.0
  S1.00 V0.84 in every panel, so a cool badge that is not exactly that must be
  the green -- and 054 g9's `#1da39e` (H177.8 S0.82 V0.64) turned out to be a
  **shaded blue**, which the review made Dewey and which then flipped 054 g11 as
  well. Anchor on the green instead: it runs **H117-130** (`#4e9c51`, `#50984d`,
  `#4da33e`) and never leaves that range, so anything cooler than about H140 is
  the blue however muddy it looks. Value does not help here -- the shaded blue
  sits at V0.64, the green's own value.
- **In *The Screaming Cowboy* the blue drifts too, and VALUE separates them.**
  The cap green prints V0.64 at any hue (`#4da33e` H111, `#2ca487` H165,
  `#2da49c` H176, `#3ba487` H163); the blue never drops below V0.74
  (`#00a5d7` V0.84, `#16a4bd` V0.74). Saturation agrees -- green S0.59-0.78,
  blue S0.88-1.00 -- but hue does not, H176 against H189 being only 13 apart.
- **Two look-alikes in that title, both of which the eye would take for a cap.**
  Donald's beret is `#04a4d5`, Dewey's blue exactly, so only size and position
  separate them; and the inn's teal wainscot is `#37a28e` H168.8 at the green's
  own S and V, in big flat blobs behind the boys on 059. Cap green there is
  H108-112, the wainscot H168-169. The pine trees are a third: `#4da140` H111,
  the cap green to two decimal places, so a green blob has to be shown sitting
  on a head before it names anybody.
- **A grey cap with a coloured diamond is not by itself a nephew.** The Junior
  Woodchucks in *Gladstone's* wear the same cap -- 052 p2 has a pig-faced club
  member in one with a red diamond. Check the head under the badge.

- **THE SLIVER IS THERE OR IT IS NOT, AND THE SAME BOY GOES BOTH WAYS ON ONE PAGE.**
  *The Think Box Bollix* prints the coloured sliver only at certain head
  angles: 106 p1 shows all three crowns from behind, blue/red/green, big
  and unmistakable, and 105 p8 two pages earlier returns `red 0 / green 0 /
  blue 0` from `capwide` at a 20px floor for the same three boys in the
  same scene. Nineteen of the title's 23 collectives are that, an outright
  silhouette (105 p5, 106 p4) or the bare-headed bedroom on 101 -- absence,
  not a declined cap. Where two crowns did read the third was named by
  elimination, which is where 3 of its 15 names came from.
  Two look-alikes in it: **Gyro wears a RED cap** through half the story and
  a red-banded straw hat through the rest, and the foliage prints **H100.9**
  against the cap green's **H111**, eight degrees apart at almost the same
  saturation.

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

Vol. 12, from *Only a Poor Old Man* 016 p5 (the three boys in a row, caps big
and lit, one balloon and one tail each) read on 2026-09-05. The cap is a
**black crown carrying a coloured band down the side**:

| | |
|---|---|
| red (Huey) | `#e82720` H2.1 S0.86 V0.91 |
| blue (Dewey) | `#00a5d7` H194.0 S1.00 V0.84 |
| green (Louie) | `#5ca93a` H101.8 S0.65 V0.66 |
| shaded green seen | `#58943c` -- same hue, S0.58 V0.58 |
| foliage and grass | `#5caa3c` H102.5, the cap green to a decimal place |
| a second, darker green | `#33a250` H136, pines and deep foliage |

- **SCROOGE'S COAT IS `#e82720` -- HUEY'S EXACT RED -- AND IT IS THE BIGGEST
  RED BLOB IN NEARLY EVERY PANEL.** A whole-title census found 771 hits of
  that hex, the largest 17,609px, and almost all of them are the coat. The
  blue is worse: **Donald's sailor cap and Scrooge's top-hat band both print
  `#00a5d7`**, Dewey's exact blue, 439 hits in the title. Neither ink names a
  boy until the blob has been shown sitting on a small head.
- **The green is also the grass.** Cap green H101.8 against foliage H102.5 --
  under a degree apart. `heads.py` placing it on a skull is the only test that
  works; `capscan`'s band names decide nothing here.
- **One panel prints the blue at H154.** 016 p5's middle cap probes
  `#38a677` H154.4 S0.66, and it is the ONLY hit at that hue in the whole
  32-page title. It is the blue, read by ranking the two cool caps inside
  that panel: the boy beside him carries `#5ca73b` H101.7 at the identical
  S0.65, so a band 52 degrees cooler at the same saturation is the other cool
  ink and not a shaded green. Elimination agrees -- red and green are both
  taken in the row. A 3.2x crop shows it plainly teal beside a plainly grass
  green.
- **The caps come off, and often.** The boys are bare-headed for the whole
  Money Bin sequence on 014 and in the hammock on 025; 016 p7-p8 and 032 p1-p2
  are flat night silhouettes. Those collectives are absence, not a declined
  cap -- say which in the note.
- **`UNCA SCROOGE` is a nephew and `UNCLE SCROOGE` is Donald, on all fourteen
  occurrences.** The story never mixes them. It settles every wide shot and
  every off-panel voice in the title on its own, and it is worth checking for
  in any Scrooge story before spending an image on a tail.
- **One colourist slip, and the address won.** 028 addresses a boy as LOUIE in
  panel 2 and then draws him in a RED band in panels 3, 6 and 8, while 029 p5
  and p7 draw Louie in a clean green. Recorded as `Louie` with
  `cap_colour: red`, per [[feedback_colourist_error_breaks_the_chain]] --
  worth a retouch note.


**Vol. 12's *The Menehune Mystery* prints the cap on ONE page of thirty-two,
and names no nephew anywhere in its dialogue.** A direct grep for
HUEY/DEWEY/LOUIE across both engines returns nothing in 32 pages, so there is
no address chain to fall back on: every nephew call rests on a cap or a tail,
and 74 of its 398 groups end up collective.

The reason is costume, not colour. **Aboard ship (128-135) the boys wear
identical WHITE SAILOR SUITS AND HATS**, and **on the island (136-151) they are
bare-headed** -- plain white skull and hair tuft, confirmed at 4x with a full
head-height of sky above the crown on 143 p1. Neither is a declined reading.

**But 122 does print the bands, and an early draft of this entry said the title
had none.** 122 p8 shows all three crowns: middle `#e22721` H1.9 S0.85 and
right `#06a4d4` H193.4 S0.97 probed on the heads, the left one bare and
therefore Louie by elimination; 122 p4 shows a clean green band on the nearest
boy. Three panels opened at random on this title all happened to be capless.
**Three panels is not a sweep.**

Three decoys run the whole 32 pages and each is the largest blob of its colour
in most panels:

| | |
|---|---|
| Scrooge's coat | `#a04453` H350.2 S0.57 -- NOT the `#e82720` cap red, but it is the biggest red on almost every page |
| Donald's sailor cap and Scrooge's top-hat band | both `#00a5d7`, Dewey's exact ink, and between them nearly every blue at head height |
| island foliage | `#5caa3c` H102, the cap green to a decimal place, in blobs up to 142,000px |

Add the ducks' **red bow ties** at neck height, which `heads.py` reports as red
on a head all through the Duckburg chapters, and the **Beagle Boys' yellow
number plates**, which are the story's most frequent piece of background
lettering (twenty-odd groups).

`The Beagle Boys` is supplied by the database as a **bare roster value** for
this story, like `Black Pete` in Vol. 3 -- no `other:` prefix, and 76 groups use
it. The genuine `other:` values are just four: `other:Opu Nui` (17),
`other:the birds` (6), `other:the Coast Guard admiral` (2) and
`other:the menehunes` (1).

**The story italicises every Hawaiian word it then glosses** -- HOA, KAMA'AINA,
MALIHINI(S), KANES, PUPULE, HAOLES -- and sets MENEHUNES! bold and upright
instead. Confirmed at 3x on 143 g10, where MALIHINIS and KANES are plainly
slanted against upright neighbours in the same balloon.

Vol. 13, from *The Hypno-Gun* 057 p5 and 057 p8 (the three boys in a row, then
the same three seen from above) read on 2026-09-05 -- the volume's first title.
The cap is a **black skull cap carrying broad coloured segments over the crown**,
a gore pattern of alternating black and colour, 400-1600px and unmistakable:

| | |
|---|---|
| red (Huey) | `#e61b1f` H358.8 S0.88 V0.90 |
| blue (Dewey) | `#04a4d5` H194.0 S0.98 V0.84 |
| green (Louie) | `#4da33e` H111.1 S0.62 V0.64 |

The three inks are Vol. 11's and Vol. 10's to within a count or two, so only the
construction is new. The green lands in `leafgrn`: **`green` reports 0 blobs on
every panel of the title**, which is the standing trap and not a finding about
this story.

- **THE CAPS COME OFF FOR THE FIRST TWO PAGES AND COME BACK FOR THE LAST.** On
  048 and 049 all three boys are bare-headed -- plain white skulls with a hair
  tuft -- and `capscan` at an **8px** floor returns `leafgrn 0` on every panel
  of both pages, with 049 p5 (the three of them in a row, a balloon each)
  returning **zero blobs in all three bands**. That is absence, not a declined
  reading, and it is why every nephew name on those pages has to come from the
  words. They are capped again on 057, which is where the palette above comes
  from.
- **THE ADDRESS CARRIES THE WHOLE OF 048.** The boy with the gun names his first
  target LOUIE and his second DEWEY, and then asks DEWEY to hypnotize him in
  turn -- so he is neither, and by elimination he is Huey. Six of the page's ten
  groups hang off that one chain. Panel 1 at 1.7x settles which boy holds the
  gun (the right-hand one) and therefore which is Louie.
- **049 p5 IS THREE TAILS AND THREE BOYS AND STILL NAMES NOBODY.** Three
  separate balloons, one tail each, so they are three different speakers and not
  a chorus -- but with no cap and no address anywhere on the page, left-to-right
  order gives an order and no names. Recorded `nephews` three times over, and
  the reason is worth keeping distinct from the ordinary under-naming case:
  the tails were traced and the answer still is not there.
- **Scrooge's coat is `#a04453`/`#9f4553`**, H350-351 S0.57, and it is the
  biggest thing in the red band on most panels of both this title and *Spending
  Money*. It is 8 degrees off the cap red and half its saturation, so the hex
  separates them cleanly -- but a red-band blob count does not.


**Three more Vol. 13 titles, read 2026-09-06: *Trick or Treat*, *Hobblin'
Goblins* and *Omelet*.** The three inks above held on every panel that printed
them, so the palette is settled for the volume. What these titles add is the
two ways it goes wrong.

**The cap green runs H103-132 and the `green` band is never it.** Measured
across the batch: `#4da33e` H111, `#4fa43e` H110, `#45a257` H132, `#4f9c5a`
H129, `#60a34a` H105, `#6ca257` H103, `#69a670` H127 -- all at **S0.37-0.63**.
Every one of them lands in `leafgrn`, and capscan's `green` band (H140-182)
held nothing but grass, hedge and foliage all batch long: `#009e49` H147.7
S1.00 on *Hobblin' Goblins*, `#009f8b` H172.5 S1.00 on *Omelet*. So `green: 0`
is the normal reading here and says nothing. Saturation is the discriminator,
not the band name: the foliage sits at S0.94-1.00 and the caps at S0.4-0.6.
Note also that a cap below about S0.4 drops out of `leafgrn` too -- *Hobblin'
Goblins* 045 p3 returns `leafgrn 0` for a cap that probes `#69a670` H126.9
S0.37 -- so `probe.py` on the head, not the census, settles those.

**Four decoys that print a cap ink exactly.** Each is large, none is on a head:

| | | |
|---|---|---|
| apples | `#e61b1f` | *Hobblin' Goblins* 042 and 043 -- the identical hex to the cap red, 40+ blobs a panel |
| picket fence | `#00a5d7` | *Hobblin' Goblins* 044 p1 -- the identical hex to the cap blue, over 3000px |
| grass | `#54b041` H109.7 | *Omelet* 060 p8 -- the cap-green hue exactly, in 13,000-15,000px blobs |
| hens' combs | `#e41a20` | *Omelet* 060 and 062 -- the cap red on every bird in a flock of 10,000 |

Add to these the adult reds already known in the volume: Gyro's trousers
`#a04453` H350.2 S0.57 and Scrooge's coat at the same hex. The rule they all
serve is the standing one -- a blob has to sit on a HEAD -- but on these titles
it is doing most of the work, not a little of it.

**And one title prints no cap ink at all.** *Trick or Treat* puts the three
boys in Halloween costume for all 32 pages and never takes it off, so
`cap_colour` is null wherever the costume is black or the panel is a
silhouette. The costumes carry the convention instead, and this was confirmed
with the reviewer before the pass was written: the red devil hood and suit
sample `#e61b1f` and the black witch hat's band `#00a5d7` -- both on a head
covering -- with the yellow ghost sheet (`#f8ea89`, not a roster colour) the
third by elimination. The assignment is stable across every page: witch hat and
loot sack = Dewey, ghost sheet and jack-o'-lantern pole = Louie, devil hood and
pitchfork = Huey, and the three are separable even in the story's flat
silhouette panels by hat point, horns and curled hood.


**Vol. 13's *My Lucky Valentine* puts the three inks on the BOW TIE, not the
cap.** All three boys wear the identical plain brown Junior Woodchuck coonskin
cap with a yellow diamond badge, and the convention is carried on the Woodchuck
bow tie under the chin. Reference panel 099 p1, the three sitting in a row: red
`#e51a20` at panel x204-378, blue `#04a4d5` at x444-517, green `#4da33e` H110.7
at x639-826, each under its own skull. Two decoys: **their MITTENS are the same
blue as Dewey's bow and every boy wears a pair**, which is the biggest blob in
most panels, and **Donald's own bow tie is the same red**. On 098 the boys are
in plain black jerseys with no bow tie at all -- a whole-panel census returns
only the red exercise mat and the blue window curtains -- so that page's
collectives are absence of the convention rather than a declined reading.
The title also uses an **offset fan** on 107 p6: three balloons, three boys,
and all three tails sitting about 150px LEFT of their own boy with the leftmost
landing on bare brickwork.

**Vol. 13's *Much Ado about Quackly Hall* is the volume's second costume title,
and the mapping is fixed for all ten pages**: red bandana and eyepatch = Huey
(`cap_colour: red` -- the bandana counts as the ink), black pirate tricorn =
Dewey (`blue`, and his cap band shows inside the brim), gold paper crown = Louie
(`null`, named by elimination). Read it off the sole-figure panels -- 140 p1,
145 p1 and 145 p4 for the bandana; 140 p4 and 141 p2 for the crown -- before
page 1. Two decoys run the whole title: the bandana is the same `#e61b1f` as the
cap red, and the movie wind machine on 144-145 is painted in it too, in blobs up
to 42735px.

**Two more Vol. 13 titles paint a major prop in the cap red**, which makes the
red band unusable for whole pages: *Worm Weary*'s board fence and stage curtain,
and *The Master Rainmaker*'s aeroplane (23380px of `#e61b1f` filling the frame on
158 and 161). In both, Donald's own hat is the volume's Dewey blue at `#00a5d7`
and up to 14809px -- larger than any cap in either story -- so size the head
before naming a blue cap.

**Vol. 13's cap inks held everywhere they printed clean** across this batch:
red `#e61b1f`/`#e41a20`, blue `#00a5d7`/`#04a4d5`, green `#4da33e` H111. The
green again lands in `leafgrn` and never in capscan's `green` band; and a cool
sliver at H171-180 is the BLUE, not the green -- *The Talking Dog* 120 p3
(`#2ea3a3` H180.0) and *The Master Rainmaker* 167 p8 (`#2a9f8f` H171.8) are both
that shape, the first confirmed by review and the second corrected for being
named at all at S0.74.

**Vol. 12's *Back to the Klondike* keeps the volume's black cap with a coloured
side band, but at 30-80px** -- capscan at a 25px floor finds the slivers mixed
with noise, so the reading is a 1.0-1.5x crop, not a census. Reference panel
049 p5, the three in a row: green, red, blue left to right. Four decoys, all
live for the whole 32 pages:

| | |
|---|---|
| Scrooge's coat | `#5caa3c` H102.5 -- the SAME ink as Louie's band |
| Scrooge's top hat band | `#00a5d7` -- Dewey's blue |
| Scrooge's duffel bag | `#4da33e` H111 -- a second green that is never a cap |
| the boys' trail packs | red, blue and green BEDROLLS of the roster inks |

- **The caps come off indoors.** Through the cabin scenes on 070-072 the boys
  hold their caps in their hands; the band still names them, but it has to be
  read off the cap in the hand rather than off a head.
- **A colourist swap runs through 071-072.** Dewey names the third boy in 071
  g1 -- LOUIE'S ALREADY TAKEN THE BEANSHOOTER AND SCRAMMED -- so the two left
  in the cabin are Dewey and Huey; but the boy who runs off with the gun is
  printed RED and the one left behind is printed GREEN. The address wins and
  the printed ink is recorded as observed, per the standing rule.
- **`UNCA SCROOGE` is a nephew and `UNCLE SCROOGE` is Donald** holds on this
  title too, on every occurrence -- as it did on *Only a Poor Old Man*.

**Both Vol. 12 titles in this batch draw balloons with MORE THAN ONE TAIL.**
*Somethin' Fishy Here* 079 g7 and 082 g6 carry two apiece and 082 g10 three;
*Back to the Klondike* 074 g6, 075 g4 and 075 g9 each carry three spread across
the row of boys. They are long narrow pointed spikes, not the balloon's own
scalloped bottom, and each one lands on a different figure. Two or three
distinct figures receiving a tail is two or three speakers, so the group is
`nephews` however readable the bands are -- record the bands in the note so a
reviewer can see it was not a declined reading.

**Caption boxes in these three titles are all set in a slanted display hand.**
That slant is the house hand for a caption, not emphasis, so no `[i]` is marked
on any of them. Contrast *My Lucky Valentine* 102 g6/g7 and *Somethin' Fishy
Here* 079 g2, where a quotation is set slanted INSIDE an otherwise upright
balloon and IS marked -- the same treatment as the Cornelius Coot inscription
in Vol. 11 072. The corpus is split on this (31 Vol. 13 narration groups carry
`[i]`, 46 do not), so it is flagged for the reviewer rather than settled here.


**A third Vol. 12 title, *The Secret of Atlantis*, and its caps come and go by
setting.** It is a Scrooge story with the boys in and out of it, and the cap is
the volume's black crown with a coloured side band -- but only outdoors. Cap
reference **164 p8**, the three boys at the bakery window, all three bands big
and clean:

| | |
|---|---|
| green (Louie) | `#5caa3b` H102.0 S0.65 |
| red (Huey) | `#e61b1f` H358.8 S0.88 |
| blue (Dewey) | `#00a5d7` H194.0 S1.00 |

**Where the bands are and are not printed, checked panel by panel:** banded on
161 p1 (blue/red/olive left to right), 164 p8, 167 p1/p3/p4/p6 and 168 p1/p5/p6;
**bare-headed** on 158 p4 -- capscan over the whole panel returns `red: 0
blob(s) total`, `green: 0`, `leafgrn: 0`, and a 2.4x crop shows plain white
skulls with a hair tuft, the four blue blobs being the boys' collars at chest
height -- and again on 156 p1 and all of 175. So `capscan` zeros on this title
mean two different things on two different pages, and only the crop separates
them.

**The third boy's band is repeatedly an unreadable shaded olive** rather than a
roster green: 161 p1 prints blue and red cleanly and leaves the third at an
olive too desaturated to name, which is the *two named leaves the third* case.
On 167 p1 the middle boy's crown probes `#7ba85a` **H94.6** S0.46, 175px --
`capscan`'s `leafgrn` band starts at H95, so its `leafgrn: 0` misses a real
green cap **by four tenths of a degree**. Probe the crown before believing that
zero.

**And from 175 p5 the caps stop mattering: everybody is in a diving helmet.**
The story hands back the names instead -- 176 g1 and 183 g7 both call the two
divers HUEY AND DEWEY, and 185 g0's caption puts LOUIE on the boat -- so the
underwater collectives are a fact about the helmets, not a declined reading.
Say which in the note.

**Two levers do most of the adult work in this title, and both are free.**
`UNCA SCROOGE` is a nephew's form and `UNCLE SCROOGE` is Donald's, on all 19
occurrences, exactly as in *Only a Poor Old Man*. And inside the identical grey
diving suits **Donald is the smooth-headed figure and Scrooge the one with
muttonchop whiskers round the beak plus a red chest fitting** -- checked at 1.7x
on 172 p1, 173 p1 and 174 p6, where Donald is the left figure in all three.
That one crop settled about sixty groups.

**The decoys are the volume's usual ones**, and Scrooge is in nearly every
panel: his coat `#a04453` H350.2 is the biggest red on most pages, his top-hat
band and Donald's sailor cap both print `#00a5d7`, and the bakery/roadside
foliage sits at H102, the cap green to a decimal place.


Vol. 15, from *Fix-up Mix-up* 036 p1 (the splash -- the three boys in a row
below Donald's ladder), read 2026-09-07. The volume's cap is a **black crown
carrying one broad coloured band** down the front and side:

| | |
|---|---|
| red (Huey) | `#e61b1f` H358.8 S0.88 |
| blue (Dewey) | `#08a4d4` H194.1 S0.96 |
| green (Louie) | `#3f8164` H153.6 S0.51 |

**The green is MUTED and the foliage is not.** `#3f8164` sits at S0.51 against
this volume's `#009e49` H147.7 **S1.00** grass, hedge and shop-door green, and
the two are only about six degrees apart in hue. Saturation is the
discriminator, exactly as in Vol. 13; a `green`-band blob count says nothing on
its own. Re-probed on a second panel the cap green came back `#319f60` H155.5,
so the band runs H153-156.

**But two of the volume's three 1953 titles print no cap at all**, and that is
the thing to establish before page 1 rather than after:

| | |
|---|---|
| *Wispy Willie* | the boys are **bare-headed** for all ten pages -- white skull, hair tuft, no cap (025 p8, 023 p5 at source resolution) |
| *The Hammy Camel* | **bare-headed** for all ten pages (027 p4, 034 p8) |
| *Fix-up Mix-up* | black crown with the coloured band, readable whenever the crown faces the reader |

So a `capscan` zero on a Vol. 15 title is very often absence of the convention,
not a declined reading -- but *Fix-up Mix-up* proves it is per title and not per
volume, and it yielded **nine named nephews in 106 groups**. Read one panel of
the boys at source resolution before assuming either way.

**Donald wears the `#00a5d7` sailor cap through all three titles**, and in
*Fix-up Mix-up* it is the largest blue in almost every panel -- 2,000-12,400px
against a nephew band of 300-1,200px. Size the head before reading a blue blob
as Dewey's band. His **red bow tie** is the matching trap in the red band, at
400-2,000px, and it sits BELOW the beak where a band sits above the crown.

**Three decoys that are not caps and were each measured on a nephew's own body:**
a blue jug and a green bundle of tule roots the boys CARRY on *Wispy Willie*
022 p6 (`#06a5d5` and `#049c48`, ~570px each, at chest height); a red-and-white
striped BALL in the wagon on *Fix-up Mix-up* 038 p1; and blue MARBLES on the
floor of *Wispy Willie* 023 p5. All four sit where a census expects a cap and
none is on a head.


**A fourth Vol. 15 title, *Turkey Trot at One Whistle*, and its cap green is
NOT the volume's.** Reference panel 050 p8, the three boys' heads in a row: the
construction is the volume's black crown with a coloured band, but here the
band is mostly hidden and shows as a **small sliver of 98-218px** at the
crown's edge rather than the 300-1200px of *Fix-up Mix-up*.

| | |
|---|---|
| red (Huey) | `#e31b20` / `#e61b1f` H358-359 S0.88 |
| blue (Dewey) | `#05a5d5` / `#00a5d7` H194 S0.97-1.00 |
| green (Louie) | `#4da33e` H111.1 **S0.62 V0.63** |

**That green lands in `leafgrn`, never in capscan's `green` band** -- H111, not
the H153.6 the *Fix-up Mix-up* entry above gives. On this title `green: 0` says
nothing at all; it is the Vol. 13 behaviour, not the Vol. 15 one.

**Donald wears a GREEN stationmaster cap through the whole title, and it is the
decoy that costs a name.** It prints `#4f753b` / `#4d743b` **H99-103 S0.47-0.50
V0.45** -- close enough to Louie's band in hue to be mistaken for it, and the
pass did exactly that on 048 g2 before review caught it. **Value separates them
cleanly: Donald V0.45, Louie V0.63**, and so does hue at H99-103 against
H110-112. Where that is still not enough, the CONSTRUCTION decides -- Donald's
is a kepi with a black brim, the boys' a black crown with a band.

Four more decoys, all measured on this title: the boys' jerseys carry a
**pale-blue collar and bow** at neck height (`#0aa5d3`, up to 1380px); the
kitchen shelf on 050 p2 holds **blue, yellow, red and green books** in exactly
the roster inks; the bedroom wall on 049 p8 is `#4da33e` H111 S0.62 in a
**16,367px** blob, the cap-green hex exactly; and the turkey crates on 053 p8
are the same green. Every one of them sits where a census expects a cap.

**And the nightclothes actively lie.** On 050 p6 the boy in BLUE pyjamas wears
a clean RED band and the boy in GREEN pyjamas a clean BLUE one. Read the crown,
not the costume, on that page.

**A fifth Vol. 15 title, *Raffle Reversal*, and its band is a sliver like
*Turkey Trot*'s, not the broad band of *Fix-up Mix-up*.** Reference panel
**056 p4**, the three boys under one balloon: the band shows as a small patch at
the crown's upper-left plus a second sliver at the left side, 71-75px each.

| | |
|---|---|
| blue (Dewey) | `#00a5d5` H193.7 S1.00 |
| red (Huey) | `#e21d21` H358.8 S0.87 |
| green (Louie) | lands in `leafgrn` at `#4fa43d` **H109.5** S0.63 (057 p3), never in capscan's `green` |

So this title behaves like *Turkey Trot*, not like *Fix-up Mix-up*: `green: 0`
says nothing, and the third boy is repeatedly shaded past reading -- 056 p4's
left band probes `#4e7474` H180 **S0.33** and names nobody, so he is Louie by
elimination with `cap_colour` null.

**GLADSTONE WEARS A `#00a5d7` HAT, NOT ONLY THE BOW TIE.** That is Dewey's exact
ink and the same ink as Donald's sailor cap, and Gladstone is in two thirds of
the panels, so a blue blob on a head in this title is his as often as Donald's.
What separates them is the **maroon `#a04453` suit** underneath -- `heads.py`
reports both as `blue` on a head and cannot tell them apart. Read at 2.6x on the
splash, where he is held aloft holding the winning ticket.

**The bold cut is about 1.15, and one word is only half bold.** Whole-word bold
sits at 1.27-1.43 and everything unemphasised at 1.06 or below, so the gap is
wide -- but `HOWDEE,` comes back at 1.19 on three separate pages because Barks
sets **`HOW` plain and `DEE` heavy inside the one word**, three times in this
story (056 g16, 058 g3, 059 g4). A ratio between the two populations is worth a
crop before it is called clean.

**Three more Vol. 15 titles, read 2026-09-08, and all three put the green in
`leafgrn`.** *Fix-up Mix-up*'s H153.6 green is now the exception in this
volume, not the rule: every title measured since lands at H109-116, so on a
Vol. 15 title `green: 0` should be read as *the band is empty*, not as *no
green cap*.

| title | reference panel | red (Huey) | green (Louie) | blue (Dewey) |
|---|---|---|---|---|
| *Flour Follies* | 066 p2, three boys leaping along a wall | `#c4292f` H357.7 S0.79 dim, `#de1b1f` elsewhere | `#4fa340` **H110.9** S0.61 | `#05a6d5` H193.6 S0.98 |
| *The Price of Fame* | 077 p6, the only frame that prints all three | `#e51a20` H358.5 S0.89 | `#5b9757` **H116.2 S0.42** | `#10a1c1` H190.8 S0.92 |
| *Midgets Madness* | 095 p8, two heads in close-up | `#e61b1f` H358.8 S0.88 | `#4da33f` **H111.6** S0.61 | `#00a5d7` H194.0 S1.00 |

**The bands are small and often shaded below capwide's own floors.** On *Flour
Follies* 070 p6 the plain census returns `green: 0` and no red on any head, and
probing the three crowns finds green 77px `#248a47`, red 221px `#de1b1f` and
blue 61px `#06a5d4` -- three clean roster inks, none of which the screen saw.
*The Price of Fame*'s green at **S0.42** sits barely above capscan's 0.40
saturation floor, and a per-panel band sweep of that whole title finds `leafgrn`
on exactly three panels out of eighty. **Probe the crown before writing any
absence on a Vol. 15 title.**

**THE CAPS COME OFF INDOORS, AND *The Price of Fame* IS ALMOST ALL INDOORS.**
Six of its seven named nephews come from one page's four outdoor panels; the
other forty nephew groups are collectives forced by the art, with capscan
returning 0 blob(s) total in every band on most indoor panels. *Flour Follies*
is the same shape at smaller scale. Establish which way a Vol. 15 title runs
from one indoor panel and one outdoor panel before page 1 -- and note that
*Midgets Madness* is the reverse case, outdoors at a fairground for ten pages,
and yields 21 names.

**Four decoys measured on a nephew's own head in these three titles**, all of
them ink of a roster colour sitting exactly where a band would:

| decoy | title | what it is |
|---|---|---|
| `#00a5d7` H194.0 S1.00, a=1025-1263 | *Flour Follies* 070 p6, 072 p5 | **Scrooge's top hat carries a Dewey-blue band**, larger than every nephew band on the page put together |
| red diamond, a=506-646 | *Midgets Madness* 087 p4, 090 p5 | **Donald's lavender crash helmet**, and the racing men wear the same helmet |
| `#009e49` H147.7 S1.00 | *Midgets Madness* throughout, *The Price of Fame* 082/083 | the foliage green, seven degrees off the cap's leafgrn and fully saturated -- and on 082 p8 it is an **ICE BAG on a nephew's head** |
| `#a04453` H350.2 S0.57 | *Flour Follies* 066 | the brick wall, in the red band at head height for a whole page |

Add to them *The Price of Fame* 085 p2, where the head census hangs red on all
three boys at once: those blobs sit at y181-214, above every skull top at
y273-278, and are the striped awning behind them.

**Two balloon shapes worth knowing in this volume.** Barks letters SINGING in a
balloon with a bumpy outline and no bubble trail -- *The Price of Fame* 078 g9
comes through a closed door's KEYHOLE that way, and 079 g5 joins Donald's head
directly. That is `dialogue`, not `thought`; the thought balloons in the same
titles have a cloud-scalloped edge AND a trail of separate outlined bubbles, and
the two are told apart at 1.0x. The same bumpy outline carries an ENGINE on
*Midgets Madness* 095 g8, where the marks between the balloon and Donald are
sweat drops rather than bubbles and his beak is shut.

**Two more Vol. 15 titles, read 2026-09-09, and between them the volume's cap
green now spans FOUR hues.** *Fix-up Mix-up*'s H153.6 and the H109-116 of
Turkey Trot, Raffle Reversal, Flour Follies, Price of Fame and Midgets Madness
are no longer the whole range:

| title | reference panel | red (Huey) | green (Louie) | blue (Dewey) |
|---|---|---|---|---|
| *Salmon Derby* | 098 p4, three boys in a row on the beach | `#e61b1f` H358.8 S0.88 | `#4da13f` **H111.4** S0.61 | `#00a5d7` H194.0 S1.00 |
| *Cheltenham's Choice* | 107 p4, three boys and Donald in the trailer | `#dc1f21` H359.4 S0.86 | `#45a252` **H128.4** S0.57 | `#00a5d7` H194.0 S1.00 |

**And each of those two titles prints Louie's band at more than one hue.**
*Salmon Derby* gives H111.4 on 098 p4, 098 p7 and 097 p3 but `#179557`
**H150.5** on 096 p4 and `#159a52` H147.5 on 099 p5 -- the second value is the
volume's own foliage hue, so on the H150 pages the band and the trees are the
same ink and only `heads.py` putting it on a skull separates them.
*Cheltenham's Choice* is worse: H128.4 on 107 p4, `#43a048` **H123.2** on
108 p4, `#4da33f` H111.1 on 110 p7 and 113 p2, and `#029e47` **H147.7** on
111 p4 -- four hues in ten pages, the last of them the foliage green printed as
a broad clean band on a black crown. **Do not carry a green hue from one panel
of a Vol. 15 title to the next; probe each crown.**

**A COOL INK AT H171-176 RUNS THROUGH BOTH TITLES AND NAMES NOBODY.** Salmon
Derby puts `#51857f` H173.1 S0.39 on 101 p7's third boy, `#26a290` H171.3
**S0.77** on 103 p5's, and H173 on both readable crowns of 102 p2; Cheltenham's
Choice puts `#04a29b` H176.6 **S0.98** on 111 p4's left boy and `#2fa37c` H162
on 115 p1's. Saturation does not rescue these -- S0.98 is as saturated as the
roster blue -- because the HUE sits squarely between the green band's ceiling
and the blue band's floor. Every one of them had to be resolved by elimination
off the other two boys, and where the other two were not both clean the group
stayed collective. Treat H165-180 on a crown as an unreadable band, not as a
shaded blue and not as a shaded green.

**Two decoys measured on these titles.** On *Salmon Derby* the bay water is
`#0182bb` H198.6 S1.00 in blobs of 12,000-19,000px, right beside the boys'
heads on 100, 101 and 104; on *Cheltenham's Choice* the bayou is the same ink
at 1729px directly under a nephew's chin on 108 p4. Both are more saturated
than any nephew band on their pages. And Gladstone's `#00a5d7` hat is in two
thirds of Salmon Derby's panels, on top of Donald's sailor cap in the same ink.

Vol. 15, the four titles read 2026-09-09 (forty-fourth batch). All four use the
volume's leafgrn cap green and its stable red and blue, but each puts an ADULT
in one of the three inks:

| title | reference panel | red (Huey) | green (Louie) | blue (Dewey) |
|---|---|---|---|---|
| *Too Safe Safe* | 140 p2, three boys on the stoop | `#e51a1f` | `#4da33e` **H111.1** | `#00a5d7` |
| *Search for the Cuspidoria* | 147 p5, two boys in close-up | `#e61b1f` | `#4da23f` **H111.1** S0.6 | `#08a4d4` H193.8 |
| *New Year's Revolutions* | 156 p4, three boys in a row | `#e61b1f` | `#4ea23f` **H111** | `#00a5d7` |
| *Iceboat to Beaver Island* | 166 p1, the splash row | `#e61b1f` | `#4da33f` **H111** | `#04a4d6` |

- ***Cuspidoria* prints its green at a SECOND hue**: `#3c907b` **H165.0 S0.58**
  on the splash, inside the H165-180 dead band, against `#4da23f` H111 on 147
  p5 and 150 p8. On the splash it was named only by elimination against a
  clean blue and a clean red in the same row.
- **The adults wear the roster inks.** Donald's sailor cap is `#00a5d7` in
  *Too Safe Safe* and `#02a5d5` in *Cuspidoria*; he wears a blue winter cap in
  *New Year's Revolutions* and a **maroon `#a04453` coat** for the whole of
  *Iceboat*. Scrooge's top-hat band is `#04a4d5` in *Cuspidoria* and his coat
  is the roster red there. In *New Year's Revolutions* 162 p2 there are two
  blue caps in one panel, one a nephew and one Donald.
- **Two of the four are WINTER stories and take the caps off indoors.** *New
  Year's Revolutions* is capless on 160, 161 p1-p3, 164 p2-p8 and 165 -- 37 of
  its 77 nephew groups -- and *Iceboat* on 168 p3-p7. Both print big, solid,
  easy earflap caps outdoors, so the difficulty is entirely about which pages
  are interiors.
- **Decoys measured on these four**: the green armchair upholstery `#009e49`
  H147.7 (8563px) beside the boys on *Too Safe Safe* 145 p7; the green sofa
  `#009e49` (5559px) on *Iceboat* 168 p6; the red books on the shelf
  `#e61b1f` (8988px) on *Iceboat* 168 p3, right where a band would be; the bay
  water and the red machinery on *Cuspidoria* 149 p2.

Vol. 12, two more titles read 2026-09-09, and the volume's H102.5 cap green is
NOT universal either:

| title | reference panel | red (Huey) | green (Louie) | blue (Dewey) |
|---|---|---|---|---|
| *Tralla La* | 194 p4, two boys and Scrooge in close-up | `#e21c1f` H359.1 S0.88 | `#5ca93a` **H102.0** S0.66 | `#00a5d7` H194.0 S1.00 |
| *Outfoxed Fox* | 219 p7, three boys in a row | `#e11b20` H358.2 S0.87 | `#4da23e` **H111.2** S0.61 | `#00a5d7` H194.0 S1.00 |

*Tralla La* is the volume's textbook case -- its green is the grass to a
decimal place, so a green blob names a boy only when `heads.py` puts it on a
skull. *Outfoxed Fox* is eleven degrees off it and much easier, and the lawn in
that story does not compete.

- **SCROOGE'S COAT IS `#a04453` H350.2 ON BOTH TITLES**, and it is the largest
  red on nearly every page he is in; his top-hat band is `#00a5d7`, Dewey's
  exact ink, and it is 2500-4500px against a nephew band of 100-1000px. On
  *Tralla La* he also wears a GREEN ROBE for 204 and a blue one for 202-203,
  and the robe prints `#5caa3c` -- the cap green exactly. The 242px of it the
  census put beside a nephew's head on 204 p4 is his sleeve.
- **THE TRALLA LA BOYS GO BARE-HEADED FOR WHOLE PAGES.** No cap at all on
  204 p4, 204 p6, 208 p6, 209 p2 or 209 p4 -- plain white skull and a hair
  tuft -- and the caps are back, clean, on 205 p2, 205 p4, 207 p7 and 209 p7.
  Both facts are per panel. The flying suits on 197-199 hide them completely,
  and their colours are red / green / yellow, which is not the roster palette.
- **`UNCA SCROOGE` IS A NEPHEW AND `UNCLE SCROOGE` IS DONALD, ON BOTH TITLES
  AND ON EVERY OCCURRENCE.** Tralla La: 7 UNCA against 12 UNCLE. Outfoxed Fox:
  3 UNCA SCROOGE and 4 UNCA DONALD, all nephews', against 8 UNCLE SCROOGE, all
  Donald's or narration. It settled about twenty groups between them for free
  and it is worth grepping before page 1 of any Scrooge story.
- **`barks-ocr-name-grep` DOES NOT SEE NEPHEW NAMES.** It reports non-dictionary
  tokens plus repeated word pairs, so a name it knows is invisible: it returned
  nothing for *Tralla La*, and *Tralla La* 196 g5 is Scrooge saying QUICK,
  DEWEY! -- the only nephew named in the story. Grep `ai_text` directly for
  HUEY/DEWEY/LOUIE as well as running name-grep.


Vol. 15, two more titles read 2026-09-09, and on THESE two the saturation
split that failed on *Salmon Derby* works:

| title | reference panel | red (Huey) | green (Louie) | blue (Dewey) |
|---|---|---|---|---|
| *Travelling Truants* | 117 p4, three nightshirts in one frame | `#e51a20` | `#4da33d` | `#00a5d7` |
| *Rants About Ants* | banded black crowns, outdoors only | `#e51a20` | `#4da33d` | `#00a5d7` |

**The cap green prints S0.61-0.63 and the cap blue S0.96-1.00**, so an
intermediate hue resolves on saturation rather than staying unreadable:
`#08a182` **H167.8 S0.95** on *Travelling Truants* 120 p4 is inside the
H165-180 dead band the Salmon Derby entry above says to give up on, but its
saturation is the blue's and nothing like the green's. Those calls were made
and held at **medium**, with the measured hue and saturation written into the
note so a reviewer can overturn them in one look. Do not read this as
cancelling the Salmon Derby rule: there the two inks were NOT separated by
saturation, so measure the volume's own green before leaning on it.

- ***Travelling Truants* carries two colour keys, not one.** Black crowns with
  a coloured band outdoors, and nightshirts in the same three inks on the
  bedroom page 117 -- whose panel 4 prints all three in one frame and is the
  title's reference panel for that reason.
- ***Rants About Ants* takes the caps off indoors** -- bare-headed through 126
  and most of 128, banded crowns everywhere outdoors. Two panels print two
  green bands and no blue (127 p6; 126 p9's balloon also carries two tail
  points over three boys), so those groups stay collective.

Vol. 14, established on *The Seven Cities of Cibola* 2026-09-09 and confirmed
on *Million Dollar Pigeon*:

| | |
|---|---|
| red (Huey) | `#e61b1f` H358.8 |
| blue (Dewey) | `#00a4d7` H194.0 |
| green (Louie) | `#4ca33e` H111.7 S0.62 |

- **THE VOLUME-WIDE DECOY IS SCROOGE'S TOP HAT.** Its band prints `#00a5d5`
  -- the roster blue, the same ink as Donald's sailor cap and Dewey's band --
  so a blue blob at head height is his about as often as anybody's. It is in
  the head census on six of *Million Dollar Pigeon* 036's eight panels.
- **HIS COAT PRINTS `#e61b1f`, THE ROSTER CAP RED EXACTLY**, in blobs of
  5,000-8,300px against a nephew band of a few hundred. On a Scrooge story in
  this volume the largest red on the page is his coat, every time.
- A saturated green near a figure need not be a cap or a leaf: on *Million
  Dollar Pigeon* 037 p6 the 2,853px of `#009e49` **H147.7 S1.00** at the lower
  left is the upholstery of his desk chair.
- **THE Vol. 12 `UNCA SCROOGE` / `UNCLE SCROOGE` SPLIT HOLDS HERE TOO, 11 FOR
  11.** After review, all seven UNCA groups in Cibola are nephews (009 g1,
  012 g1, 013 g8, 014 g5, 015 g14, 025 g2, 029 g2) and none of the four UNCLE
  ones is (006 g0 `none`, 006 g1 and 027 g18 narrator, 032 g1 Donald). The
  entry that stood here until 2026-09-09 claimed the split failed, on the
  strength of Cibola 012 g1 -- and 012 g1 was the pass's own error, corrected
  by the review from Donald to Dewey. Grep the addresses before page 1 and let
  them outrank a cap.
- *Million Dollar Pigeon* has no nephews in it at all, so `cap_colour` is null
  on all 42 of its groups. Check the cast before deriving a palette from a
  title.

Vol. 14, three more titles read 2026-09-10 (forty-fifth batch), and the volume
entry above holds for two of them and fails outright for the third:

| title | reference panel | red (Huey) | green (Louie) | blue (Dewey) |
|---|---|---|---|---|
| *The Mysterious Stone Ray* | 042 p3, three boys in a row on the beach | `#e61b1f` H358.8 S0.88 | `#4ba43d` **H111.8** S0.63 | `#0ea5b7` H186.4 |
| *The Tuckered Tiger* | 098 p5, three boys facing Scrooge | `#cf262d` / `#e61b1f` | `#4a9f3b` **H112** | `#03a5d6` |
| *A Campaign of Note* | 070 p1, only one boy reads | -- | `#4ea341` **H112** | -- |

- ***The Mysterious Stone Ray* DOES NOT TRACK THE CONVENTION AND SAYS SO ITSELF.**
  Its reference panel is clean, and its dialogue then contradicts it twice:
  053 g3 leaves Huey on the beach, 055 g3 names Donald, Dewey and Louie as the
  three petrified, and the surviving boy is painted H112 GREEN on 055/056 and
  1786px of roster BLUE on 057 p5. Take the address, record the printed ink,
  hold at medium. This is the volume's exception, not its rule.
- **THE CAP CONSTRUCTION DIFFERS BETWEEN THE TWO Vol. 14 TITLES.** Stone Ray
  draws a narrow band that reads 35-700px and is often below capscan's 25px
  floor at the crown edge; Tuckered Tiger draws a black cap with a small
  coloured WEDGE at the side reading 130-720px. Neither is a broad crown band.
- **SCROOGE'S COAT IS NOT THE ROSTER RED ON EVERY TITLE IN THIS VOLUME.** It is
  `#a04453` **H350.2 S0.57** maroon on *The Tuckered Tiger* and *A Campaign of
  Note* -- which makes a clean `#e61b1f` blob on those two a nephew's wedge --
  and the roster red at 5,000-21,000px on *The Mysterious Stone Ray*. Measure
  it once per title.
- **ON STONE RAY THE SEA IS THE ROSTER BLUE**, `#00a5d5` H193.5 S1.00 in blobs
  of 13,000px and up, sharing its hex with Dewey's band, Donald's sailor cap
  and Scrooge's hat band. Four things, one ink; only area and position separate
  them. Its foliage and upholstery are the volume's usual `#009e49` H147.7.

Vol. 15, one more title read 2026-09-10, and its bands are the smallest yet:

| title | reference panel | red (Huey) | green (Louie) | blue (Dewey) |
|---|---|---|---|---|
| *The Daffy Taffy Pull* | no single panel; the three are named on 181, 182 and 184 | `#e41b1f` 243px | `#4ea340` **H112** 480px | clean blue on 184 |

- **ITS WHOLE-TITLE `bands.txt` READS `leafgrn: 0` ON ALL 77 PANELS AND THAT IS
  A THRESHOLD, NOT AN ABSENCE.** `title_heads` finds 136px, 163px and 181px of
  `#4ea340` H112 on Louie's crown on 182 p5, in the same panel where Donald
  names him. The band column's floor is above a wedge of a few hundred pixels.
- **THE BOYS ARE GENUINELY BARE-HEADED INDOORS** on 176-179, every one of them
  an interior, and wear the bands outdoors from 181. That is a measured absence
  and the reason every nephew group on those four pages is collective.
- The 2035px and 3017px of `#019d47` H147 beside Louie on 182 p5 are the green
  candy box he carries, not a band -- the band is the 136-181px H112 above it.


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

### Findings to paste into the next run (2026-09-16, sixty-first batch, NONE REVIEWED YET -- *Fearsome Flowers*, *Donald's Pet Service*, *Back to Long Ago!*)

**565 groups over 41 pages, 69 images, 1.68 per page.** No review has run
yet, so there are no correction rates here -- these are findings about the
*reading*, and the next review will price them. 4 type corrections, 0 text
corrections, 1 missed-text item in the batch.

- **THE KNOWN `name-grep` HOLE COST THIS BATCH NINE NAMING LINES, AND I RAN THE
  GREP ANYWAY RATHER THAN THE SCAN.** That HUEY, DEWEY and LOUIE are all
  dictionary words, and so invisible to both of `name-grep`'s passes, has been a
  standing rule since 2026-08-10 -- and the standing instruction is to run the
  direct scan at PREP. I ran `name-grep` on all three titles first, got a clean
  sheet, and only ran the scan later on a hunch. **It reported nine naming lines
  `name-grep` had reported as zero**, one of which fixes a permuted palette. The
  scan is free and takes seconds; run it at prep, not on a hunch:
  `re.search(r"\b(HUEY|DEWEY|LOUIE)\b", ai_text)` over the title's
  `*-easyocr-gemini-prelim-groups.json` -- the groups live under a `"groups"` key,
  not at the top level, which is the one thing that trips the one-liner up.
- **AND THAT FACT WAS A COLOURIST ERROR RUNNING THE WHOLE TITLE.** (Written up
  here first as a `permuted palette`; the reviewer has since RULED that Huey is red,
  Dewey blue and Louie green across the corpus always, and that a title disagreeing
  is the colourist getting it wrong. See the ruling at the end of this section.)
  *Donald's Pet Service* prints **Louie RED and Huey GREEN**, Dewey blue as usual,
  and the names are not a guess: the
  story hands one boy per job and names him each time -- 099 g7 gives the key to
  the red-capped boy and calls him Louie, 101 g1 names the blue one Dewey, 102 g0
  names the green one Huey, 103 g8 calls the red one Louie again to his face --
  and each naming line is followed by two to eight panels of that boy ALONE with
  one unmistakable cap. Reading that title on the roster default would have put a
  wrong name on roughly forty groups. **A title that names a boy and then isolates
  him is the cheapest check on the ink there is; look for it at prep.**
- **`capscan`'s DEFAULT min_area=25 MISSES THIS CONSTRUCTION ENTIRELY.** On
  *Fearsome Flowers* 093 p1 the three caps are slivers of **54, 34 and 33 pixels**,
  desaturated to `#ce4b25` S0.82, `#599147` S0.51 and `#1aadc8` -- and the default
  bands found exactly one of the three. `capwide` at **min_area=6** found all
  three, one per head and nowhere else. Run the head census with a LOW MIN_CAP
  (`title_heads.py <out-dir> 400 8`) at prep on any Vol. 18 title; at the default
  the thin-rim caps are invisible before the reading starts.
- **A NEW SCRIPT DOES THE "A BLOB MUST SIT ON A HEAD" TEST FOR YOU**:
  `scripts/vision/crowns.py <census-file> [PAGE ...]` keeps only the ink whose
  centre falls inside a head's skull span and whose bottom edge is on the crown,
  and prints `NO INK ON CROWN` otherwise. It is what caught, for free and without
  an image, that the a=16350 red beside a boy on *Fearsome Flowers* 094 p6 is the
  HOUSE ROOF, that the a=1213 red on 097 p4 is a WINDOW FRAME, that the a=3391 red
  on 097 p3 is an AXE BLADE, and that the a=11150 green on *Back to Long Ago!* 099
  p2 is a floor VASE. It is a screen, not a verdict -- when a name hangs on it,
  still crop.
- **THE REAL CAP QUESTION IN THESE TITLES IS NOT WHICH COLOUR, IT IS WHETHER A CAP
  IS THERE AT ALL** -- and at 250px the montage answers it. These caps are a solid
  BLACK crown carrying a thin rim, so a bare head reads as a plain white skull with
  a hair tuft and a capped one as a black mass, and the two are never confusable at
  contact-sheet scale. *Fearsome Flowers* is bare-headed indoors and capped outdoors;
  *Donald's Pet Service* the same, plus 107 p1 knocks both caps into the air;
  *Back to Long Ago!* has the boys CARRYING their caps in their hands through
  108-110 while they pack. **[STRUCK OUT AFTER REVIEW -- this said "a cap in a hand,
  a cap in mid-air and a cap on a head are three different facts and only the third
  names anybody", and it is FLATLY WRONG. A cap names its owner wherever it is in
  the panel. It cost *Back to Long Ago!* most of its 22 under-namings. See the
  third-of-three section below, and note that the rule was already in THIS FILE at
  the *Magic Hourglass* and *Rich Finds* entries before I wrote the contradiction.]**
- **A BALLOON SPOKEN BY MORE THAN ONE BOY IS DRAWN WITH ONE TAIL PER BOY, and
  both titles do it.** *Fearsome Flowers* 088 g2 has three tails fanning to three
  boys, 093 g15 has two, 097 g2/g3/g6 have two each; *Back to Long Ago!* 099 g6 has
  three. Count the points on a balloon's lower edge before assigning it: a single
  tail is a name, two or three is a chorus and the answer is `nephews`. Going the
  other way, TWO TAILS THAT BOTH LAND ON THE SAME BOY are the balloon's own
  plumbing and still one speaker (097 g13, 106 g4, 107 g9 in *Pet Service*).
- **THE CAPTION BOX AND THE TAILLESS BALLOON ARE DIFFERENT DEVICES AND THIS TITLE
  USES BOTH.** *Back to Long Ago!* draws narration as a **pink squared box** and
  a character's off-figure speech as a **cream rounded balloon with a tail** -- and
  the two were stored the wrong way round in two places: 100 g7 (`So-`, the pink
  box) was `dialogue`, and 101 g11 (a cream balloon whose tail runs to the window,
  first person, `WHEN I HYPNOTIZED HIM`) was `narration`. One 1.1x crop of each
  settled both. **Before overruling a caption's type, crop it and look at the
  outline** -- and note that the neighbouring group often tells you the answer for
  free: 101 g13 is the same device as g11 and was already stored correctly.
- **A PAST LIFE IS STILL THE SAME CHARACTER.** *Back to Long Ago!* spends eight
  pages in 1564 with Scrooge drawn as Matey McDuck and Donald as Bo'sn Pintail.
  Every line in the flashback is settled by WHO IS ADDRESSED BY NAME -- `AYE,
  PINTAIL!` cannot be Pintail's -- and none of it needs the art at all. I recorded
  the speakers as `Scrooge` and `Donald`, because the story says outright that they
  are the same two (105 g11, 107 g6), with the past-life names in every note.
  **This is the one title-wide judgement call in the batch and it is cheap to
  reverse** if the reviewer would rather have `other:Matey McDuck`.
- **A COSTUME IN THE ROSTER INKS IS A CAP; A DISGUISE IS NOT.** *Fearsome Flowers*
  093 puts the boys in red, blue and green PYJAMAS at 3,000-14,000px each, one per
  boy, aligned to the three heads the census finds -- that is a cap key and it names
  five groups. *Back to Long Ago!* 117 puts them in a bowler, a blue cap and a red
  fireman's hat as a disguise -- those are costume colours, the convention does not
  apply, and everything from 117 on is a forced collective.
- **THE COLLECTIVE RATE IS HIGH IN THIS BATCH AND MOSTLY NOT A DECLINE.** Where the
  caps are off, in silhouette, in hand or in costume there is nothing to decline;
  the reviewer should expect *Back to Long Ago!* in particular to be a Scrooge story
  in which the nephews are a chorus by construction. Only 16 of 565 groups came out
  at medium.
- **A COUGH IS DIALOGUE** (*Fearsome Flowers* 092 g7, `COFF! COFF!` from
  sound_effect). Same test as a laugh or a sigh: a character's voice makes it.
- **`panel_boxes.py` TRUNCATES `ai_text` at about 50 characters**, which is not
  enough to read a page's script off disk before opening any image. Worth a `--full`
  flag; I wrote a throwaway dumper for it three times.
- **The page-capture files are `ensure_ascii=False`** -- already a known format
  rule, but `CLAUDE.md` gave only `indent=2` plus a trailing newline, so a round-trip
  check written from the repo's own note FAILS on any capture holding a non-ASCII
  glyph. *Fearsome Flowers* 090's `50¢` is such a glyph and my first check flagged a
  clean file as mis-formatted. `CLAUDE.md` now carries the escaping too. The groups
  files remain `indent=4`, ASCII-escaped, no trailing newline.

## Per-volume cap palette

Vol. 18 and Vol. 20, four titles read 2026-09-17 (sixty-fifth batch; none reviewed).
30 pages, 51 images, **1.70 per page**; per title 1.33 / 2.20 / 1.50 / 1.50.

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Gyro's Imagination Invention* (18) | 141 p3 (three caps knocked into the air) and 141 p4 (red, blue, green rims in a row) | `#e51a20`-`#e71c20` (138 p4, 141 p4); shaded `#bd251d` (141 p6), `#db1b20`/`#90191a` (141 p3), `#cd2431` (140 p7) | `#009e45`-`#009f45` H146 (140 p7, 141 p4, 141 p6); `#009c64` H160 (139 p3); `#0b8d69` H163 sliver (138 p3); `#266e3e` H140 (144 p4); **teal `#05a1a1` H180 on the boy 142 g2 names LOUIE**, and dull teal `#21847e` H176 / `#3f797a` H181 (141 p7, 143 p7) | `#00a4bd` H188 (140 p7), `#00a3af` H184 ranked blue beside a `#266e3e` green (144 p4), `#01a5d6`/`#0fa7d0` H193 (141 p4, 146 p5) | black cap with a thin rim or quarter; bare-headed indoors in Gyro's workshop (140 p2-p6); night panels print every cap the same dark `#0079b0` (147 p7-p8) |
| *Red Apple Sap* (18) | 148 p1 (three quartered caps) and 151 p8 (red, blue, green from behind) | `#e71c20` 60-1,869px; dim `#933e25` H14 (153 p7), `#a0361e` (157 p8), `#cb2623` (150 p6) | `#67ac40` H98 (148 p1), `#4da43d` H111 (152 p3), `#4ea43e` (157 p6), `#49944b` H122 (153 p7) -- only 2 named groups | `#00a5d5` 21-1,213px throughout | quartered black caps outdoors all through; one naming line, 157 g7 `WHERE'S HUEY?` |
| *Picnic*, *The Sure-Fire Gold Finder* (20) | none -- no nephews | -- | -- | -- | Gyro solo stories with his Helper (and a mouse, lizards, a horned toad, rattlesnakes). No cap key at all |

- **TEAL IN *IMAGINATION INVENTION* SPLITS BY BRIGHTNESS, NOT HUE.** The bright cyans
  `#00a4bd`/`#00a3af` (H184-188) sit beside a clean green and are Dewey's; the teal on
  the boy Donald names LOUIE (142 g2) is `#05a1a1` H180, and the dull teals
  `#21847e`/`#3f797a` are on boys drawn in Louie's pose. 143 g13 was named Louie on
  that dull teal at medium -- the least certain cap call in the batch.
- **THE OVERVIEW LIED ABOUT COLOUR ON 146.** The Betelgeuse page looks green-tinted
  in `page.png`, Donald's cap included; the pixels are the roster `#00a5d5`. Sample,
  do not read colour off the page image.
- The workshop machine in *Imagination Invention* is teal `#01a08c`/`#007a6b`, and it
  sits behind every boy's head on 139 p6-p8 -- the census lays it on their crowns.
  *Red Apple Sap*'s bushes print `#74a83c` H89 at head height beside the green caps.
- Donald's cap is the roster blue in both; Gladstone is blue-coated. The apple expert
  and Grandma Duck appear in *Red Apple Sap*.
- Type corrections: 28 proposed (Picnic 4, Imagination 2, Red Apple Sap 7, Gold
  Finder 15), and 20 of them are `dialogue -> thought` on bubble-trailed balloons,
  16 in the two Gyro stories. Snores (149 g1, 155 g11) and the
  gopher's HIC (155 g12) went to dialogue, following the 58-to-24 split in the
  reviewed corpus.
- Added lettering groups: *Gold Finder* 164 the lizard's `?`, 165 the LAMP BLACK pot
  label (LA under a paint drip).

Vol. 18, four titles read 2026-09-17 (sixty-fourth batch; none reviewed):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *In Kakimaw Country* | 109 p1 (blue, red, green boys in a row) and 113 p4 (green and red rims) | `#e61a1f`-`#e71c20` 273-1,414px (113 p4, 115 p4, 116 p1); dark `#c51e1c` H0.7 (109 p5), `#ce242c` (114 p8), `#d1262e` (115 p2), `#d92227` (112 p7) | `#4ea43e`-`#4fa43e` H110 (109 p1, 113 p4, 115 p4, 116 p5); `#52a33d` H107.6 (114 p5), `#5da543` H104 (110 p4), `#64a951` H107 (115 p2) | `#00a5d5` (109 p1, 114 p6, 115 p8); quartered `#00a4d5` (112 p7); `#01a4c6` H190 (117 p1); `#0ca5bf` (116 p5) | a thin rim on a black cap outdoors; bare-headed in swimsuits on 108 and 109 p6-p7; plain black caps with no rim on 116 p3 |
| *The Lost Peg Leg Mine* | 009 p4 (red, green, blue patches) and 008 p2 | `#e61a20`-`#e61b20` 165-1,591px; dark `#c2171e` (008 p1), `#c53542` (012 p1), `#cb1b1c` (014 p6), `#dd181f` (016 p7) | `#009d45`-`#009e46` H147 (009 p4, 016 p3); `#019267` (008 p2), `#139f4e` (013 p6), `#00a06a`/`#00a070` H160-162 (014 p4, 015 p5), `#299445` H136 (015 p2), `#3d9470` H155 (016 p4); **TEAL H172-182 IS LOUIE HERE**: `#00a186` (008 p5, beside a `#00a5d5` boy), `#147a70` (014 p6, beside red and a `#00a3c2` blue), then `#12908d` (013 p7), `#00a3a6` (011 p8), `#347b75` (013 p3), `#2d8378` (015 p7) | `#00a5d5`-`#01a4d6` H193 (008 p2, p4; 009 p4; 016 p7); `#00a3c2` H188 (014 p6) | a coloured patch or rim on a black cap, quartered on 009 p2 and 013 p7; plain black caps on 012 p3 and 017 p1; firelit and silhouetted on 012 |
| *Losing Face* | 118 p5 (three boys from behind, green, red, blue) and 125 p7 (quartered caps) | `#e61a20` 218-2,126px; dark `#b91d1e` (122 p5), `#dd181e` (122 p6) | `#009e46`-`#009e47` H147 (118 p5, 122 p3, 125 p7, 126 p8); `#009f61` H157 (122 p1), `#009e6e` (123 p2), `#009e71` H163 (126 p7), `#0b9c7f` H168 (125 p1, medium); `#16887c` H173 ranked green beside a `#0ea6c3` blue (123 p6) | `#00a4d5`-`#00a5d5` (125 p7, 127 p5); `#0ea6c3` H190 (123 p6); **teal `#02a199` H177 ranked blue beside a `#009f61` green (122 p1)** | a rim or quartered black cap; told in flashback to Daisy, with the quoted captions as Donald's narration; no roster ink on the boy on 124 p5-p6 and 125 p2 |
| *The Day Duckburg Got Dyed* | 130 p1 (big green and red quartered caps) and 133 p1 (green, teal, red) | `#e61b20`-`#e61c1f` (129 p4, 130 p1, 133 p1); dark `#b51e22` (130 p5) | `#009e46`-`#009e47` H147 (129 p7, 130 p1, p4); `#00a141` H144 (133 p1); a 59px `#009d46` sliver (129 p4, medium) | `#03a4d5` (129 p4); **teal `#02987e` H171 ranked blue beside `#00a141` green (133 p1)** | rim or quartered cap outdoors; bare-headed indoors on 128, 129 p1-p2 and 132; in Timbuktu (137 p5-p8) turbans in the roster red and blue |

- **TEAL IS A PER-TITLE INK, NOT A PER-VOLUME ONE.** In *Peg Leg* a teal rim sits
  beside a true `#00a5d5` blue twice, so it is Louie's; in *Losing Face* and *Dyed* it
  sits beside a true green, so it is Dewey's. Earlier Vol. 18 titles ranked teal as
  blue. Rank it inside the panel, and carry it across a title only where a panel
  shows it beside the other colour -- and never into the next title.
- Donald's cap is the roster blue throughout. *Peg Leg*'s Scrooge wears a darker
  hat band `#0078af`-`#0183b8` (H197-199) and a `#b44a5e` coat; *Kakimaw*'s coat is
  `#a14554`. *Kakimaw*'s feathered medicine man is Donald in disguise and is named
  Donald.
- Added lettering groups: *Kakimaw* 109 AJAX RAIN POWDER, 111 and 112 the farmer's
  sweater `W` (x4) and the 111 plate `313`; *Peg Leg* 010 plate `313`; *Dyed* 129
  Gyro's door sign, cut by the panel border.

Vol. 16, two titles read 2026-09-17 (sixty-third batch; none reviewed):

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *Land of the Pygmy Indians* | 179 p1 and 184 p5, three boys side by side with red, blue and green rims | `#df1d21`-`#e61b1f` 128-1,057px; dimmed `#842b1c` H8.7 (164 p8), `#b6281c` H4.7 (177 p8), `#c33225` (168 p2), `#cd282a` (181 p5) | `#4da33e`-`#50a440` H110-117, 170-1,195px -- the `leafgrn` band; shaded `#579b65` H132 (164 p8), `#62a35f` H117 S0.42 (183 p4), dark `#37886d` (183 p3), `#3aa276` (172 p1) | `#00a5d7`-`#08a6d4` 130-1,650px; teal `#42a3aa` H184 (180 p7), `#21a4a0` H178 ranked blue against a clean green beside it (185 p2) | a thin coloured rim on a black cap; several boys print no rim at all (164 p7 right boy, 167 p5, 179 p3, 183 p2) or a level teal the channel test calls unreadable (168 p2, 183 p4) |
| *The Fantastic River Race* | none -- no nephews | -- | -- | -- | a flashback told to Grandma Duck: Scrooge, Ratchet Gearloose, Blackheart Beagle, the Beagle Boys, a banker. No cap key at all |

- *Pygmy Indians*: the `green` band is the forest `#016c62`/`#2f9d44` on every
  outdoor panel, and it reaches the boys' crowns in the census (165 p1's green
  segment probes as `#016c62`, the pines behind it). Scrooge's coat `#a04453` fills
  the red column wherever he stands. The small Indian painted blue on 183 p7 is
  `#07a4d4`, the roster blue, at head height beside two black-capped boys.
- Donald wears his blue sailor cap throughout; Scrooge his blue-banded top hat.

Vol. 18 and Vol. 16, three titles read 2026-09-16 (sixty-first batch; none reviewed):

| title | reference | red | green | blue | construction |
|---|---|---|---|---|---|
| *Fearsome Flowers* (18) | 088 p1, the splash -- the only INTERIOR panel in the title with the caps on | `#e71c20` a=188 (088 p1); `#e5-e61a1f` a=360-1,436 (091); `#e71c20` a=808-1,333 (092, 097); faint `#ce4b25` H13.5 a=54 (093 p1) | `#009e45` a=10-25 (088 p1) **and** `#4fa43e` H110 a=766-1,342 (090 p7, 092 p7) -- the volume prints BOTH greens; shaded `#599147` H105 a=34 (093 p1); `#48a541` a=20-32 (094 p4) | `#00a5d5` a=120-174 (088 p1); `#01a4d5` a=525-1,226 (091); teal `#00a291` H173.7 and `#0da5b9` H186 ranked blue (097 p1, p2) | thin rim on a black cap. **Bare-headed indoors** (088 p2-p5, 089, 097 p6-p8), capped outdoors, and on 093 p4-p8 the key moves to RED/BLUE/GREEN PYJAMAS at 3,000-14,000px |
| *Donald's Pet Service* (18) | 099 p3 and p5, the three boys in a row outdoors | **LOUIE** -- `#e61a20` a=194-1,024, and the same ink on 100 for eight straight panels | **HUEY** -- `#4ea43e` H110 a=499-660 (102 p2-p4) | **DEWEY** -- `#00a5d5` a=37-302, all of 101 | **COLOURIST ERROR, WHOLE TITLE: red and green are swapped, so the red cap is Louie's and the green one Huey's.** Four naming lines fix the names; the inks are recorded as printed. Bare-headed indoors (098, 099 p1-p2, 107 p4-p7); both caps knocked off on 107 p1 |
| *Back to Long Ago!* (16) | 115 p2 (blue/green/red row) and 107 p7 (red/green/blue row) | `#de1e21`-`#e01c20` a=168-238 (107 p7, p8); the thin band on the boy Donald names Huey (116 p1) | `#46-51a44x` H110-118 -- but **on 114 p3 the green over two crowns is PALM FRONDS**, not a band | `#00-0ea4d5` a=96-483 (107 p1, p7); teal `#2aa098` H175 ranked blue (107 p8) | the ordinary roster, one anchor only (116 g2). **Donald wears a BLUE sailor cap all through the modern-day pages** -- the same ink as Dewey's band. Caps off indoors 108-110 and carried in hand while packing; costume headgear from 117 on |

- *Fearsome Flowers*: the `leafgrn` column is worthless on this title -- it is a
  garden story and the band fills with foliage (1,026-1,243 blobs a panel), while
  089's SOFA prints `#3bac42` at H123.7, inside it. The cap green is in BOTH bands
  depending on the panel. Donald wears his own blue cap from 090 p1.
- *Donald's Pet Service*: Donald's cap is blue too; the red window frames on 097 p4
  and p5 (a=1,213 and a=1,024-1,672, wide flat bands at head height) are the trap on
  that page, and the red roof on 094 p6 is a=16,350.
- *Back to Long Ago!*: Scrooge's coat is `#a04453` and accounts for most of what the
  census hangs on his head; the shop awning on 094 p3 of *Fearsome Flowers* and the
  ticket-office lettering here are both the roster blue.

### Findings to paste into the next run (2026-09-16, sixty-first batch, ONE OF THREE REVIEWED -- *Fearsome Flowers*)

**143 groups, 7 speaker corrections in the 141 the pass wrote (5.0%), 7 of 65 in
the nephew domain (10.8%)**; by the confidence the pass wrote, **high 6/130
(4.6%), medium 2/11 (18.2%)**. The one type proposal held, no text correction was
proposed. The review added 2 groups. Mirrored clean: 143/143 reviewed on both
engines, 128 `identified_by`, distributions identical. 29 images, 2.9 per page.
(Two further `unknown -> none` moves in the tool's output are the reviewer setting
the speaker on the two ADDED groups, not corrections to the pass; the counts above
exclude them.)

- **FOUR OF THE SEVEN CORRECTIONS ARE CALLS WHERE MY OWN NOTE CONTAINED THE
  REVIEWER'S ANSWER.** This is the single finding of the review.
  - 091 g0 I wrote `MEDIUM, and the reason is worth checking: the GREEN-capped boy
    at the left is the one drawn with his beak open and a hand raised... If the
    review reads the beaks rather than the tip this is Louie.` The review read the
    beaks. It is Louie.
  - 097 g1/g2 I wrote `Reviewer: the two present are Huey and Dewey` and declined
    to split the joined pair. The review split it as **Huey then Dewey**, in that
    order -- the exact mapping in my note.
  - So the rule is not "look harder", it is **CASH THE NOTE**. When the note names
    the alternative reading and the alternative is a NAME, take the name: the cost
    of being wrong is one keystroke and the cost of declining is a guaranteed
    correction. `feedback_use_the_evidence_you_already_wrote` is now four batches
    old and this is its worst instance, because the note was not merely evidence --
    it was the answer, written out, with the reviewer addressed by name.
- **THE MULTI-TAIL RULE I DERIVED THIS BATCH IS WRONG IN THE DECLINING DIRECTION,
  AND ALL THREE INSTANCES REVERSED.** I found that a balloon spoken by more than
  one boy carries one tail per boy, and turned that into "two tails means a chorus,
  so `nephews`". The review named **every** one of them: 097 g1, 097 g2 and 097 g6.
  The corrected rule:
  - **A CLUSTER OF JOINED BALLOONS IS NOT A CHORUS.** When N stacked balloons carry
    N tails between them, the tails belong to the cluster and map to the balloons
    IN ORDER -- upper balloon to left tail, lower to right. That is what the review
    did on 097 g1/g2.
  - **ONE GROUP WITH TWO TAILS TAKES THE FIRST (LEFTMOST) TAIL.** 097 g6's two tips
    were at panel (586,208) and (843,181); the review took the left one and called
    it Dewey.
  - A chorus is still what you record when the tails cannot be told apart -- three
    tails fanning to three distinct boys on ONE group, as on 088 g2 -- but two
    balloons with two tails is two speakers, not one collective.
- **THE TWO `nephews -> Huey` MOVES ARE NOT ABSENT-CAP ERRORS, AND ONE OF THEM HAS
  NO RED INK BEHIND IT.** Both were re-scanned after the review:
  - **092 g1**: the ink is exactly where the pass put it -- `capwide` at min_area=3
    over the head band returns red `#e71c20` a=301 and a=263 at panel (845,297) and
    (788,270), BOTH on the BACK boy (head x777-876), and nothing at all on the front
    boy (x662-757). The disagreement is **which boy the tail reaches**: the pass put
    the tip at (683,267), inside the front boy's skull. This is a tail call, not a
    cap call, and the lesson is that a tip inside the near boy's skull loses to the
    far boy when only the far boy can be named.
  - **095 g5**: `capwide` over the WHOLE panel at min_area=3 returns **red: 2 blobs
    of 4px and 3px at `#562216` H11.2** -- dark brown, not cap ink. The two visible
    crowns carry a green sliver and blue, and the third boy is behind a tree trunk.
    **The recorded `cap_colour: red` has no printed ink behind it in that panel.**
    Flagging rather than absorbing: if the name came from the scene rather than the
    art, the colour field should be null, because that field is the only check on
    the convention.
- **THE MISSED-TEXT AUDIT SUPPRESSED A REAL ITEM AS A NEAR DUPLICATE.** The review
  added TWO groups, not the one the audit reported. 090's `50¢` was flagged; 092
  p3's `BLACK EYED SUSANS` plant tag was **not**, because the same words appear in
  the neighbouring balloon (`THE TAG SAYS THEY'RE BLACK-EYED SUSANS!`) and the audit
  files that as "nearly a grouped text" and drops it. **A sign that a character
  reads aloud is invisible to the audit by construction.** Put it in the hand-back
  from the `visible_text` list directly whenever the page has a sign somebody quotes
  -- I had transcribed this tag and described it in g5's note, and still let the
  audit's silence stand in for a decision.
- **MEDIUM IS THE WORSE BET FOR THE SIXTH BATCH RUNNING**: 18.2% against high's
  4.6%, a factor of four. Both medium reversals (091 g0, 093 g11) were gap tips.
  Note the asymmetry: the gap tip that went to a NAME held nothing back and was
  reversed to another name, while the gap tip that over-named (093 g11 Huey ->
  nephews) is the only over-naming in the title. Gap tips are where medium lives and
  they are worth about one in five.
- **11 OF THE 18 BOYS THE PASS NAMED HELD, AND THE 3 PURELY-CAP CALLS ALL HELD.**
  Naming off a band that sits on a crown was not reversed once; every reversal
  involved a tail.

### Findings to paste into the next run (2026-09-16, sixty-first batch, TWO OF THREE REVIEWED -- *Donald's Pet Service*)

**134 groups, 1 speaker correction in the 132 the pass wrote (0.8%), 1 of 58 in
the nephew domain (1.7%)**; by the confidence the pass wrote, **high 1/132
(0.8%)** -- nothing was written at medium. The type proposal held, no text
correction was proposed, and the review added 2 groups. Mirrored clean: 134/134
reviewed on both engines, 111 `identified_by`, distributions identical. 14 images,
1.4 per page. (Two further `unknown -> none` moves are the reviewer setting the
speaker on the added groups, not corrections to the pass.)

- **THE READING HELD IN FULL, AND THIS IS THE FINDING OF THE BATCH.**
  All 39 named nephew calls survived with **no `cap_colour` changed anywhere**:
  Louie/red 16, Dewey/blue 17, Huey/green 6 (now 7). Reading this title on the
  roster default would have put a wrong name on 22 of those 39. **A title that names
  a boy in dialogue and then isolates him for a page is an anchor stronger than any
  scan, and it is free** -- the whole key came from four lines the direct
  three-name grep found at prep.
- **AND IT IS THE CHEAPEST TITLE IN THE LEDGER THAT ACTUALLY NAMES NEPHEWS.**
  `docs/vision-pass-cost.md` records two earlier near-zeroes -- *Wired* and *The
  Sunken Yacht* -- and both got there because the art made every nephew call a
  FORCED collective, so there was nothing to get wrong. This one named 39 of 58 and
  still came in at 1.7%. The lesson is not that the pass read better; it is that
  **an anchored palette converts the nephew domain from guesswork into bookkeeping.**
  Spend the prep minute looking for the anchor before spending any images.
- **THE ONE CORRECTION IS, AGAIN, A MAPPING I WROTE DOWN AND DECLINED.** 107 g2,
  `nephews -> Huey`. The panel knocks both caps into the air, and I wrote
  `Reviewer: if this pair is split it is Dewey (left) then Huey (right)`. The review
  split it and named the right-hand balloon **Huey**. That is now **five** such
  calls across two reviews in this batch, and in every one the note contained the
  answer. **CASH THE NOTE.**
- **`cap_colour` RECORDED WITHOUT PRINTED INK, SECOND REVIEW RUNNING -- WORTH A
  WORD WITH THE REVIEWER.** 107 g2 came back `Huey` with `cap_colour: red`, but
  `capwide` over the whole of 107 panel 1 at min_area=3 finds the only two caps in
  it are the **blue** and **green** ones in mid-air (green `#51a443` H111.3 a=291 at
  x492-518); every red blob in the panel is the `CRANK!` sound-effect lettering
  (`#e71c20` a=878 at x512-564, inside the SFX box) plus two specks. So `red` is the
  CHARACTER'S canonical colour standing in for the ink -- Huey's cap prints **green**
  here, seven times over, every one confirmed. The NAME was right and never in
  doubt; it is the colour field that was filled from it. Paired with
  *Fearsome Flowers* 095 g5, where `red` was recorded in a panel whose whole-panel
  red is 4px and 3px of `#562216`, that is two in two reviews. **`cap_colour` is the
  only check the corpus has on the convention, so filling it from the name quietly
  destroys the thing it exists to test.** RESOLVED: set to `green`, re-mirrored and
  committed (`2a73cc8f`), with the colourist error written into the group's note.
- **THE MISSED-TEXT AUDIT HAS A SECOND BLIND SPOT: REPEATED IDENTICAL LETTERING.**
  It reported **zero** for this title, and the review added two groups -- the second
  and third `A-1 PEA-NUTS` sacks in 103 panel 3, a panel that holds three of them
  and had one grouped. The audit matches `visible_text` against grouped text by
  CONTENT, so one grouped instance covers all N. Together with *Fearsome Flowers*
  092 (a sign a character reads aloud, suppressed as a near duplicate) the rule is:
  **the audit answers "does this string appear in a group", not "is every instance
  of this lettering boxed".** When a panel shows the same sign more than once, or a
  character quotes a sign, count the instances yourself and put them in the hand-back
  from `visible_text` -- the audit's silence is not a finding.
- **NOTHING ELSE MOVED.** No cap reversed, no tail reversed, no type reversed, and
  the 18 collectives all stood -- they were forced by silhouettes, bare heads and
  airborne caps rather than declined.

### RULING, 2026-09-16 -- colourist errors, and what `cap_colour` is for

The reviewer settled this while closing the sixty-first batch, and it overrides the
"permuted palette" language used in this file from *High-wire Daredevils* onward.
It is now also in `vision_schema.py`, so it reaches every future pass through the
generated `roster.txt`.

**Huey is red, Dewey is blue and Louie is green. Always, everywhere in the corpus.**
That is a fact about the characters, not a per-title convention, and it is not
negotiable by a title. There is no such thing as a story with its own key.

**What varies is the colourist, who sometimes gets it wrong -- occasionally for a
whole title.** When he does:

- the **DIALOGUE** names the boy. It always wins.
- **`cap_colour` still records the ink he was actually given.** Do not correct the
  colour to match the name, and do not rename the boy to match the colour.
- the error IS that disagreement, plus a word in the note.

**Why, in one line:** nothing downstream joins `cap_colour` to identity -- it is
read only by a display swatch in `vision_report.py` and by the editor -- so
recording the ink costs nothing, while deriving it from the name costs the only
evidence the error ever happened. Across the corpus the split is about **6,600
groups where cap and name agree against 120 where they do not**, and those 120 are
the entire record of the colourist's mistakes. Write the colours in from the names
and all 120 read as clean, permanently.

**The query that finds them**, and the reason the field is worth keeping honest:

```python
STD = {"Huey": "red", "Dewey": "blue", "Louie": "green"}
if g.get("speaker") in STD and g.get("cap_colour") and STD[g["speaker"]] != g["cap_colour"]:
    ...  # a colourist error, or a misread -- either way, worth a look
```

**Worked example, and the one this ruling came out of.** *Donald's Pet Service*
(Vol. 18) has red and green swapped for the entire story: Donald hands the key to
the RED-capped boy and calls him Louie (099 g7), names the BLUE one Dewey (101 g1)
and the GREEN one Huey (102 g0), then leaves each alone for two to eight panels.
Recorded as printed it comes out **Louie/red 16, Dewey/blue 17, Huey/green 7**, and
the swap is uniform, so it is findable. One group, 107 g2, had been set to Huey/red
during review -- the canonical colour standing in for the ink, in a panel whose only
two caps are the blue and green ones knocked into the air. It is now `green`.

**What this does NOT change:** how you NAME a boy. The convention is still the
anchor, a clean cap still names its wearer, and you should still expect red to be
Huey. It changes only what you write in the colour field when the art disagrees --
and it means a title-wide disagreement is a finding to report, not a local key to
adopt.

### Findings to paste into the next run (2026-09-16, sixty-first batch, THREE OF THREE -- *Back to Long Ago!*, batch closed)

**295 groups, 47 speaker corrections in the 292 the pass wrote (16.1%), 36 of 69
in the nephew domain (52.2%)**; by the confidence the pass wrote, **high 42/287
(14.6%), medium 4/5 (80.0%)**. Both type proposals held. The review added 3
groups. Mirrored clean: 295/295 reviewed on both engines, 273 `identified_by`,
distributions identical. 26 images, 1.24 per page. **This is much the worst title
in the batch and one of the worst in the ledger, and the cost was not images --
it was 1.24 per page, the cheapest of the three.**

- **I CONTRADICTED A RULE THAT WAS ALREADY IN THIS FILE, AND IT COST 22 CALLS.**
  Twenty-two of the corrections are collectives the review named **from the boys'
  own caps, held in their hands while they packed**. I had written the opposite
  into this very document: *"a cap in a hand, a cap in mid-air and a cap on a head
  are three different facts and only the third names anybody."* The correct rule
  was already here, twice, from earlier batches -- ***Magic Hourglass***: "A cap in
  a hand names its holder", and the *Rich Finds* entry extending it to "a cap lying
  at a boy's side indoors". I appended my contradiction to the same file.
  **108 panel 1 proves it three for three**: capwide puts green at x170-306, red at
  x440-504 and blue at x646-720, and the three balloons above them were named
  **Louie, Huey, Dewey in exactly that order**. The rule, stated once and for all:
  **A CAP NAMES ITS OWNER WHEREVER IT IS IN THE PANEL -- worn, held, on the sofa
  beside him, or knocked into the air above him -- provided you can tell whose it
  is.** *Donald's Pet Service* 107 g2 is the airborne case and the review named that
  one too.
- **SO "BARE-HEADED" IS THE WRONG QUESTION.** I ran the montage check for "is
  there a black mass on the head", answered no across 108-110, and stopped. The
  question is **"where is this boy's cap"**, and on a packing page the answer is
  "in his hand, 200px lower down". Scan the whole panel for the three inks and ask
  whose each one is, rather than scanning crowns.
- **TEN DONALD-AGAINST-NEPHEW CONFUSIONS, THE OLDEST ERROR CLASS IN THE FILE.**
  Six `nephews -> Donald` and four the other way. They cluster on the pages where
  the family is drawn small (113, 116, 117) and where Donald is IN the row of boys
  rather than apart from them -- 117 g1 I gave to "Donald in the middle of the three
  boys, the tall figure of the group" and it is Huey. When Donald stands among them
  at small scale, height is not a discriminator; find the bow tie or the sailor
  collar, or say `nephews`.
- **NINE `other:` ROLE ERRORS, AND TWO ARE PURE CARELESSNESS.**
  - **115 g12/g13 are swapped.** `STILL A DEAL, SENOR?` I gave to Scrooge because
    it addresses a "Senor" -- but the boat owner calls SCROOGE Senor (`SURE THING,
    SENOR!`, g9, two panels earlier). The address names the ADDRESSEE, so the
    question is the owner's and `YOU ASK THE DUMBEST QUESTIONS!` is Scrooge's. I
    had the evidence in the same panel sequence and read it backwards.
  - **116 g1 `VIVA EL SUNSHINE!` is a villager, not a nephew.** A line in Spanish,
    in a Caribbean port, from a crowd -- and I gave it to a boy.
  - The rest are collectives: `other:Donald and the nephews` -> `Donald` or
    `nephews` (117, 118), and three `Donald` -> `other:Donald and Scrooge` at the
    end (119 g14, 120 g14/g15) where the two of them speak together.
- **MEDIUM WAS 4 OF 5 WRONG.** Eighty per cent. Across the batch medium ran
  18.2% / n-a / 80.0% against high's 4.6% / 0.8% / 14.6%. **Seventh batch running.**
- **THE REVIEW ADDED THREE DRAWN DEVICES I NEVER GROUPED** -- thought-bubble `!`
  marks on 102 and 117, and the **ring of dollar signs round Scrooge's head on 102
  panel 3**. I described that panel in my own capture as "Scrooge alone in close-up
  ringed by floating dollar signs" and put "dollar signs" in its `objects`, and
  still did not box them. **A drawn device is LETTERING: `!`, `?`, `$` go in
  `visible_text` and, when no group covers them, into `added_groups`.** The roster
  already says a device over one figure names that figure; I applied it to devices
  Gemini had already grouped and never once added one it had missed. That is the
  batch's THIRD missed-text blind spot, after the read-aloud sign and the repeated
  sign -- and the only one that is entirely mine, because the audit cannot see what
  `visible_text` never mentioned.
- **THE PASS MIS-TRANSCRIBED ITS OWN SOUND EFFECT AND MARKED THE GROUP CORRECT.**
  103 and 105 record the time-travel bell as `BONG` in `visible_text` while asserting
  `text_ok: true` on a group holding `BOING`. The art reads B-O-I-N-G, the group was
  right, the capture was wrong, and the two halves of my own output disagreed. The
  audit's near-miss WARN caught it -- **read that row, it is not always the group
  that is wrong.** Captures corrected.
- **WHAT DID HOLD:** both type corrections (100 g7 and 101 g11, the pink caption box
  against the tailed cream balloon); every Scrooge/Spellcaster call in the 1564
  flashback, all settled by who is addressed by name and never by the art; and the
  decision to record the flashback under `Scrooge` and `Donald` rather than
  `other:Matey McDuck` -- not one of those 90 Scrooge groups was touched.

### Batch close -- sixty-first batch, all three reviewed

| title | groups | speaker corrections | nephew domain | high | medium | images/pg |
|---|---|---|---|---|---|---|
| *Fearsome Flowers* | 143 | 7 / 141 (5.0%) | 10.8% | 4.6% | 18.2% | 2.9 |
| *Donald's Pet Service* | 134 | 1 / 132 (0.8%) | 1.7% | 0.8% | -- | 1.4 |
| *Back to Long Ago!* | 295 | 47 / 292 (16.1%) | 52.2% | 14.6% | 80.0% | 1.24 |
| **batch** | **572** | **55 / 565 (9.7%)** | **26.6%** | **11.0%** | **56.3%** | **1.68** |

**The spread is the whole story, and it is not about effort.** The cheapest title
per page was also the worst and the second-cheapest was the best. What separated
them:

- ***Pet Service* had an anchor**: four dialogue lines naming a boy and then
  isolating him. 0.8%.
- ***Back to Long Ago!* had a rule I contradicted**, one already written in this
  file. 16.1%, and 22 of the 47 come from that single mistake.

**Five of the batch's 55 corrections are calls whose answer I had already written
into my own note**, and 22 more come from overriding a standing rule. So roughly
half the batch's error is not perception at all -- it is failing to use what was
already known, either in the note or in the file. **The cheapest possible
improvement for the next run is not more images. It is reading the last review's
findings properly and cashing the notes.**

## Sixty-second batch read 2026-09-16 (none reviewed)

Vol. 20 and Vol. 16, four titles, 41 pages, 541 groups. 59 images, **1.44 per
page**; per title 2.75 / 1.75 / 1.83 / 1.11.

| title | vol | pages | groups | type corr. | missed text | images/pg |
|---|---|---|---|---|---|---|
| *Forecasting Follies* | 20 | 4 | 51 | 8 | 1 | 2.75 |
| *Fishing Mystery* | 20 | 4 | 50 | 4 | 0 | 1.75 |
| *The Colossalest Surprise Quiz Show* | 16 | 6 | 86 | 0 | 0 | 1.83 |
| *A Cold Bargain* | 16 | 27 | 355 | 0 | 0 | 1.11 |

### Per-volume cap palette

| title | reference | red (Huey) | green (Louie) | blue (Dewey) | construction |
|---|---|---|---|---|---|
| *A Cold Bargain* (16) | 136 p2, the three boys in a row, read at 2.4x | `#e61920` H358.0 S0.89, 419-617px side panel (136 p2) | `#4fa43e` H110.0 S0.62, 1545px over three blobs, INDOORS (136 p8); `#4fa43c`/`#50a33f` H109-110.5 6091px (139 p7) | `#06a4d4`/`#00a4d6` H194.0, 123-318px panel (136 p2) | a BLACK cap with a coloured SIDE PANEL; the third boy's panel prints pure black on 136 p2, so one of the three is unreadable by colour in any given panel |
| *The Colossalest Surprise Quiz Show* (16) | none -- no cap ink on any head in the title | -- | -- | -- | the boys are bare-headed on both couch panels (128 p1, p7) |

- ***A Cold Bargain* has two confounders that print the roster inks at head
  height, and both are now measured.** The ship's red **deck railing** is
  `#e61b1f` H358.8 S0.88 -- within a degree of Huey's `#e61920` cap panel -- and
  it runs across 139 p3/p5, 140 p7, 141-146. Red names nobody on deck. Outdoors
  the **grass** is `#4f933e` H108 S0.58 against Louie's `#4fa43e` H110, so green
  names nobody outdoors either. Donald's sailor cap is the SAME `#00a4d6` H194 as
  Dewey's panel, at 2371px, and Scrooge's hat band and the studio backdrop are
  the roster blue too.
- ***The Colossalest Surprise Quiz Show* is the cleanest worked example yet of
  "a blob is only a cap once a crop has put it on a head."** capwide on 128 p1
  returns **13 red and 4 green blobs**, including 3018px of `#e41c20` H358.8
  sitting directly above a head. A 1.5x crop shows both nephews bare-headed: the
  red above the head line is the **picture-frame trim on the wall**, the 13433px
  `#da4922` is the **cushion Donald lies on**, and the 2840px `#009d46` the census
  attached to a nephew's crown is the **green couch**. On 128 p7 the only
  roster-red is 755px of `#e51a20` which is **Donald's own bow tie**, plus a 3px
  wall sliver. Had any of those been taken at face value the title would carry
  four wrong names.

### Findings to paste into the next run (2026-09-16, sixty-second batch, NONE REVIEWED)

These are read-side findings, not review corrections -- the batch has not been
reviewed yet, so the usual correction-rate table cannot be written and the next
run should treat this section as provisional.

- **A COSTUME KEY CAN BE DIALOGUE-ANCHORED, AND THEN IT IS EVIDENCE.** The
  standing rule is that a costume key does not travel. *A Cold Bargain* 148 is
  the exception that shows what makes one hold: the marching file in the blizzard
  names itself, front to back, in four consecutive balloons -- `IS THAT YOU IN
  THE LEAD, UNCA DONALD?` / `YES! IS THAT YOU BEHIND ME, DEWEY?` / `YES! AND
  LOUIE'S BEHIND ME!` / `AND I AM BEHIND LOUIE, AND UNCA SCROOGE IS BEHIND ME!`
  -- and a 1.35x crop of p3 and p4 puts a ruff colour on each position: **Donald
  red, Dewey yellow, Louie blue, Huey orange**. That is a NON-ROSTER palette:
  red is not Huey, blue is not Dewey, green is nobody. **Record cap_colour null
  when the garment palette is demonstrably not the roster's**, put the garment in
  the note and `costume` in identified_by, and say so -- writing Louie's blue
  ruff into cap_colour would manufacture a colourist error that
  `cap_mismatch.py` would later report as real.
- **AN ADDRESS NAMES THE ADDRESSEE, AND IT CARRIED THIS WHOLE BATCH.** It settled
  the speaker on roughly forty groups with no image at all: every `UNCA SCROOGE`,
  `UNCLE SCROOGE`, `MR. McDUCK`, `DONALD`, `BOYS`, `NEPHEW`, `SKIPPER`, `PILOT`
  and `PENGY` line names somebody who is NOT speaking. It is the cheapest
  discriminator in the file and it should be run over the page text before any
  panel is opened.
- **READ allbold's BASE, NOT JUST ITS RATIO.** The ratio is against the group's
  OWN baseline, so it fails in BOTH directions on a balloon whose lettering is not
  uniform. *Quiz Show* 128 g7 has base **4.70** against the page's usual 3.1 --
  a balloon that is almost entirely bold, so `I DON'T KNOW!` scores a flat 1.00x
  while the blurted `GREE —` scores 0.80x, and comparing the two against the page
  norm is what proves the catchphrase is set bold. The same effect runs the other
  way on 126 g12, base **3.76** because `PILLOWS FOR SALE` is drawn large as a
  street cry: `SOFT` measures 1.07x on a clean line and a 2.4x crop shows it
  bold-slanted.
- **AND DO NOT READ EMPHASIS OFF A 250px MONTAGE.** *Quiz Show* 125 g12: I read
  `STUMPERS` as slanted on the contact sheet, allbold scored it 1.06x on a
  cleanly-split line, and a 2.3x crop shows it **upright**. The montage was wrong
  and the tool was right. One calibration crop per title settles the threshold --
  it came out at about 1.14 for this title -- and is worth its single image.
- **A WHOLLY SLANTED BALLOON IS A VOICE EFFECT, NOT EMPHASIS.** The quiz show
  announcer's balloons (124 g1/g3/g5, 128 g0/g15/g18) are set slanted throughout
  as the story's convention for a voice coming out of a television; inside them
  emphasis is extra WEIGHT. Tagging those words `[i]` would have been wrong.
  Check the whole balloon before choosing the tag, and prefer the volume's own
  habit -- Vol. 16 runs 956 `[b]` to 320 `[i]`.
- **LISTING A GROUPED CAPTION OR A GROUPED `?` IN visible_text MAKES A FALSE
  MISSED-TEXT HIT.** Five of the batch's six audit findings are mine:
  `audit_missed_text.classify` matches only against groups typed as lettering the
  ART carries, so a `narration` caption or a `?` typed `thought` can never match
  and comes back as `[quoted aloud, not boxed]`. Put signs, labels, sound effects
  and ungrouped drawn devices in visible_text; leave caption boxes and devices
  you have typed `thought` out of it.
- **THE DRAWING TEST IS WORTH ONE STACKED IMAGE PER TITLE.** Ten of the batch's
  twelve applied type corrections are `dialogue -> thought` on Gyro's solo
  balloons, and every one was settled by a scalloped cloud edge with a trail of
  separate bubbles, six of them in a single stacked crop at 1.15x. The words are
  no guide at all -- *Fishing Mystery* 154 g11 reads `NO FOOLIN'! I THINK I'VE
  CAUGHT A WHALE!`, which sounds spoken, and the drawing is a cloud.
  **A ninth was refused and that is correct behaviour**: *Forecasting Follies*
  150 g3, the lone `?` beside Gyro's head, already carries `type_reviewed` from a
  human on 2026-08-24, and `_apply_type` declines to overrule a review. The prep
  stub exposes only `ai_text`, `panel_num`, `text_box` and `type`, so a pass
  CANNOT see that a type has been reviewed and will keep proposing against it --
  expect the applied count to fall short of the written one and check `type_was`
  rather than assuming the apply dropped something.
- **WHERE THE TAIL WAS NOT TRACED, THE ANSWER IS `nephews`, AND THAT IS A COST
  DECISION TO DECLARE.** *A Cold Bargain* carries roughly 60 collective nephew
  calls. Two boys are named -- 141 g6 and 145 g6, both sole-figure-with-a-clean-cap
  -- and four more on 148 off the dialogue chain. The rest have cap ink recorded
  in the note but no traced tail, and per the roster a balloon's x-span is not a
  tail. The next review will show whether 1.11 images per page under-bought this
  title; that is the number to watch.

### CORRECTION to the sixty-second batch, 2026-09-17 -- the ACB nephew domain was under-read

The provisional findings above stand except for the last bullet, which called
*A Cold Bargain*'s ~60 collectives "a cost decision to declare". It was not a
defensible cost decision. It was a reading failure, and the review caught it at
page 140 with **every nephew name being filled in by hand**.

**The numbers, measured against the pass commit.** Three of the four titles came
back with **0 speaker corrections in 187 groups**. *A Cold Bargain* came back
with 30 in 386, **23 of them `nephews` -> a name**, 30.5% of its nephew domain --
and every one of those 23 arrived with a `cap_colour` the reviewer filled in,
which is the tell: **the caps were readable and I had not read them.**

**The mechanism, and it is not the one the findings above describe.** I measured
the confounders correctly -- the ship's railing really is `#e61b1f` H358.8, one
degree off Huey's cap panel -- and then made exactly the wrong inference from
them. `capwide` and the head census reported the RAILING on all three crowns of
139 p3 because it passes behind their heads at y265, and I wrote *"which boy is
which cannot be settled here"* three times **without ever opening the panel**.
One crop at 2.6x shows red, green and blue side panels, unmistakably, in the
order the review later corrected them to. The whole title cost 1.11 images per
page against a budget of 3.

- **A PANEL-LEVEL CONFOUNDER IS NOT A HEAD-LEVEL VETO.** Same-ink scenery means
  the SCAN cannot separate cap from background. It says nothing about whether the
  ART can. The roster already says a zero is a fact about the scan; this is the
  same rule one step on -- **an ambiguous scan is an instruction to crop, not a
  licence to decline**. When a band and a confounder share a hue, that panel has
  just become MORE worth an image, not less.
- **THE QUIZ SHOW IS THE CONTROL, AND IT IS IN THIS SAME BATCH.** There I had the
  identical problem -- 13 red and 4 green blobs, one of them 3018px directly above
  a head -- and I spent one crop. The boys were bare-headed, the scan was junk,
  and the title came back **0 corrections in 86 groups**. Same batch, same reader,
  same tools; the only difference is whether a panel was opened.
- **SPENDING UNDER BUDGET IS NOT A RESULT.** 1.11 images per page was reported as
  a good number in the close-out. It was the worst number in the batch. The budget
  is 3; the cheapest title in the ledger is not automatically the best one, and a
  page of small figures in a cap-keyed title is precisely where the images belong.
  **Report images/page next to the correction rate, and treat a low rate on a
  cap-dense title as a flag to re-check, not as a saving.**
- **A COLLECTIVE WHOSE NOTE RECORDS THE CAP INK IS THE WORST OF BOTH.** Several
  notes read "6091px of #4fa43c H109 at x164-280 ... the inks are recorded and not
  used". That costs the reviewer the same keystroke as a wrong name AND throws
  away the measurement. If the ink is good enough to write down, crop it and use
  it.

**Fixed 2026-09-17**: the 66 unreviewed nephew-domain groups on 140-155 were
re-read against crops showing balloon and cap together, and re-applied. 43 are
now named, 14 remain genuinely collective (figures 20-40px, or a tail tip in a
gap between two boys), and 9 moved out of the domain to Donald or Scrooge --
including two lines the first pass had given to **Scrooge** whose tails run to a
boy (144 g3, 145 g4). `vision_apply` left all 156 already-reviewed groups
untouched, as designed. `cap_mismatch.py` reports **zero** cap/name
disagreements from the title.

**The Antarctic parka key held and is worth keeping.** 148's dialogue chain names
the marching file, and the outfits recur unchanged through 147-155: red
ruff/blue trousers Donald, yellow/green Dewey, blue/orange Louie, orange/green
Huey. Confirmed panel by panel on 147 p2/p5/p8, 148 p7, 149 p5/p6, 150 p3/p7,
152 p8, 154 p1/p6/p7 and 155 p2/p3/p4. A costume key does not travel by
default -- but one the dialogue anchors, on characters wearing the same clothes
in the same sequence, does.

### Findings to paste into the next run (2026-09-17, sixty-second batch, ALL FOUR REVIEWED)

**541 groups, 48 speaker corrections (8.9%), and all 48 are in one title.**
*The Colossalest Surprise Quiz Show* (86), *Forecasting Follies* (51) and
*Fishing Mystery* (50) came back with **0 speaker corrections in 187 groups**.
*A Cold Bargain* came back with 48 in 355 (12.4%), **44 of them in the nephew
domain (55.0%)**. By the confidence the pass wrote: high 47/353 (13.3%),
medium 1/2. All 12 type corrections were confirmed and the whole corpus now
reports nothing outstanding across 460 titles. Mirrored clean on all four:
group count, reviewed count, `identified_by` and every distribution match, no
stragglers. 73 images over 41 pages, 1.78 per page.

**The split is the entire lesson, and it is not about difficulty.** All three
clean titles had a cap question in them; in each the pass opened the panel. The
one dirty title had the same kind of question on nearly every page and the pass
answered it from colour scans alone. See the 2026-09-17 correction section above
for the mechanism -- a panel-level confounder taken as a head-level veto -- which
is the single most expensive habit in this batch and the one to carry forward.

- **AFTER BEING TOLD YOU UNDER-NAMED, YOU WILL OVER-NAME. WATCH FOR IT.** The
  49 groups the re-read rewrote scored 10.2% corrected against 14.1% for the rest
  of the title, so the re-read was worth doing -- but **two of its five misses
  were over-naming** (141 g7 `Louie` -> `nephews`, 144 g8 `Huey` -> `nephews`,
  the latter with `cap red` -> `None`), which is the opposite error from the one
  being fixed. A cap you can see in a crop still has to be ON the speaker: 144 g8
  is one balloon over a row of three and the red cap belonged to a boy the tail
  did not reach. Cropping tells you what is printed; it does not excuse you from
  tracing the tail.
- **DONALD AGAINST SCROOGE IS THIS TITLE'S SECOND ERROR CLASS, AND IT IS NOT A
  CAP PROBLEM.** Nine corrections are `Scrooge` -> `Donald` (8) or the reverse
  (1), on 135, 136, 145, 149, 150, 152 and 155 -- two adults, no cap key between
  them, and the pass repeatedly gave the money-owner's register to Scrooge where
  the tail ran to Donald. Seven more are `nephews` -> `Donald`. **Sixteen of the
  48 corrections are Donald being missed.** In the Antarctic he is the RED hood;
  aboard ship he is the blue sailor cap and the red bow tie. Check for him before
  writing either `Scrooge` or `nephews`.
- **A DIALOGUE-ANCHORED COSTUME KEY IS WORTH ITS CROP AND IT TRAVELS.** 148's
  marching chain names the file front to back and keys the parkas -- Donald red
  ruff/blue trousers, Dewey yellow/green, Louie blue/orange, Huey orange/green --
  and the key held from 147 to 155 across ten pages. Of the 21 re-read calls made
  on it, 20 survived review. The standing rule that a costume key does not travel
  is about keys inferred from a prop; one the dialogue states, on characters
  wearing the same clothes through one continuous sequence, is evidence.
- **THE REVIEW WILL COIN A SECOND LABEL FOR A CHARACTER YOU ALREADY NAMED.**
  151 g1 and g2 are the same man one panel apart and came back as
  `other:the helicopter pilot` and `other:the pilot`. Nothing checks free-text
  speakers, so **list the distinct `other:` values at close-out on the REVIEWED
  data, not just on the pass's** -- the drift can enter at either end. Now
  reconciled; the batch ends on 24 distinct values.
- **WHAT THE CLEAN TITLES SHARE.** Both Gyro four-pagers and the Quiz Show
  resolved every speaker from an address (`UNCA SCROOGE`, `MR. McDUCK`, `BOYS`,
  `NEPHEW`, `SKIPPER`, `PILOT`, `SONNY`), from a sole figure in frame, or from one
  crop. None of them needed a colour scan to name anybody. The scans earn their
  place on cap-keyed nephew pages and almost nowhere else; on an adult-only title
  they are close to pure cost.

### Emphasis is [b] -- ruled 2026-09-17

**Emphasis is always `[b]`; `[i]` only when it covers a whole group set in a
slanted face** (emphasis inside a face is still `[b]`). The roster had offered
both tags as equal options, so batches drifted -- this one wrote Vol. 20 in `[i]`
and Vol. 16 in `[b]`. 1,184 groups across 16 volumes were rewritten by
`scripts/vision/normalize_emphasis.py` (214 face groups kept `[i]`), the roster
now states the rule, and `vision_apply` refuses `[i]` emphasis at dry run. An old
out-dir holding `[i]` results will be refused if re-applied; that is intended.

### Findings to paste into the next run (2026-09-17, sixty-third batch, BOTH REVIEWED)

**523 groups, 27 speaker corrections (5.2%).** *Land of the Pygmy Indians*
came back with 21 in 343 (6.1%), **19 of them in the nephew domain (21.1% of
90)**; *The Fantastic River Race*, which has no nephews, came back with 6 in
180 -- four of those are the review's own added lettering groups moving from
the editor's default `unknown` to `none`, so the pass itself had 2. By the
confidence the pass wrote: high 15/466 (3.2%), **medium 10/50 (20.0%)**. All
27 type corrections were confirmed. Mirrored clean on both, no stragglers after
one (167 g9). 76 images over 47 pages, 1.62 per page.

- **A CENSUS ZERO ON A THIN RIM IS STILL NOT A BARE HEAD. TEN COLLECTIVES WERE
  NAMED.** *Pygmy*'s boys wear black caps with a rim a few dozen pixels wide,
  and every one of the ten under-namings rested on the scan: `the census puts no
  cap ink on his head` (167 g7, 182 g1/g2, 183 g1/g8), a level teal the channel
  test calls unreadable (168 g3, 183 g6), or a grey crown probe (164 g12). The
  review named all ten, and none of the ten had a crop of the crown. This is the
  2026-08-31 *New Toys* finding again: on a rim construction, `no ink` means
  crop the crown, never write `nephews`.
- **THE LONG-SHOT DONALD DEFAULT IS WRONG WHEN SOMEBODY ELSE IS RUNNING THE
  EXPEDITION.** Six of *Pygmy*'s 21 were the default: 173 g7/g8 and 185 g8 went to
  Scrooge, 174 g1/g5 and 180 g4 to the boys. On a Scrooge story the planning and
  order-giving lines in a long shot are his; the default only holds where Donald
  is the lead. Read who is steering the plot before reaching for it.
- **A GAP TIP IS NOT A RULE ON ITS OWN.** 161 g19 (`Huey` -> `Dewey`) was a tip in
  the gap sent one head left while the tail visibly leaned right, and 179 g3
  (`Dewey` -> `Louie`) was an elimination built on a gap tip. Where the lean and
  the gap disagree, crop the tail; do not let the gap rule outvote the drawing.
- **MEDIUM IS STILL WHERE THE ERROR IS.** 20.0% against 3.2% for high. Nine of
  *Pygmy*'s 40 mediums were overturned.
- **ADULT-ONLY FLASHBACK TITLES ARE CHEAP AND CLEAN.** *River Race* named every
  speaker from an address (`CAP'N McDUCK`, `RATCHET`, `PAPPY`, `BOYS`) or a sole
  figure and cost 1.35 images per page -- six of its 27 images went on sweater
  badges and a bottle label, two on a label that stayed half-read. Crop lettering
  once; if it does not read at 4x, record the best reading and let the audit hand
  it to the reviewer.
- **THE REVIEW COINED `other:Peeweegahs` BESIDE `other:the Peeweegahs`.** Caught
  on the reviewed data and normalised. Keep listing the distinct `other:` values
  after the review, not only after the pass.
- **Captions set wholly in the slanted face were left untagged**, matching the
  earlier Vol. 16 titles (0 of 64 narrator groups carry `[i]`); the review did
  not change that.

### Findings to paste into the next run (2026-09-17, sixty-fourth batch, ALL FOUR REVIEWED)

**577 groups the pass wrote, 33 speaker corrections (5.7%)**, 32 of them in the
nephew domain (21.9% of 146). By title: *In Kakimaw Country* 10/157, *The Lost Peg
Leg Mine* 12/157, *Losing Face* 6/139, *The Day Duckburg Got Dyed* 5/124 (the two
`unknown ->` rows the tool prints are the review's own added groups). By the
confidence the pass wrote: **high 29/550 (5.3%), medium 5/27 (18.5%)**. All 8
type proposals confirmed; no text corrections. 74 images over 40 pages, 1.85 per
page. Peg Leg and Losing Face mirrored clean at full review; Kakimaw (112 g18) and
Dyed (136 g13) each came back one straggler short, both the last group on a page
where the review added a group.

- **UNDER-NAMING WAS 19 OF THE 33, AND EVERY ONE RESTED ON AN ABSENCE CLAIM.**
  `plain black caps with no rim` in a 0.8x crop (Kakimaw 116 g4/g5 -> Huey, Dewey),
  `bare-headed in swimsuits` (108 g10, 109 g11, 109 g13), `census NO INK ON CROWN`
  on tiny boys never cropped (Dyed 132 g8/g9), `no roster ink` (Losing Face, six
  times, all Louie). This is the sixty-third batch's first finding again, and
  quoting a zero count did not protect against it: on a thin-rim construction a
  0.45-0.8x crop and a capwide zero are both too coarse. **Crop the crown at 3x+
  before writing `nephews` on a lone or named-candidate boy.** Confirmed by the
  reviewer for *Losing Face*: all five cap-named Louies (123 g16, 124 g10, 124 g13,
  125 g4, 126 g1) have "a bit of green in the cap" -- a sliver that the pass's
  whole-panel capwide AND its after-the-fact crown probes both missed. A probe
  box guessed from a census span can sit off the ink; crop, do not probe.
- **A BOY KEEPS HIS NAME ACROSS A SCENE.** *Losing Face* 124 g14 (`IT DID!`, two
  tiny figures on the cliff) was named Louie with no cap readable, because Louie
  was the boy beside Donald on the nose in the panels just before. Where a wide
  shot is too small for a cap, carry the name from the panels that showed who is
  there.
- **TWO NAMED LEAVES THE THIRD -- STILL MISSED.** Dyed 137 g11: a turbaned
  silhouette beside a red-turbaned and a blue-turbaned boy was left `nephews`; the
  review wrote `Not Huey or Dewey` and named Louie. When the other two are placed,
  the silhouette is the third.
- **A TEAL RIM IS NOT A COLOUR JUDGEMENT TO DISMISS.** Peg Leg 010 g16: `#0d6d88`
  38px was written off as "dark teal, not a roster ink", in the same title where
  the pass itself established teal as Louie's ink. The review named Louie. Apply a
  title finding back to every note already written (back-propagate), not only
  forward.
- **ADULT-VS-BOY IS THE SECOND CLASS: 10 CORRECTIONS.** Donald -> a boy (Kakimaw 111
  g2 Louie, 117 g7, Peg Leg 010 g1 Louie, 012 g6, Dyed 128 g9), Scrooge -> Louie (Peg Leg
  016 g10, 017 g3), a boy -> Donald (Kakimaw 108 g9, Peg Leg 017 g12), Scrooge ->
  Donald (Kakimaw 117 g8). Every one was a tail read off the montage with no crop,
  the balloon assigned to the adult nearest it. **Peg Leg 012 g6 was named on
  `UNCLE SCROOGE is Donald's form` -- register is not evidence where a tail is
  drawn.** Crop the tail when an adult and a boy are both within reach.
- **A GAP TIP WITH A NAMED ALTERNATIVE: TAKE THE ALTERNATIVE THE GAP RULE GIVES.**
  Peg Leg 008 g1 went Huey (tip at the middle boy's crown edge) -> Dewey, which the
  note named as the one-head-left alternative. Over-naming twice where the call was
  a thin margin plus a ranked teal (008 g13, 014 g7 -> `nephews`).
- **LETTERING THE CAPTURE NEVER LISTED STAYS INVISIBLE TO THE AUDIT.** The review
  added Kakimaw 112 p6's `313` plate and Dyed 136 p8's `?` over Donald; neither was
  in `visible_text`. Every licence plate and drawn device, every page.
- **MEDIUM IS STILL WHERE THE ERROR IS** (18.5% vs 5.3%), but the absence claims
  above were all written at high.

### Findings to paste into the next run (2026-09-17, sixty-fifth batch, ALL FOUR REVIEWED AND MIRRORED -- batch closed)

**379 groups, 17 speaker corrections (4.5%), every one in the nephew domain (16.5%
of 103).** By title: *Picnic* 0/44, *The Sure-Fire Gold Finder* 0/50, *Gyro's
Imagination Invention* 11/142, *Red Apple Sap* 6/143. By the confidence the pass
wrote: **high 7/352 (2.0%), medium 10/27 (37.0%)** -- the widest split recorded. All
28 type proposals confirmed; no text corrections. 51 images over 30 pages, 1.70 per
page. All four mirrored clean at full review; *Imagination Invention* came back one
straggler short (143 g9), signed off separately.

- **A GYRO SOLO STORY IS FREE ACCURACY.** 94 groups, 0 speaker corrections, 19 type
  proposals all confirmed. The balloon drawing test -- a trail of bubbles is a
  thought, a pointed tail is speech -- carried both titles. Spend nothing extra there.
- **MEDIUM WAS WRONG MORE THAN ONE TIME IN THREE.** 10 of 27. Every medium was a tail read at
  page scale or a tip in a gap, and the pass's own note already said so. Where a
  medium is a gap tip between two boys, crop at 2x+ before writing it; a medium left
  as page-scale reading is a coin toss with a note attached.
- **UNDER-NAMING IS STILL THE LARGEST CLASS: 7 of 16**, and the same shape as the two
  batches before. *Imagination* 144 g9, 147 g1, 147 g4, 143 g11 and *Red Apple Sap*
  152 g6, 153 g14, 155 g9 were all `nephews` on `the census puts no cap ink` or
  `a sample returns no chromatic ink` -- none with a 3x crown crop. Two more reasons
  the review gave:
  - **Scene continuity names a boy** (155 g9: "Huey's on the fence in the next
    panel"). Look one panel either side before declining.
  - **An off-hue sliver on a cap is the dim roster ink, not a non-roster colour.**
    152 g6's `#a86625` H29 was written off as orange-brown; the review named Huey,
    and this title's reds print dim throughout (`#933e25` H14, `#a0361e` H11).
- **TINY FIGURES ARE NOT DONALD BY REGISTER.** 145 g2 and 146 g0 were given to
  Donald as "the explaining voice" over specks too small to tell apart; both went to
  `nephews`. The sixty-third batch's long-shot rule again: where the art cannot
  place the voice, the explaining-adult default is not evidence.
- **A GAP TIP IS NOT A NAME, EVEN AT MEDIUM.** 141 g6 (`Huey` on the lean) -> `nephews`;
  151 g14 (`Huey`, a few pixels) -> `Dewey`, the alternative the note named; 153 g5
  and 153 g17 (both page-scale) -> `Louie`, the boy neither note considered. 145 g10
  (`Louie`, tail pointing "away from Donald") -> `Donald`, again the named
  alternative. 143 g9 (`Dewey`, a balloon point read off a 1x crop with the pointing
  boy as the alternative) -> `Huey`, the red-capped boy neither reading named.
- **A COLOURIST ERROR CAN BE A TOUCH OF THE WRONG INK.** 143 g8: the census put
  dark red `#b1271a` 573px on the boy's crown and the pass named Huey; the review
  found the cap "mostly green but in error there is a touch of red" and named Louie.
  A census CAP-INK hit on a crown is the largest blob, not the cap's colour -- crop
  before naming off one.
- **DULL TEAL NAMES NOBODY ON ITS OWN.** 143 g13, named Louie on `#3f797a` 43px by
  analogy with the 142 g2 naming line, went to `nephews`. Teal ranks only beside
  another rim in the same panel.
- `other:` values after review: `Gyro's Helper`, `a lizard`, `the rattlesnake`,
  `Grandma Duck`, `Grandma Duck, Daisy and the boys`, `a tipsy gopher`,
  `the apple expert`, `the bees`, `the hen`. No near-duplicates.

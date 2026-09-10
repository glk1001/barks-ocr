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

## Per-volume cap palette
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

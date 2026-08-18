# The corpus-run prompt

The prompt that starts a vision pass over the next titles. Recovered from the
session transcripts on 2026-08-09 after it went missing; keep it here rather
than in scrollback.

The procedure lives in the `vision-pass` skill and the reading rules in the
generated `roster.txt`. **This file is only the part neither of those can
supply**: which titles, and what the last review found.

## The prompt

```
Run the next <N> corpus titles. Crops are not prepped.

  1. <Title>   (vol <V>, <P> pages, <year>)
  2. <Title>   (vol <V>, <P> pages, <year>)
  3. <Title>   (vol <V>, <P> pages, <year>)

<total> pages, #1-<N> on --todo. Sanity-check any title that looks incomplete
against its zero-group count before re-running it.

The vision-pass skill has the procedure; roster.txt has the reading rules.
Don't restate either back at me.

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

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

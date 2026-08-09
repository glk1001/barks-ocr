# Missed text — finding it, and a design for catching it during the pass

Some lettering in the art never becomes a group. Neither OCR engine finds it, so
nothing downstream can: it is not searchable, it has no box, and no review queue
will ever raise it. On *The Mad Chemist* four such pieces turned up by hand in a
ten-page title — a `WHOOM`, a `THUD`, and the car's `313` plate on two separate
pages — which is what prompted writing this down.

This splits into two halves. The **audit** exists and runs today. The **pass
change** does not, and the second half is a proposal.

## What the pass already knows

When the vision pass reads a page it transcribes non-speech lettering into the
page capture's `visible_text` — signs, plates, newspapers, sound effects painted
into the art. That is the same lettering the engines are apt to miss, and it is
already written down on every vision-passed page.

Nothing compares it against the groups. So the pass sees the miss, records it,
and the record goes nowhere.

## The audit (`scripts/vision/audit_missed_text.py`)

```bash
uv run python scripts/vision/audit_missed_text.py [--title "Some Title"] [--csv out.csv]
```

Diffs each page's `visible_text` against both engines' `ai_text`. Reads the
corpus rather than an out-dir, so it answers for titles whose scratch directory
is long gone. Read-only apart from the CSV.

Three things it has to get right, learned by getting them wrong first:

- **Normalize through the markup helpers, not a bare regex.** `ai_text` carries
  inline emphasis and escaped entities. A regex that keeps only letters and
  digits turns `[b]DANGER[/b]` into `BDANGERB` and `&amp;` into `AMP`, and the
  lettering then fails to match a group that plainly exists. A first pass
  reported 15 findings; using `strip_markup`/`unescape_markup` it is 12, and the
  three that vanished were all real groups.
- **Suppress story-logo echoes.** Some passes wrote the story logo into
  `visible_text` on every page of the run rather than only the splash that draws
  it. That was 63 of 78 raw hits on the first sweep. Matched against every
  `title`-typed group in the title.
- **Match per page, not per title.** Do not clear a hit because the same
  lettering is grouped somewhere else in the title — that is exactly the real
  case. *The Mad Chemist*'s `313` plate is grouped on 131 and missing on 128 and
  129.
- **Separate a near match from a gap.** The pass transcribes `visible_text` by
  eye, and on a sound effect that means counting repeated letters. It wrote
  `FZZZZT!` where the group — which both engines found — says `FZZZT!`. Reporting
  that as missing sends a reviewer to a page with nothing to add. Anything within
  `NEAR_MATCH_RATIO` of a grouped text goes to its own class instead, printed
  with the text it nearly matches so a reader can settle which reading is right.
  It is deliberately not folded into the covered case: which of the two is
  correct is a judgement, not something to resolve silently.

  These are worth reading rather than dismissing. The second one found —
  `5 BALLS 1` against a grouped `5 BALLS` — is not a wobble in the capture at
  all: the group's text looks truncated, which is a correction to that group
  rather than a new one.

Result of the corpus sweep, 2026-08-08: 203 vision-passed pages carrying
`visible_text` → **8 genuinely ungrouped items on 8 pages**, in volumes 1, 2 and
11, plus 2 near matches to check and 2 entries on the ignore list. Mostly signs
and small scenery.

That figure fell from 15 as each filter went in — 3 lost to proper markup
handling, 2 to the ignore list, 2 to the near-match class. Nearly half of the
first raw count was noise, which is worth knowing before trusting a future sweep
that has not been read carefully.

### Ignoring a finding

Some lettering is real but not worth a group, and there is no group to hang an
acknowledgement on — that is what makes it a finding in the first place. So the
audit keeps its own list, `scripts/vision/missed-text-ignore.txt`:

```
SOME LETTERING              # ignored wherever it appears
2 075 SOME LETTERING        # ignored only on that volume and page
```

Matched on the same normalization as everything else, so punctuation and case do
not matter. Two wartime public-service fillers are listed there, which is why the
sweep above reports 12 and a run today reports 10.

The audit prints how many entries it ignored on every run. An ignore list that
hides its own size stops being a record of a decision and becomes a way of not
seeing the problem.

**Do not instead edit a page's `visible_text`.** That field records what is
printed on the page and is true as it stands; an ignore belongs in the list,
where it carries a reason.

**Its limit:** it only finds what a pass wrote down. Lettering no pass ever
noticed is invisible to it, so the count is a floor, not a total. Closing that
gap is what the rest of this document is for.

## The pass can add the group — built 2026-08-08

### Where it goes, and why that is the whole design

At **apply time**, in `vision_apply` — never afterwards.

This is not a preference. Adding groups after a review was tried twice — on
*The Mad Chemist*, then across six pages of the back-catalogue sweep — and cost
four separate faults:

1. `renumber_groups()` sorts by `(panel_num, min_y, min_x)`, so a group added
   for an early panel takes its reading-order slot and pushes every higher id up
   one. Every stored id — queue files, the out-dir `result.json` — silently goes
   stale. Worse, the renumber does not fire on the add; it fires on the next
   ordinary **Save**, which may be minutes later and look unrelated.
2. The editor seeds a new group from a neighbour, so it arrives carrying that
   neighbour's `speaker`, `identified_by`, `vision_note` and `type` — a sound
   effect claiming `Donald` and a balloon tail. It does not look blank. It looks
   finished.
3. Because it looks finished, the one-key speaker confirm signed off on it.
   A wrong call acquired a human review flag.
4. Worse than 3, and the reason this is not just a matter of care: **Copy In
   deep-copies `speaker_reviewed`**. In a finished title every group is reviewed,
   so every group copied from one is born already flagged as reviewed, wearing
   the seed's speaker. Nobody has to press confirm at all. That happened on 6 of
   6 groups added during the back-catalogue sweep, without the reviewer doing
   anything wrong.

At apply time none of that exists yet: nothing is reviewed, no queue has been
cut, and the renumber settles once before anything depends on an id.

### What the sweep showed about doing it by hand

Six groups were added through the editor to close audit findings. Every box was
placed, every group reached both engines, and the numbering settled — and still
only three of the six were right:

- two had the box dead on the target lettering but kept the seed's `ai_text`
  (a group over `FOOF` reading `PFONK!`, one on the `313` plate reading `GET
  ALONG LITTLE DOGIES!`). The canvas looks correct; the text field is elsewhere
  on screen.
- one had correct text on a box over the wrong label entirely.
- all six arrived reviewed, per fault 4 above.

None of this is carelessness — it is what the interaction makes easy. The audit
caught all three text faults on the next run, because a group whose text does not
match the lettering still reads as missing. It could not have caught the box
fault; that needed cropping the box off the restored page image and looking.
`text_box` is in full-page coordinates, so the page image needs no panel
arithmetic — but note that some Vol. 1 pages are absent from
`Fantagraphics-restored` and present in `Fantagraphics-fixes-and-additions` as
`.jpg`, so a checker has to try both trees.

### Schema

A new top-level key in `result.json`, beside `groups` and `capture`. It has to be
separate, because `groups` validates its ids against the page's existing groups
and these have none yet.

```json
"added_groups": [
  {
    "panel": 5,
    "text_box_panel": [x0, y0, x1, y1],
    "ai_text": "WHOOM",
    "type": "sound_effect",
    "speaker": "none",
    "speaker_confidence": "high",
    "text_ok": true,
    "note": "Explosion lettered into the art above the goldfish bowl."
  }
]
```

**Panel-local coordinates, converted by the tool.** This is the one field worth
arguing about. The pass works in panel crops — that is the frame it can see, and
`panel-NN.png` shares the `text_box` coordinate space — so asking it for
full-page coordinates means asking it to do arithmetic it has no way to check.
The tool already knows every panel's origin from the data `dump_boxes.py` writes.
A wrong box is worse than no group: it anchors searchable text to the wrong place
and reads as authoritative.

### What `vision_apply` enforces

All of it before a byte is written, so a bad entry costs a message rather than a
group somebody has to find later:

- the entry is well formed, `type` is given (there is no stored value to fall
  back on) and `text_ok` is true (the text is being read off the art, so there
  is nothing to disagree with)
- the panel exists on that page, and the box lies inside its bounds
- the box does not cover more than `ADDED_GROUP_MAX_OVERLAP` of an existing
  group — that is a correction to that group, not a miss
- both engines have the page, since a group missing on one side is precisely
  what the mirror cannot repair: it copies fields onto matched groups and never
  creates one

Then it appends at `max(id) + 1` on both engines, renumbers each once, writes
`vision_added: true`, and does **not** set `speaker_reviewed` — the group reaches
the reviewer through the ordinary unreviewed queue like any other.

Proven end to end on 2026-08-08 against *The Mad Chemist*: a valid entry created
the same group with the same id on both engines with the numbering settled, and
the three refusals each reported and wrote nothing — a box given in full-page
coordinates by mistake (caught by the panel-bounds check, which is exactly the
mistake panel-local input exists to make impossible to commit silently), a box
over an existing balloon (100% overlap), and a panel the page does not have.

### The renumbering shifts every later annotation — found 2026-08-09

The append-and-renumber above is correct in itself, and it is also a trap: the
per-group annotations are written by the id in `result.json`, which is the
**pre-insertion** numbering. An addition at reading-order position *n* therefore
gives every group from *n* upwards the *previous* group's speaker, cap colour,
`identified_by`, note and type correction, and leaves the last group on the page
with none. Both engines.

Found on *Farragut the Falcon* 163, where a `ZOW` inserted at position 4 moved
nine groups: a `Dewey` call landed on the wrong balloon, and a speech balloon was
typed `sound_effect` because it inherited the next group's correction. Nothing
downstream catches it — the audit runs clean afterwards precisely because the
addition has landed, and the generated queue is one entry short for that page,
which is what desynchronises the editor mid-review.

Until `vision_apply` keys annotations after renumbering, treat any run that
reports *Added N group(s)* as suspect: re-check that page's annotations against
the corpus by `(panel_num, ai_text)`, which renumbering cannot move, before
building any queue. Repair the same way.

Two habits that would have avoided it entirely. **Check the other engine first**
— paddleocr already had that `ZOW`, so it was a copy-across and not an addition
at all, and adding it produced a duplicate. And note that the audit matches by
substring, so a short effect inside a longer one (`AWK!` within `SQUAWK!`) reads
as already grouped.

### Doing the adds after the review — worked through 2026-08-09

*Farragut the Falcon* finished with three structural gaps, deliberately left
until the review was mirrored because each renumbers a page: an `AWK!` on 159
grouped by neither engine, a panel-8 `OW!` on 158 that only easyocr had, and the
vertical `LATER` on 166 grouped twice on both. Closing them in the editor
afterwards worked — both engines came back holding the same 139 groups, matching
on every `(panel, text)` key and on every count — but it cost two repairs worth
knowing about in advance.

**A group added in the editor keeps the seed's `ai_text`.** The `AWK!` arrived on
both engines reading `SQUAWK!`, the text of the group it was seeded from, and
attributed to the wrong bird with it. The one group added to close a
searchability gap was therefore itself unsearchable, and the wrong text was on
the searchable field rather than anywhere a reader would notice. Check the text
of any added group against its own crop, not just its box.

**On easyocr it also arrived `speaker_reviewed`,** deep-copied from the seed, so
it was signed off before anyone had looked at it — and a title reporting a
complete review would have carried a group nobody read. Clear it and requeue.

Both hazards are in `SKILL.md` already; what this run adds is that they land
together on the same group, and that the corrupted field is the one the addition
existed to populate. The remaining check that catches them is the one that
catches the renumbering: re-verify by `(panel_num, ai_text)` afterwards, and read
the added groups' text off the art.

### The part that is not plumbing — still not built

The pass can now add a group when it notices one. It still only notices
incidentally: `visible_text` is filled in as conspicuous lettering catches the
eye. Making it dependable means an explicit step in the read — for each panel,
inventory every piece of lettering, then diff that against the groups supplied
for the page.

That is a real cost on every page, to catch something that ran about 2% of groups
on *The Mad Chemist* and 8 items across 203 pages elsewhere. Deliberately left
undecided: the audit now runs on every title, so the evidence for whether the
inventory earns its keep will accumulate on its own rather than being guessed at
now. The misses skew toward signs and shop lettering — the searchable content the
capture layer exists to serve — rather than toward speech, which is the argument
in favour when the time comes.

## Related

- `docs/vision-pass.md` — the pass itself
- `.claude/skills/vision-pass/SKILL.md` — the run procedure
- `scripts/vision/dump_boxes.py`, `scripts/vision/crop.py` — the panel-coordinate
  helpers the proposal leans on

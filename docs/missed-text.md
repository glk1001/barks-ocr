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

## Proposal: let the pass add the group

### Where it goes, and why that is the whole design

At **apply time**, in `vision_apply` — never afterwards.

This is not a preference. Adding groups after a review was tried on
*The Mad Chemist* and cost three separate faults:

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

At apply time none of that exists yet: nothing is reviewed, no queue has been
cut, and the renumber settles once before anything depends on an id.

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

### What `vision_apply` should enforce

- the panel exists on that page, and the box lies inside its bounds
- the box does not overlap an existing group above a threshold — that is a
  duplicate, not a miss
- write to **both** engines: a miss is nearly always a miss on both
- append at `max(id) + 1`, then renumber immediately, once
- never set `speaker_reviewed`, so it reaches the reviewer through
  `--unreviewed` exactly like every other group
- mark the group as pass-added — a reviewer looking at it should be able to see
  it did not come from OCR

### The part that is not plumbing

The pass has to notice reliably, not incidentally. Today `visible_text` is
filled in as conspicuous lettering catches the eye. Making it dependable means an
explicit step in the read: for each panel, inventory every piece of lettering,
then diff that against the groups supplied for the page.

That is a real cost on every page, to catch something that ran about 2% of groups
on *The Mad Chemist* and 12 items across 203 pages elsewhere. Worth deciding
deliberately rather than by default — and worth noting that the misses skew
toward signs and shop lettering, which is the searchable-content the capture
layer exists to serve, rather than toward speech.

## Related

- `docs/vision-pass.md` — the pass itself
- `.claude/skills/vision-pass/SKILL.md` — the run procedure
- `scripts/vision/dump_boxes.py`, `scripts/vision/crop.py` — the panel-coordinate
  helpers the proposal leans on

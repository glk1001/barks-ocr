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

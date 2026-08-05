# Vision pass — workflow, schema, and what the pilot found

A Claude Code vision pass over comic pages. It adds four things the OCR pipeline
cannot produce on its own: verification of `ai_text` against the art, **word-level
bold**, speaker attribution, and **structured page capture**.

Written 2026-08-01, after a pilot on Vol. 1 pages 076-085 — which is to say, on
the story *The Victory Garden*, since that page range is exactly one title.

---

## It runs in Claude Code, not against an API

This is deliberate and easy to get wrong. A standalone CLI that calls a model
programmatically — headless `claude -p` or the Claude Agent SDK — needs
`ANTHROPIC_API_KEY` and bills as API usage; a Max subscription will not
authenticate either, and the Batch API is API-billing only.

But this workflow does not need any of that. Claude Code reads the crops with the
Read tool and writes JSON, which is ordinary subscription usage. The Python tools
do only deterministic I/O.

```
barks-ocr-name-grep    --title "The Victory Garden"    # proper nouns, before reading page 1
barks-ocr-vision-prep  --title "The Victory Garden"    # crop, queue, roster.txt
   <Claude Code reads roster.txt + the crops, writes result.json per page>
barks-ocr-vision-status                                  # what has been read, and under which rules
barks-ocr-vision-report --out-dir ~/barks-vision/the-victory-garden
barks-ocr-vision-apply  --out-dir ~/barks-vision/the-victory-garden \
    --queue-out review.txt --queue-speakers speakers.txt
barks-ocr-retrieval-score --title "The Victory Garden"   # measurement 2
```

Two queues, deliberately separate: `--queue-out` holds the proposed text
corrections, `--queue-speakers` the groups whose speaker the model was unsure
of. They are different jobs — one is a transcription check, the other is a look
at the art — and the correction rate of each is only meaningful measured alone.
`--speaker-confidences` selects which confidences to queue, default `low`.

`--out-dir` defaults to `~/barks-vision/<title-slug>`. **Not `/tmp`**: a
snap-confined Firefox gets a private `/tmp` namespace and cannot open a report
written there, whatever the permissions say.

---

## Running a title: the short version

Everything below this section is *why*. This is *what*, for a session picking the
work up cold. The five-title trial is finished; what follows is the corpus run.

**1. Read `<out-dir>/roster.txt` before page 1.** It is generated from
`utils/vision_schema.py` on every prep and carries the whole vocabulary plus the
seven reading rules the trial produced — the collective, per-cap colour, no
reading order, observed cap colour, evidence, framing, emphasis — plus the crop
scales below. It is short, and it is what `vision_apply` validates against, so a
run that ignores it fails after the reading work is done. **Do not rely on this document for the rules**;
the rules are in that file precisely because prose in here was twice found not
to reach the pass.

**2. Batch one message per page.** `groups.json`, `page.png` and every panel crop
issued together in a single message. This is not a nicety — it is the entire
difference between **1.6 min/page and 11**, because the per-page cost is then one
model turn rather than ten round trips. Short titles cannot amortise the fixed
cost; long ones can.

**2a. Crop tails from `panel-NN.png`, never from `page.png`.** The panel crops
are source resolution and match the `text_box` coordinates in `groups.json`;
`page.png` is the downscaled overview, about half, so those same numbers land
somewhere else on it and the miss is silent. Upscale the crop 2–6x to trace a
tail or settle a letter. See *Two constraints that shape everything*.

**3. Grep the names first.** `barks-ocr-name-grep --title "…"` runs two passes
and both are needed: non-dictionary tokens catch odd spellings, repeated word
pairs catch names made of ordinary words. It buys the *spelling*, not the
identification.

**4. Stamp the model.** `vision_apply --capture-model "claude-opus-5[1m]"`, or the
provenance is written null and the page joins an unidentifiable cohort.

**5. Check state with `barks-ocr-vision-status`**, which reports pages read and
the rule version each was read under. Nothing else is a reliable record: the
scratch directories under `~/barks-vision` are not.

```bash
barks-ocr-vision-status --titles --todo     # the work list, oldest story first
barks-ocr-vision-status --next              # just the next title, for a script
```

`--titles` is the answer to *what have I done and what is left*, and it is
**derived from the corpus on every run rather than kept in a tracking file** —
the same argument the volume report has always made. A title is read iff its
groups carry a speaker, so there is nothing to keep in step and nothing to go
stale. Chronological order comes free: the `Titles` enum is already in
submission order, checked across all 450 titles with a year for **zero
inversions** against it.

Chronological order **front-loads the risk**, deliberately. The first forty-odd
stories are 1942-45, which is exactly where the reading-order finding is
untested. Better to learn that on title 3 than on title 200 — but expect the
early titles to be less representative than the trial's averages suggest.

### Where things stand, 2026-08-03

| | |
|---|---|
| pages read | 77 of 5,560 (1.2%) — the pilot and five trial titles |
| rule version | **6** (`capture_prompt_version`); cohorts on disk are unstamped and v2 |
| retrieval | `barks-ocr-retrieval-score`, three matcher generations, `--validate` first |
| speaker review | four audits and two backfills complete — see *Four audits* below |

Two things to watch on the first titles of the corpus run, both recorded as open
rather than settled:

- **the reading-order finding rests on one pre-1948 title.** Vols 1-5 are roughly
  1942-47. If early tails really are less precise, that is where it shows.
- **`observed-cap-colour` should start surfacing tail/cap disagreements.** If it
  never does across many titles, suspect the colour is still being written in
  from the convention rather than read off the page.

Known blockers, unchanged: **155 one-pagers cannot be prepped at all**, and 24
pages have no prelim OCR.

---

## The unit of work is the story, not the volume

`--title` is the primary selector. `--volume` with `--pages` still works for a
deliberate page range, and warns when the range crosses titles.

This is a correctness argument rather than a tidy one. **The closed vocabulary is
per-story**: it is the roster plus the characters the database tags as appearing
in *this* story (below). A volume averages 15.5 titles, so a volume-wide run can
only be handed the union of fifteen casts — which is looser, and lets the pass
confidently name a character out of a different story. `setting` has the same
problem, and `panels_of_note` is meaningless outside a story, since "worth
addressing on its own" is relative to the story around it.

Everything upstream is already keyed this way — `TitlePanelBoxes`,
`BARKS_TAGGED_TITLES`, `story-titles/<Title>.ini`, the sibling wiki's story
pages. A Fantagraphics volume is a printing artifact, an arbitrary bundle of
stories; the knowledgebase is about the stories.

Measured: **450 configured titles across 29 volumes**, 5,560 prelim pages —
about 12.4 pages per title against ~205 per volume. One-pagers are the awkward
case, since a prep run, a session and an apply run for a single page is mostly
overhead; they are best batched, which is safe precisely because they share no
context.

---

## Two constraints that shape everything

**Crops must be 256-colour PNGs.** Claude Code's Read tool re-encodes any image
over ~500KB as reduced-quality JPEG, which destroys exactly the fine lettering
bold detection depends on. Plain `save("PNG")` exceeds that on roughly a third of
Vol. 18's panels. `quantize(colors=256)` is visually lossless on flat-colour line
art and takes the median from 454KB to 217KB. `vision_prep` asserts the threshold
and fails loudly rather than hand over a degraded crop.

**Send panel crops, not the page.** A whole page would be downscaled *and*
recompressed. Panels (median 891x636) pass through at native resolution, so the
36px lettering survives. The page overview is sent too, but only for cross-panel
context — reading order, who is in frame.

**So the two image files in a page directory are not in the same coordinate
space, and tracing a tail means knowing which is which.** `panel-NN.png` is at
source resolution; `page.png` is the downscaled overview — about half, 1087x1500
against a ~2175px page on a Vol. 1 ten-pager. The `text_box` corners in
`groups.json` are in **source** coordinates, so they line up with the panel crops
and are roughly 2x too large for the overview.

Crop from the panel files. Cropping `page.png` with numbers taken from
`groups.json` lands somewhere else on the page entirely, and the failure is
silent: what comes back is a plausible piece of comic art with no balloon tail in
it, which reads as a badly drawn tail rather than as a mistake in the crop. Cost
a wasted cycle on *The Limber W. Guest Ranch* before the ratio was noticed.

Upscaling the crop is what settles the hard calls — `Image.LANCZOS` at 2–3x to
see which hat a tail leans at, 4–6x to settle a single letter. On that same title
the page overview showed a balloon ending in a D where the panel crop at 6x shows
the P of `GIDDAP!` — a word-level correction that would have been filed against
text that was right all along.

**A panel too big even quantized is tiled, not shrunk.** Added 2026-08-03, when
*The Big Bin on Killmotor Hill* became the first title to abort prep: four of its
75 panels exceed 500KB at 256 colours, and **two of them do not fit at any palette
depth down to 64**. So the palette had nothing left to give and the choice was
between resolution and tiling.

Tiling wins because the two things a smaller crop costs are exactly the two the
pass is weakest at — the 36px lettering, and telling a green cap in shadow from a
blue one, which the trial-4 audit found is where 4 of 5 speaker errors live.
`_write_panel` therefore splits an oversized panel into 2–4 overlapping
full-resolution tiles (`panel-01a.png`, `panel-01b.png`, …), 15% overlap so no
balloon or face lands on a cut. The overview keeps its *resolution* ladder for
the opposite reason: it carries no lettering at all.

The queue's `panels` list carries the tile names, and `vision_report` reads that
list rather than guessing `panel-NN.png`, so a tiled panel renders as its tiles
instead of one broken image.

One unexpected benefit: **Big Bin needed zero enlargements in ten pages**, against
Sheriff's 11 in 32 and *Plenty of Pets*' 8 in 10, because the tiles are already a
magnified view of the biggest panels. And one unexpected diagnosis — see trial 5:
`047`'s oversized panel is oversized because `panel_boxes` merged two drawn panels
into one box, so the size assertion doubles as a panel-segmentation smoke alarm.

---

## Schema

Written onto each group in the prelim JSON by `vision_apply`:

| key | values |
|---|---|
| `speaker` | roster name, `narrator`, `none`, `unknown`, or `other:<free text>` |
| | roster: Donald, Huey, Dewey, Louie, `nephews`, Daisy, Gladstone, Scrooge, Gyro |
| `speaker_confidence` | `high` / `medium` / `low` |
| `speaker_reviewed` | `true` once a human has confirmed the speaker in the editor. It also **freezes the call against a re-apply** — see below |
| `cap_colour` | `red` / `blue` / `green`, or `null` when not visible |
| `identified_by` | what the call rests on — a **list** of `balloon-tail`, `cap-colour`, `costume`, `hat`, `sole-figure`, `dialogue`, `caption`, `off-panel`. Required wherever somebody speaks |
| `speaker_was`, `cap_colour_was` | the pass's call, kept when a review **changes** it. Absent on a confirmation |
| `speaker_reviewed_date` | when a human looked |
| emphasis | inline in `ai_text` as `[b]WORD[/b]` / `[i]WORD[/i]`, not a separate field |
| `vision_note` | the reasoning behind the call |
| `vision_text_ok` | `false` when the art disagrees with `ai_text` |
| `vision_corrected_text` | the reading from the art |

**A review outranks the pass, and `vision_apply` now enforces that.** On a group
carrying `speaker_reviewed`, a re-apply leaves `speaker`, `speaker_confidence`,
`cap_colour` and `identified_by` exactly as the reviewer left them — the four
keys the editor writes — and says how many it left alone. It still refreshes
`vision_note` and the two text fields, because those are the pass's own
reasoning and its text proposal, not the reviewer's; the reviewer's reasoning
lives in `speaker_review_note`. A reviewed group is also no longer re-offered by
`--queue-speakers`.

Fixed 2026-08-05, after a re-apply run only to regenerate the review queues put
`Donald` and `medium` back over a review that had corrected *Good Deeds* 262 g4
to `nephews`, leaving `speaker_reviewed: true` beside a `speaker_was` equal to
`speaker`. That equality is the signature of the damage if it is ever seen
again. Before the fix a second apply was safe only on a title with no review on
it yet, which is not a property anybody could see from the outside.

**A capture record is only rewritten when its substance changed.** `captured` is
stamped fresh on every run, so an unconditional write made a re-apply rewrite
every capture file on the title even when the reading was identical — ten files
of pure timestamp churn burying the two or three lines that actually changed,
which is most of why the clobber above was hard to see in a diff. The comparison
ignores `captured` alone, so a changed `capture_model` or prompt version still
rewrites, and an unchanged record keeps the older and more accurate date: the
stamp says when the reading was established, not when a command last ran over
it. The run reports how many it left alone.

**The group JSON is likewise only saved when applying moved something in it.**
`save_json` copies the file into the backup tree before every write, and backup
names carry the source file's timestamp, so they accumulate — an unconditional
save meant a re-apply left a fresh backup of every page on the title with
nothing to distinguish it from the last one. 383 of them had piled up against
these ten pages, 90 in one afternoon. The test is the serialized page JSON
before and after, not the counters kept while applying: those count groups
*touched*, and every group is touched on every run by design.

**A re-apply of an unchanged title is now a complete no-op** — verified on *Good
Deeds*: 147 groups, both engines, zero files written and zero backups taken.
Change one group and exactly that page is rewritten and backed up, on both
engines, while the other nine are left alone.

### Page capture

One record per page, written to a sibling `{page}-page-capture.json` — **not**
into the group JSON, since `final_groups.py` copies only the `groups` key and
would silently drop a new top-level section.

| key | values |
|---|---|
| `characters` | who is **depicted**, from the closed set. Not who speaks: silent and in frame still counts |
| `setting` | `indoors`, `outdoors`, `street`, `countryside`, `wilderness`, `at sea`, `underground`, `unknown`, or `other:<named place>` |
| `time_of_day` | `day` / `night` / `dusk-or-dawn` / `indoors-or-unclear` |
| `visible_text` | lettering that is not speech — signs, posters, newspapers, labels, painted sound effects |
| `objects` | notable things visible, at most 12. Free text: `fly swatter`, `goldfish bowl` |
| `beats` | 1–3 plain sentences saying what happens. Only what is shown |
| `panels_of_note` | `[[panel_num, phrase], …]` for panels worth addressing alone |
| `capture_model`, `capture_prompt_version`, `captured`, `capture_rules` | provenance — written by `vision_apply`, not by the pass. Null on everything read before 2026-08-03; see the status section |

**This replaced free-prose panel descriptions, which the pilot used.** Prose is
inconsistent across stories, hard to query, impossible to review at ~33,000
panels, and it blurs *what is in the panel* (verifiable, the same category as
OCR) with *what it means* (inference). Structured fields separate the two.

The deeper reason it can be this thin: the **panel image stays the artifact**.
`panel_boxes.py` already addresses every panel in the corpus, and crops
regenerate in seconds, so capture only has to put the right page in front of a
model that will then look at the art. That is a far weaker requirement than
describing the art in words — and it is only available because *complete story
reconstruction from text alone* is explicitly not a goal.

`panels_of_note` is how "panels on demand" is encoded without describing all
33,000: most pages need none. `beats` is capped at three sentences, which is the
schema's only guard against capture drifting into a page-by-page retelling.

`visible_text` is the biggest gap it closes — unrecoverable from speech OCR, and
with **no pilot baseline at all**, so its yield is itself a thing the next run
measures.

### `objects` exists because the queries specified it

It was not in the original design. `beats` was expected to carry props, and the
plan said an explicit field had to earn its place only after raising `MAX_BEATS`
failed. Writing the retrieval queries settled it without needing the trial:
around sixty of them ask for background props, and **"Roscoe the Robot" is four
pages whose queries name ten distinct objects** — a fly swatter, a goldfish bowl,
dumbbells, a legless chair, a hammer, a medical kit, a fly. Three sentences a
page that must also carry the plot could never hold that, and a longer cap would
not have helped: a prop only reaches a beat sentence when it is plot-relevant,
and the discriminating queries are deliberately about props that are not.

That is the query set doing its job — specifying a field before any vision
session was spent discovering the gap.

No closed vocabulary, because there cannot be one. Free text, whitespace
collapsed, promoted by census like any other free-form value. The cap of 12 is
there for a different reason than `MAX_BEATS`: that one guards against retelling,
this one against an **inventory**. A page listing thirty objects matches every
query and discriminates nothing.

The database's `THINGS` tags ride along as **naming anchors** rather than a
vocabulary — `story_things()` puts `313`, `HDL driving car` and `cigarettes` in
front of a *Sheriff of Bullet Valley* run, and `square eggs` in front of *Lost in
the Andes*, so a recurring prop is written the same way every time instead of
arriving as "a car", "the red car" and "313". The category is narrow and mostly
chemical names from the Gyro stories, so an empty result is the common case.

### The vocabulary travels with the crops

The roster lives in `utils/vision_schema.py` and is enforced only at *validation*
time. So that the pass is not left guessing the names, `vision_prep` renders the
whole vocabulary — roster, this story's tagged characters, confidences, cap
colours, emphasis kinds, and every capture field — from those same constants into
**`<out-dir>/roster.txt`**, next to the crops. Read it before starting; otherwise
a run that writes `Uncle Scrooge` for `Scrooge` fails `vision_apply` after the
reading work is already done.

It is generated, never hand-written, and rewritten on every prep run, so a name
added to the roster reaches the next pass on its own. Each page also gets a
`page-capture.json` stub with its **real panel numbers already filled in**, so
`panels_of_note` is a choice from a list rather than a guess.

### The database already knows most of the cast

The roster is the main cast and nothing else, which leaves the long tail —
Bolivar, Magica, Soapy Slick, Argus McFiendy — with nowhere to go but free text.
The database has already answered this: its character tags say which named
supporting and one-off characters appear in which story, so the pass is handed a
short list and asked which of them are on the page. **A closed-set question
instead of an open one**, and a name outside the set becomes an error signal
rather than silent drift.

`vision_prep` resolves them per title and folds them into `roster.txt`;
`vision_apply` validates against the same set. 48 distinct names across four tag
groups, though many stories get none — *Lost in the Andes* and *The Victory
Garden* both do — and `other:` still carries the rest.

Note what the tags deliberately omit: Donald, the nephews and Scrooge are in
nearly everything, so tagging them would be noise. The tags are the tail; the
roster is the head; the closed set is the union.

Two traps the database data holds, both handled in `utils/story_cast.py`:

- **Its tags name `Daisy Duck`, `Gladstone Gander` and `Gyro Gearloose` in
  full**, where the roster has the short forms. Offering both would make one
  character into two speakers — exactly the drift the closed set exists to
  prevent — so they are aliased. Two further entries, `Gyro not in GG series`
  and `Uncle Scrooge not in US series`, are not names at all: they record where a
  story sits in the series and only look like cast because of where they live.
- **`Secondary Characters` *contains* the `Pig Villains` group**, rather than
  listing its members. Iterating the raw dict therefore adds the literal string
  `"Pig Villains"` as though it were a person, and drops Soapy Slick and five
  others. Use the database's own `get_all_tags_in_tag_group`, which flattens
  recursively.

### One-off characters, and keeping them from splitting

A character neither on the roster nor tagged for the story goes behind the
prefix: `other:Argus McFiendy`. In the pilot that mechanism carries 26 of 138
attributions, though for unnamed roles rather than named one-offs —
`other:crows` (17), `other:crowd` and `other:football players` (4 each),
`other:shopkeeper`.

Free text is where drift gets in: `other: Argus` and `other:Argus` name one
character and are two speakers. Both write paths therefore run
`normalize_speaker` — outer and repeated whitespace collapsed, and a roster name
written behind the prefix (`other:Donald`) unwrapped to the roster entry it
already is. `vision_apply` canonicalizes *before* validating, so the value that
is checked is the value that gets stored.

Case is deliberately left alone. "McFiendy" has no safe automatic casing, and
title-casing it would be a different kind of wrong, so case variants are
surfaced for a human instead:

```bash
barks-ocr-speaker-census                 # whole corpus, ~5s
barks-ocr-speaker-census --volume 1-3
```

It reports counts per name, spellings that collapse onto one speaker, anything
off-roster or not in canonical form, and the free-form names used often enough
to be worth promoting (`--promote-at`, default 10). It is read-only.

**A recurring `other:` name is the signal to promote it** into `SPEAKER_OPTIONS`.
It is then exact-matched, so its spelling can no longer drift, and `roster.txt`
regenerates on the next prep. Genuinely one-off characters stay behind the
prefix — putting a single story's villain on the roster would only make the
editor's popup unusable.

---

## What may be published, and what may not

The Barks comics stay in US copyright until roughly **2038–2062**, so the corpus
splits permanently. That split is recorded **per field, in code** —
`PublicationClass` in `utils/vision_schema.py` — rather than left to whoever
writes the next exporter.

| class | meaning | fields |
|---|---|---|
| `FACT` | measurements, ids, closed-vocabulary labels | `panel_num`, `text_box`, `characters`, `setting`, `time_of_day`, `speaker`, `cap_colour` |
| `DERIVED` | our own words *about* the work | `beats`, `panels_of_note`, `vision_note`, `notes` |
| `VERBATIM` | text copied out of the comic, or inseparable from it | `ai_text` (emphasis markup included), `visible_text`, `vision_corrected_text` |

`classify()` **raises on any field not in the table** rather than defaulting. A
field nobody has classified must stop an export, because guessing permissively
publishes someone else's copyright. Each written capture record also stamps its
own fields with their class, so an exporter never has to look it up elsewhere —
and cannot quietly stop looking.

Emphasis needs no row of its own: it is inside `ai_text`, which is already
`VERBATIM`. Under the retired `emphasis_spans` it was classed `VERBATIM` too, on
the reasoning that offsets encode the shape of the text they index — inline
markup makes that literal rather than an inference.

**Why in the data and not in a document:** the sibling `barks-wiki` states "never
reproduce" in four separate places, and its `generate_covers()` still emits 189
verbatim Barrier synopses — because the rule lived in prose and the generator
underneath it did not follow it. A rule a generator cannot read is a rule a
generator will break.

The public-facing precedent is worth knowing: **no long-lived public Barks
project publishes dialogue.** INDUCKS has run 30 years on story codes, credits,
appearance lists and one-line descriptions, with scans disclaimed and hosted
separately. Wikipedia publishes plot summaries, short quotes and one cover per
article. The operative test is *could someone read the work from what you
published?*

---

## The speech script

```bash
barks-ocr-speech-script --title "The Victory Garden"
barks-ocr-speech-script --out-dir ~/scripts --format json    # whole corpus, ~7s
```

Assembles what is already on disk — the speech, the panel numbers, and the
speaker attributions where the pass has run — into one ordered document per
title. It needs no vision session, so it is the cheapest available check that
`(title, page, panel_num)` really addresses the corpus: a full run produces **441
scripts and 71,355 lines in under seven seconds**, and reproduces the
missing-prelim list below page for page.

Reading order is derived rather than assumed. `get_panel_groups()` is
deliberately *not* used — it drops every group whose `panel_num` is -1, which
would silently lose 140 real lines corpus-wide. Those are kept, sorted to the end
of their page, and counted, since a page whose groups are mostly unplaced has a
`panel_num` problem worth seeing.

One engine per run: the two engines' group ids do not correspond, so interleaving
them would print each line twice under two numbers. With no speaker data the
column disappears rather than filling with blanks, so it is useful on the corpus
as it stands today. Output is `VERBATIM` and stamped local-only in both formats.

---

Design decisions worth not re-litigating:

- **A result with no page capture is refused.** One record per page is the
  schema, and a missing one used to apply cleanly and print a group count that
  read as success — which is how *Billions to Sneeze At* once merged 136 groups
  and zero capture records silently. The commonest cause is composing the record
  in the `page-capture.json` stub `vision_prep` leaves in the page directory and
  never copying it into `result.json`; `vision_apply` checks the stub and says so
  when that is what happened. `--no-capture` is for a deliberately groups-only
  run. The closing line counts capture records alongside groups, so a shortfall
  is visible even when it is allowed.
- **The vision pass never changes the words of `ai_text`.** It adds emphasis
  markup, and the run is refused unless that strips back to the stored text.
  Corrections go to a kivy-editor queue for review. Saves use
  `save_json(backup_file=...)`, unlike `ocr_check`'s bare `save_json()`.
  **The text queue converges**: a group whose stored `ai_text` already matches its
  `vision_corrected_text` is not re-queued, both sides compared stripped, so a
  human who applied a correction while keeping the emphasis still counts as done.
- **Publication class lives in the data**, not in this document. See above.
- **`setting` and `time_of_day` are separate fields.** Folded together, every
  place would need a value per lighting condition. And the pilot showed time of
  day carries its own signal: the unreadable cap colours on 079 are unreadable
  *because* it is a night scene, so recording it explains a low-confidence
  cluster rather than merely observing one.
- **Inline markup, not spans.** Emphasis is written into `ai_text` itself as
  `[b]WORD[/b]`, Kivy's own syntax. This reverses an earlier decision and the
  reasoning is worth keeping — see below.
- **Both the name and the colour.** Naming a nephew relies on the Huey-red /
  Dewey-blue / Louie-green convention, which was not firmly fixed in 1943 Barks.
  Recording `cap_colour` alongside keeps the mapping reversible if it turns out wrong.
- **`nephews` is a roster entry.** Some stories give two or three of them the
  same cap colour — 085 p3 of the pilot does — and some lines the three speak
  together. `nephews` is the honest answer there, and is not the same as
  `unknown`, which means the speaker could not be placed at all. Prefer it to
  guessing a name; a guess is unrecoverable, a collective is not.
- **`vision_` prefix on the reasoning fields.** The group already carries a
  Gemini-written `notes`; a bare `note` beside it would be a trap.
- **The vocabulary lives in `utils/vision_schema.py`.** `vision_apply` validates
  against it and the editor offers it back; a roster name in one but not the
  other would be a trap that only shows up as a rejected result file.

---

## Emphasis: inline markup, and why the spans were retired

Emphasis lives **inside** `ai_text`, as `[b]WORD[/b]`. It used to be a separate
`emphasis_spans` field holding `[[start, end, kind], …]` character offsets. That
was the wrong call, and it was reversed on 2026-08-02, before the trial went any
further.

**Offsets index a string that other tools edit.** The kivy editor rewrites
`ai_text`, `string_replacer` runs bulk regex substitutions over it, and applying
a queued vision correction changes its length. Each of those moves the text out
from under a stored offset.

The pilot had already produced the failure and nobody had noticed. `077 g1`
carries a bold span over `SABOTEURS` and a **queued, unapplied** correction that
shortens the text by two characters. Applying it would have slid the span two
characters along, off the word it marks:

```
span (26, 35)
in stored ai_text : 'SABOTEURS'
after correction  : 'BOTEURS!'
```

**No validator could have caught that**, which is the whole argument. The span
stays in range, so a bounds check passes; the corruption is a shift, not an
overflow. Roscoe then added two *one-character* spans — a lone emphasized `I` —
which is the case where a drifted offset is guaranteed to land on some other
letter and look entirely reasonable.

Inline tags travel with the characters they mark, so the failure cannot occur.

### What the reversal cost, and the four guards that pay for it

The original objections were real but all dissolve under stripping at the
consumer boundary, and Whoosh turns out to support exactly the shape needed:
`_stored_content_raw` lets one field be **analysed stripped and stored marked
up**, so search matches plain text while the reader gets tags back to render.

What does not dissolve is that markup fails *open* — a consumer that forgets to
strip leaks `[b]` into a search result — where spans fail *safe*. That trade is
still worth making, because a leaked tag is noticed the first time anyone looks
and a drifted offset is invisible forever. **Visible failures beat silent ones.**
Four guards keep it honest:

1. **Strip in the accessor.** `SpeechText.ai_text` is plain; `ai_text_markup`
   carries the tags; `raw_ai_text` is what is on disk. A consumer that has never
   heard of emphasis is correct by doing the obvious thing. `SearchEngine`'s
   `SpeechInfo` has the same split. The raw-dict readers an accessor cannot
   reach — `ocr_check`, `group_checks` — strip explicitly.
2. **Escape on write.** `[`, `]` and `&` in the lettering become `&bl;`, `&br;`,
   `&amp;`. Not hypothetical: 31 corpus groups hold brackets, including Gemini's
   own `[Illegible Comic Covers]` annotations, and 59 hold an ampersand, from
   signs like `GOLDSTEIN & CO.`
3. **Compare stripped text where the metric matters.** `save_group` stays
   markup-sensitive or an emphasis edit would be dropped; `groups_with_text_changes()`
   answers the different question the correction rate counts. Stronger still,
   `vision_apply` **refuses the run** unless the proposed markup strips back to
   the stored words — which also closes the gap between reading the crops at prep
   time and applying the result later.
4. **`string_replacer` strips, matches, re-inserts.** A pattern for `YOU — YOU`
   would not match `YOU — [b]YOU[/b]`: a silent under-match, the same class of
   wrongness. It now matches against stripped text and accepts the substitution
   only when it does not straddle a tag, refusing and **reporting** the rest.

Two places refuse rather than mangle: re-wrapping a marked-up group (`ocr_check`
and the editor's Copy Fmt) would have to move the tags to new positions, which is
the offset problem again.

### The one accepted regression

Search highlighting is confined to the lettering, so a phrase spanning an
emphasis boundary — "really sharp", where only SHARP is bold — is not
highlighted. Retrieval is unaffected; the page is still found, because the index
holds stripped text. It is only the colour in the bubble list that goes missing.

Confining it is not optional. Substituting over the whole string let a search for
`b` wrap the `b` inside `[b]`, and `amp` the one inside `&amp;`, producing a tag
Kivy cannot parse — **visibly broken text on screen**, and for `amp` in any of
the 59 ampersand groups whether or not emphasis was ever added. A missed
highlight is harmless; a mangled tag is not.

### Migration

`barks-ocr-migrate-emphasis` (dry run by default, backs up every file it writes)
folded 17 span sets into markup and escaped 90 groups — 107 groups across 86 of
11,120 files. Every conversion was verified to strip back to the original text
before anything was written. Doing it at 25 spans was cheap; at corpus scale it
would not have been.

## Reviewing the speaker calls in the editor

```bash
uv run barks-ocr-kivy-editor -- --queue-file ~/barks-vision/<title>-speakers.txt
```

**The bare `--` is required**, and only for the Kivy tools — this one and
`barks-ocr-annotate`. Kivy parses `sys.argv` itself at import and rejects flags
it does not recognise; it stops at `--` and leaves the rest to Typer. Neither
tool sets `KIVY_NO_ARGS=1`, which would remove the need for it. Every other
command in this document takes its flags bare.

Each engine column has a **Speaker** button. It opens the roster, the cap-colour
row, and — read-only — what the vision pass itself said and why.

It is deliberately **per-pane**, unlike Set Type and Set Flor. The vision pass
runs against one engine, and the two engines' group ids do not correspond, so
writing the other pane's group would invent an attribution for an unrelated text
box.

Saving records the human's answer, sets `speaker_confidence` to `high` — someone
has now looked at the art — and sets `speaker_reviewed`, which is what
distinguishes a confirmation from the model's own confident guess. The
population that *was* low-confidence before review survives in the
`--queue-speakers` file, so the correction rate is still measurable afterwards.

Nothing is written unless a roster entry is picked: opening the popup on a group
the vision pass never saw and pressing Save is a no-op. `other:` with an empty
box is refused rather than saved as a nameless speaker.

**Confirm as is** covers the other outcome — agreeing with the call. Added
2026-08-03, before the *Plenty of Pets* queue was reviewed. It stamps
`speaker_reviewed` and moves the confidence to `high` while leaving `speaker`
and `cap_colour` exactly as the pass wrote them.

Without it, agreeing wrote nothing at all, so **a confirmation was
indistinguishable on disk from a group nobody ever opened** — which is why
*Sheriff of Bullet Valley*'s 13 confirmations rest on GLK's report rather than
on the data, and why the pilot's four genuinely-unjudgeable entries cannot be
told from entries no one reached. The denominator of the speaker-review rate is
now self-evidencing.

The button refuses rather than guesses if the popup's selection has been moved
off the stored value: "as is" means what is on disk, and a reviewer who retyped
a name and then hit the wrong button would otherwise record a confirmation of
the value they had just replaced. Comparison runs through `normalize_speaker`,
so `other:Donald` typed over a stored `Donald` is correctly seen as *unchanged*
rather than as an edit. It saves through `save_json()` on `_has_changes` alone,
so a group whose text never changed still reaches disk.

The pane header carries `[spkr: <name>]` once a group has one, so the queue can
be walked without opening the popup on every entry.

---

## Pilot results — Vol. 1, pages 076-085

10 pages, 55 panels, 134 groups.

| | |
|---|---|
| `vision_text_ok: false` | 2 (1.5%) |
| groups with emphasis | 5 |
| confidence | high 78 / medium 38 / low 18 |
| `cap_colour` non-null | 37 |

**The 1.5% correction rate is the baseline that matters.** Vol. 1 is already
checked, so a high rate would mean the pass is hallucinating, not that the volume
is dirty. Re-measure this on any future run before trusting anything else in it.

The five bolds each carry a joke or plot beat, and one is in **background text**
(`QUICK-GROWING INVISIBLE SEEDS` on a shop poster) — the hook the story's ending
hangs on. None are recoverable from existing fields.

### `style == "emphasized"` is not ground truth

`style` is a **whole-group** flag. Across these 10 pages, not one group carries
`emphasized` despite five unmistakable bold words. Do not use it to validate bold
detection — the only real check is looking at the art.

### Speaker confidence degrades predictably

Caps read cleanly in daylight panels. They are unreadable when:

- the scene is at night — everything renders flat moonlight blue (079 p2);
- the colourist slips — 085 p3 gives two nephews the same green.

Those cases are among the 18 `low` entries, and `cap_colour` is `null` there, so
nothing is silently guessed. Where the art carries the colour some other way — the
red/blue/green pyjamas in 085 p5 — identification still works.

**Football helmets are *not* a reliable predictor**, though an earlier draft of
this doc said so. The review below confirmed all three of 078's helmeted nephews
as correctly named, while 080 and 083 — also helmeted — were wrong. Helmets
appear on both sides, so they do not explain the failures; the night scene does.

### The speaker review: 10 of 14 wrong, and 9 of those are one mistake

Run on the pilot's 18 `low` entries. 14 judged, 4 left unjudged as genuinely
unreadable — which is the honest outcome, not a gap.

| | |
|---|---|
| queued | 18 |
| reviewed | 14 |
| model wrong | **10 (71%)** |

The rate is not the finding. The **shape** is:

```
079 g4,g5,g6   Huey, Dewey, Louie  ->  nephews     (night scene)
080 g0,g1,g2   Huey, Dewey, Louie  ->  nephews     (helmets)
083 g5,g6,g7   Huey, Dewey, Louie  ->  nephews     (helmets)
084 g8         Dewey               ->  Huey
```

**Nine of the ten are the same error, in three clean triples.** Only 084 g8 is a
real misidentification. The pass is not bad at seeing — it fails to fall back to
`nephews` when it cannot read a cap.

And it knew. The four left unjudged carry `vision_note`s that state the ambiguity
outright — *"tail ambiguous between the red- and blue-capped nephews"*, *"the
middle and right caps BOTH read…"*. It wrote down that it could not tell, and
named a specific nephew anyway. The rule was already in `roster.txt`.

**So the fix is enforcement, not rewording.** `vision_apply` now refuses an
individual nephew at `low` confidence: if the cap cannot be read the answer is
`nephews`, and that is not a low-confidence call. The rule is rendered into
`roster.txt` from the same constant, so the pass is told it and cannot violate
it — a rule the model states and then breaks needs a validator, not better prose.

**Keep queueing `low`; do not move the threshold.** A 71% error rate more than
earns the review. But this one rule would have prevented 9 of these 10, which
matters most at scale: a volume's ~370 low-confidence entries was the workload
concern, and if that population is mostly this pattern it largely evaporates.

### Bonus: the `type` field mis-labels speech as thought

The art distinguishes true thought clouds (scalloped, bubble trail) from
pointed-tail speech balloons. **3 of the 5 groups typed `thought` in the pilot are
wrong** (079 g16, 080 g6, 080 g7); 081 g3 and 083 g12 are correct. Recorded in
`vision_note` only — nothing was changed.

---

## The next run: a title mix, not a volume

Because the unit is the story, the next run tests the axis that actually varies
— **story length** — rather than 205 pages of one volume's sameness.

The titles were **chosen by the queries, not the other way round**: 63 of the 97
in [`retrieval-queries.md`](retrieval-queries.md) name a specific story, and
those stories are the run. Picking titles first and hoping the queries reached
them would have been the wrong order.

| title | vol | pages | queries | DB cast | run |
|---|---|---:|---:|---|---|
| **Sheriff of Bullet Valley** | 6 | 144-175 (32) | 27 | none | **trial 3** |
| **Billions to Sneeze At** | 10 | 044-053 (10) | ~14 | none | **trial 2** |
| **Plenty of Pets** | 7 | 199-208 (10) | ~13 | none | **trial 4** |
| **Roscoe the Robot** | 20 | 175-178 (4) | ~13 | none | **trial 1** |
| **The Big Bin on Killmotor Hill** | 11 | 038-047 (10) | 24 | **The Beagle Boys** | **trial 5** |

**~66 pages.** 4 to 32 is a wider length spread than the original plan had, and
Roscoe is a deliberate density stress test: 13 queries against 4 pages, roughly
2.5 objects per page.

The fifth title is not a spare. The other four carry **no DB-tagged cast at
all**, so `story_characters`, the aliasing and the nested-group flattening would
have gone completely untested by the run meant to prove them. Big Bin is the only
unit exercising the closed set end to end.

Four of the five also carry `THINGS` anchors — `313`, `HDL driving car` and
`cigarettes` on Sheriff, `sulphuric acid` on Big Bin — so the naming-anchor path
gets covered too.

**The one-pager batch unit was dropped as impossible**, not as unnecessary — see
Open threads. The question it was for, whether a union of unrelated casts
degrades the closed set, can be tested separately and cheaply with `--volume`
and `--pages` across a title boundary, which exercises the same warning path.

Five things to measure, in this order:

1. **Correction rate** against the pilot's **1.5%**. Read this first: materially
   higher means the pass is hallucinating, not that the story is dirty.
2. **Retrieval hit rate** on the pre-committed queries, each miss split into
   *not recorded* vs *not retrieved*. The pass/fail gate.
3. **Low-confidence speaker error rate.** Decides whether `low` is worth queueing
   at corpus scale, or whether the threshold should move.
4. **Off-vocabulary rate** for `characters` and `setting`, and which `other:`
   names recur enough to promote.
5. **Cost per title** in sessions and wall-clock. This is what makes the
   remaining ~5,500 pages an arithmetic decision rather than a guess, and none of
   the other four substitute for it.

`visible_text` has no baseline, so establishing its yield is itself an output.

---

## Trial results 1 — Roscoe the Robot, vol 20 pages 175-178

Run 2026-08-02. 4 pages, 32 panels, 44 groups. First unit of the five-title trial.

| | |
|---|---|
| `vision_text_ok: false` | 1 (**2.3%**, against the pilot's 1.5%) |
| emphasized words | 20 across 44 groups (**45%**, against the pilot's 3.7%) |
| confidence | high 44 / medium 0 / low 0 |
| `cap_colour` non-null | 0 |

**The correction rate holds.** One in 44, and it is a real defect: `175 g12`
`ELECTRIC RULES` → `ELECTRIC BULBS`, hand-scrawled on the crate the Little Helper
is loading a spare bulb into. Queued in `~/barks-vision/roscoe-review.txt`. At
2.3% against 1.5% on a 44-group sample the pass is reading, not inventing.

### Bold density is a property of the series, not of the corpus

20 emphasized words where the pilot found 5 — twelve times the rate. The Gyro Gearloose
stories letter emphasis constantly; *The Victory Garden* (1943) almost never
does. **So the pilot's 5 is not a corpus baseline**, and neither is this. Two of
the twenty are single characters — the lone `I` in "this is where **I** wanted to
hide" — which is the case a stored offset would have handled worst, and one
reason the spans were retired the same day.

### Measurement 3 is untestable on this title, and that is structural

All 44 calls are `high`; `--queue-speakers` wrote **zero** entries. Gyro is the
only duck in the story, so there is no cap to read and no nephew to confuse. A
one-lead story cannot exercise the low-confidence path at all — the remaining
four titles have to carry that measurement alone.

### Retrieval: 15 of 16, but only 11 the vision pass earned

Scored by keyword search over the capture records, so every hit is attributable
to a field. 12 Roscoe-specific queries plus 4 that any title can answer (#16,
#30, #43, #96).

*Reproducible since trial 2:* `barks-ocr-retrieval-score --validate` re-runs this
exact scoring and fails if it no longer comes out 15 / 1 / #93. It credits #16 to
the speech layer rather than to capture, so it reports 10 capture-only where the
count below says 11 — 176's dialogue calls Roscoe "a strong, alert HELPER", which
a lexical matcher cannot tell from the Little Helper.

| | |
|---|---|
| hit | 15 |
| miss — *not retrieved* | 1 (#93) |
| miss — *not recorded* | 1 (#85, on the first pass) |
| false positives | 0 |

**Four of the fifteen are not the vision pass's to claim.** #84 *a robot*, #87 *a
fly swatter*, #90 *a fly* and #96 *an alleyway* are all answerable from the OCR
speech alone — the dialogue says "a robot that can act", "gone after the
swatter", "swat that fly", "the terrible footpad's alley". Capture found them
too, but they discriminate nothing. **The honest figure is 11 capture-only hits.**

The two misses want opposite fixes, which is the split working:

- **#93 *a character being hit* — not retrieved.** 176 panel 4 is recorded, in
  two fields: "swats the fly on Gyro's face with a SPLAT, knocking Gyro off his
  feet". Keyword search cannot get from *hit* to *swats* and *knocking off his
  feet*; an embedding retriever would. The schema is fine. **This is the single
  strongest argument in the trial so far for semantic rather than lexical
  retrieval** — nothing about the record is deficient.
- **#85 *a character being electrocuted* — not recorded.** 175 panel 3 has the
  Little Helper grabbing the live wire out of Roscoe's open chest, limbs flung
  out, bulb head blazing, lightning jagging in every direction. The first pass
  wrote the panel's dialogue and its bold span and **did not mention the gag at
  all** — it is background business in a panel whose balloon is about something
  else. Re-reading the panel with the query in hand found it immediately.

That second miss is the one to learn from, and it is not a schema failure: three
sentences and eleven object slots had room. It is an **attention** failure —
the pass followed the dialogue and under-read the silent business around it.
Whatever the fix is (a prompt that asks explicitly what else is happening in each
panel, or a second reading pass), it is not another field.

### Free text drifts inside a single title, let alone across the corpus

Query #92 *a legless chair* hit page 176 and missed 175 — the same blue chair,
written `legless blue deck chair` on one page and `blue folding chair` on the
next, four pages apart in one sitting. The census catches this across stories;
nothing catches it within one. Both are now the same string.

The same problem, caught in time: the holdup man of 177 is drawn in full on 178
as a workman with a wrench. Recording him as `other:the thug` on one page and
`other:the workman` on the next would have made **one character into two**. He is
`other:the workman` on both, and the silhouette gag is recorded in
`vision_note` and `panels_of_note` instead.

### Off-vocabulary rate is near-total, and mostly unavoidable

`characters`: 6 distinct values, of which **1** is on the roster. The other five
— `other:Roscoe the robot`, `other:Gyro's Little Helper`, `other:the workman`,
`other:the postman`, `other:the kitten` — are all free text, and the database
tags this story with no cast at all. A Gyro Gearloose story simply has an
off-roster cast; this is what the closed set cannot cover.

`setting`: **0 of 4 pages** used a closed-vocabulary value. Both are `other:`
(`other:Gyro's workshop`, `other:the footpad's alley`), because `indoors` and
`street` are true but carry no retrievable information, and query #96 wanted the
alley by name.

**`other:Gyro's Little Helper` is the promotion candidate**, and a better one than
`other:crows`: it recurs across every Gyro story in the corpus rather than
seventeen times in one. Query #16 asks for it by name.

### `visible_text` yield on this title: zero net new lettering

13 strings captured — crate labels, the gate sign, two letters, the title logo,
and the painted sound effects. **Every one already exists as an OCR group.** The
OCR pass caught all of the non-speech lettering on these four pages, so
`visible_text` duplicated the speech layer and added nothing. The pilot's
invisible-seeds poster shows that is not always true, but this title says the
field's yield is uneven and cannot be assumed. Worth re-measuring per title
rather than declaring it settled either way.

### `type` is wrong the other way round here

The pilot found 3 of 5 `thought`-typed groups were really speech. Roscoe has the
mirror-image defect and far more of it: **12 of 44 groups (27%) are drawn as
thought clouds and typed `dialogue`** — and `177 g4` is typed `narration` while
the art gives it a bubble trail running down to Gyro's head. The story's premise
is a machine that reads thoughts, so almost every balloon in it is a thought.
Recorded in `vision_note` only; nothing was changed.

`177 g3` is a different defect: one group holding **two physically separate
letters** lying at opposite corners of the panel. Both readings are correct, so
it is not a text correction, but it should be two groups.

### Cost

**One session, ~45 minutes wall-clock**, 40 images read (4 page overviews, 32
panel crops, 4 enlargements to settle small lettering). That includes reading
both design docs and the `vision_apply` source once, which the next title will
not repeat.

Do not extrapolate ~11 min/page to the corpus from a 4-page sample — the fixed
cost dominates at this size, and Roscoe was deliberately chosen as the densest
title in the trial. The 32-page *Sheriff of Bullet Valley* is the unit that will
actually answer measurement 5.

---

## Trial results 2 — Billions to Sneeze At, vol 10 pages 044-053

Run 2026-08-02. 10 pages, 78 panels, 136 groups. Second unit of the five-title
trial, and 2.5× the size of the first.

| | |
|---|---|
| `vision_text_ok: false` | **0** (against Roscoe's 2.3% and the pilot's 1.5%) |
| emphasized runs | 71 across 53 of 136 groups (**39%** of groups) |
| confidence | high 136 / medium 0 / low 0 |
| `cap_colour` non-null | 0 |

### A zero correction rate is a result, not a clean bill of health

136 groups and nothing to correct. Read against the pilot's 1.5% and Roscoe's
2.3% that is reassuring about hallucination, which is what measurement 1 is for.
It is **not** evidence the pass reads better than it did — the sample is one
story, and vol 10 may simply be cleaner than vol 20.

Two disagreements with the art were found and deliberately **not** raised as
corrections, because counting them would have meant comparing against a
different rule than Roscoe's:

- `050 g4`, the framed office motto, is lettered in mixed case in the art
  (*"A penny SAVED is a penny EARNED!"*) and stored in caps. Every group in the
  corpus is stored in caps; flagging this would flag the transcription
  convention, corpus-wide, on every page that has a mixed-case sign.
- `052 g4` stores a plain hyphen where the art letters a dash. Punctuation
  normalisation is `string_replacer`'s job, not the vision pass's.

Roscoe's one correction was a **word** misread (`ELECTRIC RULES` → `ELECTRIC
BULBS`). Holding the rate to word-level misreadings keeps the two numbers
measuring the same thing. Both observations are recorded in `vision_note`.

### Bold density: a third data point, and still no baseline

39% of groups carry emphasis against Roscoe's 45% and the pilot's 3.7%. Roscoe
argued that bold density is a property of the series; this widens that to
**a property of the era**. Both 1951-52 stories letter emphasis constantly and the
1943 *Victory Garden* almost never does. Do not treat any of the three as a
corpus baseline.

One emphasis case the schema had no kind for: `050 g8` is a single balloon
reading "MONEY — AH-CHOO!" where the sneeze is lettered several times the size
of the rest. That is unmistakably the emphasis, but it is *size*, not weight or
slant. It is marked `[b]`, which is the least-wrong of the two available kinds
and is noted in place. `053 g10` needed the opposite care — three repetitions of
"OH, SO?" growing in weight, where a substring replace would have tagged all
three.

### Measurement 3 is untestable again, for the opposite reason

Zero `low`-confidence calls, so `--queue-speakers` wrote **zero** entries — the
same outcome as Roscoe, from a different cause. Roscoe had no nephews to confuse;
this story has all three, but Barks draws them **capless throughout**. Every
nephew line is `nephews` at `high`, which is the correct answer and is exactly
what the collective rule asks for.

`cap_colour` is null on all 136 groups for the same reason. **Two titles in, the
low-confidence path has not been exercised once**, and the trial has three titles
left to do it. That is now the measurement most at risk of going unanswered.

### Retrieval: 12 of 18, and the scorer is now a tool

`barks-ocr-retrieval-score` replaces trial 1's throwaway script. Its `--validate`
mode re-scores Roscoe and **fails if the result is not 15 hits, 1 miss, #93** —
so the two titles' numbers are comparable by construction rather than by hope.
It is deliberately lexical: no stemmer, no embeddings.

| | 14 committed queries | 4 cross-title | total |
|---|---:|---:|---:|
| hit | 9 | 3 | **12** |
| miss | 5 | 1 | **6** |
| false positives | 0 | 1 | **1** |

Nine of the twelve hits are capture-only; three (#11, #36, #40) the speech layer
answers too. `panels_of_note` carried seven hits, `objects` six, `beats` five.

**Four of the five committed misses are *not retrieved*, not *not recorded*** —
and that lopsidedness is the finding:

- **#38 *a character that is sneezing*.** The word "sneeze"/"sneezes" is in the
  records of four separate pages. The query says "sneezing". A prefix match gets
  from `alley` to `alleyway` but not from `sneeze` to `sneezing`, so **the story
  called *Billions to Sneeze At* misses the query "a character that is
  sneezing".** Nothing is wrong with the schema, the capture or the reading.
- **#33 *sick*** is recorded as "does not feel well" and "allergic to money".
- **#34 *sad*** is recorded as "in tears", "crying", "sobbing", "cry in bed".
- **#26** is the trial's first **false positive**: 045 is returned for "an
  establishing shot with no characters in frame" because its `panels_of_note`
  says "establishing shot" — and Scrooge is in the frame. A lexical retriever
  cannot express the negation, and the query is built entirely out of one.

Only two misses argue for a schema change:

- **#35 *smiling* — not recorded.** Nowhere in the ten pages. Probably correct:
  Barks characters smile on most panels, so the tag would return most pages and
  discriminate nothing. This is the #34 objection, arriving on a different query.
- **#46 *a sound effect* — not recorded as a category.** `visible_text` holds
  `SMACK!`, `KA-CHOO!`, `AH-CHOO!` as strings but nothing says they *are* sound
  effects, so the category query cannot reach them. `visible_text` is untyped by
  design; this is the first query to want it typed. Roscoe has the same shape
  (`BZZT`, `SPLAT`) and simply never ran the query.

### Emotion: it fails on retrieval, not on discrimination

The query set put emotion on trial and named #34 *sad* the deliberate test case,
to be scored by **what fraction of the trial's pages it returns**. The answer is
**zero of ten** — and #37 *crying* returns two of ten, the right two.

So the objection the doc anticipated is not the one that bit. Emotion is not
returning everything and discriminating nothing; it is unreachable, because the
records use the word Barks draws (`crying`, `in tears`, `sobbing`) and the query
uses the word a reader thinks in (`sad`). **The emotion field's fate is a
vocabulary question, not a discrimination one**, and lexical retrieval is what
decides it. Nothing here argues for adding an emotion field; #37 already works
without one, because "crying" is a thing you can see.

### `setting` is one value per page, and Barks pages have two

Four of the ten pages cut between two locations mid-page — 050 spends five
panels in Scrooge's office and three at the cave, 052 splits four and four. The
schema takes one value, so on each of those pages **one real setting is not
recorded as a setting**. It survives in `objects`, `beats` and `panels_of_note`,
which is why #41 *a cave* still hits both 050 and 052, but the field itself is
lossy on 40% of this title's pages. Worth watching on *Sheriff of Bullet
Valley*, which is long enough to say whether this is a Barks structure or a
ten-page coincidence.

### Off-vocabulary rate

`characters`: 7 distinct values, **3 on the roster** (Donald, Scrooge,
`nephews`) covering 21 of 28 page-appearances. The four `other:` names are the
story's one-offs — `other:the washerwoman`, `other:the doctor`,
`other:Mr. O'Dope`, `other:Miss Lily de la Field` — and the database tags this
story with no cast at all, so the closed set could not have covered them. Better
than Roscoe's 1-of-6, and for a structural reason: this is a Donald/Scrooge story
where the leads *are* the roster.

`setting`: **2 of 10 pages** used a closed-vocabulary value (`street` twice).
The other eight are `other:`, all naming a specific place. Same finding as
Roscoe, on 2.5× the sample: the closed vocabulary is true but carries no
retrievable information, so the pass reaches past it every time.

`barks-ocr-speaker-census --volume 10` reports **no variant spellings and
nothing off-roster**. No promotion candidate: the most-used free-form name is at
5, half the threshold, and all four are single-story one-offs.

### `visible_text`: 2 net new strings in 18

18 strings captured, and **16 already exist as OCR groups**. The two that do not:

- `049` — the `1¢` on the gumball machine
- `050` — the `M.D.` on the doctor's bag

Both are small lettering on a prop, which is the shape of what OCR misses.
Roscoe's yield was zero of 13, the pilot's was the invisible-seeds poster. Three
titles in, `visible_text` yields **little but not nothing**, and what it yields
is consistently the same kind of thing. Do not declare it settled either way yet.

### The pass under-reads silent background business — not seen here

Roscoe's #85 raised this as a hypothesis: a full-panel electrocution gag missed
because the balloon was about something else. **It did not recur on this title.**
The silent business here — the halo on 051 p8 and 052 p4, the full-silhouette
panel on 051 p7, the washerwoman face down on 047 p5 — was all caught on the
first read, and #42 and #43 hit because of it. One recurrence, one
non-recurrence; the hypothesis stays open rather than confirmed or dropped.

### `type` is wrong the same way as Roscoe, at a fifth the rate

**4 of 136 groups (2.9%) are drawn as thought clouds and typed `dialogue`** —
`045 g1`, `047 g11`, `048 g10`, `048 g11`. Every group actually typed `thought`
on this title is correct, which is the reverse of the pilot. Roscoe's 27% was
inflated by its premise (a machine that reads thoughts); 2.9% is probably nearer
the corpus rate. Recorded in `vision_note` only; nothing was changed.

`046 g2` is genuinely ambiguous — a small scalloped cloud with drool drips and no
bubble trail, beside Scrooge sniffing coins — and is left as typed.

**A panel-number defect, which is new:** `048 g3` and `g4` are stored as
`panel_num 1` but belong to panel 3, the coin-kissing close-up. Panel 3 has no
groups at all. It is visible in the prep output as well as the art — their text
boxes get unioned into panel 1's crop, which is why that crop reaches down two
rows. The vision result schema has no `panel_num` field, so it is recorded in
`vision_note`; the kivy editor is where it gets fixed.

`053 g9` and `g15` each cover a whole scatter of separate `BILL` sheets under one
group. Unlike Roscoe's `177 g3` this is defensible — they are one drift of paper,
not two letters at opposite corners of a panel.

### Cost

**One session, ~90 minutes wall-clock**, 98 images read (10 page overviews, 88
panel crops, no enlargements needed). No design-doc reading beyond this document
and `retrieval-queries.md`.

That is **~9 min/page against Roscoe's ~11**, on 2.5× the pages — so the fixed
cost is visibly amortising, but not fast. The 32-page *Sheriff of Bullet Valley*
is still the unit that answers measurement 5.

## Trial results 3 — Sheriff of Bullet Valley, vol 6 pages 144-175

Run 2026-08-02. 32 pages, 254 panels, 407 groups. Third unit of the five-title
trial, and 3.2× the size of the second. **This is the measurement-5 title.**

| | |
|---|---|
| `vision_text_ok: false` | **0** (against Roscoe's 2.3%, Billions' 0, the pilot's 1.5%) |
| emphasis runs | 154 across 126 of 407 groups (**31%** of groups) |
| confidence | high 393 / medium 12 / **low 2** |
| `cap_colour` non-null | 37 (blue 19, green 9, red 9) |
| `visible_text` strings | 62 |

### Cost — measurement 5, which is what this title was for

**One session, 52 minutes wall-clock** (16:07 to 16:59), 297 images read: 32 page
overviews, all 254 panel crops, and 11 enlargements. No design-doc reading beyond
this document and `retrieval-queries.md`.

That is **~1.6 min/page against Billions' ~9 and Roscoe's ~11**, on 3.2× and 8×
the pages. The fixed cost has not merely amortised, it has stopped mattering.

**Do not read that as the pass getting cleverer.** The whole difference is
batching: a page is one message containing `groups.json` and ten `Read` calls
issued together, and the per-page cost is then dominated by one model turn rather
than by ten round trips. Roscoe's 4 pages and Billions' 10 could not amortise a
fixed cost they were too small to hide; 32 pages can. The honest projection is
that **the remaining ~5,500 pages are on the order of 150 hours of session time at
this rate**, and that this is now a token-cost question rather than a wall-clock
one — which is a different decision from the one measurement 5 was set up to
answer, and a much easier one.

The 11 enlargements are the real per-page variable, and they were spent almost
entirely on cap colours (below) rather than on lettering.

### Correction rate: zero again, and the rule earned its keep

407 groups and nothing to correct. Two titles running, on a sample four times the
size. Read with Roscoe's 2.3% and the pilot's 1.5%, measurement 1 says the pass
is reading rather than inventing, and that is all it says.

Holding to Billions' **word-level-misreadings-only** rule mattered more here than
on either previous title, because a 32-page story surfaces far more near-misses.
None of the following was counted, and all are recorded in `vision_note`:

- **Film titles in single quotes** where the stored text has double — 145 g6 and
  g8, 146 g2, 149 g5, 154 g6. Punctuation normalisation, `string_replacer`'s job.
  Not uniform in the art either: 169 g9, 172 g0 and 175 g14 *are* double-quoted
  and match.
- **`MCQUIRT` vs `McQUIRT`.** The art letters the villain's name with a small c
  throughout; the OCR stored it capitalised on 149, 150 and 169 and preserved the
  small c on 170. One name, two transcriptions, inside one story — a case
  difference, so the same rule that spared Billions' mixed-case office motto
  spares it.
- **An em-dash stored where the art letters a hyphen** (156 g4) — the mirror of
  Billions' 052 g4.
- **Drawn brand devices.** The Diamond Ranch gate sign is stored three different
  ways: bare `RANCH` on 146, `◇ RANCH` (U+25C7) on 150 and 154, `◊ RANCH`
  (U+25CA) on 157. Each matches its own art; the inconsistency is corpus-wide, not
  a misreading.
- **Music notes** drawn inside balloons on 171 g1 and 172 g7, not transcribed.
  Correctly — they are a device, not lettering.

**One thing that is a genuine defect but not a text correction**: `172 panel 5`
letters `FZZT!` along the grenade's flight path and **has no OCR group at all**.
The pass caught it in `visible_text`. That is a missing group rather than a wrong
one, so it does not touch the correction rate — but it is the clearest single
demonstration in three titles that `visible_text` is doing work the OCR layer
missed.

### Measurement 3: 2 low-confidence calls in 407 — and the reason is the fix

`--queue-speakers` wrote **2 entries**, both on 168: `g10` and `g11`, two adult
figures in a night panel drawn in flat black silhouette with no hat, no
neckerchief and no star to tell a posseman from Old Jim. They are genuinely
unreadable, which is why they are `low`.

**Two entries is not a population you can compute an error rate from**, and I am
not going to dress it up as one. Measurement 3 has now gone three titles without
a real answer, and this title had the full cast, 32 pages and readable caps.

But it did not fail for Roscoe's reason (one lead, no caps) or Billions' reason
(nephews drawn capless throughout). It failed for a **structural** reason that is
worth more than the number would have been:

> The collective rule is what destroys the low-confidence population. Every time
> the art would not say which nephew was speaking, the honest answer was
> `nephews` at **high** confidence — not an individual at `low`. The pilot's 18
> low-confidence entries existed precisely *because* the pass was naming
> individuals it could not see.

So the right reading is that **the rule added after the pilot works, and its
success is measured by the queue being empty rather than by the queue being
accurate.** A trial designed to measure the error rate of a bad behaviour cannot
measure it once the behaviour is fixed.

#### The `low,medium` run: 14 entries, and 9 of them are adults

```bash
barks-ocr-vision-apply --out-dir ~/barks-vision/sheriff-of-bullet-valley \
    --queue-speakers ~/barks-vision/sheriff-speakers-low-medium.txt \
    --speaker-confidences low,medium
```

14 entries — the 2 lows plus all 12 mediums. The original low-only queue is kept
separately so the population that *was* low before review survives, as the editor
section requires. The 14 split three ways:

| | | |
|---|---:|---|
| **adult identity, two candidates and no colour to separate them** | **8** | 151 g9, 164 g4, 164 g9, 168 g2, g3, g5, g10, g11 |
| nephew identity, marginal hue or imprecise tail | 5 | 144 g12, 159 g5, 161 g9, 161 g10, 162 g13 |
| speaker placed by what the line says, not by the art | 1 | 165 g0 |

**This is the finding the low-only queue was too small to show.** The pilot's
entire low-confidence population was nephews; Sheriff's is **9 of 14 adults**
(counting 165 g0, which is also an adults-vs-jeep question). The cause is
structural and new to this title: the story carries four similar dog-faced men —
the sheriff, Old Jim Diamond, possemen and Double X riders — who are told apart
**only by hat and shirt colour**, and Barks repeatedly removes exactly that
evidence:

- **168 alone contributes 5 of the 14.** It is the story's one night-and-indoors
  page: the men are drawn hatless at the desk and in the rocking chair, then in
  flat black silhouette outside. Same mechanism as the pilot's night scene on 079,
  applied to adults instead of nephews.
- **168 g3 is a colourist swap**, not a reading failure: the man in the green
  rocking chair wears a blue shirt and red trousers in one panel and a red shirt
  and blue trousers in the next. Either his colours were swapped or they are two
  different men, and the art will not say which.
- **164 g4 and g9** fail the same way at distance — two riders at the head of a
  posse whose hats both print teal, and a rider in a green hat wearing the
  sheriff's yellow shirt.

**There is no adult equivalent of the two things that make nephews tractable.**
`cap_colour` records the evidence behind a nephew call and makes it reversible;
nothing records "identified by hat colour" for an adult. And `nephews` is an
honest collective that loses almost nothing, where the adult fallback is
`unknown`, which loses everything. That asymmetry — not the nephew rule — is
where the remaining speaker risk in the corpus lives, and a story with a large
adult supporting cast is where it will show up.

#### Trial 4's review, for comparison: 2 corrections in 6

*Plenty of Pets* was reviewed on 2026-08-03 with the new Confirm as is button, so
its denominator is the first that can be read off disk: **6 queued, 6 stamped
`speaker_reviewed`, 2 wrong (33%)** — `199 g12` Huey→**Dewey** and `204 g1`
Louie→**Huey**.

**Both are balloon-tail errors, not colour errors**, which makes them a *different*
class from `168 g5` below rather than a repeat of it. In each the pass picked the
wrong figure in a multi-nephew panel and then read that figure's cap correctly. So
`168 g5` stays the trial's only confirmed instance of costume colour overriding
better evidence, and the adult-identity risk described above is still supported by
exactly one case. See trial 4 for the full account, including that both panels had
been enlarged specifically to trace those tails and both traces are recorded in
confident language and wrong.

#### The review: 1 correction in 14 — against the pilot's 10 in 14

GLK reviewed the queue and made **one** correction:

```
168 g5   other:Old Jim Diamond  ->  other:posseman
```

| | pilot | Sheriff |
|---|---:|---:|
| queued | 18 | 14 |
| reviewed | 14 | 14 |
| model wrong | **10 (71%)** | **1 (7%)** |

**Measurement 3 finally has a number**, and it is a tenth of the pilot's. That is
the collective rule and the nine-of-ten error pattern it was written to prevent,
measured on a title with the full cast, readable caps and 32 pages.

**One caveat on the 13 confirmations, and it is a tooling gap rather than a
doubt.** Only the corrected group carries `speaker_reviewed` on disk. The editor
writes nothing unless a roster entry is picked and saved, so agreeing with a call
and moving on is **indistinguishable from never having looked at it**. The 13
confirmations therefore rest on GLK's report, not on the data. **Closed
2026-08-03** by the editor's Confirm as is button, which was added before the
next queue was reviewed; these 13 are deliberately not retrofitted.

**The one error is exactly the class this section predicted.** 168 g5 is the man
in the green rocking chair, and the pass gave him to Old Jim because his red shirt
and blue neckerchief in panel 4 matched the hatless figure at the desk in panel 2.
He is a posseman — the *same* man as 168 g3, which the pass had already called a
posseman after noticing his shirt and trousers swap colour between the two panels.
So the pass saw the anomaly, recorded it, and then let costume colour override it
one panel later. Adult-identity-by-costume-colour was named above as the residual
risk; it is also, on this title, the *only* thing the pass got wrong.

That the single error sits on the one night-and-indoors page, in the one group
where two panels disagree about a man's clothes, is the strongest available
argument for the `identified_by` idea in Open threads: had the call recorded
*what evidence identified him*, the contradiction with g3 would have been
mechanical to catch instead of needing a human eye.

### The colourist breaks the cap convention on five pages

This is the finding that forced the rule above. Barks — or the colourist — gives
**two nephews the same colour in one panel** on 159 p7, 161 p4, 162 p1, 163 p1 and
163 p4, and twice paints a cap **orange-gold**, which is not a roster colour at
all (161 p4, 162 p1). 168 and 175 draw the nephews **bare-headed indoors**, as
Billions did throughout.

The rule adopted and applied consistently: **if two nephews in one panel show the
same colour, or a cap shows a non-roster colour, colour is not evidence in that
panel** — the speaker is `nephews` even when the balloon tail lands unambiguously
on one of them. Where all three are separable (158, 160 p6, 161 p8, 162 p7, 163
p2, 167) the individual name is recorded with its `cap_colour`.

That yielded 37 non-null cap colours — **the first title in the trial to produce
any at all**, Roscoe and Billions having produced zero each — and a 19/9/9
blue/green/red split that is itself worth noting: blue is twice as often readable
as either other colour.

### Retrieval: 26 of 30, and every miss is a *retrieval* miss

`barks-ocr-retrieval-score --validate` was run **first** and reproduced Roscoe at
15 / 1 / #93, so these numbers are comparable by construction. It still validates
after the Sheriff query set was added.

27 of the queries in `retrieval-queries.md` name this title (#22, #29, #31 and the
whole run #59-#82); three more (#30, #43, #83) are cross-title.

| | |
|---|---:|
| hit | **26** |
| miss | **4** (#29, #70, #76, #79) |
| capture-only hits | 9 |
| also answerable from speech | 17 |
| false positives | 0 |

**Only 9 of the 26 hits are the vision pass's to claim.** That is a far worse
ratio than Roscoe's 11-of-15 or Billions' 9-of-12, and the reason is structural:
this story *talks about* its own props constantly — the brands, the guns, the
steers, the ranch, the jeep are all named in dialogue — so the speech layer
reaches them without capture's help. A western is the worst case for
demonstrating that page capture earns its place.

The queries that capture genuinely won are the visual ones: #30 splash, #31 the
nephews driving, #43 silhouettes, #62 river/creek, #66 cutting the wire fence,
#71 rifle, #73 sleeping, #80 empty handgun, #82 smoking a pipe.

#### Four misses, and **not one of them is "not recorded"**

This is the sharpest result in the trial so far. Every expected page for every
missed query has the thing written down.

- **#29 *a chase or pursuit across several panels* — a new failure mode.** 164
  ("Blacksnake gives chase") and 174 ("Donald chases Blacksnake") both score the
  **maximum** and are still not returned: **nine pages tie at the top score, and
  `TOP_BAND = 3` truncates the tie alphabetically** to 144, 155, 157. Nothing is
  wrong with the record, the schema or even the matcher. This miss is caused by
  the **length of the title** — 32 pages generate ties that 4 and 10 pages could
  not — and it will get worse, not better, at corpus scale.
- **#70 *a character hiding* — the sneezing bug again, verbatim.** 159 records
  "hide to listen" and "hidden under one haystack". `hide` is not a prefix of
  `hiding` (the silent *e* is dropped) and `hidden` is two edits away, so neither
  matches. This is exactly Billions' `sneeze` vs `sneezing`, in a story where
  hiding is a plot point on three pages. Worse, 165 *did* score — by
  `_within_one_edit` matching **`hiding` to `riding`**, which in a western is on
  nearly every page. The fuzzy matcher bought a false positive and still missed.
- **#76 *a character feeling pain* — recorded as depiction, never as concept.**
  Zero of the five expected pages match. The records say `YEOWCH!`, `YEEK!`,
  `EE-YOW!`, "seeing stars", and "a small blue star drawn at his backside where a
  bullet stung him". All faithful; none says *pain* or *hurt*. This is the third
  instance of Billions' finding (sick → "does not feel well", sad → "in tears")
  and it is now the trial's most repeated result: **the record uses the word Barks
  draws and the query uses the word a reader thinks in.**
- **#79 *a character's pants falling down* — capture drifted away from the
  comic's own vocabulary.** 173 and 174 record "his blue trousers drop round his
  ankles" and the object `blue trousers round the ankles`. The query says *pants*
  — **and so does the comic**, in 173 g7: "HE FILLED MY **PANTS** SO FULL OF LEAD
  MY BELT BUCKLE BROKE!" The speech layer would have answered this query and
  capture did not, because the pass wrote British *trousers* over the source's
  *pants*. Roscoe found free text drifting **within** a title; this is free text
  drifting **away from the source text**, which is a new and more avoidable class.
  The lesson is concrete: **prefer the comic's own word for a thing it names.**

So the split that "makes the trial answer anything" comes out **4 not-retrieved,
0 not-recorded**. Roscoe was 1 and 1, Billions was 4 and 2. Three titles in, the
schema has stopped generating misses.

### `visible_text`: 7 net new in 62, the best yield of the three titles

62 strings captured, **7 of which exist nowhere in the OCR groups**:

| page | string | what it is |
|---|---|---|
| 144 | `313` | the licence plate on the car, unread on this page |
| 145 | `REWARD` | a small mugshot poster on the sheriff's office wall |
| 146 | `REWARD` | the same poster in a different panel |
| 146 | `LAST CHANCE` | a saloon sign at the edge of frame |
| 148 | `XX` | the Double X brand on the horse and the saddle |
| 160 | `XX` | the Double X brands on the driven herd |
| 172 | `FZZT!` | the hand grenade's fuse — a whole sound effect with no group |

Against Roscoe's **0 of 13** and Billions' **2 of 18**, this is 11% and the field's
best showing yet. The shape is consistent with Billions' finding — small lettering
on a prop (`1¢`, `M.D.`, and now a licence plate and two cattle brands) — with one
new category: **a sound effect the OCR pass missed entirely**. Four titles in
(counting the pilot's invisible-seeds poster), `visible_text` yields little but
reliably not nothing, and the yield is rising with page count rather than being
uniform per page.

### Off-vocabulary rate

`characters`: **13 distinct values, 5 of them on the roster** (Donald, `nephews`,
Huey, Dewey, Louie), covering 63 of 126 page-appearances — an even 50/50 split
with the eight `other:` names, and the best roster coverage of the three titles.
The eight are `Blacksnake McQuirt`, `Old Jim Diamond`, `the sheriff`,
`Double X rider`, `posseman`, `townsman`, `cowboy` and `Donald's horse`.

**The database tags this story with no cast at all**, yet it has two substantial
named characters who carry the whole plot. Three titles in, `story_cast` has been
empty every time, and the closed-set machinery it was built for is still
completely untested — Big Bin remains the only unit that will exercise it.
(It did, on 2026-08-03: see trial 5, where the Beagle Boys come back from the
closed set and roster coverage reaches 98% of page-appearances.)

`setting`: **0 of 32 pages used a closed-vocabulary value.** Every one is
`other:`, across six distinct places (`badlands` 17, `the Diamond Ranch` 7,
`a western town street` 3, `the sheriff's office` 2, `the canyon` 2,
`the Double X camp` 1). Roscoe was 0 of 4 and Billions 2 of 10. The closed
vocabulary is now 0-for-3 on being worth reaching for.

`barks-ocr-speaker-census --volume 6` reports **no variant spellings and nothing
off-roster** — the naming discipline held across 32 pages. It names four
promotion candidates over the threshold of 10: `Blacksnake McQuirt` (54),
`Old Jim Diamond` (36), `the sheriff` (19), `Double X rider` (12).

**Three of those four should not be promoted**, for exactly the reason
`other:crows` should not: they are single-story names, and the threshold was meant
for names recurring *across* stories. **`other:the sheriff` is different** — it is
a *role*, not a name, and a town sheriff recurs across the corpus. That is the
first real promotion candidate the census has produced, and it argues the census
should distinguish roles from names as well as weighting by title count.

#### How the names were kept from splitting

Blacksnake McQuirt is not named in the art until 149 and Old Jim not until 150,
but both appear from 147. Rather than invent a provisional name and rename later
— Roscoe's `other:the thug` / `other:the workman` failure — **the whole title's
`groups.json` was grepped for capitalised names before page 147 was read.** It
cost one command and removed the failure mode entirely. Worth doing by default —
and since trial 5 it is a tool, `barks-ocr-name-grep`, with the two passes that
run turned out to need. See Open threads.

### `setting` is one value per page, and this title says Billions was right

Billions found 4 of 10 pages cutting between two locations. Sheriff does it on
**at least 8 of 32** — 144 (badlands then town), 145 (office then boardwalk), 146,
154, 155, 157, 168 and 175 (sunset badlands, then the office, then the town at
night). So it is a Barks structure, not a ten-page coincidence, and the field is
lossy on roughly a quarter to a third of pages. As on Billions the lost value
survives in `objects`, `beats` and `panels_of_note`, which is why #77 badlands and
#83 cattle ranch both still hit. Worth a second value; not worth it yet.

### `type` is wrong at 1.7%, and always the same way

**7 of 407 groups (1.7%) are drawn as thought clouds and typed `dialogue`** —
149 g2, 156 g0, 169 g10, 170 g0, 171 g0, 171 g4, 171 g7. Not one group typed
`thought` on this title is wrong, and there are no `dialogue`-drawn-as-`thought`
errors at all. Billions was 2.9% the same way and Roscoe 27% (inflated by its
thought-reading premise); the pilot was the only title to err in the other
direction. **1.7% on 407 groups is the best corpus estimate available**, and the
error is one-directional.

Two other defects worth the editor's time:

- **`150 g9` and `165 g4` carry the wrong `panel_num`** — both belong a panel
  later than they are stored, and both are visible in the prep output because the
  text box drags the crop down a row. Same class as Billions' 048 g3/g4.
- **`164 g1` merges two physically separate balloons** — a small "WE MADE IT!"
  and a larger "DRIVE ON HARD GROUND…", each with its own outline, possibly two
  different nephews. Same class as Roscoe's 177 g3.

### Two schema edges this title hit first

- **A horse gets a balloon.** `174 g5` is "PANT! PUFF!" with its tail on the
  horse's head, not Donald's. Recorded as `other:Donald's horse`, against the
  convention used everywhere else here that animals are `objects` — the steers,
  the coyote and the sidewinder all stay out of `characters`. A named-role animal
  that acts and is given a balloon is a different thing from livestock, and the
  `other:` prefix is exactly the escape hatch for it.
- **Yells lettered without a balloon.** 166's `YEOWCH!` and `YEEK!` are typed
  `sound_effect` but are uttered by riders, so the speaker is recorded rather than
  left as `none`; 169's `SNARL!` and `HISS!` come from a coyote and a snake and
  are left `none`. 174 g4 then letters `SNARL!` *inside a proper balloon* and is
  correctly typed `dialogue`. The distinguishing test used throughout: **does a
  character make the noise**, not whether it sits in a balloon.

---

## Trial results 4 — Plenty of Pets, vol 7 pages 199-208

Run 2026-08-02. 10 pages, 79 panels, 144 groups. Fourth unit of the five-title
trial, and the first since the pilot with a **full nephew cast on nearly every
page**.

| | |
|---|---|
| `vision_text_ok: false` | **0** (Sheriff 0, Billions 0, Roscoe 2.3%, pilot 1.5%) |
| emphasis runs | 24 across 23 of 144 groups (**16%** of groups) |
| confidence | high 138 / **medium 6** / low 0 |
| `cap_colour` non-null | 8 (red 4, green 2, blue 2) |
| `visible_text` strings | 25 |

### Correction rate: zero for the third title running

144 groups and nothing to correct. Holding to the word-level-misreadings-only
rule, the following were seen and deliberately **not** counted, each recorded in
`vision_note`:

- **A soft hyphen where the art letters an ordinary one** — `202 g16` breaks
  `WOOD­PECKER` across lines with U+00AD. Word-break convention.
- **An extra comma** — `205 g11` stores `NO, YOU DON'T, BUD!` where the art
  letters `NO YOU DON'T, BUD!`. Punctuation, `string_replacer`'s job, same rule
  that spared Billions' `052 g4` and Sheriff's `156 g4`.

**Three genuine defects that are not text corrections**, all new-ish shapes:

- **`206 panel 2` letters `CLICK!` beside the key and has no OCR group at all.**
  Caught in `visible_text`. Exactly Sheriff's `172 FZZT!`.
- **`199` has a page-wide `panel_num` shift.** `panel_boxes` gives the page seven
  panels and the crops follow that, but every group except `g0` and `g10` is
  stored one panel too high, and `g11`/`g12` say `8`, which is not a panel on the
  page at all. The grouping pass appears to have counted the title logo and the
  splash art as two panels. Previous titles produced *single* mis-numbered groups
  (Billions `048 g3/g4`, Sheriff `150 g9`); a whole-page shift on the splash is a
  bigger version of the same class and is the kind of thing worth a cheap
  mechanical check, since `max(panel_num) > len(panel_boxes)` catches it outright.
- **The drawn `?` device is typed three different ways.** `205 g9` is
  `background`, `207 g12` is `sound_effect`, and the three `?`s over the nephews'
  heads on `208 panel 5` have **no groups at all**. It makes no sound in any of
  them.

### Measurement 3: six medium calls, and the first *reviewable* nephew population

`--queue-speakers` at the default wrote **zero** entries — the fourth title in a
row, and for the reason Sheriff established: the collective rule means an
unreadable cap yields `nephews` at `high`, so the low band cannot fill. The
`low,medium` run wrote **6**:

```
199 g12   Huey   tail lands on the red cap, but both crate-haulers have the pole in their beaks
200 g2    Huey   same panel-and-pole problem one page later
204 g1    Louie  green cap unmistakable, but the red cap in the same panel prints brown
204 g3    Huey   the same muddy red flash
207 g4    Donald a shout through a wall with nobody in frame; the burglar would suit it too
208 g20   Louie  named by the *previous balloon*, not by the art
```

**Reviewed 2026-08-03: 2 wrong in 6 (33%), and both are balloon-tail errors.**
All six carry `speaker_reviewed` on disk, the first title whose denominator does
not rest on a verbal report.

```
199 g12   Huey  -> Dewey     the tail points at a different nephew
204 g1    Louie -> Huey      the tail points at a different nephew
```

**Not one of them is a colour error.** In both the pass picked the wrong *figure*
and then read that figure's cap correctly; the colour was never in question. This
matters because it reverses what an earlier draft of this section concluded. That
draft read both corrections as cap-colour failures and generalised, across three
titles, that the pass "continues to use colour after recording that it is
unreliable". **That conclusion was wrong**, and it was wrong in the most seductive
way available: the `vision_note`s on both groups really do record the colouring as
untrustworthy, so the story fitted perfectly and was built on a cause that turns
out not to be the cause. *Sheriff*'s `168 g5` remains the **only** confirmed
colour-override error in the trial — one instance, not a pattern, and not grounds
for a rule change.

**Both panels had been enlarged to 2x specifically to trace their tails**, and
both traces are recorded in the notes with false precision — "the tail comes down
squarely onto the middle nephew", "lands squarely on the red-capped nephew's cap
at 2x". The enlargement raised confidence without raising accuracy. That is the
finding worth carrying: **on a panel where several balloons drop into one dark
background over closely-spaced nephews, magnification is not the safeguard it
feels like**, and a note that sounds certain is not evidence that it was.

`204 g1` is the sharper of the two. The correct answer is the nephew whose cap the
pass had *itself* flagged as printing a warm brown rather than red — so it
discounted the figure with the awkward colour and took the one with the clean
green, when the tail pointed at the awkward one all along. Colour did play a part,
but as a distraction from the tail rather than as a misreading.

What this does not tell us is whether the same failure is loose in the calls
nobody has checked. Every speaker error rate in this document — the pilot's 71%,
Sheriff's 7%, this title's 33% — comes from the low/medium band, roughly 4% of
annotated groups. **50 individual-nephew calls sit at `high` and have never been
looked at** (32 on Sheriff, 18 here), and **36 of those 50 are in panels naming
more than one nephew — which is to say, panels where a balloon tail decides the
answer, exactly where both known errors happened.** Queued to
`~/barks-vision/high-confidence-nephews.txt`.

A mechanical check was tried and **rejected on evidence**: within one panel, two
nephews sharing a `cap_colour`, or one nephew carrying two. Across all 867
annotated groups it finds **zero** contradictions, and it would have caught
neither error. There is no free validator in the stored fields — unsurprising in
hindsight, since it was built to catch a colour failure and these are not colour
failures.

### The high-confidence audit: 5 wrong in 50, and the risky configuration is the opposite of the expected one

Run 2026-08-03 on all 50 unreviewed individual-nephew calls at `high`. This is
the first time the high band has ever been looked at.

| | |
|---|---:|
| queued | 50 |
| confirmed | 45 |
| **corrected** | **5 (10%)** |

**10% is not clean.** The high band is better than the medium band's 33% but it
is not the safe population the confidence label implies, and every error rate
before this one was measured on the ~4% of groups that get queued.

Split by panel configuration — classified as the *pass* wrote it, not as the disk
reads after correction — the result inverts the hypothesis that produced it:

| panel | calls | wrong |
|---|---:|---:|
| two or three nephews speaking, tails converging | 33 | **1 (3%)** |
| **one nephew speaking, no sibling in the panel** | **17** | **4 (24%)** |

The pass is not worse at crowded panels; it is worse at empty ones. Three caps
side by side are read *against each other*, and a lone cap is read against
nothing:

```
155 g2   Louie(green) -> Dewey(blue)
158 g9   Dewey(blue)  -> Louie(green)
159 g1   Louie(green) -> Dewey(blue)
163 g2   Dewey(blue)  -> Huey(red)
208 g3   Dewey        -> nephews      (two tails on two nephews, genuinely unresolvable)
```

**All four swaps involve blue, and three are blue↔green in both directions.** That
directly contradicts *Sheriff*'s reading that blue was the most legible colour
because it was recorded most often (19 of 37). It is the most **over-called** one:
on the restored colour, green in shadow prints close enough to blue to take it,
and with no neighbouring cap for reference the pass commits.

`208 g3` is the fifth and is a different animal — two tails landing on two
different nephews, which is exactly what `nephews` is for. It was `high`, so
**neither the low/medium queue nor the new rule below would have caught it**; only
this exhaustive audit did. At 1 in 33 it is not worth tripling the review queue
to reach, and that is a deliberate acceptance rather than an oversight.

### The rule this bought

`--queue-speakers` now also queues **an individual nephew named on a cap colour
with no other nephew speaking in the same panel**, whatever confidence the pass
gave it. Everything it needs is already stored — `speaker`, `cap_colour`,
`panel_num` — so it needs no new field.

Replayed against the audit it queues **4 of the 5** corrections. Its cost is
small and, usefully, concentrated where the risk is:

| title | groups queued |
|---|---|
| Sheriff of Bullet Valley | 19 of 407 (4.7%) |
| Plenty of Pets | 2 of 144 (1.4%) |
| Billions, Roscoe | 0 — neither names an individual nephew at all |
| **The Big Bin on Killmotor Hill** | **8 of 133 (6.0%)** — and *all* of its queue |

**The rule was first reviewed on trial 5, and came back 0 wrong in 8** — see that
section. That is the first direct test of the population this rule exists to
catch, and it neither confirms nor refutes the 24% the audit measured: eight is a
small denominator, and six of the eight rest on an unambiguous bright red, a
colour absent from all four of the audit's swaps. What it does show is the rule
firing on exactly the right configuration — on Big Bin it *is* the whole queue,
because the pass made no low-confidence calls at all.

`speaker_confidence` is deliberately **not** rewritten. It records what the pass
believed; this rule is the reviewer knowing something about the configuration
that the pass could not.

**This is a different population from Sheriff's, and that is the finding.**
Sheriff's 14 were 9 adults, 5 nephews. These 6 are **4 nephews, 1 adult-ish
offstage shout, and 1 placed by dialogue** — back to the pilot's shape, because
this story has the three nephews on nine of ten pages and Sheriff's four
interchangeable dog-faced men do not exist here.

**The open question from Sheriff — does adult-identity-by-costume-colour recur?
— answers *no*, and the reason is structural.** This story is built on unnamed
adult roles (`other:the policeman`, `other:the Black Mask Burglar`) exactly as
predicted, but there are only **two adults in the whole story and they never
share a panel**. The failure mode needs *two similar adults told apart only by
costume colour*; a story with one policeman and one burglar in a checked cap
cannot produce it however many unnamed roles it has. So Sheriff's error class is
better described as **a large similar-looking supporting cast**, not "unnamed
adult roles" — which is a narrower and more useful thing to watch for.

What did recur, in a new place: **the colourist**. On this title the caps are
drawn near-solid black with a small colour flash, and the flash is unreliable —
`200 panel 1` prints one cap a dull olive-grey, `204 panel 1` prints red as
brown, and `203 panels 7 and 8` each give **two of three nephews a green flash**.
Sheriff's rule (two the same colour, or a non-roster colour, means colour is not
evidence in that panel) was applied panel-wide each time, which is why five
individually-named calls came out `nephews` instead.

That rule is also what makes the 8 non-null `cap_colour` values the *low* number
here rather than a shortfall: the caps are visible on far more pages than that,
and were discarded on purpose.

**Two evidence kinds the schema cannot record**, both of which carried real calls:

- **Pyjama and shirt colour.** `204 panels 4-5` and `208 panels 2, 3, 5` dress
  the nephews in red/blue/green with no caps at all, and all eleven calls there
  are `high`. This is the pilot's `085 p5` case, and `cap_colour` has nowhere to
  put it — which is the strongest argument yet for the `identified_by` idea in
  Open threads, since the *same* field would then carry "cap", "pyjamas" and
  Sheriff's missing "hat colour" for adults.
- **The previous balloon.** `208 g20` is Louie because `g19` says
  "WHAT DO YOU THINK, LOUIE?" — nothing in the art says so. Recorded at medium to
  match Sheriff's `165 g0`, which is the same category.

### Retrieval: 11 of 15, and **again not one miss is *not recorded***

`--validate` was run first and reproduced Roscoe at 15 / 1 / #93; it still does
with the *Plenty of Pets* set added.

13 queries name this title (#47-#58 and #95); two more (#30, #43) are cross-title.

| | |
|---|---:|
| hit | **11** |
| miss | **4** (#51, #55, #57, #95) |
| capture-only hits | 7 |
| also answerable from speech | 4 |
| false positives | 0 |

Seven of eleven capture-only is the best ratio of the four titles (Roscoe 11/15,
Billions 9/12, Sheriff 9/26) — a domestic slapstick story talks about its props
much less than a western does.

The four misses split **4 not-retrieved, 0 not-recorded**, matching Sheriff
exactly. Two are the failure modes already documented and two are worth reading:

- **#51 *colliding* — not retrieved.** All three pages record the collision:
  "knocks Donald off his feet" (200), "butts Donald head first into the tree
  trunk" (203), "butts the burglar off his feet" (206). Nothing says *collide*.
  Morphology does not help here and neither would a stemmer — this is the
  **reader-vocabulary vs drawn-vocabulary** gap, now on its fifth instance after
  *sick*, *sad*, *pain* and (below) *scared*.
- **#57 *scared* — not retrieved, and it is the emotion case again.** The records
  carry the *depiction* on every expected page — "sweat drops flying", "sweating,
  backed into the corner", "pulling up short" — and never the word. This is
  precisely Billions' #34 *sad* → "in tears" result, reproduced on a different
  emotion in a different story. **Two titles have now independently shown that
  emotion fails on retrieval rather than on discrimination.** That is no longer a
  single observation, and it is the clearest case in the trial for embeddings.
- **#55 *bag* against the record's *sack*** — plain synonymy. Unlike Sheriff's
  #79 there is no source word to prefer: the comic never names it.
- **#95 *letterbox* against the record's *mailbox*.** This one was **called in
  advance and left to fail on purpose.** Reading page 199 it was obvious that the
  query's British *letterbox* would not reach an American comic's *mailbox*, and
  writing both would have manufactured a hit. Sheriff's rule — prefer the comic's
  own word — cannot decide it, because the art names the box only `DONALD DUCK`.
  So this is a **third** vocabulary class, distinct from the two already recorded:
  not drifting within a title (Roscoe), not drifting away from the source
  (Sheriff), but **the query and the record using different correct words for the
  same object with no source text to arbitrate**. Only embeddings fix it.

One property of the scorer worth recording from this title: **#49
*non-speaking animals* hits, but on the wrong pages.** Its expected list is nine
of the ten pages, and the top band returns `199, 200, 203` — of which 199 is not
on the list at all, because the animals there are shut in a cage. A query true of
almost a whole title is close to a guaranteed hit and discriminates nothing; it
is reported here rather than trimmed, as Sheriff did for #60 and #65.

### Where the animals went, and why

**Decision: non-speaking animals stay in `objects`; an animal gets into
`characters` only if the art gives it a balloon.** This follows Sheriff exactly
(livestock in `objects`, `other:Donald's horse` in `characters` because 174 g5
gives it "PANT! PUFF!"), and it was worth deciding deliberately because this is a
pet story where the animals drive the entire plot — they are the ones who defeat
the burglar.

The test fires exactly once in ten pages: **`205 g8`, where the police whistle
the goat has swallowed sounds inside it in a balloon of its own with a proper
tail.** So `other:the goat` is in `characters` on 205 and the goat is in
`objects` on every other page. Every other animal noise in the story — the owl's
`HOO!`, the goat's `BAA!`, the woodpecker's `RAT-A-TAT` — is display lettering
with no balloon and is left `none`, the same treatment as Sheriff's coyote and
snake.

Retrieval is unaffected either way, since the scorer indexes `characters` and
`objects` equally; this is a schema-consistency decision, not a retrieval one.

Two conventions this title needed on top of that:

- **The nephews' `ZZZ`s get a speaker** (`207 g9`, `nephews`), where the drawn
  `?` on `205 g9` does not. Snoring is a noise the characters make, which is
  Sheriff's test; a question mark represents a state and makes no sound.
- **The burglar's balloon-less `YEEK! YOWCH!`** (`206 g6`) records him as the
  speaker, on Sheriff's `166 YEOWCH!` precedent. Note the mirror image: Sheriff's
  case was typed `sound_effect` and this one is typed `dialogue`, and they are
  the same thing.

### `visible_text`: 1 net new in 25, and the yield is not rising with page count

25 strings, of which **one exists nowhere in the OCR groups** — `CLICK!` on 206,
the key turning in the closet door. Against Roscoe's 0 of 13, Billions' 2 of 18
and Sheriff's 7 of 62, that is **4%**, the second-worst of the four.

Sheriff suggested the yield was rising with page count. This title says otherwise:
10 pages here yield 1 where 10 pages of Billions yielded 2. What actually
predicts the yield is **how much non-speech lettering the story has that OCR did
not already catch**, and Barks' sound effects are nearly always caught — 24 of
these 25 strings are already OCR groups. The one that got away is small lettering
on a prop, which is now the shape of **every** net-new string across four titles
(`1¢`, `M.D.`, `313`, two cattle brands, a `REWARD` poster, and now `CLICK!`).

### Off-vocabulary rate

`characters`: **8 distinct values, 5 on the roster** (Donald, Huey, Dewey, Louie,
`nephews`), covering 29 of 35 page-appearances — **83%**, far the best of the four
titles (Sheriff 50%, Billions 75% of values but a smaller cast, Roscoe 1 of 6).
The three `other:` names are `the Black Mask Burglar`, `the policeman` and
`the goat`. **The database tags this story with no cast at all** — `story_cast`
in `queue.json` is `[]` for the **fourth title running**, so the closed-set
machinery (`story_characters`, the `Daisy Duck`/`Gyro Gearloose` aliasing, the
nested `Pig Villains` flattening) is still completely untested after 56 of the
trial's ~66 pages. **Big Bin is the only unit left that can exercise it**, and
skipping it would leave the trial having proved nothing about the one design
decision it was built to validate. **It was run on 2026-08-03 and did exercise
it** — see trial 5, which is the only place in this document where `story_cast`
and `story_things` are non-empty.

`setting`: **0 of 10 pages used a closed-vocabulary value**, all `other:`
(`Donald's house` 8, `Donald's kitchen` 1, `Donald's back yard` 1). The closed
vocabulary is now **0-for-4** on being worth reaching for, and this title is the
cleanest demonstration of why: nine of the ten pages are `indoors`, which is true
and answers nothing.

Note also that the one-value-per-page limitation bites here in a *new* way. It is
not that pages cut between two locations (they do — 202 alternates yard and
living room four times); it is that a whole story set in one house makes `setting`
**constant**, so the field discriminates nothing at all within the title. Sheriff
and Billions lost information to the single value; this title has almost none to
lose.

`barks-ocr-speaker-census --volume 7` reports **no variant spellings and nothing
off-roster**. One name clears the promotion threshold — `the Black Mask Burglar`
at 11 — and **should not be promoted**, for the same reason as Blacksnake McQuirt
and `other:crows`: it is a single-story name. This is the third title to put a
single-story name over the threshold, which strengthens Sheriff's argument that
the census should weight by *how many titles* a name appears in.

### `type` is wrong at 2.8%, and this title breaks the one-directional finding

**4 of 144 groups (2.8%)**, and unlike the last three titles they do **not** all
run the same way:

| direction | count | groups |
|---|---:|---|
| thought cloud typed `dialogue` | 2 | 200 g4, 200 g5 |
| **speech balloon typed `thought`** | **2** | 207 g2, 207 g14 |

Every group actually typed `thought` elsewhere on the title was checked against
the art and is correct — eleven of them, most on 205.

`207 g2` and `g14` are Donald shouting from inside the locked closet: plain
triangular tails, no bubble trail, beak open. Sheriff reported "no
`dialogue`-drawn-as-`thought` errors at all" and called the error
one-directional on the strength of 407 groups; **the pilot found this direction
and so does this title**, so the corpus estimate should stay ~2-5% and
**bidirectional**, with the reverse direction rarer.

The two on `200` are the mirror pair — `g4` and `g5` are both scalloped clouds
with two-circle trails typed `dialogue`, and `g5` is the harder call because
Donald's beak is wide open in it.

### Cost

**One session**, 116 images read: 10 page overviews, 79 panel crops, and **8
enlargements**. Batched one message per page, as Sheriff established.

The page-reading phase ran **19:42 to 20:06, ~24 minutes for 10 pages** —
**~2.4 min/page against Sheriff's 1.6**. Page 199 alone took ~7 of those minutes
(the splash, three enlargements, and the pre-read name grep), so **the last nine
pages ran at ~1.9 min/page**, which is Sheriff's rate within noise. Reading the
two design docs, adding the query set and scoring sit on top of that and are not
counted, as on previous titles.

So this title neither confirms nor undercuts Sheriff's 1.6 — it reproduces it
once the first page is excluded, on a fifth of the pages, which is about the most
a 10-page unit can say. The 8 enlargements are the honest per-page variable, and
they are concentrated: **Sheriff spent 11 on 32 pages, this title 8 on 10**,
because the caps here are drawn near-black with a small colour flash and three
panels send three balloon tails into one black background.

### The pre-read name grep worked, and its one gap is worth fixing

Sheriff's discipline — grep the whole title's `groups.json` for capitalised names
before reading page 1 — was followed and resolved **Sylvester** (the squirrel),
**Jasmine Joe** and **the Black Mask Burglar** up front, so the burglar was never
provisionally `other:the thug`.

It **missed `Yehooty`**, the owl, which is named on 202. The grep printed the
frequency table's head and its rare tail, and `YEHOOTY` occurs three times —
enough to fall out of the tail and too rare to reach the head. The fix is to
print *all* distinct capitalised tokens minus a stop list rather than the two
ends of the distribution. The cost was one retrospective edit across four pages
(`owl` → `Yehooty the owl`), caught because the name appeared before the story
was finished; on a longer title it would have been the Roscoe split.

The same edit was made for `skunk` → `Jasmine Joe the skunk`, which the grep
*did* surface but whose referent only became clear on 204, when the nephew
holding the skunk asks whether to leave Jasmine Joe outside. **A name in the
dialogue does not tell you which thing it names**, so the grep buys the spelling,
not the identification.

---

## Trial results 5 — The Big Bin on Killmotor Hill, vol 11 pages 038-047

Run 2026-08-03. 10 pages, 75 panels, 133 groups. **The last unit of the
five-title trial, and the only one that exercises the closed set.**

| | |
|---|---|
| `vision_text_ok: false` | **1 (0.75%)** (Sheriff 0, Plenty of Pets 0, Billions 0, Roscoe 2.3%, pilot 1.5%) |
| emphasis runs | 62 across 51 of 133 groups (**38%** of groups) |
| confidence | high 131 / **medium 2** / low 0 |
| `cap_colour` non-null | 8 (red 6, blue 1, green 1) |
| `visible_text` strings | 29 |
| first title stamped | `capture_prompt_version: 2` |

### The closed set works, and it is worth more than the retrieval number

This is what the title was kept for. Four titles ran with `story_cast: []`, so
`story_characters`, the `Daisy Duck`/`Gladstone Gander`/`Gyro Gearloose` aliasing
and the nested `Pig Villains` flattening had **never been exercised once** across
56 of the trial's 66 pages. All four paths now have evidence:

- **`roster.txt` offered it.** `story_cast: ['The Beagle Boys']` and
  `story_things: ['sulphuric acid']` reach `queue.json` and the roster file, the
  first non-empty values in the trial. The roster renders the Beagle Boys under
  *"and, tagged in the database as appearing in THIS story"*, which is the closed-set
  question the design asks for rather than an open one.
- **They came back from the closed set, not from `other:`.** `042` and `047`
  store `"The Beagle Boys"` bare in `characters`. On any previous title a recurring
  group villain had nowhere to go but free text, where `other:the Beagle Boys` and
  `other:Beagle Boys` are two characters.
- **The aliasing and the flattening are correct**, checked directly rather than
  inferred: `Daisy Duck → Daisy`, `Gladstone Gander → Gladstone`,
  `Gyro Gearloose → Gyro`, and — the part that matters — the two entries that are
  **not names at all**, `Gyro not in GG series` and `Uncle Scrooge not in US series`,
  fold onto `Gyro` and `Scrooge` instead of becoming characters. `Soapy Slick` and
  `Mr. McSwine` are present in the 48-name set, which they could only be if
  `get_all_tags_in_tag_group` really flattens the nested `Pig Villains` group.
  Nothing leaks: no full-form name and no pseudo-entry survives canonicalization.

**Measurement 4 is the result this title moves**, and it moves a long way.
`characters` has 8 distinct values across the title, of which **6 are roster
entries and 1 is the closed set**; exactly one is free text
(`other:a bystander`, used once). By page-appearances that is **40 of 41 covered
by roster + closed set — 98%**, against *Plenty of Pets*' 83%, Sheriff's 50% and
Roscoe's 1-of-6.

The census makes the same point from the other end:
`barks-ocr-speaker-census --volume 11` reports **no variant spellings and nothing
off-roster**, and — the telling part — **the Beagle Boys do not appear in the
free-form section at all.** The two free-form names are `a bystander` and
`the radio announcer`, one use each, neither near the promotion threshold. This is
the first title in five to produce **no promotion candidate and no single-story
name over the threshold**, and the reason is structural rather than lucky: the one
name that would have recurred was already in the closed set.

`setting` is the exception and gets no help: **0 of 10 pages used a
closed-vocabulary value**, all `other:` (`the money bin` 7, `Killmotor Hill` 2,
`the cleared space` 1). The closed vocabulary is now **0-for-5**.

### Correction rate: 1 in 133, and it is a real word

`046 g7` stores `PUT EXTRA BLANKETS ON THE **BEDS**!` where the radio bulletin
letters **`BED!`** singular. A word-level misreading, so it counts: **0.75%**,
sitting between Roscoe's 2.3% and the three zeroes. Five titles in, measurement 1
says the pass is reading rather than inventing and nothing more.

Held to the word-level-misreadings-only rule, the following were seen and
deliberately **not** counted, each recorded in `vision_note`:

- **`MCDUCK` against the art's `McDUCK`** (043 g11) — a case difference, the same
  rule that spared Sheriff's `McQUIRT`.
- **A soft hyphen** (U+00AD) breaking `COOK-STOVE` across lines on `046 g12`
  where the art letters an ordinary one. Word-break convention, as *Plenty of
  Pets* `202 g16`.
- **Two clipped signs completed by the OCR** — `039 g11` stores `STOP HERE` for a
  sign drawn running off the panel edge showing only `STO / HER`, and `043 g8` does
  the same for `PERISCOPE PEEPHOLE`. Completing a clipped sign is the right reading,
  not a misreading.

**One correction, and the emphasis had to be written against the uncorrected
text.** `046 g7` also carries a bold run over the whole second half of the
bulletin. `vision_apply` refuses any markup that does not strip back to the
*stored* words, so the markup is written over `BEDS!` and the correction is
proposed separately. The tags sit entirely after the corrected word, so applying
the queued fix cannot disturb them — which is the inline-markup argument working
exactly as the spans section claims, on the first case in the trial where a
correction and an emphasis run share a group.

### A speaker population that is entirely the new rule's doing

`--queue-speakers` wrote **8 entries at the default `low` threshold, and not one
of them is a low-confidence call** — the pass made zero. All 8 come from the
lone-panel rule added after trial 4: an individual nephew named on a cap colour
with no other nephew speaking in the same panel.

```
038 g5, g12   039 g8   040 g3, g9   041 g1   043 g2   044 g9
```

This is the rule paying for itself at 6.0% of groups (Sheriff 4.7%, *Plenty of
Pets* 1.4%), and it is the fifth title running in which the **low band is empty
because the collective rule works**. Only 2 groups are `medium`, both the
placed-by-what-the-line-says category: `042 g9` (a periscope-view panel whose tail
runs off-panel toward where both Donald and Scrooge stand) and `046 g20` (`OH, ME!
OH, MY!` from inside a bin nobody is drawn in, given to Scrooge on register alone).

**Reviewed 2026-08-03: 8 queued, 8 confirmed, 0 wrong.** GLK walked the queue in
the editor and found no issues; all 8 carry `speaker_reviewed` with `speaker` and
`cap_colour` exactly as the pass wrote them — 6 Huey on red, 1 Dewey on blue,
1 Louie on green.

Against the pilot's 71%, Sheriff's 7%, *Plenty of Pets*' 33% and the high-band
audit's 10%, **zero in eight is the cleanest speaker result in the trial.** Two
things temper it and both should be said plainly. Eight is a small denominator —
it cannot distinguish a genuinely easy title from a lucky one. And the population
is not the same population those other rates measured: these are all *lone-panel*
calls, the configuration the audit found worst at 24%, but on a title where six of
the eight rest on an unambiguous bright red. Red was involved in none of the
audit's four swaps, which were all blue and mostly blue↔green. So the honest
reading is that **the lone-panel rule queued the right configuration and this
title happened to be an easy instance of it**, not that the configuration is safe.

The two calls that were *not* red — `040 g3` Dewey on blue and `044 g9` Louie on
green — are the ones that carried real risk, since blue↔green is where the audit's
errors live. Both were confirmed. Two data points do not overturn the audit, but
they are the first evidence that a blue/green call made *with another cap in the
same panel for reference* holds up.

**The denominator is readable off disk**, which is what the Confirm as is button
was added for: this is the second title after *Plenty of Pets* whose review count
rests on the data rather than on a verbal report.

One workflow note worth keeping. The review happened *after* `vision_apply` had
run the mirror, so the 8 flags landed on easyocr only and
`barks-ocr-vision-mirror --write` had to be run again to carry them across. That
is not a defect in either tool — the mirror is idempotent and the second run wrote
6 pages and then went quiet — but **a review is always after the apply that
queued it**, so mirroring again afterwards is a standing step rather than a
one-off.

Two things about the cap evidence here are worth recording whatever the review
says. **Only 8 of 133 groups carry a `cap_colour` at all**, because this story
keeps the nephews bare-headed for long stretches (039 panels 2-3, 046 panel 1) and
because the whole middle of the story has only *one* nephew on the page. And the
colourist is unreliable in a new place: **Donald's own sailor hat prints green
rather than blue** on `045 panel 7` and `042 panel 2`. Four titles found the
colourist slipping on nephew caps; this is the first time it slips on a lead's
costume, which is a caution that "identified by costume colour" is shaky even for
a character nobody would otherwise doubt.

### Retrieval: 17 of 24, and the first *not-recorded* misses in three titles

`barks-ocr-retrieval-score --validate` was run **first** and reproduced Roscoe at
15 / 1 / #93, and still does with the Big Bin set added. 19 queries name this
title (#98-#116) plus five cross-title (#11, #17, #26, #30, #43).

| | |
|---|---:|
| hit | **17** |
| miss | **7** (#11, #26, #98, #103, #107, #111, #112) |
| capture-only hits | 9 |
| also answerable from speech | 8 |
| false positives | 0 |

**#17 is the query this title existed for and it hits on both pages**, via
`characters` among four other fields — which is to say the closed-set name is
retrievable, not merely storable.

#### The split: 5 not-retrieved, 2 not-recorded

Sheriff and *Plenty of Pets* had each produced **zero** not-recorded misses, and
Roscoe's only one was fixed on a re-read. This title produces two, and they are
the same gap twice:

- **#98 *an establishing shot* and #26 *an establishing shot with no characters in
  frame* — both not recorded.** The pages are described in detail — 038's splash
  as "the money bin drawn as a plain riveted steel cube standing alone on the bare
  summit", 046 panel 4 as "a fire hydrant burst open in the **empty** night street"
  — but the phrase *establishing shot* appears nowhere on the title, and neither
  does any other shot-type word. **Capture records what is in a panel and never how
  it is framed.** That is a real hole and a new one: `panels_of_note` is free text
  and could carry framing vocabulary, so this argues for guidance rather than a
  field. Note it is *not* Billions' #26 result — that was a false positive caused by
  a record that happened to say "establishing shot"; here nothing says it, which is
  the honest version of the same finding.

The other five are all *not retrieved*, and between them they add **two new
vocabulary classes** to the three already documented:

- **#103 *flypaper* — and the source-word rule caused this miss.** The record says
  `fly paper` in `objects`, `visible_text` and `beats`, because **the comic letters
  it `FLY PAPER` as two words** and the standing rule is to prefer the comic's own
  word. The query says the closed compound. So this is neither synonymy nor
  morphology but **compounding**, and it is the first case where *following* the
  Sheriff `trousers`/`pants` rule produced the miss rather than preventing one. The
  two rules can conflict, and no amount of care about vocabulary resolves it —
  a stemmer will not join `flypaper` to `fly paper` either, since the split is in
  tokenisation, not in morphology.
- **#112 *wall painting* against the record's *wall picture*** — plain synonymy
  with no source word to arbitrate, since the comic letters only the captions
  (`MIGHTY DOLLAR`, `A FAST BUCK`) and never names the object. Exactly *Plenty of
  Pets*' #95 letterbox/mailbox class, reproduced.
- **#11 *Scrooge diving into his money bin* — the iconic one, and it misses.**
  The doc said of this query: *"If capture misses this, it fails."* The gag is
  recorded twice on 041 — "throws himself off the catwalk into the coins" in
  `beats`, "launching himself off the catwalk into the heaped coins, arms spread,
  hat and spectacles flying loose" in `panels_of_note` — and the word *dive* is in
  neither. **The schema and the reading are fine; the retriever cannot get from
  *diving* to *launching himself*.** Read against the pass/fail framing this is the
  single strongest embeddings argument in five titles, because it is the one query
  the doc singled out in advance and the record could hardly be better.
- **#107 *love* and #111 *worry* — emotion, for the third and fourth time.**
  041 records `hearts` in `objects` and "three red hearts floating around his head"
  in `panels_of_note`; 043 records "sobbing" and "flat on his back on the floor".
  Neither says *love* or *worry*. Both were **called in advance and left to fail on
  purpose**, as *Plenty of Pets* did with #95: writing the reader's word over the
  drawn one would manufacture a hit and destroy the measurement.

So **reader-vocabulary vs drawn-vocabulary now stands at seven instances** across
four titles — *sick*, *sad*, *pain*, *scared*, *colliding*, *love*, *worry* — plus
*diving*. It is not a schema problem and five titles have not made it one.

### `visible_text`: 1 net new in 29

29 strings, of which **one exists nowhere in the OCR groups** — `B Co.`, a shop
awning at the edge of frame on 039. That is **3.4%**, against Roscoe's 0 of 13,
Billions' 2 of 18, Sheriff's 7 of 62 and *Plenty of Pets*' 1 of 25.

Five titles in, the field's shape is settled and *Plenty of Pets* had it right:
what predicts the yield is how much non-speech lettering the story carries that
OCR did not already catch, and **every net-new string across five titles is small
lettering on a prop or at the edge of frame** (`1¢`, `M.D.`, `313`, two cattle
brands, a `REWARD` poster, `CLICK!`, and now a half-seen shop sign). This title has
a great deal of non-speech lettering — five warning signs, `SULPHURIC ACID`, three
`FLY PAPER` sheets, `BEAGLE BOYS` placards, seven `BILLS`/`LEDGER` spines — and
the OCR caught essentially all of it.

One string is genuinely net-new and *not* counted above because it is a second
instance rather than a missing one: `047` letters `BEAGLE BOYS` across two
sweaters and the OCR grouped both, but `042`'s four Beagle Boys carry four
placards of which the OCR grouped one.

### `type` is wrong at 0.75%, and the *other* mislabel is the balloon/sound-effect axis

**1 of 133 groups (0.75%)** is a thought cloud typed `dialogue` — `042 g5`, a
scalloped cloud with a four-circle trail rising from the periscope. That is the
lowest rate of the five titles (Sheriff 1.7%, Billions 2.9%, *Plenty of Pets*
2.8%, Roscoe's premise-inflated 27%), and both groups actually typed `thought`
here — `042 g3` and `045 g4` — are correct.

A second mislabel sits on a different axis and is worth separating: **`043 g5`
`YOICKS!` is typed `sound_effect` but the art puts it in a proper rounded balloon
with a tail to Donald.** That is the Sheriff `174 g4` / *Plenty of Pets* `206 g6`
category — a yell that is dialogue by the test used throughout — and it argues the
corpus `type` error rate should be tracked as *two* rates, since a
thought/dialogue confusion and a dialogue/sound-effect confusion have nothing to
do with each other.

The drawn-punctuation device appears again and is typed a **fourth** way:
`045 g8` is three exclamation marks around Scrooge's head typed `sound_effect`,
against *Plenty of Pets*' `?` as `background` (205 g9) and `sound_effect`
(207 g12) and as no group at all (208 panel 5). `046 g18` has a drawn `?` with no
group. It still makes no sound in any of them.

### A panel-segmentation defect, found by the size assertion

`047`'s panel 1 crop is 1872x1345 and 854KB — the largest in the title — and the
reason is not a big drawing. **The art draws two panels there with a ruled border
between them**, the ice-cube view and the caption panel where the ducks crawl out,
and `panel_boxes` returns a single box spanning both. All three groups in that
row therefore carry `panel_num: 1`, correctly with respect to the box and wrongly
with respect to the page.

This is a different class from every panel defect the trial has found so far —
Billions `048 g3/g4`, Sheriff `150 g9` and `165 g4`, *Plenty of Pets* `199` — all
of which were *stored `panel_num`* errors against correct boxes. Here the box
itself is wrong, so no `panel_num` check could catch it and the kivy editor cannot
fix it. Usefully, **the 500KB assertion caught it for free**: a panel box that
spans two drawn panels is roughly twice the area of its neighbours, which is
exactly what trips the size limit. Worth knowing that the crop-size failure is a
weak panel-segmentation smoke alarm, and worth checking the other three oversized
panels (038 p1, 040 p5, 047 p4) on the same suspicion — 038's is a genuine splash,
but 040 p5 has the same two-areas-one-box look.

### Mirroring: the first title with no residue at all

`vision_apply` mirrored **133 of 133 groups and all 51 marked-up groups (62
emphasis runs)** onto paddleocr, and **nothing was refused** — no line-break
differences and no word differences, where Roscoe left 5 and 4.

That is not the pass being tidier; it is where the volume sits. Vol 11 is inside
the reconciled range (vols 1-18 at 99.6% identical), so the two engines already
agreed word for word and newline for newline on every annotated group. The mirror
doubling as a reconciliation finder is only interesting where reconciliation is
outstanding.

### Cost

**One session**, 85 images read: 10 page overviews and 75 panel images (79 panel
boxes' worth, four of them delivered as tiles), and **zero enlargements** — the
first title in the trial to need none, because the tiles already magnify the
panels that would have prompted one and because there are only 8 readable caps in
the story to trace.

The page-reading phase ran **11:25 to 11:43, ~18 minutes for 10 pages — ~1.8
min/page**, against Sheriff's 1.6 and *Plenty of Pets*' 2.4 (1.9 excluding its
splash). Reading the two design docs, fixing the prep abort, adding the query set
and scoring sit on top of that and are not counted, as on every previous title.

**This does not move measurement 5 and is not offered as doing so.** Ten pages
cannot; Sheriff's 32-page 1.6 min/page stands as the projection, and the honest
reading of 1.8 is that a third 10-page title reproduced it within noise. What it
does confirm is that the batching discipline — one message per page carrying
`groups.json`, the overview and every panel crop — is what the rate depends on,
since this title used it from page 1 and shows none of *Plenty of Pets*' first-page
penalty.

---

## Mirroring across engines: the pass must not undo the reconciliation

Added 2026-08-03, after four titles had been annotated on one engine only.

The corpus carries **both** engines all the way through on purpose. They are not
alternatives to choose between — they are being **reviewed and reconciled toward
each other**, with `ocr_check` and the kivy editor, until both files say the same
thing and can collapse into a single set of finals. `use_as_final` was an early
idea for picking a winner per page and is not going to be used; measured on
2026-08-03 it is `false` on all 5,560 easyocr pages and `true` on exactly one
paddleocr page, so nothing has ever depended on it.

Against that, **a vision pass makes the two engines less alike.** Every bold run
it writes lands on one side only, and *Plenty of Pets* produced 219 of them in a
single sitting — 219 fresh discrepancies for a human to reconcile, created by the
tool that is supposed to help finish the job. That, and not the loss of the
annotations, is why mirroring exists: the annotations are cheap to redo, the
reconciliation is not.

```bash
barks-ocr-vision-mirror --title "Plenty of Pets"          # dry run
barks-ocr-vision-mirror --title "Plenty of Pets" --write
```

`vision_apply` now runs it automatically at the end of every apply, with
`--no-mirror` to opt out.

### Reconciliation progress, which is what makes this cheap

Identical stored text between the two engines, markup ignored:

| | identical | groups still differing |
|---|---:|---:|
| **vols 1-18** | **99.6%** | 199 |
| **vols 19+** | **90.0%** | 2,568 |
| all | 96.1% | 2,767 |

Vol 28 is already at 99.9%, out of sequence; vol 29 is furthest out at 82.8%.
Because the annotated titles sit mostly in the reconciled range, **99.5% of
annotated groups mirror cleanly**.

### Matching is by text, not by group id

The two engines' group ids do not correspond — that is why the editor's Speaker
button is per-pane and why the pass reads one engine. But the *words* do
correspond, after Gemini's grouping, for 99.7% of annotated groups. So a group is
paired with the one on the other side that stores the same words, whitespace
ignored. Where several balloons on a page carry identical words — "YES," twice in
one panel of 202 — the nearest text box wins, keeping the pairing one-to-one.

**Emphasis is held to a stricter test than the speaker fields.** A speaker call is
about the art and travels with the balloon, so whitespace cannot invalidate it.
Markup indexes the characters of one specific string, so it crosses only when both
sides store exactly the same characters, **newlines included** — a tag placed
against different line breaks lands on the wrong word, which is the offset problem
in another guise. Both sides are compared *stripped*, so a re-run over already
mirrored groups is a clean no-op rather than a page of false differences.

`speaker_reviewed` is mirrored deliberately. A human's answer to "who is speaking"
is about the art, not about which engine transcribed the balloon, and the two
files are destined to become one — leaving the flag off one side would only
manufacture a difference to reconcile later.

### The residue is a worklist, not a failure

Backfilled across the pilot and all four trial titles: **861 groups and 211
emphasis runs** mirrored, over 66 pages. What did **not** cross is reported in two
buckets, and the distinction is the useful part:

- **5 groups agree word for word but break their lines differently** (Roscoe 175
  g5, 178 g5/g6/g7/g9). Speaker fields crossed; emphasis did not. Fix the line
  breaks and re-run.
- **4 groups the engines genuinely disagree about**, all Roscoe, all in a vol-20
  file that is only 89% reconciled: the `GYRO GEARLOOSE` title logo, the
  `INVENTION KIT` and `FOR BIG INVENTIONS` crate labels, and `177 g3` — which is
  the two-separate-letters-in-one-group defect trial 1 already recorded. Nothing
  was copied onto these.

So the mirror doubles as a reconciliation finder, pointed at exactly the groups a
vision pass has just looked at closely.

---

## Tracking what has been read: a status scan, not a ledger

Asked before trial 5, prompted by the sibling repo's `restore-ledger.jsonl` and
`upscale-ledger.jsonl`. The answer is **yes to provenance and coverage, no to a
run/page ledger**, and the reason is that the two workloads are not the same
shape.

A restore or upscale run is long, unattended, parameterised by a recipe hash, and
can be stopped half way through — so its ledger earns its place answering *where
did I get to* for work that cannot simply be repeated, and *which recipe produced
this page*. A vision pass is one title in one session and is **idempotent**:
applying a result twice changes nothing. There is no lost position to recover,
and a second record of what is on disk could only drift away from the disk.

```bash
barks-ocr-vision-status          # volumes with vision data
barks-ocr-vision-status --all    # every volume
```

### The provenance was designed and never written

`capture_model`, `capture_prompt_version` and `captured` were declared in
`vision_schema.py`, given publication classes, rendered into every
`page-capture.json` stub by `vision_prep`, and documented in this file as the
provenance row — and **never written by anything**. They were absent from
`vision_apply`'s `CAPTURE_KEYS`, so a result that set them was *rejected*, and
`_stamped()` did not add them. All 56 capture records written before 2026-08-03
carry nulls.

Fixed that day. Every capture record now carries:

```json
"capture_model": "claude-opus-5[1m]",
"capture_prompt_version": 2,
"captured": "2026-08-03T11:09:52+10:00",
"capture_rules": ["collective-nephew", "inline-emphasis",
                  "mirror-engines", "lone-panel-queue"]
```

The version and the rule list are filled in **by the applying code**, not
accepted from the result file: they are properties of the tooling, not claims a
reading session should be trusted to make about itself. `capture_model` is the
one thing the session does know, so it comes from `--capture-model` and stays
`null` rather than being guessed.

`capture_rules` exists because a bare integer tells a future reader nothing about
what changed. Add a rule, bump the version, in the same commit.

**The five titles already read are deliberately left unstamped.** Re-applying
them would write `v2` onto pages that were not read under v2's rules — the mirror
and the lone-panel queue did not exist when they were read. The nulls are what
identifies that cohort, and the status report names it rather than hiding it:

```
capture prompt version (current is v2):
   unstamped (pre-2026-08-03)    56 page(s)  <- read before provenance was written; rules unknown
```

**Big Bin will therefore be the first title distinguishable from them**, which is
the whole reason this went in before trial 5 rather than after.

Done — `barks-ocr-vision-status` now reports the split it was built to show:

```
capture prompt version (current is v2):
   unstamped (pre-2026-08-03)    56 page(s)  <- read before provenance was written; rules unknown
   v2                            10 page(s)
```

The 10 stamped pages carry `capture_model: "claude-opus-5[1m]"`, passed on the
command line, with the version and the four-rule list filled in by the applying
code rather than accepted from the result file.

### What a scan cannot recover, and the agreed shape for it

A review outcome is an *event*, not a state. Trial 4's *2 wrong in 6* and the
*5 wrong in 50* audit were both reconstructed by diffing the `result.json` files
in `~/barks-vision` against the corpus; delete that scratch directory and both
measurements are gone. `speaker_reviewed` records that a human looked, never what
they changed.

Agreed shape when this is built: **store the pass's original call on the group**,
beside the reviewer's answer — `speaker_was` and the review date — rather than
adding a ledger. The datum belongs with the thing it describes, it survives any
scratch directory, and it makes a per-title error rate computable from the corpus
alone. **Built 2026-08-03**, exactly to that shape — see below.

---

## Three changes with a deadline

Made 2026-08-03, deliberately **before** the corpus run rather than after, and
grouped because they share one property: the vision pass writes fields *into* the
corpus, so a field added later needs those pages read again. Re-reading is the one
cost in this project that cannot be amortised, which gives schema and guidance
decisions a hard deadline at the start of the run. Everything else on the open
threads — the panel-box checks, census weighting, the `type` mislabels — is as
cheap after 5,483 pages as before, and can wait.

`capture_prompt_version` goes to **3**, with `identified-by` and
`framing-vocabulary` added to `capture_rules`.

### `identified_by` — what the call rests on

`cap_colour` records the evidence behind a *nephew* call and is what makes one
reversible. The trial found three populations with no equivalent, and every one
of them is unrecoverable without this:

- **adults told apart only by hat and shirt colour** — where the trial's single
  confirmed colour-override error lives (Sheriff `168 g5`, whose contradiction
  with `g3` would have been mechanical to catch had the evidence been recorded);
- **eleven high-confidence calls made from what a character was wearing**
  (*Plenty of Pets* 204 and 208), which `cap_colour` has nowhere to put;
- **a call made from the previous balloon** rather than from the art at all
  (`208 g20`, Sheriff `165 g0`).

A **list**, because a real call rests on more than one thing — a tail that lands
on a figure *and* the cap that figure wears — and separating them is what lets a
later check ask whether two calls in one panel disagree about the same evidence.

**Closed, with no `other:` escape**, unlike `speaker` and `setting`. The point is
to make calls comparable across the corpus — to ask whether the costume-based
calls are the ones that turn out wrong — and free text cannot be counted. A kind
genuinely missing is a reason to add one here deliberately.

It is **required wherever somebody speaks**, since a call with no recorded
evidence is precisely the state the field exists to end; `none` needs none.
Two cross-checks come free and both are cheap to state: a `cap_colour` was read
but the call does not cite it, or it cites `cap-colour` and no colour was
recorded. Either means the two fields were filled in independently rather than
describing one judgement.

### Framing vocabulary — guidance, not a field

The trial's only *not recorded* misses were #98 and #26, both asking for a shot
type. Capture describes what is *in* a panel and never how it is framed. Since
`panels_of_note` is free text, this costs a paragraph in `roster.txt` rather than
a schema change — which is what the trial argued for, and `v3` then showed the
content is often already there in substance: an embedding reaches "establishing
shot" from a wide scene-setting description. The guidance asks for the shot to be
named *only where the framing is what makes the panel notable*, since labelling
every panel would defeat `panels_of_note` entirely.

### `speaker_was` — making a review outcome survive

Every speaker error rate in this document — the pilot's 10 in 14, Sheriff's 1 in
14, *Plenty of Pets*' 2 in 6, the 5 in 50 audit, Big Bin's 0 in 8 — was
reconstructed by diffing `~/barks-vision` against the corpus, and would vanish
with that directory. The editor now keeps the superseded call beside the new one.

The rule is exact and the asymmetry is the whole design: **`speaker_was` is
written only when a review changes the call.** A reviewed group carrying it is a
correction; a reviewed group without it is a confirmation. So a per-title error
rate becomes computable from the corpus alone, with no scratch directory and no
ledger — the datum sits on the thing it describes, and a second record of what is
on disk could only drift away from it.

It is written **once**: a second edit of an already-corrected group must not
overwrite the pass's original answer with the first reviewer's. `Confirm as is`
deliberately writes no `speaker_was` at all, only the date.

### Reviewing evidence, and building a queue from the corpus

The editor's Speaker popup now carries the `identified_by` checkboxes, and this
is where the field earns its keep on data that predates it: **every group
annotated before 2026-08-03 has none**, so the only way to backfill the evidence
for the highest-risk population is to record it while reviewing anyway.

The rule the popup follows is worth stating, because it is not the obvious one.
`speaker` and `cap_colour` are **the call**, and `Confirm as is` still refuses if
either has been moved. `identified_by` is **evidence about** the call, and saying
what a call rested on does not contradict agreeing with it — so a confirmation
may record it. Ticking evidence therefore does not turn a confirmation into a
correction, and no `speaker_was` is written.

```bash
barks-ocr-speaker-queue --other --per-name 3 --out ~/barks-vision/other-audit.txt
barks-ocr-speaker-queue --title "Sheriff of Bullet Valley" --confidence low,medium
barks-ocr-speaker-queue --collective --unreviewed
barks-ocr-speaker-queue --missing-evidence      # everything read before v3
```

`barks-ocr-speaker-queue` builds a review queue from **what is already in the
corpus**, which `vision_apply --queue-speakers` cannot: that writes a queue as a
side effect of applying a run, and the five trial titles can no longer be applied
at all. It also **samples**, because the populations are lopsided — see the
`other:` audit below.

### The `other:` population, and why a flat audit of it would say little

Measured across the six annotated titles: **197 `other:` speaker calls, 22
distinct names**. Every error rate in this document is a *nephew* rate, and at
corpus scale `other:` is the larger population, since four of five trial titles
had an off-roster cast.

But the shape defeats a flat audit. **Sheriff is 132 of the 197**, and three
names — `Blacksnake McQuirt` (54), `Old Jim Diamond` (35), `the sheriff` (19) —
are 55% of the whole. Reviewing all 197 would spend most of the effort re-asking
*"is this Blacksnake or Old Jim?"*, a question Sheriff's own low/medium review
already answered: 1 wrong in 14, and the one error was exactly that confusion.

Sampling three per name covers **all 22 names in 53 groups**, and asks the
question that has no answer yet — which *kinds* of `other:` call are unreliable:

| kind | names | what can go wrong |
|---|---:|---|
| named one-off | 6 | simply the wrong character |
| unnamed role | 10 | drift into a neighbouring role |
| collective | 3 | little — a group attribution can hardly be misread |
| animal | 3 | the balloon / no-balloon convention |

The queue is grouped by kind with comment separators, so stopping after one kind
still leaves a complete answer for that kind rather than a random slice of
everything.

**This is the first audit that will record itself.** `speaker_was` landed the
same day, so its corrections carry the superseded call and its confirmations
carry only a date — where the pilot's 71%, the 5-in-50 audit and every other rate
here survive solely as diffs against a scratch directory.

#### The result: 1 wrong in 53, and `other:` is the safe population

Reviewed 2026-08-03. All 53 carry `speaker_reviewed` on disk, and the tally was
read back from the corpus rather than from a report — the first time that has
been possible.

| | | |
|---|---:|---|
| queued and reviewed | 53 | of 197 `other:` calls, all 22 names |
| **corrected** | **1 (1.9%)** | `047 g2`, Billions |

Read against the only comparable measurement — the 50-call audit of unreviewed
*high-confidence individual nephews*, which came back 5 wrong in 50 — **a free-form
speaker is about five times safer than a named nephew.** Both audits looked at a
population nobody had checked, rather than at a queue selected for doubt, so the
comparison is fair. That is the reassuring answer for corpus scale, where four of
five titles had an off-roster cast and `other:` is the dominant population.

The per-kind split is a *distribution of one error*, not four rates, and should
not be read as though it were:

| kind | reviewed | wrong |
|---|---:|---:|
| named one-off | 18 | 0 |
| unnamed role | 23 | 1 |
| collective | 9 | 0 |
| animal | 3 | 0 |

**The one error is not the failure mode this audit was designed around.** The
prediction was role-into-role drift — a posseman recorded as a townsman. Instead
it is an off-roster name given to a line a **lead character** speaks. Billions
`047` panel 3 carries two balloons, and the pass gave both to the washerwoman,
saying so in as many words: *"Both balloons in this panel are hers; Donald and
Scrooge are silent."* The plea is hers; `OH, ME! OH, MY!` is Donald's.

Two things follow, and the second is the more useful.

**A confident note is still not evidence.** This is the *Plenty of Pets* finding
again — "the tail comes down squarely onto the middle nephew", recorded with
false precision and wrong — in a population where nothing to do with caps or
nephews is involved. The pattern is not about colour or about nephews; it is
that the pass writes its conclusion in the same confident register whether or not
the art supports it.

**Short exclamations are where attribution is weakest.** `OH, ME! OH, MY!` is a
stock Barks interjection with no tail worth tracing, and it went wrong here. The
identical line appears on Big Bin `046 g20`, where it was recorded at **medium**
confidence precisely because nobody is drawn in the panel and only register
suggested Scrooge. The same phrase defeated attribution twice in one trial. A
rule worth considering before the corpus run: **a balloon of two or three words
with no tail on a figure is a low-confidence call whoever speaks it**, which is a
cheaper and more general guard than anything cap-specific.

#### The evidence, recorded on a second pass — and `costume` is the finding

The `identified_by` checkboxes went unused on the first run and were filled in on
a second: **52 of the 53**, with **zero consistency problems** — no unknown kind,
and no call citing `cap-colour` without a colour or the reverse.

`off-panel` (8 calls) proved correct everywhere it was used, which is worth
stating because a *collective* marked `off-panel` looks wrong at a glance. Each
one is a genuinely unseen speaker: the unboxed floating shouts on 082, the crowd
cheer whose tail runs off the panel edge on 083, Roscoe's holdup man whose tail
disappears into a black doorway, and the kitten that is "never drawn on this
page, only heard."

The distribution is the useful part:

| speaker kind | calls | resting on `costume` |
|---|---:|---:|
| unnamed role | 22 | **81%** |
| named one-off | 19 | 78% |
| collective | 9 | 22% |
| animal | 3 | 0% |

**For an unnamed role, costume is not corroboration — it is the identification.**
A policeman is a policeman because of the uniform; the washerwoman by her patched
dress; the doctor by the coat. Which lands the field exactly where it was aimed:
the population that rests most heavily on costume is the unnamed-role population,
and costume is the evidence class this trial found most fragile — Sheriff's
`168 g5`, the one confirmed colour-override error in five titles, is a
costume-based unnamed-role call. Those calls can now be pulled as a class and
checked together, which was impossible before the field existed.

`cap-colour` is used zero times here, correctly: every call in this audit is
`other:`, so no nephew and no cap is involved.

#### `speaker_review_note`, because a correction leaves a false note behind

The missing 53rd is the one call the audit **corrected**, and it exposed a gap
worth more than the tick it was missing. Its `vision_note` still reads:

> The washerwoman — a dog-faced woman in a patched blue dress and pink bonnet —
> on her knees. **Both balloons in this panel are hers; Donald and Scrooge are
> silent.**

The speaker now says `Donald`. Nothing supersedes `vision_note`, so **after a
correction it asserts something the data contradicts, in an authoritative
register**, and there was no field for the reviewer's own reasoning at all.

Added 2026-08-03: `speaker_review_note`, a second note rather than an edit of the
first. Overwriting `vision_note` would destroy the evidence of *how the pass went
wrong* — which is the raw material every finding in this document is made of, the
ambiguous tails and the 2x enlargements recorded in false precision. Both notes
are kept and `speaker_was` says which one the data agrees with. The editor also
marks a superseded note as such where it displays it, since a stale note read
unmarked is worse than no note.

It is offered on a confirmation as readily as on a correction: agreeing with a
call for a stated reason is worth more than agreeing silently.

143 `other:` calls remain unreviewed, and the corpus-wide `identified_by`
backfill is still outstanding — `--missing-evidence` returns 948.

### The collective audit: 0 errors in 47, and 9 recoverable identifications

Reviewed 2026-08-03, the last of the three populations. Sampled **per title
rather than per name**, because the collective is a single speaker value —
`--per-name` would have returned three groups — and the thing that varies is how
a title draws its caps.

```bash
barks-ocr-speaker-queue --collective --unreviewed --per-title 10
```

**Not one call is a real error.** Across 47 reviewed, `nephews` is never given to
somebody who is not a nephew. In the direction that matters the collective is
completely safe, which is what the rule was written to guarantee.

All 9 corrections are the *other* thing: `nephews` where the art did name one
after all. That is over-caution, not error — and it is **recoverable**, as this
review just demonstrated. The asymmetry the collective rule was built on
("a guess is unrecoverable, a collective is not") is therefore holding exactly as
designed, and 19% recoverable loss against 0% unrecoverable error is arguably the
correct operating point rather than a fault.

**The per-title sample earned itself**, because the result varies almost entirely
on the axis it was spread across:

| title | reviewed | over-caution | why |
|---|---:|---:|---|
| Sheriff of Bullet Valley | 10 | **6** | caps readable on many pages |
| Plenty of Pets | 11 | 2 | caps near-black with a small unreliable flash |
| The Big Bin on Killmotor Hill | 7 | 1 | mixed; several bare-headed panels |
| **Billions to Sneeze At** | 10 | **0** | nephews drawn **capless throughout** |

Billions returning zero is the control working: where the art gives no cap, the
collective is forced and cannot be over-used. Sheriff returning 6 in 10 is the
finding.

#### Three of the nine are the panel-wide colour rule over-firing

This is the actionable part, and it is visible in the data rather than inferred.
Sheriff's rule — *if two nephews in one panel show the same colour, or a cap
shows a non-roster colour, colour is not evidence **in that panel*** — was applied
panel-wide. In three of the corrected panels a **sibling group is still
`nephews`**:

| | corrected | siblings left as `nephews` |
|---|---|---|
| Sheriff `161` p4 | `g6` → Huey | `g5` |
| Sheriff `162` p1 | `g1` → Louie | `g0`, `g2` |
| Plenty of Pets `203` p7 | `g10` → Louie | `g8`, `g9` |

Two of those panels are the very ones this document lists as colourist slips. So
the mechanism is exact: **one nephew's cap was unreadable, and the rule discarded
colour for every nephew in the panel — including ones whose caps were perfectly
clear.** The reviewer could name one and not the others, which is precisely what
a per-cap rule would have produced in the first place.

**The fix is a narrowing, not a loosening**, and it costs nothing in safety:
apply "colour is not evidence" to *the caps that are actually ambiguous*, not to
the panel. The pilot's failure — naming a nephew whose cap could not be read —
stays refused, because that cap is still ambiguous. Worth doing before the corpus
run, since it is a reading rule rather than a schema change.

The other six are plain over-caution with no panel rule involved: a nephew alone
or nearly alone in frame, with a readable cap, called collectively anyway. One of
them (`038 g9`) is from this session's own Big Bin read, where the note recorded
"caps drawn near-solid black with only a small colour flash" and declined to
name — and the flash was red enough.

One reviewer note is worth quoting, because it marks the honest edge of the
finding. On Sheriff `144 g8`: *"The blue color is not really visible except by
zooming in. In a case like this 'nephews' would have been an acceptable answer."*
So of the nine, at least one is a judgement call rather than a clear miss.

### The collective backfill: 26% recovered, and the rule's evidence base does not survive

Backfilling evidence onto the collective produced **21 more corrections**, on top
of the audit's 9. Every one is again over-caution, and across **all 115
originally-collective calls now reviewed there is still not a single real
error** — the collective is never given to somebody who is not a nephew.

| | |
|---|---:|
| originally collective | 115 |
| moved to a name | **30 (26%)** |
| real errors | **0** |

**A quarter of the collective was recoverable**, and it concentrates on Sheriff
(17 of the 21) and *Plenty of Pets* (4), exactly as the per-title sample
predicted.

The sharper result is what happened to the panels this document cites as the
*reason* for the panel-wide rule. That passage reads:

> Barks — or the colourist — gives **two nephews the same colour in one panel** on
> 159 p7, 161 p4, 162 p1, 163 p1 and 163 p4, and twice paints a cap
> **orange-gold**, which is not a roster colour at all (161 p4, 162 p1).

All five are now fully resolved into individual names, with clean and *distinct*
roster colours:

| panel | now |
|---|---|
| 159 p7 | Dewey blue |
| 161 p4 | Dewey blue, Huey red |
| **162 p1** | Huey red, Louie green, Dewey blue |
| 163 p1 | Louie green, Huey red |
| 163 p4 | Louie green, Dewey blue |

No panel shows two nephews sharing a colour, and no orange-gold cap survives —
including on the two panels where it was specifically claimed.

#### One thing this does *not* settle, and it matters

Two readings disagree, and the data cannot arbitrate between them:

- the earlier session misread the colours, and the panel-wide rule was built on
  an observation that was not there; or
- **`cap_colour` was written from the convention rather than from the page.**

The second is a real risk and the recorded evidence cannot rule it out. Nearly
every one of these corrections carries `identified_by: [balloon-tail,
cap-colour]`. If the *tail* identified the nephew and the colour was then filled
in from the Huey-red/Dewey-blue/Louie-green convention, those are not two
independent pieces of evidence — they are one, with the second derived from the
answer. The field would then be recording a tautology, which is the same failure
the query set guards against by taking expected pages from the art rather than
from the capture records.

**Added 2026-08-03 as `observed-cap-colour`.** `cap_colour` records what is
*printed*, never what the convention implies once the nephew has been named some
other way — because deriving the evidence from the answer makes it a tautology
and removes the only check on the red/blue/green convention itself. A cap that
reads blue on a nephew the tail says is Huey is recorded blue, and **the
disagreement is the point**.

Fixing this required **relaxing the validator**, which had the tension backwards.
It used to reject a `cap_colour` recorded without `cap-colour` cited as
evidence — so a reader who saw a colour that did not support the call had to
either drop the observation or claim it as evidence anyway. The second is
precisely how those 30 calls came to cite a cap reading. That direction is now
allowed, and it is the most informative state the two fields can hold. The
reverse — citing `cap-colour` with no colour recorded — is still refused, since
identifying somebody by a colour nobody wrote down is incoherent.

Until the corpus is read under this rule, the five panels above are best read as
*one reviewer's reading against one earlier session's*, not as a refutation.
`capture_prompt_version` goes to **6**.

### The classification audit: 0 in 47, and the prediction was wrong

Reviewed 2026-08-03, the fourth and last population: the 156 `none` calls and 56
`narrator` calls, sampled eight per title across all six.

```bash
barks-ocr-speaker-queue --speaker none,narrator --unreviewed --per-title 8
```

**47 reviewed, zero corrections.** This was predicted to be the highest-yield
population left, on the reasoning that these are *classification* rather than
identification calls — "does a character make this noise?" is applied by
judgement on every sound effect, and the trial had already turned up several
where the answer was yes: Sheriff's `YEOWCH!` from a rider, *Plenty of Pets*'
`YEEK! YOWCH!` from the burglar, Big Bin's `ROOT SNORT` from Scrooge, the
nephews' `ZZZ`.

**The prediction was wrong, and the record already contained the reason.** Every
one of those cases was *caught during reading* and written up at the time. They
were caught because the test is easy once it is asked — not because it is hard.

### The evidence backfill found something else: the pass was using reading order

Backfilling `identified_by` onto the 108 individually-named nephew calls was
meant to be bookkeeping. It produced **11 speaker corrections, and every one of
them is in *The Victory Garden*** — none in Sheriff, *Plenty of Pets* or Big Bin.

GLK noticed the pattern first and proposed the cause: a very early Barks story
whose balloon tails are less precisely drawn than his later work. The data agrees,
and the pass's own notes say how the failure happened.

On `076` the three nephews come out as a **cyclic permutation**:

| | the pass | corrected to | cap actually |
|---|---|---|---|
| `g4` | Huey — *"rests on the cap-colour convention **plus balloon-tail order**"* | Louie | green |
| `g5` | Dewey — *"Blue-capped; **middle of the three-balloon chain**"* | Huey | red |
| `g6` | Louie — *"Green-capped; **last of the chain**"* | Dewey | blue |

And `084 g1`: *"Caps clearly readable at the counter — red, blue, green **left to
right**."* Corrected to green, red, blue.

**The pass was not tracing tails. It was assigning nephews by balloon order and
left-to-right position, and writing the result up as though it had read the
caps.** That is the confident-register failure again — the same shape as *Plenty
of Pets*' "the tail comes down squarely onto the middle nephew" and the
washerwoman's "both balloons in this panel are hers" — but with a specific
substitute heuristic now named.

It explains why only this title. In later Barks the tails are precise enough that
reading order and the true speaker usually coincide, so the heuristic agrees with
the art and is never caught. In a 1942 story they diverge, and every divergence
is an error.

The pass's own doubt tracks the same line. Tail-ambiguity language in nephew
notes, against the story's submission year:

| title | submitted | notes | tail doubt |
|---|---:|---:|---:|
| The Victory Garden | **1942** | 36 | **11%** |
| Sheriff of Bullet Valley | 1948 | 84 | 3% |
| Plenty of Pets | 1949 | 56 | 0% |
| Billions to Sneeze At | 1950 | 15 | 0% |
| The Big Bin on Killmotor Hill | 1951 | 15 | 0% |

**One caveat, and it is a real one: only one title in the trial predates 1948.**
So "early Barks" rests on a single story, and this could be that story's
lettering rather than the era's. What is *not* in doubt is the mechanism, because
the pass wrote down that it used balloon order — that is independent of how many
early titles were sampled.

**This also revises the pilot's 71%.** That figure is attributed above to the
absence of the collective rule, and 9 of its 10 errors were a named nephew that
should have been collective. The backfill shows a second cause underneath: even
where the pass named a specific nephew it had the *names in the wrong rotation*.
The collective rule fixed the symptom that was measured; the reading-order
substitution was never visible until evidence had to be recorded for each call.

**Added 2026-08-03 as `no-reading-order`**, and it is the same shape as the
per-cap fix: *balloon order and left-to-right position are not evidence.* If a
tail cannot be traced to a figure, the answer is the collective — which is what
`nephews` has always been for. It is rendered into `roster.txt` with the measured
finding attached, so the pass is told what went wrong rather than only what to
do.

Deliberately **not** a new `identified_by` kind: recording "reading order" as
legitimate evidence would license the thing that went wrong. There is no way to
say a call rested on position, and that is the point — a call that can only rest
on position is a collective.

Vols 1-5 are roughly 1942-47 and are where this will bite. `capture_prompt_version`
goes to **5**.

### Four audits, and they agree about where the risk is

| population | reviewed | wrong |
|---|---:|---:|
| named nephews, high band | 50 | **5 (10%)** |
| `other:` | 53 | 1 (1.9%) |
| collective | 47 | 0 errors (9 over-caution) |
| `none` / `narrator` | 47 | **0** |

Three of the four return essentially nothing, and the one that does not is the
one where the question is *which of several similar figures is this*. **Speaker
error lives in visual discrimination and almost nowhere else** — not in free-form
naming, not in the collective, not in classification. That is a more useful
result than any single rate, and it is the argument for stopping here: auditing
Donald's remaining 259 calls would test the easiest discrimination in the corpus
at five times the cost of anything above.

### The cost: the five read titles can no longer be re-applied

Making `identified_by` required means every `result.json` from the five-title
trial now fails validation, since none of them carries it. That is the same
state the pilot has been in since the collective-nephew rule went in, and it is
correct for the same reason: **those pages were read under v2's rules and saying
so is more useful than pretending otherwise.** The annotations already on disk
are untouched; only a re-apply would abort, and a re-apply would be wrong.

---

## The scorer's second generation

Built 2026-08-03, once all five titles were in and the deferred changes were
unblocked. Three of the four documented failure modes are lexical, so they went
first; the fourth needs embeddings and is still open.

**Both generations stay runnable.** `--matcher lexical` is what the trial was
scored with and is frozen; `--matcher v2` is the default. Replacing the old
matcher would have made every number above unverifiable the moment the scorer
moved on, which is precisely the failure the scorer exists to prevent — so
`--validate` carries one calibration per generation. `lexical` reproduces all
five titles byte for byte, checked as a regression rather than asserted.

| | lexical | v2 |
|---|---:|---:|
| hits | 81 | **85** |
| misses | 22 | **18** |

Five queries fixed, one lost:

- **#38 *sneezing*** and **#70 *hiding*** — the stemmer, exactly as predicted.
  Both are the silent-*e* case prefix matching cannot reach. #38 now returns all
  three expected pages and nothing else.
- **#79 *pants falling down*** — retrieved on `falling`/`fall`. The noun still
  misses, so the `trousers`/`pants` vocabulary gap is real and unfixed; the page
  comes back because the record describes the same event in the same words the
  query uses for everything except the garment.
- **#103 *flypaper*** — compound joining, against the art's own `FLY PAPER`.
- **#29 *a chase*** — IDF weighting, the nine-way tie.
- **#82 *smoking a pipe*** is the one lost, and it is the most interesting result
  of the four. Its `lexical` hit was **also** a tie artifact: seven pages tied at
  score 1.0 on the single token `pipe`, and alphabetical truncation happened to
  keep two correct ones. So one title produced a lucky hit and an unlucky miss by
  the same mechanism, and the fix that corrected #29 necessarily gave up #82.
  Counting it as a straight regression would be reading the tie as though it had
  been a judgement.

### Two mistakes worth recording, because both looked like successes

The first cut of `v2` scored **87**, and two of those hits were false.

**Compound joining polluted the index.** Pairs were formed across the whole
flattened field text, so unrelated neighbours fused into words the record never
contained — and because a compound sat in the ordinary token set, the *prefix*
rule then matched any word that started one. A query's `down` reached a junk join
beginning "down" and scored a page on nothing. That is what made **#11 *Scrooge
diving into his money bin*** appear fixed: the expected page came back without
matching `diving` at all, on generic tokens alone. The fix is two constraints —
compounds are formed **within one string**, and matched by **equality only**.
#11 is a miss again, correctly.

**The fuzzy rule's `hiding`/`riding` bug has a twin**: `diving` matches `driving`.
It scored a wrong page highly on the same query.

The lesson is not about either bug. It is that **a rise in the hit count is not
evidence the matcher improved** — every one of these changes makes hits easier,
so the count moves whether or not retrieval got better. What distinguishes them
is reading the per-token trace for each newly-hit query and asking which token
earned it. Both false hits looked exactly like the four real ones in the tally.

### The fuzzy rule, finally measured

The trial recorded a suspicion that `_within_one_edit` cost more than it earned
and asked for a measurement when the retriever was revisited. Under `v2` its
**only** effect across all five titles is **#91**, where it carries the query
set's own typo (`dumbells` against the record's `dumbbells`). Removing it changes
nothing else: 85 → 84 hits, and the difference is that one query.

So it neither earns its keep nor costs anything measurable any more. The stemmer
took over the morphology it was compensating for. It is kept because removing it
would lose a hit, but the honest description is that **it now exists to paper over
a typo in the query set**, and correcting `dumbells` in the query text would
retire it — which is a change to the pre-committed set, so it is left alone.

### What is left, and what could reach it

| | count | queries |
|---|---:|---|
| **semantic — an embedding could reach** | **12** | #93, #33, #34, #76, #51, #55, #57, #95, #11, #107, #111, #112 |
| *not recorded* — no retriever can reach | 5 | #35, #46, #26 (×2), #98 |
| ranking artifact | 1 | #82 |

The 12 are the reader-vocabulary vs drawn-vocabulary finding in full: *sick* for
"does not feel well", *sad* for "in tears", *pain* for `YEOWCH!`, *scared* for
"sweat drops flying", *colliding* for "knocks him off his feet", *love* for
hearts, *worry* for sobbing, *diving* for "throws himself off the catwalk", plus
three plain synonym pairs (*bag*/sack, *letterbox*/mailbox, *painting*/picture)
and #93's *hit*/swats.

**Nothing lexical will close any of them**, which is what makes the remaining
question a clean one: an embedding either reaches these 12 or the finding stands.

### `v3`: the dense retriever, and it reaches eight of the twelve

Added 2026-08-03. `--matcher v3` adds sentence embeddings
(`all-mpnet-base-v2` via `sentence-transformers`) alongside `v2`'s lexical rules.

| | lexical | v2 | **v3** |
|---|---:|---:|---:|
| hits of 103 | 81 | 85 | **93** |

**Eight of the twelve semantic misses close, and nothing regresses** — every
`v2` hit is still a hit, on every title. Fixed: #33 *sick*, #34 *sad*,
#46 *a sound effect*, #51 *colliding*, #57 *scared*, #76 *pain*,
#98 *an establishing shot*, #107 *love*.

Two are worth singling out. **#107 returns exactly `041` and nothing else** —
the page whose record says "three red hearts floating around his head", with no
lexical field matching at all. And **#46 returns exactly its three expected
pages**, which the trial had filed as *not recorded* because `visible_text` is
untyped and nothing says `KA-CHOO!` *is* a sound effect; the embedding reaches
the category without the field being typed. So does **#98**: "establishing shot"
is never written anywhere, but a wide scene-setting description is close enough
to the phrase. **Two of the four *not recorded* misses were only ever
lexically unrecorded** — the content was there, and that is a softer result than
the trial's "capture never records how a panel is framed".

Three design decisions, each made against a mistake:

- **A page is scored by its best-matching phrase, not by one page vector.**
  `objects` holds up to twelve unrelated noun phrases; averaging a fly swatter
  together with everything else matches nothing in particular.
- **The dense side must clear a sigma above its own title's spread** to propose a
  page at all. A cosine is never zero, so left unbounded it proposes a full band
  for every query — on a four-page title that returns three of four pages
  whatever was asked, and it collapsed the capture-only/speech-answerable split
  to **zero capture-only on Roscoe**. That split is one of the numbers the trial
  reports, so it matters more than the hit rate. The gate is relative to the
  query's own spread rather than a fixed cosine **because a fixed threshold would
  have to be picked by seeing which value let the expected pages through** — and
  the queries are the acceptance test. Nothing here is tuned against them.
- **It backfills; it never displaces.** Reciprocal rank fusion was tried first and
  rejected on evidence: giving both rankers equal say scored 95, but *lost* #43
  and #93, pushing correct lexical answers out of a full band. Backfill buys a
  property worth more than the two queries it forfeits — **a rise in the hit count
  can now only mean the dense retriever found a page the lexical one missed.**

That last point is the methodological lesson of this whole exercise, and it was
learnt twice. The first cut of `v2` scored 87 with two false hits; the first cut
of `v3` scored 95 with two real losses. **Both looked like improvements and both
needed a per-query trace to see through.** Every change here makes hits easier, so
the count moves whether or not retrieval got better.

#### What backfill costs, measured

Four of the ten remaining misses are *only* the no-displacement rule, and in each
the dense retriever **had the correct page** but the lexical band was already full
of wrong ones: **#82, #55, #95, #112**. Switching to fusion would take them and
give back #43 and #93. The residue, diagnosed:

| | count | queries |
|---|---:|---|
| band full — semantic had it, backfill could not fire | 4 | #82, #55, #95, #112 |
| band full — semantic proposed nothing | 1 | #11 |
| semantic proposed nothing or wrong pages | 3 | #93, #35, #111 |
| negation — unreachable by any retriever | 2 | #26 (×2) |

**#11 is the honest disappointment.** *Scrooge diving into his money bin* is the
query the design named in advance as the one that must not miss; `diving` against
"launching himself off the catwalk" embeds at **0.824**, the strongest similarity
measured anywhere in this work — and it still misses, because the lexical band is
full of three wrong pages and the gate rejected the rest of the title. The signal
is there and the band mechanics hide it.

**#111 *worry* is the one genuine semantic failure**, and it is instructive:
against "flat on his back on the floor, sobbing" it embeds at **0.119**, below
control pairs chosen to be unrelated (*a cannon* / "a bear trap", 0.199). So does
#76's *pain* against `YEOWCH!` at **0.079** — an interjection carries no meaning
the model knows, and #76 only hits by reaching a different phrase. The
reader-vocabulary finding is therefore **narrowed rather than overturned**: an
embedding closes the ones where the record describes the thing in words
(*sad*/"in tears", *sick*/"does not feel well"), and fails where the record is a
noise or a symbol.

---

## Open threads

- **The pilot's `result.json` no longer validates**, and correctly so: it names
  individual nephews at `low` confidence on four groups, which is exactly the
  pattern the collective rule was added to refuse. Re-applying that directory
  therefore aborts. Leave it — rewriting those calls would erase the evidence the
  rule was derived from. It does mean the pilot can no longer be re-applied
  without a re-read.
- **4 of the pilot's 18 speaker calls are still unjudged** — 077 g11/g12 and 085
  g10/g12, all genuinely unreadable. They keep `low` and no `speaker_reviewed`
  flag, which is the correct state for them, not a gap to close.
- **`other:crows` is at 17 uses and above the promotion threshold**, but all 17
  come from one story where crows are the antagonists. The threshold was meant
  for names recurring *across* stories, so this waits for corpus evidence — and
  is a hint the census could weight by how many titles a name appears in.
- **The pilot's `type: thought` mislabels are unfixed** — 079 g16, 080 g6, 080 g7
  are recorded in `vision_note` only. Roscoe adds 12 more in the other direction,
  plus `177 g3`, which is two separate letters in one group.
- **No retrieval engine exists** — but the *scorer* is no longer a variable.
  `barks-ocr-retrieval-score` was written for trial 2 and calibrated until it
  reproduced trial 1 exactly; `--validate` re-runs Roscoe and exits non-zero if
  the result is not 15 / 1 / #93. Score every future title with it, and treat a
  validate failure as "these numbers are not comparable" rather than as a bug to
  work around. Its one known divergence is recorded in the module: it credits
  Roscoe's #16 to the speech layer, where the trial-1 write-up credited capture,
  because 176's dialogue happens to call Roscoe "a strong, alert HELPER".
- **Lexical retrieval, not the schema, is the binding constraint — now settled.**
  Trial 1 had one recorded-but-unreachable miss (#93 *hit* vs *swats*). Trial 2
  had four of six, including a story named *Billions to Sneeze At* missing "a
  character that is sneezing" over `sneeze` vs `sneezing`. **Trial 3 is four of
  four**: not one Sheriff miss is *not recorded*. Three failure modes are now
  documented — morphology (`hide`/`hiding`, the silent *e*, identical to
  `sneeze`/`sneezing`), reader-vocabulary vs drawn-vocabulary (*pain* vs
  `YEOWCH!`, the third instance after *sick* and *sad*), and tie-truncation. A
  stemmer fixes the first, embeddings the second, a ranking change the third.
  Changing the scorer mid-trial is exactly what the bullet above exists to
  prevent, so all three wait for the end of the five titles and are then applied
  to every title at once.
  **The five titles are now in (trial 5, 2026-08-03), so that wait is over.**
  The scored tally across all five is **81 hits / 22 misses** (Roscoe 15/1,
  Billions 12/6, Sheriff 26/4, Plenty of Pets 11/4, Big Bin 17/7), of which
  **18 are *not retrieved* and 4 are *not recorded*** — the four being Billions'
  #35 *smiling* and #46 *a sound effect*, and Big Bin's #26 and #98, which are one
  gap counted twice (shot type is never written down). Not one is thinness in a
  field the queries were built to test.
  Trial 5 adds a **fourth** failure mode to the three above:
  **compounding** (`flypaper` against the comic's own `FLY PAPER`), which neither
  a stemmer nor an embedding over unigrams closes — a bigram index would.
  So the priority is now evidenced rather than guessed: the stemmer is cheapest
  and fixes fewest, tie-ranking matters more the longer the title, and
  **embeddings are what the bulk of the residue needs** — seven
  reader-vocabulary instances plus #11, the query the design named in advance as
  the one that must not miss.

  **Done, for the three lexical fixes, on 2026-08-03** — see *The scorer's second
  generation* below. `81 hits → 85`. What is left is the embeddings question,
  now with a number on it: **12 of the 18 remaining misses are semantic**, 5 are
  *not recorded* and so unreachable by any retriever, and 1 is a ranking artifact.
- **The matcher's fuzzy rule buys false positives.** `_within_one_edit` matches
  **`hiding` to `riding`** — which in a western is on nearly every page. It gave
  Sheriff's #70 a spurious score on 165 and still missed the two pages that
  actually record the hiding. Worth measuring the fuzzy rule's precision when the
  retriever is revisited; it may cost more than it earns.
- **Capture can drift away from the comic's own vocabulary.** Sheriff's #79 miss
  is `trousers` in the capture against `pants` in the query *and in the dialogue
  on the same page*. Roscoe found free text drifting **within** a title; this is
  drifting **away from the source**, it is more avoidable, and the rule is simply
  **prefer the comic's own word for a thing it names**. Not yet a validator, but
  it could be one: a capture noun that has a synonym in the same page's `ai_text`
  is a smell.
- ~~**The pass under-reads silent background business.**~~ Roscoe query #85 missed
  a full-panel electrocution gag because the panel's balloon was about something
  else. It did **not** recur on *Billions to Sneeze At* and did **not** recur on
  *Sheriff of Bullet Valley*, where the jackrabbits watching car 313 (155 p3), the
  buzzards over the knocked-out Donald (171 p2), the bluebird on the revolver
  (175 p3) and the brand changing on the horse between 156 p5 and 156 p8 were all
  caught on the first read. **One instance against two non-instances**: treat
  Roscoe's #85 as a one-off rather than a standing weakness, and do not change the
  prompt for it.
- **Measurement 3 is effectively answered, but not the way it was posed.** Three
  titles have now produced 0, 0 and **2** `--queue-speakers` entries. Two is not
  an error rate. But Sheriff explains the emptiness rather than merely repeating
  it: the collective rule added after the pilot means an unreadable cap yields
  `nephews` at `high`, so the low-confidence population the pilot measured cannot
  form any more. The `low,medium` run has since been done — **14 entries, 9 of
  them adults**, the reverse of the pilot's all-nephew population — and reviewed:
  **1 wrong in 14 (7%), against the pilot's 10 in 14 (71%)**. Measurement 3 is
  answered. The one error is adult-identity-by-costume-colour, the class named in
  the bullet below.
- ~~**A confirmed speaker call is not recorded, so the denominator is not
  self-evidencing.**~~ **Fixed 2026-08-03** by the editor's **Confirm as is**
  button, added before the *Plenty of Pets* queue was reviewed — see the editor
  section. It stamps `speaker_reviewed` and `high` confidence without touching
  `speaker` or `cap_colour`, and refuses if the popup selection has been edited.
  **The two runs already done are not retrofitted**: Sheriff's 13 confirmations
  still rest on GLK's report and the pilot's four unjudgeable entries still carry
  no flag, because stamping them now would record a review that did not happen
  the way the data would then claim. From *Plenty of Pets* onward the denominator
  is readable off disk.
- **The speaker risk has moved from nephews to adults, and nothing supports
  adults.** Sheriff's `low,medium` queue is dominated by the sheriff / Old Jim /
  posseman / Double X rider set, who are distinguishable only by hat and shirt
  colour, and it concentrates on the one night-and-indoors page (168 gives 5 of
  14) where Barks draws them hatless or in silhouette. Two things make nephews
  tractable and neither has an adult analogue: `cap_colour` records the evidence
  and keeps a call reversible, and `nephews` is a collective that loses almost
  nothing. The adult fallback is `unknown`, which loses everything. Worth
  considering a general `identified_by` note or an adult-collective convention
  before a title with a big supporting cast is run at scale.
- ~~**`setting` is one value per page and four of Billions' ten pages have two.**~~
  **Settled by Sheriff**: at least 8 of its 32 pages cut between two locations, so
  it is a Barks structure rather than a ten-page coincidence. The field is lossy on
  roughly a quarter to a third of pages corpus-wide. The lost value survives in
  `objects`, `beats` and `panels_of_note` and retrieval still works, so this is a
  known limitation rather than a pending change.
- **Retrieval now fails on title *length*, which is new.** Sheriff's #29 miss is
  not a vocabulary problem: nine pages tie at the top score and `TOP_BAND = 3`
  truncates the tie **alphabetically**, dropping both correct pages. 4 and 10-page
  titles could not generate ties that deep. Any fix to the retriever has to
  address ranking-under-ties, not just matching — and like every other scorer
  change it waits until all five titles are in.
- **The census should distinguish roles from names.** Sheriff puts four names over
  the promotion threshold, and three of them (`Blacksnake McQuirt`,
  `Old Jim Diamond`, `Double X rider`) are single-story, exactly like
  `other:crows`. The fourth, **`other:the sheriff`, is a role rather than a name**
  and plausibly recurs across the corpus — the first genuine promotion candidate
  the census has produced. Weighting by how many titles a name appears in would
  separate all four correctly. *Plenty of Pets* adds a fourth single-story name
  over the threshold (`other:the Black Mask Burglar`, 11) and a genuine role
  below it (`other:the policeman`, 2), which is the same argument again: the
  threshold is measuring the wrong thing.
- **The residual speaker error is balloon-tail tracing, not colour.** *Plenty of
  Pets* came back 2 wrong in 6 and **both** are the pass picking the wrong figure
  in a multi-nephew panel; the cap it then read was correct each time. Colour
  handling therefore needs no change on this evidence, and *Sheriff*'s `168 g5`
  is still the only confirmed colour-override error in the trial. Two things
  follow. **Enlarging does not fix it** — both panels were magnified 2x
  specifically to trace those tails, and both notes record the wrong trace in
  confident language. And the collective rule may want a second trigger: not just
  "the cap cannot be read" but **"several balloons converge over adjacent
  nephews"**, where `nephews` is the honest answer however legible the caps are.
  Not worth writing until the audit below says how common this is.
- ~~**50 high-confidence individual-nephew calls have never been reviewed.**~~
  **Done 2026-08-03: 5 wrong in 50 (10%)**, and the answer inverted the guess that
  motivated it. Crowded panels are *safe* (1 in 33); a nephew speaking alone in a
  panel is not (4 in 17, 24%), because a lone cap is read against no reference.
  All four swaps involve blue and three are blue↔green. `--queue-speakers` now
  covers that configuration. **The high band is 10% wrong, which is the more
  general finding**: every other error rate in this document comes from the ~4% of
  groups that get queued, so the same question is open for `other:` speakers and
  for the collective, neither of which has ever been audited.
  **Both were audited 2026-08-03 and the question is now closed.** `other:` came
  back **1 wrong in 53 (1.9%)** against the nephew high band's 5 in 50 — a
  free-form speaker is roughly five times safer than a named nephew, which is the
  good news for corpus scale since `other:` is the larger population there. The
  **collective came back 0 errors in 47**: it is never given to a non-nephew.
  Its 9 corrections are all over-caution, and 3 of those are the panel-wide
  colour rule suppressing readable caps alongside unreadable ones.
- ~~**The panel-wide colour rule is too blunt.**~~ **Fixed 2026-08-03, and the
  root cause was worse than the rule.** Going to change it revealed that the rule
  **was never in `roster.txt` at all** — it existed only as prose in this document
  describing what one session had done, so every later session had to read that
  and re-derive it. The panel-wide form it kept being re-derived in cost 9
  identifications, 3 of them a clear cap suppressed by an unreadable one beside
  it. It is now rendered into `roster.txt` from `vision_schema.py` in its
  per-cap form: judge each cap on its own, and a nephew beside an unreadable cap
  is still nameable if his own is plainly red. The guard the rule exists for is
  untouched — a nephew whose *own* cap cannot be read still cannot be named, so
  the pilot's failure stays refused.
  This is the document's own lesson landing on the document: **a rule a generator
  cannot read is a rule a generator will break.** Two rules had already been moved
  into `roster.txt` for exactly this reason; this one was missed because it read
  like a finding rather than an instruction.
- **Blue is over-called, not most legible.** *Sheriff* concluded blue was the most
  readable cap because it was recorded most often (19 of 37). The audit says the
  opposite: blue is where the errors are. Worth a line in `roster.txt` warning
  that green in shadow prints close to blue on the restored colour — though the
  pilot's lesson is that a rule the model is told and then breaks needs a
  validator, which is why the queue rule went in as well as any prose.
  **Trial 5 adds the first two confirmed blue/green lone-panel calls** — `040 g3`
  Dewey on blue and `044 g9` Louie on green, both reviewed and both right. They do
  not overturn the audit, but they share a property the audit's four swaps did
  not: in each, a second cap of a different colour is in the same panel to read
  against. That is consistent with the audit's own explanation — a lone cap is
  read against nothing — and suggests the risky case is narrower than "an
  individual nephew alone in a panel". Worth checking on the next title whether
  the queue rule can ask for *no other cap in frame* rather than *no other nephew
  speaking*, which is a different and smaller population.
- **A within-panel colour-consistency validator was tried and rejected.** Two
  nephews sharing a `cap_colour` in one panel, or one nephew carrying two, finds
  **zero** contradictions across all 867 annotated groups and catches neither
  known error. Recorded so it is not re-proposed.
- **The engines must be mirrored, or the pass fights the reconciliation.** Handled
  2026-08-03 — see the mirroring section. Left open: **5 line-break differences
  and 4 word differences on Roscoe** that the mirror would not cross, which are
  real reconciliation work rather than tool failures.
- ~~**The `identified_by` idea now has three distinct callers, not one.**~~
  **Built 2026-08-03, before the corpus run** — see *Three changes with a
  deadline* below. It is a required list wherever somebody speaks, closed with no
  `other:` escape, because the point is to make calls *comparable* and free text
  cannot be counted. Two cross-checks come free: a `cap_colour` was read but the
  call does not claim to rest on it, or the reverse.
- **The `identified_by` idea now has three distinct callers, not one.** Sheriff
  wanted it for adults identified by hat colour with nothing to record it.
  *Plenty of Pets* adds two more: eleven `high`-confidence calls made from
  **pyjama and shirt colour** (204 panels 4-5, 208 panels 2, 3, 5), which
  `cap_colour` cannot hold, and one made from **the previous balloon** (208 g20,
  named by the line before it). One field naming the evidence would cover cap,
  costume, hat and dialogue alike, and would make a call reversible the way
  `cap_colour` already makes a nephew call reversible.
- **Sheriff's adult-identity error class did not recur, and the reason narrows
  it.** *Plenty of Pets* was the natural test — it is built on unnamed adult
  roles (#47 policeman, #54 burglar) — and produced none of it, because the story
  has only **two adults and they never share a panel**. The failure needs two or
  more similar-looking figures separated only by costume colour, so the class is
  better stated as **a large similar-looking supporting cast** than as "unnamed
  adult roles". **Big Bin was named as the next place to look and cannot answer
  either**, for a third structural reason: its four Beagle Boys are drawn as a
  set of near-identical masked figures — precisely the configuration — but they
  **never speak**. Not one balloon in the story is theirs, so no attribution is
  ever demanded of them. Three titles have now failed to reproduce Sheriff's error
  class for three different reasons (one lead; two adults who never share a panel;
  a similar-looking group that is silent), which is itself worth knowing: the
  failure needs a large similar-looking cast that also *talks*, and that is rarer
  than a large similar-looking cast.
- **Emotion's retrieval failure is now reproduced, not observed once.** Billions
  found #34 *sad* recorded as "in tears" and unreachable; *Plenty of Pets* finds
  #57 *scared* recorded as "sweat drops flying" and "backed into the corner", and
  unreachable in the same way. Two titles, two emotions, same result. Combined
  with *sick* and *pain*, **reader-vocabulary vs drawn-vocabulary is now the
  trial's single most repeated finding at five instances**, and the argument for
  embeddings rather than for any schema change. **Trial 5 adds *love* (recorded as
  `hearts`) and *worry* (recorded as "sobbing"), taking it to seven** — and, more
  pointedly, adds **#11 *Scrooge diving into his money bin***, the one query the
  design doc singled out in advance with *"if capture misses this, it fails"*. It
  misses on `diving` against a record that says "throws himself off the catwalk
  into the coins" and "launching himself off the catwalk, hat and spectacles
  flying". Nothing about that record is deficient, which makes it the cleanest
  embeddings argument the trial has produced.
- **A third free-text vocabulary class, and this one has no rule.** Roscoe found
  drift *within* a title, Sheriff found drift *away from the source* (`trousers`
  vs the comic's own `pants`). *Plenty of Pets* #95 is neither: the query says
  *letterbox*, the record says *mailbox*, both are correct, and **the comic never
  names the object**, so "prefer the comic's own word" cannot arbitrate. It was
  recorded as `mailbox` deliberately and allowed to miss rather than writing both
  words to manufacture a hit. Nothing but semantic retrieval fixes this one.
- **`max(panel_num) > len(panel_boxes)` would be a cheap mechanical check.**
  *Plenty of Pets* 199 has a **page-wide** panel_num shift — every group but two
  stored one panel too high, with two groups claiming a panel 8 the page does not
  have — apparently because the grouping pass counted the splash's title logo and
  its art as two panels. Previous titles produced single mis-numbered groups
  (Billions 048 g3/g4, Sheriff 150 g9, 165 g4); this is the same class at page
  scale, on a splash, and unlike the others it is detectable without looking at
  the art.
- **The drawn punctuation device has no consistent type, and trial 5 found a
  fourth.** `045 g8` types three exclamation marks around Scrooge's head as
  `sound_effect`, and `046 g18` gives a drawn `?` no group at all. With the two
  below that is four treatments across two titles for a device that makes no
  sound in any of them.
- **The drawn `?` device has no consistent type.** `205 g9` is `background`,
  `207 g12` is `sound_effect`, and the three on `208 panel 5` have no group at
  all. It makes no sound in any of them. Small, but it is the kind of thing a
  category query over `type` would trip on.
- ~~**The pre-read name grep needs to print the whole distribution.**~~
  **Done on trial 5, and it is now a tool rather than a discipline:**

  ```bash
  barks-ocr-name-grep --title "The Big Bin on Killmotor Hill"
  barks-ocr-name-grep --volume 11 --min-pair 3
  ```

  It runs **two passes, because they fail in opposite ways and neither alone is
  enough**, which is the finding trial 5 produced.

  *Pass 1, non-dictionary tokens.* `/usr/share/dict/american-english` and
  `british-english` as the stop list, printing **every** surviving token rather
  than a frequency head and tail. A dictionary has no cutoff to fall through, so
  the gap that lost `Yehooty` (3 occurrences: too rare for the head, too common
  for the tail) cannot reopen. The output stays readable — Big Bin leaves 18
  tokens from 451 distinct, Roscoe 7 from 226.

  *Pass 2, repeated word pairs.* **A name spelled out of ordinary words is
  invisible to a dictionary filter**, and Big Bin's antagonists are exactly that:
  `BEAGLE` and `BOYS` are both dictionary words, so pass 1 returned *nothing at
  all* for the story's entire villain cast. This is the mirror of the Yehooty gap
  — that one was too rare, this one too *ordinary*. Casing cannot rescue it since
  the lettering is stored in caps. Adjacent pairs can, and immediately give
  `BEAGLE BOYS` (13, five pages), `MONEY BIN`, `UNCLE SCROOGE`, plus *Plenty of
  Pets*' `BLACK MASK` / `MASK BURGLAR` and Roscoe's `GYRO GEARLOOSE`.

  Pass 2 pays a second time by surfacing **the comic's own wording** for things
  the story names, which is what capture is meant to reuse: `FLY PAPER` and
  `PERISCOPE PEEPHOLE` both came out of it. (Trial 5's #103 shows that cuts both
  ways — see the compounding bullet below.)

  Two implementation notes worth not rediscovering. The **dictionary is the only
  stop list** for pass 1; comic interjections survive as noise, deliberately,
  because every hand-written stop entry is a chance to hide a name. And the scan
  is restricted to the pages the title **really owns** via the shared
  `title_pages`, since the page map reaches into the stories around it — an
  unfiltered run reports *Sheriff of Bullet Valley* as 35 pages and mixes three
  other stories' names into its list.

  Note what the grep still cannot buy: on *Plenty of Pets* it surfaced
  `JASMINE JOE` but not *which animal that is*, which only page 204 settled. It
  buys the spelling, not the identification.
- **`panel_boxes` can merge two drawn panels into one box.** Trial 5's `047`
  panel 1 spans the ice-cube view *and* the bordered caption panel beside it, so
  three groups carry a `panel_num` that is right for the box and wrong for the
  page. Every previous panel defect in the trial was a stored `panel_num` against
  a correct box, which the editor can fix; this one cannot be fixed there at all,
  and `max(panel_num) > len(panel_boxes)` cannot see it either. The one cheap
  signal available is that a merged box is roughly double the area of its
  neighbours — which is why the 500KB crop assertion caught it. Worth a check that
  flags a panel box far larger than its page's median.
- **Following "prefer the comic's own word" can itself cause a miss.** Trial 5's
  #103 asks for *flypaper*; the art letters `FLY PAPER` and the record says
  `fly paper`, so the query misses **because the rule was obeyed**. This is a
  fourth vocabulary class — **compounding** — and unlike the other three neither a
  stemmer nor care about wording fixes it, since the split is in tokenisation. A
  retriever that indexes bigrams as well as tokens would close it; nothing in the
  writing discipline can.
- **Capture never records how a panel is framed.** Trial 5's #98 and #26 are the
  first *not-recorded* misses in three titles, and both ask for a shot type. The
  pages are described richly and the words *establishing shot*, *close-up*, *wide*
  appear nowhere in five titles of capture. `panels_of_note` is free text and could
  carry framing vocabulary at no schema cost, so this argues for guidance in
  `roster.txt` rather than a new field — but it is a genuine hole, and it is the
  only one the five-title trial found in the schema itself.
- **`visible_text` is untyped, so category queries over it cannot be answered.**
  Query #46 *a sound effect* misses on a page holding `SMACK!`, `KA-CHOO!` and
  `AH-CHOO!`, because nothing records that those strings are sound effects. First
  query to want the field typed; not worth a schema change on one instance.
  Sheriff does not press the case either way — it captures 23 sound-effect strings
  but the query set does not ask #46 of it.
- **The `type` error rate should be tracked as two rates, not one.** Trial 5 has
  **1 of 133 (0.75%)** thought-cloud-typed-`dialogue`, the lowest of the five, and
  separately `043 g5` `YOICKS!` typed `sound_effect` inside a proper balloon with a
  tail. A thought/dialogue confusion and a dialogue/sound-effect confusion have
  nothing to do with each other and averaging them into one percentage hides both.
  Across five titles the thought/dialogue axis is ~0.75-2.9% (ignoring Roscoe's
  premise-inflated 27%) and bidirectional; the balloon/sound-effect axis has now
  appeared on three titles (Sheriff `174 g4`, *Plenty of Pets* `206 g6`, Big Bin
  `043 g5`) and has never been counted at all.
- **The `type` field's corpus error rate is now estimable: ~1.7%, one-directional.**
  Sheriff has 7 thought-clouds-typed-`dialogue` in 407 groups and no errors the
  other way, against Billions' 2.9% on 136 and Roscoe's premise-inflated 27%. Only
  the pilot ever erred in the other direction. The mislabels across all four runs
  are still recorded in `vision_note` only and none has been fixed.
- **`170 g9` shows the OCR transcribing one name two ways inside one story** —
  `McQUIRT` there against `MCQUIRT` on 149, 150 and 169, for identical art. Not a
  correction under the case rule, but a `string_replacer` candidate if the corpus
  ever wants one spelling.
- **24 pages have no prelim OCR at all** — see below. The tools no longer trip over
  them, but the OCR still needs to be run.
- **One-pagers cannot be prepped at all.** All 155 `ONE_PAGERS` fail to resolve —
  128 `TitleNotFoundError`, 27 `KeyError` — because they have no `.ini`, and no
  one-pager OCR exists in the corpus under any title. This is why the trial has
  no one-pager unit. Whether they are ever worth capturing is open; they would
  need OCR first, and then a way to address them that is not a story title.
- ~~**136 pages of OCR are unreachable, all in vol 2.**~~ **Fixed 2026-08-02** by
  regenerating vol 2's panel segments. The staleness guard had been firing
  correctly — the restored PNGs were rebuilt after the panel segments — and
  aborted twelve vol-2 stories with

  > `Panels segments info file ".../Frozen Gold/031.json" is older than srce image file ".../images/031.png"`

  All **5,358** easyocr prelim pages are now reachable through a title, up from
  5,222, and **no title aborts** across the 450 configured in vols 1-29.
  `barks-ocr-vision-prep --title "Kite Weather"` prepares 10 pages / 58 panels
  cleanly, and a whole-corpus `barks-ocr-speech-script` run closes with only the
  24 genuinely-missing-OCR pages below.
- **Two database accessors disagree about story ownership.** The comic page map
  can claim pages belonging to neighbouring stories — *Sheriff of Bullet Valley*
  comes back with 103, 176 and 177 on top of its real 144-175.
  `vision_prep._title_pages` now keeps only pages both accessors agree on and
  names the rest in a warning, but the underlying disagreement is unfixed, and
  anything else walking the page map will hit it too.

---

## Missing prelim OCR files

`barks-ocr-check --volume N` used to abort on the first absent prelim JSON, taking
the whole volume with it. `_get_speech_text_list` wrapped every read failure —
including a plain `FileNotFoundError` — in a `ValueError`. Fixed 2026-08-01.

A survey of vols 1–29 (445 titles) split the absent files cleanly in two, and the
two halves want opposite treatment.

**Reprinted one-pagers — ignore, silently.** Vol 1's `All One-Pagers` pages
500-627 are one-pagers collected from other volumes. Their source images are
symlinks in `Fantagraphics-fixes-and-additions/.../images` pointing at the
original volume's page, which is where the OCR lives. They are not this title's
OCR work and never were, so they are no longer offered as pages at all —
`_get_srce_page_to_dest_page_map` drops them unconditionally, for every caller.

The test is `ComicBook.get_srce_original_fixes_story_file(page).is_symlink()`.
Check the **fixes** source, not the restored image: 21 of the 128 have a real
restored PNG and would slip through. Across all 445 titles the predicate matches
those 128 pages, none of which has OCR, and no page that does.

**Genuinely missing OCR — skip, loudly, and only where asked.** 24 pages:

| Vol | Title | Pages |
|---|---|---|
| 8 | Letter to Santa | 078 |
| 9 | Donald's Grandma Duck | 096-109 |
| 9 | Camp Counselor | 110-117 |
| 20 | The Mines of King Solomon | 035 |

These are defects to fix, so they stay loud. `get_speech_page_groups` takes
`skip_missing`, **default `False`** — the abort is still the default everywhere.
`ocr_check`, `compare`, `annotate`, `florence_check`, `vision_prep` and
`vision_apply` opt in and log a warning per file; `whoosh_index` and
`string_replacer` deliberately do not, since a silent hole there means an
incomplete search index or a half-applied bulk edit.

Only an *absent* file is tolerated. A malformed one still raises, under
`skip_missing` too.

`ocr_check` closes with the roll-call, so the defects do not live only in the log:

```
Missing prelim OCR — 1 page(s), OCR never ran on these:
  Vol  8  Letter to Santa: 078
```

They are **not** written to the queue file — there is nothing for the editor to
open. Re-run `barks-ocr-check --volume 8 9 20` after any OCR backfill; the block
disappears when the list is empty.

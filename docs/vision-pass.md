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
barks-ocr-vision-prep  --title "The Victory Garden"    # crop, queue, roster.txt
   <Claude Code reads roster.txt + the crops, writes result.json per page>
barks-ocr-vision-report --out-dir ~/barks-vision/the-victory-garden
barks-ocr-vision-apply  --out-dir ~/barks-vision/the-victory-garden \
    --queue-out review.txt --queue-speakers speakers.txt
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

---

## Schema

Written onto each group in the prelim JSON by `vision_apply`:

| key | values |
|---|---|
| `speaker` | roster name, `narrator`, `none`, `unknown`, or `other:<free text>` |
| | roster: Donald, Huey, Dewey, Louie, `nephews`, Daisy, Gladstone, Scrooge, Gyro |
| `speaker_confidence` | `high` / `medium` / `low` |
| `speaker_reviewed` | `true` once a human has confirmed the speaker in the editor |
| `cap_colour` | `red` / `blue` / `green`, or `null` when not visible |
| `emphasis_spans` | `[[start, end, "bold"], …]` — char offsets into the **current** `ai_text` |
| `vision_note` | the reasoning behind the call |
| `vision_text_ok` | `false` when the art disagrees with `ai_text` |
| `vision_corrected_text` | the reading from the art |

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
| `capture_model`, `capture_prompt_version`, `captured` | provenance |

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
| `VERBATIM` | text copied out of the comic, or inseparable from it | `ai_text`, `visible_text`, `emphasis_spans`, `vision_corrected_text` |

`classify()` **raises on any field not in the table** rather than defaulting. A
field nobody has classified must stop an export, because guessing permissively
publishes someone else's copyright. Each written capture record also stamps its
own fields with their class, so an exporter never has to look it up elsewhere —
and cannot quietly stop looking.

`emphasis_spans` is offsets rather than text, but it is meaningless apart from
the `ai_text` it indexes and encodes the shape of it, so it is classed with the
text it belongs to.

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

- **`ai_text` is never modified.** Corrections go to a kivy-editor queue for review.
  Saves use `save_json(backup_file=...)`, unlike `ocr_check`'s bare `save_json()`.
- **Publication class lives in the data**, not in this document. See above.
- **`setting` and `time_of_day` are separate fields.** Folded together, every
  place would need a value per lighting condition. And the pilot showed time of
  day carries its own signal: the unreadable cap colours on 079 are unreadable
  *because* it is a night scene, so recording it explains a low-confidence
  cluster rather than merely observing one.
- **Spans, not inline markup.** Inline `**bold**` would break
  `whoosh_index.check_capitalization_map`, perturb `ocr_check`'s width-fit and
  line-height heuristics, invalidate cached `florence_passed` entries, and render
  literally in reader search results. 139 groups also already contain a `*` used as
  a footnote marker, so `*` cannot mean emphasis.
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

## Reviewing the speaker calls in the editor

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

The pane header carries `[spkr: <name>]` once a group has one, so the queue can
be walked without opening the popup on every entry.

---

## Pilot results — Vol. 1, pages 076-085

10 pages, 55 panels, 134 groups.

| | |
|---|---|
| `vision_text_ok: false` | 2 (1.5%) |
| bold spans | 5 |
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

| title | vol | pages | queries | DB cast |
|---|---|---:|---:|---|
| **Sheriff of Bullet Valley** | 6 | 144-175 (32) | ~23 | none |
| **Billions to Sneeze At** | 10 | 044-053 (10) | ~14 | none |
| **Plenty of Pets** | 7 | 199-208 (10) | ~13 | none |
| **Roscoe the Robot** | 20 | 175-178 (4) | ~13 | none |
| **The Big Bin on Killmotor Hill** | 11 | 10 | ~19 | **The Beagle Boys** |

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
| bold spans | 20 across 44 groups (**45%**, against the pilot's 3.7%) |
| confidence | high 44 / medium 0 / low 0 |
| `cap_colour` non-null | 0 |

**The correction rate holds.** One in 44, and it is a real defect: `175 g12`
`ELECTRIC RULES` → `ELECTRIC BULBS`, hand-scrawled on the crate the Little Helper
is loading a spare bulb into. Queued in `~/barks-vision/roscoe-review.txt`. At
2.3% against 1.5% on a 44-group sample the pass is reading, not inventing.

### Bold density is a property of the series, not of the corpus

20 spans where the pilot found 5 — twelve times the rate. The Gyro Gearloose
stories letter emphasis constantly; *The Victory Garden* (1943) almost never
does. **So the pilot's 5 is not a corpus baseline**, and neither is this. Two of
the twenty are single characters — the lone `I` in "this is where **I** wanted to
hide" — which is the case inline markup would have handled worst.

### Measurement 3 is untestable on this title, and that is structural

All 44 calls are `high`; `--queue-speakers` wrote **zero** entries. Gyro is the
only duck in the story, so there is no cap to read and no nephew to confuse. A
one-lead story cannot exercise the low-confidence path at all — the remaining
four titles have to carry that measurement alone.

### Retrieval: 15 of 16, but only 11 the vision pass earned

Scored by keyword search over the capture records, so every hit is attributable
to a field. 12 Roscoe-specific queries plus 4 that any title can answer (#16,
#30, #43, #96).

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

## Open threads

- **1 queued Roscoe correction is unapplied.** `~/barks-vision/roscoe-review.txt`.
  `175 g12` (`ELECTRIC RULES` → `ELECTRIC BULBS`) is solid; it needs a pass
  through the kivy editor like any other queued correction.
- **2 queued corrections are unapplied.** `~/barks-vision/vol01-vision-review.txt`.
  `077 g1` (`YOU — YOU` → `YOU-YOU`) is solid — and is visible in context in the
  speech script. `085 g7` (`INVISIBLE SEEDS,` → `INVISIBLE, SEEDS,`) is explicitly
  low-confidence: the stored reading is the more sensible phrase and the mark is
  small, so it needs an eyeball.
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
- **No retrieval engine exists.** The Roscoe queries were scored with a keyword
  search over the capture JSON, written for that run and not kept. Miss #93 is
  recorded-but-unreachable by keyword and would fall to an embedding search, so
  the scoring tool is now itself a variable in the measurement: **the next title
  must be scored the same way as this one, or the two numbers cannot be
  compared.**
- **The pass under-reads silent background business.** Roscoe query #85 missed a
  full-panel electrocution gag because the panel's balloon was about something
  else. One instance, so it is a hypothesis rather than a finding — watch for it
  on the next title before changing the prompt.
- **24 pages have no prelim OCR at all** — see below. The tools no longer trip over
  them, but the OCR still needs to be run.
- **One-pagers cannot be prepped at all.** All 155 `ONE_PAGERS` fail to resolve —
  128 `TitleNotFoundError`, 27 `KeyError` — because they have no `.ini`, and no
  one-pager OCR exists in the corpus under any title. This is why the trial has
  no one-pager unit. Whether they are ever worth capturing is open; they would
  need OCR first, and then a way to address them that is not a story title.
- **136 pages of OCR are unreachable, all in vol 2.** 5,358 easyocr prelim pages
  are on disk; 5,222 are reachable through a title. The gap is twelve vol-2
  stories — *Good Neighbors*, *Salesman Donald*, *Snow Fun*, *Kite Weather*,
  *The Hard Loser*, *Too Many Pets*, *The Duck in the Iron Pants*, *Three Dirty
  Little Ducks* and others — which abort with:

  > `Panels segments info file ".../Frozen Gold/031.json" is older than srce image file ".../images/031.png"`

  That is the staleness guard firing correctly, not corruption: the restored PNGs
  were regenerated after the panel segments. Regenerating vol 2's panel segments
  clears it. Until then `vision_prep --title` fails on any of those twelve.
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

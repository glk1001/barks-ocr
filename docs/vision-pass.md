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
- the nephews wear football helmets (078 p1, 080 p2, 083 p2);
- the colourist slips — 085 p3 gives two nephews the same green.

Those cases are exactly the 18 `low` entries, and `cap_colour` is `null` there, so
nothing is silently guessed. Where the art carries the colour some other way — the
red/blue/green pyjamas in 085 p5 — identification still works.

### Bonus: the `type` field mis-labels speech as thought

The art distinguishes true thought clouds (scalloped, bubble trail) from
pointed-tail speech balloons. **3 of the 5 groups typed `thought` in the pilot are
wrong** (079 g16, 080 g6, 080 g7); 081 g3 and 083 g12 are correct. Recorded in
`vision_note` only — nothing was changed.

---

## The next run: a title mix, not a volume

Because the unit is the story, the next run should test the axis that actually
varies — **story length** — rather than 205 pages of one volume's sameness. Four
units, about 60 pages total:

| unit | pages | what it tests |
|---|---:|---|
| a 10-pager | ~10 | the modal Barks story; directly comparable to the pilot |
| a second 10-pager, different cast | ~10 | does the per-story closed set hold on a different tag set? |
| a long adventure (24–32p) | ~30 | do settings multiply? does one session hold a story that long? |
| a one-pager batch | ~10 | the awkward case — its closed set is the union of ten unrelated stories |

That is ~330 panels and ~800 groups: cheap enough to run twice if the first pass
says the schema is wrong, and it puts the speaker queue at a workable ~107
entries rather than a volume's ~370.

**Pick the four so they light up ten or twelve of the queries in
[`retrieval-queries.md`](retrieval-queries.md)** — rather than picking titles
first and finding the queries cannot reach them.

Five things to measure, in this order:

1. **Correction rate** against the pilot's **1.5%**. Read this first: materially
   higher means the pass is hallucinating, not that the story is dirty.
2. **Retrieval hit rate** on the 30 pre-committed queries. The pass/fail gate.
3. **Low-confidence speaker error rate.** Decides whether `low` is worth queueing
   at corpus scale, or whether the threshold should move.
4. **Off-vocabulary rate** for `characters` and `setting`, and which `other:`
   names recur enough to promote.
5. **Cost per title** in sessions and wall-clock. This is what makes the
   remaining ~5,500 pages an arithmetic decision rather than a guess, and none of
   the other four substitute for it.

`visible_text` has no baseline, so establishing its yield is itself an output.

## Open threads

- **2 queued corrections are unapplied.** `~/barks-vision/vol01-vision-review.txt`.
  `077 g1` (`YOU — YOU` → `YOU-YOU`) is solid — and is visible in context in the
  speech script. `085 g7` (`INVISIBLE SEEDS,` → `INVISIBLE, SEEDS,`) is explicitly
  low-confidence: the stored reading is the more sensible phrase and the mark is
  small, so it needs an eyeball.
- **The speaker review has not been run yet.** The editor can now do it (above);
  what it is for is measuring how often the low-confidence calls are wrong. Run
  it on the pilot's 18 `low` entries before scaling the pass up.
- **The pilot's `type: thought` mislabels are unfixed** — 079 g16, 080 g6, 080 g7
  are recorded in `vision_note` only.
- **24 pages have no prelim OCR at all** — see below. The tools no longer trip over
  them, but the OCR still needs to be run.

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

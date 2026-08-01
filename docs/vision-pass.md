# Vision pass — workflow, schema, and what the pilot found

A Claude Code vision pass over comic pages. It adds four things the OCR pipeline
cannot produce on its own: verification of `ai_text` against the art, **word-level
bold**, per-panel descriptions, and speaker attribution.

Written 2026-08-01, after a pilot on Vol. 1 pages 076-085 ("The Victory Garden").

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
barks-ocr-vision-prep  --volume 1 --pages 076-085     # crop + build the queue
   <Claude Code reads the crops, writes result.json per page>
barks-ocr-vision-report --out-dir ~/barks-vision/vol01-076-085
barks-ocr-vision-apply  --out-dir ~/barks-vision/vol01-076-085 --queue-out review.txt
```

`--out-dir` defaults to `~/barks-vision/vol<NN>-<pages>`. **Not `/tmp`**: a
snap-confined Firefox gets a private `/tmp` namespace and cannot open a report
written there, whatever the permissions say.

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
| `speaker_confidence` | `high` / `medium` / `low` |
| `cap_colour` | `red` / `blue` / `green`, or `null` when not visible |
| `emphasis_spans` | `[[start, end, "bold"], …]` — char offsets into the **current** `ai_text` |
| `vision_note` | the reasoning behind the call |
| `vision_text_ok` | `false` when the art disagrees with `ai_text` |
| `vision_corrected_text` | the reading from the art |

Panel descriptions go to a sibling `{page}-panel-descriptions.json`, **not** into
the group JSON: `final_groups.py` copies only the `groups` key and would silently
drop a new top-level section.

Design decisions worth not re-litigating:

- **`ai_text` is never modified.** Corrections go to a kivy-editor queue for review.
  Saves use `save_json(backup_file=...)`, unlike `ocr_check`'s bare `save_json()`.
- **Spans, not inline markup.** Inline `**bold**` would break
  `whoosh_index.check_capitalization_map`, perturb `ocr_check`'s width-fit and
  line-height heuristics, invalidate cached `florence_passed` entries, and render
  literally in reader search results. 139 groups also already contain a `*` used as
  a footnote marker, so `*` cannot mean emphasis.
- **Both the name and the colour.** Naming a nephew relies on the Huey-red /
  Dewey-blue / Louie-green convention, which was not firmly fixed in 1943 Barks.
  Recording `cap_colour` alongside keeps the mapping reversible if it turns out wrong.
- **`vision_` prefix on the reasoning fields.** The group already carries a
  Gemini-written `notes`; a bare `note` beside it would be a trap.

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

## Open threads

- **2 queued corrections are unapplied.** `~/barks-vision/vol01-vision-review.txt`.
  `077 g1` (`YOU — YOU` → `YOU-YOU`) is solid. `085 g7`
  (`INVISIBLE SEEDS,` → `INVISIBLE, SEEDS,`) is explicitly low-confidence — the
  stored reading is the more sensible phrase and the mark is small; needs an eyeball.
- **kivy_editor has no speaker field.** Worth adding only if review shows the
  low-confidence calls are wrong often enough to matter.
- **Scale is undecided.** 10 pages is a shakedown. Next step would be a full volume
  (~170 pages), then a decision about the remaining ~5400.
- **`barks-ocr-check --volume N` aborts** on a missing prelim file rather than
  skipping the page — vols 8, 9, 20 and vol 1 (page 500). `--title` works around it.

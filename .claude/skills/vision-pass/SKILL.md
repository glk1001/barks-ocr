---
name: vision-pass
description: "Run a Claude Code vision pass over one or more Barks comic titles — prep, read the pages, apply, build review queues, commit; and later mirror a finished review onto the second engine. Use whenever the ask is to read/vision-pass a title, work through --todo or --next, or when the reviewer says a title's review is done. Covers only the procedure and its hazards; the reading rules live in the generated roster.txt."
---

# Vision pass — the run procedure

The **reading** rules are not here. They are in `<out-dir>/roster.txt`, generated
from `vision_schema.py` on every prep and validated against by `vision_apply`.
Read that file in full before page 1, every time. Prose that lives anywhere else
has twice been found not to reach the pass.

This skill is the **operational** half: the order of the steps, and the traps.

## The sequence, per title

```bash
barks-ocr-vision-status --titles --todo      # work list, oldest first
barks-ocr-name-grep    --title "…"           # BEFORE page 1
barks-ocr-vision-prep  --title "…"           # crops, queue.json, roster.txt
#   <read roster.txt, then the pages, writing result.json per page>
barks-ocr-vision-apply --out-dir ~/barks-vision/<slug> --dry-run --capture-model "claude-opus-5[1m]"
barks-ocr-vision-apply --out-dir ~/barks-vision/<slug>          --capture-model "claude-opus-5[1m]"
```

Then build **both** queue files, commit, and stop. Mirroring waits until the
reviewer says the review is done.

**Dry-run at page 2 of the first title** to prove the contract before doing all
the reading, then once per title before applying.

**`--capture-model` is not optional.** Without it the provenance is written null
and the pages join an unidentifiable cohort.

## Reading the pages

**One message per page**: `groups.json`, `page.png` and every panel crop issued
together. This is 1.6 min/page against 11 — the per-page cost becomes one model
turn rather than ten round trips.

**Crop tails from `panel-NN.png`, never `page.png`.** The panel files are source
resolution and share the `text_box` coordinate space; `page.png` is about half,
so the same numbers land elsewhere and the miss is *silent* — what comes back is
plausible comic art with no tail in it. Helpers, no barks imports needed:

```bash
uv run python ~/barks-vision/dump_boxes.py "Some Title" ~/barks-vision/boxes-<slug>.json
python3 ~/barks-vision/crop.py ~/barks-vision/<slug> <page> <panel> <x0> <y0> <x1> <y1> <scale> out.png
```

2–3x settles which hat a tail leans at, 4–6x a letter, 8–12x a cap crown of a
few dozen ink pixels.

**Find the title's clean cap-reference panel before page 1**, not when you reach
it — scan for the panel where caps are big and lit (held, removed, backs to
reader, a close row) and fix the palette from it. Getting this wrong costs a
rewrite of every page read before it.

**A wordless page still needs a `result.json`** with `"groups": {}` plus its
capture record.

**Verify emphasis round-trips locally** before applying — strip the tags and
compare to the stored `ai_text`. Do not learn about a mismatch from validation
after all the reading is done.

## Queues — two files, distinct paths

```bash
barks-ocr-speaker-queue --title "…" --unreviewed --confidence low,medium -o <dir>/queue-lowmed.txt
barks-ocr-speaker-queue --title "…" --unreviewed                        -o <dir>/queue-full.txt
```

Sort both by **volume, page, group (numeric), engine** — group is field 4, engine
field 3 — keep the summary header, drop the `# --- category ---` separators.
Report the counts.

**Never re-run `vision_apply` to regenerate a queue.** On a title carrying a
review it is safe now, but the habit is what caused the clobber; `speaker-queue`
reads and writes nothing.

## Committing

The prelim JSON is **its own git repo** at
`Fantagraphics-restored-ocr/Prelim` — not the parent.

**Stage explicit file paths. Never a directory, never a glob.** A pathspec of
`"Carl Barks Vol. 2*"` matches Vol. 20 through Vol. 29 — ten volumes — and
**Vol. 19 must stay out**. Build the list from the page numbers and assert before
committing:

```python
assert len(staged) == expected
assert sorted({s.split(" - ")[0] for s in staged}) == ["Carl Barks Vol. 2"]
```

Check the tree first: other volumes may have in-flight uncommitted work that is
not yours. End messages with the `Co-Authored-By` trailer.

Prelim JSON is `json.dumps(d, indent=4)` — 4-space, `ensure_ascii`, **no trailing
newline**. Prove the round trip before any scripted edit; get it wrong and a
one-string change reformats the whole file.

## When the reviewer says a title's review is done

```bash
barks-ocr-vision-mirror --title "…"            # dry run first
barks-ocr-vision-mirror --title "…" --write
```

Then verify both engines match on group count, reviewed count, `identified_by`
count, and the speaker / cap_colour / confidence distributions, and commit with
explicit paths. Report whether the mirror was clean.

Check for groups left without `speaker_reviewed` and say so — a "review complete"
commit that is really 140/141 is bad provenance. `--unreviewed` with no
`--confidence` gives exactly the stragglers; hand back a queue file for them.

**A review outranks the pass**, and `vision_apply` enforces it: on a group with
`speaker_reviewed` a re-apply leaves `speaker`, `speaker_confidence`,
`cap_colour` and `identified_by` alone. After a review use `vision-mirror`, not
`vision-apply`.

## Traps

- **Kivy tools need a bare `--`**: `uv run barks-ocr-kivy-editor -- --queue-file …`.
  Kivy parses argv itself. Non-Kivy commands take bare flags.
- **`Panels segments info file … is older than srce image file`** is an mtime
  gate, not corruption. Verify the segmentation still matches the image, then
  **ask before touching anything**.
- That gate **fails silently** in `vision-status`, which swallows it at DEBUG, so
  an affected title just vanishes from `--titles`/`--todo`/`--next`. If the
  "N of 430 title(s)" denominator drops, loop the suspect volume's titles through
  `title_pages()` to find which.
- **Deleting a group in the editor renumbers ids**, invalidating a stored
  `result.json`.
- Tool output is buried in DEBUG logs; filter with `grep -v "| DEBUG \|WARNING"`.

## Reporting

Report **per title, not in one lump**. Say whether observed cap colour surfaced
any tail/cap disagreement, and list the distinct `other:` speaker values so
near-duplicates get caught — free-text names get no closed-set check and drift
silently.

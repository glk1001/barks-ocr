# A regression gate for the vision-pass pipeline — scope, not code

The 2026-09-02 insights report proposed mining the session history for every past
correction and turning each into a pytest invariant wired into pre-commit. The
goal is right: most of the recurring friction is the same handful of shapes, and
each one is a check that does not exist. Two things about the proposal are not.

**It is not a pytest suite.** Almost every failure below is a property of the
*corpus* — a page of prelim JSON on disk — not of a function. A pytest suite
would need either the live corpus as a fixture (making the gate depend on
whichever volumes are on this machine) or synthetic fixtures that stop
resembling the real data within a month. The repo also has no test harness
today, so pytest would be a second thing to introduce alongside the checks.

The natural shape is what `scripts/vision/` already is: a corpus checker with a
CLI, run per title and corpus-wide, reporting rather than asserting. That is how
`audit_missed_text.py`, `engine_diff.py` and `barks-ocr-vision-corrections`
already work, and `scripts/closeout.sh` already sequences them and exits
non-zero. **The gate is closeout.sh; the work is adding checks to it.**

**And several of the report's failure classes are already enforced.** The
report was written from session transcripts, so it lists incidents without
knowing which ones provoked a fix at the time.

## What is already enforced

| Failure class | Enforced by | Where |
|---|---|---|
| Emphasis markup not round-tripping to stored `ai_text` | `_check_emphasis` — refuses the apply | `vision_apply.py:213` |
| A review's proposed text correction never handed on | `--queue-out`, idempotent via `_correction_applied` | `vision_apply.py:793` |
| Lettering neither engine grouped | `audit_missed_text.py` | closeout, stage apply |
| A second copy of a grouped string; one-engine-only lettering | `engine_diff.py` | closeout, both stages |
| Text/type corrections outstanding after a speaker review | `barks-ocr-vision-corrections` | closeout, both stages |
| A "review complete" title that is really 140/141 | `speaker-queue --unreviewed`, both engines | closeout, stage review |
| Mirror not actually applied | `vision-mirror` dry run must report 0 | closeout, stage review |
| A title the pass never read scoring all-clean | swept-page-count guard | closeout |
| ruff / ty / pyrefly / cspell on Python | pre-commit, `scripts/full-lint.sh` | commit |

## The gaps, ranked

Ranked by how often the class has actually fired against how cheap the check is.
Each names the incident it comes from, so a check that never fires can be
retired on evidence rather than kept out of habit.

### 1. Vol. 19 staged into the prelim repo — *cheap, catastrophic*

A pathspec of `"Carl Barks Vol. 2*"` matches Vol. 20–29, and Vol. 19 must stay
out. This is a pre-commit hook in the **prelim** repo (which has none today),
not in this one: reject any staged path under a Vol. 19 directory, and reject a
staged *directory* pathspec outright. Pure string work, no corpus load, and the
only entry on this list whose failure is unrecoverable rather than annoying.

### 2. Prelim JSON reformatted by a scripted edit — *cheap, wide blast radius*

The format is `json.dumps(d, indent=4)`, ASCII-escaped, no trailing newline. A
one-string edit written back with any other setting rewrites the whole file, and
the diff then hides the real change. Check: re-serialize every staged prelim
file and byte-compare. Same pre-commit hook as #1.

### 3. `vision_added` lost, or an id-renumber landing annotations on the wrong
group — *the two data-destroying incidents*

The editor renumbers ids on both delete *and* add, and can re-sort a page into
reading order with no add and no delete at all. A stored `result.json` is then
silently pointed at the wrong group, and `vision_added` — which marks a
hand-add, predates the pass, and sits on different ids per engine — must never
be stripped.

Check, at apply time and in closeout: match old to new by **(text, occurrence)**,
never by id and never by text alone, and refuse if the `vision_added` set has
shrunk. This is the most valuable check on the list and by some way the most
work — it needs the pre-edit state, so it wants either the git blob of the
previous commit or a checkpoint written by prep.

### 4. Copy-In residue on a group the reviewer added — *fires most often*

A group seeded from a neighbour is born carrying that neighbour's `ai_text`,
`type`, `vision_note`, `notes`, `acknowledged_issues` and `identified_by`, and
Copy In deep-copies `speaker_reviewed` so it arrives already signed off. One
batch of 4 review-added groups produced 5 distinct faults.

Check: for each group, flag `ai_text` byte-identical to another group on the same
page whose `text_box` does not overlap it. This must be a **WARN**, not a gate —
a duplicated string is sometimes the true lettering, which is itself a
documented trap. Pair it with a hard check that per-engine group counts moved
together: an add on one engine only is unambiguous.

### 5. Free-text `other:` speakers drifting — *cheap, silent*

`other:` names get no closed-set check. Two checks, both a `Counter` away: flag
any `other:` value used exactly once in a title, and hard-fail on two values
differing only by case or whitespace. Catches the capitalisation drift and the
near-duplicate name before a mirror copies it to the second engine.

### 6. Required fields missing on a group — *cheap*

`text_ok` and `speaker_confidence` are required on every group, `none` groups
included, and `roster.txt` does not say so. A wordless page still needs a
`result.json` with `"groups": {}` and its capture record. A flat schema check
over the corpus; likely finds a backlog on first run.

### 7. A title vanishing from the scans — *cheap, and it hides everything else*

The stale panel-segments mtime gate is swallowed at DEBUG in `vision-status`, so
an affected title silently drops out of `--titles`/`--todo`/`--next` and out of
any corpus sweep. closeout already catches the `vision-corrections` form of this;
the missing piece is asserting the **denominator**: the "N of 441 title(s)" total
must not fall between runs.

## Where each gates

- **closeout.sh, stage apply** — 4, 5, 6
- **closeout.sh, stage review** — 3, 4, 5
- **prelim repo pre-commit** (does not exist yet; would need creating) — 1, 2
- **corpus sweep, run occasionally with no `--title`** — 6, 7

## Suggested order

1, 2 and 7 are each an afternoon and gate the failures that are either
unrecoverable or invisible. 5 and 6 are a `Counter` and a field check, and both
will report a backlog worth reading before anything is wired to fail on them. 4
is a heuristic and should stay advisory. 3 is the real project — do it last,
deliberately, and only once there is a pre-edit checkpoint to compare against.

**Do not wire any of these to fail before running it across the whole corpus and
reading the backlog.** Every mechanical check on this list is being written after
its failure, against data that already contains the failures, so a gate switched
on at birth blocks the next commit rather than the next mistake.

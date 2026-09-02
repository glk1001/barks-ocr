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

### 1. ~~Vol. 19 staged into the prelim repo~~ — **BUILT, and downgraded** (2026-09-02)

Built as `scripts/vision/check_prelim_staged.py`, wired into the prelim repo's
`.git/hooks/pre-commit` as a forwarder. **Two of this entry's three claims were
wrong, and the evidence changed the design.**

*"Vol. 19 must stay out"* is a rule for Claude, not a repo invariant. Vol. 19 is
tracked — 340 files — and its owner commits it under their own name, most
recently 2026-08-30. A hook cannot tell who is committing, so one that refused
those paths would block the person the directory belongs to. Dropped.

*"Reject a staged directory pathspec"* is not observable. By the time a
pre-commit hook runs, git has already expanded a directory or glob into
individual paths; only its consequences survive.

*The general form — refuse a staged set spanning more than one volume — does not
survive the replay either.* Over all 380 commits, **19 span multiple volumes and
none is a mistake**: they are the corpus-wide sweeps this workflow runs on
purpose — the `other:` speaker audit (6 volumes), "settle every outstanding
vision text correction" (3), an em-dash fix that reached 23. Spans run 2 to 23
for deliberate work, so neither spanning nor its size separates accident from
intent, and a gate firing on 5% of real commits gets trained away. **It ships as
a named, counted warning** — enough to make "I meant one title and staged ten
volumes" obvious, without refusing anything.

### 2. Prelim JSON reformatted by a scripted edit — **BUILT** (2026-09-02)

Same hook. This one refuses. But the entry above said "the format", and **there
are three**, which neither CLAUDE.md nor the skill said. Measured over all 12,372
tracked JSON files at HEAD:

| kind | format | clean |
|---|---|---|
| `*-gemini-prelim-groups.json` | `indent=4`, **no** trailing newline | 10,682 / 10,716 |
| `*-page-capture.json` | `indent=2`, **with** a trailing newline | 1,537 / 1,646 |
| `*-panel-descriptions.json` | `indent=2`, **with** a trailing newline | 10 / 10 |

Only the groups files are gated. Page captures are 93% consistent and the other
107 are undiagnosed; refusing on them would block work to enforce a rule nobody
established. They are reported, not refused.

The 34 off-format groups files are two real causes: a `\u00AD` escape written in
uppercase where `json.dumps` emits lowercase (identical JSON, different bytes),
and at least one stray three-space indent from a hand edit. **The backlog blocks
nothing** — a file rewritten by the normal tooling comes back correct, so the
check can only refuse an edit that *preserves* the bad bytes.

### 3. `vision_added` lost, or an id renumber — **BUILT** (2026-09-02)

`scripts/vision/audit_drift.py`. The plan said this "wants either the git blob
of the previous commit or a checkpoint written by prep" — the prelim repo has
380 commits, so the checkpoint already existed and nothing new had to be built.

Two refinements the first run forced, each cutting the noise by an order of
magnitude:

- **Strip emphasis before comparing.** An apply writing `[b]…[/b]` into
  `ai_text` changes the bytes and nothing else, and is the commonest edit in the
  corpus. Comparing raw text gave 446 findings over 8 commits; stripping markup
  gave **24**.
- **A shift is the fault; a retype is not.** If an id's new text is what its
  *neighbour* used to hold, the page was renumbered under a stored
  `result.json`. If the text is merely different, somebody corrected it. Of the
  24, **13 were shifts and 11 ordinary retypes** (`YOWOOO`→`TOOT`, `. . .`→`.....`).

It found a live one: *The Pixilated Parrot* 008, both engines, a `'!'` group
inserted at g9 and every id above it carrying its predecessor's text.

### 4, 5, 6 — **BUILT** as one sweep (2026-09-02)

`scripts/vision/audit_groups.py`, wired into `closeout.sh` as advisory. Each of
the three needed its premise corrected by measurement first.

**Item 5 — `other:` drift.** The plan said to flag any `other:` used exactly
once. There are 172 of those and they are the normal case: a harbour messenger,
a fireman, a shark. The wrong signal by 19 to 1. What does work is normalising
case *and a leading article*: **9 real pairs**, `other:crowd` / `other:the
crowd`, `other:shopkeeper` / `other:the shopkeeper`, `a bear` / `the bear`.
Naive case-and-whitespace matching, which is what the plan proposed, finds zero.

**Item 6 — required fields.** Mostly already enforced: `vision_apply` requires
`speaker_confidence`, validates the cast, `cap_colour`, `identified_by` and the
type, and refuses `text_ok: false` with no `corrected_text`. It can only enforce
going forward, and **1,503 stored groups carry a speaker with no
`identified_by`**, concentrated in Vols. 6, 10, 7 and 1 — the shape of a cohort
read before the field existed. Report-only; `speaker-queue --missing-evidence`
is the queue path.

**Item 4 — Copy-In residue.** The plan's signal, duplicated `ai_text` with
non-overlapping boxes, does not work: 2,468 raw, 2,336 after the overlap filter,
100 after also requiring an identical `vision_note` — and every visible one of
those 100 is real repeated lettering (`SEEDS` on a packet, `D. DUCK` on a
mailbox, `CASTOR OIL`, `$100,000`). Duplicated text is not the signal.

The population that is worth checking is the **133 groups actually carrying
`vision_added`**. Against those: 25 duplicate another group's text, and — the
unambiguous one the plan did not think of — **11 pages carry a different number
of added groups on each engine**, one of them three against zero. The pass, the
mirror and `speaker-queue` all read easyocr, so a group added only to paddleocr
reaches no queue and is never reviewed.

### 7. A title vanishing from the scans — **BUILT** (2026-09-02)

`scripts/vision/title_census.py`, baselined at **441 titles**. Records the title
*names*, not just the count, because a count alone leaves you looping a suspect
volume through `title_pages()` to find which one went; the names answer it
directly. A drop exits non-zero, a rise is reported for a deliberate `--update`.

Not wired into `closeout.sh`: it takes ~40s against closeout's ~2s, because it
builds every title's page list. It belongs to the occasional corpus sweep, which
is where this document already put it.

## Where each gates

- **closeout.sh, both stages** — 4, 5, 6, via `audit_groups.py` (advisory)
- **run by hand after an editor session** — 3, via `audit_drift.py`
- **prelim repo pre-commit** — 1 (warn), 2 (refuse) — installed 2026-09-02
- **corpus sweep, run occasionally with no `--title`** — 6, 7

## All seven are built. What it taught.

**Every single entry had a wrong premise, and only measurement found them.**
Written from a friction log, each described the failure accurately and the
*detection* wrongly:

| entry | the premise | what the data said |
|---|---|---|
| 1 | never stage Vol. 19 | it is tracked, and its owner commits it |
| 1 | refuse a multi-volume stage | 19 of 380 commits span, none a mistake |
| 2 | one prelim JSON format | three, and an apply writes two of them |
| 3 | compare stored text by id | markup made 95% of it noise |
| 4 | duplicated `ai_text` finds residue | 100 findings, every visible one real lettering |
| 5 | flag an `other:` used once | 172 of them, all legitimate |
| 6 | required fields are unchecked | apply already enforces all of them |

Two lessons worth keeping:

**Replay a proposed check against the whole history before writing it.** It is
cheaper than the check, and here it changed the design of every one — twice
turning a refusal into a warning, once replacing the signal outright.

**The backlog is the design input, not an obstacle.** A check whose first run
returns thousands is measuring the wrong thing; one that returns 9, 11 or 25 has
found something. Item 4 only became useful when the population narrowed from all
groups to the 133 carrying `vision_added`.

## What is now outstanding, for a human

None of these is a code change:

- **11 pages** where a hand-added group exists on one engine only.
- **9 `other:` speaker pairs** differing by an article — pick one, retire the other.
- **1,503 groups** with a speaker and no `identified_by`, mostly an old cohort.
- **34 groups files** off-format (an uppercase `\u00AD`, one three-space indent);
  harmless, and self-healing on the next rewrite.
- ***The Pixilated Parrot* 008**, both engines: an insert cascade shifted every
  id above g9. Worth confirming no stored `result.json` was applied after it.

**Do not wire any of these to fail before running it across the whole corpus and
reading the backlog.** Every mechanical check on this list is being written after
its failure, against data that already contains the failures, so a gate switched
on at birth blocks the next commit rather than the next mistake.

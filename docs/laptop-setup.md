# Running a vision pass on a second machine

What a vision session actually depends on, and the three things that break
silently if you get them wrong.

Written 2026-08-07, when the question "what would a laptop need?" turned up a
`SKILL.md` that told you to run two scripts existing only in an untracked
scratch directory. Those are now `scripts/vision/`.

## Repos

| repo | why | path |
|---|---|---|
| `barks-ocr` | the tools, and `.claude/skills/vision-pass` | anywhere |
| `barks-compleat-reader` | supplies `barks_fantagraphics`, `comic_utils`, `barks_kivy_ui` as **uv path dependencies** | must be `../barks-compleat-reader` relative to `barks-ocr` |
| `barks-ocr-prelim` | the OCR JSON the pass writes to | `$HOME/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim` |

`pyproject.toml` points `[tool.uv.sources]` at `../barks-compleat-reader/src/`,
so the two checkouts must sit side by side. Nothing else about the location
matters.

## The data root is hard-coded

`BARKS_ROOT_DIR = Path.home() / "Books" / "Carl Barks"` in
`barks_fantagraphics/comics_consts.py`. There is **no environment override**.
Reproduce that path exactly, or make it a symlink to wherever the files really
live — which is what this machine does for the big trees.

Needed under it:

| tree | size | used for |
|---|---|---|
| `Fantagraphics-restored` | 18G | the page images every crop comes from |
| `Fantagraphics-fixes-and-additions` | 916M | substitute pages on some titles |
| `Fantagraphics-restored-panel-segments` | 22M | panel boxes |
| `Fantagraphics-restored-ocr/Prelim` | git | the OCR JSON |

## Copy with `rsync -a`, and nothing else

**A panel-segments file must be newer than its page image.** The check is an
mtime comparison, and a failure is not an error you will see — the affected
title simply disappears from `vision-status --titles` and `--todo`, and the
denominator quietly drops. Sixteen titles were invisible on this machine at one
point for exactly this reason.

So any transport that stamps fresh mtimes on the images — `cp -r`, unzipping an
archive, a cloud-sync client — breaks the corpus. `rsync -a` preserves times and
is safe. If you must copy without it, do the **images first and the segments
second**.

The symptom, if it happens: `vision-corrections` reports the titles it could not
read under `!! N title(s) NOT checked`. `vision-status` will not tell you; it
swallows the error at DEBUG.

## What you do *not* need to copy

Everything under `~/barks-vision/` except the two helper scripts, which now live
in the repo. Specifically:

- the per-title out-dirs and their crops — `vision-prep` rebuilds them
- `boxes-*.json` — `scripts/vision/dump_boxes.py` rebuilds them
- **every queue file** — `speaker-queue` and `vision-corrections` read the
  corpus, not a scratch directory, precisely so that losing the scratch costs
  nothing. Ask for the queue again on the new machine and it will be current.

## The memory directory

Claude Code keeps this project's memory in

    ~/.claude/projects/<project-path-with-slashes-as-dashes>/memory/

The directory name is the checkout path with `/` turned into `-`, so **the
laptop must use the same checkout path** or the key differs and the memory is
silently not found. It holds the accumulated review feedback — the under-naming
rule, the corrected cap-colour cutoff, the painted-noise rule. A session without
it repeats mistakes the reviewer has already corrected three times.

Copy `memory/` and nothing else. The directory above it is session transcripts:
1.1G against the memory's 128K.

```bash
rsync -av ~/.claude/projects/-home-greg-Prj-github-barks-compleat-digital-barks-ocr/memory/ \
  laptop:~/.claude/projects/-home-greg-Prj-github-barks-compleat-digital-barks-ocr/memory/
```

Two files are about this desktop's hardware rather than the project —
`feedback_ptyxis_session_restore.md` and `project_gdm_magnifier.md`. Add
`--exclude='*ptyxis*' --exclude='*gdm*'` to leave them behind.

**There is no merge.** `rsync -a` overwrites the destination, so a memory
written on the laptop is lost the next time you copy the other way. `--update`
does not save you either: `MEMORY.md` is a single index, so if both machines
added entries you end up with one side's index listing only half the files that
are present. Copy in the direction of the machine you have just worked on,
before you switch — the same discipline the prelim repo needs, for the same
reason.

## Working on two machines

The prelim repo is the shared state and it is JSON, so a divergence is a
horrible merge. The discipline is simply:

    git -C "$PRELIM" pull     # before starting
    git -C "$PRELIM" push     # before switching machines

`barks-ocr` needs the same treatment and is easy to forget because it is not
where the data lives. A pass commits to it too — the missed-text ignore list
grows, and `docs/vision-pass-run-prompt.md` accumulates the per-volume cap
palette that stops the next run re-deriving it. Pull it before you start or you
read a title with last month's palette notes.

A vision pass touches one title at a time and commits per title, so as long as
each machine pushes before you switch, there is nothing to reconcile. If you
want belt and braces, work different volumes on each.

## Every `barks-ocr-*` command needs `--offline`

    uv run --offline barks-ocr-vision-status --titles --todo

Without it, uv revalidates the `en-core-web-sm` URL dependency in
`[tool.uv.sources]` on every invocation, and with no network the command dies
before it runs. The failure looks like a broken install rather than a network
one, so it is worth putting `--offline` in from the start on a machine that may
be offline. It costs nothing when the network is up.

`python3 scripts/vision/crop.py` and the other plain-`python3` helpers are
unaffected -- they deliberately avoid the uv/barks import graph.

## Check it works

```bash
git -C "$PRELIM" pull                                        # shared state first
uv run --offline barks-ocr-vision-status --titles --todo | head
uv run --offline barks-ocr-vision-corrections
uv run --offline python scripts/vision/dump_boxes.py "Snow Fun" ~/barks-vision/snow-fun/boxes-snow-fun.json
```

`vision-corrections` is the real test: it reads every title and reports the ones
it could not, so a clean run means the mtimes survived the copy. What you are
looking for is the **absence** of a `!! N title(s) NOT checked` line —
`vision-status` will not tell you, it swallows that error at DEBUG.

A small non-zero *outstanding* count is normal and unrelated; that is the
corpus-wide correction backlog, not a copy problem.

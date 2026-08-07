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

The directory name is derived from the checkout path, so **if the laptop uses
the same path the key matches** and copying the `memory/` directory across is
enough. It holds the accumulated review feedback — the under-naming rule, the
corrected cap-colour cutoff, the painted-noise rule. A session without it
repeats mistakes the reviewer has already corrected three times.

## Working on two machines

The prelim repo is the shared state and it is JSON, so a divergence is a
horrible merge. The discipline is simply:

    git -C "$PRELIM" pull     # before starting
    git -C "$PRELIM" push     # before switching machines

A vision pass touches one title at a time and commits per title, so as long as
each machine pushes before you switch, there is nothing to reconcile. If you
want belt and braces, work different volumes on each.

## Check it works

```bash
uv run barks-ocr-vision-status --titles --todo | head        # corpus visible?
uv run barks-ocr-vision-corrections                          # nothing outstanding, nothing skipped?
uv run python scripts/vision/dump_boxes.py "Snow Fun" ~/barks-vision/snow-fun/boxes-snow-fun.json
```

The second is the real test: it reads every title and reports the ones it could
not, so a clean run means the mtimes survived the copy.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`barks-ocr` is a collection of scripts for OCR processing of Fantagraphics Carl Barks comic pages. It runs OCR engines (EasyOCR, PaddleOCR) on restored comic images, groups text boxes into logical speech/caption units using Google Gemini AI, and builds searchable Whoosh indexes.

## Commands

**Run all lint/static checks (ruff check + format, ty, pyrefly, cspell; plus a non-gating `uv audit`):**
```bash
bash scripts/full-lint.sh
```
It does not run tests — this repo has no test suite.

**Type-check (two checkers).** `ty` is the primary; **pyrefly** is gated alongside it and is stricter on nullability, which is most of what it earns us. Config and rationale live in `pyrefly.toml`.

```bash
uv run ty check . --error-on-warning
bash scripts/pyrefly.sh                      # or: uv run pyrefly check
bash scripts/pyrefly.sh --min-severity=warn  # also show the non-gating warnings
```

The pyrefly gate is a plain **0 errors** with **no baseline file**, matching the sibling `barks-comic-building` rather than `barks-compleat-reader`. Keep it that way: fix a new finding, or suppress it at the line with a `# pyrefly: ignore[<rule>]` comment saying why, rather than adding a baseline to hide it.

`tools/kivy_editor.py` and `tools/annotate.py` are Kivy apps, so this repo does carry some Kivy-boundary noise. It is handled by config in `pyrefly.toml` (`replace-imports-with-any` for the compiled/provider-loaded Kivy modules, plus the `bad-override` family disabled against Kivy's compiled base classes) — not by grandfathering. The standing line suppressions are only the two `Widget.canvas` accesses and the two numeric CSS `font-weight` values in `censorship_table.py`, each explained in place.

**Toolchain bump.** `ruff` and `ty` are `==`-pinned; bump them deliberately on a branch with `bash scripts/bump-toolchain.sh`. Runbook: `../barks-compleat-reader/docs/toolchain-bump.md`.

## Vision-Pass Pipeline

The procedure is the `/vision-pass` skill (`.claude/skills/vision-pass/SKILL.md`);
the *reading* rules are in the generated `<out-dir>/roster.txt` and nowhere else.
Three things govern every run and so live here too:

**Image budget: target 3 images read per page, 5 the ceiling** for a cap-dense
title, and say so in the report if you go over. `docs/vision-pass-cost.md` is
the authority — the per-page ladder, the measured per-title table, and the list
of what never earns an image. Read colour by sampling hexes off `panel-NN.png`
(`scripts/vision/capscan.py`) rather than opening the image, and read the prep's files straight
off disk instead of manufacturing scaled copies. Report the image count and the
per-page rate in the close-out. Undetected drift to 9.4 images per page once
burned the session limit three times and cut throughput from 30+ pages to under
10.

**Close-out is scripted.** `bash scripts/closeout.sh [--stage apply|review]
"<title>"` runs the read-only checks in one go — missed-text audit, engine diff,
outstanding text/type corrections, unreviewed speakers on *both* engines, mirror
dry run, and `git status` in this repo and the prelim repo — and exits non-zero
if any gating check is dirty. It writes nothing and commits nothing. Use it
instead of re-typing the sequence; read the WARN rows, which are advisory by
design. `UV_OFFLINE=1` when there is no network.

**The prelim JSON is its own git repo** at `Fantagraphics-restored-ocr/Prelim`,
not the parent. Stage explicit file paths — never a directory, never a glob: a
pathspec of `"Carl Barks Vol. 2*"` matches Vol. 20 through Vol. 29, and **Vol. 19
must stay out**. The format is `json.dumps(d, indent=4)`, ASCII-escaped, with
**no trailing newline** -- but ONLY for `*-gemini-prelim-groups.json`.
`*-page-capture.json` and `*-panel-descriptions.json`, which an apply also
writes, are `indent=2` **with** a trailing newline. Prove the round trip before
any scripted edit, or a one-string change reformats the whole file. The prelim
repo's pre-commit hook now refuses a mis-formatted groups file.

To work in a second checkout of that repo (a `git worktree`, so that hand edits
stay out of the tree another session is using), set `BARKS_OCR_PRELIM_DIR` to
its path: every `barks-ocr-*` command then reads and writes the prelim JSON
there, and `ocr_check` runs its git check there. Only the prelim root moves;
images, annotations and `Prelim-backups` stay put. A path that is not a
directory fails at import.

## Architecture

### Shared Packages

`barks-fantagraphics`, `barks-kivy-ui` and `comic-utils` are installed as editable **uv path dependencies** — no `PYTHONPATH` configuration needed:

| Package | Role |
|---|---|
| `barks_fantagraphics` | Comics database, titles, pages, OCR file paths, panel boxes, speech groupers |
| `barks_kivy_ui` | Shared Kivy UI widgets |
| `comic_utils` | Shared utilities (image I/O, CLI options, timing) |

Path dependencies are declared in `pyproject.toml` under `[tool.uv.sources]` pointing to `../barks-compleat-reader/src/`.

### Runtime API Keys

`barks-ocr` uses Google Gemini AI. The `.env.runtime` file contains `GEMINI_API_KEY` — do not modify or commit this file.

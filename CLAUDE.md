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

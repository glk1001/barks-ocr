# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`barks-ocr` is a collection of scripts for OCR processing of Fantagraphics Carl Barks comic pages. It runs OCR engines (EasyOCR, PaddleOCR) on restored comic images, groups text boxes into logical speech/caption units using Google Gemini AI, and builds searchable Whoosh indexes.

## Commands

**Run a script:**
```bash
uv run src/batch-ocr.py --help
uv run src/make-gemini-ai-groups-batch-job.py --help
```

**Common tasks via just (imports from `../barks-comic-building/.justfile`):**
```bash
just find-words "word"
just open-prelim volume page
just annotate-ocr volume page
just check-ocr volume
```

**Type-check (ty):**
```bash
uv run ty check
```

**Lint (ruff):**
```bash
uv run ruff check .
uv run ruff format .
```

## Architecture

### Directory Structure

| Directory | Role |
|---|---|
| `src/` | Main OCR pipeline scripts |
| `src/utils/` | Shared utility modules (geometry, OCR box types, Gemini AI helpers) |
| `src/tools/` | Utility/diagnostic tools (excluded from linting) |

### Key Scripts

- `batch-ocr.py` — Runs EasyOCR and PaddleOCR on restored comic pages, saves preliminary OCR box data
- `gemini_ai_ocr_grouper.py` — Groups OCR text boxes into speech bubbles/captions using Gemini AI and panel segment data
- `make-gemini-ai-groups-batch-job.py` / `make-gemini-ai-groups-from-batch.py` — Batch Gemini AI job management
- `make-whoosh-index-from-gemini-ai-groups.py` — Builds searchable Whoosh full-text index from AI groups
- `fix-ocr.py` / `annotate-ocr.py` — Manual OCR correction and annotation tools
- `kivy-prelim-ocr-editor.py` — Kivy GUI for editing preliminary OCR results

### Shared Packages

`barks-fantagraphics` and `comic-utils` are installed as editable **uv path dependencies** — no `PYTHONPATH` configuration needed:

| Package | Role |
|---|---|
| `barks_fantagraphics` | Comics database, titles, pages, OCR file paths, panel boxes, speech groupers |
| `comic_utils` | Shared utilities (image I/O, CLI options, timing) |

Path dependencies are declared in `pyproject.toml` under `[tool.uv.sources]` pointing to `../barks-compleat-reader/src/`.

### Runtime API Keys

`barks-ocr` uses Google Gemini AI. The `.env.runtime` file contains `GEMINI_API_KEY` — do not modify or commit this file.

## Code Style

- Python 3.13+ syntax.
- Type hints required on all function signatures; use `str | None` not `Optional[str]`.
- Formatter: `ruff` (line length 100, config in `.ruff.toml`).
- Type checker: `ty` (config in `ty.toml`).
- `src/tools/`, `**/experiments/`, and `**/scraps/` are excluded from linting and type checking.

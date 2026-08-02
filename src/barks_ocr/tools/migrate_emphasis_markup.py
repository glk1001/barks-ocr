# ruff: noqa: T201
"""One-shot migration: emphasis offsets -> inline markup, and escape literals.

Two changes to every prelim OCR group JSON, both to ``ai_text``:

1. **Retire ``emphasis_spans``.**  Each group carrying spans has them folded
   into its ``ai_text`` as ``[b]``/``[i]`` tags and the field removed.  The spans
   are character offsets into a string that other tools edit, so they drift the
   moment anything rewrites the text -- silently, and while staying in range, so
   no bounds check could ever have caught it.  See
   ``barks_fantagraphics.speech_markup`` for the full argument.

2. **Escape ``[``, ``]`` and ``&``.**  Once ``[b]`` means something, a literal
   bracket in the lettering has to be written ``&bl;``/``&br;``, and the ``&``
   that introduces those escapes has to be written ``&amp;``.  These are not
   hypothetical: the corpus has Gemini annotations like
   ``[Illegible Comic Covers]`` and shop signs reading ``GOLDSTEIN & CO.``

Idempotent: a group already migrated is left alone, so the tool can be re-run
after a partial pass.  ``--dry-run`` is the default; nothing is written without
``--write``, and every file that is written is backed up first.

    barks-ocr-migrate-emphasis                # report what would change
    barks-ocr-migrate-emphasis --write        # do it, with backups
"""

import json
import shutil
from pathlib import Path
from typing import Annotated

import typer
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.speech_markup import (
    escape_markup,
    has_markup,
    markup_from_spans,
    strip_markup,
    validate_markup,
)
from loguru import logger

app = typer.Typer()

SPANS_KEY = "emphasis_spans"
PRELIM_GLOB = "**/*-gemini-prelim-groups.json"


def _needs_escaping(text: str) -> bool:
    """Whether the text holds a markup-significant character that is still literal."""
    return escape_markup(strip_markup(text)) != text


def _migrated_text(group: dict) -> str | None:
    """Return the group's new ``ai_text``, or None when nothing needs doing.

    Args:
        group: One prelim OCR group, read but not modified.

    Returns:
        The rewritten text, or None if the group is already in the new form.

    """
    text = group.get("ai_text") or ""
    spans = group.get(SPANS_KEY) or []

    if spans:
        # `markup_from_spans` escapes as it goes, so this covers both changes.
        # Offsets index the pre-escape string, which is exactly what is stored.
        return markup_from_spans(text, spans)

    if has_markup(text):
        return None  # already migrated

    if _needs_escaping(text):
        return escape_markup(text)

    return None


def _migrate_file(path: Path, *, write: bool) -> tuple[int, int]:
    """Migrate one prelim JSON. Returns (groups changed, spans folded in)."""
    data = json.loads(path.read_text())
    groups = data.get("groups") or {}

    changed = folded = 0
    for gid, group in groups.items():
        try:
            new_text = _migrated_text(group)
        except ValueError as e:
            # A span that no longer fits its text: the drift this migration
            # exists to make impossible, caught on the way out. Leave the group
            # alone and say so -- it needs a human, not a guess.
            logger.error(f"{path.name} g{gid}: {e}. Left unchanged, spans kept.")
            continue

        had_spans = bool(group.get(SPANS_KEY))
        if new_text is None and not had_spans:
            continue

        if new_text is not None:
            problems = validate_markup(new_text)
            if problems:
                logger.error(f"{path.name} g{gid}: {problems}. Left unchanged.")
                continue
            group["ai_text"] = new_text
            changed += 1
        if had_spans:
            del group[SPANS_KEY]
            folded += 1

    if (changed or folded) and write:
        backup = Path(str(path).replace(str(OCR_PRELIM_DIR), str(OCR_PRELIM_BACKUP_DIR)))
        backup = backup.with_name(backup.name + ".pre-markup")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        with path.open("w") as f:
            json.dump(data, f, indent=4)

    return changed, folded


@app.command(help="Migrate emphasis_spans to inline markup and escape literal [ ] &.")
def main(
    write: Annotated[bool, typer.Option(help="Actually write. Default is a dry run.")] = False,
    prelim_dir: Annotated[Path | None, typer.Option(help="Override the prelim OCR root.")] = None,
) -> None:
    """Run the migration over every prelim OCR group JSON."""
    root = prelim_dir or Path(OCR_PRELIM_DIR)
    if not root.is_dir():
        msg = f'No prelim OCR directory at "{root}".'
        raise typer.BadParameter(msg)

    files = sorted(root.glob(PRELIM_GLOB))
    total_changed = total_folded = files_touched = 0
    for path in files:
        changed, folded = _migrate_file(path, write=write)
        if changed or folded:
            files_touched += 1
            total_changed += changed
            total_folded += folded
            print(f"{path.name}: {changed} group(s) rewritten, {folded} span set(s) folded in.")

    verb = "Rewrote" if write else "DRY RUN -- would rewrite"
    print(
        f"\n{verb} {total_changed} group(s) across {files_touched} of {len(files)} file(s);"
        f" {total_folded} group(s) had emphasis_spans folded into ai_text."
    )
    if not write:
        print("Re-run with --write to apply. Every written file is backed up first.")


if __name__ == "__main__":
    app()

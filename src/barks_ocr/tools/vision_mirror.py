"""Copy vision-pass annotations from one OCR engine's groups onto the other's.

The vision pass runs against a single engine, because the two engines' group ids
do not correspond and writing the other one blind would invent an attribution for
an unrelated text box.  That is still true.  What it leaves behind is a problem
for a different reason: **the two engines are supposed to be converging.**

The corpus carries both engines all the way through so that their differences can
be reviewed and reconciled — `ocr_check` and the kivy editor exist for that — until
the two files say the same thing and can collapse into one set of finals.
Measured 2026-08-03, vols 1-18 are at 99.6% identical text and vols 19+ at 90.0%.

Against that, a vision run *adds* differences: every bold run it writes onto one
engine is a new discrepancy for a human to reconcile later.  `Plenty of Pets`
alone produced 219 of them in one sitting.  So mirroring is not about preserving
the annotations, which are cheap to redo; it is about the vision pass not
undoing the reconciliation work it is meant to help finish.

Matching is by text, not by group id.  Two groups are the same balloon when their
stored words agree, which after Gemini's grouping is true of 99.7% of annotated
groups.  Where several groups on a page share the same words — "YES," twice in one
panel — the nearest text box wins, so the pairing stays one-to-one.

Emphasis is held to a stricter test than the speaker fields.  A speaker call is
about the art and travels with the balloon, so whitespace differences do not
matter.  Markup indexes the characters of a specific string, so it is copied only
when the source's stripped text matches the target's stored text **exactly**,
newlines included — the same guard `vision_apply` applies to its own output.
Anything short of that is left alone and reported: a group whose words genuinely
differ between engines is an unreconciled difference, and silently overwriting one
side with the other would destroy the evidence rather than the discrepancy.

Dry run by default, and every file it writes is backed up first.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comics_utils import get_backup_file
from barks_fantagraphics.ocr_file_paths import OCR_PRELIM_BACKUP_DIR, OCR_PRELIM_DIR
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from barks_fantagraphics.speech_markup import strip_markup
from comic_utils.common_typer_options import LogLevelArg, TitleArg, VolumesArg
from loguru import logger

from barks_ocr.cli_setup import get_comic_titles, init_logging
from barks_ocr.utils.vision_schema import (
    CAP_COLOUR_KEY,
    SPEAKER_CONFIDENCE_KEY,
    SPEAKER_KEY,
    SPEAKER_REVIEWED_KEY,
    VISION_NOTE_KEY,
)

APP_LOGGING_NAME = "vismir"

# Everything the vision pass and the editor write onto a group, except the
# emphasis that lives inside `ai_text` and is handled separately below.
#
# `speaker_reviewed` is mirrored deliberately. A human's answer to "who is
# speaking here" is about the art, not about which engine transcribed the
# balloon, and the two files are destined to become one -- so leaving the flag
# off one side would only manufacture a difference to reconcile later.
MIRRORED_KEYS = (
    SPEAKER_KEY,
    SPEAKER_CONFIDENCE_KEY,
    CAP_COLOUR_KEY,
    SPEAKER_REVIEWED_KEY,
    VISION_NOTE_KEY,
    "vision_text_ok",
    "vision_corrected_text",
)


def _match_key(ai_text: str | None) -> str:
    """Return the whitespace-insensitive key two groups are paired on."""
    return " ".join(strip_markup(ai_text or "").split())


def _centre(text_box: Any) -> tuple[float, float]:  # noqa: ANN401 -- stored as raw JSON.
    """Return the centre of a four-corner text box."""
    if not text_box:
        return (0.0, 0.0)
    xs = [float(p[0]) for p in text_box]
    ys = [float(p[1]) for p in text_box]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _distance(a: Any, b: Any) -> float:  # noqa: ANN401 -- stored as raw JSON.
    """Return the squared distance between two text boxes' centres."""
    ax, ay = _centre(a)
    bx, by = _centre(b)
    return (ax - bx) ** 2 + (ay - by) ** 2


def _is_annotated(group: dict) -> bool:
    """Return whether the vision pass has touched this group."""
    return bool(group.get(SPEAKER_KEY)) or any(
        group.get(k) is not None for k in (VISION_NOTE_KEY, "vision_text_ok")
    )


@dataclass
class MirrorReport:
    """What one run did, and what it refused to do."""

    pages: int = 0
    annotated: int = 0
    fields_copied: int = 0
    markup_copied: int = 0
    markup_skipped: list[str] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)
    pages_written: int = 0

    def log(self, *, dry_run: bool) -> None:
        """Print the run's tally, loudest thing last."""
        what = "would copy" if dry_run else "copied"
        logger.info(
            f"{self.pages} page(s), {self.annotated} annotated group(s): "
            f"{what} fields onto {self.fields_copied}, markup onto {self.markup_copied}."
        )
        # The two buckets are different kinds of unreconciled difference, and
        # saying so is the point: pairing is whitespace-insensitive, so a group
        # that paired at all already agrees word for word. Only its line breaks
        # can still differ, and that is enough to make the tags unsafe.
        if self.markup_skipped:
            logger.warning(
                f"{len(self.markup_skipped)} group(s) agree word for word but break their "
                f"lines differently, so emphasis was NOT copied -- a tag would land on the "
                f"wrong line. Reconcile the line breaks and re-run:"
            )
            for line in self.markup_skipped:
                logger.warning(f"  {line}")
        if self.unmatched:
            logger.warning(
                f"{len(self.unmatched)} annotated group(s) have no counterpart -- the engines "
                f"still disagree about these words, so nothing was copied:"
            )
            for line in self.unmatched:
                logger.warning(f"  {line}")


def _build_index(groups: dict) -> dict[str, list[tuple[str, dict]]]:
    """Return the target's groups bucketed by their match key."""
    index: dict[str, list[tuple[str, dict]]] = {}
    for gid, group in groups.items():
        index.setdefault(_match_key(group.get("ai_text")), []).append((gid, group))
    return index


def mirror_page(src_groups: dict, dst_groups: dict, where: str, report: MirrorReport) -> bool:
    """Mirror one page's annotations from *src_groups* onto *dst_groups*.

    Args:
        src_groups: The annotated engine's ``groups`` dict.
        dst_groups: The other engine's ``groups`` dict, modified in place.
        where: A short "title page" label used in the report lines.
        report: The running tally, updated in place.

    Returns:
        Whether anything in *dst_groups* changed.

    """
    index = _build_index(dst_groups)
    used: set[str] = set()
    changed = False

    for gid, src in sorted(src_groups.items(), key=lambda kv: int(kv[0])):
        if not _is_annotated(src):
            continue
        report.annotated += 1

        key = _match_key(src.get("ai_text"))
        candidates = [(i, g) for i, g in index.get(key, []) if i not in used]
        if not candidates:
            report.unmatched.append(f"{where} g{gid}: {_match_key(src.get('ai_text'))[:60]!r}")
            continue
        # Several balloons on a page can carry identical words. Pairing the
        # nearest boxes keeps the mapping one-to-one instead of piling every
        # copy onto whichever happens to be first.
        dst_gid, dst = min(
            candidates, key=lambda c: _distance(src.get("text_box"), c[1].get("text_box"))
        )
        used.add(dst_gid)

        for stored_key in MIRRORED_KEYS:
            if src.get(stored_key) != dst.get(stored_key):
                dst[stored_key] = src.get(stored_key)
                changed = True
        report.fields_copied += 1

        # Markup indexes a specific string, so it only travels when the two
        # engines store exactly the same characters -- newlines included, since
        # a tag placed against different line breaks would land on the wrong
        # word. Both sides are compared stripped rather than the source's
        # stripped text against the target's raw text: the latter would report a
        # false word-difference on every re-run, once the target already carries
        # the tags this tool put there.
        markup = src.get("ai_text") or ""
        if strip_markup(markup) == markup:
            continue
        dst_text = dst.get("ai_text") or ""
        if strip_markup(markup) == strip_markup(dst_text):
            if dst_text != markup:
                dst["ai_text"] = markup
                changed = True
            report.markup_copied += 1
        else:
            report.markup_skipped.append(f"{where} g{gid} -> g{dst_gid}")

    return changed


def mirror_title(  # noqa: PLR0913 -- src/dst engines and the shared report are all needed.
    speech_groups: SpeechGroups,
    title: Any,  # noqa: ANN401 -- the database's Titles enum.
    src_engine: OcrTypes,
    dst_engine: OcrTypes,
    report: MirrorReport,
    *,
    dry_run: bool,
) -> None:
    """Mirror every page of one title."""
    by_page: dict[str, dict[OcrTypes, Any]] = {}
    for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True):
        by_page.setdefault(page_group.fanta_page, {})[page_group.ocr_index] = page_group

    for page, engines in sorted(by_page.items()):
        src = engines.get(src_engine)
        dst = engines.get(dst_engine)
        if src is None or dst is None:
            continue
        report.pages += 1
        src_json = src.speech_page_json.get("groups", {})
        dst_json = dst.speech_page_json.get("groups", {})
        if not mirror_page(src_json, dst_json, f"{page}", report):
            continue
        if dry_run:
            report.pages_written += 1
            continue

        ocr_file = dst.ocr_prelim_groups_json_file
        backup_file = Path(
            str(get_backup_file(ocr_file)).replace(str(OCR_PRELIM_DIR), str(OCR_PRELIM_BACKUP_DIR))
        )
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        dst.save_json(backup_file=backup_file)
        report.pages_written += 1


app = typer.Typer()


@app.command(help="Mirror vision-pass annotations from one OCR engine's groups onto the other's.")
def main(  # noqa: PLR0913 -- one Typer option per CLI flag.
    volumes_str: VolumesArg = "",
    title_str: TitleArg = "",
    src_engine_str: Annotated[
        str, typer.Option("--from-engine", help="Engine the vision pass annotated.")
    ] = OcrTypes.EASYOCR.value,
    dst_engine_str: Annotated[
        str, typer.Option("--to-engine", help="Engine to copy the annotations onto.")
    ] = OcrTypes.PADDLEOCR.value,
    write: Annotated[
        bool, typer.Option("--write", help="Actually write. Without this it is a dry run.")
    ] = False,
    log_level_str: LogLevelArg = "INFO",
) -> None:
    """Copy speaker attributions and emphasis across engines, by text match."""
    init_logging(APP_LOGGING_NAME, "vision-mirror.log", log_level_str)

    src_engine = OcrTypes(src_engine_str)
    dst_engine = OcrTypes(dst_engine_str)
    if src_engine == dst_engine:
        logger.error("--from-engine and --to-engine must differ.")
        raise typer.Exit(code=1)

    comics_database, titles = get_comic_titles(volumes_str, title_str)
    speech_groups = SpeechGroups(comics_database)

    report = MirrorReport()
    for title_str_name in titles:
        title = STR_TITLE_TO_ENUM[title_str_name]
        mirror_title(speech_groups, title, src_engine, dst_engine, report, dry_run=not write)

    report.log(dry_run=not write)
    if not write:
        logger.info(f"DRY RUN -- {report.pages_written} page(s) would be written. Use --write.")
    else:
        logger.info(f"Wrote {report.pages_written} page(s) of {dst_engine.value}.")


if __name__ == "__main__":
    app()

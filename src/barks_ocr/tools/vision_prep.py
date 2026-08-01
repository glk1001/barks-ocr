# ruff: noqa: T201
"""Prepare comic pages for a Claude Code vision pass.

Crops each page into per-panel PNGs, writes a downscaled page overview, and dumps
the existing OCR groups as a compact JSON stub.  The output directory is then read
by Claude Code (see ``vision_apply.py`` for the write-back side).

**A story is the unit of work**, not a volume: ``--title`` is the primary
selector.  The closed vocabulary the pass is validated against is per-story --
it is the roster plus the characters the database tags as appearing in *this*
story -- so a run spanning several stories can only be handed the union of their
casts, which is looser and lets the pass name someone from the wrong story.
``--volume`` with ``--pages`` still works for a deliberate page range, and warns
when the range crosses titles.

Every emitted image is quantized to a 256-colour palette.  This is not cosmetic:
Claude Code's Read tool re-encodes any image over ~500KB as reduced-quality JPEG,
which destroys the fine lettering that bold detection depends on.  Barks line art
is flat colour, so a 256-colour palette is visually lossless and keeps every panel
comfortably under the threshold.  Plain ``save("PNG")`` is NOT safe -- it exceeds
500KB on roughly a third of the panels in the larger volumes.
"""

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from barks_fantagraphics.barks_titles import STR_TITLE_TO_ENUM
from barks_fantagraphics.comic_book_info import ONE_PAGERS
from barks_fantagraphics.comics_consts import PNG_FILE_EXT, PageType
from barks_fantagraphics.comics_database import ComicsDatabase
from barks_fantagraphics.comics_helpers import get_title_from_volume_page
from barks_fantagraphics.panel_boxes import PagePanelBoxes, TitlePanelBoxes
from barks_fantagraphics.speech_groupers import OcrTypes, SpeechGroups
from loguru import logger
from PIL import Image

from barks_ocr.utils.story_cast import story_characters
from barks_ocr.utils.vision_schema import (
    BEATS_KEY,
    CAPTURE_MODEL_KEY,
    CAPTURE_PROMPT_VERSION_KEY,
    CAPTURED_KEY,
    CHARACTERS_KEY,
    PANELS_OF_NOTE_KEY,
    SETTING_KEY,
    TIME_OF_DAY_KEY,
    VISIBLE_TEXT_KEY,
    roster_text,
)

app = typer.Typer()

# The per-page capture template. Written with this page's panel numbers already
# filled in, so `panels_of_note` is a choice from a list rather than a guess at
# how many panels the page has.
CAPTURE_STUB_FILE = "page-capture.json"

# The vocabulary file dropped next to the queue. The roster is enforced only when
# `vision_apply` validates, so it has to travel with the crops — otherwise the
# session doing the reading has to be told the names out of band, and a run that
# writes "Uncle Scrooge" for "Scrooge" fails after all the work is done.
ROSTER_FILE = "roster.txt"

# Claude Code recompresses images above this size; stay well under it.
MAX_IMAGE_BYTES = 500 * 1024
PALETTE_SIZE = 256
# The overview only supplies cross-panel context (reading order, who is in frame),
# so it does not need lettering-grade resolution.
OVERVIEW_LONG_EDGE = 1500
CROP_PAD_PX = 8

# Under $HOME, not /tmp: snap-confined browsers get a private /tmp namespace and
# cannot open a report written there.
DEFAULT_ROOT = Path("~/barks-vision")

# Fields the vision pass needs to judge against. Everything else is noise.
GROUP_FIELDS = ("ai_text", "text_box", "type", "panel_num")


def _save_quantized(image: Image.Image, out_file: Path) -> int:
    """Save ``image`` as a 256-colour PNG; return its size in bytes."""
    image.convert("RGB").quantize(colors=PALETTE_SIZE).save(out_file, "PNG", optimize=True)
    return out_file.stat().st_size


def _crop_panel(page_image: Image.Image, box: Any, pad: int) -> Image.Image:  # noqa: ANN401
    """Crop one padded panel, clipped to the page."""
    x0 = max(0, box.x0 - pad)
    y0 = max(0, box.y0 - pad)
    x1 = min(page_image.width, box.x0 + box.w + pad)
    y1 = min(page_image.height, box.y0 + box.h + pad)
    return page_image.crop((x0, y0, x1, y1))


def _write_overview(page_image: Image.Image, out_file: Path) -> int:
    overview = page_image.copy()
    overview.thumbnail((OVERVIEW_LONG_EDGE, OVERVIEW_LONG_EDGE), Image.Resampling.LANCZOS)
    return _save_quantized(overview, out_file)


def _page_image_file(comics_database: ComicsDatabase, title_str: str, fanta_page: str) -> Path:
    """Return the restored *colour* page -- same coordinate space as the panel boxes."""
    if STR_TITLE_TO_ENUM[title_str] in ONE_PAGERS:
        # One-pagers have no ini file, so 'get_comic_book' can't resolve them.
        volume = comics_database.get_fanta_volume_int(title_str)
        image_dir = comics_database.get_fantagraphics_restored_volume_image_dir(volume)
        return Path(image_dir) / (fanta_page + PNG_FILE_EXT)

    comic = comics_database.get_comic_book(title_str)
    return comic.get_final_srce_story_file(fanta_page, PageType.BODY)[0]


def _trimmed_groups(speech_page_json: dict) -> dict:
    """Reduce the existing groups to just what the vision pass judges against."""
    return {
        group_id: {field: group.get(field) for field in GROUP_FIELDS}
        for group_id, group in speech_page_json.get("groups", {}).items()
    }


def _find_page_group(
    speech_groups: SpeechGroups, title_str: str, fanta_page: str, engine: OcrTypes
) -> Any | None:  # noqa: ANN401
    """Return the SpeechPageGroup for one page/engine, or None if absent."""
    title = STR_TITLE_TO_ENUM[title_str]
    for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True):
        if page_group.ocr_index == engine and page_group.fanta_page == fanta_page:
            return page_group
    return None


def _prep_page(  # noqa: PLR0913
    comics_database: ComicsDatabase,
    speech_groups: SpeechGroups,
    title_panel_boxes: TitlePanelBoxes,
    volume: int,
    fanta_page: str,
    engine: OcrTypes,
    out_dir: Path,
) -> dict:
    """Write one page's crops, overview and group stub. Returns its queue entry."""
    title_str, _comic_page = get_title_from_volume_page(comics_database, volume, fanta_page)

    page_group = _find_page_group(speech_groups, title_str, fanta_page, engine)
    if page_group is None:
        msg = f'No {engine.value} groups for volume {volume} page {fanta_page} ("{title_str}").'
        raise typer.BadParameter(msg)

    page_file = _page_image_file(comics_database, title_str, fanta_page)
    if not page_file.is_file():
        msg = f'Page image not found: "{page_file}".'
        raise typer.BadParameter(msg)

    page_image = Image.open(page_file).convert("RGB")
    page_panel_boxes: PagePanelBoxes = title_panel_boxes.get_page_panel_boxes(
        STR_TITLE_TO_ENUM[title_str]
    ).pages[fanta_page]

    page_dir = out_dir / fanta_page
    page_dir.mkdir(parents=True, exist_ok=True)

    oversized: list[str] = []
    overview_bytes = _write_overview(page_image, page_dir / "page.png")
    if overview_bytes > MAX_IMAGE_BYTES:
        oversized.append(f"page.png ({overview_bytes // 1024}KB)")

    panel_files: list[str] = []
    for panel_box in page_panel_boxes.panel_boxes:
        name = f"panel-{panel_box.panel_num:02d}.png"
        size = _save_quantized(_crop_panel(page_image, panel_box, CROP_PAD_PX), page_dir / name)
        if size > MAX_IMAGE_BYTES:
            oversized.append(f"{name} ({size // 1024}KB)")
        panel_files.append(name)

    if oversized:
        # Failing loudly beats silently handing Claude Code a JPEG-mangled crop.
        msg = (
            f"Page {fanta_page}: {len(oversized)} image(s) exceed"
            f" {MAX_IMAGE_BYTES // 1024}KB and would be recompressed: {', '.join(oversized)}."
        )
        raise typer.BadParameter(msg)

    groups = _trimmed_groups(page_group.speech_page_json)
    (page_dir / "groups.json").write_text(json.dumps(groups, indent=2) + "\n")

    panel_nums = [box.panel_num for box in page_panel_boxes.panel_boxes]
    (page_dir / CAPTURE_STUB_FILE).write_text(_capture_stub(panel_nums))

    return {
        "fanta_page": fanta_page,
        "title": title_str,
        "engine": engine.value,
        "panels": panel_files,
        "panel_nums": panel_nums,
        "num_groups": len(groups),
        "status": "pending",
    }


def _capture_stub(panel_nums: list[int]) -> str:
    """Return the empty page-capture record for a page with these panels."""
    stub = {
        CHARACTERS_KEY: [],
        SETTING_KEY: None,
        TIME_OF_DAY_KEY: None,
        VISIBLE_TEXT_KEY: [],
        BEATS_KEY: [],
        # Pre-listed so the choice is which of these panels is worth naming.
        # Most pages need none; listing them all defeats the point.
        PANELS_OF_NOTE_KEY: [],
        "_panels_on_this_page": panel_nums,
        CAPTURE_MODEL_KEY: None,
        CAPTURE_PROMPT_VERSION_KEY: None,
        CAPTURED_KEY: None,
    }
    return json.dumps(stub, indent=2) + "\n"


def _default_out_dir(volume: int, pages: list[str]) -> Path:
    """Return the default work directory for a volume and page list.

    Deliberately under ``$HOME`` rather than ``/tmp``: a snap-confined browser
    gets a private ``/tmp`` namespace, so a report written there is unreachable
    from ``file:///tmp/...`` no matter what the permissions say.
    """
    span = pages[0] if len(pages) == 1 else f"{pages[0]}-{pages[-1]}"
    return DEFAULT_ROOT.expanduser() / f"vol{volume:02d}-{span}"


def _slug(title_str: str) -> str:
    """Return a directory-safe form of a story title."""
    keep = "".join(c.lower() if c.isalnum() else "-" for c in title_str)
    return "-".join(filter(None, keep.split("-")))


def _parse_pages(pages_str: str) -> list[str]:
    """Expand '076-085' or '076,079' into zero-padded page strings."""
    pages: list[str] = []
    for part in pages_str.split(","):
        chunk = part.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start, end = chunk.split("-", 1)
            pages.extend(f"{n:03d}" for n in range(int(start), int(end) + 1))
        else:
            pages.append(f"{int(chunk):03d}")
    if not pages:
        msg = f'Could not parse any pages from "{pages_str}".'
        raise typer.BadParameter(msg)
    return pages


def _title_pages(speech_groups: SpeechGroups, title_str: str, engine: OcrTypes) -> list[str]:
    """Return every page of one title that has OCR for this engine."""
    title = STR_TITLE_TO_ENUM[title_str]
    pages = sorted(
        {
            page_group.fanta_page
            for page_group in speech_groups.get_speech_page_groups(title, skip_missing=True)
            if page_group.ocr_index == engine
        }
    )
    if not pages:
        msg = f'No {engine.value} OCR pages found for "{title_str}".'
        raise typer.BadParameter(msg)
    return pages


def _cast_for(entries: list[dict]) -> tuple[list[str], list[str]]:
    """Return the closed-set cast for a prepped run, and the titles it spans.

    A single title gets exactly its own tagged characters.  A page range that
    happens to cross stories gets the union, which is looser -- the pass can
    then name a character from a story that is not the one in front of it.
    That is the argument for running per title, so the caller is told.
    """
    titles = sorted({entry["title"] for entry in entries})
    cast = sorted({name for t in titles for name in story_characters(STR_TITLE_TO_ENUM[t])})
    return cast, titles


@app.command(help="Crop comic pages into per-panel images for a Claude Code vision pass.")
def main(
    title_str: Annotated[
        str, typer.Option("--title", "-t", help="Story title. The unit the pass is built around.")
    ] = "",
    volume: Annotated[
        int | None,
        typer.Option("--volume", "-v", help="Fantagraphics volume number (with --pages)."),
    ] = None,
    pages_str: Annotated[
        str, typer.Option("--pages", "-p", help="Page range or list, e.g. '076-085' or '076,079'.")
    ] = "",
    out_dir: Annotated[
        Path | None,
        typer.Option(
            "--out-dir",
            "-o",
            help=f"Where to write the work queue (default: under {DEFAULT_ROOT}).",
        ),
    ] = None,
    engine: Annotated[
        OcrTypes, typer.Option("--engine", "-e", help="Which OCR pass to annotate.")
    ] = OcrTypes.EASYOCR,
) -> None:
    if bool(title_str) == bool(volume is not None or pages_str):
        msg = "Give either --title, or --volume with --pages."
        raise typer.BadParameter(msg)

    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    title_panel_boxes = TitlePanelBoxes(comics_database)

    if title_str:
        volume = comics_database.get_fanta_volume_int(title_str)
        pages = _title_pages(speech_groups, title_str, engine)
        out_dir = out_dir or DEFAULT_ROOT.expanduser() / _slug(title_str)
    else:
        if volume is None or not pages_str:
            msg = "--volume and --pages must be given together."
            raise typer.BadParameter(msg)
        pages = _parse_pages(pages_str)
        out_dir = out_dir or _default_out_dir(volume, pages)

    out_dir.mkdir(parents=True, exist_ok=True)
    entries = [
        _prep_page(
            comics_database,
            speech_groups,
            title_panel_boxes,
            volume,
            fanta_page,
            engine,
            out_dir,
        )
        for fanta_page in pages
    ]

    cast, titles = _cast_for(entries)
    queue_file = out_dir / "queue.json"
    queue = {
        "volume": volume,
        "engine": engine.value,
        "titles": titles,
        "story_cast": cast,
        "pages": entries,
    }
    queue_file.write_text(json.dumps(queue, indent=2) + "\n")

    # Rewritten every run, so a roster entry added later reaches the next pass.
    roster_file = out_dir / ROSTER_FILE
    roster_file.write_text(roster_text(cast))

    if len(titles) > 1:
        logger.warning(
            f"These pages span {len(titles)} titles, so the character list is the union"
            " of their casts and is looser than a per-title run would give."
        )

    total_panels = sum(len(e["panels"]) for e in entries)
    total_groups = sum(e["num_groups"] for e in entries)
    logger.info(f'Wrote queue file "{queue_file}".')
    logger.info(f'Wrote roster file "{roster_file}".')
    print(
        f"Prepared {len(entries)} page(s), {total_panels} panel(s), {total_groups} group(s)"
        f' in "{out_dir}".'
    )
    print(
        f'Read "{roster_file}" before the vision pass'
        " — it is what result.json will be validated against."
    )
    print("\nNext:")
    print(f"  barks-ocr-vision-report --out-dir {out_dir}")
    print(f"  barks-ocr-vision-apply  --out-dir {out_dir} --dry-run")


if __name__ == "__main__":
    app()

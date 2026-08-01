# ruff: noqa: T201
"""Prepare comic pages for a Claude Code vision pass.

Crops each page into per-panel PNGs, writes a downscaled page overview, and dumps
the existing OCR groups as a compact JSON stub.  The output directory is then read
by Claude Code (see ``vision_apply.py`` for the write-back side).

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

app = typer.Typer()

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

    return {
        "fanta_page": fanta_page,
        "title": title_str,
        "engine": engine.value,
        "panels": panel_files,
        "num_groups": len(groups),
        "status": "pending",
    }


def _default_out_dir(volume: int, pages: list[str]) -> Path:
    """Return the default work directory for a volume and page list.

    Deliberately under ``$HOME`` rather than ``/tmp``: a snap-confined browser
    gets a private ``/tmp`` namespace, so a report written there is unreachable
    from ``file:///tmp/...`` no matter what the permissions say.
    """
    span = pages[0] if len(pages) == 1 else f"{pages[0]}-{pages[-1]}"
    return DEFAULT_ROOT.expanduser() / f"vol{volume:02d}-{span}"


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


@app.command(help="Crop comic pages into per-panel images for a Claude Code vision pass.")
def main(
    volume: Annotated[int, typer.Option("--volume", "-v", help="Fantagraphics volume number.")],
    pages_str: Annotated[
        str, typer.Option("--pages", "-p", help="Page range or list, e.g. '076-085' or '076,079'.")
    ],
    out_dir: Annotated[
        Path | None,
        typer.Option(
            "--out-dir",
            "-o",
            help=f"Where to write the work queue (default: {DEFAULT_ROOT}/vol<N>-<pages>).",
        ),
    ] = None,
    engine: Annotated[
        OcrTypes, typer.Option("--engine", "-e", help="Which OCR pass to annotate.")
    ] = OcrTypes.EASYOCR,
) -> None:
    pages = _parse_pages(pages_str)
    out_dir = out_dir or _default_out_dir(volume, pages)
    comics_database = ComicsDatabase()
    speech_groups = SpeechGroups(comics_database)
    title_panel_boxes = TitlePanelBoxes(comics_database)

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

    queue_file = out_dir / "queue.json"
    queue = {"volume": volume, "engine": engine.value, "pages": entries}
    queue_file.write_text(json.dumps(queue, indent=2) + "\n")

    total_panels = sum(len(e["panels"]) for e in entries)
    total_groups = sum(e["num_groups"] for e in entries)
    logger.info(f'Wrote queue file "{queue_file}".')
    print(
        f"Prepared {len(entries)} page(s), {total_panels} panel(s), {total_groups} group(s)"
        f' in "{out_dir}".'
    )
    print("\nNext:")
    print(f"  barks-ocr-vision-report --out-dir {out_dir}")
    print(f"  barks-ocr-vision-apply  --out-dir {out_dir} --dry-run")


if __name__ == "__main__":
    app()

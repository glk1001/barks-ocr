#!/usr/bin/env python3
"""Parse a directory of .jpg images with LlamaParse and save .md and .json output files.

Each image may be a single book page or a two-page spread. For a landscape image
(width > height) the items in the JSON are tagged with ``book_side`` ("left" or
"right") based on their bbox center-x, so the EPUB build can split the spread into
two book pages; a portrait image is left untagged and becomes one book page.

LlamaParse's agentic tier describes a scanned illustration as a text item (bbox label
``image``, markdown ``illustration: ...``) instead of extracting it. Each such region is
cropped out of the source scan into ``<stem>_fig_<n>.png`` and the item is rewritten as
a ``type: image`` item (``url`` + ``md`` alt text) so the EPUB build embeds the figure.
"""

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import typer
from dotenv import load_dotenv
from llama_cloud import LlamaCloud
from llama_cloud.types.parsing_get_response import MarkdownPageMarkdownResultPage, MetadataPage
from loguru import logger
from PIL import Image

if TYPE_CHECKING:
    from llama_cloud.types import ParsingGetResponse

app = typer.Typer(add_completion=False)

TIER = "agentic"
VERSION = "latest"
CUSTOM_PROMPT = (
    "This image is a two-page book spread. Parse the LEFT page in full first, in reading "
    "order (top to bottom, respecting any multi-column layout within that page). Then parse "
    "the RIGHT page in full, in reading order. Insert a clear page break between the two "
    "pages and do not interleave content across the gutter. If the image contains only one "
    "page, parse just that page. Ignore the dark scanner background around the pages."
)

load_dotenv(Path(__file__).parent.parent.parent / ".env.runtime")


def _printed_page_numbers(result: "ParsingGetResponse") -> dict[int, str]:
    """Extract printed page numbers from parse result metadata.

    Args:
        result: The LlamaParse get response.

    Returns:
        Mapping of LlamaParse page_number → printed page number string.

    """
    if result.metadata is None:
        return {}
    return {
        p.page_number: p.printed_page_number
        for p in result.metadata.pages
        if isinstance(p, MetadataPage) and p.printed_page_number is not None
    }


def _image_rename_map(result: "ParsingGetResponse", stem: str) -> dict[str, str]:
    """Build a filename rename map to prefix extracted images with the source stem.

    Args:
        result: The LlamaParse get response.
        stem: Source image filename stem (e.g. "CBatAotCB-000-00-fc").

    Returns:
        Mapping of original filename → prefixed filename.

    """
    if result.images_content_metadata is None:
        return {}
    return {img.filename: f"{stem}_{img.filename}" for img in result.images_content_metadata.images}


def _download_images(
    result: "ParsingGetResponse",
    rename: dict[str, str],
    output_dir: Path,
    referenced: set[str],
) -> None:
    """Download extracted images from presigned URLs into output_dir.

    Only downloads images whose original filename is in `referenced` (i.e. actually
    cited in the parsed content), skipping unreferenced full-page copies.

    Args:
        result: The LlamaParse get response.
        rename: Mapping of original filename → target filename.
        output_dir: Directory to write downloaded images into.
        referenced: Set of original filenames referenced in the parsed items/markdown.

    """
    if result.images_content_metadata is None:
        return
    for img in result.images_content_metadata.images:
        if img.filename not in referenced:
            logger.debug(f"  Skipping unreferenced image {img.filename}")
            continue
        if img.presigned_url is None:
            logger.warning(f"  No presigned URL for {img.filename}, skipping")
            continue
        img_path = output_dir / rename[img.filename]
        response = httpx.get(img.presigned_url)
        response.raise_for_status()
        img_path.write_bytes(response.content)
        logger.info(f"  Wrote {img_path}")


def _bbox_center_x(bbox: Any) -> float | None:  # noqa: ANN401
    """Return the horizontal center of a LlamaParse bbox, or None if unavailable.

    LlamaParse stores ``bbox`` as a list of region dicts (each with ``x``, ``y``, ``w``,
    ``h``); this returns the center-x of the first region. Also tolerates the case where
    ``bbox`` is a bare dict.
    """
    region = bbox[0] if isinstance(bbox, list) and bbox else bbox
    if not isinstance(region, dict):
        return None
    x = region.get("x")
    w = region.get("w")
    if x is None or w is None:
        return None
    return float(x) + float(w) / 2


def _tag_book_side(items_data: dict) -> None:
    """Annotate items on landscape pages with ``book_side`` = "left"|"right".

    A landscape page (``page_width`` > ``page_height``) is taken to be a two-page
    spread and each item is tagged by its bbox center-x against the page midpoint,
    in LlamaParse's own page-space units. Portrait pages are single book pages and
    are left untagged.

    Args:
        items_data: Dumped items result (modified in place).

    """
    for page in items_data.get("pages", []):
        page_width = page.get("page_width")
        page_height = page.get("page_height")
        if page_width is None or page_height is None or float(page_width) <= float(page_height):
            continue
        mid = float(page_width) / 2
        items = page.get("items", [])
        for item in items:
            cx = _bbox_center_x(item.get("bbox") or item.get("bBox"))
            if cx is None:
                continue
            item["book_side"] = "left" if cx < mid else "right"
        # An item with no bbox (a chapter heading, typically) takes the side of the next
        # tagged item in reading order, else the previous one; the build drops untagged
        # items on a tagged spread.
        for idx, item in enumerate(items):
            if "book_side" in item:
                continue
            neighbours = items[idx + 1 :] + items[idx - 1 :: -1] if idx else items[idx + 1 :]
            side = next((n["book_side"] for n in neighbours if "book_side" in n), None)
            if side is not None:
                item["book_side"] = side


def _bbox_label(item: dict) -> str | None:
    """Return the layout label of an item's first bbox region, or None."""
    bbox = item.get("bbox") or item.get("bBox")
    region = bbox[0] if isinstance(bbox, list) and bbox else bbox
    if not isinstance(region, dict):
        return None
    label = region.get("label")
    return label if isinstance(label, str) else None


def _crop_figures(items_data: dict, image_path: Path, output_dir: Path, stem: str) -> None:
    """Crop ``image``-labelled regions from the scan and turn them into image items.

    The bbox is in LlamaParse page-space units; the scale to scan pixels is the scan's
    pixel width over ``page_width``. A small margin is added around each crop so a
    panel border is not clipped. The item is rewritten in place: ``type`` becomes
    ``image``, ``url`` names the PNG, ``caption`` is empty and ``md`` keeps LlamaParse's
    description as the alt text.

    Args:
        items_data: Dumped items result (modified in place).
        image_path: The source scan the items were parsed from.
        output_dir: Directory to write the cropped PNGs into.
        stem: Source image filename stem used to prefix the crop filenames.

    """
    margin_units = 1.0
    min_crop_px = 2
    fig_num = 0
    with Image.open(image_path) as scan:
        for page in items_data.get("pages", []):
            page_width = page.get("page_width")
            if page_width is None:
                continue
            scale = scan.width / float(page_width)
            for item in page.get("items", []):
                # Either a text item LlamaParse used to describe the drawing, or a native
                # image item it returned with no file behind it; both carry an image bbox.
                if item.get("url") or _bbox_label(item) != "image":
                    continue
                bbox = item.get("bbox") or item.get("bBox")
                region = bbox[0]
                x0 = max(0, round((float(region["x"]) - margin_units) * scale))
                y0 = max(0, round((float(region["y"]) - margin_units) * scale))
                x1 = min(
                    scan.width,
                    round((float(region["x"]) + float(region["w"]) + margin_units) * scale),
                )
                y1 = min(
                    scan.height,
                    round((float(region["y"]) + float(region["h"]) + margin_units) * scale),
                )
                if x1 - x0 < min_crop_px or y1 - y0 < min_crop_px:
                    logger.warning(f"  Skipping degenerate figure bbox {region} on {stem}")
                    continue
                fig_num += 1
                fig_name = f"{stem}_fig_{fig_num}.png"
                scan.crop((x0, y0, x1, y1)).save(output_dir / fig_name, format="PNG")
                description = (item.get("md") or item.get("value") or "").strip()
                description = description.removeprefix("illustration:").strip()
                item["type"] = "image"
                item["url"] = fig_name
                item["caption"] = ""
                item["md"] = f"![{description}]({fig_name})"
                logger.info(f"  Cropped figure {fig_num} -> {fig_name} ({x1 - x0}x{y1 - y0}px)")


def parse_image(
    client: LlamaCloud,
    image_path: Path,
    output_dir: Path,
    overwrite: bool,
) -> None:
    """Parse a single image and write .md and .json output files.

    Args:
        client: Authenticated LlamaCloud client.
        image_path: Path to the .jpg image file.
        output_dir: Directory to write output files into.
        overwrite: If False, skip files whose outputs already exist.

    """
    stem = image_path.stem
    md_path = output_dir / f"{stem}.md"
    json_path = output_dir / f"{stem}.json"

    if not overwrite and md_path.exists() and json_path.exists():
        logger.info(f"Skipping {image_path.name} (outputs already exist)")
        return

    logger.info(f"Parsing {image_path.name} ...")

    with image_path.open("rb") as f:
        job = client.parsing.create(
            upload_file=(image_path.name, f, "image/jpeg"),
            tier=TIER,
            version=VERSION,
            agentic_options={"custom_prompt": CUSTOM_PROMPT},
            output_options={
                "extract_printed_page_number": True,
                "markdown": {"inline_images": False},
                "images_to_save": ["embedded"],
            },
            processing_options={
                "disable_heuristics": False,
                "ocr_parameters": {"languages": ["en"]},
            },
        )

    logger.debug(f"  Job ID: {job.id} — waiting for completion ...")
    client.parsing.wait_for_completion(job.id, verbose=False)

    result: ParsingGetResponse = client.parsing.get(
        job.id, expand=["markdown", "items", "metadata", "images_content_metadata"]
    )

    logger.debug(
        f"  Result fields: markdown_full={result.markdown_full is not None}, "
        f"markdown={result.markdown is not None}, "
        f"text_full={result.text_full is not None}, "
        f"text={result.text is not None}, "
        f"items={result.items is not None}, "
        f"metadata={result.metadata}"
    )

    if result.markdown is not None:
        md_content = "\n\n".join(
            page.markdown
            for page in result.markdown.pages
            if isinstance(page, MarkdownPageMarkdownResultPage)
        )
    else:
        md_content = result.markdown_full or ""

    # e.g. "page_1_image_1_v2.jpg" -> "CBatAotCB-000-00-fc_page_1_image_1_v2.jpg"
    rename = _image_rename_map(result, stem)

    printed_page_numbers = _printed_page_numbers(result)
    for lp_num, printed in printed_page_numbers.items():
        logger.debug(f"  Page {lp_num} printed page number: {printed}")

    items_data = result.items.model_dump() if result.items is not None else {}
    for page in items_data.get("pages", []):
        lp_page_num = page.get("page_number")
        if lp_page_num in printed_page_numbers:
            page["printed_page_number"] = printed_page_numbers[lp_page_num]

    _tag_book_side(items_data)
    _crop_figures(items_data, image_path, output_dir, stem)

    # Collect original filenames actually referenced in item URLs.
    referenced: set[str] = {
        item["url"]
        for page in items_data.get("pages", [])
        for item in page.get("items", [])
        if item.get("type") == "image" and "url" in item
    }

    items_json = json.dumps(items_data, indent=2, ensure_ascii=False)
    for old, new in rename.items():
        items_json = items_json.replace(old, new)
    json_path.write_text(items_json, encoding="utf-8")
    logger.info(f"  Wrote {json_path}")

    for old, new in rename.items():
        md_content = md_content.replace(old, new)
    md_path.write_text(md_content, encoding="utf-8")
    logger.info(f"  Wrote {md_path}")

    _download_images(result, rename, output_dir, referenced)


@app.command()
def main(
    image_dir: Path = typer.Argument(..., help="Directory containing .jpg image files to parse."),  # noqa: B008
    output_dir: Path = typer.Option(  # noqa: B008
        None,
        "--output-dir",
        "-o",
        help="Directory to write output files (default: 'llama_parse' next to image_dir).",
    ),
    overwrite: bool = typer.Option(
        False,  # noqa: FBT003
        "--overwrite",
        help="Re-parse and overwrite existing output files.",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="LLAMA_CLOUD_API_KEY",
        help="LlamaCloud API key (or set LLAMA_CLOUD_API_KEY env var).",
    ),
) -> None:
    """Parse all .jpg files in IMAGE_DIR using LlamaParse, writing .md and .json outputs."""
    if not image_dir.is_dir():
        logger.error(f"Not a directory: {image_dir}")
        raise typer.Exit(1)

    resolved_output_dir = output_dir if output_dir is not None else image_dir.parent / "llama_parse"
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(image_dir.glob("*.jpg")) + sorted(image_dir.glob("*.JPG"))
    if not images:
        logger.warning(f"No .jpg files found in {image_dir}")
        raise typer.Exit(0)

    logger.info(f"Found {len(images)} image(s) in {image_dir}")

    resolved_api_key = api_key or os.environ.get("LLAMA_PARSE_API_KEY")
    if not resolved_api_key:
        logger.error("No API key found. Set LLAMA_CLOUD_API_KEY or pass --api-key.")
        raise typer.Exit(1)

    client = LlamaCloud(api_key=resolved_api_key)

    errors: list[str] = []
    for image_path in images:
        try:
            parse_image(client, image_path, resolved_output_dir, overwrite)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to parse {image_path.name}: {exc}")
            errors.append(image_path.name)

    if errors:
        logger.warning(f"{len(errors)} file(s) failed: {', '.join(errors)}")
        raise typer.Exit(1)

    logger.info("Done.")


if __name__ == "__main__":
    app()

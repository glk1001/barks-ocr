#!/usr/bin/env python3
"""Parse a PDF of two-page book spreads with LlamaParse for later ebook reconstruction.

Each PDF page is assumed to be an image of a two-page book spread. For each PDF page this
script renders a JPG, sends it to LlamaParse, and writes ``.md`` / ``.json`` outputs. Items
in the JSON are tagged with ``book_side`` ("left" or "right") based on their bbox center-x,
and a ``{pdf_stem}_manifest.json`` is written listing spreads in reading order with the
book page numbers they cover.
"""

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import pypdfium2 as pdfium
import typer
from dotenv import load_dotenv
from llama_cloud import LlamaCloud
from llama_cloud.types.parsing_get_response import MarkdownPageMarkdownResultPage, MetadataPage
from loguru import logger

if TYPE_CHECKING:
    from llama_cloud.types import ParsingGetResponse

app = typer.Typer(add_completion=False)

TIER = "agentic"
VERSION = "latest"
RENDER_DPI = 300
JPEG_QUALITY = 92
CUSTOM_PROMPT = (
    "This image is a two-page book spread. Parse the LEFT page in full first, in reading "
    "order (top to bottom, respecting any multi-column layout within that page). Then parse "
    "the RIGHT page in full, in reading order. Insert a clear page break between the two "
    "pages and do not interleave content across the gutter."
)

load_dotenv(Path(__file__).parent.parent.parent / ".env.runtime")


def _render_pdf_to_jpegs(pdf_path: Path, out_dir: Path, dpi: int) -> list[Path]:
    """Render each PDF page to a JPEG file.

    Args:
        pdf_path: Path to the source PDF.
        out_dir: Directory to write rendered JPEGs into.
        dpi: Render resolution in dots per inch.

    Returns:
        Rendered JPEG paths, one per PDF page, in order.

    """
    scale = dpi / 72.0
    stem = pdf_path.stem
    rendered: list[Path] = []
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        total = len(pdf)
        for i in range(total):
            page = pdf[i]
            image = page.render(scale=scale).to_pil().convert("RGB")
            jpg_path = out_dir / f"{stem}_spread_{i + 1:03d}.jpg"
            image.save(jpg_path, format="JPEG", quality=JPEG_QUALITY)
            logger.info(f"  Rendered PDF page {i + 1}/{total} -> {jpg_path.name}")
            rendered.append(jpg_path)
    finally:
        pdf.close()
    return rendered


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
        stem: Source image filename stem (e.g. "mybook_spread_001").

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

    Only downloads images whose original filename is in ``referenced`` (i.e. actually
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
    """Annotate each item with ``book_side`` = "left"|"right" based on bbox center-x.

    Uses the parent page's ``page_width`` (in PDF points, as returned by LlamaParse) as
    the split midpoint, so bbox coordinates are compared in the same coordinate system.

    Args:
        items_data: Dumped items result (modified in place).

    """
    for page in items_data.get("pages", []):
        page_width = page.get("page_width")
        if page_width is None:
            continue
        mid = float(page_width) / 2
        for item in page.get("items", []):
            cx = _bbox_center_x(item.get("bbox") or item.get("bBox"))
            if cx is None:
                continue
            item["book_side"] = "left" if cx < mid else "right"


def parse_spread(
    client: LlamaCloud,
    image_path: Path,
    output_dir: Path,
    overwrite: bool,
) -> dict | None:
    """Parse a single spread image and write .md and .json output files.

    Args:
        client: Authenticated LlamaCloud client.
        image_path: Path to the rendered spread JPG.
        output_dir: Directory to write output files into.
        overwrite: If False, skip files whose outputs already exist.

    Returns:
        A dict of ``{page_number: printed_page_number}`` extracted from metadata, or
        ``None`` if the spread was skipped.

    """
    stem = image_path.stem
    md_path = output_dir / f"{stem}.md"
    json_path = output_dir / f"{stem}.json"

    if not overwrite and md_path.exists() and json_path.exists():
        logger.info(f"Skipping {image_path.name} (outputs already exist)")
        return None

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

    if result.markdown is not None:
        md_content = "\n\n".join(
            page.markdown
            for page in result.markdown.pages
            if isinstance(page, MarkdownPageMarkdownResultPage)
        )
    else:
        md_content = result.markdown_full or ""

    rename = _image_rename_map(result, stem)
    printed_page_numbers = _printed_page_numbers(result)

    items_data = result.items.model_dump() if result.items is not None else {}
    for page in items_data.get("pages", []):
        lp_page_num = page.get("page_number")
        if lp_page_num in printed_page_numbers:
            page["printed_page_number"] = printed_page_numbers[lp_page_num]

    _tag_book_side(items_data)

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

    return printed_page_numbers


def _write_manifest(
    pdf_path: Path,
    output_dir: Path,
    spread_images: list[Path],
    per_spread_printed: list[dict[int, str] | None],
) -> None:
    """Write a top-level manifest.json describing spreads in reading order.

    Logical book page numbers are NOT computed here; books typically have unnumbered
    covers and roman-numeral front matter that can't be derived arithmetically. Instead
    each entry records the spread position plus whatever printed page numbers LlamaParse
    detected on the spread, leaving logical labelling to ebook-assembly time.

    Args:
        pdf_path: Source PDF path (stem used for manifest filename).
        output_dir: Directory to write the manifest into.
        spread_images: Rendered spread JPG paths, in PDF page order.
        per_spread_printed: Printed-page-number dicts returned by ``parse_spread``
            (or ``None`` if that spread was skipped), aligned with ``spread_images``.

    """
    spreads: list[dict[str, Any]] = []
    for i, img_path in enumerate(spread_images):
        entry: dict[str, Any] = {
            "spread_num": i + 1,
            "image": img_path.name,
            "md": f"{img_path.stem}.md",
            "json": f"{img_path.stem}.json",
        }
        printed = per_spread_printed[i]
        if printed:
            entry["printed_page_numbers_detected"] = {str(k): v for k, v in printed.items()}
        spreads.append(entry)

    manifest = {
        "pdf": pdf_path.name,
        "num_spreads": len(spreads),
        "spreads": spreads,
    }
    manifest_path = output_dir / f"{pdf_path.stem}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Wrote manifest {manifest_path}")


@app.command()
def main(
    pdf_path: Path = typer.Argument(  # noqa: B008
        ..., help="PDF file where each page is a two-page book spread."
    ),
    output_dir: Path = typer.Option(  # noqa: B008
        None,
        "--output-dir",
        "-o",
        help="Directory to write output files (default: PDF's parent directory).",
    ),
    overwrite: bool = typer.Option(
        False,  # noqa: FBT003
        "--overwrite",
        help="Re-parse and overwrite existing output files.",
    ),
    rerender: bool = typer.Option(
        False,  # noqa: FBT003
        "--rerender",
        help="Re-render spread JPGs even if they already exist.",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="LLAMA_CLOUD_API_KEY",
        help="LlamaCloud API key (or set LLAMA_CLOUD_API_KEY env var).",
    ),
) -> None:
    """Parse PDF_PATH (two-page spreads) using LlamaParse and write per-spread outputs."""
    if not pdf_path.is_file():
        logger.error(f"Not a file: {pdf_path}")
        raise typer.Exit(1)

    resolved_output_dir = output_dir if output_dir is not None else pdf_path.parent
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    resolved_api_key = api_key or os.environ.get("LLAMA_PARSE_API_KEY")
    if not resolved_api_key:
        logger.error("No API key found. Set LLAMA_CLOUD_API_KEY or pass --api-key.")
        raise typer.Exit(1)

    stem = pdf_path.stem
    existing = sorted(resolved_output_dir.glob(f"{stem}_spread_*.jpg"))
    if existing and not rerender:
        logger.info(f"Using {len(existing)} existing spread JPG(s) in {resolved_output_dir}")
        spread_images = existing
    else:
        logger.info(f"Rendering {pdf_path.name} at {RENDER_DPI} DPI ...")
        spread_images = _render_pdf_to_jpegs(pdf_path, resolved_output_dir, RENDER_DPI)

    if not spread_images:
        logger.warning("No spread images to parse.")
        raise typer.Exit(0)

    client = LlamaCloud(api_key=resolved_api_key)

    errors: list[str] = []
    per_spread_printed: list[dict[int, str] | None] = []
    for image_path in spread_images:
        try:
            per_spread_printed.append(
                parse_spread(client, image_path, resolved_output_dir, overwrite)
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to parse {image_path.name}: {exc}")
            errors.append(image_path.name)
            per_spread_printed.append(None)

    _write_manifest(pdf_path, resolved_output_dir, spread_images, per_spread_printed)

    if errors:
        logger.warning(f"{len(errors)} file(s) failed: {', '.join(errors)}")
        raise typer.Exit(1)

    logger.info("Done.")


if __name__ == "__main__":
    app()

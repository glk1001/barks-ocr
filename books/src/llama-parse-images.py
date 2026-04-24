#!/usr/bin/env python3
"""Parse a directory of .jpg images with LlamaParse and save .md and .json output files."""

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
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
CUSTOM_PROMPT = (
    "This is a two-column document. Read columns left-to-right, top-to-bottom "
    "within each column. Preserve the reading order."
)

load_dotenv(Path(__file__).parent.parent / ".env.runtime")


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
        help="Directory to write output files (default: same as image_dir).",
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

    resolved_output_dir = output_dir if output_dir is not None else image_dir
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

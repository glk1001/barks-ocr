"""Finish a restyled panel the way it was being done by hand in GIMP.

Two steps, in GIMP's order:

1. Auto white balance (GIMP's Colors > Auto > White Balance): for each of red, green and
   blue, the darkest and lightest WHITE_BALANCE_CLIP of pixels are clipped and the rest is
   stretched to fill 0-255, which removes a colour cast and opens up a flat range.
2. Unsharp mask, with GIMP's default radius 3.0, amount 0.5 and threshold 0. This uses
   Pillow's unsharp mask, which works on the stored sRGB values; GIMP may sharpen in linear
   light, so the strength can differ slightly from GIMP's at the same settings.

A third helper, remove_frame(), cuts off a comic-panel frame the model sometimes draws (a
thin dark line just inside the image edge, often with a light margin outside it) that the
source panel does not have, and scales the rest back to the full size. Kontext drew one on
Mythtic Mystery 092-1's halftone twice, ignoring a prompt that asked for no border.

Run by hand, the finished copy is saved beside the original as ``<stem>-fin.png`` and an
existing one is never overwritten, so the original is kept:

    uv run --offline src/barks_ocr/nano/finishing.py IMAGE [IMAGE ...] [--frame-only]

A frame is removed first if there is one; --frame-only does only that. kontext_panels.py
instead calls remove_frame() on every output and finish() on the styles in its
FINISH_STYLES before saving, so only the finished image is written there.
"""

from pathlib import Path
from typing import Annotated

import numpy as np
import typer
from loguru import logger
from PIL import Image, ImageFilter

WHITE_BALANCE_CLIP = 0.0005  # 0.05% of pixels at each end of each channel, as GIMP does
UNSHARP_RADIUS = 3.0
UNSHARP_AMOUNT = 0.5
UNSHARP_THRESHOLD = 0
FINISHED_SUFFIX = "-fin"

FRAME_SEARCH_FRACTION = 0.06  # look for a frame line this far in from each edge
FRAME_MAX_LINE_FRACTION = 0.03  # a frame line is at most this thick
FRAME_DARK = 60  # a row or column at least this dark on average (0-255) is frame line
FRAME_CROP_PAD = 2  # also cut this many pixels inside the line, past its soft edge


def auto_white_balance(image: Image.Image, clip: float = WHITE_BALANCE_CLIP) -> Image.Image:
    """Stretch each colour channel to the full range, ignoring a sliver of outliers.

    Args:
        image: The image to balance. An alpha channel is kept unchanged.
        clip: The fraction of pixels clipped at each end of each channel.

    Returns:
        The balanced image, in the input's mode (RGB or RGBA).

    """
    alpha = image.getchannel("A") if image.mode == "RGBA" else None
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)

    balanced = np.empty_like(rgb)
    for channel in range(3):
        values = rgb[..., channel]
        low, high = np.quantile(values, [clip, 1.0 - clip])
        if high <= low:  # a flat channel has nothing to stretch
            balanced[..., channel] = values
        else:
            balanced[..., channel] = (values - low) * (255.0 / (high - low))

    result = Image.fromarray(np.clip(balanced, 0, 255).round().astype(np.uint8), mode="RGB")
    if alpha is not None:
        result.putalpha(alpha)
    return result


def unsharp_mask(image: Image.Image) -> Image.Image:
    """Sharpen an image with an unsharp mask at the UNSHARP_* settings.

    Args:
        image: The image to sharpen.

    Returns:
        The sharpened image.

    """
    return image.filter(
        ImageFilter.UnsharpMask(
            radius=UNSHARP_RADIUS,
            percent=round(UNSHARP_AMOUNT * 100),
            threshold=UNSHARP_THRESHOLD,
        )
    )


def finish(image: Image.Image) -> Image.Image:
    """Return an image white-balanced and then sharpened.

    Args:
        image: The image to finish.

    Returns:
        The finished image.

    """
    return unsharp_mask(auto_white_balance(image))


def _frame_line_end(lines: np.ndarray, max_line: int) -> int | None:
    """Return how far in from an edge a frame line ends, or None if there is no frame line.

    Args:
        lines: The mean brightness of each row (or column), from the edge inward.
        max_line: The thickest run of dark rows that still counts as a line.

    Returns:
        The index just inside the first dark run. None if there is no dark run, if it is too
        thick to be a line, or if it runs to the end of the search depth (a dark scene).

    """
    dark = lines < FRAME_DARK
    if not dark.any():
        return None
    start = int(np.argmax(dark))
    end = start
    while end < len(dark) and dark[end]:
        end += 1
    if end - start > max_line or end >= len(dark):
        return None
    return end


def find_frame(image: Image.Image) -> tuple[int, int, int, int] | None:
    """Find a frame drawn around the whole image.

    A frame needs a thin, dark, full-length line near all four edges; one dark edge (a black
    sky, a shadow) is not a frame.

    Args:
        image: The image to check.

    Returns:
        The (left, top, right, bottom) box just inside the frame, or None if there is none.

    """
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    height, width = gray.shape
    depth_y = max(1, round(height * FRAME_SEARCH_FRACTION))
    depth_x = max(1, round(width * FRAME_SEARCH_FRACTION))
    max_line = max(1, round(min(height, width) * FRAME_MAX_LINE_FRACTION))

    top = _frame_line_end(gray[:depth_y].mean(axis=1), max_line)
    bottom = _frame_line_end(gray[::-1][:depth_y].mean(axis=1), max_line)
    left = _frame_line_end(gray[:, :depth_x].mean(axis=0), max_line)
    right = _frame_line_end(gray[:, ::-1][:, :depth_x].mean(axis=0), max_line)
    if top is None or bottom is None or left is None or right is None:
        return None
    pad = FRAME_CROP_PAD
    return left + pad, top + pad, width - right - pad, height - bottom - pad


def remove_frame(image: Image.Image) -> Image.Image | None:
    """Cut off a frame drawn around the image and scale the rest back to the full size.

    Args:
        image: The image to check.

    Returns:
        The unframed image at the original size, or None if there was no frame.

    """
    box = find_frame(image)
    if box is None:
        return None
    return image.crop(box).resize(image.size, Image.Resampling.LANCZOS)


def get_finished_path(image_file: Path) -> Path:
    """Return where the finished copy of an image is saved.

    Args:
        image_file: The original image.

    Returns:
        ``<stem>-fin.png`` beside the original.

    """
    return image_file.with_name(f"{image_file.stem}{FINISHED_SUFFIX}.png")


def finish_image(image_file: Path, frame_only: bool = False) -> Path | None:
    """Remove any frame from an image, white-balance and sharpen it, and save it beside it.

    Args:
        image_file: The image to finish.
        frame_only: Only remove a frame; skip the white balance and sharpening.

    Returns:
        The finished file, or None if it already existed and was left alone.

    """
    dest = get_finished_path(image_file)
    if dest.exists():
        logger.warning(f'Not finishing "{image_file.name}": "{dest.name}" already exists.')
        return None

    with Image.open(image_file) as image:
        image.load()
        unframed = remove_frame(image)
        if unframed is not None:
            logger.info(f'Removed a frame from "{image_file.name}".')
        finished = unframed or image
        if not frame_only:
            finished = finish(finished)
    finished.save(dest)
    logger.info(f'Finished "{dest}".')
    return dest


def main(
    image_files: Annotated[list[Path], typer.Argument(help="The images to finish.")],
    frame_only: Annotated[
        bool, typer.Option(help="Only remove a frame; no white balance or sharpening.")
    ] = False,
) -> None:
    """Save a finished copy of each image as <stem>-fin.png."""
    for image_file in image_files:
        if image_file.stem.endswith(FINISHED_SUFFIX):
            logger.warning(f'Skipping "{image_file.name}": it is already a finished copy.')
            continue
        finish_image(image_file, frame_only)


if __name__ == "__main__":
    typer.run(main)

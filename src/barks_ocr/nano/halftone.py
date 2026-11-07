"""Turn a panel into a true printed halftone: CMY dot screens plus solid black line art.

Kontext only imitates halftone (flat colour with dots sprinkled over it). This builds the
colour from dots, the way a comic was printed: each colour is split into cyan, magenta and
yellow ink, each ink is screened into round dots on its own rotated grid (the classic 15, 75
and 0 degree screen angles, which give the rosette), and the dots are overprinted on white
paper. Dark pixels (the line art and solid blacks) stay solid black rather than screened, as
the black plate did. The work is done at SUPERSAMPLE times the size and scaled back down, so
the dot edges are smooth.

    uv run --offline src/barks_ocr/nano/halftone.py INPUT [OUTPUT] [--cell 6]

The input can be an original panel or a Kontext output. The default OUTPUT is INPUT with
``-dots`` added to its name; an existing output is never overwritten.
"""
# cspell:words Kontext halftoned interp mgrid SUPERSAMPLE

from pathlib import Path
from typing import Annotated

import numpy as np
import typer
from loguru import logger
from PIL import Image

SUPERSAMPLE = 3
DEFAULT_CELL = 6.0  # dot spacing in output pixels
SCREEN_ANGLES = (15.0, 75.0, 0.0)  # cyan, magenta, yellow
BLACK_LUMINANCE = 0.22  # darker than this prints as solid black
_CALIBRATION_STEPS = 1025


def _spot(u: np.ndarray, v: np.ndarray, cell: float) -> np.ndarray:
    """Return the dot-shape function: 1 at a dot centre, -1 midway between dots."""
    return (np.cos(2 * np.pi * u / cell) + np.cos(2 * np.pi * v / cell)) / 2


def _coverage_to_threshold(coverage: np.ndarray) -> np.ndarray:
    """Map ink coverage (0-1) to the spot threshold that inks exactly that fraction of a cell.

    The spot function's area above a threshold is not linear in the threshold, so it is
    measured once over one cell and inverted, so that a 30% tint inks 30% of the paper.
    """
    grid = np.linspace(0.0, 1.0, 256, endpoint=False, dtype=np.float32)
    u, v = np.meshgrid(grid, grid)
    spot_values = np.sort(_spot(u, v, 1.0).ravel())
    thresholds = np.linspace(-1.0, 1.0, _CALIBRATION_STEPS, dtype=np.float32)
    area = 1.0 - np.searchsorted(spot_values, thresholds, side="right") / spot_values.size
    # area falls as the threshold rises; np.interp needs increasing x.
    return np.asarray(np.interp(coverage, area[::-1], thresholds[::-1]), dtype=np.float32)


def screen(coverage: np.ndarray, cell: float, angle_degrees: float) -> np.ndarray:
    """Screen one ink's coverage into round dots on a rotated grid.

    Args:
        coverage: Ink coverage per pixel, 0 (none) to 1 (solid), shape (height, width).
        cell: The dot spacing in pixels.
        angle_degrees: The screen angle.

    Returns:
        A boolean array, True where this ink prints.

    """
    height, width = coverage.shape
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    angle = np.deg2rad(angle_degrees)
    u = x * np.cos(angle) + y * np.sin(angle)
    v = -x * np.sin(angle) + y * np.cos(angle)
    return _spot(u, v, cell) > _coverage_to_threshold(coverage)


def halftone(image: Image.Image, cell: float = DEFAULT_CELL) -> Image.Image:
    """Return a CMY halftone of an image, with dark pixels kept solid black.

    Args:
        image: The panel to screen.
        cell: The dot spacing in output pixels.

    Returns:
        The halftoned RGB image, the same size as the input.

    """
    rgb_image = image.convert("RGB")
    big_size = (rgb_image.width * SUPERSAMPLE, rgb_image.height * SUPERSAMPLE)
    big = rgb_image.resize(big_size, Image.Resampling.BILINEAR)
    rgb = np.asarray(big, dtype=np.float32) / 255.0

    luminance = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    solid_black = luminance < BLACK_LUMINANCE

    paper = np.ones_like(rgb)
    for channel, angle in enumerate(SCREEN_ANGLES):
        # Cyan ink absorbs red, magenta green, yellow blue.
        ink = screen(1.0 - rgb[..., channel], cell * SUPERSAMPLE, angle)
        paper[..., channel][ink] = 0.0
    paper[solid_black] = 0.0

    out = Image.fromarray((paper * 255).round().astype(np.uint8), mode="RGB")
    return out.resize(rgb_image.size, Image.Resampling.LANCZOS)


def main(
    input_file: Annotated[Path, typer.Argument(help="The panel image to halftone.")],
    output_file: Annotated[
        Path | None, typer.Argument(help="Where to save it; default INPUT-dots.png.")
    ] = None,
    cell: Annotated[float, typer.Option(help="Dot spacing in output pixels.")] = DEFAULT_CELL,
) -> None:
    """Save a printed-style CMY halftone of a panel image."""
    if output_file is None:
        output_file = input_file.with_name(f"{input_file.stem}-dots.png")
    if output_file.exists():
        msg = f"Output already exists: {output_file}"
        raise FileExistsError(msg)

    with Image.open(input_file) as image:
        result = halftone(image, cell)
    result.save(output_file)
    logger.info(f'Saved "{output_file}" ({result.width}x{result.height}, cell {cell}px).')


if __name__ == "__main__":
    typer.run(main)

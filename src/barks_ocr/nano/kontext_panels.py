"""Restyle a Barks panel with FLUX.1 Kontext [dev] through Hugging Face Inference Providers.

Gemini and OpenAI refuse Disney characters; the open-weights Kontext model does not. Set the
panel and the styles in the constants below, then run:

    uv run --offline src/barks_ocr/nano/kontext_panels.py

Needs ``HF_TOKEN`` (a fine-grained token with "Make calls to Inference Providers") in
``.env.runtime`` at the repo root; calls are billed to that Hugging Face account. Outputs go
beside the Gemini ones as ``<panels>/AI/<title>/<edited>/<stem>-<style>-kontext.png``. An
output that already exists is skipped, never overwritten, so a re-run only fills the gaps.

Kontext follows one plain instruction far better than a list of prohibitions, so each prompt
is a single sentence that names what to keep.

Kontext returns an image the size of the one it is sent (each side rounded down to a multiple
of 16) and ignores a requested output size. So the panel is resized locally to about
TARGET_MEGAPIXELS before sending: scaling by area rather than by a long side gives wide and
tall panels the same detail as a standard one, and ~1 megapixel is the size Kontext is built
for. A standard 806x616 panel goes out at 1168x896.
"""
# cspell:words Kontext impres Ansel huggingface

import math
import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from loguru import logger
from PIL import Image

MODEL = "black-forest-labs/FLUX.1-Kontext-dev"
PROVIDER = "fal-ai"

# Resize each panel to about this many megapixels before sending; None sends it as it is.
TARGET_MEGAPIXELS: float | None = 1.05
_SIZE_MULTIPLE = 16

BARKS_PANELS_PNG = Path("/home/greg/Books/Carl Barks/Barks Panels Pngs")

PANEL_TYPE = "Favourites"  # or "Censorship", "Closeups", "Insets", "Splash", "Silhouettes"
TITLE = "Luck of the North"
EDITED = ""  # or "edited"
IMAGE_FILENAME = "116-6.png"

_KEEP = (
    ", while keeping the exact same composition, framing, characters, poses, clothing,"
    " facial expressions and eyes."
)
_KEEP_INK = (
    ", while keeping the exact same black ink lines, composition, framing, characters, poses,"
    " clothing, facial expressions and eyes."
)

# The keys are the output-name styles; most match the Gemini script's suffixes.
STYLE_PROMPTS: dict[str, str] = {
    "photo": "Transform this comic book panel into a super-realistic 3D photograph" + _KEEP,
    "render3d": (
        "Transform this comic book panel into a highly detailed, realistic 3D render with"
        " lifelike textures, materials and cinematic lighting" + _KEEP
    ),
    "oil": (
        "Transform this comic book panel into a very realistic and beautiful oil painting"
        " with visible brushstrokes" + _KEEP
    ),
    "impres": (
        "Transform this comic book panel into a very beautiful impressionist painting with"
        " loose, visible brushstrokes and soft natural light" + _KEEP
    ),
    "impres-color": (
        "Transform this comic book panel into a very beautiful impressionist painting with"
        " vibrant, luminous colors, loose visible brushstrokes and dappled natural light" + _KEEP
    ),
    "water": (
        "Transform this comic book panel into a very beautiful watercolor painting with soft"
        " washes, gentle color bleeds and visible paper texture" + _KEEP
    ),
    "pastel": (
        "Transform this comic book panel into a very beautiful pastel painting with soft chalky"
        " strokes, blended colors and visible paper texture" + _KEEP
    ),
    "ansel": (
        "Transform this comic book panel into a very detailed black and white Ansel Adams"
        " photograph with deep blacks, bright highlights and a full range of gray tones" + _KEEP
    ),
    "ansel-color": (
        "Transform this comic book panel into a very detailed color landscape photograph in the"
        " style of Ansel Adams, with dramatic natural light, deep shadows and crisp detail" + _KEEP
    ),
    "recolor": (
        "Recolor this comic book panel using smooth color gradients and soft shading in place"
        " of the flat colors" + _KEEP_INK
    ),
    "halftone": (
        "Recolor this comic book panel using classic printed half-tone dot shading in place of"
        " the flat colors" + _KEEP_INK
    ),
    "clean": (
        "Clean up this comic book panel by sharpening and smoothing the black ink lines and"
        " removing specks and printing noise" + _KEEP
    ),
}

STYLES = ["photo", "oil", "impres", "water", "pastel", "ansel", "recolor", "halftone", "clean"]


def get_source_image() -> Path:
    """Return the panel image named by the PANEL_TYPE/TITLE/EDITED/IMAGE_FILENAME constants.

    Returns:
        The path of the source panel PNG.

    """
    if PANEL_TYPE == "Insets":
        return BARKS_PANELS_PNG / PANEL_TYPE / EDITED / IMAGE_FILENAME
    return BARKS_PANELS_PNG / PANEL_TYPE / TITLE / EDITED / IMAGE_FILENAME


def get_dest_image(srce_image: Path, style: str) -> Path:
    """Return where the Kontext output for one style of a panel is saved.

    Args:
        srce_image: The source panel image.
        style: A key of STYLE_PROMPTS.

    Returns:
        The output path, beside the Gemini outputs for the same title.

    """
    return BARKS_PANELS_PNG / "AI" / TITLE / EDITED / f"{srce_image.stem}-{style}-kontext.png"


def get_client() -> InferenceClient:
    """Create an Inference Providers client from HF_TOKEN in the repo's .env.runtime.

    Returns:
        A client that routes requests to PROVIDER.

    Raises:
        RuntimeError: If HF_TOKEN is not set.

    """
    load_dotenv(Path(__file__).parents[3] / ".env.runtime")
    token = os.environ.get("HF_TOKEN")
    if not token:
        msg = "HF_TOKEN is not set: add it to .env.runtime at the repo root."
        raise RuntimeError(msg)
    return InferenceClient(provider=PROVIDER, api_key=token)


def get_scaled_size(width: int, height: int, megapixels: float) -> tuple[int, int]:
    """Return a size of about ``megapixels`` with the same aspect ratio, in multiples of 16.

    Args:
        width: The panel width in pixels.
        height: The panel height in pixels.
        megapixels: The target area, in millions of pixels.

    Returns:
        The scaled (width, height), each side rounded to the nearest multiple of 16.

    """
    scale = math.sqrt(megapixels * 1_000_000 / (width * height))

    def _round(side: int) -> int:
        return max(_SIZE_MULTIPLE, round(side * scale / _SIZE_MULTIPLE) * _SIZE_MULTIPLE)

    return _round(width), _round(height)


def load_panel_to_send(srce_image: Path) -> Image.Image:
    """Load a panel and resize it to TARGET_MEGAPIXELS, ready to send to Kontext.

    Args:
        srce_image: The source panel image.

    Returns:
        The RGB panel, resized unless TARGET_MEGAPIXELS is None.

    """
    image = Image.open(srce_image).convert("RGB")
    if TARGET_MEGAPIXELS is None:
        return image
    size = get_scaled_size(image.width, image.height, TARGET_MEGAPIXELS)
    return image.resize(size, Image.Resampling.LANCZOS)


def restyle_panel(
    client: InferenceClient, panel: Image.Image, style: str, dest_image: Path
) -> bool:
    """Restyle one panel in one style and save it, unless the output already exists.

    A request the provider rejects (a refusal, a bad token, no credit) is logged and skipped,
    so one failure does not stop the remaining styles.

    Args:
        client: The Inference Providers client.
        panel: The panel image to send, already at the size wanted back.
        style: A key of STYLE_PROMPTS.
        dest_image: Where to save the output.

    Returns:
        True if an image was saved.

    """
    if dest_image.is_file():
        logger.warning(f'Skipping "{style}": "{dest_image}" already exists.')
        return False

    prompt = STYLE_PROMPTS[style]
    logger.info(f'"{style}": {prompt}')
    try:
        output = client.image_to_image(panel, prompt=prompt, model=MODEL)
    except HfHubHTTPError as e:
        logger.error(f'"{style}" failed, nothing saved: {e}')
        return False

    dest_image.parent.mkdir(parents=True, exist_ok=True)
    output.save(dest_image)
    logger.info(f'Saved "{dest_image}" ({output.width}x{output.height}).')
    return True


def main() -> None:
    """Restyle the configured panel in every style listed in STYLES."""
    srce_image = get_source_image()
    if not srce_image.is_file():
        msg = f"Source panel not found: {srce_image}"
        raise FileNotFoundError(msg)
    unknown = [style for style in STYLES if style not in STYLE_PROMPTS]
    if unknown:
        msg = f"Unknown styles {unknown}; choose from {list(STYLE_PROMPTS)}."
        raise ValueError(msg)

    panel = load_panel_to_send(srce_image)
    with Image.open(srce_image) as original:
        logger.info(
            f"Sending {original.width}x{original.height} panel at {panel.width}x{panel.height}."
        )

    client = get_client()
    saved = sum(
        restyle_panel(client, panel, style, get_dest_image(srce_image, style)) for style in STYLES
    )
    logger.info(f"Saved {saved} of {len(STYLES)} styles for {srce_image}.")


if __name__ == "__main__":
    main()

"""Restyle a Barks panel with open-weights FLUX models through Hugging Face Inference Providers.

Gemini and OpenAI refuse Disney characters; the open-weights models do not. Most styles use
FLUX.1 Kontext [dev]; STYLE_MODELS sends a style to FLUX.2 [dev] instead, which paints a real
impressionist picture where Kontext keeps the ink outlines under one swirly oil texture. Set
the panel and the styles in the constants below, then run:

    uv run --offline src/barks_ocr/nano/kontext_panels.py

Needs ``HF_TOKEN`` (a fine-grained token with "Make calls to Inference Providers") in
``.env.runtime`` at the repo root; calls are billed to that Hugging Face account. Outputs go
beside the Gemini ones as ``<panels>/AI/<title>/<edited>/<stem>-<style>-<model tag>.png``
(tag ``kontext`` or ``flux2``), so two models' versions of a style sit side by side. An
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

import base64
import io
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from loguru import logger
from PIL import Image

KONTEXT_MODEL = "black-forest-labs/FLUX.1-Kontext-dev"
FLUX2_MODEL = "black-forest-labs/FLUX.2-dev"
DEFAULT_MODEL = KONTEXT_MODEL
PROVIDER = "fal-ai"

# The output-name tag for each model.
MODEL_TAGS: dict[str, str] = {KONTEXT_MODEL: "kontext", FLUX2_MODEL: "flux2"}
# fal's FLUX.2 edit endpoint reads a list of images (image_urls) and returns no image when sent
# only the single image_url the Hugging Face client fills in, so these models get the list.
_MODELS_TAKING_IMAGE_LIST = {FLUX2_MODEL}

# Resize each panel to about this many megapixels before sending; None sends it as it is.
TARGET_MEGAPIXELS: float | None = 1.05
_SIZE_MULTIPLE = 16

BARKS_PANELS_PNG = Path("/home/greg/Books/Carl Barks/Barks Panels Pngs")

PANEL_TYPE = "Favourites"  # or "Censorship", "Closeups", "Insets", "Splash", "Silhouettes"
TITLE = "Crown of the Mayas"
EDITED = ""  # or "edited"
IMAGE_FILENAME = "109-1.png"

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
        "Repaint this comic book panel as an unsigned impressionist oil painting made of short,"
        " separate dabs of pure color, with soft painted edges in place of the black ink"
        " outlines and colored shadows, while keeping the exact same"
        " composition, framing, characters, poses, clothing, colors, facial expressions and eyes."
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
        "Recolor this comic book panel using Ben-Day dots like a 1950s printed comic, where every"
        " colored area is made of evenly spaced round dots of printing ink on white paper in a"
        " regular grid" + _KEEP_INK
    ),
    "clean": (
        "Clean up this comic book panel by sharpening and smoothing the black ink lines and"
        " removing specks and printing noise" + _KEEP
    ),
}

STYLES = [
    "photo",
    "oil",
    "impres",
    "water",
    "pastel",
    "ansel",
    "recolor",
    "halftone",
    #    "clean",
]

# Extra instructions for one panel, keyed by (TITLE, IMAGE_FILENAME) and appended to every
# style's prompt whenever that panel is run.
EXTRA_PROMPTS: dict[tuple[str, str], str] = {
    ("A Spicy Tale", "080-8.png"): "The panther must be colored black.",
}

# The models each style is run on, one output per model; a style not listed here runs on
# DEFAULT_MODEL alone.
STYLE_MODELS: dict[str, list[str]] = {
    "impres": [FLUX2_MODEL],
    "water": [KONTEXT_MODEL, FLUX2_MODEL],
    "pastel": [KONTEXT_MODEL, FLUX2_MODEL],
}


def get_source_image() -> Path:
    """Return the panel image named by the PANEL_TYPE/TITLE/EDITED/IMAGE_FILENAME constants.

    Returns:
        The path of the source panel PNG.

    """
    if PANEL_TYPE == "Insets":
        return BARKS_PANELS_PNG / PANEL_TYPE / EDITED / IMAGE_FILENAME
    return BARKS_PANELS_PNG / PANEL_TYPE / TITLE / EDITED / IMAGE_FILENAME


def get_style_models(style: str) -> list[str]:
    """Return the models a style is run on.

    Args:
        style: A key of STYLE_PROMPTS.

    Returns:
        The style's models from STYLE_MODELS, or just DEFAULT_MODEL.

    """
    return STYLE_MODELS.get(style, [DEFAULT_MODEL])


def get_dest_image(srce_image: Path, style: str, model: str) -> Path:
    """Return where one model's output for one style of a panel is saved.

    Args:
        srce_image: The source panel image.
        style: A key of STYLE_PROMPTS.
        model: The model the style is run on.

    Returns:
        The output path, beside the Gemini outputs for the same title, tagged with the
        model.

    """
    tag = MODEL_TAGS[model]
    return BARKS_PANELS_PNG / "AI" / TITLE / EDITED / f"{srce_image.stem}-{style}-{tag}.png"


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


def _as_data_url(image: Image.Image) -> str:
    """Return an image as a base64 PNG data URL."""
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def restyle_panel(
    client: InferenceClient,
    panel: Image.Image,
    style: str,
    model: str,
    extra_prompt: str = "",
) -> bool:
    """Restyle the configured panel in one style on one model, unless that output exists.

    A request the provider rejects (a refusal, a bad token, no credit) is logged and skipped,
    so one failure does not stop the remaining styles.

    Args:
        client: The Inference Providers client.
        panel: The panel image to send, already at the size wanted back.
        style: A key of STYLE_PROMPTS.
        model: The model to run the style on; a key of MODEL_TAGS.
        extra_prompt: Instructions for this panel, appended to the style's prompt.

    Returns:
        True if an image was saved.

    """
    tag = MODEL_TAGS[model]
    dest_image = get_dest_image(get_source_image(), style, model)
    if dest_image.is_file():
        logger.warning(f'Skipping "{style}" ({tag}): "{dest_image}" already exists.')
        return False

    # None is dropped from the provider payload, so other models get no image_urls key.
    image_urls = [_as_data_url(panel)] if model in _MODELS_TAKING_IMAGE_LIST else None

    prompt = f"{STYLE_PROMPTS[style]} {extra_prompt}".strip()
    logger.info(f'"{style}" ({tag}): {prompt}')
    try:
        output = client.image_to_image(panel, prompt=prompt, model=model, image_urls=image_urls)
    except HfHubHTTPError as e:
        logger.error(f'"{style}" ({tag}) failed, nothing saved: {e}')
        return False
    except KeyError:
        # The client raises this when the provider's reply holds no image.
        logger.error(f'"{style}" ({tag}): the model returned no image, nothing saved.')
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
    jobs = [(style, model) for style in STYLES for model in get_style_models(style)]
    untagged = {model for _, model in jobs} - MODEL_TAGS.keys()
    if untagged:
        msg = f"Models {sorted(untagged)} have no entry in MODEL_TAGS."
        raise ValueError(msg)

    panel = load_panel_to_send(srce_image)
    with Image.open(srce_image) as original:
        logger.info(
            f"Sending {original.width}x{original.height} panel at {panel.width}x{panel.height}."
        )

    extra_prompt = EXTRA_PROMPTS.get((TITLE, IMAGE_FILENAME), "")
    if extra_prompt:
        logger.info(f"Extra prompt for this panel: {extra_prompt}")

    client = get_client()
    saved = sum(restyle_panel(client, panel, style, model, extra_prompt) for style, model in jobs)
    logger.info(f"Saved {saved} of {len(jobs)} outputs for {srce_image}.")


if __name__ == "__main__":
    main()

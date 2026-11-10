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
import functools
import io
import json
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from huggingface_hub.inference._common import RequestParameters
from huggingface_hub.inference._providers import fal_ai
from loguru import logger
from PIL import Image

from barks_ocr.nano.finishing import find_frame, finish, remove_frame

KONTEXT_MODEL = "black-forest-labs/FLUX.1-Kontext-dev"
FLUX2_MODEL = "black-forest-labs/FLUX.2-dev"
DEFAULT_MODEL = KONTEXT_MODEL
PROVIDER = "fal-ai"

# The output-name tag for each model.
MODEL_TAGS: dict[str, str] = {KONTEXT_MODEL: "kontext", FLUX2_MODEL: "flux2"}
# fal's FLUX.2 edit endpoint reads a list of images (image_urls) and returns no image when sent
# only the single image_url the Hugging Face client fills in, so these models get the list.
_MODELS_TAKING_IMAGE_LIST = {FLUX2_MODEL}

# fal's content checker on FLUX.2 flags some ordinary panels (Farragut the Falcon 159-4) as
# content_policy_violation, where Kontext takes them. False turns it off for FLUX.2 requests;
# True restores fal's default.
FLUX2_SAFETY_CHECKER = False

# Resize each panel to about this many megapixels before sending; None sends it as it is.
TARGET_MEGAPIXELS: float | None = 1.05
_SIZE_MULTIPLE = 16

BARKS_PANELS_PNG = Path("/home/greg/Books/Carl Barks/Barks Panels Pngs")

PANEL_TYPE = "Favourites"  # or "Censorship", "Closeups", "Insets", "Splash", "Silhouettes"
TITLE = "The Beachcombers' Picnic"
EDITED = ""  # or "edited"
IMAGE_FILENAME = "073-2.png"

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
    "photo": (
        "Transform this comic book panel into a super-realistic photograph taken on location"
        " with a camera, with real-world materials and textures such as moving water, foam and"
        " spray, weathered wood, rough stone, feathers and woven fabric, and natural light, so"
        " that nothing looks like clay, plastic or a miniature model" + _KEEP
    ),
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

# Extra instructions for one panel, appended to the style's prompt when that panel is run. A
# (TITLE, IMAGE_FILENAME) key applies to every style; a (TITLE, IMAGE_FILENAME, style) key to
# that style alone. When both match, the panel-wide one comes first.
EXTRA_PROMPTS: dict[tuple[str, str] | tuple[str, str, str], str] = {
    ("A Spicy Tale", "080-8.png"): "The panther must be colored black.",
    ("Missile Fizzle", "093-7.png"): (
        "The ducks are locked inside the two wooden crates, and each crate's front is a wire"
        " mesh that sits in front of the ducks, so the ducks are seen through the wire."
    ),
    ("Pipeline to Danger", "079-6.png"): (
        "The scene is in a dry desert far from any sea: the pale blue behind the characters is"
        " a clear desert sky, the ground is dry desert sand, and there is no ocean, water or"
        " waves anywhere. The duck riding the camel is seen in exact side profile facing left,"
        " so only one eye shows: a single narrowed, angry eye just under the brim of his white"
        " turban. His short beak points down and to the left, closed in a grim scowl, and he is"
        " not smiling."
    ),
    ("Silent Night", "253-2.png"): (
        "It is a cold winter night: the flat blue-violet background is the dark night sky, and"
        " there is no sea, water, waves, beach or sand anywhere. Fresh snow lies on top of the"
        " brown post and the pink globe at the left."
    ),
    ("The Beachcombers' Picnic", "073-2.png", "halftone"): (
        "The panel has no lettering at all: add no text, signature, initials or date anywhere,"
        " and keep the sky in the corners plain dots."
    ),
    ("Northeaster on Cape Quack", "014-6.png", "photo"): (
        "This is a real photograph of a storm at sea at night: the sky is black, and the"
        " crashing waves, spray and rocks are lit by the lighthouse lamp."
    ),
}

# The models each style is run on, one output per model; a style not listed here runs on
# DEFAULT_MODEL alone.
STYLE_MODELS: dict[str, list[str]] = {
    "impres": [FLUX2_MODEL],
    "water": [KONTEXT_MODEL, FLUX2_MODEL],
    "pastel": [KONTEXT_MODEL, FLUX2_MODEL],
}

# Styles whose outputs are finished (auto white balance + unsharp mask, see finishing.py)
# before they are saved, so the saved output is the finished image. Outputs saved before a
# style was added here are left as they are; finishing.py can do them by hand.
FINISH_STYLES: set[str] = {"photo", "oil", "impres", "water", "pastel", "ansel", "recolor"}


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


def get_extra_prompt(style: str) -> str:
    """Return the EXTRA_PROMPTS text for the configured panel in one style.

    Args:
        style: The style being run.

    Returns:
        The panel-wide extra prompt and the one for this style, joined by a space; empty if
        there is neither.

    """
    keys = ((TITLE, IMAGE_FILENAME), (TITLE, IMAGE_FILENAME, style))
    return " ".join(EXTRA_PROMPTS[key] for key in keys if key in EXTRA_PROMPTS)


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


class NoImageReplyError(RuntimeError):
    """The provider answered, but its reply held no image; the message is the reply."""


_MAX_REPLY_CHARS = 1000
_fal_get_response = fal_ai.FalAIImageToImageTask.get_response


def _drop_echoed_input(reply: object) -> object:
    """Return a fal reply without the ``input`` it echoes back, which holds the whole image.

    A rejection repeats the full request, base64 panel and all, inside each ``detail`` entry;
    the reason (``msg``, ``type``) is what is worth logging.
    """
    if isinstance(reply, dict):
        return {key: _drop_echoed_input(value) for key, value in reply.items() if key != "input"}
    if isinstance(reply, list):
        return [_drop_echoed_input(item) for item in reply]
    return reply


def _get_response_or_explain(
    self: fal_ai.FalAIImageToImageTask,
    response: bytes | dict,
    request_params: RequestParameters | None = None,
) -> bytes:
    """Wrap fal's image-to-image reply parsing so a reply with no image says what it held.

    The Hugging Face client reads ``reply["images"][0]["url"]`` and lets a bare
    ``KeyError: 'images'`` escape when fal answers without one (a low balance, a moderation
    block or a rejected input), hiding the reason. This re-reads the finished reply and puts
    its text in the error instead.
    """
    try:
        return _fal_get_response(self, response, request_params)
    except KeyError as e:
        reply = fal_ai.FalAIQueueTask.get_response(self, response, request_params)
        reply_dict = fal_ai._as_dict(reply)  # noqa: SLF001
        text = json.dumps(_drop_echoed_input(reply_dict))[:_MAX_REPLY_CHARS]
        raise NoImageReplyError(text) from e


# huggingface_hub has no hook for this, so its private fal provider class is patched; pinned
# by uv.lock, and only image-to-image replies are affected.
fal_ai.FalAIImageToImageTask.get_response = _get_response_or_explain


@functools.cache
def _has_frame(image_file: Path) -> bool:
    """Return whether an image has a frame drawn round it, so a model's copy of it is kept."""
    with Image.open(image_file) as image:
        return find_frame(image) is not None


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

    # None is dropped from the provider payload, so other models get neither key.
    image_urls = [_as_data_url(panel)] if model in _MODELS_TAKING_IMAGE_LIST else None
    safety_checker = FLUX2_SAFETY_CHECKER if model == FLUX2_MODEL else None

    prompt = f"{STYLE_PROMPTS[style]} {extra_prompt}".strip()
    logger.info(f'"{style}" ({tag}): {prompt}')
    try:
        output = client.image_to_image(
            panel,
            prompt=prompt,
            model=model,
            image_urls=image_urls,
            enable_safety_checker=safety_checker,
        )
    except HfHubHTTPError as e:
        logger.error(f'"{style}" ({tag}) failed, nothing saved: {e}')
        return False
    except NoImageReplyError as e:
        logger.error(f'"{style}" ({tag}): the model returned no image, nothing saved. Reply: {e}')
        return False

    unframed = None if _has_frame(get_source_image()) else remove_frame(output)
    if unframed is not None:
        logger.info(f'"{style}" ({tag}): removed a frame the model drew around the panel.')
        output = unframed

    finished = style in FINISH_STYLES
    if finished:
        output = finish(output)

    dest_image.parent.mkdir(parents=True, exist_ok=True)
    output.save(dest_image)
    note = ", finished" if finished else ""
    logger.info(f'Saved "{dest_image}" ({output.width}x{output.height}{note}).')
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
    bad_keys = [key for key in EXTRA_PROMPTS if not set(key[2:]) <= STYLE_PROMPTS.keys()]
    if bad_keys:
        msg = f"EXTRA_PROMPTS keys {bad_keys} name unknown styles."
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

    client = get_client()
    saved = sum(
        restyle_panel(client, panel, style, model, get_extra_prompt(style)) for style, model in jobs
    )
    logger.info(f"Saved {saved} of {len(jobs)} outputs for {srce_image}.")


if __name__ == "__main__":
    main()

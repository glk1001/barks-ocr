import os
from enum import Enum, auto
from pathlib import Path

from PIL import Image
from io import BytesIO

from google import genai
from google.genai.types import GenerateContentConfig


class Prompts(Enum):
    REMOVE_SPEECH_BUBBLES = auto()
    REMOVE_NARRATION_AND_SPEECH_BUBBLES = auto()
    COLORIZE_WITH_GRADIENTS = auto()
    MAKE_PHOTO_REALISTIC = auto()
    MAKE_OIL_PAINTING = auto()
    MAKE_IMPRESSIONIST_PAINTING = auto()
    MAKE_ANSEL_ADAMS = auto()
    EXTRACT_TEXT = auto()


REMOVE_BUBBLE_DEST_SUFFIX = "-no-bubbles.png"
RECOLOR_DEST_SUFFIX = "-recolor.png"
PHOTO_DEST_SUFFIX = "-photo.png"
OIL_DEST_SUFFIX = "-oil.png"
IMPRES_DEST_SUFFIX = "-impres.png"
ANSEL_DEST_SUFFIX = "-ansel.png"
EXTRACT_TEXT_DEST_SUFFIX = "-just-text.txt"

PROMPT_TEXT = {
    Prompts.REMOVE_SPEECH_BUBBLES: (
        "Remove all speech bubbles.",
        REMOVE_BUBBLE_DEST_SUFFIX,
    ),
    Prompts.REMOVE_NARRATION_AND_SPEECH_BUBBLES: (
        "Remove all speech bubbles and narrator box.",
        REMOVE_BUBBLE_DEST_SUFFIX,
    ),
    Prompts.COLORIZE_WITH_GRADIENTS: (
        "Colorize this using color gradients.",
        RECOLOR_DEST_SUFFIX,
    ),
    Prompts.MAKE_PHOTO_REALISTIC: (
        "Make this look like a super-realistic 3D photograph.",
        PHOTO_DEST_SUFFIX,
    ),
    Prompts.MAKE_OIL_PAINTING: (
        "Make this look like a very realistic and beautiful oil painting.",
        OIL_DEST_SUFFIX,
    ),
    Prompts.MAKE_IMPRESSIONIST_PAINTING: (
        "Make this look like a very beautiful impressionist painting.",
        IMPRES_DEST_SUFFIX,
    ),
    Prompts.MAKE_ANSEL_ADAMS: (
        "Make this like a very detailed black and white Ansel Adams photograph.",
        ANSEL_DEST_SUFFIX,
    ),
    Prompts.EXTRACT_TEXT: (
        "Extract the text from this image.",
        EXTRACT_TEXT_DEST_SUFFIX,
    ),
}
# PROMPT = "Remove the smaller inner panel."
# PROMPT = "Improve this comic book cover."  # bit of a dud

SYSTEM_INSTRUCTION = (
    "Do not remove any part of characters."
    " Do not change character's expressions."
    " Do not change character's eyes."
    " Do not add any characters."
    " Do not vignette."
    " Do not crop image."
    " Do not add a signature."
    " Do not change any objects."
    " Do not change any clothing."
    " Do not add a border."
)
CANDIDATE_COUNT = 1
AI_TOP_P = None
AI_TOP_K = None
SEED = 5

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
BARKS_PANELS_PNG = ROOT_DIR / "Barks Panels Pngs"
FANTA_RESTORED_DIR = ROOT_DIR / "Fantagraphics-restored"

# PANEL_TYPE = "Censorship"
# PANEL_TYPE = "Closeups"
PANEL_TYPE = "Favourites"
# PANEL_TYPE = "Insets"
# PANEL_TYPE = "Splash"
# PANEL_TYPE = "Silhouettes"
DEST_SUFFIX_PRE = ""
# DEST_SUFFIX_PRE = "-cl"

TITLE = "Serum to Codfish Cove"
EDITED = ""
# EDITED = "edited"
IMAGE_FILENAME = "190-4.png"
EXTRA_PROMPT = " Do not change character's eyes. Do not change position of eye pupils."
AI_TEMPERATURE = 0.0

PROMPTS_TO_USE = [
    # Prompts.COLORIZE_WITH_GRADIENTS,
    # Prompts.MAKE_PHOTO_REALISTIC,
    # Prompts.MAKE_OIL_PAINTING,
    Prompts.MAKE_IMPRESSIONIST_PAINTING,
    # Prompts.MAKE_ANSEL_ADAMS,
]

if PANEL_TYPE == "Insets":
    SRCE_IMAGE1 = ROOT_DIR / BARKS_PANELS_PNG / PANEL_TYPE / EDITED / IMAGE_FILENAME
else:
    SRCE_IMAGE1 = (
        ROOT_DIR / BARKS_PANELS_PNG / PANEL_TYPE / TITLE / EDITED / IMAGE_FILENAME
    )

AI_MODEL = "gemini-2.5-flash-image-preview"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

srce_image1 = Image.open(SRCE_IMAGE1, mode="r")

dest_files = []
for prompt_to_use in PROMPTS_TO_USE:
    dest_suffix_part = PROMPT_TEXT[prompt_to_use][1]
    dest_suffix = DEST_SUFFIX_PRE + dest_suffix_part

    dest_image = (
        ROOT_DIR
        / BARKS_PANELS_PNG
        / "AI"
        / TITLE
        / EDITED
        / (SRCE_IMAGE1.stem + dest_suffix)
    )

    dest_image.parent.mkdir(parents=True, exist_ok=True)
    if not dest_image.parent.is_dir():
        raise FileNotFoundError(
            f"ERROR: Parent directory does not exist and could not be created: {dest_image.parent}"
        )
    if dest_image.is_file():
        raise FileExistsError(f"Dest file exists: {dest_image}")

    dest_files.append(dest_image)

for prompt_to_use, dest_image in zip(PROMPTS_TO_USE, dest_files, strict=True):
    prompt_str, dest_suffix_part = PROMPT_TEXT[prompt_to_use]
    dest_suffix = DEST_SUFFIX_PRE + dest_suffix_part

    prompt_str += EXTRA_PROMPT

    print("-" * 80)
    print(f"Prompt: {prompt_str}")
    print(f'Saving edited content to "{dest_image}"...')

    response = client.models.generate_content(
        model=AI_MODEL,
        contents=[
            prompt_str,
            srce_image1,
        ],
        config=GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            candidate_count=CANDIDATE_COUNT,
            temperature=AI_TEMPERATURE,
            top_p=AI_TOP_P,
            top_k=AI_TOP_K,
            seed=SEED,
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            dest_image.write_text(part.text)
            print(f"Saved text to {dest_image}")
        elif part.inline_data is not None:
            output_image = Image.open(BytesIO(part.inline_data.data))
            output_image.save(dest_image)
            print(f"Saved image to {dest_image}")

    print("-" * 80)

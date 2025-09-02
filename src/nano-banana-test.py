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
    EXTRACT_TEXT = auto()


REMOVE_BUBBLE_DEST_SUFFIX = "no-bubbles.png"
RECOLOR_DEST_SUFFIX = "-recolor.png"
PHOTO_DEST_SUFFIX = "-photo.png"
OIL_DEST_SUFFIX = "-oil.png"
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
    Prompts.EXTRACT_TEXT: (
        "Extract the text from this image.",
        EXTRACT_TEXT_DEST_SUFFIX,
    ),
}
# PROMPT = "Remove the smaller inner panel."
# PROMPT = "Improve this comic book cover."  # bit of a dud

PROMPT_TO_USE = Prompts.MAKE_OIL_PAINTING

SYSTEM_INSTRUCTION = "Do not remove any part of characters. Do not vignette."
CANDIDATE_COUNT = 1
AI_TEMPERATURE = 0.9
AI_TOP_P = None
AI_TOP_K = None
SEED = None

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
BARKS_PANELS_PNG = ROOT_DIR / "Barks Panels Pngs"
FANTA_RESTORED_DIR = ROOT_DIR / "Fantagraphics-restored"
# PANEL_TYPE = "Favourites"
PANEL_TYPE = "Splash"
TITLE = "Tralla La"
EDITED = "edited"
# EDITED = ""
IMAGE_FILENAME = "255-big-3.png"

DEST_SUFFIX = PROMPT_TEXT[PROMPT_TO_USE][1]
PROMPT_STR = PROMPT_TEXT[PROMPT_TO_USE][0]

PROMPT_STR += " Make the trees in the foreground taller. Make the sky darker with more clouds."
#PROMPT_STR += " Add a some extra trees and rocks in the foreground. Add some more clouds to the sky."
#PROMPT_STR += " Outpaint the top and bottom of the image to give a consistent scene that seamlessly matches the middle. Crucially make color and structure match."
#SYSTEM_INSTRUCTION += " Change the shape of the output image so that it's 1000 pixels wide and 1600 pixels high."

# SRCE_IMAGE="/home/greg/Books/Carl Barks/Fantagraphics-fixes-and-additions/Carl Barks Vol. 8 - Donald Duck - Trail of the Unicorn (Digital-Empire)/images/245.png"
SRCE_IMAGE = ROOT_DIR / BARKS_PANELS_PNG / PANEL_TYPE / TITLE / EDITED / IMAGE_FILENAME

# SRCE_IMAGE = "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/01.png"
# PROMPT = ("This is a scanned image. Cleanup and correct any warping caused by scanning. Keep the"
#           " output resolution the same as the input resolution."
#           " Don't crop any panel borders.")

dest_image = (
    ROOT_DIR
    / BARKS_PANELS_PNG
    / "AI"
    / TITLE
    / EDITED
    / (SRCE_IMAGE.stem + DEST_SUFFIX)
)
dest_image.parent.mkdir(parents=True, exist_ok=True)
if not dest_image.parent.is_dir():
    raise FileNotFoundError(dest_image)
if dest_image.is_file():
    raise FileExistsError(dest_image)

print(f"Prompt:\n    {PROMPT_STR}\n")
print(f'Saving edited image to "{dest_image}"...')

AI_MODEL = "gemini-2.5-flash-image-preview"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

image = Image.open(SRCE_IMAGE, mode="r")

response = client.models.generate_content(
    model=AI_MODEL,
    contents=[PROMPT_STR, image],
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
        print(part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save(dest_image)

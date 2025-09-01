import os
import sys
from pathlib import Path

from PIL import Image
from io import BytesIO

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig

SYSTEM_INSTRUCTION = "Do not remove any part of characters"
CANDIDATE_COUNT = 1
AI_TEMPERATURE = 0.1
AI_TOP_P = None
AI_TOP_K = None
SEED = None

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
BARKS_PANELS_PNG = ROOT_DIR / "Barks Panels Pngs"
#PANEL_TYPE = "Favourites"
PANEL_TYPE = "Splash"
TITLE ="Only a Poor Old Man"
EDITED = "edited"
#EDITED = ""
IMAGE_FILENAME = "252.png"

#SRCE_IMAGE="/home/greg/Books/Carl Barks/Fantagraphics-fixes-and-additions/Carl Barks Vol. 8 - Donald Duck - Trail of the Unicorn (Digital-Empire)/images/245.png"
SRCE_IMAGE = ROOT_DIR / BARKS_PANELS_PNG / PANEL_TYPE / TITLE / EDITED / IMAGE_FILENAME
#SRCE_IMAGE = "/tmp/255.png"
PROMPT = "Colorize this using color gradients."
#PROMPT = "Make this look like a very realistic 3D photograph."
#PROMPT = "Remove all speech bubbles."
#PROMPT = "Remove all speech bubbles and narrator box."
#PROMPT = "Remove the smaller inner panel."
#PROMPT = "Extract the text from this image."
#PROMPT = "Improve this comic book cover."  # bit of a dud
DEST_SUFFIX="-recolor.png"
#DEST_SUFFIX="-photo.png"

# SRCE_IMAGE = "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/01.png"
# PROMPT = ("This is a scanned image. Cleanup and correct any warping caused by scanning. Keep the"
#           " output resolution the same as the input resolution."
#           " Don't crop any panel borders.")

dest_image = ROOT_DIR / BARKS_PANELS_PNG / 'AI' / TITLE / EDITED / (SRCE_IMAGE.stem + DEST_SUFFIX)
dest_image.parent.mkdir(parents=True, exist_ok=True)
if not dest_image.parent.is_dir():
    raise FileNotFoundError(dest_image)
print(f'Saving edited image to "{dest_image}"...')
if dest_image.is_file():
    raise FileExistsError(dest_image)

AI_MODEL = "gemini-2.5-flash-image-preview"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

image = Image.open(SRCE_IMAGE, mode="r")

response = client.models.generate_content(
    model=AI_MODEL,
    contents=[PROMPT, image],
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

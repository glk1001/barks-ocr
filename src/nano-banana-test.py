import os
from pathlib import Path

from PIL import Image
from io import BytesIO

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig

AI_TEMPERATURE = 0.1
AI_TOP_P = None
AI_TOP_K = None
CANDIDATE_COUNT = 1
SYSTEM_INSTRUCTION = None

ROOT_DIR = Path("/home/greg/Books/Carl Barks")

SRCE_IMAGE = ROOT_DIR / "Barks Panels Pngs/Silhouettes/Darkest Africa/088-3.png"
#SRCE_IMAGE = "/tmp/255.png"
PROMPT = "Colorize this using color gradients."
#PROMPT = "Make this look like a very realistic 3D photograph."
#PROMPT = "Remove all speech bubbles."
#PROMPT = "Remove all speech bubbles and narrator box."
#PROMPT = "Remove the smaller inner panel."
#PROMPT = "Extract the text from this image."

# SRCE_IMAGE = "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/01.png"
# PROMPT = ("This is a scanned image. Cleanup and correct any warping caused by scanning. Keep the"
#           " output resolution the same as the input resolution."
#           " Don't crop any panel borders.")

AI_MODEL = "gemini-2.5-flash-image-preview"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

image = Image.open(SRCE_IMAGE, mode="r")

response = client.models.generate_content(
    model=AI_MODEL,
    contents=[PROMPT, image],
    config=GenerateContentConfig(
        candidate_count=CANDIDATE_COUNT,
        temperature=AI_TEMPERATURE,
        top_p=AI_TOP_P,
        top_k=AI_TOP_K,
        seed=1,
    ),
)
    # config=types.GenerateContentConfig(temperature=AI_TEMPERATURE,
    #                              top_p=AI_TOP_P,
    #                              candidate_count=CANDIDATE_COUNT,
    #                              system_instruction=SYSTEM_INSTRUCTION))

for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save("/tmp/generated_image.png")

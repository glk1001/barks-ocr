import os
from pathlib import Path

from PIL import Image
from io import BytesIO

from google import genai
from google.genai.types import GenerateContentConfig


SYSTEM_INSTRUCTION = "Keep all panel borders intact."
CANDIDATE_COUNT = 1
AI_TOP_P = None
AI_TOP_K = None
SEED = None

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
BARKS_PANELS_PNG = ROOT_DIR / "Barks Panels Pngs"
FANTA_RESTORED_DIR = ROOT_DIR / "Fantagraphics-restored"

IMAGE_FILENAME = "190-4.png"

AI_TEMPERATURE = 0.0


SRCE_IMAGE1 = "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/Originals/RCO008_1466986159.jpg"
SRCE_IMAGE2 = "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/06_upscayl_8400px_digital-art-4x-small-test.png"

# dest_image = (
#     ROOT_DIR
#     / BARKS_PANELS_PNG
#     / "AI"
#     / TITLE
#     / EDITED
#     / (SRCE_IMAGE1.stem + DEST_SUFFIX)
# )
dest_image = Path("/tmp/color-test.png")
dest_image.parent.mkdir(parents=True, exist_ok=True)
if not dest_image.parent.is_dir():
    raise FileNotFoundError(dest_image)
if dest_image.is_file():
    raise FileExistsError(dest_image)

print(f'Saving edited image to "{dest_image}"...')

AI_MODEL = "gemini-2.5-flash-image-preview"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)


image1 = Image.open(SRCE_IMAGE1)
image2 = Image.open(SRCE_IMAGE2)

contents = [
    "This is the first image (Image 1) of a scanned comic book page with halftone coloring, low quality,"
    " and misregistered colors:",
    image1,
    "And this is the second image (Image 2) of the same page but with clean black-and-white lineart:",
    image2,
    """
Task:
Use Image 1 as a color reference and Image 2 as the target. Recolor Image 2 with the colors from Image 1 but use a flat coloring style.

Requirements:

Preserve the black lineart from Image 2 exactly.

Apply the correct flat comic-style colors from Image 1, but remove all halftone dots, noise, and misregistered color artifacts.

Ensure colors align cleanly within the lineart boundaries.

Ensure all panel borders are intact.

Produce a high-quality, professional comic page that looks freshly printed with smooth flat digital coloring.

Keep the aspect ratio of the output image the same as Image 2.

Instruction to Model:
“Colorize the clean lineart (Image 2) using Image 1 as the color guide. Ignore halftone dots, noise,
 and misalignment. Final output should be sharp, clean, and professionally colored in a flat colored style.”
""",
]

response = client.models.generate_content(
    model=AI_MODEL,
    contents=contents,
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
        srce_image1 = Image.open(BytesIO(part.inline_data.data))
        srce_image1.save(dest_image)

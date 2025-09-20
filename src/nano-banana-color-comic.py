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
SEED = 1

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
BARKS_PANELS_PNG = ROOT_DIR / "Barks Panels Pngs"
FANTA_RESTORED_DIR = ROOT_DIR / "Fantagraphics-restored"

IMAGE_FILENAME = "190-4.png"

AI_TEMPERATURE = 0.0


SRCE_IMAGE1 = "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/06_upscayl_8400px_digital-art-4x-orig.png"
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
width, height = image2.size

contents = [
    "This is the first image (Image 1) of a scanned comic book page with halftone coloring,"
    " low quality,and misregistered colors:",
    image1,
    "And this is the second image (Image 2) of the same page but with clean black-and-white lineart:",
    image2,
    f"""
**Primary Command:** Your most important task is to generate an output image that is 
**exactly {width} pixels wide and {height} pixels high**. Do not deviate from these dimensions.

**Objective:** Use the colors from Image 1 to colorize the lineart in Image 2.

**Execution Rules:**
1.  **Color Style:** Apply colors in a smooth, **flat, digital comic book style**.
2.  **Lineart:** Preserve the black lineart from Image 2 perfectly.
3.  **Image Integrity:** The output must contain the entire area of Image 2. All panel borders must
    be fully intact.

**Strict Prohibitions (DO NOT):**
-   **DO NOT** use any halftone patterns, dots, or textures. The color must be flat.
-   **DO NOT** crop, resize, or alter the aspect ratio. The output dimensions are non-negotiable.
-   **DO NOT** copy any noise, blur, or printing errors from Image 1.

**Final Output Checklist:**
-   Dimensions are exactly {width}x{height}.
-   Coloring is flat, with no halftone dots.
-   The entire image, including all borders from Image 2, is present.
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

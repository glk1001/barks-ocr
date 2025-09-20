import os
from io import BytesIO
from pathlib import Path

from google import genai
from google.genai.types import GenerateContentConfig
from PIL import Image

SYSTEM_INSTRUCTION = None
CANDIDATE_COUNT = 1
AI_TOP_P = None
AI_TOP_K = None
SEED = 1

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
CENSORSHIP_FIXES_DIR = ROOT_DIR / "Fantagraphics-censorship-fixes"
DIR_TO_FIX = CENSORSHIP_FIXES_DIR / "wdcs-34"

AI_TEMPERATURE = 0.0


COLOR_REF_FILE = DIR_TO_FIX / "08_upscayl_8400px_digital-art-4x-orig.png"
TARGET_BW_LINEART_FILE = DIR_TO_FIX / "08_upscayl_8400px_digital-art-4x-small-test.png"
dest_image_file = Path("/tmp/color-test-8.png")

dest_image_file.parent.mkdir(parents=True, exist_ok=True)
if not dest_image_file.parent.is_dir():
    raise FileNotFoundError(dest_image_file)
if dest_image_file.is_file():
    raise FileExistsError(dest_image_file)

print(f'Saving edited image to "{dest_image_file}"...')

AI_MODEL = "gemini-2.5-flash-image-preview"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)


image1 = Image.open(COLOR_REF_FILE)
image2 = Image.open(TARGET_BW_LINEART_FILE)
width, height = image2.size
aspect_ratio = height / width

contents = [
    "This is the first image (Image 1) and is a scanned comic book page with halftone coloring,"
    " of low quality, and with misregistered colors:",
    image1,
    "And this is the second image (Image 2) of the same page but with cleaned up black-and-white lineart:",
    image2,
    f"""
**Primary Command:** Your most important task is to generate an output image that has the **exact same aspect ratio as Image 2 ({aspect_ratio})**. Do not deviate from this.

**Objective:** Use the colors from Image 1 as a reference to color the black and white lineart in Image 2.

**Execution Rules:**
1.  **Color Transfer:** Every single colored area in Image 1 must be transferred to the corresponding
    colored area in Image 2. Do not omit any colors. If an area is colored in Image 1, it must be colored in the output.
2.  **Color Style:** Apply colors in a smooth, **flat, digital comic book style**.
3.  **Lineart:** Preserve the black and white lineart from Image 2 perfectly. The lineart must remain on top and be unchanged.
4.  **Image Integrity:** The output must contain the entire area of Image 2. All panel borders must be fully intact. Image 2 must not be rotated or cropped.
5.  **Alignment:** The black and white lineart in the output image must exactly align with the black and white lineart in Image 2.

**Strict Prohibitions (DO NOT):**
-   **DO NOT** use any halftone patterns, dots, or textures. Colors must be flat.
-   **DO NOT** leave any areas uncolored that are colored in Image 1.
-   **DO NOT** crop, resize, or alter the aspect ratio. The output dimensions are non-negotiable.
-   **DO NOT** copy any noise, blur, or printing errors from Image 1.
-   **DO NOT** rotate or resize Image 2 and the output image.

**Final Output Checklist:**
-   Aspect ratio is exactly {aspect_ratio}.
-   All colors from Image 1 are present in the output.
-   Coloring is flat, with no halftone dots.
-   Lineart from Image 2 is perfectly preserved and aligned.
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
        dest_image = Image.open(BytesIO(part.inline_data.data))
        dest_image.save(dest_image_file)

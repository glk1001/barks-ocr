import os
from enum import Enum, auto
from io import BytesIO
from pathlib import Path

from google import genai
from google.genai.types import GenerateContentConfig
from PIL import Image


class Prompts(Enum):
    COLORIZE_WITH_GRADIENTS = auto()
    MAKE_PHOTO_REALISTIC = auto()
    MAKE_OIL_PAINTING = auto()
    MAKE_IMPRESSIONIST_PAINTING = auto()
    MAKE_ANSEL_ADAMS = auto()


RECOLOR_DEST_SUFFIX = "-recolor.png"
PHOTO_DEST_SUFFIX = "-photo.png"
OIL_DEST_SUFFIX = "-oil.png"
IMPRES_DEST_SUFFIX = "-impres.png"
ANSEL_DEST_SUFFIX = "-ansel.png"
EXTRACT_TEXT_DEST_SUFFIX = "-just-text.txt"

PROMPT_TEXT = {
    Prompts.COLORIZE_WITH_GRADIENTS: (
        "colorize the input image using color gradients",
        RECOLOR_DEST_SUFFIX,
    ),
    Prompts.MAKE_PHOTO_REALISTIC: (
        "make the input image look like a super-realistic 3D photograph",
        PHOTO_DEST_SUFFIX,
    ),
    Prompts.MAKE_OIL_PAINTING: (
        "make the input image look like a very realistic and beautiful oil painting",
        OIL_DEST_SUFFIX,
    ),
    Prompts.MAKE_IMPRESSIONIST_PAINTING: (
        "make the input image look like a very beautiful impressionist painting",
        IMPRES_DEST_SUFFIX,
    ),
    Prompts.MAKE_ANSEL_ADAMS: (
        "make the input image like a very detailed black and white Ansel Adams photograph",
        ANSEL_DEST_SUFFIX,
    ),
}
# PROMPT = "Remove the smaller inner panel."
# PROMPT = "Improve this comic book cover."  # bit of a dud

CANDIDATE_COUNT = 1
AI_TOP_P = None
AI_TOP_K = None
SEED = 4

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
BARKS_PANELS_PNG = ROOT_DIR / "Barks Panels Pngs"
FANTA_RESTORED_DIR = ROOT_DIR / "Fantagraphics-restored"

# PANEL_TYPE = "Censorship"
# PANEL_TYPE = "Closeups"
PANEL_TYPE = "Favourites"
#PANEL_TYPE = "Insets"
# PANEL_TYPE = "Splash"
# PANEL_TYPE = "Silhouettes"
DEST_SUFFIX_PRE = ""
# DEST_SUFFIX_PRE = "-cl"

TITLE = "Good Deeds"
EDITED = ""
# EDITED = "edited"
IMAGE_FILENAME = "263-4.png"
AI_TEMPERATURE = 0.5
EXTRA_PROHIBITION = ""
#EXTRA_PROHIBITION = "- **DO NOT** have any characters sleeping."

PROMPT_TYPES = [
    Prompts.COLORIZE_WITH_GRADIENTS,
    Prompts.MAKE_PHOTO_REALISTIC,
    Prompts.MAKE_OIL_PAINTING,
    Prompts.MAKE_IMPRESSIONIST_PAINTING,
    Prompts.MAKE_ANSEL_ADAMS,
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
for prompt_type in PROMPT_TYPES:
    dest_suffix_part = PROMPT_TEXT[prompt_type][1]
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

for prompt_type, dest_image in zip(PROMPT_TYPES, dest_files, strict=True):
    prompt_str, dest_suffix_part = PROMPT_TEXT[prompt_type]
    dest_suffix = DEST_SUFFIX_PRE + dest_suffix_part

#    Use the image's black ink lines to reinforce the structure of the output image.

    final_prompt = f'''
    **Primary Command:** Your most important task is to {prompt_str}.
    
    **Strict Prohibitions (DO NOT):**
    - **CRITICAL MASKING INSTRUCTION:** The character's eyes and pupils are a masked area.
            **DO NOT** alter the characters' eyes or pupils in any way.
            They must be perfectly preserved from the original image.
    - **DO NOT** remove any part of characters.
    - **DO NOT** change character's expressions.
    - **DO NOT** change any objects.
    - **DO NOT** change any clothing.
    - **DO NOT** remove any characters' glasses.
    - **DO NOT** add a signature.
    - **DO NOT** add a border.
    - **DO NOT** add any characters.
    - **DO NOT** vignette.
    - **DO NOT** crop image.
    - **DO NOT** add a signature.
    {EXTRA_PROHIBITION}
    '''

    final_prompt = prompt_str

    print("-" * 80)
    print(f"Prompt: {final_prompt}")
    print(f'Saving edited content to "{dest_image}"...')

    response = client.models.generate_content(
        model=AI_MODEL,
        contents=[
            final_prompt,
            srce_image1,
        ],
        config=GenerateContentConfig(
            system_instruction=None,
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

import os
from enum import Enum, auto
from io import BytesIO
from pathlib import Path

from google import genai
from google.genai.types import GenerateContentConfig
from PIL import Image


class Prompts(Enum):
    CLEAN_AND_SHARPEN = auto()
    COLORIZE_WITH_GRADIENTS = auto()
    MAKE_PHOTO_REALISTIC = auto()
    MAKE_OIL_PAINTING = auto()
    MAKE_IMPRESSIONIST_PAINTING = auto()
    MAKE_ANSEL_ADAMS = auto()


CLEAN_DEST_SUFFIX = "-clean.png"
RECOLOR_DEST_SUFFIX = "-recolor.png"
PHOTO_DEST_SUFFIX = "-photo.png"
OIL_DEST_SUFFIX = "-oil.png"
IMPRES_DEST_SUFFIX = "-impres.png"
ANSEL_DEST_SUFFIX = "-ansel.png"
EXTRACT_TEXT_DEST_SUFFIX = "-just-text.txt"

PROMPT_TEXT = {
    Prompts.CLEAN_AND_SHARPEN: (
        "Enhance the image by cleaning, sharpening, and smoothing black ink lines in input image",
        CLEAN_DEST_SUFFIX,
    ),
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
SEED = 8

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
BARKS_PANELS_PNG = ROOT_DIR / "Barks Panels Pngs"
FANTA_RESTORED_DIR = ROOT_DIR / "Fantagraphics-restored"

# PANEL_TYPE = "Censorship"
# PANEL_TYPE = "Closeups"
PANEL_TYPE = "Favourites"
#PANEL_TYPE = "Insets"
#PANEL_TYPE = "Splash"
# PANEL_TYPE = "Silhouettes"
DEST_SUFFIX_PRE = ""
# DEST_SUFFIX_PRE = "-cl"

TITLE = "Trouble Indemnity"
EDITED = ""
#EDITED = "edited"
IMAGE_FILENAME = "062-6.png"
AI_TEMPERATURE = 1.0
EXTRA_PROHIBITION = ""
EXTRA_PROHIBITION += "- Do not change character's expressions"
EXTRA_PROHIBITION += "- Keep the character's EYES EXACTLY as in input image."
EXTRA_PROHIBITION += "- Do not add glasses to characters."
EXTRA_PROHIBITION += "- Do not add extra clothing or hats."
EXTRA_PROHIBITION += "- Do not add extra pupils to characters' eyes."
#EXTRA_PROHIBITION = "- Keep the character's EYES CLOSED EXACTLY as in input image. Do not add glasses to characters"
#EXTRA_PROHIBITION = "- Add a few clouds to the sky."
#EXTRA_PROHIBITION = "- The character on the tv set is bending over with his tail up and his head is not visible."
#EXTRA_PROHIBITION = "- Carefully horizontally squeeze the image to make it not as wide. Make it look like a landscape photograph"
#EXTRA_PROHIBITION = "- EXTREMELY IMPORTANT - Keep the character jumping up and down in the trailer's eyes closed exactly as in input image."
#EXTRA_PROHIBITION = "- Give the feeling of a mysterious temple in a dark South American jungle. Make it look like a realistic nature photograph"
#EXTRA_PROHIBITION = "- Scrooge is so worried he is wearing a circular rut into the concrete floor of his worry room"
# EXTRA_PROHIBITION = ("- The top hat should be colored black. Between the penguin's legs is a large orange egg. Keep the shape and dimensions"
#                      " and position of the egg the same as the input image. The egg should be resting between the penguin's leg just as in"
#                      " the input image. The penguin is not wearing a hat. Keep the output image very realistic. Like a photo")
#EXTRA_PROHIBITION = "- Give the feeling of a mysterious lost city high in the Andes. Make it look like a realistic nature photograph"
#EXTRA_PROHIBITION = "- It's a scary halloween scene with a witch on a broomstick. MAke it super-realistic."
#EXTRA_PROHIBITION += "- It's an inside view of a pumpkin and a sword is coming through a triangular hole. Keep yellow background with black shadow at top. Just as in input image. Do not cover eyes with anything"
#EXTRA_PROHIBITION += "- Note: the duck character's eyes are closed. No eyelids are visible though. Just single lines as in the input image "
#EXTRA_PROHIBITION = "The lemming in the hat is eating a piece of cheese"
#EXTRA_PROHIBITION = "Looking up at an old mysterious castle on the outskirts of The Black Forest."
#EXTRA_PROHIBITION += "Scrooge is looking away from us. We cannot see his face"
#EXTRA_PROHIBITION += "Scrooge is wearing pince-nez glasses but with no cord. The scrooge in the dream bubble has a goatee"
#EXTRA_PROHIBITION += "Keep the left-hand character a silhouette"
#EXTRA_PROHIBITION += " The javelin thrower has a little bit of hayfever but he does not have a runny nose. He is not bald"
#EXTRA_PROHIBITION += " The musician has his eyes closed enjoying the music he's making."
#EXTRA_PROHIBITION += " Keep the people in the background silhouetted. But make the rest of the image photo-realistic."
EXTRA_PROHIBITION += " Make sure the image photo-realistic."

PROMPT_TYPES = [
    Prompts.MAKE_PHOTO_REALISTIC,
    # Prompts.COLORIZE_WITH_GRADIENTS,
    # Prompts.MAKE_OIL_PAINTING,
    # Prompts.MAKE_IMPRESSIONIST_PAINTING,
    # Prompts.MAKE_ANSEL_ADAMS,
    # Prompts.CLEAN_AND_SHARPEN,
]

if PANEL_TYPE == "Insets":
    SRCE_IMAGE1 = ROOT_DIR / BARKS_PANELS_PNG / PANEL_TYPE / EDITED / IMAGE_FILENAME
else:
    SRCE_IMAGE1 = (
        ROOT_DIR / BARKS_PANELS_PNG / PANEL_TYPE / TITLE / EDITED / IMAGE_FILENAME
    )

AI_MODEL = "gemini-2.5-flash-image"

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
    - **DO NOT** alter the characters' eyes or pupils in any way.
        They must be perfectly preserved from the original image.
    - **DO NOT** remove any part of characters.
    - **DO NOT** change character's expressions.
    - **DO NOT** change any objects.
    - **DO NOT** change any clothing.
    - **DO NOT** remove any characters' glasses.
    - **DO NOT** add any characters.
    - **DO NOT** vignette.
    - **DO NOT** crop image.
    - **DO NOT** add a border.
    - **DO NOT** add a signature.
    {EXTRA_PROHIBITION}
    '''

#    final_prompt = prompt_str

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

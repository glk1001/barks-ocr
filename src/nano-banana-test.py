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
    REMOVE_NARRATION_BOX_ONLY = auto()
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
    Prompts.REMOVE_NARRATION_BOX_ONLY: (
        "Remove all narrator boxes.",
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

CANDIDATE_COUNT = 1
AI_TOP_P = 0.1
AI_TOP_K = None
SEED = 1

ROOT_DIR = Path("/home/greg/Books/Carl Barks")
BARKS_PANELS_PNG = ROOT_DIR / "Barks Panels Pngs"
FANTA_RESTORED_DIR = ROOT_DIR / "Fantagraphics-restored"

# PANEL_TYPE = "Censorship"
# PANEL_TYPE = "Closeups"
PANEL_TYPE = "Favourites"
#PANEL_TYPE = "Insets"
# PANEL_TYPE = "Splash"
PANEL_TYPE = "Silhouettes"
DEST_SUFFIX_PRE = ""
# DEST_SUFFIX_PRE = "-cl"

TITLE = "Forbidden Valley"
EDITED = ""
# EDITED = "edited"
IMAGE_FILENAME = "027-1.png"

AI_TEMPERATURE = 0.0
PROMPT_TO_USE = Prompts.REMOVE_SPEECH_BUBBLES

DEST_SUFFIX = DEST_SUFFIX_PRE + PROMPT_TEXT[PROMPT_TO_USE][1]
PROMPT_STR = PROMPT_TEXT[PROMPT_TO_USE][0]
EXTRA_PROHIBITION = ""
#EXTRA_PROHIBITION = " Do not remove any black ink hatching on the back wall. And make sure you inpaint the black ink hatching under the righthand speech bubble."
#EXTRA_PROHIBITION = " Do not remove the chicken wire in the background."
#EXTRA_PROHIBITION = " Make sure you remove the yellow narration box."
#EXTRA_PROHIBITION = " Do not crop the righthand side of the image. Slightly extend the width to the right"
#EXTRA_PROHIBITION += " Under the narration box are the legs and shoes of two people lying down."

final_prompt = f"""
**Primary Command:** Your most important task is to {PROMPT_STR}.

**Strict Prohibitions (DO NOT):**
- **CRITICAL MASKING INSTRUCTION:** The character's eyes and pupils are a masked area.
        **DO NOT** alter the characters' eyes or pupils in any way.
        They must be perfectly preserved from the original image.
- **DO NOT** remove any characters.
- **DO NOT** remove any part of characters.
- **DO NOT** change character's expressions.
- **DO NOT** change any objects.
- **DO NOT** change any clothing.
- **DO NOT** remove any characters' glasses.
- **DO NOT** remove any characters' hats.
- **DO NOT** add a signature.
- **DO NOT** add a border.
- **DO NOT** add any characters.
- **DO NOT** add any hats or other clothing.
- **DO NOT** change any colors.
- **DO NOT** vignette.
- **DO NOT** crop the image.
- **DO NOT** trim the image.
- **DO NOT** add a signature.
- **KEEP** the same aspect ratio as the input image.
{EXTRA_PROHIBITION}
"""

#PROMPT_STR += " Also, inpaint missing part of image at top left."
#PROMPT_STR += " Keep window in background."

# PROMPT_STR += " Don't change Donald's expressions."
# PROMPT_STR += " Keep the high collar. Keep Donald's beak closed the same as the input image. Donald's hat should be blue, the same as the input image."
# PROMPT_STR += " Just remove the speech bubbles. Do not change anything else."
# PROMPT_STR += "No clouds."
# PROMPT_STR += " Do not put a hat on Donald."
# PROMPT_STR += " Show grey smoke and more blackened background. It's the aftermath of a bushfire."
# PROMPT_STR += " Clearly show the '313' number plate"
# PROMPT_STR = ("The first image is a black and white comic book page."
#               # " It consists of black lines on a white page forming panels (rectangular sections),"
#               # " each panel containing character and object shapes."
#               " Turn this into a colored comic book image where each black line shape is colored in."
#               " The black lines of the first image should not be changed."
#               " As a color guide, use the colors from the second image which is a colored comic"
#               " book page similar to the first image."
#               " The image that is output should be the first black and white image but with added colors."
#               " Do not output anything from the second image."
#               " Do not use any of the black lines from the second image."
#               " VERY IMPORTANT: Like a coloring book, keep all colors WITHIN the black line shapes."
#               " So colors should not go over black lines."
#               " Use a flat coloring style."
#               " Color in all the characters and objects in each panel."
#               " Color in all characters' clothing including hats and bow-ties."
#               " The color of each character and object should match the color in the second guide image."
#               " Character and object colors should be consistent over all panels."
#               " Include the yellow fence in panel 1,"
#               " the yellow background in panel 2, "
#               " and the red shape in panel 3."
#               " Do not trim the top and bottom of the first image."
#               " Write the number of each panel in a large black font in the middle of each panel. ")
# PROMPT_STR = ("The first image is a colored comic book page containing 5 bordered panels."
#               " The second image is a black and white uncolored version of the same comic book page."
#               " Using the first color image as guide, for each panel in the second image"
#               " add colors to the black and white panel and output the colored result.")
# PROMPT_STR += " Make background detailed and sharp."
# PROMPT_STR += " Do not remove the wanted poster and text inside it"
# PROMPT_STR = " Make the character rowing the boat have a very soft subtle glow of light like the other characters in the boat. Don't touch the other characters"
# PROMPT_STR += " Make the trees in the foreground taller. Make the sky darker with more clouds."
# PROMPT_STR += " Add a some extra trees and rocks in the foreground. Add some more clouds to the sky."
# PROMPT_STR += (" This is an image of a deep valley in the Himalayas. Outpaint the top of the image to give a consistent scene that seamlessly matches the middle."
#                " Extend the image by having a very tall and steep snow covered mountain range moving off to the right in the background."
#                " Extend the mountain range to near the top of the image."
#                " The steep slope above the waterfall should be seamlessly continued."
#                " DO NOT have another waterfall."
#                " Make a dark cloudy sky. Crucially make color and structure match.")
# PROMPT_STR += " Outpaint the top and bottom of the image to give a consistent scene that seamlessly matches the middle. Crucially make color and structure match."
# SYSTEM_INSTRUCTION += " Change the shape of the output image so that it's 1000 pixels wide and 1600 pixels high."

# SRCE_IMAGE="/home/greg/Books/Carl Barks/Fantagraphics-fixes-and-additions/Carl Barks Vol. 8 - Donald Duck - Trail of the Unicorn (Digital-Empire)/images/245.png"
if PANEL_TYPE == "Insets":
    SRCE_IMAGE1 = ROOT_DIR / BARKS_PANELS_PNG / PANEL_TYPE / EDITED / IMAGE_FILENAME
else:
    SRCE_IMAGE1 = (
        ROOT_DIR / BARKS_PANELS_PNG / PANEL_TYPE / TITLE / EDITED / IMAGE_FILENAME
    )

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
    / (SRCE_IMAGE1.stem + DEST_SUFFIX)
)
# dest_image = Path("/tmp/color-test.png")
dest_image.parent.mkdir(parents=True, exist_ok=True)
if not dest_image.parent.is_dir():
    raise FileNotFoundError(dest_image)
if dest_image.is_file():
    raise FileExistsError(dest_image)

print(f"Prompt:\n    {final_prompt}\n")
print(f'Saving edited image to "{dest_image}"...')

AI_MODEL = "gemini-2.5-flash-image"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

# SRCE_IMAGE1 = "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/Originals/RCO003_1466986159.jpg"
# SRCE_IMAGE2 = "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/01_cleaned_small.png"
srce_image1 = Image.open(SRCE_IMAGE1, mode="r")
# srce_image2 = Image.open(SRCE_IMAGE2, mode="r")

response = client.models.generate_content(
    model=AI_MODEL,
    contents=[
        final_prompt,
        srce_image1,
        #       srce_image2,
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
        print(part.text)
    elif part.inline_data is not None:
        srce_image1 = Image.open(BytesIO(part.inline_data.data))
        srce_image1.save(dest_image)

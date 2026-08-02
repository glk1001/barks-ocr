# ruff: noqa: T201,E501,N806,PLR0915,C901,S108

from io import BytesIO
from pathlib import Path

from google.genai.errors import ClientError
from google.genai.types import GenerateContentConfig, HarmBlockThreshold, HarmCategory
from PIL import Image

from barks_ocr.utils.gemini_ai import AI_PRO_IMAGE_MODEL, CLIENT


def main() -> None:
    CANDIDATE_COUNT = 1
    AI_TOP_P = None
    AI_TOP_K = None
    SEED = 8

    ROOT_DIR = Path("/tmp")
    BARKS_PANELS_PNG = ROOT_DIR / "mines-of-king-solomon-023-1.png"
    BARKS_PANELS_PNG_OUT = ROOT_DIR / "mines-of-king-solomon-023-1-out.png"

    AI_TEMPERATURE = 0.5

    EXTRA_PROHIBITION = ""
    EXTRA_PROHIBITION += "- **VERY IMPORTANT:** **DO NOT** change any characters' expressions.\n"
    EXTRA_PROHIBITION += "- **Keep** all characters' **EYES EXACTLY** as in input image.\n"
    EXTRA_PROHIBITION += "- **DO NOT** add glasses to any characters.\n"
    EXTRA_PROHIBITION += "- **DO NOT** add extra clothing or hats.\n"
    EXTRA_PROHIBITION += "- **DO NOT** change clothing or hats.\n"
    EXTRA_PROHIBITION += "- **DO NOT** add extra pupils to characters' eyes.\n"

    srce_image1 = Image.open(BARKS_PANELS_PNG, mode="r").convert("RGB")

    dest_image = BARKS_PANELS_PNG_OUT

    dest_image.parent.mkdir(parents=True, exist_ok=True)
    if not dest_image.parent.is_dir():
        msg = (
            f"ERROR: Parent directory does not exist and could not be created: {dest_image.parent}"
        )
        raise FileNotFoundError(msg)
    if dest_image.is_file():
        msg = f"Dest file exists: {dest_image}"
        raise FileExistsError(msg)

    prompt_str = """
You a great artist with oil paints and also a lover of comics.
I've uploaded a comic book panel from the 1957 story "The Mines of King Solomon". Can you remove the speech bubbles,
and re-shape the panel as a tall comic book cover, taller than it is wide, in portrait orientation.
Color it in a very mysterious way with a 50's oil painting look. Keep the look, pose, and expression of the characters
the same as in the input image. Keep the same orientation and look of the all the objects in the scene the same
as in input image.
Because you love comics you want to keep the look and structure of your painting as close as possible
to the artist's drawing. Try to capture the character faces as close as possible to how the comic artist drew them.
**Don't put in any extra text like mastheads or titles.**
        """

    print("-" * 80)
    print(f"Prompt: {prompt_str}")
    print(f'Saving edited content to "{dest_image}"...')

    config_kwargs = {
        "candidate_count": CANDIDATE_COUNT,
        "temperature": AI_TEMPERATURE,
        "seed": SEED,
        "safety_settings": [
            {"category": category, "threshold": HarmBlockThreshold.BLOCK_NONE}
            for category in [
                HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                HarmCategory.HARM_CATEGORY_HARASSMENT,
                HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
            ]
        ],
    }
    if AI_TOP_P is not None:
        config_kwargs["top_p"] = AI_TOP_P
    if AI_TOP_K is not None:
        config_kwargs["top_k"] = AI_TOP_K

    config = GenerateContentConfig(**config_kwargs)
    print(f"Config: {config}")

    try:
        response = CLIENT.models.generate_content(
            model=AI_PRO_IMAGE_MODEL,
            contents=[
                prompt_str,
                srce_image1,
            ],
            config=config,
        )
    except ClientError as e:
        print(f"API Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response body: {e.response.text}")
        raise

    if not response.candidates:
        print("ERROR: No candidates in response.")
        print(f"Prompt feedback: {response.prompt_feedback}")
        return

    candidate = response.candidates[0]
    print(f"Finish reason: {candidate.finish_reason}")
    if candidate.content is None:
        print("ERROR: Candidate content is None (likely blocked or unsupported).")
        print(f"Safety ratings: {candidate.safety_ratings}")
        return
    if candidate.content.parts is None:
        print("ERROR: Candidate content.parts is None.")
        return

    for part in candidate.content.parts:
        if part.text is not None:
            dest_image.write_text(part.text)
            print(f"Saved text to {dest_image}")
        elif part.inline_data is not None:
            output_image = Image.open(BytesIO(part.inline_data.data))
            output_image.save(dest_image)
            print(f"Saved image to {dest_image}")

    print("-" * 80)


if __name__ == "__main__":
    main()

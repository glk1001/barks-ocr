import copy
import json
from pathlib import Path
from typing import Any

from loguru import logger
from PIL import Image
from pydantic import BaseModel, Field

from .gemini_ai import AI_FLASH_MODEL, CLIENT
from .gemini_ai_comic_prompts import comic_prompt


class Group(BaseModel):
    panel_id: str = Field(description="Panel id.")
    text_bubble_id: str = Field(description="Text bubble id.")
    box_ids: list[str] = Field(description="List of cleaned text box ids.")
    split_cleaned_box_texts: dict[str, str] = Field(
        description="Dict of box ids and corresponding text"
    )
    original_text: str = Field(description="The OCR output before cleaning")
    cleaned_text: str = Field(description="The corrected and cleaned text")
    type: str = Field(description="dialogue|thought|narration|sound_effect|background")
    style: str = Field(description="normal|emphasized|angled|split")
    notes: str = Field(
        description="Justification for inclusion if background or sound effect, any corrections"
        " or uncertainties|none"
    )


class OcrOutput(BaseModel):
    groups: list[Group]


def get_cleaned_text(text: str) -> tuple[str, str]:
    reason = ""
    if r"\\n" in text:
        text = text.replace(r"\\n", "\\n")
        reason = "Double backslash newline"
    if r"\\'" in text:
        text = text.replace(r"\\'", "'")
        reason = "Double backslash single quote"
    if r"\'" in text:
        text = text.replace(r"\'", "'")
        reason = "Single backslash single quote"

    return text, reason


def get_ai_predicted_groups(
    svg_stem: str, ocr_type: str, image: Image.Image, ocr_results: list[dict[str, Any]]
) -> list[Any]:
    # Make the data AI-friendly.
    width, height = image.size
    norm_ocr_results = norm2ai(ocr_results, height, width)
    prompt = comic_prompt.format(norm_ocr_results)

    """Process OCR results with AI."""
    response = CLIENT.models.generate_content(
        model=AI_FLASH_MODEL,
        contents=[
            image,
            prompt,
        ],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": OcrOutput.model_json_schema(),
        },
    )

    cleaned, reason_changed = get_cleaned_text(response.text)
    if reason_changed:
        logger.warning(f"Fixed json in model response: {reason_changed}.")

    temp_cleaned_file = Path(f"/tmp/{svg_stem}-{ocr_type}-gemini-cleaned-response.json")  # noqa: S108
    logger.info(f'Writing gemini cleaned response to "{temp_cleaned_file}".')
    with temp_cleaned_file.open("w") as f:
        f.write(cleaned)

    return json.loads(cleaned, strict=False)


def norm2ai(bounds: list[dict[str, Any]], height: int, width: int) -> list[dict[str, Any]]:
    """Convert normal image bounds to AI supported Bounds."""
    norm_bounds = copy.deepcopy(bounds)

    for bound in norm_bounds:
        box = bound["text_box"]
        norm_box = []
        for xy in box:
            x = int((xy[0] / width) * 1000)
            y = int((xy[1] / height) * 1000)
            # Note: Gemini coords have y values before x values.
            norm_box.append(y)
            norm_box.append(x)

        bound["text_box"] = norm_box

    return norm_bounds

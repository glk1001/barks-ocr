import copy
import json
from typing import Dict, List

import google.generativeai as genai
from PIL import Image
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig

from .gemini_ai_comic_prompts import comic_prompt


def get_ai_predicted_groups(ocr_name: str, image: Image.Image, ocr_results: List[Dict[str, any]], api_key: str) -> Dict:
    # Make the data AI-friendly
    width, height = image.size
    norm_ocr_results = _norm2ai(ocr_results, height, width)

    """Process OCR results with AI."""
    model = configure_genai(api_key)
    prompt = comic_prompt.format(norm_ocr_results)
    response = model.generate_content([image, prompt])
    text = response.text

    cleaned = text
    # cleaned = text.replace(r'\"', '"')
    # cleaned = cleaned.replace(r"\'", "'")
    # cleaned = cleaned.replace(r"\\n", "\n")
    with open(f"/tmp/{ocr_name}-prelim-cleaned.json", "w") as f:
        f.write(cleaned)
    data = json.loads(cleaned, strict=False)

    return data


def _norm2ai(bounds: List[Dict[str, any]], height: int, width: int):
    """Converts normal image bounds to AI supported Bounds"""
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


def configure_genai(api_key: str) -> genai.GenerativeModel:
    """Configure and return a GenerativeModel instance."""

    safety_ratings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=GenerationConfig(
            response_mime_type="application/json", temperature=0, top_k=1, top_p=0
        ),
        safety_settings=safety_ratings,
    )

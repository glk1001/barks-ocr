import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

AI_PRO_IMAGE_MODEL = "gemini-3-pro-image-preview"
AI_PRO_MODEL = "gemini-3-pro-preview"

load_dotenv(Path(__file__).parent.parent.parent / ".env.runtime")

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CLIENT = genai.Client(api_key=GEMINI_API_KEY)

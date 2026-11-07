import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

AI_PRO_IMAGE_MODEL = "gemini-nano-banana-2.1"
AI_PRO_MODEL = "gemini-4-argon"

load_dotenv(Path(__file__).parents[3] / ".env.runtime")

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CLIENT = genai.Client(api_key=GEMINI_API_KEY)

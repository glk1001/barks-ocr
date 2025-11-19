import os

from google import genai

AI_FLASH_IMAGE_MODEL = "gemini-2.5-flash-image"
AI_FLASH_MODEL = "gemini-2.5-flash"
AI_PRO_MODEL = "gemini-2.5-pro"
# AI_PRO_MODEL = "gemini-3-pro-preview"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CLIENT = genai.Client(api_key=GEMINI_API_KEY)

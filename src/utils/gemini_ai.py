import os

from google import genai

AI_IMAGE_MODEL = "gemini-2.5-flash"
AI_PRO_MODEL = "gemini-2.5-pro"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CLIENT = genai.Client(api_key=GEMINI_API_KEY)

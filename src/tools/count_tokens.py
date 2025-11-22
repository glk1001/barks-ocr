from google import genai

from utils.gemini_ai import AI_PRO_MODEL, CLIENT
from utils.gemini_ai_comic_prompts import comic_prompt

client = genai.Client()
prompt = comic_prompt.format("hello")
prompt = "0"
image_file = "/home/greg/Books/Carl Barks/Projects/OCR/Results/Carl Barks Vol. 2 - Donald Duck - Frozen Gold (Salem-Empire)/007-paddleocr-ocr-gemini-boxes-annotated.png"
your_image_file = client.files.upload(file=image_file)

print(CLIENT.models.count_tokens(model=AI_PRO_MODEL, contents=[prompt, your_image_file]))
# ( e.g., total_tokens: 263 )

# response = client.models.generate_content(
#     model="gemini-2.0-flash", contents=[prompt, your_image_file]
# )
# print(response.usage_metadata)
# ( e.g., prompt_token_count: 264, candidates_token_count: 80, total_token_count: 345 )

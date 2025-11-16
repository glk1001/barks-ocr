import os
import sys
from pathlib import Path

from google import genai
from google.genai.types import UploadFileConfigDict

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-2.5-flash"


prompt = """
Please convert these image files of complex scanned page images into a reflowable HTML file suitable for EPUB conversion. Ensure the following:
1 Note that the pages have two columns of text.
2 Note that most of the paragraphs are synopses, each with a formatted heading in bold.
4 Don't deviate from synopsis text. If you're not sure of the text say so. 
5 Retain Text Formatting: Extract all text, formatted with proper headings and paragraphs for reflowable layout on e-readers.
6 Exclude any images: exclude images but put a note where the image should.
7 Output Ready for EPUB: Save the result as a single HTML file with embedded images, ready for seamless import into Calibre for EPUB conversion.
"""

# for model in list_models():
#     print(model)

client = genai.Client(api_key=GEMINI_API_KEY)

image_dir = "/tmp/book"
image_paths = [
    os.path.join(image_dir, f)
    for f in os.listdir(image_dir)
    if f.lower().endswith((".png", ".jpg", ".jpeg"))
]

# for f in client.files.list():
#     client.files.delete(name=f.name)
# sys.exit(0)

uploaded_files = []
for path in image_paths:
    uploaded_file = client.files.upload(
        file=path, config=UploadFileConfigDict(name=Path(path).stem)
    )
    uploaded_files.append(uploaded_file)
uploaded_files = sorted(uploaded_files, key=lambda f: f.name)

print("My files:")
for f in uploaded_files:
    print(" ", f.name)
# for f in client.files.list():
#     print(' ', f.name)
# sys.exit(0)

# Prepare the content with the uploaded file IDs and a text prompt
contents = [prompt]
contents.extend(uploaded_files)

response = client.models.generate_content(model=MODEL, contents=contents)

print(response.text)

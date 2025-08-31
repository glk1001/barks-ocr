import google.generativeai as genai
import os

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

prompt = """
Please convert these images of complex scanned page images into a reflowable HTML file suitable
for EPUB conversion. Ensure the following:
1 Note that the pages have two columns of text.
2 Retain Text Formatting: Extract all text, formatted with proper headings and paragraphs for
reflowable layout on e-readers.
3 Exclude any images: exclude images but put a note where the image should be.
4 Output Ready for EPUB: Save the result as a single HTML file with embedded images, ready for
seamless import into Calibre for EPUB conversion.
"""

image_dir = "/tmp/book"
image_paths = [
    os.path.join(image_dir, f)
    for f in os.listdir(image_dir)
    if f.lower().endswith((".png", ".jpg", ".jpeg"))
]

contents = []
for image_path in image_paths:
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    contents.append({"mime_type": "image/png", "data": image_data})

response = model.generate_content([prompt, contents])
print(response.text)

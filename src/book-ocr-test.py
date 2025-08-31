import os

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]


prompt = """
Please convert this zip file of complex scanned page images into a reflowable HTML file suitable
for EPUB conversion. Ensure the following:
1 Note that the pages have two columns of text.
2 Retain Text Formatting: Extract all text, formatted with proper headings and paragraphs for
reflowable layout on e-readers.
3 Exclude any images: exclude images but put a note where the image should be.
4 Output Ready for EPUB: Save the result as a single HTML file with embedded images, ready for
seamless import into Calibre for EPUB conversion.
"""


def get_book_html(zip_file_path: str, api_key: str) -> str:
    model = configure_genai(api_key)
    print("Configured model.")

    try:
        print(f'Uploading file: "{zip_file_path}".')
        uploaded_file = genai.upload_file(
            zip_file_path,
            name=os.path.basename(zip_file_path),
            #        zip_file_path, mime_type = "application/zip", name = os.path.basename(zip_file_path)
        )
        print(f'Uploaded file: "{uploaded_file}".')

        response = model.generate_content(
            [
                uploaded_file,
                prompt,
            ]
        )

        print(response.text)
        return response.text

    except Exception as e:
        raise Exception(f"An error occurred: {e}")


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


if __name__ == "__main__":
    #    zip_file = "/home/greg/Prj/workdir/barks/of ducks and men-e summer.zip"
    zip_file = "article01.jpg"

    book_html = get_book_html(zip_file, GEMINI_API_KEY)

    with open("/tmp/book-test.html", "w") as f:
        f.write(book_html)

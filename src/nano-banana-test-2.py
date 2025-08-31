import os
import base64
import google.generativeai as genai

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash-image-preview')

with open("/home/greg/Books/Carl Barks/Barks Panels Pngs/Favourites/Rival Beachcombers/173-4.png", 'rb') as img_file:
    img_data = base64.b64encode(img_file.read()).decode()

prompt = "Colorize this comic book panel using color gradients."
response = model.generate_content([{'inline_data': {'mime_type': 'image/jpeg', 'data': img_data}}, prompt])

generated_img = base64.b64decode(response.parts[0].inline_data.data)
with open('/tmp/173-4.png', 'wb') as out:
    out.write(generated_img)
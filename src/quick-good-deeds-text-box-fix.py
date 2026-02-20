import json
from pathlib import Path

files = [
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim/Carl Barks Vol. 1 - Donald Duck - Finds Pirate Gold (Salem-Empire)/259-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim/Carl Barks Vol. 1 - Donald Duck - Finds Pirate Gold (Salem-Empire)/259-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim/Carl Barks Vol. 1 - Donald Duck - Finds Pirate Gold (Salem-Empire)/260-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim/Carl Barks Vol. 1 - Donald Duck - Finds Pirate Gold (Salem-Empire)/260-paddleocr-gemini-prelim-groups.json"
    ),
]

for file in files:
    ocr_json = json.loads(file.read_text())

    for group in ocr_json["groups"].values():
        text_box = group["text_box"]
        for i in range(4):
            for j in range(2):
                text_box[i][j] = round(text_box[i][j] * (8700 / 9900))

    with file.open("w") as f:
        json.dump(ocr_json, f, indent=4)

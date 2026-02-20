import json
from pathlib import Path

files = [
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/250-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/250-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/251-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/251-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/252-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/252-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/253-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/253-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/254-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/254-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/255-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/255-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/256-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/256-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/257-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/257-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/258-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/258-paddleocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/259-easyocr-gemini-prelim-groups.json"
    ),
    Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)/259-paddleocr-gemini-prelim-groups.json"
    ),
]

for file in files[:1]:
    ocr_json = json.loads(file.read_text())

    for group in ocr_json["groups"].values():
        text_box = group["text_box"]
        for i in range(4):
            for j in range(2):
                text_box[i][j] = round(text_box[i][j] * (8700 / 8480))

    with file.open("w") as f:
        json.dump(ocr_json, f, indent=4)

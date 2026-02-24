# ruff: noqa: ERA001

import json
from pathlib import Path


def scale_rect(  # noqa: D417
    scale: float, x0: float, y0: float, x1: float, y1: float
) -> tuple[int, int, int, int]:
    """Scales a rectangle from its center point.

    Args:
        scale: The scaling factor (e.g., 2.0 makes it twice as big, 0.5 makes it half size).
        x0, y0: Top-left coordinates.
        x1, y1: Bottom-right coordinates.

    Returns:
        (new_x0, new_y0, new_x1, new_y1)

    """
    # 1. Calculate current dimensions
    width = x1 - x0
    height = y1 - y0

    # 2. Calculate the center point
    center_x = x0 + (width / 2)
    center_y = y0 + (height / 2)

    # 3. Calculate new dimensions based on scale
    new_width = width * scale
    new_height = height * scale

    # 4. Calculate new coordinates relative to the center
    # We subtract half the new width/height from the center to get top-left
    # We add half the new width/height to the center to get bottom-right
    new_x0 = center_x - (new_width / 2)
    new_y0 = center_y - (new_height / 2)
    new_x1 = center_x + (new_width / 2)
    new_y1 = center_y + (new_height / 2)

    return round(new_x0), round(new_y0), round(new_x1), round(new_y1)


def main() -> None:
    prelim_dir = Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim/"
        "Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)"
    )
    prelim_backup_dir = Path(
        "/home/greg/Books/Carl Barks/Fantagraphics-restored-ocr/Prelim-backups/"
        "Carl Barks Vol. 3 - Donald Duck - Mystery of the Swamp (Salem-Empire)"
    )

    files = [
        # "250-easyocr-gemini-prelim-groups.json",
        # "250-paddleocr-gemini-prelim-groups.json",
        # "251-easyocr-gemini-prelim-groups.json",
        # "251-paddleocr-gemini-prelim-groups.json",
        # "252-easyocr-gemini-prelim-groups.json",
        # "252-paddleocr-gemini-prelim-groups.json",
        # "253-easyocr-gemini-prelim-groups.json",
        # "253-paddleocr-gemini-prelim-groups.json",
        # "254-easyocr-gemini-prelim-groups.json",
        # "254-paddleocr-gemini-prelim-groups.json",
        # "255-easyocr-gemini-prelim-groups.json",
        # "255-paddleocr-gemini-prelim-groups.json",
        # "256-easyocr-gemini-prelim-groups.json",
        # "256-paddleocr-gemini-prelim-groups.json",
        # "257-easyocr-gemini-prelim-groups.json",
        # "257-paddleocr-gemini-prelim-groups.json",
        # "258-easyocr-gemini-prelim-groups.json",
        # "258-paddleocr-gemini-prelim-groups.json",
        # "259-easyocr-gemini-prelim-groups.json",
        # "259-paddleocr-gemini-prelim-groups.json",
    ]

    x_scale = 0.92 * (8700 / 8480)
    y_scale = 0.925 * (8700 / 8480)
    # scale = 1.0
    xlat = 60
    ylat = -25

    # odd
    # x_scale = 0.92*(8700 / 8480)
    # y_scale = 0.928*(8700 / 8480)
    # # scale = 1.0
    # xlat = 130
    # ylat = -25

    rect_scale = 1.1

    for file in files:
        backup_file_path = prelim_backup_dir / file
        file_path = prelim_dir / file
        file_path.write_bytes(backup_file_path.read_bytes())

        ocr_json = json.loads(file_path.read_text())

        for group in ocr_json["groups"].values():
            text_box = group["text_box"]
            for i in range(4):
                text_box[i][0] = round(x_scale * (xlat + text_box[i][0]))
                text_box[i][1] = round(y_scale * (ylat + text_box[i][1]))
                # text_box[i][0] = round((x_scale * text_box[i][0]) + xlat)
                # text_box[i][1] = round((y_scale * text_box[i][1]) + ylat)

            new_x0, new_y0, new_x1, new_y1 = scale_rect(rect_scale, *text_box[0], *text_box[2])

            text_box[0] = (new_x0, new_y0)
            text_box[1] = (new_x1, new_y0)
            text_box[2] = (new_x1, new_y1)
            text_box[3] = (new_x0, new_y1)

        with file_path.open("w") as f:
            json.dump(ocr_json, f, indent=4)


if __name__ == "__main__":
    main()

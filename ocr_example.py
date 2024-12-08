import sys
from typing import Tuple

import autocorrect
import cv2 as cv
import easyocr
import enchant
import numpy as np
import pytesseract
from PIL import Image
from PIL import ImageDraw

REJECTED_WORDS = ["OO", "|", "L", "\\", "IY"]

spell_dict = enchant.DictWithPWL("en_US", "mywords.txt")
spell_correct = autocorrect.Speller()


def word_is_ok(word: str) -> Tuple[bool, str]:
    word = word.upper().strip()
    orig_word = word

    if not word:
        return False, ""

    if word in REJECTED_WORDS:
        return False, ""

    if spell_dict.check(word):
        return True, word
    word = word.rstrip(").!;?,")
    if spell_dict.check(word):
        return True, orig_word

    possible_words = spell_dict.suggest(word)
    possible_words = [f'"{word}"' for word in possible_words]
    # print(f"  possible_words = {possible_words}.")
    if possible_words:
        return True, possible_words[0]

    word = spell_correct.autocorrect_word(word)
    print(f"AUTO corrected word: '{word}'")
    if not spell_dict.check(word):
        return False, ""
    return True, word


def get_easyocr_text_box_data(image_file: str):
    reader = easyocr.Reader(["en"])
    result = reader.readtext(image_file)

    txt_boxes = []
    for bbox, text, prob in result:
        (tl, tr, br, bl) = bbox
        print(
            f'prob = {prob:4.2f}, text = "{text}", Box:'
            f" {bl[0]:.0f}, {bl[1]:.0f}, {br[0]:.0f}, {br[1]:.0f},"
            f" {tl[0]:.0f}, {tl[1]:.0f}, {tr[0]:.0f}, {tr[1]:.0f}"
        )

        text_str = text.strip()
        if prob < 0.1 or not text_str:
            continue

        words = text_str.split(" ")
        accepted_words = []
        text_ok = True
        for word in words:
            text_ok, accepted_word = word_is_ok(word)
            if not text_ok:
                break
            accepted_words.append(accepted_word)
        if not text_ok:
            continue

        print(f'prob = {prob:4.2f}, text = "{" ".join(accepted_words)}" -- ACCEPTED')
        x0 = tl[0]
        y0 = tl[1]
        x1 = tr[0]
        y1 = tr[1]
        x2 = br[0]
        y2 = br[1]
        x3 = bl[0]
        y3 = bl[1]
        txt_boxes.append([x0, y0, x1, y1, x2, y2, x3, y3])

        # txt_boxes.append([x0, y0, x1, y1])
        # if y0 > y1:
        #     print(f"ERROR: y0, {y0} > {y1}.")

    return txt_boxes


def get_text_box_data(img):
    config = r"--oem 1 --psm 6"  # 3,4,6,11

    d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=config)
    print(d)

    txt_boxes = []
    n_boxes = len(d["level"])
    for i in range(n_boxes):
        text_str = d["text"][i].strip()
        print(f'i: {i} - conf = {d["conf"][i]}, text = "{text_str}"')
        if d["conf"][i] == -1:
            continue
        if d["conf"][i] < 30 or not text_str:
            continue
        if not word_is_ok(text_str):
            continue
        print(f'i: {i} - conf = {d["conf"][i]}, text = "{text_str}" -- ACCEPTED')
        (x, y, w, h) = (d["left"][i], d["top"][i], d["width"][i], d["height"][i])
        txt_boxes.append([x, y, x + w, y + h])

    return txt_boxes


def get_text_boxes(img):
    h, w, _ = img.shape  # assumes color image

    boxes = pytesseract.image_to_boxes(img)  # also include any config options you use

    txt_boxes = []
    for b in boxes.splitlines():
        b = b.split(" ")
        x1 = int(b[1])
        y1 = h - int(b[2])
        x2 = int(b[3])
        y2 = h - int(b[4])
        txt_boxes.append([x1, y1, x2, y2])

    return txt_boxes


def get_bw_image(file: str) -> cv.typing.MatLike:
    black_mask = cv.imread(file, -1)

    scale = 4
    black_mask = cv.resize(
        black_mask, (0, 0), fx=1.0 / scale, fy=1.0 / scale, interpolation=cv.INTER_AREA
    )

    _, _, _, binary = cv.split(black_mask)
    binary = np.uint8(255 - binary)

    return binary


if __name__ == "__main__":
    input_image_file = sys.argv[1]

    bw_image = get_bw_image(input_image_file)
    grey_image_file = "/tmp/image_grey.png"
    cv.imwrite(grey_image_file, bw_image)

    # tesseract_text = pytesseract.image_to_string(image)
    # print(tesseract_text)

    # text_boxes = get_text_boxes(image)
    # print(text_boxes)

    # pil_image = Image.fromarray(image)
    # img_rects = ImageDraw.Draw(pil_image)
    # for box in text_boxes:
    #     shape = [(box[0], box[3]), (box[2], box[1])]
    #     img_rects.rectangle(shape, outline="red")
    #
    # img_rects._image.save("/tmp/bubbles-text-boxes.png")

    # text_data_boxes = get_text_box_data(image)
    #
    # pil_image = Image.fromarray(image)
    # img_rects = ImageDraw.Draw(pil_image)
    # for box in text_data_boxes:
    #     shape = [(box[0], box[1]), (box[2], box[3])]
    #     img_rects.rectangle(shape, outline="green", width=5)
    #
    # img_rects._image.save("/tmp/bubbles-text-data-boxes.png")

    text_data_boxes = get_easyocr_text_box_data(grey_image_file)

    pil_image = Image.fromarray(cv.merge([bw_image, bw_image, bw_image]))
    img_rects = ImageDraw.Draw(pil_image)
    for box in text_data_boxes:
        img_rects.polygon(box, outline="green", width=5)

    img_rects._image.save("/tmp/bubbles-text-data-boxes-easy.png")

# NOT SO GOOD - EXAMPLE WOULD NOT RUN - 'draw_ocr' parameter issues

import sys

import cv2 as cv
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR, draw_ocr


# Paddleocr supports Chinese, English, French, German, Korean and Japanese.
# You can set the parameter `lang` as `ch`, `en`, `french`, `german`, `korean`, `japan`
# to switch the language model in order.


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

    ocr = PaddleOCR(
        use_angle_cls=True, lang="en"
    )  # need to run only once to download and load model into memory
    result = ocr.ocr(grey_image_file, cls=True)
    for line in result:
        print(line)

    # draw result
    image = Image.open(input_image_file).convert("RGB")
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    print(txts)
    print(scores)
    im_show = draw_ocr(image, boxes, txts, scores=None)
    im_show = Image.fromarray(im_show)
    im_show.save("result.jpg")

import cv2 as cv
import sys
import numpy as np

from damishshah_comic_book_reader import findSpeechBubbles


if __name__ == "__main__":
    input_image_file = sys.argv[1]

    black_mask = cv.imread(input_image_file, -1)
    _, _, _, binary = cv.split(black_mask)
    binary = np.uint8(255 - binary)
    grey = cv.merge([binary, binary, binary])
    cv.imwrite("/tmp/grey.png", grey)

    contours = findSpeechBubbles(grey)
    cv.drawContours(grey, contours, -1, (0, 255, 0), 3)

    cv.imwrite("/tmp/bubbles.png", grey)

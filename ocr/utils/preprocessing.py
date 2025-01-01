import cv2 as cv
import numpy as np
from PIL import Image, ImageEnhance


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Preprocess the input image for better OCR results."""

    pil_image = Image.fromarray(image)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(pil_image)
    sharpened = enhancer.enhance(2.0)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(sharpened)
    contrasted = enhancer.enhance(1.5)

    # Convert back to OpenCV format
    cv_image = np.array(contrasted)

    # Denoise
    denoised = cv.fastNlMeansDenoising(cv_image, None, 10, 7, 21)

    return denoised

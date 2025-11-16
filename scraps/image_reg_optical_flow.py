import cv2
import numpy as np
from skimage.color import rgb2gray
from skimage.registration import optical_flow_tvl1, optical_flow_ilk
from skimage.transform import warp, resize
from skimage.io import imread, imsave

output_image = "/tmp/color-test-01-reg.png"

image0_color = imread(
    "/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/01_upscayl_8400px_digital-art-4x-small-test.png"
)  # Reference image.
# image1_color = imread("/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/gemini-colors-panel 6/color-test.png")  # Image to be aligned.
image1_color_small = imread("/tmp/color-test-01.png")  # Image to be aligned.
imsave("/tmp/junk1.jpg", image1_color_small)

# Manually ensure image1 has only 3 channels (RGB) before resizing to prevent an alpha channel issue.
image1_color = resize(
    image1_color_small,
    image0_color.shape,
    anti_aliasing=False,
)
image1_color = (image1_color * 255).astype(np.uint8)
imsave("/tmp/junk1-1.jpg", image1_color)

# Load your color images (image0, image1)
# For example, using skimage.data:
# from skimage.data import stereo_motorcycle
# image0_color, image1_color, _ = stereo_motorcycle()

# Convert to grayscale
image0_gray = rgb2gray(image0_color)
image1_gray = rgb2gray(image1_color)

# Compute optical flow on grayscale images
v, u = optical_flow_tvl1(image0_gray, image1_gray)
# Or use optical_flow_ilk: v, u = optical_flow_ilk(image0_gray, image1_gray)

# Use the estimated flow for registration on the original color image
nr, nc = image0_color.shape[:2]
row_coords, col_coords = np.meshgrid(np.arange(nr), np.arange(nc), indexing='ij')
warped_image = warp(image1_color, np.array([row_coords + v, col_coords + u]), mode='constant')

# warped_image now contains the registered color image
imsave(output_image, warped_image)

import cv2
import numpy as np

# Open the image files.
#img1_color = cv2.imread("/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/gemini-colors-panel 6/color-test.png")  # Image to be aligned.
img1_color = cv2.imread("/tmp/color-test-01.png")  # Image to be aligned.
img2_color = cv2.imread("/home/greg/Books/Carl Barks/Fantagraphics-censorship-fixes/wdcs-34/01_upscayl_8400px_digital-art-4x-small-test.png")    # Reference image.
#ret, img1_bw = cv2.threshold(img1_color, 190, 255, cv2.THRESH_BINARY)
img1_bw = img1_color

output_image = "/tmp/color-test-01-reg.png"

# Convert to grayscale.
img1 = cv2.cvtColor(img1_bw, cv2.COLOR_BGR2GRAY)
img2 = cv2.cvtColor(img2_color, cv2.COLOR_BGR2GRAY)
height, width = img2.shape
cv2.imwrite("/tmp/bw1.jpg", img1)

# Create ORB detector with 5000 features.
orb_detector = cv2.ORB_create(50000000)

# Find keypoints and descriptors.
# The first arg is the image, second arg is the mask
#  (which is not required in this case).
kp1, d1 = orb_detector.detectAndCompute(img1, None)
kp2, d2 = orb_detector.detectAndCompute(img2, None)

# Match features between the two images.
# We create a Brute Force matcher with
# Hamming distance as measurement mode.
matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck = True)

# Match the two sets of descriptors.
matches = matcher.match(d1, d2)

# Sort matches on the basis of their Hamming distance.
matches = sorted(list(matches), key = lambda x: x.distance)

# Take the top 90 % matches forward.
matches = matches[:int(len(matches)*0.9)]
no_of_matches = len(matches)

# Define empty matrices of shape no_of_matches * 2.
p1 = np.zeros((no_of_matches, 2))
p2 = np.zeros((no_of_matches, 2))

for i in range(len(matches)):
  p1[i, :] = kp1[matches[i].queryIdx].pt
  p2[i, :] = kp2[matches[i].trainIdx].pt

# Find the homography matrix.
homography, mask = cv2.findHomography(p1, p2, cv2.RANSAC, ransacReprojThreshold = 0.01)

# Use this matrix to transform the
# colored image wrt the reference image.
transformed_img = cv2.warpPerspective(img1_color, homography, (width, height))

# Save the output.
cv2.imwrite(output_image, transformed_img)

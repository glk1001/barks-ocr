import sys

import cv2 as cv
import easyocr
import numpy as np
import supervision as sv

from barks_fantagraphics.cv_image_utils import get_bw_image_from_alpha

if __name__ == "__main__":
    input_image_file = sys.argv[1]

    bw_image = get_bw_image_from_alpha(input_image_file)
    image = cv.merge([bw_image, bw_image, bw_image])
    grey_image_file = "/tmp/image_grey.png"
    cv.imwrite(grey_image_file, bw_image)

    reader = easyocr.Reader(["en"], gpu=False)

    # Perform text detection on the image
    result = reader.readtext(grey_image_file)

    # Prepare lists for bounding boxes, confidences, class IDs, and labels
    xyxy, confidences, class_ids, label = [], [], [], []

    # Extract data from OCR result
    for detection in result:
        bbox, text, confidence = detection[0], detection[1], detection[2]

        # Convert bounding box format
        x_min = int(min([point[0] for point in bbox]))
        y_min = int(min([point[1] for point in bbox]))
        x_max = int(max([point[0] for point in bbox]))
        y_max = int(max([point[1] for point in bbox]))

        # Append data to lists
        xyxy.append([x_min, y_min, x_max, y_max])
        label.append(text)
        confidences.append(confidence)
        class_ids.append(0)

        # Convert to NumPy arrays
    detections = sv.Detections(
        xyxy=np.array(xyxy), confidence=np.array(confidences), class_id=np.array(class_ids)
    )
    print(detections)

    # Annotate image with bounding boxes and labels
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()

    annotated_image = box_annotator.annotate(scene=image, detections=detections)
    annotated_image = label_annotator.annotate(
        scene=annotated_image, detections=detections, labels=label
    )

    # Display and save the annotated image
    #    sv.plot_image(image=annotated_image)
    cv.imwrite("/tmp/annotated-output.jpg", annotated_image)

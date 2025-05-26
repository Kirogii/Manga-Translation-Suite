from typing import Tuple
import cv2
import numpy as np

def process_contour(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns the image and an array of bounding boxes detected using contours.
    Each bounding box is in [x1, y1, x2, y2] format.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w * h > 100:
            boxes.append([x, y, x + w, y + h])

    return image, np.array(boxes)

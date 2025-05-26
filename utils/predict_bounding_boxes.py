from typing import List
from ultralytics import YOLO
import numpy as np

def predict_bounding_boxes(model: YOLO, image_array: np.ndarray) -> List:
    """
    Predict bounding boxes for text in an image array using the YOLO model.
    Returns a list of [x1, y1, x2, y2] boxes labeled as 'text'.
    """
    # Set thresholds for detection
    result = model.predict(image_array, verbose=False, iou=0.8, conf=0.25)[0]
    boxes = []

    # Collect initial detections
    detections = []
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        label = result.names[class_id]
        confidence = float(box.conf[0].item())
        if label != "text":
            continue
        coords = box.xyxy[0].tolist()
        x1, y1, x2, y2 = coords
        width = x2 - x1
        height = y2 - y1

        # Filter out tiny boxes
        if width < 5 or height < 5:
            continue
        detections.append(coords)

    # Now filter out boxes that are overly large or contain others
    filtered_boxes = []

    for i, box_a in enumerate(detections):
        x1_a, y1_a, x2_a, y2_a = map(int, box_a)
        area_a = (x2_a - x1_a) * (y2_a - y1_a)

        # Skip very small boxes
        if area_a < 15:
            continue

        # Check if box_a fully contains any other detection with significant size difference
        containers = False
        for j, box_b in enumerate(detections):
            if i == j:
                continue
            x1_b, y1_b, x2_b, y2_b = map(int, box_b)
            area_b = (x2_b - x1_b) * (y2_b - y1_b)

            # Check containment
            if (x1_a <= x1_b and y1_a <= y1_b and x2_a >= x2_b and y2_a >= y2_b):
                # Only consider containment if the container is significantly larger
                if area_a / (area_b + 1e-5) > 2:
                    containers = True
                    break

        # Only keep if not a container of other boxes
        if not containers:
            filtered_boxes.append([x1_a, y1_a, x2_a, y2_a])

    return filtered_boxes

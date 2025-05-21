from typing import List
from ultralytics import YOLO
import numpy as np

def predict_bounding_boxes(model: YOLO, image_array: np.ndarray) -> List:
    """
    Predict bounding boxes for text in an image array using the YOLO model.
    Returns a list of [x1, y1, x2, y2] boxes labeled as 'text'.
    """
    result = model.predict(image_array, verbose=False)[0]

    filtered_boxes = []
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        label = result.names[class_id]

        if label != "text":
            continue

        coords = box.xyxy[0].tolist()
        filtered_boxes.append(coords)

    return filtered_boxes

import uuid
import os
from typing import List
from PIL import Image
from ultralytics import YOLO
def predict_bounding_boxes(model: YOLO, image_path: str) -> List:
    """
    Predict bounding boxes for text in images using the trained Object Detection model.
    Only saves and returns boxes labeled as 'text'.
    """

    image = Image.open(image_path)
    bounding_box_images_path = "./bounding_box_images"

    # Create the directory if it doesn't exist
    if not os.path.exists(bounding_box_images_path):
        os.makedirs(bounding_box_images_path)

    # Clear the directory
    for file in os.listdir(bounding_box_images_path):
        os.remove(os.path.join(bounding_box_images_path, file))

    # Perform inference
    result = model.predict(image_path)[0]

    # Filter only boxes with class "text"
    filtered_boxes = []
    for i, box in enumerate(result.boxes):
        class_id = int(box.cls[0].item())
        label = result.names[class_id]

        if label != "text":
            continue  # Skip non-text detections

        coords = [round(x) for x in box.xyxy[0].tolist()]
        cropped_image = image.crop(coords)
        cropped_image.save(f"{bounding_box_images_path}/{uuid.uuid4()}.png")
        filtered_boxes.append(result.boxes.data[i])  # Get corresponding tensor row

    return [box.tolist() for box in filtered_boxes]

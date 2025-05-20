"""
This module contains the function to return the full image as a bounding box.
"""
from typing import Tuple
import cv2
import numpy as np


def process_contour(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns the full image area as the bounding box.
    Clears the image (sets it to white) and returns the full bounding box.
    """
    h, w = image.shape[:2]
    image[:, :] = (255, 255, 255)  # Clear the image

    # Return full image bounding box as 4-point rectangle
    return image, np.array([[0, 0], [w, 0], [w, h], [0, h]])

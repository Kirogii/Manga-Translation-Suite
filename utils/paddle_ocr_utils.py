from paddleocr import PaddleOCR
import numpy as np
from PIL import Image
import time
from typing import List

class PaddleOCRWrapper:
    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='korean',
            show_log=False
        )
        print("PaddleOCR initialized with downloaded models")

    def get_text_from_image(self, image):
        """For direct OCR without YOLO detection (like old version)"""
        if isinstance(image, Image.Image):
            image = np.array(image)

        start_time = time.time()
        result = self.ocr.ocr(image, cls=True)
        processing_time = time.time() - start_time
        print(f"PaddleOCR processing time: {processing_time:.2f}s")

        if not result or not result[0]:
            return ""

        texts = []
        for line in result[0]:
            box, (text, confidence) = line
            if confidence > 0.5:
                texts.append(text)
        
        combined_text = "\n".join(texts)
        print(f"PaddleOCR result: {combined_text}")
        return combined_text

    def get_text_with_boxes(self, image, yolo_boxes: List[List[int]]):
        """
        Process image with YOLO boxes (like old version)
        Args:
            image: PIL Image or numpy array
            yolo_boxes: List of [x1, y1, x2, y2] boxes from YOLO
        Returns:
            List of dicts with text and box info
        """
        if isinstance(image, Image.Image):
            image = np.array(image)

        results = []
        for box in yolo_boxes:
            x1, y1, x2, y2 = map(int, box[:4])
            cropped = image[y1:y2, x1:x2]
            
            # Get OCR results for this cropped region
            ocr_result = self.ocr.ocr(cropped, cls=True)
            
            if not ocr_result or not ocr_result[0]:
                continue
                
            # Combine texts in this region
            texts = []
            for line in ocr_result[0]:
                box_points, (text, confidence) = line
                if confidence > 0.5:
                    texts.append(text)
            
            if texts:
                combined_text = " ".join(texts)
                results.append({
                    'box': [x1, y1, x2, y2],
                    'text': combined_text
                })
        
        return results

# Global instance
paddle_ocr = PaddleOCRWrapper()
from manga_ocr import MangaOcr
from .paddle_ocr_utils import paddle_ocr

# Global instances
mocr = MangaOcr()

def get_text_from_image(image, use_paddle=False):
    """Extract text using the selected OCR method"""
    try:
        if use_paddle:
            if isinstance(image, Image.Image):
                image = np.array(image)
            result = paddle_ocr.get_text_from_image(image)
        else:
            result = mocr(image)
        
        print(f"[OCR] {'Paddle' if use_paddle else 'Manga'} result: {result}")
        return result
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return None
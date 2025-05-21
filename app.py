import os
import io
import base64
from typing import Dict, Any
import requests

import numpy as np
from fastapi import FastAPI, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from PIL import Image
import uvicorn
from ultralytics import YOLO

from utils.predict_bounding_boxes import predict_bounding_boxes
from utils.manga_ocr_utils import get_text_from_image
from utils.translate_manga import translate_manga
from utils.process_contour import process_contour
from utils.write_text_on_image import add_text

# Constants
MODEL_URL = "https://huggingface.co/deepghs/manga109_yolo/resolve/main/v2023.12.07_x/model.pt?download=true"
MODEL_DIR = "./models"
MODEL_PATH = os.path.join(MODEL_DIR, "model.pt")

# Download model if not present
def download_model_if_missing():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading model from {MODEL_URL} ...")
        response = requests.get(MODEL_URL, stream=True)
        response.raise_for_status()
        with open(MODEL_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Model downloaded successfully.")

download_model_if_missing()

# Load model
object_detection_model = YOLO(MODEL_PATH)

# FastAPI setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")
templates = Jinja2Templates(directory="templates")

# Utilities
def decode_base64_image(encoded_image: str) -> Image.Image:
    decoded_bytes = base64.b64decode(encoded_image)
    image = Image.open(io.BytesIO(decoded_bytes))
    return image.convert("RGB")

def convert_image_to_base64(image: Image.Image) -> str:
    buff = io.BytesIO()
    image.save(buff, format="PNG")
    return base64.b64encode(buff.getvalue()).decode("utf-8")

# Routes
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict")
def predict(request: Dict[str, Any]):
    try:
        image = decode_base64_image(request["image"])
        np_image = np.array(image)

        results = predict_bounding_boxes(object_detection_model, np_image)

        image_info = []
        for box in results:
            x1, y1, x2, y2 = map(int, box[:4])
            cropped = np_image[y1:y2, x1:x2]
            pil_crop = Image.fromarray(cropped)
            text = get_text_from_image(pil_crop)
            translation = translate_manga(text)
            image_info.append({
                "box": [x1, y1, x2, y2],
                "text": text,
                "translation": translation
            })

        return {"status": "ok", "regions": image_info}

    except Exception as e:
        print("Error:", e)
        return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})

@app.post("/predict_url")
def predict_url(request: Dict[str, Any] = Body(...)):
    try:
        image_url = request.get("image_url")
        if not image_url:
            return JSONResponse(status_code=400, content={"code": 400, "message": "Missing image_url"})

        headers = {
            "User-Agent": "Mozilla/5.0",  # some sites block scripts without this
            "Referer": image_url
        }
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()

        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        np_image = np.array(image)

        results = predict_bounding_boxes(object_detection_model, np_image)

        image_info = []
        for box in results:
            x1, y1, x2, y2 = map(int, box[:4])
            cropped = np_image[y1:y2, x1:x2]
            pil_crop = Image.fromarray(cropped)
            text = get_text_from_image(pil_crop)
            translation = translate_manga(text)
            image_info.append({
                "box": [x1, y1, x2, y2],
                "text": text,
                "translation": translation
            })

        return {"status": "ok", "regions": image_info}

    except Exception as e:
        print("Error processing URL:", e)
        return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})

# Run server
if __name__ == "__main__":
    uvicorn.run("app:app", host="localhost", port=8000, reload=False)

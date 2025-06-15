import os
import io
import json
import base64
import socket
import threading
import requests
import numpy as np
import pygame
import time
from collections import deque
from datetime import datetime, timedelta
from PIL import Image
from fastapi import FastAPI, Request, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, StreamingResponse
from ultralytics import YOLO
from utils.predict_bounding_boxes import predict_bounding_boxes
from utils.manga_ocr_utils import get_text_from_image
from utils.translate_manga import translate_manga
from utils import translate_manga as tm
from utils.paddle_ocr_utils import PaddleOCRWrapper
from utils.paddle_ocr_utils import paddle_ocr
from TTS.api import TTS
from TTS.tts.utils.text.tokenizer import TTSTokenizer
import tempfile
import shutil
import subprocess
import psutil
import torch  # Import torch

# Constants
MODEL_URL = "https://huggingface.co/Kirogii/Yolo-Manga_Textbox-Region_Detect/resolve/main/model.pt?download=true"
MODEL_DIR = "./models"
MODEL_PATH = os.path.join(MODEL_DIR, "model.pt")

IP_WHITELIST_FILE = "ip_whitelist.json"
BLOCKED_IPS_FILE = "blocked_ips.json"
DENY_DURATION = 10  # seconds
RATE_LIMIT = 30
RATE_WINDOW_MINUTES = 3
TEMP_BLOCK_DURATION = 3600  # seconds

# State
ip_whitelist = {}
deny_cache = {}
REQUEST_HISTORY = {}
TEMP_BLOCKED_IPS = {}
PERM_BLOCKED_IPS = set()
ocr_model_in_use = 'default'  # global state for OCR model

# Load IP whitelist
if os.path.exists(IP_WHITELIST_FILE):
    try:
        with open(IP_WHITELIST_FILE, "r") as f:
            content = f.read().strip()
            if content:
                ip_whitelist = json.loads(content)
    except Exception as e:
        print(f"Warning: Could not load IP whitelist. Reason: {e}")

# Load permanent blocks
if os.path.exists(BLOCKED_IPS_FILE):
    try:
        with open(BLOCKED_IPS_FILE, "r") as f:
            PERM_BLOCKED_IPS = set(json.load(f))
    except Exception as e:
        print(f"Warning: Could not load blocked IPs. Reason: {e}")

def save_ip_whitelist():
    with open(IP_WHITELIST_FILE, "w") as f:
        json.dump(ip_whitelist, f, indent=4)

def save_blocked_ips():
    with open(BLOCKED_IPS_FILE, "w") as f:
        json.dump(list(PERM_BLOCKED_IPS), f, indent=4)

def is_temporarily_denied(ip: str) -> bool:
    now = time.time()
    return ip in deny_cache and now < deny_cache[ip]

def confirm_ip(ip: str) -> bool:
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except Exception:
        hostname = "Unknown"

    decision_event = threading.Event()
    decision_result = {"allow": False, "decision_made": False}

    def popup():
        pygame.init()
        screen = pygame.display.set_mode((500, 250))
        pygame.display.set_caption("IP Confirmation")
        font = pygame.font.SysFont(None, 24)
        big_font = pygame.font.SysFont(None, 32)
        white = (255, 255, 255)
        black = (0, 0, 0)
        green = (0, 200, 0)
        red = (200, 0, 0)

        def draw_button(text, rect, color):
            pygame.draw.rect(screen, color, rect)
            label = font.render(text, True, white)
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)

        running = True
        while running:
            screen.fill(white)
            screen.blit(big_font.render("New Request from IP", True, black), (150, 30))
            screen.blit(font.render(f"IP: {ip}", True, black), (50, 80))
            screen.blit(font.render(f"Device: {hostname}", True, black), (50, 110))

            allow_btn = pygame.Rect(100, 160, 120, 40)
            deny_btn = pygame.Rect(280, 160, 120, 40)

            draw_button("Allow (Y)", allow_btn, green)
            draw_button("Deny Once (X)", deny_btn, red)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if allow_btn.collidepoint(event.pos):
                        decision_result["allow"] = True
                        decision_result["decision_made"] = True
                        running = False
                    elif deny_btn.collidepoint(event.pos):
                        decision_result["allow"] = False
                        decision_result["decision_made"] = True
                        running = False

        pygame.quit()
        decision_event.set()

    popup_thread = threading.Thread(target=popup)
    popup_thread.start()
    decision_event.wait()

    if decision_result["decision_made"]:
        if decision_result["allow"]:
            ip_whitelist[ip] = hostname
            save_ip_whitelist()
            print(f"Allowed IP {ip} ({hostname}) permanently.")
            return True
        else:
            print(f"Temporarily denied IP {ip}.")
            return False
    else:
        print("No decision made; denying by default.")
        return False

async def check_ip_safety(request: Request):
    body = await request.body()
    try:
        data = json.loads(body)
        ip = data.get("client_ip", request.client.host)
    except Exception:
        ip = request.client.host

    now = datetime.now()

    if ip in PERM_BLOCKED_IPS:
        print(f"Permanently blocked IP {ip} attempted access. Shutting down.")
        os._exit(1)

    if ip in TEMP_BLOCKED_IPS and now < TEMP_BLOCKED_IPS[ip]:
        raise HTTPException(status_code=403, detail="Temporarily rate limited")

    history = REQUEST_HISTORY.setdefault(ip, deque())
    history.append(now)
    cutoff = now - timedelta(minutes=RATE_WINDOW_MINUTES)
    while history and history[0] < cutoff:
        history.popleft()

    if len(history) >= RATE_LIMIT and ip not in ip_whitelist:
        if ip in TEMP_BLOCKED_IPS:
            PERM_BLOCKED_IPS.add(ip)
            save_blocked_ips()
            print(f"IP {ip} permanently blocked.")
            raise HTTPException(status_code=403, detail="Permanently blocked")
        else:
            TEMP_BLOCKED_IPS[ip] = now + timedelta(seconds=TEMP_BLOCK_DURATION)
            print(f"IP {ip} temporarily rate limited.")
            raise HTTPException(status_code=403, detail="Temporarily rate limited")

    if is_temporarily_denied(ip):
        raise HTTPException(status_code=403, detail="Access temporarily denied")

    if ip in ip_whitelist:
        return True

    if not confirm_ip(ip):
        deny_cache[ip] = time.time() + DENY_DURATION
        raise HTTPException(status_code=403, detail="Access denied")

# Download model if missing
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
object_detection_model = YOLO(MODEL_PATH)

# --- TTS Model Auto-Download/Initialization ---
tts_models = {
    'en': 'tts_models/en/vctk/vits',
    'ja': 'tts_models/ja/kokoro/tacotron2-DDC'
}
tts_instances = {}

def ensure_tts_model_downloaded(model_name):
    """
    Ensure the TTS model is downloaded and available locally.
    """
    try:
        # This will trigger download if not present
        TTS(model_name)
        print(f"TTS model {model_name} is ready.")
    except Exception as e:
        print(f"Error ensuring TTS model download: {e}")

# Download TTS models on first launch
for tts_model in tts_models.values():
    ensure_tts_model_downloaded(tts_model)

# Initialize Japanese tokenizer at startup
try:
    tokenizer = TTSTokenizer("ja")
    print("Japanese tokenizer loaded!")
except Exception as e:
    print(f"Failed to load Japanese tokenizer: {e}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def decode_base64_image(encoded_image: str) -> Image.Image:
    decoded_bytes = base64.b64decode(encoded_image)
    image = Image.open(io.BytesIO(decoded_bytes))
    return image.convert("RGB")

def convert_image_to_base64(image: Image.Image) -> str:
    buff = io.BytesIO()
    image.save(buff, format="PNG")
    return base64.b64encode(buff.getvalue()).decode("utf-8")


# import torch  # Moved import to the top

def get_tts_instance(lang):
    if lang not in tts_models:
        raise ValueError(f"Unsupported language: {lang}")
    if lang not in tts_instances:
        use_cuda = torch.cuda.is_available()

        tts = TTS(
            model_name=tts_models[lang],
            progress_bar=False,
            gpu=use_cuda,
        )

        if hasattr(tts, "config") and tts.config is not None:
            cfg = tts.config
            cfg.use_cuda = use_cuda
            cfg.audio.do_trim_silence = True
            cfg.audio.trim_db = 50
            cfg.audio.signal_norm = True
            cfg.audio.symmetric_norm = True
            cfg.audio.max_norm = 4.0
            cfg.audio.clip_norm = True

        if hasattr(tts, "vocoder_config") and tts.vocoder_config is not None:
            vc = tts.vocoder_config
            vc.dither = 0.0
            vc.noise_scale = 0.33
            vc.length_scale = 0.8  # Balanced between speed and quality
            vc.inference_noise_scale = 0.33
            vc.inference_length_scale = 0.8
            vc.pad_short = 10

        tts_instances[lang] = tts
    return tts_instances[lang]


# OCR model registry
ocr_models = [
    {"id": "default", "name": "YOLO + manga_ocr", "ram": "2GB", "type": "yolo"},
    {"id": "hal-utokyo/MangaLMM", "name": "MangaLMM (HuggingFace)", "ram": "10-15GB", "type": "huggingface"},
    {"id": "paddle", "name": "PaddleOCR (Korean)", "ram": "1-2GB", "type": "paddle"}
]

def add_huggingface_ocr_model(model_id, name, ram="10-15GB"):
    global ocr_models
    if not any(m["id"] == model_id for m in ocr_models):
        ocr_models = ( [{"id": model_id, "name": name, "ram": ram, "type": "huggingface"}] +
                      [m for m in ocr_models if m["type"] != "huggingface"] +
                      [m for m in ocr_models if m["type"] == "huggingface" and m["id"] != model_id])

@app.post("/add_ocr_model")
def add_ocr_model(request_body: dict = Body(...)):
    model_id = request_body.get("id")
    name = request_body.get("name")
    ram = request_body.get("ram", "10-15GB")
    if not model_id or not name:
        return JSONResponse(status_code=400, content={"error": "Missing id or name"})
    add_huggingface_ocr_model(model_id, name, ram)
    return {"status": "ok", "ocr_models": ocr_models}

import time





@app.post("/predict")
def predict(request_body: dict = Body(...), _: bool = Depends(check_ip_safety)):
    start_total = time.time()
    try:
        # Decode image
        start_decode = time.time()
        image = decode_base64_image(request_body["image"])
        np_image = np.array(image)
        print(f"Decode + convert to array: {time.time() - start_decode:.2f}s")

        # Detect text regions with YOLO
        start_detection = time.time()
        results = predict_bounding_boxes(object_detection_model, np_image)
        print(f"Object detection: {time.time() - start_detection:.2f}s")

        image_info = []
        for box in results:
            x1, y1, x2, y2 = map(int, box[:4])
            cropped = np_image[y1:y2, x1:x2]
            pil_crop = Image.fromarray(cropped)
            start_ocr = time.time()

            # Handle different OCR methods
            if ocr_model_in_use == 'paddle':
                # Use PaddleOCR's box-specific processing
                ocr_result = paddle_ocr.get_text_with_boxes(np_image, [box])
                if ocr_result:  # If we got results for this box
                    text = ocr_result[0]['text']
                else:
                    text = ""
            elif ocr_model_in_use == 'hal-utokyo/MangaLMM':
                text, _ = translate_mangalmm(pil_crop)
            else:  # default manga_ocr
                text = get_text_from_image(pil_crop, use_paddle=False)

            print(f"OCR time: {time.time() - start_ocr:.2f}s")
            
            # Translate the text
            start_translate = time.time()
            translation = translate_manga(text)
            print(f"Translation time: {time.time() - start_translate:.2f}s")
            
            image_info.append({
                "box": [x1, y1, x2, y2],
                "text": text,
                "translation": translation,
                "original_text": text
            })

        print(f"Total request time: {time.time() - start_total:.2f}s")
        return {"status": "ok", "regions": image_info}
    except Exception as e:
        print("Error:", e)
        return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})












@app.get("/list_ocrmodels")
def list_ocrmodels():
    return {"ocr_models": [[m["id"], f'{m["name"]} ({m["ram"]})'] for m in ocr_models]}

@app.get("/current_ocrmodel")
def current_ocrmodel():
    return {"current_ocr_model": ocr_model_in_use}

@app.post("/set_ocr_method")
def set_ocr_method(request_body: dict = Body(...)):
    method = request_body.get("method", "manga")
    if method not in ["manga", "paddle"]:
        return JSONResponse(status_code=400, content={"error": "Invalid method"})
    
    from utils.manga_ocr_utils import set_ocr_method
    set_ocr_method(method)
    return {"status": "ok", "method": method}

# In app.py, add this endpoint (around line 500 where other OCR endpoints are)
@app.post("/set_ocr_model")
def set_ocr_model(request_body: dict = Body(...)):
    global ocr_model_in_use
    model_id = request_body.get("ocr_model")
    if not model_id:
        return JSONResponse(status_code=400, content={"error": "Missing ocr_model parameter"})
    
    # Validate the model exists
    if not any(m["id"] == model_id for m in ocr_models):
        return JSONResponse(status_code=400, content={"error": "Invalid OCR model specified"})
    
    ocr_model_in_use = model_id
    print(f"OCR model changed to: {ocr_model_in_use}")
    return {"status": "ok", "current_ocr_model": ocr_model_in_use}

@app.get("/available_ocr_methods")
def get_ocr_methods():
    return {"methods": ["manga", "paddle"]}

@app.post("/predict_url")
async def predict_url(request_body: dict = Body(...), _: bool = Depends(check_ip_safety)):
    try:
        # Validate input
        if not request_body or not isinstance(request_body, dict):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid request body"}
            )

        # Check for both image_url and direct image data
        image_url = request_body.get("image_url")
        image_data = request_body.get("image")
        
        if not image_url and not image_data:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing image_url or image data"}
            )

        # Process base64 image data if provided
        if image_data:
            try:
                # Ensure the base64 string is clean (remove data URI prefix if present)
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                np_image = np.array(image)
                print(f"Image loaded from base64 data. Dimensions: {np_image.shape}")
            except Exception as img_error:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": f"Invalid image data: {str(img_error)}"}
                )
        else:
            # Process image URL if provided
            print(f"Processing image URL: {image_url}")
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": image_url.split('?')[0] if image_url else ""
            }
            
            try:
                response = requests.get(image_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                if not response.content:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "error", "message": "Empty image content"}
                    )
                    
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
                np_image = np.array(image)
                print(f"Image loaded successfully. Dimensions: {np_image.shape}")
            except requests.exceptions.RequestException as req_error:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": f"Failed to download image: {str(req_error)}"}
                )
            except Exception as img_error:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": f"Invalid image format: {str(img_error)}"}
                )

        # Process with selected OCR method
        try:
            start_detection = time.time()
            results = predict_bounding_boxes(object_detection_model, np_image)
            print(f"Object detection: {time.time() - start_detection:.2f}s")

            image_info = []
            for box in results:
                x1, y1, x2, y2 = map(int, box[:4])
                cropped = np_image[y1:y2, x1:x2]
                pil_crop = Image.fromarray(cropped)
                start_ocr = time.time()

                # Handle different OCR methods
                if ocr_model_in_use == 'paddle':
                    # Use PaddleOCR for text recognition only (after YOLO detection)
                    text = paddle_ocr.get_text_from_image(cropped)
                elif ocr_model_in_use == 'hal-utokyo/MangaLMM':
                    text, _ = translate_mangalmm(pil_crop)
                else:  # default manga_ocr
                    text = get_text_from_image(pil_crop, use_paddle=False)

                print(f"OCR time: {time.time() - start_ocr:.2f}s")
                
                # Translate the text
                start_translate = time.time()
                translation = translate_manga(text)
                print(f"Translation time: {time.time() - start_translate:.2f}s")
                
                image_info.append({
                    "box": [x1, y1, x2, y2],
                    "text": translation,
                    "translation": translation,
                    "original_text": text
                })

            return {
                "status": "ok",
                "regions": image_info,
                "ocr_model": ocr_model_in_use
            }

        except Exception as processing_error:
            print(f"Error during OCR processing: {str(processing_error)}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"OCR processing error: {str(processing_error)}",
                    "ocr_model": ocr_model_in_use
                }
            )

    except Exception as e:
        print(f"Unexpected error in predict_url: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Unexpected server error: {str(e)}",
                "type": type(e).__name__
            }
        )

@app.get("/ocr_model_info")
def get_ocr_model_info():
    """Get detailed information about available OCR models"""
    models_info = []
    for model in ocr_models:
        model_info = {
            "id": model["id"],
            "name": model["name"],
            "ram": model["ram"],
            "type": model["type"],
            "description": ""
        }
        if model["id"] == "paddle":
            model_info["description"] = "PaddleOCR optimized for Korean text recognition"
        elif model["id"] == "default":
            model_info["description"] = "Default manga_ocr for general Japanese/English text"
        elif model["id"] == "hal-utokyo/MangaLMM":
            model_info["description"] = "Large multimodal model for manga text recognition"
        
        models_info.append(model_info)
    
    return {"models": models_info}


@app.post("/set_aimodel")
def set_aimodel(request_body: dict = Body(...)):
    model_name = request_body.get("model")
    try:
        tm.set_current_model(model_name)
        print(f"Model switched to: {model_name}")
        return {"status": "ok", "current_model": tm.get_current_model()}
    except Exception as e:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})

@app.get("/list_aimodels")
def list_aimodels():
    return {"models": tm.get_available_models()}

@app.get("/current_aimodel")
def current_aimodel():
    return {"current_model": tm.get_current_model()}

@app.get("/get_api_endpoint")
def get_api_endpoint():
    return {
        "endpoint": "http://localhost:8000",
        "models": tm.get_available_models()
    }

@app.post("/tts_get")
def tts_get(request: dict = Body(...)):
    text = request.get("text", "")
    lang = request.get("lang", "ja")
    if not text:
        return JSONResponse({"error": "No text provided"}, status_code=400)
    try:
        tts = get_tts_instance(lang)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tts.tts_to_file(text=text, file_path=f.name)
            f.seek(0)
            wav_data = f.read()
        return StreamingResponse(io.BytesIO(wav_data), media_type="audio/wav")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="localhost", port=8000, reload=False)
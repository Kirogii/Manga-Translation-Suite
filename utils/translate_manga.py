"""
This module is used to translate manga from one language to another.
"""

import os
import subprocess
import torch
import json
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, MarianMTModel, MarianTokenizer
except ImportError:
    subprocess.check_call([os.sys.executable, "-m", "pip", "install", "transformers", "sentencepiece"])
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, MarianMTModel, MarianTokenizer

# Constants
DEFAULT_MODEL = "cyy0/JaptoEnBetterMTL-2"
AI_MODELS_PATH = os.path.join(os.path.dirname(__file__), 'AiModels.json')
TRANSFORMERS_CACHE = os.environ.get('HF_HOME') or os.environ.get('TRANSFORMERS_CACHE') or os.path.expanduser('~/.cache/huggingface/hub')

# Global state
_model_cache: Dict[str, Tuple[any, any]] = {}  # Cache of loaded models and tokenizers
_current_model_name: str = DEFAULT_MODEL
_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_ai_models() -> List[List[str]]:
    """Load or create AiModels.json"""
    default_models = [
        ["cyy0/JaptoEnBetterMTL-2", "2GB"],
        ["Helsinki-NLP/opus-mt-ja-en", "1.2GB"],
        ["facebook/m2m100_1.2B", "6-12GB"],
        ["tunib/electra-ko-en-base", "500MB-1GB"]
    ]
    
    if not os.path.exists(AI_MODELS_PATH):
        with open(AI_MODELS_PATH, 'w', encoding='utf-8') as f:
            json.dump({"models": default_models}, f, indent=2)
        return default_models
    
    try:
        with open(AI_MODELS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("models", default_models)
    except Exception as e:
        print(f"Error loading AiModels.json: {e}")
        return default_models

def save_ai_models(models: List[List[str]]) -> None:
    """Save models to JSON"""
    try:
        with open(AI_MODELS_PATH, 'w', encoding='utf-8') as f:
            json.dump({"models": models}, f, indent=2)
    except Exception as e:
        print(f"Error saving AiModels.json: {e}")

def add_ai_model(model_id: str, ram_usage: str) -> List[List[str]]:
    """Add a new model to the list"""
    models = load_ai_models()
    if not any(model[0] == model_id for model in models):
        models.append([model_id, ram_usage])
        save_ai_models(models)
    return models

def load_model(model_name: str) -> bool:
    """Load model and tokenizer"""
    global _model_cache, _current_model_name
    
    if model_name in _model_cache:
        print(f"Using cached model: {model_name}")
        return True
        
    print(f"Loading model: {model_name}")
    try:
        # Try AutoTokenizer/Model first
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(_DEVICE)
        except:
            # Fallback to MarianMT
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name).to(_DEVICE)
        
        model.eval()
        _model_cache[model_name] = (tokenizer, model)
        _current_model_name = model_name
        print(f"Successfully loaded model: {model_name} on device: {_DEVICE}")
        return True
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")
        return False

# Initialize available models
AVAILABLE_MODELS = load_ai_models()

# Ensure default model is loaded
if not load_model(_current_model_name):
    print(f"Warning: Failed to load default model {_current_model_name}")

def get_available_models() -> List[List[str]]:
    """Get list of available models"""
    return AVAILABLE_MODELS

def get_current_model() -> str:
    """Get current model name"""
    return _current_model_name

def set_current_model(model_name: str) -> bool:
    """Set and load a new model"""
    global _current_model_name
    if model_name not in [m[0] for m in AVAILABLE_MODELS]:
        raise ValueError(f"Model {model_name} not in available models")
    
    # Only reload if different model
    if model_name != _current_model_name:
        if not load_model(model_name):
            return False
    _current_model_name = model_name  # <- Ensure update even when cached

def translate_manga(text: str, source_lang: str = "", target_lang: str = "en") -> str:
    """Translate manga text from Japanese to English using the current model."""
    if not text or not text.strip():
        return ""

    if _current_model_name not in _model_cache:
        if not load_model(_current_model_name):
            print(f"Error: Failed to load model {_current_model_name}")
            return text

    tokenizer, model = _model_cache[_current_model_name]
    print(f"Using model {_current_model_name} for translation")
    print(f"Original text: {text}")

    try:
        # M2M100-style multilingual models
        if "electra-ko-en-base" in _current_model_name.lower():
            tokenizer.src_lang = "ko"
            encoded = tokenizer(text, return_tensors="pt").to(_DEVICE)
            with torch.no_grad():
                output = model.generate(
                    **encoded,
                    forced_bos_token_id=tokenizer.get_lang_id("en"),
                    max_length=256,
                    num_beams=8,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    length_penalty=1.2,
                    repetition_penalty=2.5
                )
            translated_text = tokenizer.decode(output[0], skip_special_tokens=True)

        # MarianMT-style models
        else:
            encoded = tokenizer([text], return_tensors="pt", truncation=True, padding=True).to(_DEVICE)
            with torch.no_grad():
                output = model.generate(
                    **encoded,
                    max_length=256,
                    num_beams=8,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    length_penalty=1.2,
                    repetition_penalty=2.5
                )
            translated_text = tokenizer.decode(output[0], skip_special_tokens=True)

        print(f"Translated text: {translated_text}")
        return translated_text.strip() or text

    except Exception as e:
        print(f"Translation error: {e}")
        return text

def translate_mangalmm(image: 'PIL.Image.Image') -> Tuple[str, str]:
    try:
        from transformers import AutoTokenizer, CLIPImageProcessor, AutoModelForVision2Seq
        import torch, subprocess, psutil, tempfile

        model_id = "hal-utokyo/MangaLMM"
        global mangalmm_tokenizer, mangalmm_image_processor, mangalmm_model

        device_map = "auto"
        torch_dtype = torch.float16
        use_cpu = False
        use_4bit = False
        max_memory = None

        try:
            import bitsandbytes as bnb
            use_4bit = True
        except ImportError:
            pass

        gpu_ram_mb = 0
        try:
            if torch.cuda.is_available():
                result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                                        capture_output=True, text=True, check=True)
                gpu_rams = [int(x.strip()) for x in result.stdout.strip().split('\n') if x.strip().isdigit()]
                gpu_ram_mb = max(gpu_rams) if gpu_rams else 0
                total_ram_gb = psutil.virtual_memory().total // (1024 ** 3)
                cpu_mem = max(12, total_ram_gb - 2)
                if gpu_ram_mb <= 4096:
                    max_memory = {0: "3000MB", "cpu": f"{cpu_mem}GB"}
                elif gpu_ram_mb <= 6144:
                    max_memory = {0: "5000MB", "cpu": f"{cpu_mem}GB"}
                elif gpu_ram_mb <= 12288:
                    max_memory = {0: "10000MB", "cpu": f"{cpu_mem}GB"}
                elif gpu_ram_mb >= 30000:
                    device_map = {"": 0}
                    max_memory = {0: f"{gpu_ram_mb}MB"}
                else:
                    use_mb = int(gpu_ram_mb * 0.8)
                    max_memory = {0: f"{use_mb}MB", "cpu": f"{cpu_mem}GB"}
            else:
                use_cpu = True
        except:
            use_cpu = True

        if use_cpu:
            device_map = {"": "cpu"}
            torch_dtype = torch.float32
            use_4bit = False
            max_memory = {"cpu": "14GB"}

        if 'mangalmm_tokenizer' not in globals():
            mangalmm_tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        if 'mangalmm_image_processor' not in globals():
            mangalmm_image_processor = CLIPImageProcessor.from_pretrained(model_id, trust_remote_code=True)
        if 'mangalmm_model' not in globals():
            model_kwargs = dict(torch_dtype=torch_dtype, device_map=device_map, trust_remote_code=True)
            if max_memory: model_kwargs["max_memory"] = max_memory
            if psutil.virtual_memory().total // (1024 ** 3) <= 18:
                model_kwargs["low_cpu_mem_usage"] = True
                model_kwargs["offload_folder"] = tempfile.mkdtemp(prefix="mangalmm_offload_")
            if use_4bit:
                from transformers import BitsAndBytesConfig
                quant_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                                                  llm_int8_enable_fp32_cpu_offload=True)
                model_kwargs["quantization_config"] = quant_config
                if device_map == "auto":
                    model_kwargs["device_map"] = {"": 0, "lm_head": "cpu"}
            mangalmm_model = AutoModelForVision2Seq.from_pretrained(model_id, **model_kwargs)
            mangalmm_model.eval()

        prompt = "<image>\nOcr the text in this image."
        image_inputs = mangalmm_image_processor(images=image, return_tensors="pt")
        text_inputs = mangalmm_tokenizer(prompt, return_tensors="pt")
        inputs = {**image_inputs, **text_inputs}
        for k, v in inputs.items():
            if hasattr(v, 'to'):
                inputs[k] = v.to(mangalmm_model.device, dtype=torch.long if k in ["input_ids", "attention_mask"] else torch_dtype)
        with torch.inference_mode():
            generated_ids = mangalmm_model.generate(**inputs, max_new_tokens=64, num_beams=1, do_sample=False)
        result = mangalmm_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return result.strip(), None
    except Exception as e:
        return "", str(e)

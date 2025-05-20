"""
This module is used to translate manga from one language to another.
"""

import os
import subprocess
import torch

try:
    from transformers import MarianMTModel, MarianTokenizer
except ImportError:
    subprocess.check_call([os.sys.executable, "-m", "pip", "install", "transformers", "sentencepiece"])
    from transformers import MarianMTModel, MarianTokenizer


def translate_manga(text: str, source_lang: str = "ja", target_lang: str = "en") -> str:
    """
    Translate manga from one language to another using OPUS model from Hugging Face.
    Uses CUDA if available.
    """

    if source_lang == target_lang:
        return text

    model_name = "Helsinki-NLP/opus-mt-ja-en"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name).to(device)

    print("Original text:", text)

    inputs = tokenizer(text, return_tensors="pt", truncation=True).to(device)
    translated = model.generate(**inputs)
    translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)

    print("Translated text:", translated_text)

    return translated_text

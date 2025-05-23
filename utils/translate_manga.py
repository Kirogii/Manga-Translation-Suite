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

# Constants
MODEL_NAME = "cyy0/JaptoEnBetterMTL-2"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Loading translation model on device: {DEVICE}")

# Load tokenizer and model once
tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
model = MarianMTModel.from_pretrained(MODEL_NAME).to(DEVICE)
model.eval()

# Translation function
def translate_manga(text: str, source_lang: str = "ja", target_lang: str = "en") -> str:
    """
    Translate manga from one language to another using OPUS model from Hugging Face.
    Uses CUDA if available.
    """
    if not text.strip():
        return ""

    if source_lang == target_lang:
        return text
    print("Original text:", text)
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True).to(DEVICE)
    with torch.no_grad():
        translated = model.generate(
            **inputs,
            max_length=256,                # Increase from 128 → 256 (better for long sentences)
            num_beams=8,                   # Increase from 5 → 8 (better beam search = better quality)
            early_stopping=True,
             no_repeat_ngram_size=3,       # Increase to 3 to reduce repetition
            length_penalty=1.2,           # Encourage longer, fuller translations
            repetition_penalty=2.5        # Stronger penalty against repeated phrases
        )
    translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)

    print("Translated text:", translated_text)

    return translated_text

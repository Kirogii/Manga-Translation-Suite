# Manga-Translation-Suite
Based on the sourcecode from https://github.com/Detopall/manga-translator/tree/main
- [Installation](#installation)
- [Information](#information)
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________




## Installation

Install python 3.11 (Unsure if other versions are supported)
https://www.python.org/downloads/release/python-3110/

After installing python run one of the commands:

If you want to use the cpu: (Do this if unsure)
```
pip install -r requirementscpu.txt

```
If you have a gpu supporting cuda then run: (Recommended for speed)
```
pip install -r requirementscuda.txt

```

_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________

## Information

How to change models (You might need to edit code for some models that dont use the tokenizer)
[huggingface.co]

- 1: Goto Utils Folders>translate_manga.py
- 2: Edit line 25 [model_name = "Helsinki-NLP/opus-mt-ja-en"] and change [*"Helsinki-NLP/opus-mt-ja-en"*] to any huggingface model identifier
- 3: Done

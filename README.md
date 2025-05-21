# Manga-Translation-Suite
Based on the sourcecode from https://github.com/Detopall/manga-translator/tree/main
- [Installation](#installation)
- [Information](#information)
- [Credits](#credits)
- IMPORTANT NOTE: When translating dont scroll down and stay at the top of the page until its finished theres a indicator on the top right corner it disappears after its done
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________




## Installation
Click on the main page
Code>Download Zip

- Install python 3.11 (Unsure if other versions are supported)
https://www.python.org/downloads/release/python-3110/

# After installing python run one of the commands:

- If you want to use the cpu: (Do this if unsure)
```
pip install -r requirementscpu.txt

```
- If you have a gpu supporting cuda: (Recommended for speed)
```
pip install -r requirementscuda.txt

```
# Install the extension to chrome from the folder
-  goto ```chrome://extensions``` webpage
-  click the developer mode switch and turn it to blue
-  click "load unpacked extension"
-  select the extension from the zip we downloaded earlier

You should be done by this point now click the extension icon whenever you want to start translation/ocr-ing

_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________

## Information

How to change models (You might need to edit code for some models that dont use the tokenizer)
[huggingface.co]

- 1: Goto Utils Folders>translate_manga.py
- 2: Edit line 25 [model_name = "Helsinki-NLP/opus-mt-ja-en"] and change [*"Helsinki-NLP/opus-mt-ja-en"*] to any huggingface model identifier
- 3: Save then you are Done :)

_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________

## Credits
[https://huggingface.co/deepghs/manga109_yolo] Box Model for identifying text
[https://github.com/Detopall/manga-translator/tree/main] Original sourcecode used as a base
[https://huggingface.co/kha-white/manga-ocr-base] Ocr used for text detection
[https://chatgpt.com] For all code edits


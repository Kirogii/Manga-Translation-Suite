# Manga-Translation-Suite
Based on the sourcecode from https://github.com/Detopall/manga-translator/tree/main
- [Installation](#installation)
- [Information](#information)
- [Credits](#credits)
- [Translations](#translations)
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

_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________


## Translations
and no i will not provide the source image because of copyright

Original text: 近くにナルシーナって街があるから案内するよそこで今後のことを決めるといい
Translated text: there's a town in the neighborhood called Narcina, so I'll show you where you can choose what will follow.
DeepL Translated: There's a town nearby called Narcina, and I'll show you around and you can decide what you want to do.

Original text: しまった．．．少しは持って来ればよかった
Translated text: oh, no... i should have brought some.
DeepL Translated: Oh shit ... I should have brought some.

Original text: ハハハ．．．大丈夫俺が貸してやるよ
Translated text: don't worry, i'll give it to you.
DeepL Translated: Ha ha ha .... Don't worry, I'll lend it to you.

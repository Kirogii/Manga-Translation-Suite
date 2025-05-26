# Manga-Translation-Suite
Based on the sourcecode from https://github.com/Detopall/manga-translator/tree/main
- [Installation v1 + v2 (Partial)](#installation)
- [Setup V2/Info](#V2)
- [Information](#information)
- [Credits](#credits)
- [Translations](#translations)
- IMPORTANT NOTE: When translating dont scroll down and stay at the top of the page until its finished theres a indicator on the top right corner it disappears after its done
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________




## Installation
Download a release from the releases page

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

How to change models for v1 (You might need to edit code for some models that dont use the tokenizer)
[huggingface.co]

- 1: Goto Utils Folders>translate_manga.py
- 2: Edit line 25 [model_name = "Helsinki-NLP/opus-mt-ja-en"] and change [*"Helsinki-NLP/opus-mt-ja-en"*] to any huggingface model identifier
- 3: Save then you are Done :)

How to change models for v2
click the cog icon
- Click the + next to ai models (adding ocr models doesnt work as of now because it requires a little more effort to make ocr models work)
- Type in the id (hugging face model ie [Helsinki-NLP/opus-mt-ja-en] first 2 boxes set them to the model you wish to add
- 3rd box is just a tag of how much ram it takes you can also put "Good" "Bad" "1GB" doesn't matter
- Click the refresh button if its not added and then select it and it should save for every new launch

To remove a model for v2
- Go to the backend folder inside it goto "utils"
- Inside utils change aimodels.json and just remove lines of what you dont want
Example aimodels.json:
```
{
  "models": [
    ["cyy0/JaptoEnBetterMTL-2", "2GB"],
    ["Helsinki-NLP/opus-mt-ja-en", "1.2GB"],
    ["facebook/m2m100_1.2B", "6-12GB"]
  ]
}
```
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

*Original text: 近くにナルシーナって街があるから案内するよそこで今後のことを決めるといい
*Translated text: there's a town in the neighborhood called Narcina, so I'll show you where you can choose what will follow.
*DeepL Translated: There's a town nearby called Narcina, and I'll show you around and you can decide what you want to do.

*Original text: しまった．．．少しは持って来ればよかった
*Translated text: oh, no... i should have brought some.
*DeepL Translated: Oh shit ... I should have brought some.

*Original text: ハハハ．．．大丈夫俺が貸してやるよ
*Translated text: don't worry, i'll give it to you.
*DeepL Translated: Ha ha ha .... Don't worry, I'll lend it to you.

_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________
_________________________________________________________________________________________________________________________________________________________

## V2 
* Major improvements in this first few lines I will list some of the changes
- Added a gui to the extension (popup)
- Added multiple selectable models
- Added tts (takes rougly 0.5-3s for japanese)
- Added dictionary searching from ocr results (Quality is not 100% accurate to source material)
Some things you will need



# How do you setup?
[Android](#android_V2)[Backend](#installation_v2)
## Installation_V2
Download a release from the releases page

- Install python 3.11 + nodejs (Unsure if other versions are supported)
https://www.python.org/downloads/release/python-3110/
https://nodejs.org/en

# After installing python run one of the commands in cmd prompt:

- If you want to use the cpu: (Do this if unsure)
```
pip install -r requirementscpu.txt

```
- If you have a gpu supporting cuda: (Recommended for speed)
```
pip install -r requirementscuda.txt

```

# After installing node run the command in cmdprompt/node:

- This is for android support (check [Android Guide](#android_v2)
```
npm i localtunnel
```
## Android_V2
# Install the extension on android browser
-  install the extension from the repository and compress the files in it on your pc then put it on your phone
-  install an browser app like lemur browser,mises,kiwi browser (Chromium with extension support)
-  goto ```chrome://extensions``` webpage
-  click the developer mode switch and turn it to blue
-  click "load unpacked extension" -- sometimes it says something other than what i listed it 
-  select the extension from the compressed zip we did earlier
# Setup the server
Goto android_server.js edit it in notepad++/notepad (a code editing program)
* Goto line 8 and edit inside the '' the server ip you will connect to on phone
* Take important note any connections by ::1 unless you started it you should decline and stop server and change the ip your connecting from
- After changing line 8 to your own customized ip run android_server.js after app.py says hosting on localhost
# How to use it on phone
* When you launch android_server.js with node you should get a ip type that in the textbox from the main page on the popup then click save endpoint
* You should now get an popup on your pc server click allow if you trust that its yours/someone you trust with your ip (dont let random people in basically)
* After allowing it api requests should work from phone
- Now click translate button on your phone and it should send requests to your pc

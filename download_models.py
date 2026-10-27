"""Download all models used by the demo.

* Vosk models (word recognition)  -> ./models/<lang>
* wav2vec2 phoneme model          -> Hugging Face cache (~/.cache/huggingface)
* MMS letter model + 5 adapters   -> Hugging Face cache
"""
import io
import os
import shutil
import sys
import urllib.request
import zipfile

from huggingface_hub import snapshot_download

from recognition.letter_recognizer import MMS_LANGUAGES
from recognition.letter_recognizer import MODEL_NAME as LETTER_MODEL
from recognition.phoneme_recognizer import MODEL_NAME as PHONEME_MODEL

# Small / lgraph models are used on purpose: they support runtime grammars
# (vosk KaldiRecognizer(model, rate, grammar)), big models do not.
# Ukrainian: vosk-model-small-uk-v3-small returns empty results in grammar mode,
# so the lgraph model (325 MB) is used instead.
MODELS = {
    "en": "vosk-model-small-en-us-0.15",
    "uk": "vosk-model-uk-v3-lgraph",
    "es": "vosk-model-small-es-0.42",
    "it": "vosk-model-small-it-0.22",
    "de": "vosk-model-small-de-0.15",
}
BASE_URL = "https://alphacephei.com/vosk/models/"
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def download(lang, name):
    target = os.path.join(MODELS_DIR, lang)
    if os.path.isdir(target):
        print(f"[{lang}] already present: {target}")
        return
    url = f"{BASE_URL}{name}.zip"
    print(f"[{lang}] downloading {url} ...")
    data = urllib.request.urlopen(url).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(MODELS_DIR)
    shutil.move(os.path.join(MODELS_DIR, name), target)
    print(f"[{lang}] ready: {target}")


if __name__ == "__main__":
    os.makedirs(MODELS_DIR, exist_ok=True)
    langs = sys.argv[1:] or list(MODELS)
    for lang in langs:
        download(lang, MODELS[lang])
    print(f"[phonemes] downloading {PHONEME_MODEL} (~1.2 GB) ...")
    snapshot_download(PHONEME_MODEL)
    print("[phonemes] ready")
    # The repo holds ~1100 language adapters (~9 MB each): fetch only ours.
    print(f"[letters] downloading {LETTER_MODEL} (~3.9 GB) ...")
    adapters = [f"adapter.{code}.safetensors" for code in MMS_LANGUAGES.values()]
    snapshot_download(LETTER_MODEL, allow_patterns=["*.json", "model.safetensors", *adapters])
    print("[letters] ready")

"""Which LETTERS were heard? (Meta MMS, audio -> spelling, no dictionary)

    recognize_letters("es", pcm)  ->  "manana"   # "mañana" said for "manzana"

Model: facebook/mms-1b-all (Hugging Face, ~3.9 GB, 1B parameters). One shared
model plus a small adapter per language. It writes what it hears letter by
letter, so a mispronunciation becomes a misspelling instead of the nearest
real word (as with Vosk).

License: CC-BY-NC-4.0 - non-commercial use only.
"""
import functools
import re
import threading

import torch
from transformers import AutoProcessor, Wav2Vec2ForCTC

from .audio import SAMPLE_RATE, pcm_to_float
from .device import DEVICE

MODEL_NAME = "facebook/mms-1b-all"
MMS_LANGUAGES = {"en": "eng", "uk": "ukr", "es": "spa", "it": "ita", "de": "deu"}
NOT_LETTERS = re.compile(r"[^\w' ]")

# The model holds one language adapter at a time, so switching + decoding
# must not interleave between concurrent requests.
_lock = threading.Lock()
_current = {"lang": None}


@functools.cache
def _load():
    return AutoProcessor.from_pretrained(MODEL_NAME), Wav2Vec2ForCTC.from_pretrained(MODEL_NAME).eval().to(DEVICE)


def recognize_letters(lang, pcm):
    processor, model = _load()
    with _lock:
        if _current["lang"] != lang:
            processor.tokenizer.set_target_lang(MMS_LANGUAGES[lang])
            model.load_adapter(MMS_LANGUAGES[lang])
            _current["lang"] = lang
        inputs = processor(pcm_to_float(pcm), sampling_rate=SAMPLE_RATE, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            ids = model(**inputs).logits.argmax(-1)[0].cpu()
        text = processor.decode(ids)
    return NOT_LETTERS.sub("", text).strip()

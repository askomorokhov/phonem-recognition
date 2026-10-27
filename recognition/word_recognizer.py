"""Which WORD was said? (Vosk, offline, word-level)

Vosk always returns real dictionary words; it has no phoneme output.
Two ways to use it:

* open vocabulary - recognize(lang, pcm): the closest word(s) from the whole
  model dictionary, with per-word confidence and n-best alternatives.
* closed set      - recognize(lang, pcm, grammar=[...]): Vosk must choose one of
  the given words, or the garbage token returned as "[unk]".
"""
import json
import os

from vosk import KaldiRecognizer, Model, SetLogLevel

from .audio import SAMPLE_RATE

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
# Garbage token used in grammars: "[unk]" in most models, "<UNK>" in the Ukrainian one.
UNK = {"uk": "<UNK>"}

SetLogLevel(-1)
_models = {}


def get_model(lang):
    if lang not in _models:
        _models[lang] = Model(os.path.join(MODELS_DIR, lang))
    return _models[lang]


def unk_token(lang):
    return UNK.get(lang, "[unk]")


def _recognizer(lang, grammar):
    if grammar:
        # ensure_ascii=False: Vosk's JSON parser does not decode \uXXXX escapes,
        # so Cyrillic / accented words would be silently dropped otherwise.
        return KaldiRecognizer(get_model(lang), SAMPLE_RATE, json.dumps(grammar, ensure_ascii=False))
    return KaldiRecognizer(get_model(lang), SAMPLE_RATE)


def recognize(lang, pcm, grammar=None):
    """Returns (words with confidence, n-best texts)."""
    rec = _recognizer(lang, grammar)
    rec.SetWords(True)
    rec.AcceptWaveform(pcm)
    words = json.loads(rec.FinalResult()).get("result", [])

    # Second decode just for the n-best list (result format differs when alternatives are on).
    rec = _recognizer(lang, grammar)
    rec.SetMaxAlternatives(5)
    rec.AcceptWaveform(pcm)
    alternatives = [a["text"] for a in json.loads(rec.FinalResult())["alternatives"] if a["text"].strip()]

    words = [{"word": "[unk]" if w["word"] == UNK.get(lang) else w["word"], "conf": round(w["conf"], 2)}
             for w in words]
    return words, alternatives

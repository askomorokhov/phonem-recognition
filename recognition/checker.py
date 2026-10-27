"""Runs the enabled checks on one recording and builds the result.

Checks (each can be switched off; a disabled model is never loaded):
  "word"     - Vosk:                 which word was said?
  "phonemes"      - espeak-ng + wav2vec2: which sounds were right or wrong?
  "pronunciation" - GOP on wav2vec2:      how well was each expected sound pronounced?
  "spelling"      - MMS:                  how would it be spelled as heard?

Result (sections of disabled checks are absent):
{
  "target": "manzana",
  "verdict": "correct" | "close" | "wrong" | "silence" | null,
  "latency_ms": 640,                                      # all checks together
  "word": {
    "heard": "mañana", "heard_words": [{"word", "conf"}], "alternatives": [...],
    "closed_set": [{"word", "conf"}],   # target vs. other card words vs. [unk]
    "letters": [{"symbol", "status"}], "similarity": 0.77, "latency_ms": 210
  },
  "phonemes": {
    "expected": ["m", "a", "n", "θ", "ˈa", "n", "a"], "heard": ["m", "a", "n", "a", "n", "a"],
    "diff": [{"symbol", "status"}], "similarity": 0.92, "latency_ms": 90
  },
  "pronunciation": {
    "phonemes": [{"symbol": "θ", "gop": -13.7, "status": "ok|unsure|wrong|missing", "instead": ""}],
    "similarity": 0.57, "latency_ms": 15     # similarity = share of sounds scored "ok"
  },
  "spelling": {
    "heard": "manana", "diff": [{"symbol", "status"}], "similarity": 0.92, "latency_ms": 340
  }
}
"""
import time

from words import WORDS

from . import (compare, expected_phonemes, letter_recognizer, phoneme_recognizer,
               pronunciation_score, word_recognizer)
from .audio import pad_silence

ENGINES = ("word", "phonemes", "pronunciation", "spelling")


def _word(lang, target, pcm):
    # Open vocabulary: which real word is closest to what was said?
    heard_words, alternatives = word_recognizer.recognize(lang, pcm)
    heard = " ".join(w["word"] for w in heard_words)
    # Closed set: target vs. the other card words vs. garbage.
    grammar = sorted({w[lang] for w in WORDS} | {target}) + [word_recognizer.unk_token(lang)]
    closed_set, _ = word_recognizer.recognize(lang, pcm, grammar)
    letters, similarity = compare.diff_letters(target, heard)
    return {"heard": heard, "heard_words": heard_words, "alternatives": alternatives,
            "closed_set": closed_set, "letters": letters, "similarity": similarity}


def _phonemes(lang, target, pcm):
    # Expected sounds (from text) vs. heard sounds (from audio).
    expected = expected_phonemes.expected_phonemes(lang, target)
    heard = phoneme_recognizer.recognize_phonemes(pcm)
    diff, similarity = compare.diff_phonemes(expected, heard)
    return {"expected": expected, "heard": heard, "diff": diff, "similarity": similarity}


def _pronunciation(lang, target, pcm):
    # GOP score per expected sound (reuses the wav2vec2 output of _phonemes when both are on).
    return pronunciation_score.score_pronunciation(lang, target, pcm)


def _spelling(lang, target, pcm):
    # Letters as heard, no dictionary, vs. the target spelling.
    heard = letter_recognizer.recognize_letters(lang, pcm)
    diff, similarity = compare.diff_letters(target, heard.lower())
    return {"heard": heard, "diff": diff, "similarity": similarity}


CHECKS = {"word": _word, "phonemes": _phonemes, "pronunciation": _pronunciation, "spelling": _spelling}


def _verdict(target, sections):
    if "word" in sections:
        w = sections["word"]
        if not w["heard_words"]:
            return "silence"
        if w["heard"] == target:
            return "correct"
        if any(c["word"] == target for c in w["closed_set"]) or target in w["alternatives"] or w["similarity"] >= 0.6:
            return "close"  # target is plausible, but it was not the best match
        return "wrong"
    # Without Vosk: fall back to the best similarity of the other checks. "correct"
    # needs a near-exact match: one missing sound in a short word is already ~0.9.
    if not sections:
        return None
    heard = [s["heard"] for s in sections.values() if "heard" in s]
    if heard and not any(heard):
        return "silence"
    best = max(s["similarity"] for s in sections.values())
    return "correct" if best >= 0.95 else "close" if best >= 0.6 else "wrong"


def check_word(lang, target, pcm, engines=ENGINES):
    target = target.lower()
    pcm = pad_silence(pcm)

    sections = {}
    started = time.perf_counter()
    for name in ENGINES:
        if name in engines:
            t = time.perf_counter()
            sections[name] = CHECKS[name](lang, target, pcm)
            sections[name]["latency_ms"] = round((time.perf_counter() - t) * 1000)

    return {
        "target": target,
        "verdict": _verdict(target, sections),
        "latency_ms": round((time.perf_counter() - started) * 1000),
        **sections,
    }

"""Where do EXPECTED and HEARD differ? Works for letters and for phonemes.

    diff("manzana", "mañana")  ->  m a [ñ wrong] [n missing] [z missing] a n a

Each item is {"symbol": ..., "status": "ok" | "wrong" | "missing" | "extra"}:
  wrong   - heard instead of the expected symbol(s) that follow as "missing"
  missing - expected but not heard
  extra   - heard but not expected
"""
import difflib
import re

# Phoneme clean-up before comparing: drop stress, length and aspiration marks
# (the recognizer can't hear them reliably), then fold symbols that are just
# notational variants or near-identical sounds. This is a tuning knob: an empty
# BROAD map gives a strict comparison.
MARKS = re.compile("[ˈˌːʰ͡‍]")
BROAD = {
    "ɑ": "a", "ɐ": "a", "ɔ": "o", "ɛ": "e", "ɪ": "i", "ʊ": "u", "ʏ": "y",
    "ɹ": "r", "ɾ": "r", "ʁ": "r", "ɫ": "l", "l̪": "l", "t̪": "t", "d̪": "d", "s̪": "s",
}


def clean_phoneme(p):
    return MARKS.sub("", p)


def phoneme_key(p):
    return BROAD.get(p, p)


def diff(expected, heard, key=lambda s: s):
    """Align two sequences; `key` decides which symbols count as equal."""
    out = []
    sm = difflib.SequenceMatcher(None, [key(s) for s in expected], [key(s) for s in heard], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out += [{"symbol": s, "status": "ok"} for s in expected[i1:i2]]
        elif op == "delete":
            out += [{"symbol": s, "status": "missing"} for s in expected[i1:i2]]
        elif op == "insert":
            out += [{"symbol": s, "status": "extra"} for s in heard[j1:j2]]
        else:  # replace
            out += [{"symbol": s, "status": "wrong"} for s in heard[j1:j2]]
            out += [{"symbol": s, "status": "missing"} for s in expected[i1:i2]]
    return out, round(sm.ratio(), 2)


def diff_letters(expected_word, heard_word):
    return diff(expected_word, heard_word.replace(" ", ""))


def diff_phonemes(expected, heard):
    return diff([clean_phoneme(p) for p in expected], [clean_phoneme(p) for p in heard], key=phoneme_key)

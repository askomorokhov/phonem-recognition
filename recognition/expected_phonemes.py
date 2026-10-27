"""Which sounds SHOULD be made? (espeak-ng, text -> IPA phonemes)

    expected_phonemes("uk", "м'яч")  ->  ["m", "j", "ˈa", "tʃ"]

Uses the espeak-ng command line tool (brew / apt install espeak-ng).
The phoneme recognizer was trained on espeak-ng transcriptions, so both
sides use the same phoneme symbols.
"""
import functools
import subprocess

ESPEAK_VOICES = {"en": "en-us", "uk": "uk", "es": "es", "it": "it", "de": "de"}


@functools.cache
def expected_phonemes(lang, word):
    out = subprocess.run(
        ["espeak-ng", "-q", "--ipa=1", "--sep= ", "-v", ESPEAK_VOICES[lang], word],
        capture_output=True, text=True, check=True,
    ).stdout
    return out.split()

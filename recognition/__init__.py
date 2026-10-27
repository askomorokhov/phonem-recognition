"""Speech checking for picture-naming practice.

Pipeline (see checker.check_word):

    audio ──► word_recognizer     (Vosk)      which WORD was said?
          ──► phoneme_recognizer  (wav2vec2)  which SOUNDS were made?
                └─► pronunciation_score (GOP) how WELL was each expected sound made?
          ──► letter_recognizer   (MMS)       which LETTERS were heard (no dictionary)?
    word  ──► expected_phonemes   (espeak-ng) which sounds SHOULD be made?
                    └──► compare  (difflib)   where do they differ?

Each module is independent and can be replaced on its own.
"""
from .checker import check_word

__all__ = ["check_word"]

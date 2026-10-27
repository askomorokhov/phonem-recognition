"""Which SOUNDS were made? (wav2vec2, audio -> IPA phonemes, no dictionary)

    recognize_phonemes(pcm)  ->  ["m", "a", "n", "a", "n", "a"]   # "mañana" said for "manzana"

Model: facebook/wav2vec2-lv-60-espeak-cv-ft (Hugging Face, ~1.2 GB, downloaded
on first use). It is multilingual (trained on Common Voice transcribed with
espeak-ng), so it needs no language parameter and returns sounds as heard,
without snapping them to a real word.

Alternatives we tried on the same test clips:
* facebook/wav2vec2-xlsr-53-espeak-cv-ft - similar, slightly worse
* allosaurus (pip) - much lighter, but too inaccurate for this demo
"""
import functools
import re

import torch
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC, Wav2Vec2PhonemeCTCTokenizer

from .audio import SAMPLE_RATE, pcm_to_float
from .device import DEVICE

MODEL_NAME = "facebook/wav2vec2-lv-60-espeak-cv-ft"
# The model's vocabulary includes Mandarin tones ("ɑ5", "ouɜ"), pinyin-style
# aspirates ("th", "kh") and odd notations from other languages ("ts.", "dZ").
# None occur in our 5 languages, so we forbid them.
NOT_OUR_LANGUAGES = re.compile(r"[0-9.\[\^\"?A-Z]|.ɜ|^(ph|th|kh|tsh|tɕh)$")


@functools.cache
def _load():
    features = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME)
    # do_phonemize=False: we only decode, so the phonemizer package is not needed.
    tokenizer = Wav2Vec2PhonemeCTCTokenizer.from_pretrained(MODEL_NAME, do_phonemize=False)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_NAME).eval().to(DEVICE)
    blocked = [i for token, i in tokenizer.get_vocab().items() if NOT_OUR_LANGUAGES.search(token)]
    return features, tokenizer, model, blocked


@functools.lru_cache(maxsize=4)
def log_probs(pcm):
    """Per-frame log-probabilities over the phoneme vocabulary, shape [frames, vocab], on CPU.
    Cached so recognition and pronunciation scoring share one model run (don't modify the result)."""
    features, _, model, blocked = _load()
    inputs = features(pcm_to_float(pcm), sampling_rate=SAMPLE_RATE, return_tensors="pt")
    with torch.no_grad():
        logits = model(inputs.input_values.to(DEVICE)).logits[0]
    logits[:, blocked] = float("-inf")
    return torch.log_softmax(logits, dim=-1).cpu()


def vocabulary():
    """Phoneme symbol -> token id, for every phoneme the model may output (no blocked or special tokens)."""
    _, tokenizer, _, blocked = _load()
    excluded = set(blocked) | set(tokenizer.all_special_ids)
    return {token: i for token, i in tokenizer.get_vocab().items() if i not in excluded}


def recognize_phonemes(pcm):
    tokenizer = _load()[1]
    return tokenizer.decode(log_probs(pcm).argmax(-1)).split()

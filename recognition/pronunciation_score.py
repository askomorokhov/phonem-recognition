"""How WELL was each expected sound pronounced? (GOP on the wav2vec2 output)

    score_pronunciation("es", "manzana", pcm)
      -> {"phonemes": [{"symbol": "θ", "gop": -6.1, "status": "missing", "instead": ""}, ...], "similarity": 0.86}

GOP = Goodness of Pronunciation. We know which sounds should be there (espeak-ng),
so instead of asking the model "what was said?" we ask "how well does each
expected sound explain the audio?". For expected phoneme i:

    gop_i = log P(expected sequence | audio) - max log P(same sequence with phoneme i replaced or deleted | audio)

  gop >= 0  the expected sound is the best explanation                  -> "ok"
  gop <  0  another sound (or nothing) explains the audio better         -> "instead" says which

P(sequence | audio) is the CTC probability on the same wav2vec2 output that
phoneme_recognizer uses, so no extra model run is needed.

Symbols that compare.py treats as the same sound (t̪/t, ɪ/i, ɾ/r, length marks…)
are not competitors: each expected sound first takes whichever equivalent
spelling the model prefers, so notation differences don't count as errors.

Only meaningful if the person attempted the target word: for a different word
every sound scores badly. Thresholds are NOT calibrated - that needs recordings
of healthy speakers per language.
"""
from collections import defaultdict

import torch
import torch.nn.functional as F

from . import phoneme_recognizer
from .compare import clean_phoneme, phoneme_key
from .expected_phonemes import expected_phonemes

OK_FROM = 0.0       # gop >= OK_FROM: pronounced well
WRONG_BELOW = -2.0  # gop <  WRONG_BELOW: mispronounced; in between: unsure


def _sound(symbol):
    return phoneme_key(clean_phoneme(symbol))


def _expected(lang, target, equivalents):
    """Expected phonemes as (display symbol, ids of all model tokens for that sound)."""
    symbols = [clean_phoneme(p) for p in expected_phonemes(lang, target)]
    return [(s, equivalents[_sound(s)]) for s in symbols if equivalents[_sound(s)]]


def _sequence_log_probs(log_probs, sequences):
    """log P(sequence | audio) for each candidate sequence, via CTC, in one batch."""
    n = len(sequences)
    lengths = torch.tensor([len(s) for s in sequences])
    targets = torch.zeros(n, max(1, int(lengths.max())), dtype=torch.long)
    for k, s in enumerate(sequences):
        targets[k, :len(s)] = torch.tensor(s, dtype=torch.long)
    frames = torch.full((n,), log_probs.shape[0], dtype=torch.long)
    batch = log_probs.unsqueeze(1).expand(-1, n, -1)  # [frames, n, vocab]
    return -F.ctc_loss(batch, targets, frames, lengths, blank=0, reduction="none")


def score_pronunciation(lang, target, pcm):
    vocab = phoneme_recognizer.vocabulary()
    symbol_of = {i: s for s, i in vocab.items()}
    equivalents = defaultdict(list)  # sound -> ids of every model token spelling that sound
    for symbol, i in vocab.items():
        equivalents[_sound(symbol)].append(i)
    expected = _expected(lang, target, equivalents)
    log_probs = phoneme_recognizer.log_probs(pcm)

    # Pick, per position, the equivalent spelling that best fits the audio.
    sequence = [ids[0] for _, ids in expected]
    for i, (_, ids) in enumerate(expected):
        scores = _sequence_log_probs(log_probs, [sequence[:i] + [q] + sequence[i + 1:] for q in ids])
        sequence[i] = ids[int(scores.argmax())]
    base = _sequence_log_probs(log_probs, [sequence])[0]

    phonemes = []
    for i, (symbol, ids) in enumerate(expected):
        others = [q for q in vocab.values() if q not in ids]
        variants = [sequence[:i] + [q] + sequence[i + 1:] for q in others]  # substitutions
        variants.append(sequence[:i] + sequence[i + 1:])                    # deletion
        scores = _sequence_log_probs(log_probs, variants)
        best = int(scores.argmax())
        gop = float(base - scores[best])
        instead = symbol_of[others[best]] if best < len(others) else ""
        if gop >= OK_FROM:
            status = "ok"
        elif gop >= WRONG_BELOW:
            status = "unsure"
        else:
            status = "wrong" if instead else "missing"
        phonemes.append({"symbol": symbol, "gop": round(gop, 1), "status": status,
                         "instead": instead if status != "ok" else ""})

    ok = sum(ph["status"] == "ok" for ph in phonemes)
    return {"phonemes": phonemes, "similarity": round(ok / len(phonemes), 2) if phonemes else 0.0}

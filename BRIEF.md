# Speech-check models: comparison


| Model | Output | Pros | Cons |
| --- | --- | --- | --- |
| **Vosk** | a word from the dictionary | fast (~0.3 s); reliable word ID in all 5 languages; small models (40–330 MB); Apache-2.0; mobile SDKs | snaps every error to the nearest real word; no phoneme output |
| **wav2vec2** | IPA phonemes | shows exactly which sound is wrong; one model for all languages; Apache-2.0 | 1.3 GB; weak on some English/German words |
| **MMS** | spelling as heard | no dictionary; 1,100+ languages | 3.9 GB, ~4 GB RAM; weak on single words; can't tell "яблуко" from "яблоко"; non-commercial license |

## Why phonemes beat words and letters

- **Words hide errors.** A dictionary turns a mispronunciation into some other real word ("tapple" → "turbo").
- **Letters depend on spelling rules.** In English and German, spelling often doesn't match the sounds ("Apfel" → `apse`).
- **Phonemes describe what was actually said**, in the same form in every language. They map directly to aphasia errors (a sound substituted, missing or added) and compare directly with the expected pronunciation.

## wav2vec2: the leader

- **What it is:** `facebook/wav2vec2-lv-60-espeak-cv-ft`, a 316M-parameter model (Apache-2.0) that turns audio into IPA phonemes without a dictionary.
  espeak-ng provides the expected phonemes for comparison.
- **Hardware (measured on Apple M2):**
  - 1.3 GB download, ~1.7 GB RAM.
  - **0.14 s per word on CPU**, 0.05 s on the Mac GPU.
  - First call 2–5 s (model loading).
  - A GPU is optional. For phones it would need conversion and compression (ONNX/int8; not tested).
- **Alternatives:**
  - `wav2vec2-xlsr-53-espeak-cv-ft`: same size, slightly worse in our test.
  - Allosaurus: tiny, but much less accurate.
  - ZIPA (2025): smaller multilingual phone recognizer, not tested.
  - Kaldi GOP: scores each expected phoneme; more engineering work. **Not needed:** we built GOP directly on wav2vec2 (see below).

## GOP: score per expected sound (built on wav2vec2)

Instead of asking "what was said?", GOP asks "how well does each expected sound explain the audio?".
It compares the expected word against the same word with one sound replaced or removed.
The result is a number per sound: ≥ 0 good, strongly negative wrong, plus which sound was heard instead.
It reuses the wav2vec2 output, so it adds only 5–30 ms.

| Said | GOP result |
| --- | --- |
| "яблоко" for "яблуко" | `u −2.8`, heard `o`; all other sounds positive |
| "mañana" for "manzana" | `θ −13.7`, missing |

GOP only makes sense if the person attempted the target word. Its thresholds still need calibration on real speakers.

## Microphone matters

Phoneme recognition has no dictionary to "repair" bad audio, so noise, echo or a distant laptop mic turns into false sound errors.
Use a headset or a close microphone in a quiet room.


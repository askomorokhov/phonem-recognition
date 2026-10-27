# Say the Word: speech-check PoC for aphasia word-naming practice

The user sees a picture (🍎, 🚗, … 20 cards), presses a button and says the word. The app answers three questions:

1. **Did they say the right word?** Vosk word recognition.
2. **Which sounds were right or wrong?** wav2vec2 phoneme recognition compared with the expected pronunciation from espeak-ng.
3. **How would it be spelled as heard?** Meta MMS letter recognition, with no dictionary.

Example: someone says "mañana" for the picture 🍎 *manzana*.

```text
Verdict:  🟡 Almost
Word:     m a [ñ] ~~n z~~ a n a          heard "mañana" (87 %), closed-set check: manzana
Sounds:   m a n ~~θ~~ a n a  (92 % match)   expected /m a n θ ˈa n a/, heard /m a n a n a/
Letters:  m a n ~~z~~ a n a  (92 % match)   heard "manana"
```

Languages: English, Ukrainian, Spanish, Italian, German. Everything runs locally and no audio leaves the machine.

This is a demo only. The code is deliberately minimal.

## Run it

```bash
brew install espeak-ng                  # Linux: apt install espeak-ng
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python download_models.py     # Vosk ~650 MB + phoneme model ~1.2 GB + MMS ~3.9 GB
.venv/bin/python app.py                 # open http://localhost:8000
```

Models load on first use: the first check takes ~20 s, and the first Ukrainian check ~10 s (large Vosk model).
After that, a check takes 0.4–1.6 s on an M-series Mac, where the neural models run on the GPU (`recognition/device.py`).
On CPU only, expect 5–15 s per check. The neural models alone take ~5 GB of memory.
Browsers only allow the microphone on `localhost` or HTTPS.

Command-line version (prints the full JSON result) for a 16 kHz mono WAV file:

```bash
.venv/bin/python check_wav.py es manzana recording.wav
.venv/bin/python check_wav.py es manzana recording.wav --engines word,phonemes   # only some models
```

### Model switches and latency

The header of the page has a switch per model: **Word · Vosk**, **Sounds · wav2vec2**, **Score · GOP**, **Letters · MMS**.
A switched-off model is not run and, if it was never used, never loaded (saves ~4 GB for MMS). The choice is remembered in the browser.

Each result box shows how long its model took. The line under the verdict shows the total for all models and the total including upload.
The first check after start includes model loading (10–20 s); after that, typical numbers on an M-series Mac are:

| Model | Latency |
| --- | --- |
| Word · Vosk | 200–450 ms |
| Sounds · wav2vec2 | 60–400 ms |
| Score · GOP | 5–30 ms (reuses the wav2vec2 output) |
| Letters · MMS | 100–250 ms |

## Code map

```text
recognition/                  ← all speech logic, one module per question
  checker.py                  runs the pipeline, builds the result, decides the verdict
  word_recognizer.py          WHICH WORD was said?          Vosk (per-language models)
  phoneme_recognizer.py       WHICH SOUNDS were made?       wav2vec2 (one multilingual model)
  expected_phonemes.py        which sounds SHOULD be made?  espeak-ng (text → IPA)
  pronunciation_score.py      how WELL was each sound made? GOP on the wav2vec2 output (no extra model)
  letter_recognizer.py        which LETTERS were heard?     Meta MMS (one model + adapter per language)
  compare.py                  WHERE do they differ?         difflib alignment (letters + phonemes)
  audio.py                    shared audio format (16 kHz mono 16-bit PCM)
  device.py                   where neural models run: Apple GPU (mps) / NVIDIA (cuda) / cpu
words.py                      20 cards: emoji + word in 5 languages
app.py                        Flask: GET /api/words, POST /api/check?lang=es&word=apple&engines=word,phonemes,pronunciation,spelling (body = raw PCM)
static/index.html             single-page UI: mic → resample to 16 kHz in browser → POST
check_wav.py                  CLI
download_models.py            fetches all models
```

```text
audio ──► word_recognizer     (Vosk)      ──► heard word, confidence, alternatives, closed-set check
      ──► phoneme_recognizer  (wav2vec2)  ──► heard phonemes   ─┐
target ─► expected_phonemes   (espeak-ng) ──► expected phonemes ─┴─► compare ──► phoneme diff + similarity
expected phonemes + wav2vec2 output ──► pronunciation_score (GOP) ──► score per expected sound
audio ──► letter_recognizer   (MMS)       ──► heard spelling  ──────► compare ──► letter diff + similarity
```

The modules don't depend on each other. Only `checker.py` combines them, so each engine can be swapped independently.
For example, `phoneme_recognizer.recognize_phonemes(pcm) -> list[str]` is the whole interface to replace.

### Result JSON (`POST /api/check`)

```json
{
  "target": "manzana",
  "verdict": "close",
  "latency_ms": 640,
  "word": {
    "heard": "mañana",
    "heard_words": [{"word": "mañana", "conf": 0.87}],
    "alternatives": ["mañana", "manana"],
    "closed_set": [{"word": "manzana", "conf": 1.0}],
    "letters": [{"symbol": "m", "status": "ok"}, "..."],
    "similarity": 0.77,
    "latency_ms": 210
  },
  "phonemes": {
    "expected": ["m", "a", "n", "θ", "ˈa", "n", "a"],
    "heard": ["m", "a", "n", "a", "n", "a"],
    "diff": [{"symbol": "θ", "status": "missing"}, "..."],
    "similarity": 0.92,
    "latency_ms": 90
  },
  "pronunciation": {
    "phonemes": [{"symbol": "θ", "gop": -13.7, "status": "missing", "instead": ""}, "..."],
    "similarity": 0.57,
    "latency_ms": 15
  },
  "spelling": {
    "heard": "manana",
    "diff": [{"symbol": "z", "status": "missing"}, "..."],
    "similarity": 0.92,
    "latency_ms": 340
  }
}
```

Sections of switched-off models are left out. `engines` is optional; the default is all four.
In `pronunciation`, `similarity` is the share of sounds scored `ok`, and `status` can also be `unsure`.

`status` is one of:

* `ok`
* `wrong`: heard instead of the `missing` symbols that follow it
* `missing`
* `extra`

## How each part works

**Word check (Vosk).** The audio is decoded twice:

* **Open vocabulary:** the closest real word, with confidence and n-best alternatives. Catches word substitutions ("Katze" for "Hund").
* **Closed set:** the grammar is the target, the 19 other card words and `[unk]`. Answers yes or no for the target.

The verdict comes from the word check:

* `correct`: the open-vocabulary result equals the target.
* `close`: the target is among the alternatives, or wins the closed set, or the spelling is ≥ 60 % similar.
* `wrong`: none of the above.

**Sounds check.** espeak-ng turns the target word into IPA phonemes.
`facebook/wav2vec2-lv-60-espeak-cv-ft` turns the audio into IPA phonemes *without* a dictionary, so a mispronunciation comes out as it sounds.
The model was trained on espeak-ng transcriptions, so both sides use the same symbols.

Before comparing, `compare.py` drops stress and length marks and treats near-identical symbols as equal (`ɔ`=`o`, `ɾ`=`r`, …).
That map (`BROAD`) is a tuning knob: an empty map gives a strict comparison.

**Pronunciation score (GOP).** Free recognition asks "what was said?". GOP (Goodness of Pronunciation) asks
"how well does each *expected* sound explain the audio?". For expected sound *i*:

```text
gop_i = log P(expected sequence | audio) − max log P(same sequence with sound i replaced or deleted | audio)
```

* `gop ≥ 0`: the expected sound is the best explanation (`ok`).
* `0 > gop ≥ −2`: `unsure`.
* `gop < −2`: `wrong` (with the sound heard instead) or `missing`.

The probabilities are CTC scores on the same wav2vec2 output (`phoneme_recognizer.log_probs`, cached), so no extra model run and no Kaldi are needed.
Symbols that `compare.py` treats as the same sound (`t̪`/`t`, `ɪ`/`i`, length marks…) are not counted as competitors.
The thresholds are **not calibrated**; that needs recordings of healthy speakers per language.
GOP only makes sense when the person attempted the target word, so the UI warns when the word check says a different word was said.

**Letters check (MMS).** `facebook/mms-1b-all` writes the audio as letters in the selected language, with no dictionary.
A mispronunciation becomes a misspelling ("manana") instead of the nearest real word.
The model holds one language adapter at a time, so `letter_recognizer.py` switches adapters under a lock.

The phoneme and letter similarities are shown next to the verdict but do **not** change it.
How to combine the signals should be decided with therapists.

**Without Vosk** (word check switched off), the verdict falls back to the best similarity of the other checks:
`correct` ≥ 95 %, `close` ≥ 60 %, otherwise `wrong`.
"Correct" needs a near-exact match, because one missing sound in a short word already gives ~90 %.
On the test clips this agreed with the Vosk verdict in 11 of 15 cases. It never called a wrong word correct, but sometimes said `close` for a correct one.

## What we learned

1. **Vosk has no phoneme output** (checked the Python API 0.3.44 and the C++ source).
   It always snaps speech to a dictionary word ("tapple" → "turbo"), which is why a separate phoneme model is needed.
   Vosk's NLSML option is only an XML output format for telephony systems.
2. **Phoneme models we compared** on the same clips:

   | Model | Result |
   | --- | --- |
   | `facebook/wav2vec2-lv-60-espeak-cv-ft` | **chosen**, best overall |
   | `facebook/wav2vec2-xlsr-53-espeak-cv-ft` | similar, slightly worse |
   | `allosaurus` (pip) | much lighter, but too inaccurate ("Schlüssel" → `s ɪ s ɪ z`) |

3. The wav2vec2 vocabulary contains Mandarin tone tokens (`ɑ5`) and other-language notations (`th`, `ts.`).
   They are blocked before decoding (`NOT_OUR_LANGUAGES` in `phoneme_recognizer.py`). Otherwise they leak into results.
4. **Ukrainian Vosk:** in grammar mode, the small model `vosk-model-small-uk-v3-small` returns empty or wrong words.
   We use `vosk-model-uk-v3-lgraph`. Its garbage token is `<UNK>`, not `[unk]`.
5. **Gotcha:** Vosk grammars must be built with `json.dumps(..., ensure_ascii=False)`.
   Vosk does not decode `\uXXXX`, so Cyrillic and accented words would silently disappear.
6. Small silence padding (`audio.pad_silence`) noticeably improves both recognizers on tightly cut clips.
7. **MMS letters** compared with Vosk on the same clips:
   * Good: Spanish ("mañana" → `manana`, the missing *z* shown) and Italian.
   * Weak: English and German single words ("apple" → `af`, "Schlüssel" → `je le seis`).
   * **Ukrainian:** MMS gave `я блоко` for both the correct "яблуко" and the mispronounced "яблоко", so it can't separate them. Vosk and wav2vec2 can.
   * Likely reason: MMS was trained mostly on read sentences, and isolated words are hard for it.
     Its per-language adapters are small, so fine-tuning on recordings of single words is a realistic next step.
8. **Speed:** running wav2vec2 and MMS on the Apple GPU (PyTorch `mps`) instead of the CPU took a check from 5–15 s down to under 2 s, with identical output.
9. **GOP** pinpoints errors with clear numbers:
   * "mañana" → `θ −13.7` (missing).
   * "яблоко" → `u −2.8` (heard `o`); on the correct "яблуко" the same sound scores −0.2.
   * Correct "кіт", "машина", "manzana" and "car" → all sounds `ok`.
   * Without the sound equivalences, notation differences (espeak `t̪` vs. model `t`) scored as false errors around −3.
   * An error can spill onto neighbouring sounds ("mañana": `n −2.2`, `a −3.6` next to the missing θ).
10. **Tested only with synthetic speech** (macOS TTS voices). The full browser flow was also run in headless Chrome with a fake microphone.
   * Good: Spanish, Ukrainian, Italian, and German "Schlüssel". The phoneme diff pinpoints real errors: missing `θ` in "mañana", `o`→`u` in "яблоко".
   * Weak: the phoneme model on English "apple" and German "Apfel" TTS clips (`aː f o`, `a b s i`), while Vosk recognised both words correctly.
   * **Nothing has been tested with real aphasic speech.** That needs real recordings and clinical input.

## Suggestions for the engineering team

* Evaluate accuracy on real recordings (healthy speakers first, then patients) before tuning thresholds or the `BROAD` map.
* Calibrate the GOP thresholds (`OK_FROM`, `WRONG_BELOW` in `pronunciation_score.py`) on recordings of healthy speakers, per language and ideally per sound.
* GOP doesn't detect *inserted* sounds yet; adding insertion variants works the same way as substitutions.
* For on-device use, Vosk has Android, iOS and WASM (`vosk-browser`) bindings. The wav2vec2 model can be exported to ONNX.
  See the [Vosk integrations page](https://alphacephei.com/vosk/integrations).
* Check licenses for production:
  * Vosk: Apache 2.0.
  * espeak-ng: GPL-3. It's called here as a separate CLI process.
  * wav2vec2 phoneme model: see its Hugging Face card.
  * **MMS: CC-BY-NC-4.0, non-commercial only.** Fine for a free charity app, but confirm with whoever handles legal before release.
    The other modules don't depend on it, so it can be removed in one place (`checker.py`) if needed.
* Replace emoji with real pictures, and avoid words that depend on articles (Italian "l'orologio" vs "orologio").

"""Command-line demo: check a WAV recording against an expected word.

    python check_wav.py en apple recording.wav
    python check_wav.py en apple recording.wav --engines word,phonemes

The WAV must be 16 kHz, mono, 16-bit. Convert any file with:
    ffmpeg -i input.m4a -ar 16000 -ac 1 -sample_fmt s16 recording.wav
"""
import argparse
import json
import sys
import wave

from recognition import check_word
from recognition.audio import SAMPLE_RATE
from recognition.checker import ENGINES

if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("lang")
    parser.add_argument("target")
    parser.add_argument("path")
    parser.add_argument("--engines", default=",".join(ENGINES), help=f"comma-separated subset of {ENGINES}")
    args = parser.parse_args()
    with wave.open(args.path, "rb") as wf:
        if wf.getframerate() != SAMPLE_RATE or wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            sys.exit("WAV must be 16 kHz mono 16-bit, see --help")
        pcm = wf.readframes(wf.getnframes())
    print(json.dumps(check_word(args.lang, args.target, pcm, args.engines.split(",")), ensure_ascii=False, indent=2))

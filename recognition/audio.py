"""Audio format shared by all modules: 16 kHz, mono, 16-bit little-endian PCM bytes."""
import numpy as np

SAMPLE_RATE = 16000


def pad_silence(pcm, seconds=0.3):
    """Both recognizers do noticeably better on tightly cut clips with a bit of silence around them."""
    silence = b"\0\0" * int(SAMPLE_RATE * seconds)
    return silence + pcm + silence


def pcm_to_float(pcm):
    """PCM bytes -> float32 samples in [-1, 1], the format neural models expect."""
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768

"""Where the neural models (wav2vec2, MMS) run: Apple GPU, NVIDIA GPU, or CPU.

On an M-series Mac, "mps" made a check ~100x faster than CPU (0.07 s vs 5-15 s).
"""
import torch

DEVICE = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"

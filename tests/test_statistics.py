"""
Test statistical metrics on synthetic audio clips.

Paper Section 8:
  Tests entropy, adjacent-sample correlation, NSCR, and UACI.
"""

import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecga.genetic import compute_byte_entropy
from ecga.keyexchange import derive_demo_session_key
from ecga.pipeline import AudioFrameCipher, bytes_to_pcm, pcm_to_bytes


def compute_adjacent_sample_correlation(pcm_samples: list) -> float:
    """Compute Pearson correlation coefficient between adjacent PCM samples."""
    x = np.array(pcm_samples[:-1], dtype=np.float64)
    y = np.array(pcm_samples[1:], dtype=np.float64)
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def compute_nscr_uaci(pcm1: list, pcm2: list) -> tuple:
    """
    Compute NSCR (%) and UACI (%) between two 16-bit PCM sample vectors of equal length.
    """
    s1 = np.array(pcm1, dtype=np.int32)
    s2 = np.array(pcm2, dtype=np.int32)
    n = len(s1)

    diff_count = np.sum(s1 != s2)
    nscr = (diff_count / n) * 100.0

    abs_diff = np.abs(s1 - s2)
    uaci = (np.mean(abs_diff) / 65535.0) * 100.0

    return float(nscr), float(uaci)


def test_statistics_on_synthetic_frame():
    """Test entropy, correlation, and differential metrics on encrypted synthetic frame."""
    # Create 16000 16-bit PCM samples (2 seconds at 8kHz)
    t = np.linspace(0, 2.0, 16000, endpoint=False)
    signal = (20000.0 * np.sin(2 * np.pi * 440.0 * t)).astype(np.int16)
    pcm_plain = list(signal)

    ks = derive_demo_session_key("statistics_test_key")
    cipher = AudioFrameCipher()

    c_bytes, tag = cipher.encrypt_frame(pcm_plain, ks)
    c_pcm = bytes_to_pcm(c_bytes)

    # 1. Byte entropy
    entropy = compute_byte_entropy(c_bytes)
    assert entropy > 7.98, f"Expected high entropy > 7.98, got {entropy}"

    # 2. Plaintext correlation should be high for sine wave
    r_plain = compute_adjacent_sample_correlation(pcm_plain)
    assert abs(r_plain) > 0.95

    # 3. Ciphertext correlation should collapse to ~0
    r_cipher = compute_adjacent_sample_correlation(c_pcm)
    assert abs(r_cipher) < 0.03, f"Expected low correlation < 0.03, got {r_cipher}"

    # 4. Differential sensitivity: flip 1 sample in plaintext
    pcm_plain_flipped = list(pcm_plain)
    pcm_plain_flipped[0] ^= 1

    c_bytes_flipped, tag2 = cipher.encrypt_frame(pcm_plain_flipped, ks)
    c_pcm_flipped = bytes_to_pcm(c_bytes_flipped)

    nscr, uaci = compute_nscr_uaci(c_pcm, c_pcm_flipped)
    assert nscr > 99.0, f"Expected NSCR > 99%, got {nscr}%"
    assert 30.0 < uaci < 37.0, f"Expected UACI ~33.5%, got {uaci}%"

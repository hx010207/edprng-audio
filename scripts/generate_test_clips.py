"""
Procedural Audio Clip Generator for Section 8.1 Evaluation.

Paper Section 8.1:
  Generates 8 test clips (2 seconds long, mono, 16-bit PCM, 8 kHz sample rate = 16,000 samples = 32,000 bytes):
    1. Multi-formant speech-like signal (500, 1500, 2500 Hz formants)
    2. Sustained musical chord (C-major chord: C4, E4, G4 + harmonics)
    3. Pure tone (1000 Hz sine wave)
    4. Linear frequency chirp (200 Hz -> 3800 Hz sweep)
    5. Amplitude-modulated tone (1000 Hz carrier, 5 Hz AM)
    6. Broadband percussive/noise signal (white noise)
    7. Voiced-speech simulation (harmonic series f0=120Hz + formant envelope)
    8. Whispered-speech simulation (unvoiced noise + formant envelope)
"""

import os
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

SAMPLE_RATE = 8000
DURATION = 2.0
N_SAMPLES = int(SAMPLE_RATE * DURATION)  # 16000 samples


def generate_speech_multiformant() -> np.ndarray:
    """Clip 1: Multi-formant speech-like signal (500, 1500, 2500 Hz)."""
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    s1 = 0.5 * np.sin(2 * np.pi * 500.0 * t)
    s2 = 0.3 * np.sin(2 * np.pi * 1500.0 * t)
    s3 = 0.2 * np.sin(2 * np.pi * 2500.0 * t)
    sig = s1 + s2 + s3
    sig = sig / np.max(np.abs(sig)) * 28000.0
    return sig.astype(np.int16)


def generate_musical_chord() -> np.ndarray:
    """Clip 2: Sustained C-major chord (C4, E4, G4 + harmonics)."""
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    freqs = [261.63, 329.63, 392.00]
    sig = np.zeros(N_SAMPLES)
    for f in freqs:
        sig += np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t)
    sig = sig / np.max(np.abs(sig)) * 28000.0
    return sig.astype(np.int16)


def generate_pure_tone() -> np.ndarray:
    """Clip 3: Pure tone (1000 Hz sine wave)."""
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    sig = 28000.0 * np.sin(2 * np.pi * 1000.0 * t)
    return sig.astype(np.int16)


def generate_frequency_chirp() -> np.ndarray:
    """Clip 4: Linear frequency chirp (200 Hz to 3800 Hz)."""
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    f0, f1 = 200.0, 3800.0
    phase = 2 * np.pi * (f0 * t + 0.5 * (f1 - f0) / DURATION * t**2)
    sig = 28000.0 * np.sin(phase)
    return sig.astype(np.int16)


def generate_am_tone() -> np.ndarray:
    """Clip 5: Amplitude-modulated tone (1000 Hz carrier, 5 Hz AM)."""
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    carrier = np.sin(2 * np.pi * 1000.0 * t)
    modulator = 0.5 * (1.0 + np.sin(2 * np.pi * 5.0 * t))
    sig = 28000.0 * carrier * modulator
    return sig.astype(np.int16)


def generate_percussive_noise(seed: int = 42) -> np.ndarray:
    """Clip 6: Broadband percussive/noise signal."""
    rng = np.random.default_rng(seed)
    sig = rng.uniform(-28000.0, 28000.0, N_SAMPLES)
    return sig.astype(np.int16)


def generate_voiced_speech() -> np.ndarray:
    """Clip 7: Voiced-speech simulation (f0=120Hz + formant shaping)."""
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    f0 = 120.0
    sig = np.zeros(N_SAMPLES)
    for h in range(1, 30):
        freq = h * f0
        if freq < 3800.0:
            env = np.exp(-((freq - 500.0) ** 2) / (2 * 100**2)) + \
                  np.exp(-((freq - 1500.0) ** 2) / (2 * 150**2)) + \
                  np.exp(-((freq - 2500.0) ** 2) / (2 * 200**2))
            sig += env * np.sin(2 * np.pi * freq * t)
    sig = sig / np.max(np.abs(sig)) * 28000.0
    return sig.astype(np.int16)


def generate_whispered_speech(seed: int = 42) -> np.ndarray:
    """Clip 8: Whispered-speech simulation (formant noise)."""
    rng = np.random.default_rng(seed + 81)
    noise = rng.uniform(-1.0, 1.0, N_SAMPLES)
    t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)
    env = np.exp(-((t - 1.0) ** 2) / 0.5)
    sig = noise * (0.5 + 0.5 * env)
    sig = sig / np.max(np.abs(sig)) * 28000.0
    return sig.astype(np.int16)


def generate_all_test_clips(seed: int = 42) -> Dict[str, np.ndarray]:
    """Generate dict of 8 synthetic test clips (Section 8.1)."""
    return {
        "Speech (multi-formant)": generate_speech_multiformant(),
        "Musical chord": generate_musical_chord(),
        "Pure tone": generate_pure_tone(),
        "Frequency chirp": generate_frequency_chirp(),
        "AM tone": generate_am_tone(),
        "Percussive noise": generate_percussive_noise(seed=seed),
        "Voiced speech": generate_voiced_speech(),
        "Whispered speech": generate_whispered_speech(seed=seed),
    }

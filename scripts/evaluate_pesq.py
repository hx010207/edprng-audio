#!/usr/bin/env python3
"""
PESQ (Perceptual Evaluation of Speech Quality) evaluation for ECGA-IDPRNG-A.
Evaluates decrypted audio quality against original plaintext with bit-for-bit verification.

Usage:
    python scripts/evaluate_pesq.py --corpus data/LibriSpeech/dev-clean --output results/pesq_results.json
    python scripts/evaluate_pesq.py --corpus data/LibriSpeech/dev-clean --output results/pesq_results.json --max-utterances 100

Requirements:
    pip install pesq soundfile

Note: PESQ requires sampling rate of 8000 Hz (narrowband) or 16000 Hz (wideband).
Since our pipeline uses 8 kHz, we use narrowband (nb) mode.
PESQ MOS-LQO range: -0.5 to 4.5. Score ~4.549 = imperceptible degradation (lossless).
"""

import argparse
import json
import numpy as np
import os
import sys
from pathlib import Path

import soundfile as sf
from scipy.signal import resample_poly
from pesq import pesq

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecga.pipeline import AudioFrameCipher
from ecga.keyexchange import derive_demo_session_key


def load_corpus_utterances(corpus_dir: str, max_utterances: int = None):
    """
    Load audio utterances from a corpus directory (supports FLAC and WAV).

    Returns list of (filepath, samples_int16, sample_rate) tuples.
    All audio is resampled to exactly 8000 Hz and cast to int16.
    """
    corpus_path = Path(corpus_dir)
    # Support both FLAC (LibriSpeech) and WAV
    audio_files = sorted(
        list(corpus_path.rglob("*.flac")) + list(corpus_path.rglob("*.wav"))
    )
    if max_utterances:
        audio_files = audio_files[:max_utterances]

    utterances = []
    for audio_file in audio_files:
        # soundfile handles FLAC, WAV, OGG etc. natively
        samples, sr = sf.read(str(audio_file))

        # Convert stereo to mono
        if len(samples.shape) > 1:
            samples = samples.mean(axis=1)

        # sf.read returns float64 by default for FLAC; convert to int16
        if samples.dtype != np.int16:
            if np.issubdtype(samples.dtype, np.floating):
                samples = (samples * 32767).astype(np.int16)
            else:
                samples = samples.astype(np.int16)

        # Resample to exactly 8000 Hz using exact rational ratio
        if sr != 8000:
            samples = resample_poly(samples, 8000, sr).astype(np.int16)
            sr = 8000

        utterances.append((str(audio_file), samples, sr))

    return utterances


def evaluate_pesq_on_utterance(cipher, session_key, samples, sr=8000):
    """
    Encrypt -> decrypt an utterance frame-by-frame, verify bit-for-bit lossless
    reconstruction, and compute PESQ on each valid frame.

    Args:
        cipher: AudioFrameCipher instance.
        session_key: 32-byte session key for this utterance.
        samples: np.ndarray of int16 PCM samples at 8 kHz.
        sr: Sample rate (must be 8000).

    Returns:
        Dict with per-frame PESQ scores, bit-for-bit status, and aggregate statistics.
    """
    # Ensure int16 for PESQ compatibility
    if samples.dtype != np.int16:
        samples = samples.astype(np.int16)

    frame_size = 16000  # 2 seconds at 8 kHz
    pesq_scores = []
    bit_for_bit_flags = []
    total_diff_samples = 0

    for i in range(0, len(samples), frame_size):
        frame = samples[i:i + frame_size]

        # Skip if frame is too short for PESQ (needs at least ~160 samples = 20ms at 8kHz)
        if len(frame) < 160:
            print(f"  Skipping short final frame ({len(frame)} samples < 160 threshold)")
            pesq_scores.append(None)
            continue

        # Pad to full frame_size if needed (for cipher frame boundary), but evaluate only original samples
        if len(frame) < frame_size:
            frame_padded = np.pad(frame, (0, frame_size - len(frame)), mode='constant')
            ciphertext_bytes, hmac_tag = cipher.encrypt_frame(frame_padded.tolist(), session_key)
            decrypted_samples = cipher.decrypt_frame(ciphertext_bytes, hmac_tag, session_key)
            decrypted_frame = np.array(decrypted_samples[:len(frame)], dtype=np.int16)
        else:
            ciphertext_bytes, hmac_tag = cipher.encrypt_frame(frame.tolist(), session_key)
            decrypted_samples = cipher.decrypt_frame(ciphertext_bytes, hmac_tag, session_key)
            decrypted_frame = np.array(decrypted_samples, dtype=np.int16)

        plaintext_arr = np.array(frame, dtype=np.int16)

        # BIT-FOR-BIT VERIFICATION
        is_identical = np.array_equal(plaintext_arr, decrypted_frame)
        bit_for_bit_flags.append(bool(is_identical))

        if not is_identical:
            diff_count = np.sum(plaintext_arr != decrypted_frame)
            max_diff = np.max(np.abs(plaintext_arr - decrypted_frame))
            total_diff_samples += int(diff_count)
            print(f"  WARNING: {diff_count} samples differ! Max diff: {max_diff}")

        # Compute PESQ (narrowband, 8 kHz)
        try:
            score = pesq(sr, plaintext_arr, decrypted_frame, 'nb')
            pesq_scores.append(score)
        except Exception as e:
            print(f"  PESQ error on frame {i // frame_size}: {e}")
            pesq_scores.append(None)

    valid_scores = [s for s in pesq_scores if s is not None]
    all_identical = bool(all(bit_for_bit_flags)) if bit_for_bit_flags else False

    return {
        'pesq_scores_per_frame': pesq_scores,
        'pesq_mean': float(np.mean(valid_scores)) if valid_scores else None,
        'pesq_std': float(np.std(valid_scores)) if valid_scores else None,
        'num_frames': len(pesq_scores),
        'num_valid_frames': len(valid_scores),
        'bit_for_bit_identical': all_identical,
        'diff_samples_count': total_diff_samples
    }


def main():
    parser = argparse.ArgumentParser(description='PESQ evaluation for ECGA-IDPRNG-A')
    parser.add_argument('--corpus', type=str, required=True,
                        help='Path to corpus directory containing FLAC/WAV files')
    parser.add_argument('--output', type=str, default='results/pesq_results.json',
                        help='Output JSON file for results')
    parser.add_argument('--max-utterances', type=int, default=None,
                        help='Maximum number of utterances to evaluate')
    parser.add_argument('--seed', type=str, default='pesq_eval_session',
                        help='Base seed string for per-utterance session key derivation')
    args = parser.parse_args()

    print(f"Loading corpus from: {args.corpus}")
    utterances = load_corpus_utterances(args.corpus, args.max_utterances)
    print(f"Loaded {len(utterances)} utterances")

    if not utterances:
        print("ERROR: No audio files found. Check corpus path.")
        sys.exit(1)

    cipher = AudioFrameCipher()

    results = {
        'config': {
            'corpus': args.corpus,
            'max_utterances': args.max_utterances,
            'actual_utterances': len(utterances),
            'seed_base': args.seed,
            'sampling_rate': 8000,
            'pesq_mode': 'nb',
            'frame_size': 16000
        },
        'utterances': []
    }

    all_pesq_means = []
    all_bit_identical = True

    for idx, (filepath, samples, sr) in enumerate(utterances):
        print(f"\n[{idx+1}/{len(utterances)}] Evaluating: {filepath}")
        print(f"  Duration: {len(samples)/sr:.2f}s, Samples: {len(samples)}")

        # Per-utterance ephemeral key for statistical independence
        session_key = derive_demo_session_key(
            f"{args.seed}_{idx}_{Path(filepath).stem}"
        )

        utt_result = evaluate_pesq_on_utterance(cipher, session_key, samples, sr)
        utt_result['filepath'] = filepath
        utt_result['num_samples'] = int(len(samples))
        results['utterances'].append(utt_result)

        if not utt_result['bit_for_bit_identical']:
            all_bit_identical = False

        if utt_result['pesq_mean'] is not None:
            all_pesq_means.append(utt_result['pesq_mean'])
            print(f"  PESQ mean: {utt_result['pesq_mean']:.4f} +/- {utt_result['pesq_std']:.4f} | Bit-for-bit: {utt_result['bit_for_bit_identical']}")
        else:
            print(f"  PESQ: FAILED | Bit-for-bit: {utt_result['bit_for_bit_identical']}")

    if all_pesq_means:
        results['aggregate'] = {
            'pesq_mean_overall': float(np.mean(all_pesq_means)),
            'pesq_std_overall': float(np.std(all_pesq_means)),
            'pesq_min': float(np.min(all_pesq_means)),
            'pesq_max': float(np.max(all_pesq_means)),
            'num_utterances_evaluated': len(all_pesq_means),
            'bit_for_bit_identical_all': all_bit_identical
        }
        print(f"\n{'='*60}")
        print(f"OVERALL PESQ & RECONSTRUCTION RESULTS ({len(all_pesq_means)} utterances)")
        print(f"  Bit-for-bit Identical: {all_bit_identical}")
        print(f"  Mean PESQ (NB, 8kHz):  {results['aggregate']['pesq_mean_overall']:.4f}")
        print(f"  Std PESQ:              {results['aggregate']['pesq_std_overall']:.4f}")
        print(f"  Min PESQ:              {results['aggregate']['pesq_min']:.4f}")
        print(f"  Max PESQ:              {results['aggregate']['pesq_max']:.4f}")
        print(f"{'='*60}")

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {args.output}")


if __name__ == '__main__':
    main()

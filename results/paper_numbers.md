# Paper numbers — authoritative values after the v2 code fixes

Regenerated 2026-11-15 from `scripts/run_corpus_evaluation.py --n-utterances 100`
on the revised cipher (domain-separated subkeys, per-frame counter, keystream
whitening, fixed key exchange). Use ONE dataset per sentence — do not mix the
synthetic 8-clip numbers with the LibriSpeech 100-utterance numbers.

## LibriSpeech dev-clean, N = 100 utterances (PRIMARY — use in Abstract, C1, Conclusion)

| Metric | Plaintext (mean ± std) | Ciphertext (mean ± std) |
|---|---|---|
| Normalised spectral entropy H_s | 0.719 ± 0.062 | 0.953 ± 0.001 |
| Spectral flatness | 0.050 ± 0.047 | 0.557 ± 0.005 |
| Byte entropy (bits) | 6.958 ± 0.421 | 7.994 ± 0.001 |
| Adjacent-sample correlation | 0.886 ± 0.105 | −0.001 ± 0.009 |
| STOI (ciphertext) | — | 0.348 ± 0.070 |
| STOI (decrypted) | — | 1.000 |
| PESQ (decrypted, NB MOS-LQO) | — | 4.549 |
| NSCR Part A (plaintext-flip) | — | 99.40 % ± 5.93 |
| UACI Part A (plaintext-flip) | — | 33.20 % ± 2.00 |
| NSCR Part B (key-flip) | — | 99.999 % ± 0.003 |
| UACI Part B (key-flip) | — | 33.34 % ± 0.17 |
| Bit-for-bit recovery | — | 100 % (all frames) |

Std values above are population std (ddof=0) as emitted by the script; state
"population std" in captions, or switch the script to ddof=1 before final.

## Known text/reference corrections (not measurement-dependent)

| Location | Old | Correct |
|---|---|---|
| Abstract plaintext H_s | 0.44 ± 0.40 (synthetic) | 0.719 ± 0.062 (LibriSpeech) |
| Abstract adjacent corr | 0.575 → 0.006 (synthetic) | 0.886 → −0.001 (LibriSpeech) |
| Abstract UACI | 33.55 % | 33.20 % (Part A) / 33.34 % (Part B) |
| UACI ideal (16-bit samples) | 33.46 % | 33.33 % = 100·(M+1)/(3M), M=65536 |
| UACI ideal (8-bit bytes) | — | 33.4635 % |
| LibriSpeech total duration | ≈ 54 min | recompute from audio (297×2 s ≈ 9.9 min of framed audio) |
| Security level | "exactly 2^256" | 256-bit key, ~128-bit security (P-256 ECDH) |
| Worked-example session label | "...||demo||NA=7b1e||NB=d92a" | "...::demo::NA=7b1e::NB=d92a" (hashes to 1697fac7) |
| PESQ scale | −0.5..4.5 (P.862) | MOS-LQO P.862.1 (≈1.02..4.55); 4.549 is MOS-LQO |
| NIST count (Conclusion) | "passes 13 of 14" | Layer 2 raw 11/14; +Layer 3 13/14; full ciphertext 14/14 |
| Flatness white-noise ref | "expected value 0.556" | e^(−γ) ≈ 0.5615 for a raw periodogram |

## Still to regenerate (needs heavy compute / hardware — NOT done today)

- NIST SP 800-22 multi-sequence run (100 × 10^6 bits per stage, raw/whitened/full)
- GA 8-run report with full Lyapunov spectrum + random-search baseline
- ESP32 / Cortex-M on-device timing and memory (needs physical hardware)
- C reference determinism check across compilers/flags

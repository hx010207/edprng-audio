# ECGA-IDPRNG-A: Hyperchaotic Speech Encryption Framework for IoT Audio Devices

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A complete, production-quality Python implementation of the **ECGA-IDPRNG-A** 5-layer audio-frame encryption scheme described in the research paper:

> **Spectral Flattening as a Security Guarantee: Hyperchaotic Speech Encryption with Constrained Genetic Keystream Certification for IoT Audio Devices**

---

## ⚠️ Security Disclaimer

> [!CAUTION]
> **RESEARCH PROTOTYPE DISCLAIMER**
> This repository contains an academic reference implementation created for audio security research and reproducibility verification. It has **not** undergone an independent commercial security audit. **Do not use this software for sensitive or production cryptographic deployments.**

---

## 🔒 Architecture Overview

ECGA-IDPRNG-A is a 5-layer audio-frame cipher operating on little-endian byte serializations of pulse-code-modulated (PCM) speech:

```
+-----------------------------------------------------------------------------------+
|                            Session Setup (Layer 1)                                |
|  ECDSA-authenticated ECDH (P-256) Key Agreement -> Session Key Ks                 |
|  (3, 5) Shamir Threshold Secret Sharing over GF(2^256) Escrow                     |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                         Per-Frame Encryption (Layers 2-5)                         |
|                                                                                   |
|  Plaintext PCM S ──► LE Bytes P ──► L4 Permutation q = π(P) (Logistic Map)       |
|                                                │                                  |
|  L2 Hyperchaotic Keystream KS ─────────────────┼──► L5 Forward ARX Pass           |
|  L3 Rule-30 Mask CA ───────────────────────────┘    fi = (((qi ⊞ KSi) ⊕ CAi) ≪ 3) ⊞ fi-1
|                                                │                                  |
|                                                ▼                                  |
|                                     L5 Backward ARX Pass                          |
|                                     ci = (fi ⊞ ci+1) ≪ 5,  cL = 0x3C              |
|                                                │                                  |
|                                                ▼                                  |
|                                     HMAC-SHA256 Tag τ                             |
+-----------------------------------------------------------------------------------+
```

### The 5 Cipher Layers

1. **Layer 1: Key Agreement & Escrow**
   - **ECDSA-authenticated ECDH (P-256)**: Computes shared secret point $Z = n_A Q_B = n_B Q_A$ and derives session key $K_s = \text{SHA-256}(x(Z) \| N_A \| N_B)$ (Eq. 3).
   - **(3,5) Shamir Escrow**: Splits $K_s$ into 5 shares over $GF(2^{256})$ (Eq. 7). Any 3 custodians can reconstruct $K_s$.

2. **Layer 2: Genetically Certified Hyperchaotic Keystream**
   - **4D Hyperchaotic System** (Eq. 4):
     $$\dot{x} = a(y - x) + w, \quad \dot{y} = cx - xz - y, \quad \dot{z} = xy - bz, \quad \dot{w} = -dx + ew$$
   - **Integration**: Integrated with 4th-order Runge-Kutta ($h = 0.01$), 1000 warm-up steps, and `fmod(state, 1000)` state reduction.
   - **Keystream Generation** (Eq. 8): $KS_i = \lfloor (|\xi_i| - \lfloor |\xi_i| \rfloor) \cdot 2^{32} \rfloor \bmod 256$, cycling through $(x, y, z, w)$.
   - **Genetic Algorithm Search**: Optimizes coefficients $\theta = (a, b, c, d, e)$ with a **hard constraint** discarding any candidate with largest Lyapunov exponent $\lambda_1 \le 0$ before scoring (Eq. 10). Deployed parameters: $\theta^* = (30.175, 3.585, 29.642, 6.168, 0.622)$.

3. **Layer 3: Rule-30 Cellular Automaton Diffusion Mask**
   - 512-cell binary ring seeded from $\text{SHA-256}(K_s \| \text{"CA"})$ and evolved 512 steps according to Rule 30 (Eq. 5): $c_i^{t+1} = c_{i-1}^t \oplus (c_i^t \lor c_{i+1}^t)$.

4. **Layer 4: Logistic-Map Byte Permutation**
   - Chaotic map $x_{k+1} = 3.999 x_k (1 - x_k)$ (Eq. 6) with 50 warm-up iterations.
   - Permutation vector $\pi = \text{argsort}(x_0, \dots, x_{L-1})$ (Eq. 11) shuffles bytes $q = \pi(P)$.

5. **Layer 5: Two-Pass ARX Transform with HMAC Authentication**
   - **Forward Pass** (Eq. 12): $f_i = (((q_i \boxplus KS_i) \oplus CA_i) \ll 3) \boxplus f_{i-1} \bmod 256$, with $f_{-1} = \text{0xA5}$.
   - **Backward Pass** (Eq. 13): $c_i = ((f_i \boxplus c_{i+1}) \ll 5) \bmod 256$, with $c_L = \text{0x3C}$.
   - **Integrity Tag** (Eq. 14): $\tau = \text{HMAC-SHA256}_{K_s}(C)$.

6. **Active-Stream Lyapunov (ASL) Monitor**
   - Periodically monitors local trajectory divergence of live stream bytes to detect and prevent orbit collapse.

---

## 📁 Repository Structure

```
ecga-idprng-a/
├── src/ecga/
│   ├── __init__.py
│   ├── __main__.py
│   ├── keyexchange.py       # Layer 1: ECDSA/ECDH handshake (P-256)
│   ├── shamir.py           # Layer 1 Escrow: (k,n) Shamir over GF(2^256) & GF(257)
│   ├── hyperchaos.py       # Layer 2: RK4 integrator & keystream generation
│   ├── genetic.py          # Layer 2 Certification: GA with hard Lyapunov culling
│   ├── cellular_automaton.py  # Layer 3: Rule-30 diffusion mask
│   ├── permutation.py      # Layer 4: Logistic map permutation
│   ├── arx.py              # Layer 5: Two-pass ARX + HMAC-SHA256 tag
│   ├── pipeline.py         # Top-level encrypt_frame() / decrypt_frame()
│   ├── monitor.py          # Active-stream Lyapunov monitor
│   └── cli.py              # WAV file encryption/decryption CLI
├── tests/
│   ├── test_worked_example.py  # Section 6 byte-for-byte reproduction
│   ├── test_shamir.py          # Table 2 GF(257) & GF(2^256) validation
│   ├── test_statistics.py      # Entropy, correlation, NSCR, UACI
│   └── test_nist_sp800_22.py   # 14 NIST SP 800-22 statistical tests
├── scripts/
│   ├── generate_test_clips.py  # 8 procedural test clips (Sec 8.1)
│   ├── run_full_evaluation.py  # Reproduces Tables 5-15 & Figures 3-6
│   └── benchmark_throughput.py # Throughput comparison vs AES-128-GCM
├── results/                # Output plots and generated audio clips
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

## ⚡ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ecga-idprng-a
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Quick Start (CLI & Python API)

### Command-Line Interface (WAV Files)

Encrypt a 16-bit PCM WAV file:
```bash
python -m ecga encrypt --in sample.wav --out sample.enc
```

Decrypt the encrypted file back to pristine WAV:
```bash
python -m ecga decrypt --in sample.enc --out recovered.wav
```

### Python API

```python
from ecga.pipeline import AudioFrameCipher
from ecga.keyexchange import derive_demo_session_key

# 1. Initialize cipher and derive session key
cipher = AudioFrameCipher()
session_key = derive_demo_session_key("my_session_key")

# 2. Input 16-bit PCM audio samples
pcm_samples = [1200, -3400, 15000, -800, 25, 32000, -16000, 5000]

# 3. Encrypt audio frame
ciphertext_bytes, hmac_tag = cipher.encrypt_frame(pcm_samples, session_key)

# 4. Decrypt audio frame
decrypted_samples = cipher.decrypt_frame(ciphertext_bytes, hmac_tag, session_key)
assert decrypted_samples == pcm_samples
```

---

## 🧪 Running Unit Tests & Section 6 Worked Example

Execute the test suite using `pytest`:

```bash
pytest -v tests/
```

### Section 6 Worked Example Verification
`tests/test_worked_example.py` reproduces Section 6 of the paper by hand:
- Plaintext PCM: $S = (1200, -3400, 15000, -800, 25, 32000, -16000, 5000)$
- Session Key: $K_s = \text{SHA-256}(\text{"ECGA-IDPRNG-A::demo::NA=7b1e::NB=d92a"})$
- Serialization $P$, Keystream $KS$, Mask $CA$, Permutation $\pi$, Permuted $Q$, Forward Pass $f_i$ (Table 3), Backward Pass $c_i$ (Table 4), and Reinterpreted $C_{\text{pcm}}$ are verified byte-for-byte.

---

## 📊 Full Evaluation & Figure Reproduction

Run the full evaluation script to reproduce Tables 5–15 and Figures 3–6:

```bash
python scripts/generate_test_clips.py
python scripts/run_full_evaluation.py
python scripts/benchmark_throughput.py
```

Generated plots are saved into `results/`:
- `results/fig3_ga_convergence.png`: Genetic algorithm convergence over 8 independent runs
- `results/fig4_spectrogram_comparison.png`: Plaintext vs Ciphertext speech spectrogram
- `results/fig5_spectral_statistics.png`: Spectral entropy collapse & flatness
- `results/fig6_speech_encryption_analysis.png`: Waveforms, scatter plots, and byte histograms

### Summary of Reproduced Security Metrics

| Security Metric | Original Plaintext | ECGA-IDPRNG-A Ciphertext | Target / Ideal |
|---|---|---|---|
| **Normalised Spectral Entropy ($H_s$)** | $0.440 \pm 0.398$ | **$0.953 \pm 0.001$** | $1.000$ (White Noise) |
| **Spectral Flatness** | $0.157 \pm 0.229$ | **$0.556 \pm 0.003$** | ~$0.556$ |
| **Shannon Byte Entropy ($H$)** | $6.775 \pm 1.688$ | **$7.99435 \pm 0.00036$** | $8.000$ bits/byte |
| **Adjacent-Sample Correlation ($r$)** | $0.575 \pm 0.349$ | **$0.00613 \pm 0.00620$** | $0.000$ |
| **NSCR (Plaintext / Key Flip)** | N/A | **$100.00\%$ / $99.999\%$** | $100.00\%$ |
| **UACI (Plaintext / Key Flip)** | N/A | **$33.55\%$ / $33.30\%$** | $33.46\%$ |
| **NIST SP 800-22 Battery** | N/A | **11–13 / 14 Passed** | 13/14 Passed |

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

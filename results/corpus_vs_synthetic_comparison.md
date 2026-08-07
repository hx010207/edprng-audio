# Side-by-Side Comparison: Real Speech Corpus vs Synthetic Clips

| Metric | Paper Synthetic Claims | Real Speech (`LibriSpeech (TIMIT unavailable)`) | Delta / Finding |
|---|---|---|---|
| **Ciphertext Spectral Entropy ($H_s$)** | $0.953 \pm 0.001$ | **$0.95282 \pm 0.00069$** | Ideal spectral flattening holds on real speech |
| **Ciphertext Spectral Flatness** | $0.5568 \pm 0.0032$ | **$0.55613 \pm 0.00494$** | Matches white-noise floor threshold |
| **Shannon Byte Entropy ($H$)** | $7.99435 \pm 0.00036$ | **$7.99429 \pm 0.00061$** | Uniform 8-bit randomness confirmed |
| **Adjacent Correlation ($r$)** | $0.00613 \pm 0.00620$ | **$-0.00085 \pm 0.00738$** | Temporal redundancy completely erased |
| **Plaintext NSCR / UACI** | $100.00\% / 33.55\%$ | **$100.00\% / 33.44\%$** | Complete single-bit avalanche effect |
| **STOI Intelligibility Score** | $0.216$ (Speech) / $0.009$ (Voiced) | **$0.3451 \pm 0.0663$** | Real audio is completely unintelligible ($< 0.75$) |

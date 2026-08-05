# Side-by-Side Comparison: Real Speech Corpus vs Synthetic Clips

| Metric | Paper Synthetic Claims | Real Speech (`LibriSpeech (TIMIT unavailable)`) | Delta / Finding |
|---|---|---|---|
| **Ciphertext Spectral Entropy ($H_s$)** | $0.953 \pm 0.001$ | **$0.95273 \pm 0.00040$** | Ideal spectral flattening holds on real speech |
| **Ciphertext Spectral Flatness** | $0.5568 \pm 0.0032$ | **$0.55527 \pm 0.00395$** | Matches white-noise floor threshold |
| **Shannon Byte Entropy ($H$)** | $7.99435 \pm 0.00036$ | **$7.99424 \pm 0.00044$** | Uniform 8-bit randomness confirmed |
| **Adjacent Correlation ($r$)** | $0.00613 \pm 0.00620$ | **$0.00044 \pm 0.00645$** | Temporal redundancy completely erased |
| **Plaintext NSCR / UACI** | $100.00\% / 33.55\%$ | **$100.00\% / 33.39\%$** | Complete single-bit avalanche effect |
| **STOI Intelligibility Score** | $0.216$ (Speech) / $0.009$ (Voiced) | **$0.3485 \pm 0.0554$** | Real audio is completely unintelligible ($< 0.75$) |

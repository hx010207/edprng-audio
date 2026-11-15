# Side-by-Side Comparison: Real Speech Corpus vs Synthetic Clips

| Metric | Paper Synthetic Claims | Real Speech (`LibriSpeech (TIMIT unavailable)`) | Delta / Finding |
|---|---|---|---|
| **Ciphertext Spectral Entropy ($H_s$)** | $0.953 \pm 0.001$ | **$0.95295 \pm 0.00066$** | Ideal spectral flattening holds on real speech |
| **Ciphertext Spectral Flatness** | $0.5568 \pm 0.0032$ | **$0.55745 \pm 0.00491$** | Matches white-noise floor threshold |
| **Shannon Byte Entropy ($H$)** | $7.99435 \pm 0.00036$ | **$7.99419 \pm 0.00050$** | Uniform 8-bit randomness confirmed |
| **Adjacent Correlation ($r$)** | $0.00613 \pm 0.00620$ | **$-0.00134 \pm 0.00858$** | Temporal redundancy completely erased |
| **Plaintext NSCR / UACI** | $100.00\% / 33.55\%$ | **$99.40\% / 33.20\%$** | Complete single-bit avalanche effect |
| **STOI Intelligibility Score** | $0.216$ (Speech) / $0.009$ (Voiced) | **$0.3482 \pm 0.0696$** | Real audio is completely unintelligible ($< 0.75$) |
| **PESQ Decrypted Quality** | N/A (new metric) | **$4.5486 \pm 0.0000$** | Lossless decryption confirmed (narrowband max 4.549) |
| **STOI Decrypted Quality** | N/A (new metric) | **$1.0000 \pm 0.0000$** | Perfect round-trip reconstruction (1.0000) |

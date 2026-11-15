# Cover Letter — Computers & Security

Dear Editor-in-Chief,

We are pleased to submit our manuscript, *"Spectral Flattening as a Security
Guarantee: Hyperchaotic Speech Encryption with Constrained Genetic Keystream
Certification for IoT Audio Devices,"* for consideration as a research article
in *Computers & Security*.

The work argues that confidentiality for digital speech should be judged by a
spectral, perceptual criterion — the complete flattening of formant and harmonic
structure — rather than by byte-level randomness alone, and it shows that a
cipher can score near-maximal byte entropy while its spectrogram still leaks
intelligible speech. We present ECGA-IDPRNG-A, a five-layer, resource-constrained
framework combining an ECDSA-authenticated P-256 key agreement, a per-frame
counter, domain-separated subkeys, a $(3,5)$ Shamir threshold escrow, a
Lyapunov-certified hyperchaotic keystream (whitened through a NIST-standard XOF),
cellular-automaton diffusion, chaotic permutation, and an authenticated two-pass
ARX transform. We provide reduction-based arguments for IND-CPA confidentiality,
ciphertext integrity, authenticated key exchange, forward secrecy, and threshold
recovery, and we evaluate the scheme with spectral, statistical, differential,
and perceptual metrics on 100 LibriSpeech utterances in addition to procedural
stress-test signals. A public reference implementation with the full test and
evaluation suite accompanies the paper.

We believe the manuscript fits the scope of *Computers & Security*: it addresses
practical, deployable confidentiality for constrained IoT audio endpoints,
positions the scheme honestly against standard baselines (AES-128-GCM,
ChaCha20-Poly1305, SRTP), and pairs a security analysis with a runnable
artifact.

This manuscript is original, has not been published elsewhere, and is not under
consideration by any other journal. An earlier version was declined by
*Multimedia Tools and Applications* as outside that journal's scope, without peer
review. All authors have approved the submission and declare no competing
interests.

Thank you for your consideration.

Sincerely,
The authors

"""
ECGA-IDPRNG-A: 5-Layer Hyperchaotic Audio-Frame Cipher for IoT Audio Devices.

Modules:
    keyexchange: ECDSA-authenticated ECDH (P-256) key agreement.
    shamir: (k, n) Shamir threshold secret sharing over GF(2^256) and GF(257).
    hyperchaos: RK4-integrated 4D hyperchaotic generator & keystream generation.
    genetic: GA coefficient optimization with hard Lyapunov culling.
    cellular_automaton: Rule-30 cellular automaton 512-cell diffusion mask.
    permutation: Logistic-map byte permutation.
    arx: Two-pass ARX transform with HMAC-SHA256 authentication.
    pipeline: Top-level audio frame encryption and decryption.
    monitor: Active-stream Lyapunov monitor (ASL).
"""

__version__ = "1.0.0"

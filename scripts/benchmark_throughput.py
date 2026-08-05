"""
Throughput & Timing Benchmark Script (Table 14).

Paper Section 8.10 & Table 14:
  Compares per-frame execution time and throughput on a 32,000-byte frame (2s, 8kHz 16-bit):
    - ECGA-IDPRNG-A (transform only)
    - ECGA-IDPRNG-A (incl. key schedule)
    - AES-128-GCM (reference baseline)
"""

import os
import sys
import time
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecga.keyexchange import KeyExchangeParty, derive_demo_session_key
from ecga.pipeline import AudioFrameCipher


def benchmark_ecga_and_aes():
    print("\n==================================================================")
    print("ECGA-IDPRNG-A Throughput & Timing Benchmark (Table 14)")
    print("==================================================================")

    # 32000 bytes frame
    frame_size = 32000
    pcm_bytes = os.urandom(frame_size)

    cipher = AudioFrameCipher()
    ks = derive_demo_session_key("benchmark_session_key")

    # 1. Transform only (Layers 2-5 per frame)
    iterations = 20
    t0 = time.perf_counter()
    for _ in range(iterations):
        c_bytes, tag = cipher.encrypt_frame(pcm_bytes, ks)
    t1 = time.perf_counter()
    transform_only_ms = ((t1 - t0) / iterations) * 1000.0
    transform_only_kbps = (frame_size / 1024.0) / ((t1 - t0) / iterations)

    # 2. Incl. Key Schedule (Layer 1 ECDH + Layers 2-5)
    t0 = time.perf_counter()
    for _ in range(iterations):
        alice = KeyExchangeParty()
        bob = KeyExchangeParty()
        pub_a, n_a, sig_a = alice.generate_ephemeral_handshake(b"nonce_a_12345678")
        pub_b, n_b, sig_b = bob.generate_ephemeral_handshake(b"nonce_b_12345678")
        ks_fresh = alice.compute_session_key(bob.long_term_public_key, pub_b, n_b, sig_b)
        c_bytes, tag = cipher.encrypt_frame(pcm_bytes, ks_fresh)
    t1 = time.perf_counter()
    incl_key_ms = ((t1 - t0) / iterations) * 1000.0
    incl_key_kbps = (frame_size / 1024.0) / ((t1 - t0) / iterations)

    # 3. AES-128-GCM reference
    aes_key = AESGCM.generate_key(bit_length=128)
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)

    iterations_aes = 1000
    t0 = time.perf_counter()
    for _ in range(iterations_aes):
        ct = aesgcm.encrypt(nonce, pcm_bytes, None)
    t1 = time.perf_counter()
    aes_ms = ((t1 - t0) / iterations_aes) * 1000.0
    aes_kbps = (frame_size / 1024.0) / ((t1 - t0) / iterations_aes)

    print(f"{'Scheme':42s} | {'Frame time (ms)':16s} | {'Throughput (KB/s)':18s}")
    print("-" * 82)
    print(f"{'ECGA-IDPRNG-A (transform only)':42s} | {transform_only_ms:16.2f} | {transform_only_kbps:18.1f}")
    print(f"{'ECGA-IDPRNG-A (incl. key schedule)':42s} | {incl_key_ms:16.2f} | {incl_key_kbps:18.1f}")
    print(f"{'AES-128-GCM (reference, faster)':42s} | {aes_ms:16.4f} | {aes_kbps:18.1f}")
    print("=" * 82)


if __name__ == "__main__":
    benchmark_ecga_and_aes()

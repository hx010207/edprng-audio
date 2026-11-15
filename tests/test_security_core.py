"""
Regression tests for the v2 correctness fixes:
  - domain-separated subkeys (Algorithm 1)
  - authenticated key exchange: both parties derive the SAME key (Theorem 3)
  - per-frame counter: same plaintext -> different ciphertext (Section 5.5, Thm 1)
  - Encrypt-then-MAC over (session_id || ctr || C): replay/reorder rejected (Thm 2)
  - keystream whitening mode (Remark 1)
"""

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ecga.hyperchaos import HyperchaoticGenerator
from ecga.kdf import derive_subkeys, frame_seed
from ecga.keyexchange import KeyExchangeParty
from ecga.pipeline import AudioFrameCipher


def test_subkeys_distinct_and_deterministic():
    key = secrets.token_bytes(32)
    sk1 = derive_subkeys(key)
    sk2 = derive_subkeys(key)
    assert sk1 == sk2
    vals = [sk1.k_hyper, sk1.k_ca, sk1.k_perm, sk1.k_mac]
    assert all(len(v) == 32 for v in vals)
    assert len(set(vals)) == 4
    # one-bit change in key flips every subkey
    flipped = bytearray(key)
    flipped[0] ^= 1
    sk3 = derive_subkeys(bytes(flipped))
    assert sk3.k_hyper != sk1.k_hyper
    assert sk3.k_ca != sk1.k_ca
    assert sk3.k_perm != sk1.k_perm
    assert sk3.k_mac != sk1.k_mac


def test_subkeys_reject_bad_length():
    with pytest.raises(ValueError):
        derive_subkeys(b"short")


def test_key_exchange_both_parties_agree():
    a = KeyExchangeParty()
    b = KeyExchangeParty()
    pa, na, sa = a.generate_ephemeral_handshake(b"nonce_a_12345678")
    pb, nb, sb = b.generate_ephemeral_handshake(b"nonce_b_12345678")
    ka = a.compute_session_key(b.long_term_public_key, pb, nb, sb)
    kb = b.compute_session_key(a.long_term_public_key, pa, na, sa)
    assert ka == kb
    assert a.session_id == b.session_id
    assert len(ka) == 32

    # two independent runs produce different keys (freshness)
    a2 = KeyExchangeParty()
    b2 = KeyExchangeParty()
    pa2, na2, sa2 = a2.generate_ephemeral_handshake(b"nonce_a_12345678")
    pb2, nb2, sb2 = b2.generate_ephemeral_handshake(b"nonce_b_12345678")
    ka2 = a2.compute_session_key(b2.long_term_public_key, pb2, nb2, sb2)
    assert ka2 != ka


def test_per_frame_counter_freshens_ciphertext():
    cipher = AudioFrameCipher()
    key = secrets.token_bytes(32)
    sid = secrets.token_bytes(16)
    frame = [100] * 2000
    c0, t0 = cipher.encrypt_frame(frame, key, ctr=0, session_id=sid)
    c1, t1 = cipher.encrypt_frame(frame, key, ctr=1, session_id=sid)
    assert c0 != c1
    assert cipher.decrypt_frame(c1, t1, key, ctr=1, session_id=sid) == frame


def test_mac_binds_counter_and_session_id():
    cipher = AudioFrameCipher()
    key = secrets.token_bytes(32)
    sid = secrets.token_bytes(16)
    frame = [100] * 2000
    c1, t1 = cipher.encrypt_frame(frame, key, ctr=1, session_id=sid)
    # replay/reorder under a different counter must fail verification
    with pytest.raises(ValueError):
        cipher.decrypt_frame(c1, t1, key, ctr=2, session_id=sid)
    # different session_id must fail
    with pytest.raises(ValueError):
        cipher.decrypt_frame(c1, t1, key, ctr=1, session_id=secrets.token_bytes(16))
    # one flipped ciphertext bit must fail
    bad = bytearray(c1)
    bad[0] ^= 1
    with pytest.raises(ValueError):
        cipher.decrypt_frame(bytes(bad), t1, key, ctr=1, session_id=sid)


def test_keystream_whitening_modes():
    seed = secrets.token_bytes(32)
    raw = HyperchaoticGenerator(mode="raw").generate_keystream(4096, seed)
    white = HyperchaoticGenerator(mode="whitened").generate_keystream(4096, seed)
    assert raw != white
    # whitened is deterministic for the same seed
    white2 = HyperchaoticGenerator(mode="whitened").generate_keystream(4096, seed)
    assert white == white2


def test_frame_seed_counter_range():
    sub = derive_subkeys(secrets.token_bytes(32))
    with pytest.raises(ValueError):
        frame_seed(sub.k_hyper, b"\x00" * 16, 2**64)

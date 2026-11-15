"""
Key derivation: domain-separated subkeys and per-frame seeds.

Paper Section 5.1 (Algorithm 1, subkey derivation) and Section 5.5 (per-frame
counter). The master session key Ks agreed in Layer 1 is never used directly by
any layer. Instead four domain-separated subkeys are derived with HKDF-SHA256
(RFC 5869):

    K_hyper, K_ca, K_perm, K_mac = HKDF(Ks, info = "ECGA-IDPRNG-A/v2/" + label)

and, for every frame, a per-frame seed is derived from the relevant subkey, the
16-byte session identifier and the 64-bit frame counter:

    frame_key_X = HMAC-SHA256(K_X, "frame" || session_id || ctr)

The per-frame seed makes the keystream, diffusion mask and permutation fresh for
every frame of a session, which is what the IND-CPA reduction (Theorem 1)
requires: without it, every frame of a session would reuse the same KS/CA/pi and
the deterministic ARX passes would be trivially invertible under chosen
plaintext.
"""

from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes, hmac as c_hmac
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_INFO_PREFIX = b"ECGA-IDPRNG-A/v2/"
_SUBKEY_LABELS = (b"hyper", b"ca", b"perm", b"mac")


def hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    """Derive `length` bytes from `ikm` with HKDF-SHA256 (RFC 5869)."""
    return HKDF(
        algorithm=hashes.SHA256(), length=length, salt=salt, info=info
    ).derive(ikm)


@dataclass(frozen=True)
class Subkeys:
    """The four domain-separated 32-byte subkeys derived from the session key."""

    k_hyper: bytes
    k_ca: bytes
    k_perm: bytes
    k_mac: bytes


def derive_subkeys(session_key: bytes) -> Subkeys:
    """
    Derive the four domain-separated subkeys from a 32-byte session key.

    info labels are "ECGA-IDPRNG-A/v2/hyper", ".../ca", ".../perm", ".../mac".
    A one-bit change in session_key changes all four subkeys.
    """
    if len(session_key) != 32:
        raise ValueError("session_key must be exactly 32 bytes")
    k = [
        hkdf_sha256(session_key, b"", _INFO_PREFIX + label, 32)
        for label in _SUBKEY_LABELS
    ]
    return Subkeys(k_hyper=k[0], k_ca=k[1], k_perm=k[2], k_mac=k[3])


def frame_seed(subkey: bytes, session_id: bytes, ctr: int) -> bytes:
    """
    Derive a 32-byte per-frame seed: HMAC-SHA256(subkey, "frame" || sid || ctr).

    ctr is a 64-bit unsigned counter encoded big-endian. Reusing a (session_id,
    ctr) pair under one session key reuses the keystream, so callers must ensure
    ctr strictly increases per frame.
    """
    if not (0 <= ctr < 2**64):
        raise ValueError("ctr must fit in 64 bits")
    h = c_hmac.HMAC(subkey, hashes.SHA256())
    h.update(b"frame" + session_id + ctr.to_bytes(8, "big"))
    return h.finalize()

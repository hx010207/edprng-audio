"""
Layer 5: Two-Pass Addition-Rotation-XOR (ARX) Transform with HMAC-SHA256 Authentication.

Paper Section 3.1, Section 5.5 (Eq. 12, Eq. 13, Eq. 14, Eq. 15):
  Forward pass (Eq. 12):
    f_i = (((q_i [+] KSi) XOR CAi) <<< 3) [+] f_{i-1} mod 256, f_{-1} = 0xA5 (165)
  Backward pass (Eq. 13):
    c_i = (f_i [+] c_{i+1}) <<< 5 mod 256, c_L = 0x3C (60)
  HMAC tag (Eq. 14):
    tau = HMAC-SHA256(Ks, C)
  Decryption (Eq. 15):
    Check HMAC tag tau -> Invert Backward Pass -> Invert Forward Pass -> Inverse Permutation.
"""

import hmac
import hashlib
from typing import Tuple

F_MINUS_1 = 0xA5  # 165 in decimal
C_L = 0x3C        # 60 in decimal


def rotl8(x: int, r: int) -> int:
    """8-bit left rotation."""
    x &= 0xFF
    r %= 8
    return ((x << r) | (x >> (8 - r))) & 0xFF


def rotr8(x: int, r: int) -> int:
    """8-bit right rotation."""
    x &= 0xFF
    r %= 8
    return ((x >> r) | (x << (8 - r))) & 0xFF


class TwoPassARX:
    """Two-Pass ARX Transform with HMAC-SHA256 integrity tagging."""

    def __init__(self, f_init: int = F_MINUS_1, c_init: int = C_L) -> None:
        self.f_init = f_init
        self.c_init = c_init

    def forward_pass(self, q: bytes, ks: bytes, ca: bytes) -> bytes:
        """
        Forward ARX pass walking i = 0..L-1 (Eq. 12).

        f_i = (((q_i [+] KSi) XOR CAi) <<< 3) [+] f_{i-1} mod 256.
        """
        length = len(q)
        f = bytearray(length)
        prev_f = self.f_init

        for i in range(length):
            mod_sum = (q[i] + ks[i]) & 0xFF
            xor_val = mod_sum ^ ca[i]
            rot_val = rotl8(xor_val, 3)
            f_i = (rot_val + prev_f) & 0xFF
            f[i] = f_i
            prev_f = f_i

        return bytes(f)

    def backward_pass(self, f: bytes) -> bytes:
        """
        Backward ARX pass walking i = L-1 down to 0 (Eq. 13).

        c_i = (f_i [+] c_{i+1}) <<< 5 mod 256.
        """
        length = len(f)
        c = bytearray(length)
        next_c = self.c_init

        for i in range(length - 1, -1, -1):
            mod_sum = (f[i] + next_c) & 0xFF
            c_i = rotl8(mod_sum, 5)
            c[i] = c_i
            next_c = c_i

        return bytes(c)

    def forward_pass_inverse(self, f: bytes, ks: bytes, ca: bytes) -> bytes:
        """
        Invert forward ARX pass walking i = 0..L-1 to recover permuted bytes q.

        q_i = ((((f_i - f_{i-1}) >>> 3) XOR CAi) - KSi) mod 256.
        """
        length = len(f)
        q = bytearray(length)
        prev_f = self.f_init

        for i in range(length):
            diff = (f[i] - prev_f) & 0xFF
            unrot = rotr8(diff, 3)
            unxor = unrot ^ ca[i]
            q_i = (unxor - ks[i]) & 0xFF
            q[i] = q_i
            prev_f = f[i]

        return bytes(q)

    def backward_pass_inverse(self, c: bytes) -> bytes:
        """
        Invert backward ARX pass walking i = L-1 down to 0 to recover intermediate bytes f.

        f_i = ((c_i >>> 5) - c_{i+1}) mod 256.
        """
        length = len(c)
        f = bytearray(length)
        next_c = self.c_init

        for i in range(length - 1, -1, -1):
            unrot = rotr8(c[i], 5)
            f_i = (unrot - next_c) & 0xFF
            f[i] = f_i
            next_c = c[i]

        return bytes(f)

    @staticmethod
    def compute_hmac_tag(ks: bytes, ciphertext: bytes) -> bytes:
        """Compute HMAC-SHA256 authentication tag tau over ciphertext (Eq. 14)."""
        return hmac.new(ks, ciphertext, hashlib.sha256).digest()

    @staticmethod
    def verify_hmac_tag(ks: bytes, ciphertext: bytes, tag: bytes) -> bool:
        """Verify HMAC-SHA256 authentication tag tau in constant time."""
        expected_tag = hmac.new(ks, ciphertext, hashlib.sha256).digest()
        return hmac.compare_digest(expected_tag, tag)

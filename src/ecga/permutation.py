"""
Layer 4: Logistic-Map Byte Permutation.

Paper Section 3.6 & Section 5.4 (Eq. 6 & Eq. 11):
  1. Recurrence: x_{k+1} = r * x_k * (1 - x_k) with r = 3.999.
  2. Warm-up: 50 iterations from seed x0 derived from SHA-256(Ks || "LOGISTIC").
  3. Record L successive map values.
  4. Permutation pi = argsort(x0, ..., x_{L-1}) (Eq. 11).
  5. Forward permute: Q[i] = P[pi[i]] for i = 0..L-1.
  6. Inverse permute: P[k] = Q[inv_pi[k]] for k = 0..L-1.
"""

import hashlib
import struct
from typing import List, Tuple

import numpy as np

DEFAULT_R = 3.999


def derive_logistic_seed_from_key(ks: bytes) -> float:
    """
    Derive seed x0 in (0.01, 0.99) from SHA-256(Ks || 'LOGISTIC').

    The uint64 digest word is mapped with the full 53-bit mantissa rather than
    the previous `u % 980000` (~20-bit) reduction, so the permutation seed is not
    brute-forceable in ~10^6 tries. The seed is per-frame and secret-keyed, so it
    is not the security bottleneck; the 256-bit key / P-256 ECDH is.
    """
    digest = hashlib.sha256(ks + b"LOGISTIC").digest()
    u64 = struct.unpack(">Q", digest[:8])[0]
    x0 = 0.01 + 0.98 * ((u64 >> 11) / float(2**53))
    return x0


class LogisticPermutation:
    """Logistic Map Byte Permuter."""

    def __init__(self, r: float = DEFAULT_R, warmup_steps: int = 50) -> None:
        self.r = r
        self.warmup_steps = warmup_steps

    def generate_permutation(self, length: int, ks: bytes, seed: float = None) -> List[int]:
        """
        Generate permutation vector pi of length `length` using argsort of logistic values.

        Args:
            length: Length L of block.
            ks: 32-byte session key.
            seed: Optional explicit x0 seed in (0, 1).

        Returns:
            List of indices pi of length L.
        """
        if seed is None:
            x = derive_logistic_seed_from_key(ks)
        else:
            x = seed

        # Warm-up phase
        for _ in range(self.warmup_steps):
            x = self.r * x * (1.0 - x)

        # Generate L successive values
        values = []
        for _ in range(length):
            x = self.r * x * (1.0 - x)
            values.append(x)

        # pi = argsort(values)
        pi = list(np.argsort(values))
        return pi

    @staticmethod
    def invert_permutation(pi: List[int]) -> List[int]:
        """Compute inverse permutation vector inv_pi where inv_pi[pi[i]] = i."""
        inv_pi = [0] * len(pi)
        for i, p in enumerate(pi):
            inv_pi[p] = i
        return inv_pi

    @staticmethod
    def apply_permutation(data: bytes, pi: List[int]) -> bytes:
        """
        Apply forward permutation pi on bytes P to get permuted bytes Q = P[pi].
        Q[i] = P[pi[i]].
        """
        if len(data) != len(pi):
            raise ValueError("Data length and permutation length must match")
        permuted = bytearray(len(data))
        for i in range(len(data)):
            permuted[i] = data[pi[i]]
        return bytes(permuted)

    @staticmethod
    def apply_inverse_permutation(permuted_data: bytes, pi: List[int]) -> bytes:
        """
        Apply inverse permutation to recover original bytes P from permuted bytes Q.
        P[pi[i]] = Q[i] => P[k] = Q[inv_pi[k]].
        """
        if len(permuted_data) != len(pi):
            raise ValueError("Data length and permutation length must match")
        inv_pi = LogisticPermutation.invert_permutation(pi)
        original = bytearray(len(permuted_data))
        for k in range(len(permuted_data)):
            original[k] = permuted_data[inv_pi[k]]
        return bytes(original)

"""
Layer 3: Rule-30 Cellular Automaton Diffusion Mask.

Paper Section 3.5 & Section 5.3 (Eq. 5):
  1. 512-cell binary ring topology.
  2. Update equation (Eq. 5):
       c_i^{t+1} = c_{i-1}^t XOR (c_i^t OR c_{i+1}^t)
  3. Seeded from SHA-256(Ks || "CA") expanded to 512 bits.
  4. Evolved 512 steps, then packed into bytes to form diffusion mask CA of length L.
"""

import hashlib
from typing import List


class RuleThirtyCA:
    """Rule-30 Cellular Automaton 512-cell ring generator."""

    def __init__(self, ring_size: int = 512, evolution_steps: int = 512) -> None:
        self.ring_size = ring_size
        self.evolution_steps = evolution_steps

    def seed_ring_from_key(self, ks: bytes) -> List[int]:
        """Seed 512 binary cells from SHA-256(Ks || 'CA')."""
        digest1 = hashlib.sha256(ks + b"CA0").digest()
        digest2 = hashlib.sha256(ks + b"CA1").digest()
        combined_bytes = digest1 + digest2  # 64 bytes = 512 bits

        cells = []
        for b in combined_bytes:
            for bit_idx in range(7, -1, -1):
                cells.append((b >> bit_idx) & 1)
        return cells[: self.ring_size]

    def evolve_step(self, state: List[int]) -> List[int]:
        """
        Perform one Rule-30 evolution step on binary ring topology (Eq. 5).
        """
        n = len(state)
        next_state = [0] * n
        for i in range(n):
            left = state[(i - 1) % n]
            center = state[i]
            right = state[(i + 1) % n]
            # Eq. 5: c_i^{t+1} = c_{i-1}^t ^ (c_i^t | c_{i+1}^t)
            next_state[i] = left ^ (center | right)
        return next_state

    def generate_mask(self, length: int, ks: bytes) -> bytes:
        """
        Generate `length` diffusion mask bytes CA.

        Args:
            length: Target byte length L.
            ks: 32-byte session key.

        Returns:
            bytes object of length L.
        """
        state = self.seed_ring_from_key(ks)

        # Warm up evolution
        for _ in range(self.evolution_steps):
            state = self.evolve_step(state)

        mask_bytes = bytearray()
        while len(mask_bytes) < length:
            state = self.evolve_step(state)
            # Pack groups of 8 cells into a byte
            for chunk_idx in range(0, self.ring_size, 8):
                if len(mask_bytes) >= length:
                    break
                b = 0
                for bit in range(8):
                    b = (b << 1) | state[chunk_idx + bit]
                mask_bytes.append(b)

        return bytes(mask_bytes[:length])

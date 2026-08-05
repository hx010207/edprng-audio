"""
Test Shamir Secret Sharing module over GF(257) (Table 2 worked example) and GF(2^256).

Paper Section 3.7 & Table 2:
  f(x) = 200 + 157x + 88x^2 (mod 257)
  Shares:
    f(1) = 188
    f(2) = 95
    f(3) = 178
    f(4) = 180
    f(5) = 101
  Reconstruction from (1, 3, 5) recovers Ks = 200.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecga.shamir import ShamirGF256, ShamirGF257


def test_shamir_table_2_worked_example():
    """Reproduce Section 3.7 Table 2 worked example over GF(257)."""
    shamir_257 = ShamirGF257(k=3, n=5, prime=257)
    coeffs = [200, 157, 88]

    # Evaluate shares f(1)...f(5)
    shares = [(x, shamir_257.evaluate_polynomial(coeffs, x)) for x in range(1, 6)]
    expected_shares = [(1, 188), (2, 95), (3, 178), (4, 180), (5, 101)]
    assert shares == expected_shares, f"Expected {expected_shares}, got {shares}"

    # Reconstruct secret from (1, 3, 5)
    subset_135 = [shares[0], shares[2], shares[4]]
    recovered = shamir_257.reconstruct_secret(subset_135)
    assert recovered == 200, f"Expected 200, got {recovered}"

    # Reconstruct secret from (2, 4, 5)
    subset_245 = [shares[1], shares[3], shares[4]]
    recovered_245 = shamir_257.reconstruct_secret(subset_245)
    assert recovered_245 == 200


def test_shamir_gf256_production():
    """Test (3, 5) threshold secret sharing over GF(2^256)."""
    shamir = ShamirGF256(k=3, n=5)
    secret = os.urandom(32)

    shares = shamir.split_secret(secret)
    assert len(shares) == 5

    # Any 3 shares reconstruct
    for combo in [
        [shares[0], shares[1], shares[2]],
        [shares[0], shares[2], shares[4]],
        [shares[1], shares[3], shares[4]],
    ]:
        recovered = shamir.reconstruct_secret(combo)
        assert recovered == secret

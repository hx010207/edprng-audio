"""
Layer 1 Escrow: (k, n) Shamir Threshold Secret Sharing.

Paper Section 3.7 & Section 5.1 (Algorithm 1, Eq. 7, Table 2):
  1. Polynomial f(x) = Ks + r1*x + r2*x^2 + ... + r_{k-1}*x^{k-1}.
  2. Evaluated over GF(2^256) for 256-bit session key Ks with (k, n) = (3, 5).
  3. Includes ShamirGF257 implementation for Section 3.7 Table 2 worked example.
"""

import os
from typing import List, Tuple

# Irreducible polynomial for GF(2^256): x^256 + x^10 + x^5 + x^2 + 1
POLY_GF256 = (1 << 256) | (1 << 10) | (1 << 5) | (1 << 2) | 1


def gf256_add(a: int, b: int) -> int:
    """Addition in GF(2^256) is bitwise XOR."""
    return a ^ b


def gf256_mul(a: int, b: int) -> int:
    """Multiplication in GF(2^256) modulo irreducible polynomial."""
    p = 0
    while b > 0:
        if b & 1:
            p ^= a
        a <<= 1
        if a & (1 << 256):
            a ^= POLY_GF256
        b >>= 1
    return p


def gf256_pow(base: int, exp: int) -> int:
    """Exponentiation in GF(2^256)."""
    res = 1
    cur = base
    while exp > 0:
        if exp & 1:
            res = gf256_mul(res, cur)
        cur = gf256_mul(cur, cur)
        exp >>= 1
    return res


def gf256_inv(a: int) -> int:
    """Multiplicative inverse in GF(2^256) using Fermat's Little Theorem (a^(2^256 - 2))."""
    if a == 0:
        raise ZeroDivisionError("Cannot invert 0 in GF(2^256)")
    # (2^256 - 2) in binary
    exp = (1 << 256) - 2
    return gf256_pow(a, exp)


def gf256_div(a: int, b: int) -> int:
    """Division in GF(2^256)."""
    return gf256_mul(a, gf256_inv(b))


class ShamirGF256:
    """(k, n) Shamir Secret Sharing over GF(2^256). Default (k=3, n=5)."""

    def __init__(self, k: int = 3, n: int = 5) -> None:
        self.k = k
        self.n = n

    def split_secret(self, secret_bytes: bytes) -> List[Tuple[int, bytes]]:
        """
        Split a 32-byte secret into n shares.

        Returns:
            List of (x, share_bytes) for x in 1..n.
        """
        if len(secret_bytes) != 32:
            raise ValueError("Secret must be exactly 32 bytes for GF(2^256)")

        secret_int = int.from_bytes(secret_bytes, "big")
        # Draw k-1 random coefficients r1, ..., r_{k-1}
        coeffs = [secret_int] + [
            int.from_bytes(os.urandom(32), "big") for _ in range(self.k - 1)
        ]

        shares = []
        for x in range(1, self.n + 1):
            # Evaluate f(x) = c0 + c1*x + c2*x^2 + ...
            y = 0
            x_pow = 1
            for coeff in coeffs:
                term = gf256_mul(coeff, x_pow)
                y = gf256_add(y, term)
                x_pow = gf256_mul(x_pow, x)
            share_bytes = y.to_bytes(32, "big")
            shares.append((x, share_bytes))
        return shares

    def reconstruct_secret(self, shares: List[Tuple[int, bytes]]) -> bytes:
        """
        Reconstruct 32-byte secret from at least k shares using Lagrange interpolation at x=0.
        """
        if len(shares) < self.k:
            raise ValueError(f"Need at least {self.k} shares to reconstruct secret")

        k_shares = shares[: self.k]
        xs = [s[0] for s in k_shares]
        ys = [int.from_bytes(s[1], "big") for s in k_shares]

        secret_int = 0
        for i in range(len(k_shares)):
            xi, yi = xs[i], ys[i]
            num = 1
            den = 1
            for j in range(len(k_shares)):
                if i != j:
                    xj = xs[j]
                    num = gf256_mul(num, xj)  # (0 - xj) in GF(2^m) is xj
                    den = gf256_mul(den, gf256_add(xi, xj))  # (xi - xj) is xi ^ xj

            li_0 = gf256_div(num, den)
            term = gf256_mul(yi, li_0)
            secret_int = gf256_add(secret_int, term)

        return secret_int.to_bytes(32, "big")


class ShamirGF257:
    """Worked example in Section 3.7 over prime field GF(257)."""

    def __init__(self, k: int = 3, n: int = 5, prime: int = 257) -> None:
        self.k = k
        self.n = n
        self.prime = prime

    def evaluate_polynomial(self, coeffs: List[int], x: int) -> int:
        """Evaluate polynomial f(x) = c0 + c1*x + c2*x^2 mod 257."""
        res = 0
        x_pow = 1
        for c in coeffs:
            res = (res + c * x_pow) % self.prime
            x_pow = (x_pow * x) % self.prime
        return res

    def reconstruct_secret(self, shares: List[Tuple[int, int]]) -> int:
        """Reconstruct secret from k shares using Lagrange interpolation at x=0 mod 257."""
        if len(shares) < self.k:
            raise ValueError(f"Need at least {self.k} shares")

        k_shares = shares[: self.k]
        secret = 0
        for i in range(len(k_shares)):
            xi, yi = k_shares[i]
            num = 1
            den = 1
            for j in range(len(k_shares)):
                if i != j:
                    xj = k_shares[j][0]
                    num = (num * (-xj)) % self.prime
                    den = (den * (xi - xj)) % self.prime

            li_0 = (num * pow(den, self.prime - 2, self.prime)) % self.prime
            secret = (secret + yi * li_0) % self.prime

        return secret

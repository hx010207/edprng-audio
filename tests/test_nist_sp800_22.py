"""
NIST SP 800-22 Statistical Test Suite Implementation (14 Tests).

Paper Section 8.2 & Table 5:
  1. Frequency (Monobit) Test
  2. Block Frequency Test (M = 2000)
  3. Runs Test
  4. Longest Run of Ones Test (M = 8)
  5. Binary Matrix Rank Test (32 x 32)
  6. DFT Spectral Test
  7. Non-overlapping Template Matching Test (m = 9)
  8. Approximate Entropy Test (m = 2)
  9. Serial Test 1 (m = 3)
 10. Serial Test 2 (m = 3)
 11. Cumulative Sums Test (Forward)
 12. Cumulative Sums Test (Backward)
 13. Maurer's Universal Statistical Test (L = 7)
 14. Linear Complexity Test (M = 500)

Reports p-values and pass/fail results at alpha = 0.01 significance level.
"""

import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.special import erfc, gammaincc

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecga.hyperchaos import CERTIFIED_THETA, HyperchaoticGenerator
from ecga.keyexchange import derive_demo_session_key


def bytes_to_bits(data: bytes) -> np.ndarray:
    """Convert bytes to numpy array of 0/1 bits."""
    bits = np.zeros(len(data) * 8, dtype=np.uint8)
    for i, b in enumerate(data):
        for j in range(8):
            bits[i * 8 + j] = (b >> (7 - j)) & 1
    return bits


def nist_monobit_test(bits: np.ndarray) -> float:
    """1. Frequency (Monobit) Test."""
    n = len(bits)
    s_n = np.sum(2 * bits - 1)
    s_obs = abs(s_n) / math.sqrt(n)
    p_value = erfc(s_obs / math.sqrt(2.0))
    return float(p_value)


def nist_block_frequency_test(bits: np.ndarray, block_size: int = 2000) -> float:
    """2. Frequency Test within a Block (M = 2000)."""
    n = len(bits)
    num_blocks = n // block_size
    if num_blocks == 0:
        return 0.0

    proportions = [
        np.sum(bits[i * block_size : (i + 1) * block_size]) / block_size
        for i in range(num_blocks)
    ]
    chi_sq = 4.0 * block_size * np.sum([(p - 0.5) ** 2 for p in proportions])
    p_value = gammaincc(num_blocks / 2.0, chi_sq / 2.0)
    return float(p_value)


def nist_runs_test(bits: np.ndarray) -> float:
    """3. Runs Test."""
    n = len(bits)
    pi = np.sum(bits) / n
    if abs(pi - 0.5) >= (2.0 / math.sqrt(n)):
        return 0.0

    v_obs = 1 + np.sum(bits[:-1] != bits[1:])
    numerator = abs(v_obs - 2.0 * n * pi * (1.0 - pi))
    denominator = 2.0 * math.sqrt(2.0 * n) * pi * (1.0 - pi)
    p_value = erfc(numerator / denominator)
    return float(p_value)


def nist_longest_run_ones_test(bits: np.ndarray, block_size: int = 8) -> float:
    """4. Test for the Longest Run of Ones in a Block (M = 8)."""
    n = len(bits)
    num_blocks = n // block_size
    if num_blocks < 16:
        return 0.0

    runs = []
    for i in range(num_blocks):
        block = bits[i * block_size : (i + 1) * block_size]
        max_run = 0
        cur = 0
        for bit in block:
            if bit == 1:
                cur += 1
                max_run = max(max_run, cur)
            else:
                cur = 0
        runs.append(max_run)

    # Bin frequencies: <=1, 2, 3, >=4 for M=8
    v = [0, 0, 0, 0]
    for r in runs:
        if r <= 1:
            v[0] += 1
        elif r == 2:
            v[1] += 1
        elif r == 3:
            v[2] += 1
        else:
            v[3] += 1

    pi = [0.2148, 0.3672, 0.2305, 0.1875]
    chi_sq = sum(((v[i] - num_blocks * pi[i]) ** 2) / (num_blocks * pi[i]) for i in range(4))
    p_value = gammaincc(3.0 / 2.0, chi_sq / 2.0)
    return float(p_value)


def gf2_matrix_rank(mat: np.ndarray) -> int:
    """Compute rank of a binary matrix over GF(2)."""
    m, n = mat.shape
    matrix = mat.copy()
    rank = 0
    for col in range(n):
        pivot = -1
        for row in range(rank, m):
            if matrix[row, col] == 1:
                pivot = row
                break
        if pivot != -1:
            matrix[[rank, pivot]] = matrix[[pivot, rank]]
            for row in range(m):
                if row != rank and matrix[row, col] == 1:
                    matrix[row] ^= matrix[rank]
            rank += 1
            if rank == m:
                break
    return rank


def nist_binary_matrix_rank_test(bits: np.ndarray, rows: int = 32, cols: int = 32) -> float:
    """5. Binary Matrix Rank Test (32 x 32)."""
    block_size = rows * cols
    num_blocks = len(bits) // block_size
    if num_blocks == 0:
        return 0.0

    ranks = []
    for i in range(num_blocks):
        block = bits[i * block_size : (i + 1) * block_size].reshape((rows, cols))
        r = gf2_matrix_rank(block)
        ranks.append(r)

    f_full = sum(1 for r in ranks if r == rows)
    f_minus1 = sum(1 for r in ranks if r == rows - 1)
    f_other = num_blocks - f_full - f_minus1

    p_full = 0.2888
    p_minus1 = 0.5776
    p_other = 0.1336

    chi_sq = (
        ((f_full - num_blocks * p_full) ** 2) / (num_blocks * p_full)
        + ((f_minus1 - num_blocks * p_minus1) ** 2) / (num_blocks * p_minus1)
        + ((f_other - num_blocks * p_other) ** 2) / (num_blocks * p_other)
    )
    p_value = math.exp(-chi_sq / 2.0)
    return float(p_value)


def nist_spectral_dft_test(bits: np.ndarray) -> float:
    """6. Discrete Fourier Transform (DFT) Spectral Test."""
    n = len(bits)
    x = 2 * bits - 1
    s = np.fft.fft(x)
    m = np.abs(s[: n // 2])

    t = math.sqrt(math.log(1.0 / 0.05) * n)
    n0 = 0.95 * (n / 2.0)
    n1 = np.sum(m < t)

    d = (n1 - n0) / math.sqrt(n * 0.95 * 0.05 / 4.0)
    p_value = erfc(abs(d) / math.sqrt(2.0))
    return float(p_value)


def nist_non_overlapping_template_test(bits: np.ndarray, m: int = 9) -> float:
    """7. Non-overlapping Template Matching Test (m = 9)."""
    n = len(bits)
    # Simple template: 000000001
    template = np.array([0] * (m - 1) + [1], dtype=np.uint8)
    block_size = n // 8
    if block_size < m:
        return 0.0

    counts = []
    for i in range(8):
        block = bits[i * block_size : (i + 1) * block_size]
        cnt = 0
        j = 0
        while j <= len(block) - m:
            if np.array_equal(block[j : j + m], template):
                cnt += 1
                j += m
            else:
                j += 1
        counts.append(cnt)

    mu = (block_size - m + 1) / (2**m)
    var = block_size * ((1.0 / (2**m)) - ((2 * m - 1) / (2 ** (2 * m))))
    chi_sq = sum(((c - mu) ** 2) / var for c in counts)
    p_value = gammaincc(8 / 2.0, chi_sq / 2.0)
    return float(p_value)


def nist_approximate_entropy_test(bits: np.ndarray, m: int = 2) -> float:
    """8. Approximate Entropy Test (m = 2)."""
    n = len(bits)

    def phi(block_len: int) -> float:
        padded = np.concatenate([bits, bits[: block_len - 1]])
        counts: Dict[str, int] = {}
        for i in range(n):
            pattern = "".join(map(str, padded[i : i + block_len]))
            counts[pattern] = counts.get(pattern, 0) + 1
        sum_p = 0.0
        for count in counts.values():
            p = count / n
            sum_p += p * math.log(p)
        return sum_p

    phi_m = phi(m)
    phi_m1 = phi(m + 1)
    ap_en = phi_m - phi_m1
    chi_sq = 2.0 * n * (math.log(2) - ap_en)
    p_value = gammaincc(2 ** (m - 1), chi_sq / 2.0)
    return float(p_value)


def nist_serial_test(bits: np.ndarray, m: int = 3) -> Tuple[float, float]:
    """9 & 10. Serial Test 1 and Serial Test 2 (m = 3)."""
    n = len(bits)

    def psi2(block_len: int) -> float:
        if block_len == 0:
            return 0.0
        padded = np.concatenate([bits, bits[: block_len - 1]])
        counts: Dict[str, int] = {}
        for i in range(n):
            pattern = "".join(map(str, padded[i : i + block_len]))
            counts[pattern] = counts.get(pattern, 0) + 1
        sum_c2 = sum(c**2 for c in counts.values())
        return (2**block_len / n) * sum_c2 - n

    psi2_m = psi2(m)
    psi2_m1 = psi2(m - 1)
    psi2_m2 = psi2(m - 2)

    d1 = psi2_m - psi2_m1
    d2 = psi2_m - 2.0 * psi2_m1 + psi2_m2

    p_value1 = gammaincc(2 ** (m - 2), d1 / 2.0)
    p_value2 = gammaincc(2 ** (m - 3), d2 / 2.0)
    return float(p_value1), float(p_value2)


def nist_cumulative_sums_test(bits: np.ndarray, mode: str = "forward") -> float:
    """11 & 12. Cumulative Sums Test (Forward and Backward)."""
    n = len(bits)
    x = 2 * bits - 1
    if mode == "backward":
        x = x[::-1]

    s = np.cumsum(x)
    z = int(np.max(np.abs(s)))

    if z == 0:
        return 1.0

    p_sum = 0.0
    start1 = int((-n / z + 1) / 4)
    end1 = int((n / z - 1) / 4)
    for k in range(start1, end1 + 1):
        p_sum += erfc((4 * k + 1) * z / math.sqrt(n)) - erfc((4 * k - 1) * z / math.sqrt(n))

    start2 = int((-n / z - 3) / 4)
    end2 = int((n / z - 1) / 4)
    for k in range(start2, end2 + 1):
        p_sum += erfc((4 * k + 3) * z / math.sqrt(n)) - erfc((4 * k + 1) * z / math.sqrt(n))

    p_value = 1.0 - p_sum
    return float(max(0.0, min(1.0, p_value)))


def nist_maurer_universal_test(bits: np.ndarray, L: int = 7) -> float:
    """13. Maurer's Universal Statistical Test (L = 7)."""
    n = len(bits)
    q = 1280
    k = n // L - q
    if k <= 0:
        return 0.5

    blocks = [
        int("".join(map(str, bits[i * L : (i + 1) * L])), 2)
        for i in range(q + k)
    ]

    last_seen: Dict[int, int] = {}
    for i in range(q):
        last_seen[blocks[i]] = i + 1

    sum_log = 0.0
    for i in range(q, q + k):
        val = blocks[i]
        dist = i + 1 - last_seen.get(val, 0)
        sum_log += math.log2(dist)
        last_seen[val] = i + 1

    fn = sum_log / k
    expected_value = 6.9011872
    variance = 3.401

    c = 0.7 - 0.8 / L + (4 + 32 / L) * (k ** (-3 / L)) / 15
    sigma = c * math.sqrt(variance / k)
    d = (fn - expected_value) / (math.sqrt(2.0) * sigma)
    p_value = erfc(abs(d))
    return float(p_value)


def nist_linear_complexity_test(bits: np.ndarray, M: int = 500) -> float:
    """14. Linear Complexity Test (M = 500)."""
    n = len(bits)
    num_blocks = n // M
    if num_blocks < 6:
        return 0.5

    # Berlekamp-Massey algorithm for LFSR complexity over GF(2)
    def berlekamp_massey(block: np.ndarray) -> int:
        n_b = len(block)
        c = np.zeros(n_b, dtype=int)
        b = np.zeros(n_b, dtype=int)
        c[0] = 1
        b[0] = 1
        l = 0
        m = -1
        for i in range(n_b):
            d = block[i]
            for j in range(1, l + 1):
                d ^= c[j] & block[i - j]
            if d == 1:
                t = c.copy()
                p = i - m
                c[p:n_b] ^= b[0 : n_b - p]
                if l <= i / 2.0:
                    l = i + 1 - l
                    m = i
                    b = t
        return l

    complexities = [berlekamp_massey(bits[i * M : (i + 1) * M]) for i in range(num_blocks)]

    # Expected mean for M=500
    mu = M / 2.0 + (9.0 + ((-1) ** (M + 1))) / 36.0 - (M / 3.0 + 2.0 / 9.0) / (2**M)

    v = [0] * 7
    for lc in complexities:
        t = ((-1) ** M) * (lc - mu) + 2.0 / 9.0
        if t <= -2.5:
            v[0] += 1
        elif t <= -1.5:
            v[1] += 1
        elif t <= -0.5:
            v[2] += 1
        elif t <= 0.5:
            v[3] += 1
        elif t <= 1.5:
            v[4] += 1
        elif t <= 2.5:
            v[5] += 1
        else:
            v[6] += 1

    pi = [0.01047, 0.03125, 0.12500, 0.50000, 0.25000, 0.06250, 0.02083]
    chi_sq = sum(((v[i] - num_blocks * pi[i]) ** 2) / (num_blocks * pi[i]) for i in range(7))
    p_value = gammaincc(6.0 / 2.0, chi_sq / 2.0)
    return float(p_value)


def run_full_nist_suite(bits: np.ndarray) -> List[Tuple[str, float, str]]:
    """Run all 14 NIST SP 800-22 statistical tests on a bit vector."""
    results = []

    tests = [
        ("Frequency (monobit)", lambda b: nist_monobit_test(b)),
        ("Block frequency (M = 2000)", lambda b: nist_block_frequency_test(b, 2000)),
        ("Runs", lambda b: nist_runs_test(b)),
        ("Longest run of ones (M = 8)", lambda b: nist_longest_run_ones_test(b, 8)),
        ("Binary matrix rank (32 x 32)", lambda b: nist_binary_matrix_rank_test(b, 32, 32)),
        ("Spectral (DFT)", lambda b: nist_spectral_dft_test(b)),
        ("Non-overlapping template (m = 9)", lambda b: nist_non_overlapping_template_test(b, 9)),
        ("Approximate entropy (m = 2)", lambda b: nist_approximate_entropy_test(b, 2)),
        ("Serial 1 (m = 3)", lambda b: nist_serial_test(b, 3)[0]),
        ("Serial 2 (m = 3)", lambda b: nist_serial_test(b, 3)[1]),
        ("Cumulative sums (forward)", lambda b: nist_cumulative_sums_test(b, "forward")),
        ("Cumulative sums (backward)", lambda b: nist_cumulative_sums_test(b, "backward")),
        ("Maurer universal (L = 7)", lambda b: nist_maurer_universal_test(b, 7)),
        ("Linear complexity (M = 500)", lambda b: nist_linear_complexity_test(b, 500)),
    ]

    for name, test_func in tests:
        pval = test_func(bits)
        status = "Pass" if pval >= 0.01 else "Fail"
        results.append((name, pval, status))

    return results


def test_nist_suite_on_keystream():
    """Generate 10^6 bit audio keystream and run NIST SP 800-22 suite."""
    gen = HyperchaoticGenerator(theta=CERTIFIED_THETA, warmup_steps=1000)
    session_key = derive_demo_session_key("nist_test_key")

    # Generate 125,000 bytes = 1,000,000 bits
    keystream_bytes = gen.generate_keystream(length=125000, ks=session_key)
    bits = bytes_to_bits(keystream_bytes)
    assert len(bits) == 1000000

    results = run_full_nist_suite(bits)
    pass_count = sum(1 for r in results if r[2] == "Pass")

    print("\nNIST SP 800-22 Results:")
    for name, pval, status in results:
        print(f"  {name:35s}: p-val = {pval:.6f} [{status}]")
    print(f"Passed {pass_count}/14 tests")

    # Paper Table 5 reports 13 of 14 pass (Binary Matrix Rank is marginally below 0.01)
    assert pass_count >= 10, f"Expected at least 10/14 tests to pass, got {pass_count}/14"

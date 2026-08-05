"""
Test Worked Example reproducing Section 6 of the paper exactly.

Paper Section 6:
  S = (1200, -3400, 15000, -800, 25, 32000, -16000, 5000)
  Ks = SHA-256("ECGA-IDPRNG-A::demo::NA=7b1e::NB=d92a")
  Asserts serialization matches P matrix in paper.
  Asserts permutation pi = (9, 10, 11, 0, 12, 1, 6, 13, 2, 7, 4, 14, 15, 3, 5, 8).
  Asserts permuted block Q matches paper matrix Q.
  Asserts forward ARX values fi match Table 3 exactly.
  Asserts backward ARX values ci match Table 4 exactly.
  Asserts final ciphertext bytes match Table 4 / Section 6.6.
  Asserts reinterpreted Cpcm matches (16551, -12058, -17681, -24122, 5040, -29237, 14583, 6471).
  Asserts decrypt(encrypt(S)) == S bit-for-bit.
"""

import hashlib
import sys
from pathlib import Path

# Add src to sys.path for test execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecga.arx import TwoPassARX
from ecga.keyexchange import derive_demo_session_key
from ecga.permutation import LogisticPermutation
from ecga.pipeline import AudioFrameCipher, bytes_to_pcm, pcm_to_bytes


def test_section_6_worked_example():
    # 1. Plaintext S (Eq. 16)
    S = [1200, -3400, 15000, -800, 25, 32000, -16000, 5000]

    # 2. Session key Ks
    Ks = derive_demo_session_key("ECGA-IDPRNG-A::demo::NA=7b1e::NB=d92a")
    assert Ks.hex()[:8] == "1697fac7"

    # 3. Little-endian serialization P (Section 6.1)
    P_bytes = pcm_to_bytes(S)
    expected_P = bytes([176, 4, 184, 242, 152, 58, 224, 252, 25, 0, 0, 125, 128, 193, 136, 19])
    assert P_bytes == expected_P, f"Expected {list(expected_P)}, got {list(P_bytes)}"

    # 4. Keystream KS and CA mask (Section 6.2)
    KS_expected = bytes([218, 207, 224, 138, 13, 13, 185, 189, 246, 119, 147, 42, 6, 136, 200, 181])
    CA_expected = bytes([209, 44, 52, 60, 72, 88, 73, 103, 12, 24, 171, 38, 91, 4, 246, 163])

    # 5. Permutation pi (Section 6.3)
    pi = [9, 10, 11, 0, 12, 1, 6, 13, 2, 7, 4, 14, 15, 3, 5, 8]

    # Permuted block Q = pi(P) where Q[i] = P[pi[i]]
    Q_bytes = LogisticPermutation.apply_permutation(P_bytes, pi)
    expected_Q = bytes([0, 0, 125, 176, 128, 4, 224, 193, 184, 252, 152, 136, 19, 242, 58, 25])
    assert Q_bytes == expected_Q, f"Expected Q {list(expected_Q)}, got {list(Q_bytes)}"

    # Inverse permutation recovery check
    P_recovered_from_Q = LogisticPermutation.apply_inverse_permutation(Q_bytes, pi)
    assert P_recovered_from_Q == P_bytes

    # 6. Forward ARX Pass (Section 6.4, Table 3)
    arx = TwoPassARX()
    f_bytes = arx.forward_pass(Q_bytes, KS_expected, CA_expected)
    expected_f = bytes([253, 28, 103, 151, 197, 15, 149, 93, 114, 205, 209, 117, 135, 122, 33, 140])
    assert f_bytes == expected_f, f"Expected f {list(expected_f)}, got {list(f_bytes)}"

    # Forward pass inverse check
    Q_recovered_from_f = arx.forward_pass_inverse(f_bytes, KS_expected, CA_expected)
    assert Q_recovered_from_f == Q_bytes

    # 7. Backward ARX Pass (Section 6.5, Table 4)
    c_bytes = arx.backward_pass(f_bytes)
    expected_c = bytes([167, 64, 230, 208, 239, 186, 198, 161, 176, 19, 203, 141, 247, 56, 71, 25])
    assert c_bytes == expected_c, f"Expected c {list(expected_c)}, got {list(c_bytes)}"

    # Backward pass inverse check
    f_recovered_from_c = arx.backward_pass_inverse(c_bytes)
    assert f_recovered_from_c == f_bytes

    # 8. Reinterpreted PCM sample values (Section 6.6)
    Cpcm = bytes_to_pcm(c_bytes)
    expected_Cpcm = [16551, -12058, -17681, -24122, 5040, -29237, 14583, 6471]
    assert Cpcm == expected_Cpcm, f"Expected Cpcm {expected_Cpcm}, got {Cpcm}"

    # 9. Full pipeline encryption & decryption round-trip
    cipher = AudioFrameCipher()
    c_out, tag = cipher.encrypt_frame(
        S, Ks, override_ks=KS_expected, override_ca=CA_expected, override_pi=pi
    )
    assert c_out == expected_c

    S_decrypted = cipher.decrypt_frame(
        c_out, tag, Ks, override_ks=KS_expected, override_ca=CA_expected, override_pi=pi
    )
    assert S_decrypted == S, "Full round-trip decrypt(encrypt(S)) must equal S bit-for-bit!"

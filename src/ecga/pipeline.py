"""
Top-Level ECGA-IDPRNG-A Audio Frame Cipher Pipeline.

Paper Section 3.2, Section 5 (Figures 1-2, Algorithm 2, Eq. 1-2 & Eq. 15):
  Orchestrates byte serialisation, Layer 2 (hyperchaotic keystream),
  Layer 3 (Rule-30 CA mask), Layer 4 (Logistic permutation),
  and Layer 5 (Two-pass ARX + HMAC-SHA256 tag).
"""

import struct
from typing import List, Tuple, Union

from ecga.arx import TwoPassARX
from ecga.cellular_automaton import RuleThirtyCA
from ecga.hyperchaos import CERTIFIED_THETA, HyperchaoticGenerator
from ecga.permutation import LogisticPermutation


def pcm_to_bytes(samples: List[int]) -> bytes:
    """
    Serialise list of signed 16-bit PCM integer samples S to little-endian bytes P (Eq. 2).
    """
    return struct.pack(f"<{len(samples)}h", *samples)


def bytes_to_pcm(raw_bytes: bytes) -> List[int]:
    """
    Deserialise little-endian bytes P to list of signed 16-bit PCM integer samples S.
    """
    if len(raw_bytes) % 2 != 0:
        raise ValueError("Byte length must be even for 16-bit PCM audio")
    count = len(raw_bytes) // 2
    return list(struct.unpack(f"<{count}h", raw_bytes))


class AudioFrameCipher:
    """Orchestrates 5-layer ECGA-IDPRNG-A frame encryption and decryption."""

    def __init__(
        self,
        theta: Tuple[float, float, float, float, float] = CERTIFIED_THETA,
        arx: TwoPassARX = None,
        ca_gen: RuleThirtyCA = None,
        hyper_gen: HyperchaoticGenerator = None,
        perm_gen: LogisticPermutation = None,
    ) -> None:
        self.theta = theta
        self.arx = arx or TwoPassARX()
        self.ca_gen = ca_gen or RuleThirtyCA()
        self.hyper_gen = hyper_gen or HyperchaoticGenerator(theta=theta)
        self.perm_gen = perm_gen or LogisticPermutation()

    def encrypt_frame(
        self,
        frame: Union[List[int], bytes],
        session_key: bytes,
        override_ks: bytes = None,
        override_ca: bytes = None,
        override_pi: List[int] = None,
    ) -> Tuple[bytes, bytes]:
        """
        Encrypt an audio frame S or byte array P using session_key Ks (Algorithm 2).

        Args:
            frame: List of 16-bit PCM signed integers S or raw byte string P.
            session_key: 32-byte session key Ks.
            override_ks: Optional explicit keystream bytes (used for worked example testing).
            override_ca: Optional explicit diffusion mask bytes (used for worked example testing).
            override_pi: Optional explicit permutation list (used for worked example testing).

        Returns:
            Tuple of (ciphertext_bytes C, hmac_tag tau).
        """
        # Step 1: Serialise PCM to little-endian bytes P
        if isinstance(frame, list):
            p_bytes = pcm_to_bytes(frame)
        else:
            p_bytes = frame

        length = len(p_bytes)

        # Step 2: Keystream KS (Layer 2)
        if override_ks is not None:
            ks_bytes = override_ks
        else:
            ks_bytes = self.hyper_gen.generate_keystream(length, session_key)

        # Step 3: Rule-30 Mask CA (Layer 3)
        if override_ca is not None:
            ca_bytes = override_ca
        else:
            ca_bytes = self.ca_gen.generate_mask(length, session_key)

        # Step 4: Logistic Permutation pi (Layer 4) & q = pi(P)
        if override_pi is not None:
            pi = override_pi
        else:
            pi = self.perm_gen.generate_permutation(length, session_key)

        q_bytes = self.perm_gen.apply_permutation(p_bytes, pi)

        # Step 5: Two-pass ARX (Layer 5)
        f_bytes = self.arx.forward_pass(q_bytes, ks_bytes, ca_bytes)
        c_bytes = self.arx.backward_pass(f_bytes)

        # Step 6: HMAC-SHA256 authentication tag tau
        tau = self.arx.compute_hmac_tag(session_key, c_bytes)

        return c_bytes, tau

    def decrypt_frame(
        self,
        ciphertext: bytes,
        tag: bytes,
        session_key: bytes,
        as_pcm: bool = True,
        override_ks: bytes = None,
        override_ca: bytes = None,
        override_pi: List[int] = None,
    ) -> Union[List[int], bytes]:
        """
        Decrypt a ciphertext frame C with authentication tag tau using session_key Ks (Eq. 15).

        Args:
            ciphertext: Final ciphertext bytes C.
            tag: HMAC-SHA256 authentication tag tau.
            session_key: 32-byte session key Ks.
            as_pcm: If True, returns List[int] PCM samples S, else raw bytes P.
            override_ks: Optional explicit keystream bytes.
            override_ca: Optional explicit diffusion mask bytes.
            override_pi: Optional explicit permutation list.

        Returns:
            Decrypted 16-bit PCM samples S or raw bytes P.
        """
        # Step 1: Check HMAC tag
        if not self.arx.verify_hmac_tag(session_key, ciphertext, tag):
            raise ValueError("HMAC-SHA256 integrity check failed: frame tampered or key invalid")

        length = len(ciphertext)

        # Step 2: Regenerate masks
        if override_ks is not None:
            ks_bytes = override_ks
        else:
            ks_bytes = self.hyper_gen.generate_keystream(length, session_key)

        if override_ca is not None:
            ca_bytes = override_ca
        else:
            ca_bytes = self.ca_gen.generate_mask(length, session_key)

        if override_pi is not None:
            pi = override_pi
        else:
            pi = self.perm_gen.generate_permutation(length, session_key)

        # Step 3: Invert Backward ARX pass -> f
        f_bytes = self.arx.backward_pass_inverse(ciphertext)

        # Step 4: Invert Forward ARX pass -> q
        q_bytes = self.arx.forward_pass_inverse(f_bytes, ks_bytes, ca_bytes)

        # Step 5: Invert Permutation -> P
        p_bytes = self.perm_gen.apply_inverse_permutation(q_bytes, pi)

        # Step 6: Deserialise to PCM samples if requested
        if as_pcm:
            return bytes_to_pcm(p_bytes)
        return p_bytes

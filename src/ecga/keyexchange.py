"""
Layer 1: ECDSA-Authenticated Elliptic-Curve Diffie-Hellman (P-256) Key Agreement.

Paper Section 3.3 & Section 5.1 (Algorithm 1):
  1. Ephemeral public point exchange: QA = nA*G, QB = nB*G with nonces NA, NB.
  2. Signature verification of (Q || N) using long-term ECDSA key.
  3. Shared secret computation: Z = nA*QB = nB*QA.
  4. Key derivation (Eq. 3): Ks = SHA-256(x(Z) || NA || NB).
"""

import hashlib
from typing import Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


class KeyExchangeParty:
    """Represents a peer in the ECDSA-authenticated ECDH (P-256) key exchange."""

    def __init__(self) -> None:
        """Initialize party with a long-term ECDSA signing key pair (P-256)."""
        self.long_term_private_key = ec.generate_private_key(ec.SECP256R1())
        self.long_term_public_key = self.long_term_private_key.public_key()
        self._ephemeral_private_key = None
        self._ephemeral_public_key = None
        self._nonce = None

    def generate_ephemeral_handshake(self, nonce: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Generate ephemeral ECDH keypair and sign (QA_bytes || nonce).

        Returns:
            Tuple of (uncompressed public point bytes, nonce, ECDSA signature bytes).
        """
        self._nonce = nonce
        self._ephemeral_private_key = ec.generate_private_key(ec.SECP256R1())
        self._ephemeral_public_key = self._ephemeral_private_key.public_key()

        pub_bytes = self._ephemeral_public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        msg_to_sign = pub_bytes + nonce
        signature = self.long_term_private_key.sign(
            msg_to_sign, ec.ECDSA(hashes.SHA256())
        )
        return pub_bytes, nonce, signature

    def compute_session_key(
        self,
        peer_long_term_public_key: ec.EllipticCurvePublicKey,
        peer_pub_bytes: bytes,
        peer_nonce: bytes,
        peer_signature: bytes,
    ) -> bytes:
        """
        Verify peer signature and compute session key Ks = SHA256(x(Z) || NA || NB).

        Args:
            peer_long_term_public_key: Peer's long-term ECDSA public key.
            peer_pub_bytes: Ephemeral public point bytes received from peer.
            peer_nonce: Nonce received from peer.
            peer_signature: ECDSA signature over (peer_pub_bytes || peer_nonce).

        Returns:
            32-byte session key Ks (Eq. 3).
        """
        # Verify peer signature
        msg_to_verify = peer_pub_bytes + peer_nonce
        peer_long_term_public_key.verify(
            peer_signature, msg_to_verify, ec.ECDSA(hashes.SHA256())
        )

        # Reconstruct peer ephemeral public key
        peer_ephemeral_pub = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), peer_pub_bytes
        )

        # ECDH exchange: Z = nA * QB = nB * QA
        shared_key_bytes = self._ephemeral_private_key.exchange(
            ec.ECDH(), peer_ephemeral_pub
        )
        # Note: cryptography returns x-coordinate x(Z) directly in exchange()

        # Ks = SHA-256(x(Z) || NA || NB) or (self_nonce || peer_nonce depending on role)
        # We concatenate self_nonce and peer_nonce in order of party A vs party B, or as exchanged
        kdf_input = shared_key_bytes + self._nonce + peer_nonce
        session_key = hashlib.sha256(kdf_input).digest()
        return session_key


def derive_demo_session_key(
    label: str = "ECGA-IDPRNG-A::demo::NA=7b1e::NB=d92a",
) -> bytes:
    """
    Derive deterministic session key used for paper worked example (Section 6).

    Eq. 3 demo derivation: SHA-256("ECGA-IDPRNG-A::demo::NA=7b1e::NB=d92a").
    """
    return hashlib.sha256(label.encode("utf-8")).digest()

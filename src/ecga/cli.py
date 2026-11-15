"""
Command-Line Interface for ECGA-IDPRNG-A Audio Encryption & Decryption.

Supports encrypting and decrypting real 16-bit PCM WAV audio files.
Usage:
    python -m ecga encrypt --in input.wav --out encrypted.enc [--key HEX_KEY]
    python -m ecga decrypt --in encrypted.enc --out decrypted.wav [--key HEX_KEY]
"""

import argparse
import secrets
import sys
import wave
from typing import Tuple

from ecga.keyexchange import derive_demo_session_key
from ecga.pipeline import AudioFrameCipher

_MAGIC = b"ECG2"


def read_wav_file(filepath: str) -> Tuple[bytes, int, int, int]:
    """Read a 16-bit PCM WAV file and return (raw_pcm_bytes, n_channels, sampwidth, framerate)."""
    with wave.open(filepath, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        pcm_bytes = wf.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"ECGA CLI currently expects 16-bit PCM WAV files (got {sampwidth*8}-bit)")

    return pcm_bytes, n_channels, sampwidth, framerate


def write_wav_file(filepath: str, pcm_bytes: bytes, n_channels: int, sampwidth: int, framerate: int) -> None:
    """Write raw 16-bit PCM bytes to a WAV file."""
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(pcm_bytes)


def encrypt_wav(input_path: str, output_path: str, session_key: bytes) -> None:
    """Encrypt a WAV file frame-by-frame and write encrypted binary file."""
    pcm_bytes, n_channels, sampwidth, framerate = read_wav_file(input_path)
    cipher = AudioFrameCipher()

    # Fresh random session identifier; frame counter increments per frame so no
    # two frames of a session reuse the keystream (Section 5.5).
    session_id = secrets.token_bytes(16)

    # Frame size = 32000 bytes (16000 samples, ~2 seconds at 8kHz mono)
    frame_size = 32000
    encrypted_frames = []

    for ctr, offset in enumerate(range(0, len(pcm_bytes), frame_size)):
        chunk = pcm_bytes[offset : offset + frame_size]
        c_bytes, tag = cipher.encrypt_frame(chunk, session_key, ctr=ctr, session_id=session_id)
        encrypted_frames.append((len(chunk), tag, c_bytes))

    # Write binary container (v2: "ECG2" magic + 16-byte session_id; ctr is the
    # frame index and reconstructed on decrypt).
    with open(output_path, "wb") as f:
        f.write(_MAGIC)
        f.write(session_id)
        f.write(n_channels.to_bytes(2, "big"))
        f.write(sampwidth.to_bytes(2, "big"))
        f.write(framerate.to_bytes(4, "big"))
        f.write(len(encrypted_frames).to_bytes(4, "big"))

        for orig_len, tag, c_bytes in encrypted_frames:
            f.write(orig_len.to_bytes(4, "big"))
            f.write(tag)  # 32 bytes
            f.write(c_bytes)

    print(f"Encrypted '{input_path}' -> '{output_path}' ({len(encrypted_frames)} frames)")


def decrypt_wav(input_path: str, output_path: str, session_key: bytes) -> None:
    """Decrypt an encrypted binary file and recreate WAV file."""
    cipher = AudioFrameCipher()

    with open(input_path, "rb") as f:
        magic = f.read(4)
        if magic != _MAGIC:
            raise ValueError(
                "Unrecognised container (expected 'ECG2'). Re-encrypt with this version."
            )
        session_id = f.read(16)
        n_channels = int.from_bytes(f.read(2), "big")
        sampwidth = int.from_bytes(f.read(2), "big")
        framerate = int.from_bytes(f.read(4), "big")
        n_frames = int.from_bytes(f.read(4), "big")

        decrypted_chunks = []
        for ctr in range(n_frames):
            orig_len = int.from_bytes(f.read(4), "big")
            tag = f.read(32)
            c_bytes = f.read(orig_len)

            p_bytes = cipher.decrypt_frame(
                c_bytes, tag, session_key, ctr=ctr, session_id=session_id, as_pcm=False
            )
            decrypted_chunks.append(p_bytes)

    full_pcm = b"".join(decrypted_chunks)
    write_wav_file(output_path, full_pcm, n_channels, sampwidth, framerate)
    print(f"Decrypted '{input_path}' -> '{output_path}' ({n_frames} frames)")


def main() -> None:
    parser = argparse.ArgumentParser(description="ECGA-IDPRNG-A Audio Encryption Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Encrypt parser
    enc_parser = subparsers.add_parser("encrypt", help="Encrypt a WAV file")
    enc_parser.add_argument("--in", dest="input_file", required=True, help="Input WAV file")
    enc_parser.add_argument("--out", dest="output_file", required=True, help="Output enc file")
    enc_parser.add_argument("--key", dest="hex_key", default=None, help="Hex-encoded 32-byte session key")
    enc_parser.add_argument("--demo", action="store_true", help="Use the PUBLIC demo key (NOT secret)")

    # Decrypt parser
    dec_parser = subparsers.add_parser("decrypt", help="Decrypt an enc file to WAV")
    dec_parser.add_argument("--in", dest="input_file", required=True, help="Input enc file")
    dec_parser.add_argument("--out", dest="output_file", required=True, help="Output WAV file")
    dec_parser.add_argument("--key", dest="hex_key", default=None, help="Hex-encoded 32-byte session key")
    dec_parser.add_argument("--demo", action="store_true", help="Use the PUBLIC demo key (NOT secret)")

    args = parser.parse_args()

    if args.hex_key:
        session_key = bytes.fromhex(args.hex_key)
        if len(session_key) != 32:
            parser.error("--key must be exactly 32 bytes (64 hex chars)")
    elif args.demo:
        sys.stderr.write("WARNING: using the PUBLIC DEMO KEY - NOT SECRET. For demonstration only.\n")
        session_key = derive_demo_session_key()
    else:
        parser.error("No key supplied. Pass --key HEX (32 bytes) or --demo for the public demo key.")

    if args.command == "encrypt":
        encrypt_wav(args.input_file, args.output_file, session_key)
    elif args.command == "decrypt":
        decrypt_wav(args.input_file, args.output_file, session_key)


if __name__ == "__main__":
    main()

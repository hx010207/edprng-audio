"""
Command-Line Interface for ECGA-IDPRNG-A Audio Encryption & Decryption.

Supports encrypting and decrypting real 16-bit PCM WAV audio files.
Usage:
    python -m ecga encrypt --in input.wav --out encrypted.enc [--key HEX_KEY]
    python -m ecga decrypt --in encrypted.enc --out decrypted.wav [--key HEX_KEY]
"""

import argparse
import os
import sys
import wave
from typing import Tuple

from ecga.keyexchange import derive_demo_session_key
from ecga.pipeline import AudioFrameCipher


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

    # Frame size = 32000 bytes (16000 samples, ~2 seconds at 8kHz mono)
    frame_size = 32000
    encrypted_frames = []

    for offset in range(0, len(pcm_bytes), frame_size):
        chunk = pcm_bytes[offset : offset + frame_size]
        c_bytes, tag = cipher.encrypt_frame(chunk, session_key)
        encrypted_frames.append((len(chunk), tag, c_bytes))

    # Write binary container
    with open(output_path, "wb") as f:
        # Header: channels (2 bytes), sampwidth (2 bytes), framerate (4 bytes), frame count (4 bytes)
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
        n_channels = int.from_bytes(f.read(2), "big")
        sampwidth = int.from_bytes(f.read(2), "big")
        framerate = int.from_bytes(f.read(4), "big")
        n_frames = int.from_bytes(f.read(4), "big")

        decrypted_chunks = []
        for _ in range(n_frames):
            orig_len = int.from_bytes(f.read(4), "big")
            tag = f.read(32)
            c_bytes = f.read(orig_len)

            p_bytes = cipher.decrypt_frame(c_bytes, tag, session_key, as_pcm=False)
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

    # Decrypt parser
    dec_parser = subparsers.add_parser("decrypt", help="Decrypt an enc file to WAV")
    dec_parser.add_argument("--in", dest="input_file", required=True, help="Input enc file")
    dec_parser.add_argument("--out", dest="output_file", required=True, help="Output WAV file")
    dec_parser.add_argument("--key", dest="hex_key", default=None, help="Hex-encoded 32-byte session key")

    args = parser.parse_args()

    if args.hex_key:
        session_key = bytes.fromhex(args.hex_key)
    else:
        session_key = derive_demo_session_key()

    if args.command == "encrypt":
        encrypt_wav(args.input_file, args.output_file, session_key)
    elif args.command == "decrypt":
        decrypt_wav(args.input_file, args.output_file, session_key)


if __name__ == "__main__":
    main()

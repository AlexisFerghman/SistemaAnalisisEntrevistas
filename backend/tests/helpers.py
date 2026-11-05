"""Utilidades compartidas por las pruebas del backend."""

from __future__ import annotations

import io
import wave


def wav_bytes(seconds: float = 1.0, rate: int = 16000, channels: int = 1) -> bytes:
    """Genera un WAV PCM silencioso válido, sin datos reales."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x00\x00" * int(seconds * rate) * channels)
    return buffer.getvalue()

"""Adaptador de transcripción: contrato interno, normalización y política de reintentos.

El resto de la aplicación no conoce el motor concreto (research D15, D16).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

LANGUAGE = "es"


class TranscriptionError(Exception):
    """Base de los fallos del motor de transcripción."""


class TranscriptionRejected(TranscriptionError):
    """El motor rechaza el archivo (formato no soportado o audio corrupto)."""


class TranscriptionTimeout(TranscriptionError):
    """El motor no respondió dentro del límite configurado."""


class TranscriptionUnavailable(TranscriptionError):
    """El motor no pudo inicializarse o se quedó sin recursos."""


class TranscriptionInvalidResponse(TranscriptionError):
    """La salida no se puede normalizar (vacía o sin segmentos válidos)."""


class TranscriptionCancelled(TranscriptionError):
    """El usuario canceló la operación entre segmentos."""


class BaseEngine(Protocol):
    name: str

    def run(
        self,
        audio_path: Path,
        language: str,
        on_segment: Callable[[int], None] | None,
        should_cancel: Callable[[], bool] | None,
    ) -> list[dict[str, Any]]:
        ...


@dataclass(frozen=True)
class TranscriptionResult:
    language: str
    provider: str
    retry_count: int
    segments: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "provider": self.provider,
            "retry_count": self.retry_count,
            "segments": self.segments,
        }


def get_engine() -> BaseEngine:
    """Selecciona el motor según TRANSCRIPTION_ENGINE (local por defecto)."""
    name = os.getenv("TRANSCRIPTION_ENGINE", "local").strip().lower()

    if name == "fake":
        from .fake_engine import FakeEngine

        return FakeEngine()

    try:
        from .faster_whisper_engine import FasterWhisperEngine
    except Exception as exc:  # motor aún no disponible o dependencia rota
        raise TranscriptionUnavailable(f"Motor de transcripción no disponible: {exc}") from exc

    return FasterWhisperEngine()


def normalize_segments(
    raw_segments: list[dict[str, Any]],
    duration_seconds: float,
) -> list[dict[str, Any]]:
    """Ordena, recorta y numera los segmentos (contracts/transcription-adapter.md)."""
    cleaned: list[dict[str, Any]] = []

    for raw in raw_segments or []:
        text = (raw.get("text") or "").strip()
        if not text:
            continue

        start = max(0.0, float(raw.get("start_time") or 0.0))
        end = float(raw.get("end_time") or 0.0)
        if end > duration_seconds:
            end = float(duration_seconds)
        if end <= start:
            continue

        cleaned.append({"start_time": start, "end_time": end, "text": text, "words": raw.get("words") or []})

    cleaned.sort(key=lambda segment: segment["start_time"])

    merged: list[dict[str, Any]] = []
    previous_end = 0.0
    for segment in cleaned:
        start = max(segment["start_time"], previous_end)
        end = segment["end_time"]
        if end <= start:
            continue
        segment["start_time"] = start
        segment["end_time"] = end
        previous_end = end
        merged.append(segment)

    if not merged:
        raise TranscriptionInvalidResponse("La transcripción no contiene segmentos válidos")

    for index, segment in enumerate(merged, start=1):
        segment["id"] = f"segment-{index:03d}"
        segment["words"] = _normalize_words(segment["words"], segment["start_time"], segment["end_time"])

    return merged


def _normalize_words(
    words: list[dict[str, Any]],
    segment_start: float,
    segment_end: float,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for word in words or []:
        text = (word.get("text") or "").strip()
        if not text:
            continue
        start = min(max(float(word.get("start_time") or segment_start), segment_start), segment_end)
        end = min(max(float(word.get("end_time") or start), start), segment_end)
        if end <= start:
            end = min(start + 0.001, segment_end)
        normalized.append({"text": text, "start_time": start, "end_time": end})
    return normalized


def transcribe(
    audio_path: Path,
    duration_seconds: float,
    language: str = LANGUAGE,
    on_segment: Callable[[int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> TranscriptionResult:
    """Transcribe con un único reintento para timeout y disponibilidad (RF-006)."""
    engine = get_engine()
    retry_count = 0

    try:
        raw = engine.run(audio_path, language, on_segment, should_cancel)
    except (TranscriptionTimeout, TranscriptionUnavailable):
        retry_count = 1
        raw = engine.run(audio_path, language, on_segment, should_cancel)

    segments = normalize_segments(raw, duration_seconds)
    return TranscriptionResult(
        language=language,
        provider=engine.name,
        retry_count=retry_count,
        segments=segments,
    )

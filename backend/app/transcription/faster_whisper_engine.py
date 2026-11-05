"""Motor real: faster-whisper con modelo `base` precargado en la imagen (research D02, D03, D21)."""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any, Callable

from .adapter import (
    TranscriptionCancelled,
    TranscriptionRejected,
    TranscriptionUnavailable,
)

logger = logging.getLogger(__name__)

MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")

_model: Any | None = None
_model_lock = threading.Lock()


def _load_model() -> Any:
    """Carga perezosa y única por proceso."""
    global _model
    with _model_lock:
        if _model is not None:
            return _model

        from faster_whisper import WhisperModel

        try:
            logger.info("Cargando modelo %s en GPU", MODEL_SIZE)
            _model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")
        except Exception:
            logger.info("GPU no disponible; cargando modelo %s en CPU (int8)", MODEL_SIZE)
            try:
                _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
            except Exception as exc:  # pragma: no cover - depende del entorno
                raise TranscriptionUnavailable(f"No se pudo cargar el modelo: {exc}") from exc

        return _model


def reset_model() -> None:
    """Libera el modelo cacheado (solo pruebas)."""
    global _model
    with _model_lock:
        _model = None


class FasterWhisperEngine:
    name = "local"

    def run(
        self,
        audio_path: Path,
        language: str,
        on_segment: Callable[[int], None] | None,
        should_cancel: Callable[[], bool] | None,
    ) -> list[dict[str, Any]]:
        model = _load_model()

        try:
            segments, _info = model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=True,
                vad_filter=False,
                beam_size=5,
            )
        except TranscriptionUnavailable:
            raise
        except Exception as exc:
            raise TranscriptionRejected(f"El motor rechazó el audio: {exc}") from exc

        result: list[dict[str, Any]] = []
        for index, segment in enumerate(segments):
            # La cancelación se comprueba entre segmentos: el generador avanza aquí (research D12).
            if should_cancel is not None and should_cancel():
                raise TranscriptionCancelled("Operación cancelada entre segmentos")

            words = [
                {
                    "text": (word.word or "").strip(),
                    "start_time": float(word.start),
                    "end_time": float(word.end),
                }
                for word in (getattr(segment, "words", None) or [])
            ]
            result.append(
                {
                    "start_time": float(segment.start),
                    "end_time": float(segment.end),
                    "text": (segment.text or "").strip(),
                    "words": words,
                }
            )
            if on_segment is not None:
                on_segment(index)

        return result

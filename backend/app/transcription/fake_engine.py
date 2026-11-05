"""Motor determinista para pruebas y escenarios de error (research D20).

Nunca carga el modelo real. El fallo se inyecta con FAKE_TRANSCRIBER_ERROR:
timeout | unavailable | rejected | invalid | cancelled.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable

from .adapter import (
    TranscriptionCancelled,
    TranscriptionInvalidResponse,
    TranscriptionRejected,
    TranscriptionTimeout,
    TranscriptionUnavailable,
)

FAKE_SEGMENTS: list[dict[str, Any]] = [
    {
        "start_time": 0.0,
        "end_time": 2.5,
        "text": "Hola, esta es una entrevista sintetica de prueba.",
        "words": [
            {"text": "Hola,", "start_time": 0.0, "end_time": 0.4},
            {"text": "esta", "start_time": 0.4, "end_time": 0.7},
            {"text": "es", "start_time": 0.7, "end_time": 0.9},
            {"text": "una", "start_time": 0.9, "end_time": 1.1},
            {"text": "entrevista", "start_time": 1.1, "end_time": 1.7},
            {"text": "sintetica", "start_time": 1.7, "end_time": 2.2},
            {"text": "de", "start_time": 2.2, "end_time": 2.3},
            {"text": "prueba.", "start_time": 2.3, "end_time": 2.5},
        ],
    },
    {
        "start_time": 2.5,
        "end_time": 5.0,
        "text": "No contiene datos reales ni identificables.",
        "words": [
            {"text": "No", "start_time": 2.5, "end_time": 2.7},
            {"text": "contiene", "start_time": 2.7, "end_time": 3.2},
            {"text": "datos", "start_time": 3.2, "end_time": 3.6},
            {"text": "reales", "start_time": 3.6, "end_time": 4.0},
            {"text": "ni", "start_time": 4.0, "end_time": 4.2},
            {"text": "identificables.", "start_time": 4.2, "end_time": 5.0},
        ],
    },
    {
        "start_time": 5.0,
        "end_time": 7.0,
        "text": "Fin de la transcripcion de ejemplo.",
        "words": [
            {"text": "Fin", "start_time": 5.0, "end_time": 5.3},
            {"text": "de", "start_time": 5.3, "end_time": 5.4},
            {"text": "la", "start_time": 5.4, "end_time": 5.6},
            {"text": "transcripcion", "start_time": 5.6, "end_time": 6.4},
            {"text": "de", "start_time": 6.4, "end_time": 6.5},
            {"text": "ejemplo.", "start_time": 6.5, "end_time": 7.0},
        ],
    },
]

_ERRORS = {
    "timeout": TranscriptionTimeout,
    "unavailable": TranscriptionUnavailable,
    "rejected": TranscriptionRejected,
    "invalid": TranscriptionInvalidResponse,
}


class FakeEngine:
    name = "fake"

    def run(
        self,
        audio_path: Path,
        language: str,
        on_segment: Callable[[int], None] | None,
        should_cancel: Callable[[], bool] | None,
    ) -> list[dict[str, Any]]:
        error = (os.getenv("FAKE_TRANSCRIBER_ERROR") or "").strip().lower()
        delay = float(os.getenv("FAKE_TRANSCRIBER_DELAY", "0") or 0)

        if error in _ERRORS:
            raise _ERRORS[error]("Fallo simulado del motor de transcripción")

        if error == "cancelled":
            raise TranscriptionCancelled("Operación cancelada antes de empezar")

        for index, _segment in enumerate(FAKE_SEGMENTS):
            if delay > 0:
                time.sleep(delay)
            if should_cancel is not None and should_cancel():
                raise TranscriptionCancelled("Operación cancelada entre segmentos")
            if on_segment is not None:
                on_segment(index)

        return [dict(segment) for segment in FAKE_SEGMENTS]

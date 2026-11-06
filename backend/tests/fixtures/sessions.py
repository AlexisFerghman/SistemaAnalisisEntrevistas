"""Documentos de sesión deterministas para las pruebas de la feature 003."""

from __future__ import annotations

from typing import Any


def sample_document(
    *,
    segment_count: int = 60,
    words_per_segment: int = 150,
    session_id: str = "session-current",
) -> dict[str, Any]:
    """Documento de ~12 min con segmentos y marcas por palabra.

    Es determinista y no contiene datos reales: solo texto sintético repetido.
    """
    duration = float(segment_count * 30)
    segments: list[dict[str, Any]] = []

    for segment_index in range(segment_count):
        start = segment_index * 30.0
        end = start + 30.0
        step = 30.0 / words_per_segment
        words = [
            {
                "text": f"palabra-{segment_index:02d}-{word_index:02d}",
                "start_time": round(start + word_index * step, 3),
                "end_time": round(start + (word_index + 1) * step, 3),
            }
            for word_index in range(words_per_segment)
        ]
        segments.append(
            {
                "id": f"segment-{segment_index + 1:03d}",
                "start_time": round(start, 3),
                "end_time": round(end, 3),
                "text": " ".join(word["text"] for word in words),
                "words": words,
            }
        )

    return {
        "version": 1,
        "session_id": session_id,
        "status": "ready",
        "audio": {
            "filename": "entrevista-sintetica.wav",
            "mime_type": "audio/wav",
            "size_bytes": 3_210_000,
            "duration_seconds": duration,
            "storage_ref": "current.wav",
        },
        "transcription": {
            "language": "es",
            "provider": "fake",
            "retry_count": 0,
            "segments": segments,
        },
        "annotations": [
            {
                "id": "annotation-001",
                "text": "Observación sintética de prueba.",
                "segment_id": "segment-001",
                "start_time": 1.0,
                "end_time": 2.0,
            },
            {
                "id": "annotation-002",
                "text": "Segunda observación sintética.",
                "segment_id": "segment-002",
                "start_time": 31.0,
                "end_time": 32.0,
            },
        ],
        "operation": None,
    }


def legacy_document() -> dict[str, Any]:
    """Documento con el identificador literal que existía antes de `003`."""
    return sample_document(session_id="session-current")

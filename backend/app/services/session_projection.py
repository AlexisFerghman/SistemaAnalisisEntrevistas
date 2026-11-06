"""Proyección de lectura de la sesión (RF-020, RF-021, research D34)."""

from __future__ import annotations

import copy
from typing import Any


def summarize_document(document: dict[str, Any]) -> dict[str, Any]:
    """Devuelve una copia sin `words` y con `words_count` por segmento.

    El documento original no se modifica: la base de datos conserva las marcas.
    """
    summary = copy.deepcopy(document)
    transcription = summary.get("transcription")
    if not isinstance(transcription, dict):
        return summary

    segments = transcription.get("segments")
    if not isinstance(segments, list):
        return summary

    for segment in segments:
        if not isinstance(segment, dict):
            continue
        words = segment.pop("words", None)
        segment["words_count"] = len(words) if isinstance(words, list) else 0

    return summary


def segment_words(document: dict[str, Any], segment_id: str) -> list[dict[str, Any]] | None:
    """Devuelve las palabras de un segmento o `None` si el segmento no existe."""
    transcription = document.get("transcription")
    if not isinstance(transcription, dict):
        return None

    for segment in transcription.get("segments") or []:
        if isinstance(segment, dict) and segment.get("id") == segment_id:
            words = segment.get("words") or []
            return words if isinstance(words, list) else []
    return None

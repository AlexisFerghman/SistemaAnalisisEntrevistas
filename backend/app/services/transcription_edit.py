"""Validación y normalización de la transcripción editada (RF-008, RNF-004)."""

from __future__ import annotations

from typing import Any

TOLERANCE = 1e-6


class EditError(Exception):
    """Error de validación con un código estable para el sobre de errores."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def redistribute_words(text: str, start: float, end: float) -> list[dict[str, Any]]:
    """Reparte las marcas por palabra de forma proporcional al texto nuevo.

    Se usa cuando el texto cambia: las marcas antiguas dejarían de corresponder al contenido.
    """
    tokens = text.split()
    if not tokens:
        return []

    step = (end - start) / len(tokens)
    words = []
    for index, token in enumerate(tokens):
        word_start = start + index * step
        word_end = start + (index + 1) * step
        words.append(
            {
                "text": token,
                "start_time": round(word_start, 3),
                "end_time": round(word_end, 3),
            }
        )
    return words


def _clamp_words(words: list[dict[str, Any]], start: float, end: float) -> list[dict[str, Any]]:
    clamped = []
    for word in words:
        word_start = min(max(float(word.get("start_time", start)), start), end)
        word_end = min(max(float(word.get("end_time", word_start)), word_start), end)
        if word_end <= word_start:
            word_end = min(word_start + 0.001, end)
        clamped.append(
            {
                "text": word.get("text", ""),
                "start_time": round(word_start, 3),
                "end_time": round(word_end, 3),
            }
        )
    return clamped


def apply_edit(
    previous_segments: list[dict[str, Any]],
    incoming: Any,
    duration_seconds: float,
) -> list[dict[str, Any]]:
    """Valida la lista completa y devuelve los segmentos normalizados."""
    if not isinstance(incoming, list) or not incoming:
        raise EditError("invalid_timestamps", "La transcripción no puede quedar vacía")

    previous_by_id = {segment.get("id"): segment for segment in previous_segments}
    result: list[dict[str, Any]] = []
    previous_end = 0.0

    for index, segment in enumerate(incoming, start=1):
        if not isinstance(segment, dict):
            raise EditError("invalid_timestamps", "Cada segmento debe ser un objeto")

        segment_id = str(segment.get("id") or f"segment-{index:03d}")
        text = (segment.get("text") or "").strip()
        if not text:
            raise EditError("empty_text", f"El segmento {segment_id} no tiene texto")

        try:
            start = float(segment["start_time"])
            end = float(segment["end_time"])
        except (KeyError, TypeError, ValueError) as exc:
            raise EditError(
                "invalid_timestamps",
                f"El segmento {segment_id} necesita marcas numéricas de inicio y fin",
            ) from exc

        if start < 0 or end <= start:
            raise EditError("invalid_timestamps", f"El segmento {segment_id} tiene un rango inválido")
        if end > duration_seconds + TOLERANCE:
            raise EditError(
                "invalid_timestamps",
                f"El segmento {segment_id} termina después del audio",
            )
        if start < previous_end - TOLERANCE:
            raise EditError("invalid_timestamps", f"El segmento {segment_id} se solapa con el anterior")
        previous_end = end

        original = previous_by_id.get(segment_id)
        text_changed = original is None or (original.get("text") or "").strip() != text
        if text_changed:
            words = redistribute_words(text, start, end)
        else:
            words = _clamp_words(original.get("words") or [], start, end)

        result.append(
            {
                "id": segment_id,
                "start_time": round(start, 3),
                "end_time": round(end, 3),
                "text": text,
                "words": words,
            }
        )

    return result

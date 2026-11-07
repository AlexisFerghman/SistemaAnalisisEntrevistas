"""Validación y persistencia del audio cargado (RF-001, RF-002, research D04/D06)."""

from __future__ import annotations

from pathlib import Path

import av
from fastapi import UploadFile

MAX_BYTES = 125_829_120  # 120 MB
CHUNK_SIZE = 1024 * 1024

ALLOWED_TYPES: dict[str, set[str]] = {
    ".mp3": {"audio/mpeg", "audio/mp3"},
    ".wav": {"audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave"},
}


class AudioValidationError(Exception):
    """Rechazo de un audio con un código estable para el sobre de errores."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


GENERIC_TYPES = {"", "application/octet-stream", "binary/octet-stream"}


def content_length_exceeded(content_length: str | None, max_bytes: int = MAX_BYTES) -> bool:
    """Indica si el `Content-Length` declarado supera el límite sin leer el cuerpo."""
    if not content_length:
        return False
    try:
        return int(content_length) > max_bytes
    except ValueError:
        return False


def validate_upload(filename: str | None, content_type: str | None) -> str:
    """Comprueba extensión y MIME declarado. Devuelve la extensión normalizada.

    Un MIME genérico (`application/octet-stream`) se acepta: algunos navegadores y clientes no
    identifican `.wav`. La estructura real del audio se valida después con `inspect_audio`.
    """
    if not filename:
        raise AudioValidationError("missing_file", "No se recibió ningún archivo")

    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_TYPES:
        raise AudioValidationError(
            "unsupported_format",
            "Solo se admiten archivos .mp3 o .wav",
        )

    if content_type:
        declared = content_type.split(";")[0].strip().lower()
        if declared not in GENERIC_TYPES and declared not in ALLOWED_TYPES[suffix]:
            raise AudioValidationError(
                "unsupported_format",
                f"El tipo {declared} no corresponde a la extensión {suffix}",
            )

    return suffix


def persist_upload(upload: UploadFile, destination: Path) -> int:
    """Copia el archivo por bloques, cortando en cuanto supera el límite de 120 MB."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    try:
        with destination.open("wb") as target:
            while True:
                chunk = upload.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise AudioValidationError(
                        "payload_too_large",
                        "El archivo supera el límite de 120 MB",
                    )
                target.write(chunk)
    except AudioValidationError:
        destination.unlink(missing_ok=True)
        raise
    finally:
        upload.file.close()

    if total == 0:
        destination.unlink(missing_ok=True)
        raise AudioValidationError("invalid_audio", "El archivo está vacío")

    return total


def inspect_audio(path: Path) -> float:
    """Verifica que el archivo contiene audio legible y devuelve su duración en segundos."""
    try:
        with av.open(str(path)) as container:
            if not container.streams.audio:
                raise AudioValidationError(
                    "invalid_audio",
                    "El archivo no contiene una pista de audio",
                )
            stream = container.streams.audio[0]
            duration = 0.0
            if stream.duration and stream.time_base:
                duration = float(stream.duration * stream.time_base)
            elif container.duration:
                duration = float(container.duration / av.time_base)

            if duration <= 0:
                for frame in container.decode(stream):
                    rate = frame.sample_rate or 1
                    duration = float(frame.time or 0.0) + (1.0 / rate)

            if duration <= 0:
                raise AudioValidationError(
                    "invalid_audio",
                    "No se pudo determinar la duración del audio",
                )
            return duration
    except AudioValidationError:
        raise
    except Exception as exc:  # av lanza varios tipos según el códec
        raise AudioValidationError(
            "invalid_audio",
            f"El archivo no es un audio legible: {exc}",
        ) from exc

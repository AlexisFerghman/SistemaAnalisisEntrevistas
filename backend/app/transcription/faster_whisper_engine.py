"""Motor real: `faster-whisper` con `large-v3-turbo`, glosario y VAD.

Decisiones: research D01-D10. El resto de la aplicación solo conoce el
contrato de `adapter.py`; este módulo no expone el modelo ni sus detalles.
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

from .adapter import (
    TranscriptionCancelled,
    TranscriptionRejected,
    TranscriptionUnavailable,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "large-v3-turbo"
DEFAULT_GLOSSARY = Path(__file__).with_name("glosario-whisper.txt")
DEFAULT_BEAM_SIZE = 5

_model: Any | None = None
_model_device: str | None = None
_model_lock = threading.Lock()

_RESOURCE_MARKERS = (
    "out of memory",
    "cuda",
    "cudnn",
    "cublas",
    "memory",
    "allocation",
    "device",
)
_DECODE_EXCEPTION_NAMES = {
    "InvalidDataError",
    "EOFError",
    "FileNotFoundError",
    "PermissionError",
    "IsADirectoryError",
}


def _env_flag(name: str, default: bool = True) -> bool:
    """Lee un flag booleano de entorno; valores 0/false/no/off lo desactivan."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _model_name() -> str:
    return (os.getenv("WHISPER_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _glossary_path() -> Path:
    override = (os.getenv("WHISPER_GLOSSARY_PATH") or "").strip()
    return Path(override) if override else DEFAULT_GLOSSARY


def _glossary_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _load_glossary() -> str | None:
    """Lee el glosario en UTF-8. Un archivo ausente o vacío no rompe la carga."""
    path = _glossary_path()
    try:
        text = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.warning(
            "Glosario no encontrado en %s; se transcribe sin initial_prompt", path
        )
        return None
    except OSError as exc:
        logger.warning(
            "No se pudo leer el glosario %s (%s); se transcribe sin initial_prompt",
            path,
            exc,
        )
        return None

    if not text:
        logger.warning("Glosario vacío en %s; se transcribe sin initial_prompt", path)
        return None

    logger.info(
        "Glosario cargado desde %s (hash=%s, %d caracteres)",
        path,
        _glossary_hash(text),
        len(text),
    )
    return text


def _is_resource_error(exc: BaseException) -> bool:
    if isinstance(exc, MemoryError):
        return True
    message = str(exc).lower()
    return any(marker in message for marker in _RESOURCE_MARKERS)


def _is_decode_error(exc: BaseException) -> bool:
    if isinstance(
        exc, (FileNotFoundError, PermissionError, IsADirectoryError, EOFError)
    ):
        return True
    return (
        type(exc).__name__ in _DECODE_EXCEPTION_NAMES
        or type(exc).__module__.startswith("av.")
    )


def _create_model(
    model_name: str,
    device: str,
    compute_type: str,
    local_files_only: bool,
) -> Any:
    """Frontera de importación para poder simular el modelo en pruebas."""
    from faster_whisper import WhisperModel

    return WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        local_files_only=local_files_only,
    )


def _load_model() -> Any:
    """Carga perezosa y única por proceso, con GPU y fallback a CPU."""
    global _model, _model_device
    with _model_lock:
        if _model is not None:
            return _model

        model_name = _model_name()
        local_files_only = _env_flag("WHISPER_LOCAL_FILES_ONLY", True)
        started = time.perf_counter()

        try:
            logger.info("Cargando modelo %s en GPU (float16)", model_name)
            _model = _create_model(
                model_name, "cuda", "float16", local_files_only
            )
            _model_device = "cuda/float16"
        except Exception as gpu_exc:
            logger.info(
                "GPU no disponible (%s); cargando %s en CPU (int8)",
                gpu_exc,
                model_name,
            )
            try:
                _model = _create_model(
                    model_name, "cpu", "int8", local_files_only
                )
                _model_device = "cpu/int8"
            except Exception as cpu_exc:  # pragma: no cover - depende del entorno
                raise TranscriptionUnavailable(
                    f"No se pudo cargar el modelo {model_name}: {cpu_exc}"
                ) from cpu_exc

        logger.info(
            "Modelo %s cargado en %.2f s (dispositivo=%s)",
            model_name,
            time.perf_counter() - started,
            _model_device,
        )
        return _model


def reset_model() -> None:
    """Libera el modelo cacheado (solo pruebas)."""
    global _model, _model_device
    with _model_lock:
        _model = None
        _model_device = None


class FasterWhisperEngine:
    name = "local"

    def run(
        self,
        audio_path: Path,
        language: str,
        on_segment: Callable[[int], None] | None,
        should_cancel: Callable[[], bool] | None,
    ) -> list[dict[str, Any]]:
        if should_cancel is not None and should_cancel():
            raise TranscriptionCancelled("Operación cancelada antes de cargar el modelo")

        model = _load_model()

        if should_cancel is not None and should_cancel():
            raise TranscriptionCancelled("Operación cancelada antes de transcribir")

        glossary = _load_glossary()
        started = time.perf_counter()
        try:
            segments, _info = model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=True,
                vad_filter=_env_flag("WHISPER_VAD_FILTER", True),
                beam_size=DEFAULT_BEAM_SIZE,
                initial_prompt=glossary,
            )

            result: list[dict[str, Any]] = []
            for index, segment in enumerate(segments):
                # La cancelación se comprueba entre segmentos: el generador avanza aquí.
                if should_cancel is not None and should_cancel():
                    raise TranscriptionCancelled(
                        "Operación cancelada entre segmentos"
                    )

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
        except (TranscriptionUnavailable, TranscriptionRejected, TranscriptionCancelled):
            raise
        except Exception as exc:
            if _is_resource_error(exc):
                raise TranscriptionUnavailable(
                    f"Recursos insuficientes para transcribir: {exc}"
                ) from exc
            if _is_decode_error(exc):
                raise TranscriptionRejected(
                    f"El motor rechazó el audio: {exc}"
                ) from exc
            logger.exception("Fallo inesperado del motor de transcripción")
            raise TranscriptionUnavailable(
                f"Fallo del motor de transcripción: {exc}"
            ) from exc

        if not result:
            raise TranscriptionRejected(
                "No se detectó voz en el audio o el filtro de actividad eliminó todo el contenido"
            )

        elapsed = time.perf_counter() - started
        word_count = sum(len(segment["words"]) for segment in result)
        try:
            size_bytes = audio_path.stat().st_size
        except OSError:
            size_bytes = None
        logger.info(
            "Transcripción completada: archivo=%s bytes=%s segmentos=%d palabras=%d tiempo=%.2f s",
            audio_path.name,
            size_bytes,
            len(result),
            word_count,
            elapsed,
        )
        return result

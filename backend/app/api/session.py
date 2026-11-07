"""Carga de audio y cancelación de la operación en curso."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

from ..services import audio_validation, session_projection, session_store
from ..transcription import adapter
from ..transcription.adapter import TranscriptionCancelled
from .errors import ApiError

router = APIRouter(prefix="/api/session", tags=["session"])

SAFE_STATUSES = {"empty", "ready", "reviewed", "error"}


def _previous_status(document: dict[str, Any] | None) -> str:
    if not document:
        return "empty"
    status = document.get("status")
    if status in SAFE_STATUSES:
        return status
    if document.get("audio") and document.get("transcription"):
        return "ready"
    return "empty"


def _mark_audio_error(document: dict[str, Any]) -> None:
    """Conserva el documento para diagnóstico y lo deja en `error` (data-model.md)."""
    document["status"] = "error"
    session_store.save_document(document)


@router.post("/audio")
def upload_audio(file: UploadFile | None = File(None)) -> dict[str, Any]:
    """Valida y transcribe en la misma petición (research D10, D11).

    Es una función síncrona: FastAPI la ejecuta en el threadpool y el event loop sigue
    atendiendo `/health` mientras dura la transcripción.
    """
    if file is None:
        raise audio_validation.AudioValidationError(
            "missing_file",
            "No se recibió ningún archivo",
        )

    suffix = audio_validation.validate_upload(file.filename, file.content_type)

    tmp_path = session_store.AUDIO_DIR / f"{session_store.TMP_PREFIX}{uuid.uuid4().hex}{suffix}"
    try:
        size = audio_validation.persist_upload(file, tmp_path)
        duration = audio_validation.inspect_audio(tmp_path)
    except Exception:
        session_store.discard_temporary(tmp_path)
        raise

    previous = _previous_status(session_store.get_document())

    if not session_store.acquire_operation(previous):
        session_store.discard_temporary(tmp_path)
        raise ApiError("busy", "Ya hay una carga en curso", 409)

    try:
        result = adapter.transcribe(
            tmp_path,
            duration,
            language=adapter.LANGUAGE,
            should_cancel=session_store.cancel_requested,
        )

        new_document: dict[str, Any] = {
            "version": 1,
            "session_id": "",
            "status": "ready",
            "audio": {
                "filename": file.filename,
                "mime_type": file.content_type or "application/octet-stream",
                "size_bytes": size,
                "duration_seconds": round(duration, 3),
                "storage_ref": f"current{suffix}",
            },
            "transcription": result.as_dict(),
            "annotations": [],
            "operation": None,
        }
        session_store.replace_session(tmp_path, duration, new_document)
    except TranscriptionCancelled:
        session_store.clear_operation(previous)
        session_store.discard_temporary(tmp_path)
        current = session_store.get_document() or {}
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "cancelled",
                    "message": "La carga se canceló y se conservó la sesión anterior",
                },
                "session": current,
            },
        )
    except Exception:
        session_store.clear_operation(previous)
        session_store.discard_temporary(tmp_path)
        raise
    finally:
        session_store.release_operation()

    return {"session": new_document, "cancelled": False}


@router.post("/cancel")
def cancel_upload() -> JSONResponse:
    """Cancelación cooperativa: el bucle de segmentos aborta al terminar el actual (research D12)."""
    if not session_store.request_cancel():
        raise ApiError("not_processing", "No hay una operación en curso", 409)

    return JSONResponse(
        status_code=202,
        content={"status": "processing", "cancel_requested": True},
    )


@router.get("/segments/{segment_id}/words")
def get_segment_words(segment_id: str) -> dict[str, Any]:
    """Devuelve solo las marcas por palabra del segmento solicitado (RF-021)."""
    document = session_store.get_document()
    if document is None:
        raise ApiError("session_not_initialized", "No hay una sesión cargada", 404)

    words = session_projection.segment_words(document, segment_id)
    if words is None:
        raise ApiError("segment_not_found", "El segmento no existe", 404)

    return {"segment_id": segment_id, "words": words}


@router.get("/audio")
def get_audio(request: Request):
    """Entrega el audio vigente con soporte de peticiones parciales (RF-007)."""
    document = session_store.get_document()
    if document is None or not document.get("audio"):
        raise ApiError("no_audio", "La sesión no tiene audio", 404)

    audio = document["audio"]
    storage_ref = audio.get("storage_ref")
    if not storage_ref:
        _mark_audio_error(document)
        raise ApiError("audio_missing", "El audio de la sesión no está registrado", 500)

    path = session_store.AUDIO_DIR / storage_ref
    if not path.is_file():
        _mark_audio_error(document)
        raise ApiError("audio_missing", "El archivo de audio no existe en el almacenamiento", 500)

    media_type = audio.get("mime_type") or "application/octet-stream"
    total = path.stat().st_size
    request_range = request.headers.get("range")

    if not request_range:
        return FileResponse(path, media_type=media_type, headers={"Accept-Ranges": "bytes"})

    bounds = _parse_range(request_range, total)
    if bounds is None:
        return Response(
            status_code=416,
            headers={"Content-Range": f"bytes */{total}", "Accept-Ranges": "bytes"},
        )

    start, end = bounds
    length = end - start + 1

    def stream():
        with path.open("rb") as handle:
            handle.seek(start)
            remaining = length
            while remaining > 0:
                chunk = handle.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        stream(),
        status_code=206,
        media_type=media_type,
        headers={
            "Content-Range": f"bytes {start}-{end}/{total}",
            "Content-Length": str(length),
            "Accept-Ranges": "bytes",
        },
    )


def _parse_range(header: str, total: int) -> tuple[int, int] | None:
    """Interpreta `bytes=start-end` y `bytes=start-`. Devuelve `None` si no es satisfacible."""
    if not header.lower().startswith("bytes=") or total == 0:
        return None

    spec = header.split("=", 1)[1].split(",")[0].strip()
    if "-" not in spec:
        return None

    raw_start, raw_end = spec.split("-", 1)
    try:
        if raw_start == "":
            suffix = int(raw_end)
            if suffix <= 0:
                return None
            start = max(total - suffix, 0)
            return start, total - 1

        start = int(raw_start)
        end = int(raw_end) if raw_end else total - 1
    except ValueError:
        return None

    if start < 0 or start >= total or end < start:
        return None

    return start, min(end, total - 1)

"""Edición de la transcripción vigente."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ..services import session_store
from ..services.transcription_edit import EditError, apply_edit
from .errors import ApiError

router = APIRouter(prefix="/api/session", tags=["transcription"])

EDITABLE_STATUSES = {"ready", "reviewed"}


@router.put("/transcription")
def update_transcription(payload: dict[str, Any]) -> dict[str, Any]:
    document = session_store.get_document()
    if document is None:
        raise ApiError("session_not_initialized", "No hay una sesión cargada", 404)

    if document.get("status") not in EDITABLE_STATUSES:
        raise ApiError("not_editable", "La sesión no tiene una transcripción editable", 409)

    transcription = document.get("transcription") or {}
    duration = (document.get("audio") or {}).get("duration_seconds") or 0

    try:
        segments = apply_edit(transcription.get("segments") or [], payload.get("segments"), duration)
    except EditError as exc:
        raise ApiError(exc.code, exc.message, 422) from exc

    transcription["segments"] = segments
    document["transcription"] = transcription
    document["status"] = "reviewed"
    session_store.save_document(document)
    return document

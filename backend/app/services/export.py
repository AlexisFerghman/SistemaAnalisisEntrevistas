"""Exportación de la sesión vigente a la ranura única `current_export` (RF-016, D24).

La exportación es una copia consolidada del documento completo (incluidas las marcas por
palabra), no la proyección de lectura. Se guarda en una sola fila que se sobrescribe en cada
exportación y `session_store.delete_export()` la elimina al confirmar una sesión nueva.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import CurrentExport, CurrentSession
from .session_store import EXPORT_ID

EXPORTABLE_STATUSES = {"ready", "reviewed"}


class ExportError(Exception):
    """La sesión no está en condiciones de exportarse."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _current_row(db: Session) -> CurrentSession | None:
    return db.execute(
        select(CurrentSession)
        .order_by(CurrentSession.created_at.desc(), CurrentSession.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _has_confirmed_transcription(document: dict[str, Any]) -> bool:
    if document.get("status") not in EXPORTABLE_STATUSES:
        return False

    transcription = document.get("transcription")
    if not isinstance(transcription, dict):
        return False

    segments = transcription.get("segments")
    return isinstance(segments, list) and bool(segments)


def build_export_document(document: dict[str, Any]) -> dict[str, Any]:
    """Copia consolidada de la sesión: audio/metadatos, transcripción y anotaciones."""
    return {
        "version": document.get("version", 1),
        "session_id": document.get("session_id"),
        "status": document.get("status"),
        "audio": copy.deepcopy(document.get("audio")),
        "transcription": copy.deepcopy(document.get("transcription")),
        "annotations": copy.deepcopy(document.get("annotations") or []),
    }


def _isoformat(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def export_session() -> dict[str, Any]:
    """Persiste la sesión vigente y devuelve `{exported_at, document}`."""
    with SessionLocal() as db:
        row = _current_row(db)
        if row is None:
            raise ExportError("session_not_ready", "No hay una sesión para exportar")

        document = copy.deepcopy(row.payload)
        document["session_id"] = str(row.id)

        if not _has_confirmed_transcription(document):
            raise ExportError(
                "session_not_ready",
                "La sesión no tiene una transcripción confirmada",
            )

        exported_document = build_export_document(document)
        exported_at = datetime.now(timezone.utc)

        export_row = db.get(CurrentExport, EXPORT_ID)
        if export_row is None:
            export_row = CurrentExport(
                id=EXPORT_ID,
                payload=exported_document,
                exported_at=exported_at,
            )
            db.add(export_row)
        else:
            export_row.payload = exported_document
            export_row.exported_at = exported_at

        db.commit()

    return {
        "exported_at": _isoformat(exported_at),
        "document": exported_document,
    }

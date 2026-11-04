"""Sesión única: documento inicial, candado de operación, cancelación y reemplazo atómico.

Todas las operaciones abren una sesión de base de datos corta y la cierran al terminar:
una transcripción puede durar minutos y no debe retener una conexión del pool.
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import CurrentExport, CurrentSession

logger = logging.getLogger(__name__)

CURRENT_SESSION_ID = "current"
EXPORT_ID = "current"

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "/data/audio"))
TMP_PREFIX = ".tmp-"
TMP_OLD_PREFIX = ".tmp-old-"
VALID_STATUSES = {"empty", "validating", "processing", "ready", "reviewed", "error"}


class PersistenceError(Exception):
    """Fallo al persistir el documento o al promover el audio."""


# Un único proceso de uvicorn: el candado y la señal de cancelación viven aquí (research D22).
_operation_lock = threading.Lock()
_cancel_event = threading.Event()


@contextmanager
def _db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def empty_document() -> dict[str, Any]:
    return {
        "version": 1,
        "session_id": "session-current",
        "status": "empty",
        "audio": None,
        "transcription": None,
        "annotations": [],
        "operation": None,
    }


# --------------------------------------------------------------------------- lectura/escritura


def ensure_current_session() -> None:
    """Crea la sesión vacía al arrancar si todavía no existe (RF-012)."""
    with _db() as db:
        if db.get(CurrentSession, CURRENT_SESSION_ID) is None:
            db.add(CurrentSession(id=CURRENT_SESSION_ID, payload=empty_document()))
            db.commit()
            logger.info("Sesión inicial creada con status=empty")


def get_document() -> dict[str, Any] | None:
    with _db() as db:
        row = db.get(CurrentSession, CURRENT_SESSION_ID)
        return None if row is None else row.payload


def save_document(document: dict[str, Any]) -> dict[str, Any]:
    try:
        with _db() as db:
            row = db.get(CurrentSession, CURRENT_SESSION_ID)
            if row is None:
                db.add(CurrentSession(id=CURRENT_SESSION_ID, payload=document))
            else:
                row.payload = document
            db.commit()
    except Exception as exc:  # pragma: no cover - depende de la base de datos
        raise PersistenceError(f"No se pudo guardar la sesión: {exc}") from exc
    return document


# --------------------------------------------------------------------------- operación activa


def acquire_operation(previous_status: str) -> bool:
    """Marca la operación en curso. Devuelve False si ya hay otra activa (research D09)."""
    if not _operation_lock.acquire(blocking=False):
        return False
    _cancel_event.clear()
    document = get_document()
    if document is not None:
        document["status"] = "processing"
        document["operation"] = {
            "previous_status": previous_status,
            "cancel_requested": False,
        }
        save_document(document)
    return True


def release_operation() -> None:
    _cancel_event.clear()
    if _operation_lock.locked():
        try:
            _operation_lock.release()
        except RuntimeError:  # liberado por otro hilo
            logger.debug("El candado de operación ya estaba libre")


def is_busy() -> bool:
    return _operation_lock.locked()


def request_cancel() -> bool:
    """Activa la cancelación cooperativa y la refleja en el documento (research D12)."""
    document = get_document()
    if document is None or document.get("status") != "processing":
        return False
    _cancel_event.set()
    operation = document.get("operation") or {}
    operation["cancel_requested"] = True
    document["operation"] = operation
    save_document(document)
    return True


def cancel_requested() -> bool:
    if _cancel_event.is_set():
        return True
    document = get_document()
    if document is None:
        return False
    return bool((document.get("operation") or {}).get("cancel_requested"))


def clear_operation(status: str) -> None:
    document = get_document()
    if document is None:
        return
    document["status"] = status
    document["operation"] = None
    save_document(document)


# --------------------------------------------------------------------------- arranque


def reconcile_startup() -> None:
    """Revierte un `processing` huérfano y limpia temporales (research D25)."""
    _cancel_event.clear()
    document = get_document()
    if document is not None and document.get("status") == "processing":
        operation = document.get("operation") or {}
        previous = operation.get("previous_status")
        if previous not in VALID_STATUSES or previous == "processing":
            previous = "ready" if document.get("audio") and document.get("transcription") else "empty"
        document["status"] = previous
        document["operation"] = None
        save_document(document)
        logger.warning("Operación huérfana revertida a status=%s", previous)

    _cleanup_temporaries()


def _cleanup_temporaries() -> None:
    if not AUDIO_DIR.is_dir():
        return
    for path in AUDIO_DIR.glob(f"{TMP_PREFIX}*"):
        try:
            path.unlink()
        except OSError:  # pragma: no cover - permisos
            logger.warning("No se pudo borrar el temporal %s", path)


# --------------------------------------------------------------------------- reemplazo atómico


def _audio_files() -> list[Path]:
    if not AUDIO_DIR.is_dir():
        return []
    return sorted(p for p in AUDIO_DIR.glob("current.*") if p.is_file())


def replace_session(
    tmp_audio: Path,
    duration_seconds: float,
    document: dict[str, Any],
) -> dict[str, Any]:
    """Flujo de reemplazo de 7 pasos (RF-013, RF-014, RF-015, research D17).

    El audio anterior solo se borra después de confirmar el documento, y se restaura
    si la persistencia falla.
    """
    suffix = tmp_audio.suffix.lower()
    target = AUDIO_DIR / f"current{suffix}"
    backup: Path | None = None

    if not target.parent.is_dir():
        target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        backup = target.with_name(f"{TMP_OLD_PREFIX}{uuid.uuid4().hex}{suffix}")
        os.replace(target, backup)

    try:
        os.replace(tmp_audio, target)
    except OSError as exc:
        if backup is not None:
            os.replace(backup, target)
        raise PersistenceError(f"No se pudo promover el audio: {exc}") from exc

    document.setdefault("audio", {})
    document["audio"]["storage_ref"] = target.name
    document["audio"]["duration_seconds"] = round(float(duration_seconds), 3)
    document["operation"] = None

    try:
        save_document(document)
    except PersistenceError:
        # Rollback: el audio anterior vuelve a su sitio y el nuevo se descarta.
        target.unlink(missing_ok=True)
        if backup is not None:
            os.replace(backup, target)
        raise

    _post_commit_cleanup(keep=target, backup=backup)
    return document


def _post_commit_cleanup(keep: Path, backup: Path | None) -> None:
    if backup is not None:
        backup.unlink(missing_ok=True)
    for path in _audio_files():
        if path != keep:
            try:
                path.unlink()
            except OSError:  # pragma: no cover - permisos
                logger.warning("No se pudo borrar el audio anterior %s", path)
    delete_export()


def discard_temporary(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:  # pragma: no cover - permisos
        logger.warning("No se pudo borrar el temporal %s", path)


# --------------------------------------------------------------------------- exportación


def delete_export() -> None:
    with _db() as db:
        row = db.get(CurrentExport, EXPORT_ID)
        if row is not None:
            db.delete(row)
            db.commit()

"""Exportación de la sesión vigente (RF-016)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ..services.export import ExportError, export_session
from .errors import ApiError

router = APIRouter(prefix="/api/session", tags=["export"])

STATUS_BY_CODE = {"session_not_ready": 409}


@router.post("/export", status_code=201)
def create_export() -> dict[str, Any]:
    try:
        return export_session()
    except ExportError as exc:
        raise ApiError(
            exc.code,
            exc.message,
            STATUS_BY_CODE.get(exc.code, 400),
        ) from exc

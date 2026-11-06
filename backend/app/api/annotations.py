"""CRUD de anotaciones sobre la transcripción vigente (RF-009, RF-010, RF-011)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Response

from ..services import annotations as service
from ..services.annotations import AnnotationError
from .errors import ApiError

router = APIRouter(prefix="/api/session/annotations", tags=["annotations"])

STATUS_BY_CODE = {
    "empty_annotation": 422,
    "annotation_too_long": 422,
    "unknown_segment": 422,
    "invalid_range": 422,
    "not_editable": 409,
    "annotation_not_found": 404,
    "session_not_initialized": 404,
}


def _raise(exc: AnnotationError) -> None:
    raise ApiError(exc.code, exc.message, STATUS_BY_CODE.get(exc.code, 400)) from exc


@router.post("", status_code=201)
def create_annotation(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return service.create_annotation(
            payload.get("text"),
            payload.get("segment_id"),
            payload.get("start_time"),
            payload.get("end_time"),
        )
    except AnnotationError as exc:
        _raise(exc)


@router.put("/{annotation_id}")
def update_annotation(annotation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return service.update_annotation(
            annotation_id,
            payload.get("text"),
            payload.get("segment_id"),
            payload.get("start_time"),
            payload.get("end_time"),
        )
    except AnnotationError as exc:
        _raise(exc)


@router.delete("/{annotation_id}", status_code=204)
def delete_annotation(annotation_id: str) -> Response:
    try:
        service.delete_annotation(annotation_id)
    except AnnotationError as exc:
        _raise(exc)
    return Response(status_code=204)

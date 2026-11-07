"""Anotaciones sobre segmentos con escritura parcial en SQL.

Cumple `RF-009`…`RF-011` de `002` y la restricción de `003` (RF-019): cada alta, edición o borrado
se resuelve con **una sola sentencia UPDATE** sobre `current_session.payload`; nunca se lee el
documento completo para volver a escribirlo.
"""

from __future__ import annotations

import json
import math
import uuid
from typing import Any

from sqlalchemy import text

from ..db import SessionLocal

MAX_TEXT_LENGTH = 500
EDITABLE_STATUSES = {"ready", "reviewed"}

_CURRENT_ID_SQL = text(
    "SELECT id::text FROM current_session ORDER BY created_at DESC, id DESC LIMIT 1"
)
_STATUS_SQL = text(
    "SELECT payload->>'status' AS status FROM current_session WHERE id = CAST(:session_id AS uuid)"
)
_SEGMENT_SQL = text(
    """
    SELECT (s.segment->>'start_time')::numeric AS start_time,
           (s.segment->>'end_time')::numeric AS end_time
    FROM current_session,
         LATERAL jsonb_array_elements(
           COALESCE(payload->'transcription'->'segments', '[]'::jsonb)
         ) AS s(segment)
    WHERE current_session.id = CAST(:session_id AS uuid)
      AND s.segment->>'id' = :segment_id
    LIMIT 1
    """
)
_INSERT_SQL = text(
    """
    UPDATE current_session
    SET payload = jsonb_set(
          jsonb_set(payload, '{status}', to_jsonb('reviewed'::text), true),
          '{annotations}',
          COALESCE(payload->'annotations', '[]'::jsonb) || CAST(:annotation AS jsonb),
          true
        ),
        updated_at = now()
    WHERE id = CAST(:session_id AS uuid)
    RETURNING payload->'annotations'->-1 AS annotation
    """
)
_UPDATE_SQL = text(
    """
    WITH target AS (
      SELECT (ordinality - 1)::int AS idx
      FROM current_session,
           LATERAL jsonb_array_elements(
             COALESCE(payload->'annotations', '[]'::jsonb)
           ) WITH ORDINALITY AS a(annotation, ordinality)
      WHERE current_session.id = CAST(:session_id AS uuid)
        AND a.annotation->>'id' = :annotation_id
    )
    UPDATE current_session
    SET payload = jsonb_set(
          jsonb_set(payload, '{status}', to_jsonb('reviewed'::text), true),
          ARRAY['annotations', target.idx::text],
          CAST(:annotation AS jsonb),
          false
        ),
        updated_at = now()
    FROM target
    WHERE current_session.id = CAST(:session_id AS uuid)
    RETURNING payload->'annotations'->target.idx AS annotation
    """
)
_DELETE_SQL = text(
    """
    UPDATE current_session
    SET payload = jsonb_set(
          jsonb_set(payload, '{status}', to_jsonb('reviewed'::text), true),
          '{annotations}',
          COALESCE((
            SELECT jsonb_agg(a.annotation)
            FROM jsonb_array_elements(
              COALESCE(payload->'annotations', '[]'::jsonb)
            ) AS a(annotation)
            WHERE a.annotation->>'id' <> :annotation_id
          ), '[]'::jsonb),
          true
        ),
        updated_at = now()
    WHERE id = CAST(:session_id AS uuid)
      AND payload @> jsonb_build_object(
            'annotations', jsonb_build_array(jsonb_build_object('id', CAST(:annotation_id AS text)))
          )
    RETURNING payload->'annotations' AS annotations
    """
)


class AnnotationError(Exception):
    """Error de validación con código estable para el sobre de errores."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_input(
    text_value: Any,
    segment_id: Any,
    start_time: Any,
    end_time: Any,
) -> dict[str, Any]:
    """Validación pura, sin base de datos (probada en unit tests)."""
    if not isinstance(text_value, str) or not text_value.strip():
        raise AnnotationError("empty_annotation", "La anotación no puede estar vacía")

    cleaned = text_value.strip()
    if len(cleaned) > MAX_TEXT_LENGTH:
        raise AnnotationError(
            "annotation_too_long",
            f"La anotación no puede superar los {MAX_TEXT_LENGTH} caracteres",
        )

    if not isinstance(segment_id, str) or not segment_id.strip():
        raise AnnotationError("unknown_segment", "La anotación debe referenciar un segmento")

    try:
        start = float(start_time)
        end = float(end_time)
    except (TypeError, ValueError) as exc:
        raise AnnotationError("invalid_range", "Las marcas de la anotación no son numéricas") from exc

    if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
        raise AnnotationError("invalid_range", "El rango de la anotación no es válido")

    return {
        "text": cleaned,
        "segment_id": segment_id.strip(),
        "start_time": round(start, 3),
        "end_time": round(end, 3),
    }


def _current_session_id() -> str | None:
    with SessionLocal() as db:
        return db.execute(_CURRENT_ID_SQL).scalar_one_or_none()


def _require_editable(session_id: str, fields: dict[str, Any]) -> None:
    with SessionLocal() as db:
        status = db.execute(_STATUS_SQL, {"session_id": session_id}).scalar_one_or_none()

        if status not in EDITABLE_STATUSES:
            raise AnnotationError("not_editable", "La sesión no tiene una transcripción editable")

        segment = db.execute(
            _SEGMENT_SQL,
            {"session_id": session_id, "segment_id": fields["segment_id"]},
        ).first()

        if segment is None:
            raise AnnotationError("unknown_segment", "El segmento no existe")

        if fields["start_time"] < float(segment.start_time) or fields["end_time"] > float(segment.end_time):
            raise AnnotationError(
                "invalid_range",
                "El rango de la anotación queda fuera del segmento",
            )


def create_annotation(
    text_value: Any,
    segment_id: Any,
    start_time: Any,
    end_time: Any,
) -> dict[str, Any]:
    fields = validate_input(text_value, segment_id, start_time, end_time)
    session_id = _current_session_id()
    if session_id is None:
        raise AnnotationError("session_not_initialized", "No hay una sesión cargada")

    _require_editable(session_id, fields)

    annotation = {
        "id": f"annotation-{uuid.uuid4().hex[:12]}",
        **fields,
    }

    with SessionLocal() as db:
        row = db.execute(
            _INSERT_SQL,
            {"session_id": session_id, "annotation": json.dumps(annotation, ensure_ascii=False)},
        ).scalar_one()
        db.commit()
    return row


def update_annotation(
    annotation_id: str,
    text_value: Any,
    segment_id: Any,
    start_time: Any,
    end_time: Any,
) -> dict[str, Any]:
    fields = validate_input(text_value, segment_id, start_time, end_time)
    session_id = _current_session_id()
    if session_id is None:
        raise AnnotationError("session_not_initialized", "No hay una sesión cargada")

    _require_editable(session_id, fields)

    annotation = {"id": annotation_id, **fields}
    with SessionLocal() as db:
        row = db.execute(
            _UPDATE_SQL,
            {
                "session_id": session_id,
                "annotation_id": annotation_id,
                "annotation": json.dumps(annotation, ensure_ascii=False),
            },
        ).scalar_one_or_none()
        db.commit()

    if row is None:
        raise AnnotationError("annotation_not_found", "La anotación no existe")
    return row


def delete_annotation(annotation_id: str) -> None:
    session_id = _current_session_id()
    if session_id is None:
        raise AnnotationError("session_not_initialized", "No hay una sesión cargada")

    with SessionLocal() as db:
        status = db.execute(_STATUS_SQL, {"session_id": session_id}).scalar_one_or_none()
        if status not in EDITABLE_STATUSES:
            raise AnnotationError("not_editable", "La sesión no tiene una transcripción editable")

        row = db.execute(
            _DELETE_SQL,
            {"session_id": session_id, "annotation_id": annotation_id},
        ).first()
        db.commit()

    if row is None:
        raise AnnotationError("annotation_not_found", "La anotación no existe")

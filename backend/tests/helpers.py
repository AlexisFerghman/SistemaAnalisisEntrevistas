"""Utilidades compartidas por las pruebas del backend."""

from __future__ import annotations

import io
import wave
from typing import Any

from sqlalchemy import text

from app.db import engine


def wav_bytes(seconds: float = 1.0, rate: int = 16000, channels: int = 1) -> bytes:
    """Genera un WAV PCM silencioso válido, sin datos reales."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x00\x00" * int(seconds * rate) * channels)
    return buffer.getvalue()


def fetch_payload(table: str = "current_session") -> dict[str, Any] | None:
    """Devuelve el `payload` de la primera fila como valor JSON, o `None`."""
    with engine.connect() as connection:
        row = connection.execute(text(f"SELECT payload FROM {table} LIMIT 1")).first()
    return None if row is None else row[0]


def payload_size(table: str = "current_session") -> int | None:
    """Devuelve `pg_column_size(payload)` de la primera fila, o `None`."""
    with engine.connect() as connection:
        return connection.execute(
            text(f"SELECT pg_column_size(payload) FROM {table} LIMIT 1")
        ).scalar()


def count_rows(table: str = "current_session") -> int:
    """Cuenta las filas de una tabla de ranura única."""
    with engine.connect() as connection:
        return int(connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one())


def column_type(table: str, column: str) -> str | None:
    """Devuelve el `data_type` de `information_schema` para una columna."""
    with engine.connect() as connection:
        return connection.execute(
            text(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table
                  AND column_name = :column
                """
            ),
            {"table": table, "column": column},
        ).scalar()


def session_row_id() -> str | None:
    """Devuelve el `id` de la sesión vigente como texto, o `None`."""
    with engine.connect() as connection:
        value = connection.execute(text("SELECT id FROM current_session LIMIT 1")).scalar()
    return None if value is None else str(value)

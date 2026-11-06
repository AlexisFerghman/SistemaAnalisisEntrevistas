"""Migración `json` → `jsonb` e identidad UUID (RF-017, RF-018, RNF-006, RNF-010)."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import text

from app import migrations
from app.db import engine

from ..fixtures.sessions import legacy_document
from ..helpers import column_type, count_rows, fetch_payload, payload_size, session_row_id


@pytest.fixture()
def legacy_schema():
    """Deja la base en el esquema anterior con una fila `current` conocida."""
    migrations.downgrade(engine)
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM current_session"))
        connection.execute(
            text(
                "INSERT INTO current_session (id, payload) "
                "VALUES ('current', CAST(:payload AS json))"
            ),
            {"payload": json.dumps(legacy_document())},
        )
    try:
        yield
    finally:
        migrations.upgrade(engine)


def test_upgrade_conserva_el_contenido_y_cambia_los_tipos(legacy_schema):
    before = fetch_payload()
    before_size = payload_size()
    assert column_type("current_session", "payload") == "json"

    migrations.upgrade(engine)

    assert column_type("current_session", "payload") == "jsonb"
    assert column_type("current_export", "payload") == "jsonb"
    assert column_type("current_session", "id") == "uuid"
    assert column_type("current_session", "created_at") == "timestamp with time zone"

    after = fetch_payload()
    assert after["version"] == before["version"]
    assert after["status"] == before["status"]
    assert after["audio"] == before["audio"]
    assert after["transcription"] == before["transcription"]
    assert after["annotations"] == before["annotations"]
    assert after["session_id"] != "session-current"
    assert after["session_id"] == session_row_id()

    assert payload_size() <= before_size
    assert count_rows() == 1


def test_upgrade_es_idempotente(legacy_schema):
    migrations.upgrade(engine)
    first_id = session_row_id()
    first_payload = fetch_payload()

    migrations.upgrade(engine)

    assert session_row_id() == first_id
    assert fetch_payload() == first_payload
    assert count_rows() == 1


def test_upgrade_sobre_tabla_vacia_no_crea_filas():
    migrations.downgrade(engine)
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM current_session"))

    migrations.upgrade(engine)

    assert count_rows() == 0
    assert column_type("current_session", "payload") == "jsonb"
    assert column_type("current_session", "id") == "uuid"

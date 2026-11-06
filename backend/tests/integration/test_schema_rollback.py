"""Reverso de la migración de persistencia (RF-017, RF-018, RNF-010)."""

from __future__ import annotations

import pytest

from app import migrations
from app.db import engine
from app.services import session_store

from ..fixtures.sessions import legacy_document
from ..helpers import column_type, count_rows, fetch_payload, session_row_id


@pytest.fixture()
def migrated_schema():
    migrations.upgrade(engine)
    try:
        yield
    finally:
        migrations.upgrade(engine)


def test_downgrade_restaura_el_esquema_anterior_sin_perder_contenido(migrated_schema):
    session_store.save_document(legacy_document())
    before = fetch_payload()
    before_id = session_row_id()
    assert before["session_id"] == before_id

    migrations.downgrade(engine)

    assert column_type("current_session", "payload") == "json"
    assert column_type("current_export", "payload") == "json"
    assert column_type("current_session", "id") in {"text", "character varying"}
    assert column_type("current_session", "created_at") is None
    assert session_row_id() == "current"

    after = fetch_payload()
    assert after["session_id"] == "session-current"
    for key in ("version", "status", "audio", "transcription", "annotations", "operation"):
        assert after[key] == before[key]
    assert count_rows() == 1


def test_downgrade_y_upgrade_son_reversibles(migrated_schema):
    session_store.save_document(legacy_document())
    original = fetch_payload()

    migrations.downgrade(engine)
    migrations.upgrade(engine)

    assert column_type("current_session", "payload") == "jsonb"
    assert column_type("current_session", "id") == "uuid"
    restored = fetch_payload()
    assert restored["audio"] == original["audio"]
    assert restored["transcription"] == original["transcription"]
    assert restored["annotations"] == original["annotations"]
    assert restored["session_id"] == session_row_id()
    assert count_rows() == 1

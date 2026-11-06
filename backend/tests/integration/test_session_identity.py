"""Identidad de la sesión: UUID, `session_id` espejo y fila única (RF-018)."""

from __future__ import annotations

from app.services import session_store

from ..fixtures.sessions import legacy_document
from ..helpers import count_rows, session_row_id, wav_bytes


def test_session_id_es_el_uuid_de_la_fila():
    document = session_store.save_document(legacy_document())

    row_id = session_row_id()
    assert row_id is not None
    assert document["session_id"] == row_id
    assert session_store.get_document()["session_id"] == row_id
    assert count_rows() == 1


def test_guardar_dos_veces_no_crea_una_segunda_fila():
    session_store.save_document(legacy_document())
    first_id = session_row_id()

    session_store.save_document(legacy_document())

    assert session_row_id() == first_id
    assert count_rows() == 1


def test_replace_session_conserva_el_uuid():
    session_store.save_document(legacy_document())
    row_id = session_row_id()

    temporary = session_store.AUDIO_DIR / f"{session_store.TMP_PREFIX}identidad.wav"
    temporary.write_bytes(wav_bytes(1.0))
    document = legacy_document()
    session_store.replace_session(temporary, 720.0, document)

    assert session_row_id() == row_id
    assert session_store.get_document()["session_id"] == row_id
    assert count_rows() == 1

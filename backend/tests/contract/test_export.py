"""Contrato de exportación y ranura única (RF-016, research D24)."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.services import session_store

from ..fixtures.sessions import sample_document
from ..helpers import count_rows, fetch_payload, wav_bytes


@pytest.fixture(autouse=True)
def clean_export() -> None:
    """Aísla la ranura de exportación entre pruebas."""
    session_store.delete_export()
    yield
    session_store.delete_export()


def _export(client):
    return client.post("/api/session/export")


def _exported_at(body):
    return datetime.fromisoformat(body["exported_at"].replace("Z", "+00:00"))


def test_exporta_documento_con_anotaciones(client):
    session_store.save_document(sample_document(segment_count=2, words_per_segment=2))

    response = _export(client)

    assert response.status_code == 201
    body = response.json()
    assert _exported_at(body).tzinfo is not None

    document = body["document"]
    assert document["audio"]["filename"] == "entrevista-sintetica.wav"
    assert document["audio"]["storage_ref"] == "current.wav"
    assert document["transcription"]["segments"][0]["text"] != ""
    # La exportación es el documento completo: conserva las marcas por palabra.
    assert document["transcription"]["segments"][0]["words"]
    assert document["annotations"] == sample_document(segment_count=2)["annotations"]

    assert fetch_payload("current_export") == document
    assert count_rows("current_export") == 1


def test_exporta_documento_sin_anotaciones(client):
    document = sample_document(segment_count=2, words_per_segment=2)
    document["annotations"] = []
    session_store.save_document(document)

    response = _export(client)

    assert response.status_code == 201
    body = response.json()
    assert body["document"]["annotations"] == []
    assert body["document"]["transcription"]["segments"]


def test_exporta_la_transcripcion_corregida(client):
    document = sample_document(segment_count=2, words_per_segment=2)
    original = document["transcription"]["segments"][0]["text"]
    corrected = "Texto corregido por el profesional."
    document["transcription"]["segments"][0]["text"] = corrected
    document["status"] = "reviewed"
    session_store.save_document(document)

    response = _export(client)

    assert response.status_code == 201
    exported = response.json()["document"]
    assert exported["status"] == "reviewed"
    assert exported["transcription"]["segments"][0]["text"] == corrected
    assert exported["transcription"]["segments"][0]["text"] != original


def test_sobrescribe_la_ranura_unica(client):
    document = sample_document(segment_count=2, words_per_segment=2)
    session_store.save_document(document)
    assert _export(client).status_code == 201

    document["annotations"] = []
    session_store.save_document(document)
    second = _export(client)

    assert second.status_code == 201
    assert second.json()["document"]["annotations"] == []
    assert count_rows("current_export") == 1


def test_sesion_sin_transcripcion_devuelve_409(client):
    response = _export(client)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "session_not_ready"
    assert fetch_payload("current_export") is None


def test_confirmar_una_sesion_nueva_elimina_la_exportacion(client, monkeypatch):
    session_store.save_document(sample_document(segment_count=2, words_per_segment=2))
    assert _export(client).status_code == 201
    assert fetch_payload("current_export") is not None

    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    response = client.post(
        "/api/session/audio",
        files={"file": ("entrevista.wav", wav_bytes(8.0), "audio/wav")},
    )

    assert response.status_code == 200
    assert fetch_payload("current_export") is None

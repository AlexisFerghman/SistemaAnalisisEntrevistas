"""Contrato de lectura resumida y endpoint de palabras (RF-020, RF-021, RF-022)."""

from __future__ import annotations

from app.services import session_store

from ..fixtures.sessions import sample_document


def _prepare_session():
    document = sample_document(segment_count=6, words_per_segment=40)
    return session_store.save_document(document)


def test_resumen_por_defecto_es_menor_que_el_25_por_ciento(client):
    _prepare_session()

    summary = client.get("/api/session")
    full = client.get("/api/session?view=full")

    assert summary.status_code == 200
    assert full.status_code == 200
    assert len(summary.content) < len(full.content) * 0.25

    for segment in summary.json()["transcription"]["segments"]:
        assert "words" not in segment
        assert segment["words_count"] == 40


def test_view_full_devuelve_el_documento_completo(client):
    document = _prepare_session()

    response = client.get("/api/session?view=full")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == document["session_id"]
    assert body["transcription"]["segments"][0]["words"] == (
        document["transcription"]["segments"][0]["words"]
    )
    assert "words_count" not in body["transcription"]["segments"][0]


def test_view_invalido_devuelve_422(client):
    _prepare_session()

    response = client.get("/api/session?view=compact")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_view"


def test_endpoint_de_palabras_devuelve_solo_el_segmento(client):
    document = _prepare_session()
    expected = document["transcription"]["segments"][2]["words"]

    response = client.get("/api/session/segments/segment-003/words")

    assert response.status_code == 200
    assert response.json() == {"segment_id": "segment-003", "words": expected}


def test_endpoint_de_palabras_devuelve_404_si_no_existe(client):
    _prepare_session()

    response = client.get("/api/session/segments/segment-999/words")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "segment_not_found"


def test_endpoint_de_palabras_sin_sesion_devuelve_404(client):
    session_store.delete_document()

    response = client.get("/api/session/segments/segment-001/words")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "session_not_initialized"


def test_resumen_conserva_anotaciones(client):
    document = _prepare_session()

    response = client.get("/api/session")

    assert response.json()["annotations"] == document["annotations"]

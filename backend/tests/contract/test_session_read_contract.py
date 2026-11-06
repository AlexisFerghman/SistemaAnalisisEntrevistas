"""Contrato de la lectura de sesión y del audio (RF-020, RF-021, RF-022)."""

from __future__ import annotations

from app.services import session_store

from ..fixtures.sessions import sample_document
from ..helpers import wav_bytes


def test_contrato_del_resumen(client):
    session_store.save_document(sample_document(segment_count=2, words_per_segment=2))

    body = client.get("/api/session").json()

    assert set(body) == {
        "version",
        "session_id",
        "status",
        "audio",
        "transcription",
        "annotations",
        "operation",
    }
    assert set(body["transcription"]) == {"language", "provider", "retry_count", "segments"}
    assert set(body["transcription"]["segments"][0]) == {
        "id",
        "start_time",
        "end_time",
        "text",
        "words_count",
    }


def test_contrato_de_la_vista_completa(client):
    session_store.save_document(sample_document(segment_count=2, words_per_segment=2))

    body = client.get("/api/session?view=full").json()

    assert "words" in body["transcription"]["segments"][0]
    assert "words_count" not in body["transcription"]["segments"][0]


def test_audio_conserva_su_contrato(client, monkeypatch):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    response = client.post(
        "/api/session/audio",
        files={"file": ("entrevista.wav", wav_bytes(8.0), "audio/wav")},
    )
    assert response.status_code == 200

    audio = client.get("/api/session/audio")

    assert audio.status_code == 200
    assert audio.headers["accept-ranges"] == "bytes"
    assert audio.headers["content-type"].startswith("audio/")

from app.services import session_store

from ..helpers import wav_bytes


def _upload(client, monkeypatch, seconds=8.0):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    response = client.post(
        "/api/session/audio",
        files={"file": ("entrevista.wav", wav_bytes(seconds), "audio/wav")},
    )
    assert response.status_code == 200
    return response.json()["session"]


def test_edicion_valida_marca_la_sesion_como_revisada(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segments = session["transcription"]["segments"]

    segments[0]["text"] = "Hola, esta es una entrevista sintetica corregida."
    response = client.put("/api/session/transcription", json={"segments": segments})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "reviewed"
    assert body["transcription"]["segments"][0]["text"].startswith("Hola, esta es")

    words = body["transcription"]["segments"][0]["words"]
    assert [word["text"] for word in words][:3] == ["Hola,", "esta", "es"]
    assert words[-1]["end_time"] <= segments[0]["end_time"]


def test_edicion_sin_cambios_conserva_las_marcas_originales(client, monkeypatch):
    session = _upload(client, monkeypatch)
    original_words = session["transcription"]["segments"][0]["words"]

    response = client.put(
        "/api/session/transcription",
        json={"segments": session["transcription"]["segments"]},
    )

    assert response.status_code == 200
    assert response.json()["transcription"]["segments"][0]["words"] == original_words


def test_edicion_desde_resumen_conserva_las_palabras(client, monkeypatch):
    """El editor envía solo id/texto/marcas; las palabras deben sobrevivir (RF-008, RF-020)."""
    session = _upload(client, monkeypatch)
    original_words = session["transcription"]["segments"][0]["words"]
    summary_segments = [
        {key: value for key, value in segment.items() if key != "words"}
        for segment in session["transcription"]["segments"]
    ]

    response = client.put("/api/session/transcription", json={"segments": summary_segments})

    assert response.status_code == 200
    assert response.json()["transcription"]["segments"][0]["words"] == original_words



def test_edicion_invalida_no_altera_el_documento(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segments = session["transcription"]["segments"]
    original_start = segments[0]["start_time"]
    segments[0]["start_time"] = -5.0

    response = client.put("/api/session/transcription", json={"segments": segments})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_timestamps"

    current = session_store.get_document()
    assert current["transcription"]["segments"][0]["start_time"] == original_start


def test_sesion_vacia_no_es_editable(client):
    response = client.put("/api/session/transcription", json={"segments": []})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_editable"


def test_audio_se_entrega_completo(client, monkeypatch):
    _upload(client, monkeypatch)

    response = client.get("/api/session/audio")

    assert response.status_code == 200
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-type"].startswith("audio/")


def test_audio_soporta_peticiones_parciales(client, monkeypatch):
    _upload(client, monkeypatch)

    response = client.get("/api/session/audio", headers={"Range": "bytes=0-99"})

    assert response.status_code == 206
    assert response.headers["content-range"].startswith("bytes 0-99/")
    assert len(response.content) == 100


def test_audio_rechaza_rango_invalido(client, monkeypatch):
    _upload(client, monkeypatch)

    response = client.get("/api/session/audio", headers={"Range": "bytes=99999999-"})

    assert response.status_code == 416


def test_audio_sin_sesion_devuelve_404(client):
    response = client.get("/api/session/audio")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_audio"

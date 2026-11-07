import hashlib

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


def _first_segment(session):
    return session["transcription"]["segments"][0]


def _audio_hash():
    path = session_store.AUDIO_DIR / "current.wav"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_crear_anotacion_devuelve_201_y_marca_revisada(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segment = _first_segment(session)

    response = client.post(
        "/api/session/annotations",
        json={
            "text": "Observación de prueba",
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "Observación de prueba"
    assert body["segment_id"] == segment["id"]
    assert body["id"].startswith("annotation-")

    summary = client.get("/api/session").json()
    assert summary["status"] == "reviewed"
    assert len(summary["annotations"]) == 1


def test_501_caracteres_no_llega_a_la_base_de_datos(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segment = _first_segment(session)

    response = client.post(
        "/api/session/annotations",
        json={
            "text": "a" * 501,
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "annotation_too_long"
    assert client.get("/api/session").json()["annotations"] == []


def test_500_caracteres_se_guarda(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segment = _first_segment(session)

    response = client.post(
        "/api/session/annotations",
        json={
            "text": "a" * 500,
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    )

    assert response.status_code == 201
    assert len(response.json()["text"]) == 500


def test_segmento_inexistente_devuelve_422(client, monkeypatch):
    _upload(client, monkeypatch)

    response = client.post(
        "/api/session/annotations",
        json={"text": "x", "segment_id": "segment-999", "start_time": 0, "end_time": 1},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unknown_segment"


def test_rango_fuera_del_segmento_devuelve_422(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segment = _first_segment(session)

    response = client.post(
        "/api/session/annotations",
        json={
            "text": "x",
            "segment_id": segment["id"],
            "start_time": 0,
            "end_time": segment["end_time"] + 10,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_range"


def test_editar_anotacion_existente(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segment = _first_segment(session)
    created = client.post(
        "/api/session/annotations",
        json={
            "text": "Original",
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    ).json()

    response = client.put(
        f"/api/session/annotations/{created['id']}",
        json={
            "text": "Corregida",
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Corregida"
    assert client.get("/api/session").json()["annotations"][0]["text"] == "Corregida"


def test_editar_anotacion_inexistente_devuelve_404(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segment = _first_segment(session)

    response = client.put(
        "/api/session/annotations/annotation-inexistente",
        json={
            "text": "x",
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "annotation_not_found"


def test_borrar_anotacion_la_quita_del_documento(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segment = _first_segment(session)
    created = client.post(
        "/api/session/annotations",
        json={
            "text": "Temporal",
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    ).json()

    assert client.delete(f"/api/session/annotations/{created['id']}").status_code == 204

    summary = client.get("/api/session").json()
    assert summary["annotations"] == []

    again = client.delete(f"/api/session/annotations/{created['id']}")
    assert again.status_code == 404


def test_sesion_vacia_no_admite_anotaciones(client):
    response = client.post(
        "/api/session/annotations",
        json={"text": "x", "segment_id": "segment-001", "start_time": 0, "end_time": 1},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_editable"


def test_las_anotaciones_no_modifican_el_audio(client, monkeypatch):
    session = _upload(client, monkeypatch)
    segment = _first_segment(session)
    before = _audio_hash()

    created = client.post(
        "/api/session/annotations",
        json={
            "text": "Sin tocar el audio",
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    ).json()
    client.put(
        f"/api/session/annotations/{created['id']}",
        json={
            "text": "Editada",
            "segment_id": segment["id"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
        },
    )
    client.delete(f"/api/session/annotations/{created['id']}")

    assert _audio_hash() == before

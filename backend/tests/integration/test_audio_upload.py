from app.services import audio_validation, session_store

from ..helpers import wav_bytes


def _post(client, name="entrevista.wav", content=None, mime="audio/wav"):
    return client.post(
        "/api/session/audio",
        files={"file": (name, content if content is not None else wav_bytes(1.0), mime)},
    )


def _ready_document():
    return {
        "version": 1,
        "session_id": "",
        "status": "ready",
        "audio": {
            "filename": "anterior.wav",
            "mime_type": "audio/wav",
            "size_bytes": 100,
            "duration_seconds": 1.0,
            "storage_ref": "current.wav",
        },
        "transcription": {
            "language": "es",
            "provider": "fake",
            "retry_count": 0,
            "segments": [],
        },
        "annotations": [{"id": "annotation-001", "text": "previa"}],
        "operation": None,
    }


def test_carga_valida_devuelve_sesion_lista(client, monkeypatch):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")

    # 8 s para que quepan los tres segmentos que devuelve el motor falso (hasta 7 s)
    response = _post(client, content=wav_bytes(8.0))

    assert response.status_code == 200
    body = response.json()
    assert body["cancelled"] is False
    assert body["session"]["status"] == "ready"
    assert body["session"]["audio"]["storage_ref"] == "current.wav"
    assert len(body["session"]["transcription"]["segments"]) == 3
    assert (session_store.AUDIO_DIR / "current.wav").exists()


def test_transcripcion_conserva_palabras_y_marcas_validas(client, monkeypatch):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")

    response = _post(client, content=wav_bytes(8.0))

    assert response.status_code == 200
    transcription = response.json()["session"]["transcription"]
    assert transcription["language"] == "es"
    assert transcription["provider"] == "fake"
    assert transcription["segments"]

    for segment in transcription["segments"]:
        assert segment["start_time"] < segment["end_time"]
        assert segment["words"], "el motor debe entregar marcas por palabra"
        for word in segment["words"]:
            assert segment["start_time"] <= word["start_time"] < word["end_time"]
            assert word["end_time"] <= segment["end_time"]


def test_formato_no_admitido_devuelve_415(client):
    response = _post(client, name="notas.txt", content=b"texto", mime="text/plain")

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_format"


def test_sin_archivo_devuelve_400_missing_file(client):
    response = client.post("/api/session/audio")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_file"


def test_audio_ausente_marca_la_sesion_en_error(client):
    document = _ready_document()
    document["audio"]["storage_ref"] = "archivo-inexistente.wav"
    session_store.save_document(document)

    response = client.get("/api/session/audio")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "audio_missing"

    current = session_store.get_document()
    assert current["status"] == "error"
    assert current["audio"]["filename"] == "anterior.wav"
    assert current["transcription"] == document["transcription"]
    assert current["annotations"] == [{"id": "annotation-001", "text": "previa"}]


def test_content_length_excedido_responde_413_sin_cargar_el_archivo(client):
    response = client.post(
        "/api/session/audio",
        content=b"",
        headers={"Content-Length": str(audio_validation.MAX_BYTES + 1)},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_audio_ilegible_devuelve_422_y_conserva_la_sesion(client, monkeypatch):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    session_store.save_document(_ready_document())

    response = _post(client, content=b"esto no es audio")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_audio"

    current = session_store.get_document()
    assert current["status"] == "ready"
    assert current["audio"]["filename"] == "anterior.wav"
    assert current["annotations"] == [{"id": "annotation-001", "text": "previa"}]


def test_tamano_excedido_devuelve_413(client, monkeypatch):
    monkeypatch.setattr(audio_validation, "MAX_BYTES", 100)

    response = _post(client, content=b"\x00" * 500)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_carga_simultanea_devuelve_409(client, monkeypatch):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    asserted = session_store.acquire_operation("empty")
    assert asserted is True

    try:
        response = _post(client)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "busy"
    finally:
        session_store.release_operation()
        session_store.clear_operation("empty")


def test_fallo_del_motor_devuelve_503_y_conserva_la_sesion(client, monkeypatch):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    monkeypatch.setenv("FAKE_TRANSCRIBER_ERROR", "unavailable")
    session_store.save_document(_ready_document())

    response = _post(client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "transcription_unavailable"

    current = session_store.get_document()
    assert current["status"] == "ready"
    assert current["audio"]["filename"] == "anterior.wav"


def test_no_deja_temporales_tras_un_fallo(client, monkeypatch):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    monkeypatch.setenv("FAKE_TRANSCRIBER_ERROR", "rejected")

    _post(client)

    temporales = list(session_store.AUDIO_DIR.glob(f"{session_store.TMP_PREFIX}*"))
    assert temporales == []

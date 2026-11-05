import asyncio
import time

import httpx

from app.main import app

from ..helpers import wav_bytes


def test_health_responde_durante_la_transcripcion(monkeypatch):
    """El endpoint de carga es síncrono y corre en el threadpool: /health no se bloquea (D11)."""
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    monkeypatch.setenv("FAKE_TRANSCRIBER_DELAY", "0.4")

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                files = {"file": ("entrevista.wav", wav_bytes(1.0), "audio/wav")}
                upload = asyncio.create_task(client.post("/api/session/audio", files=files))
                await asyncio.sleep(0.3)

                started = time.perf_counter()
                health = await client.get("/health")
                elapsed = time.perf_counter() - started

                result = await upload
                return health, elapsed, result

    health, elapsed, upload = asyncio.run(scenario())

    assert health.status_code == 200
    assert elapsed < 1.0, f"/health tardó {elapsed:.2f}s durante la transcripción"
    assert upload.status_code == 200
    assert upload.json()["session"]["status"] == "ready"


def test_cancelacion_conserva_la_sesion_anterior(monkeypatch):
    monkeypatch.setenv("TRANSCRIPTION_ENGINE", "fake")
    monkeypatch.setenv("FAKE_TRANSCRIBER_DELAY", "0.4")

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                files = {"file": ("entrevista.wav", wav_bytes(1.0), "audio/wav")}
                upload = asyncio.create_task(client.post("/api/session/audio", files=files))
                await asyncio.sleep(0.3)

                cancel = await client.post("/api/session/cancel")
                result = await upload
                return cancel, result

    cancel, upload = asyncio.run(scenario())

    assert cancel.status_code == 202
    assert upload.status_code == 409
    assert upload.json()["error"]["code"] == "cancelled"
    assert upload.json()["session"]["status"] == "empty"

"""La sesión solo se escribe por los endpoints funcionales (D27, RNF-001, RNF-002)."""

from __future__ import annotations

from app.services import session_store

from ..fixtures.sessions import sample_document


def test_put_y_delete_de_sesion_ya_no_existen(client):
    session_store.save_document(sample_document(segment_count=2, words_per_segment=2))
    before = client.get("/api/session?view=full").json()

    assert client.put("/api/session", json={"status": "empty"}).status_code == 405
    assert client.delete("/api/session").status_code == 405

    after = client.get("/api/session?view=full").json()
    assert after == before


def test_cors_solo_permite_el_origen_configurado(client):
    allowed = client.options(
        "/api/session",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    rejected = client.options(
        "/api/session",
        headers={
            "Origin": "https://sitio-no-autorizado.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in rejected.headers

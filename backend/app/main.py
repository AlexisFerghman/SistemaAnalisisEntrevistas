import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .api.errors import ApiError, install_error_handlers
from .db import get_db, init_db
from .models import CurrentSession
from .services.session_store import (
    CURRENT_SESSION_ID,
    ensure_current_session,
    get_document,
    reconcile_startup,
)

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_current_session()
    reconcile_startup()
    yield


app = FastAPI(title="Analisis de entrevistas API", version="0.1.0", lifespan=lifespan)
install_error_handlers(app)

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
origin_regex = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1|172\.20\.\d+\.\d+)(:\d+)?$",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_origin_regex=origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/session")
def get_current_session() -> dict:
    document = get_document()
    if document is None:
        raise ApiError("session_not_initialized", "No hay una sesión cargada", 404)
    return document


@app.put("/api/session")
def save_current_session(payload: dict, db: Session = Depends(get_db)) -> dict:
    session = db.get(CurrentSession, CURRENT_SESSION_ID)
    if session is None:
        session = CurrentSession(id=CURRENT_SESSION_ID, payload=payload)
        db.add(session)
    else:
        session.payload = payload
    db.commit()
    return payload


@app.delete("/api/session", status_code=204)
def delete_current_session(db: Session = Depends(get_db)) -> Response:
    session = db.get(CurrentSession, CURRENT_SESSION_ID)
    if session is not None:
        db.delete(session)
        db.commit()
    return Response(status_code=204)

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.errors import ApiError, UploadSizeLimitMiddleware, install_error_handlers
from .api.annotations import router as annotations_router
from .api.export import router as export_router
from .api.session import router as session_router
from .api.transcription import router as transcription_router
from .db import init_db
from .services.session_projection import summarize_document
from .services.session_store import (
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
app.add_middleware(UploadSizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_origin_regex=origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_router)
app.include_router(transcription_router)
app.include_router(annotations_router)
app.include_router(export_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/session")
def get_current_session(view: str = "summary") -> dict:
    if view not in {"summary", "full"}:
        raise ApiError(
            "invalid_view",
            "La vista debe ser 'summary' o 'full'",
            422,
        )

    document = get_document()
    if document is None:
        raise ApiError("session_not_initialized", "No hay una sesión cargada", 404)
    return summarize_document(document) if view == "summary" else document

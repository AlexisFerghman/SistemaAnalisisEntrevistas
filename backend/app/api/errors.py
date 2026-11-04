"""Sobre uniforme de errores: {"error": {"code", "message", "details"}}."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..services.audio_validation import AudioValidationError
from ..services.session_store import PersistenceError
from ..transcription.adapter import (
    TranscriptionCancelled,
    TranscriptionInvalidResponse,
    TranscriptionRejected,
    TranscriptionTimeout,
    TranscriptionUnavailable,
)

logger = logging.getLogger(__name__)

VALIDATION_STATUS = {
    "missing_file": 400,
    "unsupported_format": 415,
    "payload_too_large": 413,
    "invalid_audio": 422,
}


class ApiError(Exception):
    """Error de la capa HTTP con código estable para el cliente."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(AudioValidationError)
    async def _audio_error(_: Request, exc: AudioValidationError) -> JSONResponse:
        status_code = VALIDATION_STATUS.get(exc.code, 422)
        return error_response(status_code, exc.code, exc.message)

    @app.exception_handler(PersistenceError)
    async def _persistence_error(_: Request, exc: PersistenceError) -> JSONResponse:
        logger.exception("Fallo de persistencia")
        return error_response(500, "persistence_error", str(exc))

    @app.exception_handler(TranscriptionRejected)
    async def _transcription_rejected(_: Request, exc: TranscriptionRejected) -> JSONResponse:
        return error_response(422, "invalid_audio", str(exc))

    @app.exception_handler(TranscriptionCancelled)
    async def _transcription_cancelled(_: Request, exc: TranscriptionCancelled) -> JSONResponse:
        return error_response(409, "cancelled", str(exc))

    @app.exception_handler(TranscriptionTimeout)
    @app.exception_handler(TranscriptionUnavailable)
    @app.exception_handler(TranscriptionInvalidResponse)
    async def _transcription_unavailable(_: Request, exc: Exception) -> JSONResponse:
        logger.warning("Transcripción no disponible: %s", exc)
        return error_response(503, "transcription_unavailable", str(exc))

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            422,
            "validation_error",
            "La petición no es válida",
            {"errors": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(exc.status_code, f"http_{exc.status_code}", str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado")
        return error_response(500, "internal_error", "Error interno del servidor")

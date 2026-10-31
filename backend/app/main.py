import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import get_db, init_db
from .models import CurrentSession

CURRENT_SESSION_ID = "current"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Analisis de entrevistas API", version="0.1.0", lifespan=lifespan)

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/session")
def get_current_session(db: Session = Depends(get_db)) -> dict:
    session = db.get(CurrentSession, CURRENT_SESSION_ID)
    if session is None:
        raise HTTPException(status_code=404, detail="No hay una sesión cargada")
    return session.payload


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

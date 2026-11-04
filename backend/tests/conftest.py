import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Cliente HTTP que ejecuta el lifespan de la app (crea la sesión inicial)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def database_url() -> str:
    """URL de la base de datos del contenedor (ver docker-compose.yml)."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://entrevistas:entrevistas_dev@db:5432/entrevistas",
    )

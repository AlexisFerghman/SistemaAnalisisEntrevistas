# Sistema de análisis de entrevistas

Prototipo experimental para transcribir y anotar entrevistas clínicas
sintéticas. Esta versión no está destinada a entornos clínicos reales.

## Stack inicial

- Frontend: React + JavaScript + Vite.
- API: FastAPI + Python 3.12.
- Persistencia: PostgreSQL 16.
- Orquestación: Docker Compose.

## Arranque

Requisitos: Docker Engine y Docker Compose.

```bash
docker compose up --build
```

Servicios:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API health: http://localhost:8000/health
- PostgreSQL desde el host: `localhost:5433` (dentro de Docker: `db:5432`)

La API inicial expone únicamente el estado del servicio y la sesión actual.
La sesión es única y no hay autenticación en este prototipo.

## Verificaciones locales sin Docker

```bash
python3 -m py_compile backend/app/*.py
python3 -m json.tool frontend/package.json
```

El MVP utiliza servicios locales aislados en Docker, admite audio `.mp3` y
`.wav` de hasta 120 MB y persiste la exportación como JSON en PostgreSQL. El
despliegue en un servidor cloud privado queda reservado para entregas finales.

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

La API inicial expone únicamente el estado del servicio y la sesión actual.
La sesión es única y no hay autenticación en este prototipo.

## Verificaciones locales sin Docker

```bash
python3 -m py_compile backend/app/*.py
python3 -m json.tool frontend/package.json
```

El proveedor cloud de transcripción, los límites del audio y el formato de
exportación se definirán antes de implementar las tareas funcionales.

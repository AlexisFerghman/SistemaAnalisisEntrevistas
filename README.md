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

### Lectura de la sesión

- `GET /api/session` devuelve una vista **resumen**: audio, metadatos de transcripción y segmentos
  sin el array `words`, con un contador `words_count` por segmento.
- `GET /api/session?view=full` devuelve el documento completo, incluidas las marcas por palabra.
- `GET /api/session/segments/{segment_id}/words` devuelve solo las palabras de un segmento.
- `GET /api/session/audio` no cambia y sigue soportando peticiones `Range`.
- La exportación sigue persistiendo el documento completo con `words` para cumplir `RF-016`.

### Persistencia

`current_session.payload` y `current_export.payload` son `jsonb`. La sesión se identifica con un
UUID y conserva `created_at`; el sistema sigue manteniendo una sola fila. La migración se aplica de
forma idempotente al arrancar y su reverso está documentado en
`specs/003-persistencia-jsonb-proyeccion/data-model.md`.

## Pruebas

```bash
docker compose exec api pytest
docker compose exec frontend npm test
```

## Verificaciones locales sin Docker

```bash
python3 -m py_compile backend/app/*.py
python3 -m json.tool frontend/package.json
```

El MVP utiliza servicios locales aislados en Docker, admite audio `.mp3` y
`.wav` de hasta 120 MB y persiste la exportación como JSON en PostgreSQL. El
despliegue en un servidor cloud privado queda reservado para entregas finales.

# Implementation Plan: MVP de análisis inicial

**Branch**: `002-mvp-analisis-inicial` | **Date**: 2026-11-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-mvp-analisis-inicial/spec.md`

**Note**: Este plan reemplaza como artefacto activo a `spec/01-analisis-inicial-general/plan.md`, que se
conserva como referencia histórica. Las decisiones técnicas de ese documento se consolidan en
[research.md](./research.md).

## Summary

Prototipo de un único flujo para un único usuario: cargar un audio sintético, transcribirlo en local
con `faster-whisper`, revisar y editar la transcripción con marcas de tiempo, añadir anotaciones
vinculadas a segmentos y exportar la sesión como documento JSON en PostgreSQL.

Enfoque técnico: aplicación modular única (FastAPI + React + PostgreSQL sobre Docker Compose), sin
microservicios, sin autenticación y con una sola sesión. La transcripción se ejecuta dentro del
contenedor `api`, que no tiene egreso a red, y se resuelve en la misma petición HTTP mediante el
threadpool de FastAPI (**B-lite**): el documento de sesión se marca `processing` antes de empezar,
un candado en proceso rechaza cargas simultáneas y la cancelación es cooperativa entre segmentos.
No hay cola, ni worker externo, ni polling como mecanismo principal.

## Technical Context

**Language/Version**: Python 3.12 (backend); JavaScript ESM con React + Vite (frontend).

**Primary Dependencies**: FastAPI 0.115.6, uvicorn 0.34.0, SQLAlchemy 2.0.36, psycopg 3.2.3,
`faster-whisper` (versión a fijar al implementar), React, Vite, `@vitejs/plugin-react`.

**Storage**: PostgreSQL 16-alpine (tabla `current_session`, columna `payload JSON`); audio en el
volumen de host `./data/audio` montado en `/data/audio`; exportación persistida como documento JSON.

**Testing**: `pytest` con `httpx`/`TestClient` para unit, integración y contrato del backend;
`Vitest` + `@testing-library/react` + `jsdom` para el frontend. La integración de reemplazo de
sesión usa PostgreSQL real del compose, no un doble.

**Target Platform**: Linux con Docker Engine y Docker Compose; navegador moderno de escritorio.

**Project Type**: aplicación web (backend + frontend).

**Performance Goals**: transcribir 10 minutos de audio en ≤ 15 minutos con modelo `base` e
`int8` en CPU de desarrollo; `GET /health` responde en < 100 ms incluso durante una transcripción;
la interfaz nunca queda bloqueada esperando al servidor.

**Constraints**: audio `.mp3` o `.wav` de hasta 120 MB, sin tope de duración; una sola sesión; una
sola carga concurrente; sin autenticación ni roles; solo datos sintéticos; el contenedor `api`
opera sin egreso a internet.

**Scale/Scope**: un usuario conceptual, una sesión, una carga a la vez, una pantalla principal con
estados de operación, 10 endpoints HTTP y 1 adaptador de transcripción.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate verificable | Resultado |
|---|---|---|
| I. Supervisión humana (NO NEGOCIABLE) | Ningún endpoint ni pantalla emite diagnóstico, evaluación psiquiátrica o recomendación clínica; toda salida se etiqueta como asistencia experimental y la edición profesional es obligatoria antes de exportar | PASS |
| II. Datos sintéticos y privacidad | Banner permanente + confirmación explícita por archivo; sin rutas para datos reales; sin autenticación; audio procesado localmente en `api`, que está solo en redes `internal: true` (`frontend_api`, `api_db`) y por tanto sin egreso | PASS (ver nota 1) |
| III. Sesión única y eliminación | El reemplazo confirma audio y documento antes de descartar la sesión anterior; cualquier fallo o cancelación previa a la confirmación conserva la sesión anterior sin mezclar datos | PASS |
| IV. Calidad y trazabilidad | Se persisten marcas de inicio y fin por palabra y por oración; la anotación referencia un segmento existente; el audio original nunca se sobrescribe con una versión editada | PASS |
| V. Simplicidad del MVP | El alcance se limita a carga, transcripción, edición, anotación y exportación; sin colas, workers, XAI, chatbot ni multiusuario | PASS (ver nota 2) |

**Nota 1**: `RF-004` exige "servicio local de transcripción aislado". Se interpreta como *local,
contenedorizado y sin salida a red*, no como contenedor separado, por decisión explícita del usuario.
El aislamiento queda garantizado por la topología de redes del compose y por la precarga del modelo
en la imagen (ver `research.md`, D20).

**Nota 2**: el diseño B-lite añade un estado de operación, un candado en proceso y un flag de
cancelación. No añade servicios, dependencias de infraestructura ni piezas de despliegue, por lo que
no compromete el principio V.

**Re-evaluación tras Fase 1**: sin cambios; el diseño de datos y contratos no introduce violaciones.

## Project Structure

### Documentation (this feature)

```text
specs/002-mvp-analisis-inicial/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones y alternativas
├── data-model.md        # Fase 1: entidades, reglas y estados
├── quickstart.md        # Fase 1: escenarios de validación
├── contracts/
│   ├── api.md           # Contrato HTTP público
│   └── transcription-adapter.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                 # App FastAPI, CORS, lifespan
│   ├── db.py                   # Engine, sesión, init_db
│   ├── models.py               # Modelo SQLAlchemy de la sesión única
│   ├── api/
│   │   ├── session.py          # GET/PUT de sesión, carga, cancelación
│   │   ├── transcription.py    # Edición de transcripción
│   │   ├── annotations.py      # CRUD de anotaciones
│   │   └── export.py           # Exportación del documento
│   ├── services/
│   │   ├── audio_validation.py # Extensión, MIME, estructura, tamaño
│   │   ├── session_store.py    # Reemplazo atómico y conservación previa
│   │   ├── annotations.py      # Reglas de anotación (500 caracteres, segmento)
│   │   └── export.py           # Construcción del documento exportable
│   └── transcription/
│       ├── adapter.py          # Contrato interno, reintento, errores
│       ├── faster_whisper_engine.py  # Motor real (modelo precargado)
│       └── fake_engine.py      # Motor determinista para pruebas
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── src/
│   ├── components/             # Reproductor, editor, lista de anotaciones, banner
│   ├── pages/                  # Pantalla única de revisión
│   └── services/               # Cliente de la API y estados de operación
└── tests/
```

**Structure Decision**: se mantiene la estructura de aplicación web ya existente (`backend/` +
`frontend/`) y se expande solo lo necesario. El adaptador de transcripción vive en
`backend/app/transcription/` porque se ejecuta dentro del contenedor `api`; no se crea un servicio
nuevo ni se modifica la topología de `docker-compose.yml`.

## Complexity Tracking

| Desviación | Por qué es necesaria | Alternativa simple rechazada |
|---|---|---|
| `RF-001`/`RF-002` y el caso límite mencionan validar duración; el plan fija **solo** el tope de 120 MB | La duración depende de códec, bitrate, canales y frecuencia; un tope fijo rechazaría audios válidos. La duración se lee y se usa para validar coherencia interna (segmentos dentro del audio), sin tope numérico | Fijar un máximo de minutos: rechaza grabaciones legítimas y obliga a re-transcodificar; requiere alinear la spec en `/speckit.clarify` o con un PATCH posterior |
| Transcripción dentro del contenedor `api` | Decisión del usuario; evita un cuarto servicio y su contrato de red | Contenedor `transcriber` separado: cumple literalmente "aislado", pero añade servicio, imagen y healthcheck propios |
| Modelo `base` precargado en la imagen (~150 MB extra) | El contenedor `api` no tiene egreso a red, así que no puede descargar pesos en tiempo de ejecución | Descarga en el primer arranque: imposible sin egreso; abrir egreso temporal: rompe el aislamiento |
| Candado de concurrencia en memoria del proceso | Basta para un único worker de uvicorn con una sesión y un usuario | Candado en base de datos con bloqueo de fila: más robusto ante múltiples workers, innecesario para el despliegue actual |
| Un solo worker de uvicorn | El estado de operación y el candado viven en el proceso; el modelo ocupa memoria una única vez | Múltiples workers: duplicaría el modelo en RAM y exigiría estado distribuido |

## Evolución prevista

La hoja de ruta completa para salir del prototipo de sesión única vive en
[`specs/003-persistencia-jsonb-proyeccion/plan.md`](../003-persistencia-jsonb-proyeccion/plan.md),
sección "Evolución prevista". En resumen, el orden acordado es:

1. Enmienda mayor de la constitución (`1.0.0` → `2.0.0`) para sustituir el principio de sesión única
   por sesiones múltiples con aislamiento por profesional y paciente.
2. Normalización relacional de médicos, pacientes, sesiones, segmentos, palabras, anotaciones y
   exportaciones, con integridad referencial.
3. Autenticación y roles (`medico`, `administrador`).
4. Row Level Security por médico y paciente, con roles de base de datos separados.
5. Auditoría de solo inserción y política de retención.
6. Migración por fases desde `current_session`/`current_export`, conservando el documento JSONB como
   respaldo durante la validación.

No se implementa nada de esto en `002` ni en `003`; solo se documenta para justificar por qué se
mantiene PostgreSQL y por qué no se normaliza ahora.

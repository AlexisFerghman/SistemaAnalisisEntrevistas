# Implementation Plan: Persistencia JSONB y proyección de lectura

**Branch**: `003-persistencia-jsonb-proyeccion` | **Date**: 2026-11-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-persistencia-jsonb-proyeccion/spec.md`

**Note**: Esta feature refactoriza la persistencia de `002-mvp-analisis-inicial` sin reutilizar ni
renumerar sus tareas. Se implementa **antes** de `T032`–`T038` (Fase 5, anotaciones) para que esa fase
nazca con `jsonb` y con la restricción de escritura parcial.

## Summary

Se mantiene PostgreSQL y el modelo de documento único, pero se corrigen cuatro cosas de alcance
acotado:

1. `current_session.payload` y `current_export.payload` pasan de `json` a `jsonb` con migración
   idempotente y reverso documentado.
2. `current_session.id` deja de ser el literal `current` y pasa a ser un UUID con `created_at`; el
   sistema sigue manteniendo una sola fila y `session_id` pasa a ser el espejo del UUID.
3. Las anotaciones de la Fase 5 se escribirán con `jsonb_set`/`||`; esta entrega solo fija la
   restricción de diseño.
4. `GET /api/session` devuelve una vista resumen sin `words` y con `words_count`; `?view=full`
   conserva el documento completo (la única diferencia es `session_id`, ya UUID por R2) y se añade
   `GET /api/session/segments/{id}/words`.

El audio y la exportación no cambian. No se añaden servicios, colas, caché, dependencias ni tablas
normalizadas.

## Technical Context

**Language/Version**: Python 3.12 (backend); JavaScript ESM con React + Vite (frontend).

**Primary Dependencies**: las mismas de `002`: FastAPI 0.115.6, uvicorn 0.34.0, SQLAlchemy 2.0.36,
psycopg 3.2.3, React, Vite. No se añade ninguna dependencia nueva.

**Storage**: PostgreSQL 16-alpine. `current_session` con `id uuid`, `created_at`, `payload jsonb`,
`updated_at`; `current_export` con `payload jsonb`. Audio en `/data/audio` como `current.<ext>`.

**Testing**: `pytest` + `httpx`/`TestClient` para backend; `Vitest` + `@testing-library/react` para
frontend. Se añaden pruebas de migración, proyección, contrato de lectura y componente de lista.

**Target Platform**: Linux con Docker Engine y Docker Compose; navegador moderno de escritorio.

**Project Type**: aplicación web (backend + frontend).

**Performance Goals**: la respuesta resumida de `GET /api/session` debe ocupar menos del 25 % de la
respuesta completa sobre la misma sesión; el endpoint de palabras debe devolver solo un segmento.

**Constraints**: sin cambio de motor; sin normalización; sin autenticación; una sola sesión; sin
Alembic; migración idempotente, transaccional y reversible; 49 pruebas de backend y 5 de frontend
deben seguir pasando.

**Scale/Scope**: un usuario conceptual, una sesión, una carga a la vez. Se modifican dos tablas, un
endpoint existente, un endpoint nuevo y la lista de transcripción del frontend.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate verificable | Resultado |
|---|---|---|
| I. Supervisión humana (NO NEGOCIABLE) | La feature no añade diagnósticos, evaluaciones ni recomendaciones clínicas; solo cambia almacenamiento y lectura | PASS |
| II. Datos sintéticos y privacidad | No se añaden servicios ni egreso de red; no se introducen datos identificables ni autenticación; el audio sigue local | PASS |
| III. Sesión única y eliminación | La migración conserva la fila; el reemplazo reutiliza la misma fila y no crea historial; las pruebas verifican `count(*) <= 1` | PASS (ver nota 1) |
| IV. Calidad y trazabilidad | Las marcas por palabra siguen persistidas, se devuelven en `?view=full`, en la exportación y en el endpoint de palabras; el audio no se toca | PASS |
| V. Simplicidad del MVP | Sin motor nuevo, sin normalización, sin Alembic, sin servicios ni dependencias; el alcance se limita a R1-R5 | PASS (ver nota 2) |

**Nota 1**: el esquema deja de imponer el singleton mediante una PK literal, pero el principio III se
mantiene como invariante de aplicación: `ensure_current_session()` crea una sola fila y
`replace_session()` actualiza esa misma fila. Se añade una prueba de integración que verifica
`count(*) <= 1` tras crear, reemplazar y migrar. No se conserva historial ni recuperación.

**Nota 2**: la vista resumen y el endpoint de palabras añaden una transformación de lectura y una
ruta HTTP, no infraestructura. La restricción de `jsonb_set` no se implementa en esta entrega; solo
se documenta para la Fase 5.

**Re-evaluación tras Fase 1**: sin cambios; el modelo de datos y el contrato no introducen
violaciones.

## Project Structure

### Documentation (this feature)

```text
specs/003-persistencia-jsonb-proyeccion/
├── spec.md              # Esta especificación
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones D27-D38
├── data-model.md        # Fase 1: esquema, migración y proyección
├── contracts/
│   ├── api.md           # Contrato de lectura y endpoint de palabras
│   └── annotations.md   # Restricción de escritura parcial (T024)
└── tasks.md             # Fase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                       # GET /api/session con ?view
│   ├── db.py                         # init_db + llamada a la migración
│   ├── migrations.py                 # NUEVO: upgrade/downgrade idempotentes
│   ├── models.py                     # JSONB, UUID y created_at
│   ├── api/
│   │   ├── session.py                # GET .../segments/{id}/words
│   │   └── transcription.py          # sin cambios de contrato
│   └── services/
│       ├── session_store.py          # identidad UUID y espejo de session_id
│       └── session_projection.py     # NUEVO: resumen y extracción de palabras
└── tests/
    ├── unit/
    │   └── test_session_projection.py
    ├── integration/
    │   ├── test_schema_migration.py
    │   └── test_session_view.py
    └── contract/
        └── test_session_read_contract.py

frontend/
├── src/
│   ├── services/api.js               # getSegmentWords
│   └── components/
│       └── TranscriptList.jsx        # words_count con respaldo a words.length
└── tests/
    └── TranscriptList.test.jsx
```

**Structure Decision**: se mantiene la aplicación web existente. La lógica de migración se aísla en
`backend/app/migrations.py` para que `db.py` siga siendo el punto de arranque; la proyección se
aísla en un servicio para poder probarla sin HTTP. No se crean paquetes, servicios ni contenedores
nuevos.

## Design Decisions

Las decisiones completas están en [research.md](./research.md). Resumen operativo:

| Tema | Decisión | Referencia |
|---|---|---|
| Migración | SQL idempotente y transaccional en `init_db()`, sin Alembic | D27 |
| Tipo | `jsonb` en ambas columnas, comparación por valor JSON | D28 |
| Identidad | `id uuid DEFAULT gen_random_uuid()` + `created_at` | D29 |
| `session_id` | Espejo del UUID de la fila, escrito por la persistencia | D30 |
| `session-current` | Se retira del documento y del export; `current.<ext>` sigue como ranura de audio | D31 |
| Lectura | `summary` por defecto, `full` explícito | D32 |
| Palabras | `GET /api/session/segments/{segment_id}/words` | D33 |
| Proyección | En Python, sobre una copia; no se modifica el documento persistido | D34 |
| Frontend | `words_count ?? words.length`; el editor no envía palabras | D35 |
| Exportación | Documento completo, nunca resumen | D36 |
| Anotaciones | `jsonb_set`/`||` en una sola sentencia (Fase 5) | D37 |
| Motor | PostgreSQL, sin normalizar | D38 |

## Implementation Order

1. **Setup**: línea base de pruebas y utilidades de medición.
2. **US1 — migración (P1)**: `migrations.py`, `db.py`, `models.py`, `session_store.py`, pruebas de
   migración y de identidad. Es bloqueante para el resto.
3. **US2 — proyección (P1)**: `session_projection.py`, `GET /api/session`, endpoint de palabras,
   frontend y pruebas de bytes/forma.
4. **US3 — anotaciones (P2)**: contrato y revisión de diseño para la Fase 5; sin código de negocio.
5. **US4 — evolución (P3)**: sección "Evolución prevista" y enlace desde `002`.
6. **Polish**: suite completa, medición final, README y verificación de que no se tocaron tareas de
   `002`.

**Regla de secuencia**: `003` debe estar terminada y verificada antes de empezar `T032`–`T038`. La
Fase 5 escribirá anotaciones con `jsonb_set` sobre el esquema ya migrado; hacerlo antes obligaría a
migrar código y datos dos veces.

## Evolución prevista

> Documentación únicamente. Nada de esta sección se implementa en `003`.

La decisión de mantener PostgreSQL y no normalizar ahora se sostiene porque el escenario futuro es
relacional. La hoja de ruta es la siguiente, en este orden:

### 1. Enmienda mayor de la constitución (`1.0.0` → `2.0.0`)

- Sustituir el principio III de sesión única por un principio de sesiones múltiples con aislamiento
  por profesional y paciente.
- Añadir un principio de control de acceso y auditoría.
- Mantener intactos los principios I (supervisión humana) y II (datos sintéticos en el prototipo).
- La enmienda debe aprobarse antes de cualquier cambio de esquema que permita más de una sesión.

### 2. Normalización del modelo

- `medicos` (identidad profesional, rol, estado).
- `pacientes` (identidad seudonimizada; sin datos clínicos reales en el prototipo).
- `sesiones` (médico, paciente, estado, `created_at`, `updated_at`; sustituye a `current_session`).
- `segmentos` y `palabras` (hoy dentro del documento; pasan a tablas con FK a `sesiones`).
- `anotaciones` (FK a `segmentos` y a `sesiones`, texto de hasta 500 caracteres, autor y marcas).
- `exportaciones` (una fila por exportación, con FK a `sesiones`).
- El audio sigue en almacenamiento de archivos con una referencia desde `sesiones`.

**Migración**: backfill de la fila única actual a las tablas nuevas en una transacción; conservar el
documento JSONB como respaldo de solo lectura durante una ventana de validación.

### 3. Autenticación y autorización

- Cuentas de profesional, inicio de sesión y sesión de usuario.
- Roles mínimos: `medico` y `administrador`.
- Un médico solo accede a sus pacientes y sesiones; un administrador no lee contenido clínico por
  defecto.
- Sustituir la ausencia de autenticación de `RNF-002` por un requisito explícito de la v2.

### 4. Row Level Security (RLS)

- Activar RLS en `sesiones`, `segmentos`, `palabras`, `anotaciones` y `exportaciones`.
- Políticas por `medico_id` y, cuando aplique, por `paciente_id`.
- Roles de base de datos separados para la aplicación, migraciones y soporte.
- Pruebas de fuga entre médicos y entre pacientes.

### 5. Auditoría

- Tabla `audit_log` de solo inserción: quién, qué entidad, acción, fecha y correlación.
- Registrar lectura de sesión, exportación, anotación y cambios de estado.
- Política de retención y borrado alineada con la enmienda de la constitución.
- La auditoría no puede contener el texto clínico completo; solo referencias e identificadores.

### 6. Despliegue y compatibilidad

- Migración por fases con la aplicación anterior en solo lectura.
- Ventana de validación con el documento JSONB como respaldo.
- Retirar `current_session`/`current_export` solo después de validar el backfill.
- Sin cambio de motor: PostgreSQL sigue siendo la base transaccional y de RLS.

## Complexity Tracking

| Desviación | Por qué es necesaria | Alternativa simple rechazada |
|---|---|---|
| Migrar la PK de `text` a `uuid` en vez de conservar `id = 'current'` | R2 exige un identificador real y `created_at`; el literal impide evolucionar a varias sesiones | Mantener `current`: no hay identidad ni orden temporal y la v2 exigiría otra migración |
| SQL idempotente en `init_db()` en vez de Alembic | Solo hay dos tablas y un despliegue; Alembic añade dependencia, historial y un paso operativo nuevo | Alembic: ceremonia desproporcionada para un cambio de tipo y una PK |
| Proyección en Python en vez de `jsonb` en SQL | Es una transformación de forma fácil de probar y no altera el documento | `payload #- ...` en SQL: reconstruir el array y añadir `words_count` es más frágil |
| Mantener respuestas completas en `POST /audio` y `PUT /transcription` | Evita romper contratos y pruebas ya completadas de `002`; el objetivo medible es `GET /api/session` | Cambiar todas las mutaciones a resumen: amplía el alcance y el riesgo de regresión |
| No imponer el singleton con una restricción única | R2 pide que el esquema deje de asumir una sola sesión; el principio III se garantiza en la aplicación y en pruebas | Índice único sobre un booleano: vuelve a codificar el singleton y habría que retirarlo en v2 |

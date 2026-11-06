# Tasks: Persistencia JSONB y proyección de lectura

**Input**: Documentos de diseño en `/specs/003-persistencia-jsonb-proyeccion/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/api.md](./contracts/api.md)

**Tests**: incluidas porque el plan mantiene `pytest` (backend) y `Vitest` (frontend) como stack
obligatorio. En cada historia las pruebas se escriben **antes** de la implementación.

**Organización**: las tareas se agrupan por historia de usuario. `[P]` indica paralelizable (archivos
distintos, sin dependencias pendientes). Cada tarea incluye la ruta de archivo exacta y las
referencias `RF-*`/`RNF-*` que cubre.

**Numeración**: los IDs `T001`–`T034` son locales de `003`. **No** se renumeran ni se modifican las
tareas `T001`–`T054` de `002`.

**⚠️ Orden obligatorio**: completar `003` (en especial US1 y US2) **antes** de `T032`–`T038` de la
Fase 5 de `002`. La Fase 5 debe escribir anotaciones con `jsonb_set` sobre el esquema ya migrado.

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: puede ejecutarse en paralelo con otras tareas `[P]` de la misma fase
- **[Story]**: `[US1]`…`[US4]`, según las historias de `spec.md`
- Toda tarea incluye al menos una ruta de archivo

## Convenciones de rutas

- Backend: `backend/app/…` y `backend/tests/…`
- Frontend: `frontend/src/…` y `frontend/tests/…`
- Documentación: `specs/003-persistencia-jsonb-proyeccion/…` y `docs/…`
- Pruebas de backend dentro del contenedor: `docker compose exec api pytest`
- Pruebas de frontend: `npm test` en `frontend/`

---

## Phase 1: Setup (línea base y utilidades)

**Propósito**: medir el estado actual y preparar helpers de comparación. Nada de lógica de negocio.

- [X] T001 [P] Ejecutar la suite actual y registrar la línea base (49 backend + 5 frontend) en
  `docs/validacion-003.md` (RNF-009)
- [X] T002 [P] Añadir a `backend/tests/helpers.py` utilidades para leer `payload` como valor JSON,
  medir `pg_column_size(payload)` y comprobar `count(*) <= 1` en `current_session`
  (RNF-006, RNF-007, RF-018)
- [X] T003 [P] Crear `backend/tests/fixtures/sessions.py` con un documento determinista de ~12 min
  que incluya segmentos y `words`, para las pruebas de tamaño y migración (RF-020, RNF-007)

**Checkpoint**: la línea base está registrada y existen helpers reutilizables.

---

## Phase 2: User Story 1 — Migrar la persistencia sin perder la sesión (Priority: P1) 🎯 MVP

**Goal**: `payload` es `jsonb`, `current_session.id` es un UUID con `created_at`, la fila existente
sobrevive y la migración es idempotente y reversible.

**Independent Test**: partir de una base con una fila `id = 'current'` y un `payload` `json` con
audio, transcripción, palabras y anotaciones; ejecutar la migración; comprobar tipo `jsonb`, UUID,
`created_at`, contenido íntegro, `pg_column_size` no creciente, segunda ejecución sin cambios y
reverso funcional.

**⚠️ BLOQUEANTE**: ninguna otra historia puede empezar hasta completar esta fase.

### Tests de US1 (escribir primero, deben fallar)

- [X] T004 [P] [US1] Pruebas de integración en `backend/tests/integration/test_schema_migration.py`:
  tipo `jsonb` en ambas tablas, `id uuid`, `created_at`, contenido JSON intacto, `pg_column_size` no
  aumenta, `count(*) <= 1` y segunda ejecución idempotente
  (RF-017, RF-018, RNF-006, RNF-010, SC-009, SC-010)
- [X] T005 [P] [US1] Prueba de reverso en `backend/tests/integration/test_schema_rollback.py`: volver
  a `json`, `id = 'current'` y `session_id = 'session-current'` sin pérdida de contenido
  (RF-017, RF-018, RNF-010)
- [X] T006 [P] [US1] Prueba de identidad en `backend/tests/integration/test_session_identity.py`:
  `session_id` del documento coincide con `current_session.id`, el reemplazo conserva el UUID y no
  crea una segunda fila (RF-018, RF-012, RF-013)

### Implementación de US1

- [X] T007 [US1] Crear `backend/app/migrations.py` con `upgrade(engine)` y `downgrade(engine)`:
  DDL transaccional, guardas con `information_schema`/`pg_constraint`, `jsonb_set` para actualizar
  `session_id` y reverso documentado (RF-017, RF-018, RNF-010)
- [X] T008 [US1] Modificar `backend/app/db.py` para invocar `migrations.upgrade(engine)` después de
  `Base.metadata.create_all(bind=engine)` (RF-017)
- [X] T009 [US1] Actualizar `backend/app/models.py`: `JSONB` en `CurrentSession.payload` y
  `CurrentExport.payload`, `Uuid` en `CurrentSession.id` con `server_default=gen_random_uuid()` y
  columna `created_at` (RF-017, RF-018)
- [X] T010 [US1] Refactorizar `backend/app/services/session_store.py`: eliminar la dependencia de
  `CURRENT_SESSION_ID = "current"`, seleccionar la única fila, generar/retener el UUID, escribir
  `session_id` como espejo antes de persistir y reutilizar la fila en `replace_session()`
  (RF-018, RF-012, RF-013, RF-014)
- [X] T011 [US1] Actualizar `backend/app/main.py` para resolver la sesión vigente mediante el store
  (sin `db.get(CurrentSession, CURRENT_SESSION_ID)`) en `GET`, `PUT` y `DELETE /api/session`
  (RF-018)
- [X] T012 [US1] Ajustar `backend/app/api/session.py` para que el documento de carga no fije
  `"session_id": "session-current"`; el store asigna el UUID al persistir (RF-018)
- [X] T013 [US1] Actualizar `backend/tests/conftest.py` y las aserciones de
  `backend/tests/integration/test_audio_upload.py` que esperaban `session-current`
  (RF-018, RNF-009)

**Checkpoint**: la base migra y revierte sin pérdida; la sesión tiene UUID y `created_at`; la suite
de backend vuelve a verde.

---

## Phase 3: User Story 2 — Consultar la sesión sin descargar todas las palabras (Priority: P1)

**Goal**: `GET /api/session` devuelve resumen por defecto, `?view=full` conserva el documento
completo y existe un endpoint de palabras por segmento.

**Independent Test**: sobre la sesión de prueba, medir bytes de resumen y completo; el resumen debe
ser < 25 %, sin clave `words` y con `words_count`; `?view=full` debe devolver las palabras; el
endpoint de un segmento debe devolver solo sus palabras y `404` si no existe.

### Tests de US2 (escribir primero, deben fallar)

- [X] T014 [P] [US2] Pruebas unitarias en `backend/tests/unit/test_session_projection.py`: el resumen
  elimina `words` y añade `words_count`, conserva `annotations`, no muta el documento original y
  maneja transcripción vacía (RF-020, RF-022, SC-012)
- [X] T015 [P] [US2] Pruebas de integración en `backend/tests/integration/test_session_view.py`:
  resumen < 25 % de bytes que `?view=full`, `?view=full` equivalente al documento completo,
  `422 invalid_view`, endpoint de palabras `200`/`404 segment_not_found` y audio sin cambios
  (RF-020, RF-021, RF-022, RNF-007, SC-011, SC-013)
- [X] T016 [P] [US2] Prueba de componente en `frontend/tests/TranscriptList.test.jsx`: muestra
  `words_count` y usa `words.length` como respaldo cuando la respuesta es completa
  (RF-020, RNF-009)

### Implementación de US2

- [X] T017 [US2] Crear `backend/app/services/session_projection.py` con `summarize_document()` y
  `segment_words()`: copia profunda de la transcripción, sustitución de `words` por `words_count` y
  extracción de palabras de un segmento (RF-020, RF-021)
- [X] T018 [US2] Modificar `GET /api/session` en `backend/app/main.py` para aceptar `view=summary|full`
  (por defecto `summary`) y responder `422 invalid_view` con el sobre uniforme (RF-020)
- [X] T019 [US2] Añadir `GET /api/session/segments/{segment_id}/words` en
  `backend/app/api/session.py` con `200 {segment_id, words}`, `404 segment_not_found` y
  `404 session_not_initialized` (RF-021)
- [X] T020 [US2] Añadir `getSegmentWords(segmentId)` a `frontend/src/services/api.js` (RF-021)
- [X] T021 [US2] Actualizar `frontend/src/components/TranscriptList.jsx` para mostrar
  `segment.words_count ?? segment.words?.length ?? 0` (RF-020)
- [X] T022 [US2] Verificar y cubrir en `backend/tests/integration/test_transcription_edit.py` que
  `PUT /api/session/transcription` conserva o redistribuye `words` aunque el editor envíe solo
  `id`, `start_time`, `end_time` y `text` (RF-008, RF-020, RF-022)
- [X] T023 [US2] Añadir prueba de contrato en `backend/tests/contract/test_session_read_contract.py`
  para la forma del resumen, la forma de `?view=full` y la respuesta de `GET /api/session/audio`
  (RF-020, RF-021, RF-022)

**Checkpoint**: la vista principal no descarga `words`; el editor puede pedirlas por segmento; el
audio y el documento completo no cambian.

---

## Phase 4: User Story 3 — Guardar anotaciones sin reescribir el documento (Priority: P2)

**Goal**: dejar fijada, verificable y sin código de negocio, la restricción de persistencia parcial
para la Fase 5 de `002`.

**Independent Test**: revisar el contrato y comprobar que alta, edición y borrado tienen una única
sentencia `UPDATE` con `jsonb_set`/`||`, sin `get_document()` + `save_document()`.

### Tests y documentación de US3

- [X] T024 [P] [US3] Crear `specs/003-persistencia-jsonb-proyeccion/contracts/annotations.md` con las
  tres formas SQL de referencia (alta, edición y borrado), la validación dirigida del segmento y la
  actualización de `status` en la misma sentencia (RF-019, SC-015)
- [X] T025 [P] [US3] Añadir a `docs/validacion-003.md` la lista de comprobación de la Fase 5:
  una sentencia por operación, `jsonb_set`/`||`, sin lectura completa y sin tablas nuevas
  (RF-019, RNF-008)
- [X] T026 [US3] Verificar que no se añadió código de anotaciones y que la suite existente sigue en
  verde; registrar el resultado en `docs/validacion-003.md` (RF-019, RNF-009)

**Checkpoint**: la Fase 5 tiene un contrato de persistencia parcial claro y no se adelantó
implementación.

---

## Phase 5: User Story 4 — Documentar la evolución multi-médico y multi-paciente (Priority: P3)

**Goal**: dejar escrita la hoja de ruta para v2 sin implementarla.

**Independent Test**: leer "Evolución prevista" y comprobar que cubre normalización, RLS, enmienda
mayor de la constitución, autenticación y auditoría, en orden.

- [X] T027 [P] [US4] Revisar y completar la sección "Evolución prevista" de
  `specs/003-persistencia-jsonb-proyeccion/plan.md`: normalización, RLS, enmienda `1.0.0 → 2.0.0`,
  autenticación, auditoría y compatibilidad de despliegue (RF-023, SC-015)
- [X] T028 [P] [US4] Añadir en `specs/002-mvp-analisis-inicial/plan.md` una nota "Evolución prevista"
  que remita a `003` y resuma el orden de la hoja de ruta (RF-023)
- [X] T029 [US4] Verificar que la hoja de ruta no introduce requisitos implementables en `003` ni
  cambia el alcance de `002`; registrar la revisión en `docs/validacion-003.md` (RF-023, RNF-008)

**Checkpoint**: la deuda de evolución está documentada y separada de la implementación.

---

## Phase 6: Polish y verificación transversal

**Propósito**: cerrar la feature con evidencia medible y sin tocar tareas de `002`.

- [X] T030 [P] Ejecutar `docker compose exec api pytest` y confirmar 49 pruebas de backend (más las
  nuevas) en verde; registrar el resultado en `docs/validacion-003.md` (RNF-009)
- [X] T031 [P] Ejecutar `npm test` en `frontend/` y confirmar las 5 pruebas existentes (más la nueva)
  en verde; registrar el resultado en `docs/validacion-003.md` (RNF-009)
- [X] T032 Medir sobre la sesión de prueba: `pg_column_size(payload)`, tipo reportado por
  `information_schema` y porcentaje de bytes resumen/full; registrar los tres valores en
  `docs/validacion-003.md` (RNF-006, RNF-007, SC-009, SC-011)
- [X] T033 [P] Actualizar `README.md` con `GET /api/session?view=full`, el endpoint de palabras y la
  nota de que la exportación sigue incluyendo `words` (RF-020, RF-021, RF-022)
- [X] T034 Verificar que no se modificó `docker-compose.yml`, no se añadieron dependencias, no se
  renumeró `specs/002-mvp-analisis-inicial/tasks.md` y no se adelantó `T032`–`T038`
  (RNF-008, RF-019)

---

## Dependencies & Execution Order

### Dependencias por fase

- **Setup (Fase 1)**: sin dependencias; puede empezar de inmediato.
- **US1 — migración (Fase 2)**: depende de Setup y **bloquea** US2, US3 y US4. Sin `jsonb` y UUID no
  tiene sentido la proyección ni la restricción de anotaciones.
- **US2 — proyección (Fase 3)**: depende de US1. Puede empezar en cuanto la migración y la identidad
  estén verdes.
- **US3 — anotaciones (Fase 4)**: depende de US1 (necesita `jsonb`); puede ejecutarse en paralelo con
  US2 si hay dos personas, porque solo toca documentación.
- **US4 — evolución (Fase 5)**: depende de US1; puede ejecutarse en paralelo con US2/US3 porque solo
  toca documentación.
- **Polish (Fase 6)**: depende de que US1 y US2 estén completas.

### Dependencias internas de cada historia

- Pruebas antes de implementación (deben fallar primero).
- `migrations.py` antes de `db.py`, `models.py` y `session_store.py`.
- `session_projection.py` antes de `GET /api/session` y del endpoint de palabras.
- Endpoint de palabras antes de `getSegmentWords` en el frontend.
- Ninguna tarea de `003` modifica las tareas de `002`.

### Orden recomendado para el menor tiempo total

1. Setup (T001–T003).
2. US1 completa (T004–T013) → **checkpoint bloqueante**.
3. US2 completa (T014–T023) → **reducción de tráfico verificada**.
4. US3 y US4 en paralelo (T024–T029).
5. Polish (T030–T034).
6. **Solo entonces**: `T032`–`T038` de `002` (Fase 5, anotaciones).

## Parallel Example: User Story 1

```bash
# Pruebas de migración en paralelo (archivos distintos):
Task: "Pruebas de tipo, contenido e idempotencia en backend/tests/integration/test_schema_migration.py"
Task: "Prueba de reverso en backend/tests/integration/test_schema_rollback.py"
Task: "Prueba de identidad y fila única en backend/tests/integration/test_session_identity.py"
```

## Parallel Example: User Story 2

```bash
Task: "Pruebas de proyección en backend/tests/unit/test_session_projection.py"
Task: "Pruebas de vista y endpoint en backend/tests/integration/test_session_view.py"
Task: "Prueba de TranscriptList en frontend/tests/TranscriptList.test.jsx"
```

## Implementación incremental

### Incremento 1 — Esquema seguro

1. Completar Setup (T001–T003).
2. Completar US1 (T004–T013).
3. **Parar y validar**: migración, reverso, idempotencia y fila única.

### Incremento 2 — Tráfico reducido

1. Completar US2 (T014–T023).
2. **Parar y validar**: resumen < 25 %, sin `words`, con `words_count`, `full` intacto y endpoint de
   palabras operativo.
3. Recién entonces habilitar la Fase 5 de `002`.

### Incremento 3 — Deuda documentada

1. Completar US3 y US4 (T024–T029).
2. Completar Polish (T030–T034).

## Notas

- `[P]` = archivos distintos y sin dependencia de una tarea incompleta.
- Las pruebas se escriben antes de la implementación y deben fallar primero.
- Cada tarea cabe en un solo archivo de código, prueba o documento.
- Las tareas de backend se ejecutan con `docker compose exec api pytest`.
- No se añaden dependencias fuera de las ya existentes en `requirements.txt`,
  `requirements-dev.txt` y `package.json`.
- No se toca `docker-compose.yml`.
- La vista resumen no se usa para exportar ni para `GET /api/session/audio`.
- La Fase 5 de `002` no empieza hasta que US1 y US2 estén completas y verificadas.

## Matriz de cobertura RF → tarea

| Requisito | Tareas |
|---|---|
| RF-017 | T004, T005, T007, T008, T009 |
| RF-018 | T006, T007, T009, T010, T011, T012, T013 |
| RF-019 | T024, T025, T026, T034 |
| RF-020 | T014, T015, T017, T018, T021, T023 |
| RF-021 | T015, T017, T019, T020, T023 |
| RF-022 | T014, T015, T022, T023, T033 |
| RF-023 | T027, T028, T029 |
| RNF-006 | T002, T004, T032 |
| RNF-007 | T002, T015, T032 |
| RNF-008 | T025, T029, T034 |
| RNF-009 | T001, T013, T016, T026, T030, T031 |
| RNF-010 | T004, T005, T007 |

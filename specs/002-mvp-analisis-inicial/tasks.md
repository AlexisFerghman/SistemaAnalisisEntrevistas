# Tasks: MVP de análisis inicial

**Input**: Documentos de diseño en `/specs/002-mvp-analisis-inicial/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: incluidas porque `plan.md` fija `pytest` (backend) y `Vitest` (frontend) como stack
obligatorio. En cada historia las pruebas se escriben **antes** de la implementación.

**Organización**: las tareas se agrupan por historia de usuario para que cada una sea implementable y
verificable por separado. `[P]` indica paralelizable (archivos distintos, sin dependencias pendientes).
Cada tarea incluye la ruta de archivo exacta y las referencias `RF-*`/`RNF-*` que cubre.

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: puede ejecutarse en paralelo con otras tareas `[P]` de la misma fase
- **[Story]**: `[US1]`…`[US4]`, según las historias de `spec.md`; las fases Setup, Foundational y
  Polish no llevan etiqueta
- Toda tarea incluye al menos una ruta de archivo

## Convenciones de rutas

- Backend: `backend/app/…` y `backend/tests/…`
- Frontend: `frontend/src/…` y `frontend/tests/…`
- Pruebas de backend dentro del contenedor: `docker compose exec api pytest`

---

## Phase 1: Setup (infraestructura compartida)

**Propósito**: dependencias, configuración de pruebas y volumen de audio. Nada de lógica de negocio.

- [X] T001 Añadir `faster-whisper` (versión fijada) y `av` a `backend/requirements.txt`, conservando
  `fastapi==0.115.6`, `uvicorn[standard]==0.34.0`, `SQLAlchemy==2.0.36`, `psycopg[binary]==3.2.3`
- [X] T002 [P] Crear `backend/requirements-dev.txt` con `pytest`, `httpx` y `pytest-cov` para poder
  ejecutar `docker compose exec api pytest`
- [X] T003 Modificar `backend/Dockerfile` para instalar `requirements-dev.txt` y precargar el modelo
  `base` con `RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"`
  fijando `HF_HOME=/opt/models`, de modo que el contenedor no necesite red en ejecución (research D20)
- [X] T004 [P] Crear `backend/tests/conftest.py` con un fixture `client` (`TestClient`) y un fixture de
  base de datos que use `DATABASE_URL`; crear `backend/tests/{unit,integration,contract}/__init__.py`
- [X] T005 [P] Configurar Vitest en `frontend/package.json` (devDependencies `vitest`, `jsdom`,
  `@testing-library/react`) y en `frontend/vite.config.js` (`test: { environment: 'jsdom', setupFiles }`);
  crear `frontend/tests/setup.js`
- [X] T006 [P] Crear `data/audio/.gitkeep` y añadir `data/audio/*` a `.gitignore` para no versionar
  audios ni temporales

**Checkpoint**: `docker compose build` funciona y `docker compose exec api pytest` arranca sin errores.

---

## Phase 2: Foundational (prerrequisitos bloqueantes)

**Propósito**: piezas que **todas** las historias necesitan. Ninguna historia puede empezar antes.

**⚠️ CRÍTICO**: esta fase bloquea por completo las fases 3 a 6.

- [ ] T007 Añadir el modelo `CurrentExport` (tabla `current_export`, fila fija `current`, columnas
  `payload JSON` y `exported_at`) en `backend/app/models.py` (RF-016, D24)
- [ ] T008 Implementar en `backend/app/services/session_store.py` la creación del documento inicial
  `{"version": 1, "session_id": "session-current", "status": "empty", "audio": null, "transcription": null, "annotations": [], "operation": null}`
  cuando no exista, invocado desde `backend/app/main.py` en `lifespan` (RF-012)
- [ ] T009 Implementar en `backend/app/main.py` la reconciliación de arranque: si
  `status == "processing"`, restaurar `operation.previous_status` y limpiar `operation` (research D25)
- [ ] T010 Crear `backend/app/api/errors.py` con el sobre uniforme
  `{"error": {"code", "message", "details"}}` y manejadores para 400/404/409/413/415/422/500/503
  según `contracts/api.md`
- [ ] T011 Implementar en `backend/app/services/session_store.py` el candado de operación única
  (`threading.Lock` no bloqueante) y la consulta `is_busy()` usada por las rutas (D09)
- [ ] T012 Crear `backend/app/services/audio_validation.py`: validar extensión `.mp3` o `.wav`, MIME
  `audio/mpeg` o `audio/wav`, tamaño máximo `125829120` bytes (120 MB), archivo no vacío y estructura
  legible con `av`; calcular `duration_seconds` con `av`; **sin** tope de duración (D04, D06)
- [ ] T013 Crear `backend/app/transcription/adapter.py` con `transcribe(audio_path, language="es",
  on_segment=None, should_cancel=None)`, la normalización descrita en
  `contracts/transcription-adapter.md` y las cinco excepciones (`TranscriptionRejected`,
  `TranscriptionTimeout`, `TranscriptionUnavailable`, `TranscriptionInvalidResponse`,
  `TranscriptionCancelled`); reintento único solo para timeout y unavailable (RF-006, RNF-004)
- [ ] T014 [P] Crear `backend/app/transcription/fake_engine.py`: transcripción determinista, sin cargar
  el modelo, con inyección de las cinco excepciones vía variable de entorno (D20)
- [ ] T015 Implementar en `backend/app/services/session_store.py` el reemplazo atómico de 7 pasos:
  validar sin tocar la sesión, transcribir, escribir temporales, verificar legibilidad, promover audio y
  documento, limpiar audio y exportación anteriores, revertir ante fallo o cancelación (RF-013, RF-014,
  RF-015, D17)

**Checkpoint**: existe `session-current` vacía, el candado responde, la validación de audio funciona y
el adaptador se puede probar con el motor falso.

---

## Phase 3: User Story 1 — Cargar audio sintético y obtener su transcripción (Priority: P1) 🎯 MVP

**Goal**: el profesional carga un audio sintético válido y recibe una transcripción en español con
marcas por palabra y oración, sin perder la sesión anterior ante fallos.

**Independent Test**: `POST /api/session/audio` con `fixtures/audio/entrevista-sintetica.wav` devuelve
`200` con `status: ready` y al menos un segmento con palabras marcadas; un archivo inválido devuelve
error y la sesión previa sigue intacta.

### Tests de US1 (escribir primero, deben fallar)

- [ ] T016 [P] [US1] Pruebas unitarias de validación en `backend/tests/unit/test_audio_validation.py`:
  extensión no admitida, archivo vacío, archivo corrupto, 120 MB exactos (acepta) y 120 MB + 1 byte
  (rechaza) (RF-001, RF-002)
- [ ] T017 [P] [US1] Pruebas de contrato del adaptador en `backend/tests/unit/test_transcription_adapter.py`
  con `fake_engine`: respuesta válida en español, timestamps por palabra, timeout con un reintento,
  error definitivo, respuesta vacía y segmentos solapados (RF-004, RF-005, RF-006)
- [ ] T018 [P] [US1] Prueba de integración de `/health` en
  `backend/tests/integration/test_health_during_transcription.py`: con una transcripción lenta simulada,
  `GET /health` responde `200` en menos de 1 s (research D11)

### Implementación de US1

- [ ] T019 [US1] Implementar `backend/app/transcription/faster_whisper_engine.py`: modelo `base` cargado
  de forma perezosa y reutilizado (candado de inicialización), `language="es"`,
  `word_timestamps=True`, GPU si está disponible con CPU `int8` como respaldo, y consulta de
  `should_cancel` entre segmentos (D02, D03, D12, D21)
- [ ] T020 [US1] Implementar `POST /api/session/audio` en `backend/app/api/session.py` como función
  **síncrona** (`def`, no `async def`) que devuelve `200 {session, cancelled}`, `409 busy`,
  `409 cancelled`, `413 payload_too_large`, `415 unsupported_format`, `422 invalid_audio`,
  `500 persistence_error` o `503 transcription_unavailable` (RF-001, RF-002, RF-004, RF-006, D10, D11)
- [ ] T021 [US1] Implementar `POST /api/session/cancel` en `backend/app/api/session.py`: marca
  `operation.cancel_requested = true`, devuelve `202`, o `409 not_processing` si no hay operación
  (RF-015, D12)
- [ ] T022 [P] [US1] Pruebas de integración en `backend/tests/integration/test_audio_upload.py`: carga
  válida, extensión falsa, tamaño excedido, carga simultánea `409 busy`, fallo del motor `503` y
  cancelación `409 cancelled` con sesión anterior intacta (RF-001 a RF-006, RF-012 a RF-015)
- [ ] T023 [US1] Crear `frontend/src/components/SyntheticBanner.jsx` con banner permanente y
  confirmación explícita obligatoria antes de cada envío (RF-003, RNF-001)
- [ ] T024 [US1] Crear `frontend/src/components/UploadPanel.jsx` y conectarlo en
  `frontend/src/App.jsx`: selección de archivo, estado `validating`/`processing`, botón de cancelar,
  mensajes de error por `code` y refresco de la sesión al terminar (RF-001, RF-002, RF-015, RF-016)

**Checkpoint**: el flujo cargar → transcribir funciona de punta a punta por API y por interfaz, y es
demostrable sin editor ni anotaciones.

---

## Phase 4: User Story 2 — Revisar y editar la transcripción (Priority: P2)

**Goal**: el profesional reproduce el audio sincronizado y corrige texto y marcas de tiempo.

**Independent Test**: con una transcripción existente, `PUT /api/session/transcription` acepta un texto
corregido con marcas válidas y rechaza rangos negativos, invertidos, solapados o fuera del audio; el
audio original no cambia.

### Tests de US2

- [ ] T025 [P] [US2] Pruebas unitarias en `backend/tests/unit/test_transcription_edit.py`:
  `start_time < end_time`, valores negativos, segmentos solapados, segmento fuera de
  `duration_seconds`, palabra fuera de su segmento y texto vacío (RF-008, RNF-004)
- [ ] T026 [P] [US2] Pruebas de estado del reproductor en `frontend/tests/AudioPlayer.test.jsx`:
  cambio entre 1x, 1.25x y 1.5x, pausa, salto a timestamp y resaltado del segmento activo, sin
  reproducción real de audio (RF-007)

### Implementación de US2

- [ ] T027 [US2] Implementar `PUT /api/session/transcription` en `backend/app/api/transcription.py`:
  recibe la lista completa de segmentos, valida y devuelve `200` con `status: "reviewed"`, `409
  not_editable` o `422 invalid_timestamps` / `empty_text` (RF-008)
- [ ] T028 [US2] Crear `frontend/src/components/AudioPlayer.jsx`: reproducción, pausa, velocidades
  1x/1.25x/1.5x, salto a timestamp y emisión del tiempo actual (RF-007)
- [ ] T029 [US2] Crear `frontend/src/components/TranscriptEditor.jsx`: edición de texto y de marcas por
  segmento, con validación en cliente y guardado contra `PUT /api/session/transcription` (RF-008)
- [ ] T030 [US2] Implementar en `frontend/src/App.jsx` la sincronización entre reproductor y editor:
  resaltar el segmento activo sin re-renderizar toda la lista (RF-007, RNF-004)
- [ ] T031 [P] [US2] Prueba de integración en `backend/tests/integration/test_transcription_edit.py`:
  edición válida persiste, edición inválida no altera el documento y el audio conserva tamaño y
  contenido (RF-008, RF-011)

**Checkpoint**: transcripción editable y sincronizada con el audio, con validaciones comprobadas.

---

## Phase 5: User Story 3 — Anotar fragmentos de la entrevista (Priority: P3)

**Goal**: el profesional añade, edita y elimina notas de texto libre ligadas a un segmento.

**Independent Test**: crear una anotación de 500 caracteres sobre un segmento existente devuelve `201`;
de 501 devuelve `422 annotation_too_long`; editar y eliminar no modifican el audio.

### Tests de US3

- [ ] T032 [P] [US3] Pruebas unitarias en `backend/tests/unit/test_annotations.py`: texto vacío, 1
  carácter, 500 caracteres (acepta), 501 (rechaza), `segment_id` inexistente y rango fuera del segmento
  (RF-009, RF-010)
- [ ] T033 [P] [US3] Pruebas de integración en `backend/tests/integration/test_annotations.py` para
  `POST`, `PUT` y `DELETE`, incluyendo `404 annotation_not_found` y `409 not_editable` (RF-009 a RF-011)
- [ ] T034 [P] [US3] Prueba de componente en `frontend/tests/AnnotationForm.test.jsx`: contador de
  caracteres y bloqueo del envío al superar 500 (RF-010)

### Implementación de US3

- [ ] T035 [US3] Crear `backend/app/services/annotations.py` con las reglas: texto entre 1 y 500
  caracteres Unicode, `segment_id` existente y rango contenido en el segmento referenciado (RF-009,
  RF-010, D19)
- [ ] T036 [US3] Implementar `POST /api/session/annotations`, `PUT /api/session/annotations/{id}` y
  `DELETE /api/session/annotations/{id}` en `backend/app/api/annotations.py`, con `201`/`200`/`204`
  (RF-009, RF-010, RF-011)
- [ ] T037 [US3] Crear `frontend/src/components/AnnotationList.jsx` y
  `frontend/src/components/AnnotationForm.jsx`: crear desde el fragmento seleccionado, editar, eliminar
  y mostrar el vínculo con el timestamp (RF-009, RF-010, RF-011)
- [ ] T038 [US3] Integrar anotaciones en `frontend/src/App.jsx`: selección de fragmento desde
  `TranscriptEditor` y listado sincronizado con el reproductor (RF-009)

**Checkpoint**: las tres operaciones de anotación funcionan y respetan el límite de 500 caracteres.

---

## Phase 6: User Story 4 — Exportar la sesión (Priority: P4)

**Goal**: el profesional exporta la sesión actual como documento JSON persistido.

**Independent Test**: `POST /api/session/export` devuelve `201` con `exported_at` y un documento que
contiene audio o metadatos, transcripción corregida, marcas de tiempo y anotaciones.

### Tests de US4

- [ ] T039 [P] [US4] Prueba de contrato en `backend/tests/contract/test_export.py`: documento con y sin
  anotaciones, transcripción parcialmente editada, `409 session_not_ready` y eliminación de la
  exportación anterior al confirmar una sesión nueva (RF-016, D24)

### Implementación de US4

- [ ] T040 [US4] Crear `backend/app/services/export.py` que consolide la sesión vigente en el documento
  exportable y lo persista en `current_export`, sobrescribiendo la ranura única (RF-016, D24)
- [ ] T041 [US4] Implementar `POST /api/session/export` en `backend/app/api/export.py`: `201` con
  `{exported_at, document}` o `409 session_not_ready` (RF-016)
- [ ] T042 [US4] Añadir el botón de exportación en `frontend/src/components/ExportPanel.jsx` y la
  confirmación del resultado en `frontend/src/App.jsx` (RF-016)

**Checkpoint**: flujo completo cargar → transcribir → editar → anotar → exportar operativo.

---

## Phase 7: Polish y aspectos transversales

**Propósito**: alinear el contrato, verificar cobertura y dejar el proyecto reproducible.

- [ ] T043 Eliminar `PUT /api/session` de `backend/app/main.py` y dejar solo `GET /api/session`
  (D27, `contracts/api.md`)
- [ ] T044 [P] Revisar que `backend/app/main.py` mantiene CORS restringido a `CORS_ORIGINS` y que
  `PUT`/`DELETE` no quedaron huérfanos en `contracts/api.md` (RNF-001, RNF-002)
- [ ] T045 [P] Ejecutar los 11 escenarios de `quickstart.md` y registrar el resultado en
  `docs/validacion-mvp.md` (RF-001 a RF-016)
- [ ] T046 [P] Actualizar `README.md`: endpoints reales, comandos de prueba
  (`docker compose exec api pytest`, `npm test`), precarga del modelo y límite de 120 MB (RNF-005)
- [ ] T047 [P] Añadir la matriz de cobertura RF → prueba al final de `specs/002-mvp-analisis-inicial/tasks.md`
  verificando que RF-001…RF-016 y RNF-001…RNF-005 tienen al menos una prueba (RNF-005)
- [ ] T048 Verificar el criterio de aceptación global de `quickstart.md`: los escenarios de fallo y
  cancelación conservan la sesión anterior y el reemplazo deja una única sesión (RF-012 a RF-015)

---

## Dependencies & Execution Order

### Dependencias por fase

- **Setup (Fase 1)**: sin dependencias; puede empezar de inmediato
- **Foundational (Fase 2)**: depende de Fase 1 y **bloquea** las historias
- **US1 (Fase 3)**: depende de Fase 2; sin dependencias de otras historias
- **US2 (Fase 4)**: depende de Fase 2; necesita una transcripción existente para probarse, que produce
  US1 en la práctica, pero su test independiente usa una sesión preparada por fixture
- **US3 (Fase 5)**: depende de Fase 2; su test independiente usa una sesión con transcripción de fixture
- **US4 (Fase 6)**: depende de Fase 2; su test independiente usa un documento de fixture
- **Polish (Fase 7)**: depende de que las historias que se quieran entregar estén completas

### Dependencias internas de cada historia

- Pruebas antes de implementación (deben fallar primero)
- Servicios antes que endpoints
- Endpoints antes que integración en la interfaz
- Nada de dependencias cruzadas que rompan la independencia de las historias

### Orden recomendado para el menor tiempo total

1. Fase 1 y Fase 2 completas (T001–T015)
2. US1 completa (T016–T024) → **primer incremento demostrable**
3. US2 y US3 en paralelo si hay dos personas; en serie, US2 primero
4. US4 (T039–T042)
5. Polish (T043–T048)

## Parallel Example: User Story 1

```bash
# Pruebas de US1 en paralelo (archivos distintos):
Task: "Pruebas unitarias de validación de audio en backend/tests/unit/test_audio_validation.py"
Task: "Pruebas de contrato del adaptador en backend/tests/unit/test_transcription_adapter.py"
Task: "Prueba de /health durante la transcripción en backend/tests/integration/test_health_during_transcription.py"

# Componentes de interfaz en paralelo:
Task: "Banner de datos sintéticos en frontend/src/components/SyntheticBanner.jsx"
Task: "Panel de carga en frontend/src/components/UploadPanel.jsx"
```

## Parallel Example: User Story 2

```bash
Task: "Pruebas unitarias de edición en backend/tests/unit/test_transcription_edit.py"
Task: "Pruebas de estado del reproductor en frontend/tests/AudioPlayer.test.jsx"
```

## Implementación incremental

### MVP primero (solo US1)

1. Completar Fase 1 (T001–T006)
2. Completar Fase 2 (T007–T015)
3. Completar Fase 3 (T016–T024)
4. **Parar y validar**: escenarios 1–7 de `quickstart.md`
5. Demostrar: carga, transcripción y cancelación funcionando con audio sintético

### Entrega incremental

1. Setup + Foundational → base lista
2. US1 → validar y demostrar (MVP)
3. US2 → edición sincronizada → validar
4. US3 → anotaciones → validar
5. US4 → exportación → validar
6. Polish → cobertura y documentación

## Notas

- `[P]` = archivos distintos y sin dependencia de una tarea incompleta
- Las pruebas se escriben antes de la implementación y deben fallar primero
- Cada tarea cabe en un solo archivo de código o de prueba
- Las tareas de backend se ejecutan con `docker compose exec api pytest`
- No se añaden dependencias fuera de `requirements.txt`, `requirements-dev.txt` y `package.json`
- Fuera de alcance: historial de sesiones, autenticación, XAI, chatbot y multiusuario

## Matriz de cobertura RF → prueba

| Requisito | Tareas de prueba |
|---|---|
| RF-001, RF-002 | T016, T022, T045 |
| RF-003 | T023, T048 |
| RF-004, RF-005, RF-006 | T017, T022, T045 |
| RF-007 | T026, T045 |
| RF-008 | T025, T031, T045 |
| RF-009, RF-010, RF-011 | T032, T033, T034, T045 |
| RF-012, RF-013, RF-014, RF-015 | T022, T039, T048 |
| RF-016 | T039, T045 |
| RNF-001, RNF-002 | T023, T044 |
| RNF-003 | T022, T048 |
| RNF-004 | T017, T025, T030 |
| RNF-005 | T046, T047 |

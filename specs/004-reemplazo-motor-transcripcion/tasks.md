# Tasks: Reemplazo del motor de transcripción por el enfoque validado en Audio-Transcript-main

**Input**: Documentos de diseño en `/specs/004-reemplazo-motor-transcripcion/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: incluidas porque `RNF-006` exige pruebas automatizadas y `plan.md` fija `pytest` como stack
de backend. Las pruebas de cada historia se escriben antes de la implementación específica de esa
historia. El motor real se prueba con `WhisperModel` simulado; la integración usa `fake_engine` y no
descarga pesos.

**Organización**: las tareas se agrupan por historia de usuario para que cada una sea implementable y
verificable por separado. `[P]` indica paralelizable (archivos distintos, sin dependencias pendientes).
Cada tarea incluye la ruta de archivo exacta y las referencias `RF-*`/`RNF-*` que cubre.

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: puede ejecutarse en paralelo con otras tareas `[P]` de la misma fase
- **[Story]**: `[US1]`…`[US3]`, según las historias de `spec.md`; las fases Setup, Foundational y
  Polish no llevan etiqueta
- Toda tarea incluye al menos una ruta de archivo

## Convenciones de rutas

- Backend: `backend/app/…`, `backend/tests/…` y `backend/scripts/…`
- Frontend: `frontend/…` (sin cambios en esta feature)
- Documentación: `docs/…`, `README.md` y `specs/004-reemplazo-motor-transcripcion/…`
- Pruebas de backend dentro del contenedor: `docker compose exec -T api pytest`

---

## Phase 1: Setup (infraestructura compartida)

**Propósito**: dejar listos el glosario saneado, la precarga del modelo, los artefactos de evaluación y
la configuración de ignores. Nada de lógica de transcripción.

- [X] T001 Crear `backend/app/transcription/glosario-whisper.txt` a partir de
  `Audio-Transcript-main/glosario-whisper.txt`: conservar términos técnicos y nombres sintéticos,
  eliminar nombres de personas e instituciones reales, codificar en UTF-8 y mantenerlo dentro de la
  ventana de contexto de Whisper (~224 tokens) (RF-003, RNF-001, constitución II, D04, D15)
- [X] T002 [P] Modificar `backend/Dockerfile` para precargar `large-v3-turbo` con
  `WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')` en lugar de `base`, conservando
  `HF_HOME=/opt/models` y `libgomp1` (RF-011, D07, D14)
- [X] T003 [P] Crear `fixtures/audio/entrevista-sintetica.txt` con la transcripción de referencia del
  audio sintético descrito en `fixtures/audio/README.md`, para medir WER del fixture corto (RNF-001,
  D12)
- [X] T004 [P] Añadir `data/audio/eval/` a `.gitignore` para no versionar el audio de referencia ni la
  transcripción corregida manualmente (RNF-002, D12)
- [X] T005 [P] Verificar que `backend/requirements.txt` mantiene `faster-whisper==1.2.1` y
  `av==16.1.0`, y que no se añaden dependencias de runtime para el nuevo modelo (RNF-006, D02, D14)

**Checkpoint**: el glosario saneado existe; la imagen puede precargar `large-v3-turbo`; hay referencias
para evaluar; no se versionan audios de evaluación.

---

## Phase 2: Foundational (prerrequisitos bloqueantes)

**Propósito**: helpers compartidos que usan las tres historias. No incluye todavía la transcripción
completa, para que las pruebas de US1 puedan escribirse antes de la implementación del motor.

**⚠️ CRÍTICO**: esta fase bloquea las fases 3 a 5.

- [X] T006 Añadir en `backend/app/transcription/faster_whisper_engine.py` las constantes de
  configuración: `WHISPER_MODEL` por defecto `large-v3-turbo`, `WHISPER_GLOSSARY_PATH`,
  `WHISPER_LOCAL_FILES_ONLY` por defecto `1` y `WHISPER_VAD_FILTER` por defecto `1` (RF-001, RF-002,
  RF-011, D03, D07)
- [X] T007 Implementar en `backend/app/transcription/faster_whisper_engine.py` el cargador del glosario:
  leer UTF-8, recortar espacios, devolver `None` si el archivo falta o está vacío, registrar advertencia
  y un hash corto del contenido; no fallar la transcripción por un glosario ausente (RF-003, RF-012,
  D04)
- [X] T008 Implementar en `backend/app/transcription/faster_whisper_engine.py` los helpers de error y
  registro: distinguir decodificación/formato (`TranscriptionRejected`), falta de voz
  (`TranscriptionRejected`), OOM/recursos (`TranscriptionUnavailable`) y errores internos
  (`TranscriptionUnavailable`); registrar modelo, dispositivo, tiempos y conteos (RF-006, RF-007,
  RNF-003, D09, D17)

**Checkpoint**: existen configuración, glosario y clasificación de errores; las historias pueden
empezar.

---

## Phase 3: User Story 1 — Obtener transcripciones más fieles con el nuevo motor (Priority: P1) 🎯 MVP

**Goal**: el profesional carga un audio sintético y recibe una transcripción en español con menos
errores que la del motor anterior, con nombres y términos técnicos mejor reconocidos.

**Independent Test**: transcribir el conjunto de referencia con `WHISPER_MODEL=base` y con
`WHISPER_MODEL=large-v3-turbo`, y comprobar que el WER baja al menos 20 % en términos relativos y que
los aciertos de glosario llegan al 90 %.

### Tests de US1 (escribir primero, deben fallar)

- [X] T009 [P] [US1] Crear `backend/tests/unit/test_faster_whisper_engine.py` con `WhisperModel`
  simulado: verificar que se pasa `large-v3-turbo`, `language="es"`, `beam_size=5`,
  `word_timestamps=True`, `vad_filter=True`, `initial_prompt=<glosario>` y `local_files_only=True`
  (RF-001 a RF-005, RNF-001)
- [X] T010 [US1] Añadir pruebas del cargador de glosario en `backend/tests/unit/test_faster_whisper_engine.py`: archivo válido, override por `WHISPER_GLOSSARY_PATH`, archivo ausente, archivo vacío y hash registrado (RF-003, RF-012, D04)
- [X] T011 [P] [US1] Crear `backend/scripts/evaluate_transcription.py` con argumentos `--audio`,
  `--reference` y `--model`; normalizar mayúsculas, puntuación y espacios; calcular WER por distancia de
  edición de palabras y aciertos de glosario; emitir JSON (RNF-001, SC-001, SC-002, D11)

### Implementación de US1

- [X] T012 [US1] Implementar en `backend/app/transcription/faster_whisper_engine.py` la carga del modelo
  con `local_files_only`, GPU `float16` y fallback a CPU `int8`; mantener el candado de inicialización
  y el modelo único por proceso (RF-001, RF-011, RNF-002, D07, D08)
- [X] T013 [US1] Implementar en `backend/app/transcription/faster_whisper_engine.py` la llamada a
  `model.transcribe` con `language="es"`, `word_timestamps=True`, `vad_filter` configurable,
  `beam_size=5` e `initial_prompt` del glosario; conservar `on_segment` y `should_cancel` (RF-002 a
  RF-005, D03, D06)
- [X] T014 [US1] Implementar en `backend/app/transcription/faster_whisper_engine.py` la detección de
  audio sin voz: si el VAD o el motor no producen segmentos, lanzar `TranscriptionRejected` con un
  mensaje comprensible; no devolver una transcripción vacía (RF-004, RF-007, D05, D09)
- [X] T015 [US1] Usar `Audio-Transcript-main/audioCorto.wav` con la referencia humana
  `tests_audio/transcripcion_audioCorto.txt` y, como contraste de dominio, `tests_audio/audio_espanol.wav`
  con `tests_audio/transcripcion.txt`; verificar que las referencias no tengan timestamps (SC-001, D12)
- [X] T016 [US1] Ejecutar `backend/scripts/evaluate_transcription.py` con `--model base` y con
  `--model large-v3-turbo` sobre `audioCorto` y sobre `tests_audio/audio_espanol.wav`; registrar WER y
  aciertos de glosario en `docs/validacion-004.md`; verificar ≥20 % de reducción relativa en el audio
  clínico y ≥90 % de aciertos (SC-001, SC-002, RNF-001)

**Checkpoint**: el nuevo motor transcribe en español con glosario y VAD; la evaluación demuestra la
mejora de calidad. Éste es el MVP.

---

## Phase 4: User Story 2 — Mantener la sincronización y el flujo de revisión (Priority: P2)

**Goal**: la nueva transcripción conserva marcas por palabra y por oración, se sincroniza con el audio
y se puede editar sin volver a transcribir ni modificar el audio original.

**Independent Test**: con una transcripción generada por el nuevo motor, reproducir el audio, saltar a
una marca, editar texto y tiempos, y comprobar que las palabras y el audio original siguen intactos.

### Tests de US2 (escribir primero, deben fallar)

- [X] T017 [P] [US2] Añadir en `backend/tests/unit/test_faster_whisper_engine.py` pruebas de salida con
  palabras: cada segmento tiene `start_time < end_time`, cada palabra tiene marcas dentro del segmento y
  la normalización del adaptador conserva las palabras (RF-005, SC-003, D06)
- [X] T018 [P] [US2] Añadir en `backend/tests/integration/test_audio_upload.py` una carga con
  `fake_engine` que verifique `language="es"`, `provider="local"`, segmentos con palabras y marcas
  dentro de la duración del audio (RF-005, SC-003)
- [X] T019 [P] [US2] Añadir en `backend/tests/integration/test_transcription_edit.py` pruebas de que
  editar texto y marcas conserva las palabras, no modifica el audio (hash y tamaño) y no relanza la
  transcripción (RF-008, RF-013, RF-014)
- [X] T020 [P] [US2] Añadir en `backend/tests/integration/test_session_view.py` una prueba de
  `GET /api/session/segments/{id}/words` que devuelva las marcas por palabra del segmento solicitado
  (RF-005, SC-003)

### Implementación de US2

- [X] T021 [US2] Ajustar en `backend/app/transcription/faster_whisper_engine.py` la construcción de
  `words` para conservar el texto y las marcas de cada palabra devuelta por `faster-whisper`, sin
  alterar el orden ni recortar palabras válidas (RF-005, D06)
- [X] T022 [US2] Verificar en `backend/app/transcription/adapter.py` que la normalización existente
  recorta palabras al segmento, descarta palabras vacías y conserva la relación segmento-palabra; no
  cambiar la interfaz pública (RF-005, RF-008, D06)
- [X] T023 [US2] Verificar que `backend/app/api/session.py` no vuelve a transcribir una sesión ya
  confirmada o editada y que el audio original no se sobrescribe (RF-013, RF-014)

**Checkpoint**: la transcripción nueva se reproduce, se sincroniza y se edita sin regresiones.

---

## Phase 5: User Story 3 — Conservar las garantías operativas y de privacidad (Priority: P3)

**Goal**: el nuevo motor mantiene cancelación, fallos controlados, sesión única, aislamiento de red y
rendimiento aceptable.

**Independent Test**: cancelar una transcripción, provocar un fallo de recursos, comprobar que no hay
egreso de red y medir el tiempo de un audio de ~10 minutos.

### Tests de US3 (escribir primero, deben fallar)

- [X] T024 [P] [US3] Añadir en `backend/tests/unit/test_faster_whisper_engine.py` pruebas de carga:
  GPU falla y se usa CPU `int8`; ambas fallan y se lanza `TranscriptionUnavailable`; se pasa
  `local_files_only=True` (RF-007, RF-011, RNF-002, RNF-003)
- [X] T025 [US3] Añadir en `backend/tests/unit/test_faster_whisper_engine.py` pruebas de
  cancelación: `should_cancel=True` antes de cargar no carga el modelo; `True` entre segmentos lanza
  `TranscriptionCancelled` (RF-006, RNF-005, D10)
- [X] T026 [US3] Añadir en `backend/tests/unit/test_faster_whisper_engine.py` pruebas de mapeo de
  errores: `MemoryError`/OOM → `TranscriptionUnavailable`; error de decodificación →
  `TranscriptionRejected`; salida vacía → la categoría definida en el contrato (RF-007, D09)
- [X] T027 [P] [US3] Añadir en `backend/tests/integration/test_audio_upload.py` una prueba con
  `FAKE_TRANSCRIBER_ERROR=unavailable` que verifique `503 transcription_unavailable` y la conservación
  de la sesión anterior (RF-009, SC-005)
- [X] T028 [US3] Añadir en `backend/tests/integration/test_audio_upload.py` una prueba de
  cancelación que verifique `409 cancelled`, sesión anterior intacta y ausencia de temporales
  (RF-009, RF-015, SC-005)

### Implementación y validación de US3

- [X] T029 [US3] Comprobar en `backend/app/transcription/faster_whisper_engine.py` que la cancelación se
  consulta antes de cargar, después de cargar y entre segmentos; documentar que la carga de pesos no es
  interrumpible (RF-006, D10)
- [X] T030 [US3] Comprobar que `backend/app/api/errors.py` mantiene el mapeo HTTP existente:
  `TranscriptionRejected` → `422 invalid_audio`, `TranscriptionUnavailable`/`Timeout`/`InvalidResponse`
  → `503 transcription_unavailable`, `TranscriptionCancelled` → `409 cancelled` (RF-006, RF-007,
  RF-009)
- [X] T031 [US3] Ejecutar `docker compose build api` y `docker compose run --rm api python -c` para
  cargar `large-v3-turbo` con `local_files_only=True`; verificar que no hay descargas en ejecución
  (RF-011, SC-006, D07)
- [X] T032 [US3] Ejecutar el escenario de rendimiento de `quickstart.md` con
  `Audio-Transcript-main/audioCorto.wav` y registrar el tiempo en `docs/validacion-004.md`; verificar
  que 10 minutos de audio se transcriben en menos de 15 minutos (SC-007, RNF-004)
- [X] T033 [US3] Ejecutar el escenario de aislamiento de `quickstart.md` y registrar `SIN EGRESO` en
  `docs/validacion-004.md` (SC-006, RNF-002)

**Checkpoint**: cancelación, fallos, aislamiento y rendimiento quedan demostrados.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: documentación, pruebas completas y verificación de que no cambió el contrato público.

- [X] T034 [P] Actualizar `README.md` en la sección "Modelo de transcripción": `large-v3-turbo`,
  glosario, VAD, variables `WHISPER_*`, tamaño aproximado de imagen y procedimiento de evaluación
  (RF-012, SC-008)
- [X] T035 [P] Completar `docs/validacion-004.md` con resultados de WER, glosario, rendimiento,
  aislamiento, cancelación y fallos (SC-001 a SC-008)
- [X] T036 [P] Revisar `backend/app/transcription/glosario-whisper.txt` y confirmar que no contiene
  nombres de personas reales ni datos identificables; si aparece alguno, eliminarlo o sustituirlo
  (constitución II, D15)
- [X] T037 [P] Verificar que no cambió el contrato público: `GET /api/session` y la exportación
  conservan las mismas claves y no incluyen el nombre del modelo (RF-010, SC-008)
- [X] T038 Ejecutar `docker compose exec -T api pytest -q` y corregir cualquier regresión (RNF-006,
  SC-008)
- [X] T039 Ejecutar `docker compose exec -T frontend npm test` y confirmar que el frontend no requiere
  cambios (RF-010, SC-008)
- [X] T040 Ejecutar los escenarios 1 a 10 de `quickstart.md` y registrar el resultado global (SC-008)
- [X] T041 Revisar `git status` y `git diff`: no debe haber cambios en `frontend/`, en el esquema de
  base de datos ni en `docker-compose.yml`; los audios de evaluación no deben quedar versionados
  (RF-010, RNF-002)

**Checkpoint**: documentación, pruebas y contrato público verificados.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias; puede empezar de inmediato.
- **Foundational (Phase 2)**: depende de Setup; bloquea las historias.
- **User Stories (Phase 3+)**: dependen de Foundational.
  - US1 (P1) es el MVP y debe completarse primero.
  - US2 y US3 pueden empezar después de US1; comparten el mismo motor, pero sus pruebas son
    independientes.
- **Polish (Phase 6)**: depende de las historias que se quieran entregar.

### User Story Dependencies

- **US1 (P1)**: depende de T001–T008. Entrega el motor y la evaluación de calidad.
- **US2 (P2)**: depende de US1 para tener una transcripción real; sus pruebas de marcas y edición
  pueden ejecutarse con `fake_engine` antes de que US1 termine.
- **US3 (P3)**: depende de US1 para probar fallos y rendimiento del motor real; las pruebas de
  cancelación y mapeo de errores pueden usar mocks.

### Within Each User Story

- Las pruebas se escriben antes de la implementación específica de la historia y deben fallar.
- La configuración y los helpers de Phase 2 se completan antes de las pruebas de US1.
- US1 implementa el motor y la evaluación; US2 verifica marcas y edición; US3 verifica operación.
- No se avanza a la siguiente historia sin validar el checkpoint de la anterior.

### Parallel Opportunities

- Setup: T002, T003, T004 y T005 son paralelizables tras T001.
- US1: T009 y T011 son paralelizables (archivos distintos); T010 comparte
  `test_faster_whisper_engine.py` con T009 y debe ejecutarse después. T015 y T016 pueden solaparse con
  la implementación, pero T016 requiere T011 y T015.
- US2: T017, T018, T019 y T020 son paralelizables (archivos distintos).
- US3: T024 y T027 son paralelizables (archivos distintos); T025–T026 comparten
  `test_faster_whisper_engine.py`, y T028 comparte `test_audio_upload.py` con T027.
- Polish: T034, T035, T036 y T037 son paralelizables; T038–T040 son validaciones secuenciales.

---

## Parallel Example: User Story 1

```bash
# Pruebas de configuración y script de evaluación en paralelo:
Task: "T009 [US1] Pruebas de configuración del motor en backend/tests/unit/test_faster_whisper_engine.py"
Task: "T011 [US1] Crear backend/scripts/evaluate_transcription.py"

# La prueba del glosario comparte archivo con T009 y va después:
Task: "T010 [US1] Pruebas del cargador de glosario en backend/tests/unit/test_faster_whisper_engine.py"

# La referencia manual puede prepararse en paralelo; T016 depende de T011 y T015:
Task: "T015 [US1] Verificar audioCorto/transcripcion_audioCorto.txt y tests_audio/transcripcion.txt"
```

## Parallel Example: User Story 2

```bash
Task: "T017 [US2] Pruebas de palabras en backend/tests/unit/test_faster_whisper_engine.py"
Task: "T018 [US2] Pruebas de integración de palabras en backend/tests/integration/test_audio_upload.py"
Task: "T019 [US2] Pruebas de edición en backend/tests/integration/test_transcription_edit.py"
Task: "T020 [US2] Pruebas de marcas por segmento en backend/tests/integration/test_session_view.py"
```

## Parallel Example: User Story 3

```bash
Task: "T024 [US3] Pruebas de fallback GPU/CPU en backend/tests/unit/test_faster_whisper_engine.py"
Task: "T027 [US3] Prueba de 503 y sesión previa en backend/tests/integration/test_audio_upload.py"

# T025–T026 comparten archivo con T024; T028 comparte archivo con T027:
Task: "T025 [US3] Pruebas de cancelación en backend/tests/unit/test_faster_whisper_engine.py"
Task: "T026 [US3] Pruebas de mapeo de errores en backend/tests/unit/test_faster_whisper_engine.py"
Task: "T028 [US3] Prueba de cancelación y temporales en backend/tests/integration/test_audio_upload.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1 (glosario saneado, Dockerfile, referencias).
2. Completar Phase 2 (configuración, glosario, errores).
3. Completar Phase 3 (motor `large-v3-turbo`, VAD, glosario, evaluación).
4. **STOP and VALIDATE**: ejecutar la evaluación de calidad y el quickstart de carga corta.
5. Si la mejora de WER y glosario se cumple, el MVP está listo.

### Incremental Delivery

1. Setup + Foundational → base lista.
2. US1 → motor nuevo y calidad demostrada.
3. US2 → marcas y edición verificadas.
4. US3 → cancelación, fallos, aislamiento y rendimiento verificados.
5. Polish → documentación y regresión completa.

### Notas de ejecución

- No ejecutar el modelo real en pruebas unitarias: usar `WhisperModel` simulado.
- No versionar `Audio-Transcript-main/` ni `data/audio/eval/`.
- Mantener `av==16.1.0`; no actualizar a `av 17+` sin revisar la compatibilidad con
  `faster-whisper==1.2.1`.
- Si el WER no mejora, revisar primero el glosario, el VAD y el idioma antes de cambiar de modelo.
- Si el rendimiento no cumple, medir con GPU o ajustar hilos de CPU antes de aceptar el cambio.

---

## Resultado de la comparación

- **T015** y **T016** se ejecutaron sobre el audio clínico `Audio-Transcript-main/audioCorto.wav`
  (9 min 27 s) con la referencia humana `tests_audio/transcripcion_audioCorto.txt` (1465 palabras, sin
  timestamps, corregida a mano).
- **T016 cumple `SC-001`**: `base` obtuvo WER 0,474403 y `large-v3-turbo` 0,264846, una reducción
  relativa del **44,17 %** (umbral: 20 %). En el conjunto formal (`audioCorto`, fixture corto y glosario
  controlado), `large-v3-turbo` mejora en todos los audios.
- Como contraste de dominio, se ejecutó también `tests_audio/audio_espanol.wav` (escena dialogada,
  7 min 12 s) con `tests_audio/transcripcion.txt`: `base` 0,142346 y `large-v3-turbo` 0,177261. En ese
  audio `base` es ligeramente mejor, pero no representa el dominio clínico.
- El resultado completo está documentado en `docs/validacion-004.md`.

## Requirement Coverage

| Requisito | Tareas |
|---|---|
| RF-001 | T006, T012, T013, T016 |
| RF-002 | T006, T009, T013 |
| RF-003 | T001, T007, T010, T013 |
| RF-004 | T013, T014, T017 |
| RF-005 | T009, T013, T017, T018, T020, T021 |
| RF-006 | T008, T025, T029, T030 |
| RF-007 | T008, T024, T026, T027, T030 |
| RF-008 | T019, T022 |
| RF-009 | T027, T028, T030 |
| RF-010 | T037, T038, T039, T041 |
| RF-011 | T002, T006, T012, T024, T031 |
| RF-012 | T001, T007, T010, T034 |
| RF-013 | T019, T023 |
| RF-014 | T019, T023 |
| RNF-001 | T001, T009, T011, T016 |
| RNF-002 | T004, T012, T024, T033, T041 |
| RNF-003 | T008, T024, T026, T027 |
| RNF-004 | T032 |
| RNF-005 | T025, T036 |
| RNF-006 | T005, T009–T011, T017–T028, T038 |
| SC-001 | T011, T015, T016 |
| SC-002 | T011, T016 |
| SC-003 | T017, T018, T020 |
| SC-004 | T006, T012, T013 |
| SC-005 | T027, T028 |
| SC-006 | T031, T033 |
| SC-007 | T032 |
| SC-008 | T034, T037, T038, T039, T040 |

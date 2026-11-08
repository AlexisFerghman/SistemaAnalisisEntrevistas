# Tasks: Experiencia de transcripción continua

**Input**: Documentos de diseño en `/specs/005-transcripcion-continua/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/ui.md](./contracts/ui.md),
[contracts/api.md](./contracts/api.md), [quickstart.md](./quickstart.md)

**Tests**: incluidas porque el plan fija Vitest + Testing Library y pide pruebas unitarias de las
utilidades y pruebas de componente para cada historia. En cada historia las pruebas se escriben
**antes** de la implementación.

**Organización**: las tareas se agrupan por historia de usuario para que cada una sea implementable y
verificable por separado. `[P]` indica paralelizable (archivos distintos, sin dependencias pendientes).
Cada tarea incluye la ruta de archivo exacta y las referencias `RF-*`/`RNF-*` que cubre.

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: puede ejecutarse en paralelo con otras tareas `[P]` de la misma fase
- **[Story]**: `[US1]`…`[US4]`, según las historias de `spec.md`; las fases Setup, Foundational y
  Polish no llevan etiqueta
- Toda tarea incluye al menos una ruta de archivo

## Convenciones de rutas

- Frontend: `frontend/src/…` y `frontend/tests/…`
- Documentación: `docs/…` y `specs/005-transcripcion-continua/…`
- Pruebas de frontend: `docker compose exec frontend npm test`
- Regresión de backend: `docker compose exec api pytest -q`

---

## Phase 1: Setup (línea base y utilidades de prueba)

**Propósito**: medir el estado actual y preparar helpers de layout/temporizadores. Nada de lógica de
negocio.

- [X] T001 Crear `docs/validacion-005.md` con la línea base de pruebas de frontend y backend, y los
  comandos de regresión, en `docs/validacion-005.md` (RNF-015)
- [X] T002 [P] Crear helpers de prueba para `scrollIntoView`, `getBoundingClientRect` y temporizadores
  en `frontend/tests/helpers/interactions.js` (RNF-011, RNF-016)

**Checkpoint**: la línea base y los helpers están listos.

---

## Phase 2: Foundational (prerrequisitos bloqueantes)

**Propósito**: utilidades puras que necesitan las historias de agrupación y waveform. Ninguna historia
puede empezar antes de completar esta fase.

**⚠️ CRÍTICO**: esta fase bloquea US2 y US4.

- [X] T003 [P] Pruebas unitarias de agrupación de observaciones en
  `frontend/tests/unit/observations.test.js`: mismo timestamp, distancia menor o igual a 14 px,
  distancia mayor, grupo de una sola observación y recálculo con otro ancho (RF-031, D42)
- [X] T004 [P] Pruebas unitarias de variación determinista de waveform en
  `frontend/tests/unit/waveform.test.js`: misma semilla produce el mismo perfil, semillas distintas
  producen perfiles distintos y se conserva la longitud de `peaks` (RF-037, D46)
- [X] T005 [P] Implementar `groupObservations(markers, width)` en
  `frontend/src/utils/observations.js`, con umbral de 14 px y contador por grupo (RF-031, D42)
- [X] T006 [P] Implementar la variación determinista de `peaks` a partir de una semilla de sesión en
  `frontend/src/utils/waveform.js` (RF-037, D46)

**Checkpoint**: las utilidades de agrupación y waveform están probadas y disponibles.

---

## Phase 3: User Story 1 — Leer la transcripción como un flujo continuo (Priority: P1) 🎯 MVP

**Goal**: el profesional lee la transcripción como un flujo continuo que sigue al audio sin hacer
`seek`, y controla la reproducción solo con acciones explícitas.

**Independent Test**: con una sesión de más de 50 segmentos, reproducir el audio y comprobar que el
segmento activo se mantiene visible, que el scroll manual pausa el seguimiento durante 5 s y que el
texto no provoca saltos de audio.

### Tests de US1 (escribir primero, deben fallar)

- [X] T007 [P] [US1] Pruebas de flujo continuo, auto-scroll, pausa manual, reanudación a los 5 s y
  `prefers-reduced-motion` en `frontend/tests/TranscriptList.continuous.test.jsx` (RF-024 a RF-028,
  RNF-012)
- [X] T008 [P] [US1] Pruebas de controles de `seek`, botón play, chip de tiempo y clic sobre texto sin
  `seek` en `frontend/tests/TranscriptControls.test.jsx` (RF-028 a RF-030)

### Implementación de US1

- [X] T009 [US1] Convertir `frontend/src/components/TranscriptList.jsx` en un flujo vertical continuo
  con scroll único, segmento activo visible y contexto de 1 anterior + 2 posteriores (RF-024, RF-025)
- [X] T010 [US1] Implementar en `frontend/src/components/TranscriptList.jsx` el auto-scroll con pausa
  de 5 s, reanudación automática, “Volver al audio” y detección de scroll manual (RF-026, RF-027,
  RNF-012)
- [X] T011 [US1] Añadir en `frontend/src/components/TranscriptList.jsx` el chip de tiempo, el botón
  con símbolo de play y la separación entre clic de lectura y `seek` (RF-028 a RF-030)
- [X] T012 [US1] Integrar la solicitud de reproducción desde `frontend/src/App.jsx` hacia
  `frontend/src/components/AudioPlayer.jsx` para que el botón play haga `seek` y reproduzca (RF-030)
- [X] T013 [US1] Añadir estilos de flujo continuo, segmento activo, pausa y movimiento reducido en
  `frontend/src/styles.css` (RF-024, RNF-012)

**Checkpoint**: el flujo continuo y los controles explícitos funcionan sin `seek` accidental.

---

## Phase 4: User Story 2 — Consultar observaciones agrupadas (Priority: P2)

**Goal**: el profesional ve observaciones cercanas agrupadas y las consulta en un popover no modal,
de solo lectura, con acceso para revelar el fragmento sin cambiar el audio.

**Independent Test**: con tres observaciones próximas, comprobar que hay un marcador con contador, que
el popover lista las tres, que se cierra al salir de la zona y que “Ver fragmento” desplaza la
transcripción sin hacer `seek`.

### Tests de US2 (escribir primero, deben fallar)

- [X] T014 [P] [US2] Pruebas de agrupación de marcadores en
  `frontend/tests/AudioWaveform.clusters.test.jsx`: contador, una sola observación, distancia límite y
  recálculo al redimensionar (RF-031, D42)
- [X] T015 [P] [US2] Pruebas del popover en `frontend/tests/ObservationPopover.test.jsx`: apertura por
  hover y foco, cierre por salida de zona, botón de cerrar, `Esc`, táctil y navegación por teclado
  (RF-032 a RF-034, RNF-011)
- [X] T016 [P] [US2] Pruebas de “Ver fragmento” en
  `frontend/tests/ObservationPopover.reveal.test.jsx`: revela el segmento, no cambia `currentTime` y
  pausa el auto-scroll 5 s (RF-035, D44)

### Implementación de US2

- [X] T017 [US2] Integrar `groupObservations` en `frontend/src/components/AudioWaveform.jsx` y
  renderizar el marcador agrupado con contador (RF-031)
- [X] T018 [US2] Crear `frontend/src/components/ObservationPopover.jsx` con la lista de observaciones,
  hora, texto y segmento asociado, en modo de solo lectura (RF-034)
- [X] T019 [US2] Implementar en `frontend/src/components/ObservationPopover.jsx` la zona segura
  marcador + popover, la tolerancia de 150 ms, el cierre por botón/`Esc`/toque fuera y el
  posicionamiento sin salir de la pantalla (RF-032, RF-033, D43)
- [X] T020 [US2] Añadir la solicitud de revelado desde `frontend/src/App.jsx` hacia
  `frontend/src/components/TranscriptList.jsx`, sin `seek` y con pausa de auto-scroll (RF-035)
- [X] T021 [US2] Añadir en `frontend/src/components/ObservationPopover.jsx` y
  `frontend/src/components/AudioWaveform.jsx` la semántica `aria-expanded`, `aria-controls`, foco
  devuelto al marcador y recorrido por teclado (RNF-011, D48)
- [X] T022 [US2] Añadir estilos de marcador agrupado, contador, popover, foco visible y táctil en
  `frontend/src/styles.css` (RF-031 a RF-033)

**Checkpoint**: las observaciones agrupadas, el popover y “Ver fragmento” funcionan sin bloquear la
página ni mover el audio.

---

## Phase 5: User Story 3 — Editar subtítulos en una vista unificada (Priority: P3)

**Goal**: el profesional edita la transcripción completa en bloques continuos, con timestamps visibles
y las validaciones actuales.

**Independent Test**: entrar en edición, comprobar que todos los segmentos están en un único flujo,
guardar un cambio válido y verificar que un rango inválido sigue bloqueando el guardado.

### Tests de US3 (escribir primero, deben fallar)

- [X] T023 [P] [US3] Pruebas de edición en bloques continuos en
  `frontend/tests/TranscriptEditor.test.jsx`: todos los segmentos visibles, separadores, timestamps y
  texto no truncado (RF-036)
- [X] T024 [P] [US3] Pruebas de guardado y validación en
  `frontend/tests/TranscriptEditor.save.test.jsx`: identidad de segmentos, texto vacío, rangos
  inválidos, solapamientos y audio sin cambios (RF-036, RNF-015)

### Implementación de US3

- [X] T025 [US3] Reestructurar `frontend/src/components/TranscriptEditor.jsx` en bloques continuos con
  separadores visuales, timestamps y campos editables por segmento (RF-036)
- [X] T026 [US3] Ajustar `frontend/src/styles.css` para la edición unificada, manteniendo el texto
  completo, el foco visible y la legibilidad (RF-036, RNF-011)
- [X] T027 [US3] Verificar en `frontend/src/App.jsx` y `frontend/src/components/TranscriptEditor.jsx`
  que el guardado sigue enviando la lista completa y conserva las validaciones actuales (RF-036)

**Checkpoint**: la edición unificada conserva segmentos, timestamps y validaciones.

---

## Phase 6: User Story 4 — Identificar cada sesión por su waveform (Priority: P4)

**Goal**: la waveform conserva la amplitud real y varía de forma determinista entre sesiones.

**Independent Test**: cargar dos sesiones distintas y comprobar que sus perfiles no son idénticos;
recargar la misma sesión y comprobar que el perfil se mantiene.

### Tests de US4 (escribir primero, deben fallar)

- [X] T028 [P] [US4] Pruebas de componente de waveform estable y distinta por sesión en
  `frontend/tests/AudioWaveform.waveform.test.jsx` (RF-037, SC-022)

### Implementación de US4

- [X] T029 [US4] Pasar una semilla estable de sesión desde `frontend/src/App.jsx` a
  `frontend/src/components/AudioPlayer.jsx` y `frontend/src/components/AudioWaveform.jsx` (RF-037)
- [X] T030 [US4] Aplicar la variación determinista de `peaks` y el perfil de respaldo en
  `frontend/src/components/AudioWaveform.jsx` (RF-037, D46)

**Checkpoint**: la waveform es estable por sesión, distinta entre sesiones y no rompe el `seek`.

---

## Phase 7: Polish y aspectos transversales

**Propósito**: validar accesibilidad, rendimiento, regresiones y documentación de la entrega.

- [ ] T031 [P] Ejecutar `docker compose exec frontend npm test` y
  `docker compose exec api pytest -q`, y registrar los resultados en `docs/validacion-005.md`
  (RNF-015)
- [ ] T032 Ejecutar los escenarios de `specs/005-transcripcion-continua/quickstart.md` y ampliar
  `docs/validacion-005.md` con el resultado (RF-024 a RF-038)
- [ ] T033 [P] Auditar teclado, foco, `aria` y `prefers-reduced-motion` en
  `frontend/src/components/TranscriptList.jsx`, `frontend/src/components/ObservationPopover.jsx` y
  `frontend/src/styles.css` (RNF-011, RNF-012)
- [ ] T034 [P] Medir la navegación con 200 segmentos y 500 anotaciones en
  `frontend/src/components/TranscriptList.jsx` y `frontend/src/components/AudioWaveform.jsx`
  (RNF-014, RNF-016)
- [ ] T035 Verificar que no hay cambios de API, backend, persistencia ni dependencias y registrar la
  comprobación en `docs/validacion-005.md` (RNF-013, RNF-015)
- [ ] T036 Verificar que el banner, la confirmación de datos sintéticos y las etiquetas actuales siguen
  visibles, y registrarlo en `docs/validacion-005.md` (RF-038, SC-024)

---

## Dependencies & Execution Order

### Dependencias por fase

- **Setup (Fase 1)**: sin dependencias; puede empezar de inmediato.
- **Foundational (Fase 2)**: depende de Fase 1 y **bloquea** US2 y US4.
- **US1 (Fase 3)**: depende de Fase 1; no depende de otras historias.
- **US2 (Fase 4)**: depende de Fase 2; puede integrarse con US1, pero su prueba independiente usa
  marcadores de fixture.
- **US3 (Fase 5)**: depende de Fase 1; su prueba independiente usa segmentos de fixture.
- **US4 (Fase 6)**: depende de Fase 2; su prueba independiente usa peaks de fixture.
- **Polish (Fase 7)**: depende de que las historias que se quieran entregar estén completas.

### Dependencias internas de cada historia

- Pruebas antes de implementación (deben fallar primero).
- Utilidades puras antes de integrarlas en componentes.
- Componente antes de estilos y accesibilidad final.
- La integración en `App.jsx` va después de que el componente tenga su contrato estable.
- Nada de dependencias cruzadas que rompan la independencia de las historias.

### Orden recomendado para el menor tiempo total

1. Fase 1 y Fase 2 completas (T001–T006)
2. US1 completa (T007–T013) → **primer incremento demostrable**
3. US2 completa (T014–T022)
4. US3 completa (T023–T027)
5. US4 completa (T028–T030)
6. Polish (T031–T036)

## Parallel Example: User Story 1

```bash
# Pruebas de US1 en paralelo (archivos distintos):
Task: "Pruebas de flujo continuo en frontend/tests/TranscriptList.continuous.test.jsx"
Task: "Pruebas de controles de seek en frontend/tests/TranscriptControls.test.jsx"
```

## Parallel Example: User Story 2

```bash
Task: "Pruebas de agrupación en frontend/tests/AudioWaveform.clusters.test.jsx"
Task: "Pruebas de popover en frontend/tests/ObservationPopover.test.jsx"
Task: "Pruebas de 'Ver fragmento' en frontend/tests/ObservationPopover.reveal.test.jsx"
```

## Parallel Example: User Story 3

```bash
Task: "Pruebas de bloques continuos en frontend/tests/TranscriptEditor.test.jsx"
Task: "Pruebas de guardado en frontend/tests/TranscriptEditor.save.test.jsx"
```

## Implementación incremental

### MVP primero (solo US1)

1. Completar Fase 1 (T001–T002)
2. Completar Fase 2 (T003–T006)
3. Completar Fase 3 (T007–T013)
4. **Parar y validar**: flujo continuo, pausa de 5 s y controles de `seek`
5. Demostrar lectura continua sin `seek` accidental

### Entrega incremental

1. Setup + Foundational → base lista
2. US1 → flujo continuo → validar
3. US2 → popover de observaciones → validar
4. US3 → edición unificada → validar
5. US4 → waveform determinista → validar
6. Polish → accesibilidad, rendimiento y documentación

## Notas

- `[P]` = archivos distintos y sin dependencia de una tarea incompleta
- Las pruebas se escriben antes de la implementación y deben fallar primero
- Cada tarea cabe en un solo archivo de código o de prueba
- No se añaden dependencias fuera de `frontend/package.json`
- No se modifican `backend/`, la API ni la persistencia
- Se conservan el banner, la confirmación de datos sintéticos y las etiquetas actuales
- El `seek` solo ocurre por chip de tiempo, botón play o waveform
- Fuera de alcance: eliminar avisos, XAI real, análisis afectivo, historial, autenticación y CSV

## Matriz de cobertura RF → tarea

| Requisito | Tareas |
|---|---|
| RF-024, RF-025 | T007, T009, T013 |
| RF-026, RF-027 | T007, T010 |
| RF-028, RF-029, RF-030 | T008, T011, T012 |
| RF-031, RF-032, RF-033 | T003, T005, T014, T017, T019, T022 |
| RF-034, RF-035 | T015, T016, T018, T020 |
| RF-036 | T023, T024, T025, T026, T027 |
| RF-037 | T004, T006, T028, T029, T030 |
| RF-038 | T036 |
| RNF-011 | T002, T015, T021, T033 |
| RNF-012 | T007, T010, T013, T033 |
| RNF-013 | T035 |
| RNF-014 | T034 |
| RNF-015 | T001, T024, T031, T035 |
| RNF-016 | T002, T034 |

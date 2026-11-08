# Implementation Plan: Experiencia de transcripción continua

**Branch**: `005-transcripcion-continua` | **Date**: 2026-11-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-transcripcion-continua/spec.md`

## Summary

Mejorar la experiencia de lectura y navegación de la transcripción sin tocar el backend:

1. Presentar la transcripción como un flujo vertical continuo, con auto-scroll que sigue al audio sin hacer `seek`.
2. Añadir un botón explícito de reproducción por segmento y mantener el chip de tiempo y la waveform como controles de `seek`.
3. Agrupar observaciones cercanas en un único marcador y mostrarlas en un popover no modal, de solo lectura, con acceso para revelar el fragmento sin cambiar el audio.
4. Unificar la edición en bloques continuos, conservando timestamps, identidad de segmento y validaciones actuales.
5. Variar la waveform de forma determinista por sesión manteniendo la amplitud real.

El alcance es exclusivamente de interfaz. No se añaden endpoints, tablas, servicios ni dependencias.

## Technical Context

**Language/Version**: JavaScript ESM con React y Vite, tal como existe en el frontend actual.

**Primary Dependencies**: React, Vite, Vitest, jsdom y `@testing-library/react`. No se añaden dependencias nuevas.

**Storage**: No aplica. Se reutilizan los datos ya disponibles de sesión, transcripción y anotaciones. No hay cambios de esquema ni de persistencia.

**Testing**: Vitest + Testing Library para componentes y utilidades del frontend. `pytest` se ejecuta solo como regresión del backend, que no se modifica.

**Target Platform**: navegador de escritorio moderno; soporte táctil para abrir y cerrar el popover.

**Project Type**: aplicación web existente; esta feature es solo frontend.

**Performance Goals**: mantener una navegación fluida con al menos 200 segmentos y 500 anotaciones; el avance del tiempo no debe re-renderizar toda la transcripción.

**Constraints**: sin cambios de API, base de datos, motor de transcripción ni dependencias; sin autoplay no solicitado; sin `seek` por scroll o clic sobre texto; conservar banner, confirmación y etiquetas actuales.

**Scale/Scope**: una sesión única, una pantalla de trabajo, cuatro mejoras de interfaz y sus pruebas de componente.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate verificable | Resultado |
|---|---|---|
| I. Supervisión humana (NO NEGOCIABLE) | La feature no añade diagnósticos, evaluaciones ni recomendaciones clínicas; solo cambia la presentación y navegación | PASS |
| II. Datos sintéticos y privacidad | No se alteran banner, confirmación de datos sintéticos ni procesamiento local; no se introducen datos reales | PASS |
| III. Sesión única y eliminación | No se modifica el ciclo de sesión ni la persistencia | PASS |
| IV. Calidad y trazabilidad | Se conservan timestamps, identidad de segmento, marcas por palabra, anotaciones y audio original | PASS |
| V. Simplicidad del MVP | Solo se modifica la interfaz; no se añaden servicios, dependencias ni infraestructura | PASS |

**Re-evaluación tras Fase 1**: sin cambios; el diseño de UI y los contratos no introducen violaciones.

## Project Structure

### Documentation (this feature)

```text
specs/005-transcripcion-continua/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones D39-D50
├── data-model.md        # Fase 1: entidades y estados de interfaz
├── quickstart.md        # Fase 1: escenarios de validación
├── contracts/
│   ├── ui.md            # Contrato de interacción de la pantalla
│   └── api.md           # Confirmación de que la API no cambia
└── tasks.md             # Fase 2 (/speckit.tasks, no se crea aquí)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── App.jsx                         # Estado de reproducción, revelado y edición
│   ├── components/
│   │   ├── TranscriptList.jsx          # Flujo continuo y auto-scroll
│   │   ├── TranscriptEditor.jsx        # Edición en bloques continuos
│   │   ├── AudioPlayer.jsx             # Reproducción y solicitud de play
│   │   ├── AudioWaveform.jsx           # Waveform, marcadores y agrupación
│   │   ├── ObservationPopover.jsx      # NUEVO: popover no modal
│   │   └── ...
│   ├── services/api.js                 # Sin cambios funcionales
│   ├── utils/
│   │   ├── format.js                   # Utilidades existentes
│   │   └── waveform.js                 # NUEVO: variación determinista
│   └── styles.css                      # Flujo continuo, popover y reduced motion
└── tests/
    ├── TranscriptList.test.jsx
    ├── TranscriptEditor.test.jsx       # NUEVO/ampliado
    ├── AudioWaveform.test.jsx
    ├── ObservationPopover.test.jsx     # NUEVO
    └── waveform.test.js                # NUEVO
```

**Structure Decision**: se mantiene la aplicación web existente y se concentran los cambios en componentes y utilidades del frontend. No se crean paquetes ni servicios nuevos.

## Design Decisions

Las decisiones completas están en [research.md](./research.md). Resumen operativo:

| Tema | Decisión | Referencia |
|---|---|---|
| Flujo continuo | Un único contenedor con scroll y segmentos en bloque | D39 |
| Auto-scroll | Pausa de 5 s tras interacción manual y reanudación automática | D40 |
| Seek | Solo por chip de tiempo, botón play o waveform | D41 |
| Botón play | `seek` al inicio del segmento y reproducción inmediata | D41 |
| Agrupación | Cluster por proximidad en píxeles, recalculado al redimensionar | D42 |
| Popover | No modal, hover/foco, zona marcador+popover, cierre accesible | D43 |
| Ver fragmento | Revela el segmento sin `seek` y pausa el auto-scroll 5 s | D44 |
| Edición | Bloques continuos, no un `textarea` único | D45 |
| Waveform | Amplitud real + semilla determinista por sesión | D46 |
| Backend | Sin cambios de API, datos ni persistencia | D47 |
| Accesibilidad | Teclado, foco, `aria` y movimiento reducido | D48 |
| Pruebas | Vitest + Testing Library, temporizadores falsos y mocks de layout | D49 |
| Rendimiento | Refs, memoización y actualización sin re-render global | D50 |

## Implementation Order

1. **Fundaciones de UI**: utilidades de waveform y agrupación de observaciones, con pruebas unitarias.
2. **US1 — Flujo continuo**: `TranscriptList`, auto-scroll, pausa/reanudación, controles de `seek` y botón play.
3. **US2 — Popover**: agrupación en `AudioWaveform`, `ObservationPopover`, “Ver fragmento” y accesibilidad.
4. **US3 — Edición unificada**: `TranscriptEditor` en bloques continuos y pruebas de validación.
5. **US4 — Waveform**: variación determinista y fallback de decodificación.
6. **Polish**: regresión visual, reduced motion, pruebas completas y actualización de documentación de validación si aplica.

## Complexity Tracking

> No hay violaciones constitucionales que justificar.

| Violación | Por qué se necesita | Alternativa simple rechazada |
|---|---|---|
| Ninguna | — | — |

## Re-evaluación Constitution Check

Tras el diseño de entidades, contratos y quickstart, los cinco principios siguen cumpliéndose. La feature no añade funcionalidad clínica, no modifica la sesión ni la persistencia, conserva las marcas y anotaciones, y mantiene los avisos obligatorios y el alcance de interfaz.

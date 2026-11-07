# Validación del MVP — Feature 002

**Fecha**: 2026-11-07
**Feature**: `002-mvp-analisis-inicial`
**Alcance**: Fase 7 (Polish), incluidos los 11 escenarios de
[`quickstart.md`](../specs/002-mvp-analisis-inicial/quickstart.md).

Este documento registra la ejecución manual sobre los contenedores reales. Las pruebas automatizadas
se ejecutaron además con `pytest` y `Vitest` (ver el resultado final).

## Preparación

- Audio sintético: `fixtures/audio/entrevista-sintetica.wav`, 17,40 s, 556 818 bytes.
- Entrada HTTP: `http://localhost:5173` (proxy de Vite hacia `api:8000`).
- Sesión inicial: `empty`, sin audio y sin anotaciones.
- Se respaldaron la sesión y el audio del usuario antes de la validación y se restauraron al terminar.

## Resultado de los 11 escenarios

| # | Escenario | Evidencia | Estado |
|---|---|---|---|
| 1 | Sesión inicial vacía | `status: empty`, `has_audio: false`, `annotations: []` | PASS |
| 2 | Carga válida y transcripción sincronizada | `200`, `status: ready`, `cancelled: false`, 4 segmentos; primer segmento `0.0–2.74` con 7 palabras | PASS |
| 3 | Extensión falsa | `422 invalid_audio`; la sesión siguió `ready` con 4 segmentos | PASS |
| 4 | Formato no admitido y tamaño excedido | `415 unsupported_format` y `413 payload_too_large`; sesión intacta | PASS |
| 5 | Carga simultánea rechazada | Segunda carga `409 busy`; al terminar la primera, sesión `ready` y solo `current.wav` | PASS |
| 6 | Healthcheck durante la transcripción | Tres respuestas `200` (`0.0115 s`, `0.0106 s`, `0.0046 s`); API `healthy` | PASS |
| 7 | Cancelación conserva la sesión anterior | `202` al cancelar; carga `409 cancelled`; sesión previa `ready`, sin temporales | PASS |
| 8 | Edición y validación de marcas | Marca fuera de rango `422 invalid_timestamps`; edición válida `200 reviewed`; hash y tamaño del audio sin cambios | PASS |
| 9 | Anotaciones de 500 / 501 caracteres | `201` y `422 annotation_too_long`; la sesión quedó con 1 anotación | PASS |
| 10 | Exportación y reemplazo de sesión | Exportación con `exported_at` y claves `annotations`, `audio`, `session_id`, `status`, `transcription`, `version`; nueva carga `200`; anotaciones a 0; un único `current.*`; exportación anterior eliminada | PASS |
| 11 | Aislamiento de red | `SIN EGRESO` al intentar `1.1.1.1:443`; `GET /api/session` sigue respondiendo `200` | PASS |

**Tiempo de transcripción del escenario 2**: 2,92 s para 17,40 s de audio, muy por debajo del objetivo
de 15 minutos para 10 minutos de audio.

## Criterio de aceptación global (T048)

Comprobación adicional después del escenario 10, con una anotación real en la sesión:

1. Se creó una anotación (`201`).
2. Se inició una nueva carga y se canceló (`202`).
3. La carga respondió `409 cancelled`.
4. La sesión conservó `status: reviewed` y la anotación existente (1 anotación).
5. `current_session` siguió con exactamente una fila.
6. `data/audio` contenía únicamente `current.wav`, sin temporales.

Conclusión: los fallos y la cancelación conservan la sesión anterior, y el reemplazo deja una única
sesión.

## Cambios de la Fase 7

- Se eliminaron `PUT /api/session` y `DELETE /api/session` de la API; la sesión solo se muta por los
  endpoints funcionales (`/audio`, `/transcription`, `/annotations`, `/export`).
- Se verificó que `contracts/api.md` no contiene rutas huérfanas de escritura directa de sesión.
- Se verificó que CORS sigue restringido al origen configurado (`http://localhost:5173`) y no emite
  cabecera de permiso para orígenes desconocidos.
- `README.md` se actualizó con los endpoints reales, el acceso a través del proxy del frontend, la
  precarga del modelo y el límite de 120 MB.
- La matriz RF → prueba de `tasks.md` se revisó y cubre `RF-001`…`RF-016` y `RNF-001`…`RNF-005`.

## Pruebas automatizadas

```bash
docker compose exec -T api pytest -q
docker compose exec -T frontend npm test
```

Resultado de esta validación:

- Backend: **114 pruebas en verde**.
- Frontend: **24 pruebas en verde**.

## Convergence (T055–T061)

Se cerraron los hallazgos de la fase de convergencia:

- `POST /api/session/audio` sin archivo devuelve `400 missing_file`.
- `GET /api/session/audio` marca la sesión en `error` si el archivo referenciado no existe.
- El rechazo por `Content-Length` superior a 120 MB ocurre antes de consumir el cuerpo.
- `contracts/ui.md` refleja el botón funcional `Exportar JSON` de la columna de anotaciones.
- La subida envía `model=nube` desde el frontend.
- La transcripción hace scroll al segmento activo respetando 5 s de scroll manual.
- La waveform permite `seek` por clic, arrastre y teclado.

## Limpieza

Se eliminaron los archivos temporales de la validación (`/tmp/falso.wav`, `/tmp/grande.wav`) y se
restauró la sesión original del usuario (`audioCorto.wav`, 132 segmentos).

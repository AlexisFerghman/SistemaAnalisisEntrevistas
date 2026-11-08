# Modelo de datos — Reemplazo del motor de transcripción

**Fase**: 1 (Design)
**Fecha**: 2026-11-07
**Plan**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md) · **Decisiones**: [research.md](./research.md)

## Alcance

El reemplazo del motor **no cambia el modelo persistido**. La sesión sigue siendo un único documento
JSONB en `current_session.payload`, con el mismo esquema y los mismos estados descritos en
[`specs/002-mvp-analisis-inicial/data-model.md`](../002-mvp-analisis-inicial/data-model.md).

Las únicas entidades nuevas son **artefactos de configuración y evaluación** que no se guardan en la
base de datos ni en el documento de sesión:

- el glosario del dominio, versionado como archivo en el backend;
- el conjunto de evaluación local (audio, transcripción de referencia y métricas).

## Relaciones

```text
Sesión (1) ──── (0..1) Audio
      │
      ├──── (0..1) Transcripción ──── (N) Segmento ──── (N) Palabra
      │
      └──── (0..N) Anotación ──── (1) Segmento

Glosario (archivo) ──── se usa como contexto de la Transcripción (no se persiste)
Conjunto de evaluación (local) ──── audio + referencia + métricas (no se persiste)
```

## Entidades persistidas (sin cambios)

### Sesión

| Campo | Tipo | Reglas |
|---|---|---|
| `version` | entero | Siempre `1` |
| `session_id` | texto | Siempre `session-current` |
| `status` | enumerado | `empty`, `validating`, `processing`, `ready`, `reviewed`, `error` |
| `audio` | objeto o `null` | Sin cambios |
| `transcription` | objeto o `null` | Sin cambios de forma; el motor que la produjo no se persiste |
| `annotations` | lista | Sin cambios |
| `operation` | objeto | `started_at`, `cancel_requested` |
| `updated_at` | fecha ISO-8601 | Sin cambios |

### Transcripción

| Campo | Tipo | Reglas |
|---|---|---|
| `language` | texto | Siempre `es` |
| `provider` | texto | Siempre `local`; el modelo concreto se registra en logs, no en el payload |
| `retry_count` | entero | `0` o `1` |
| `segments` | lista | Al menos un segmento; ordenados y sin solapamientos |

### Segmento

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | texto | Único dentro de la transcripción |
| `start_time` | decimal | ≥ 0 y menor que `end_time` |
| `end_time` | decimal | ≤ `duration_seconds` del audio |
| `text` | texto | No vacío |
| `words` | lista | Puede estar vacía solo si el motor no devolvió marcas por palabra; con `large-v3-turbo` se espera completa |

### Palabra

| Campo | Tipo | Reglas |
|---|---|---|
| `text` | texto | No vacío |
| `start_time` | decimal | ≥ `start_time` del segmento y menor que su `end_time` |
| `end_time` | decimal | Mayor que su `start_time` y ≤ `end_time` del segmento |

### Anotación y exportación

Sin cambios respecto de `002`. La exportación sigue siendo una copia consolidada de la sesión y no
incluye el nombre del modelo ni el glosario.

## Entidades no persistidas

### Glosario del dominio

| Campo | Tipo | Reglas |
|---|---|---|
| `path` | texto | `backend/app/transcription/glosario-whisper.txt`, o el valor de `WHISPER_GLOSSARY_PATH` |
| `content` | texto UTF-8 | Términos técnicos y nombres sintéticos separados por comas o líneas; sin nombres de personas reales |
| `version` | texto | Hash corto del contenido, registrado en logs para trazabilidad |
| `max_tokens` | entero | El contenido debe caber en la ventana de contexto de Whisper (~224 tokens); el archivo de referencia cabe |

El glosario no forma parte del documento de sesión ni de la exportación. Cambiarlo no requiere migrar
datos; requiere reconstruir la imagen o montar el archivo y reiniciar el proceso.

### Conjunto de evaluación

| Campo | Tipo | Reglas |
|---|---|---|
| `audio_path` | texto | Audio sintético local; no se versiona si es grande |
| `reference_path` | texto | Transcripción corregida manualmente, independiente de la salida del nuevo motor |
| `model` | texto | `base` o `large-v3-turbo` |
| `wer` | decimal | Errores por palabra tras normalizar mayúsculas, puntuación y espacios |
| `glossary_accuracy` | decimal | Proporción de términos del glosario correctamente escritos |
| `measured_at` | fecha ISO-8601 | Momento de la medición |

Los resultados se archivan en `docs/validacion-004.md`, no en la base de datos.

## Reglas de validación

1. `language` siempre `es`; el motor no detecta idioma.
2. Los segmentos se ordenan por `start_time` y se recortan los solapamientos.
3. `start_time` negativo se fija en `0.0`; `end_time` se limita a la duración del audio.
4. Los segmentos sin texto se descartan.
5. Las palabras heredan los límites de su segmento si el motor devuelve valores fuera de rango.
6. Si no queda ningún segmento, se distingue:
   - audio sin voz o VAD que elimina todo el contenido → `TranscriptionRejected` (422);
   - salida no normalizable por otras causas → `TranscriptionInvalidResponse` (503).
7. El audio original nunca se modifica ni se sustituye.
8. El glosario no se persiste en la sesión ni se exporta.

## Máquina de estados

La máquina de estados de la sesión no cambia:

```text
empty ──carga──▶ validating ──válido──▶ processing ──ok──▶ ready ──edición──▶ reviewed
  ▲                   │                     │                 │                  │
  │                   │ inválido            │ fallo/cancelación│                  │
  └───────────────────┴─────────────────────┴─────────────────┴──────────────────┘
                          (se conserva la sesión anterior; status vuelve a su valor previo)
```

El único cambio es interno a `processing → ready`: la transcripción se produce con
`large-v3-turbo` y debe superar la normalización existente antes de confirmar la sesión.

## Invariantes

1. Existe como máximo una fila en `current_session`.
2. Existe como máximo un audio vigente referenciado por `storage_ref`.
3. Toda anotación referencia un segmento existente.
4. Todos los segmentos caben dentro de `duration_seconds`.
5. No queda ningún archivo temporal tras una confirmación, un fallo o una cancelación.
6. `status = processing` solo se observa mientras una operación está activa.
7. El glosario y las métricas de evaluación no se escriben en la base de datos.
8. El nombre del modelo no aparece en el payload de la sesión ni en la exportación.

## Migración

No requiere migración de esquema ni de datos. Las sesiones existentes siguen siendo válidas; una
sesión ya transcrita no se vuelve a transcribir automáticamente (`RF-013`).

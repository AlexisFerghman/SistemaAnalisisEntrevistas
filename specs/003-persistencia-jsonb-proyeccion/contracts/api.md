# Contrato HTTP — Persistencia JSONB y proyección de lectura

**Base**: `http://localhost:8000` · **Formato**: JSON UTF-8 · **Autenticación**: ninguna (MVP)
**Complementa**: [`../../002-mvp-analisis-inicial/contracts/api.md`](../../002-mvp-analisis-inicial/contracts/api.md)

Este contrato solo modifica la lectura de la sesión y añade el endpoint de palabras de un segmento.
El resto de endpoints de `002` conserva su forma y sus códigos.

## Convenciones

- El sobre de error es el mismo de `002`:
  `{ "error": { "code", "message", "details" } }`.
- `session_id` es el UUID de `current_session.id`, no el literal `session-current`.
- Los tiempos de audio siguen siendo decimales en segundos.
- `view` acepta `summary` y `full`; el valor por defecto es `summary`.

## Endpoints modificados

### `GET /api/session`

Devuelve la sesión vigente en dos vistas.

**Parámetros de consulta**

| Parámetro | Valores | Por defecto | Efecto |
|---|---|---|---|
| `view` | `summary` \| `full` | `summary` | `summary` omite `words` y añade `words_count`; `full` devuelve el documento completo |

**200 — vista resumen (`summary`)**

```json
{
  "version": 1,
  "session_id": "5f0c9a7e-3d2b-4a91-8c44-1b2f0d6e7a10",
  "status": "ready",
  "audio": {
    "filename": "entrevista.wav",
    "mime_type": "audio/wav",
    "size_bytes": 3210000,
    "duration_seconds": 721.4,
    "storage_ref": "current.wav"
  },
  "transcription": {
    "language": "es",
    "provider": "local",
    "retry_count": 0,
    "segments": [
      {
        "id": "segment-001",
        "start_time": 0.0,
        "end_time": 3.2,
        "text": "Texto del segmento.",
        "words_count": 6
      }
    ]
  },
  "annotations": [],
  "operation": null
}
```

Reglas verificables:

1. Ningún objeto de `transcription.segments` contiene la clave `words`.
2. Todos los segmentos contienen `words_count` (entero, `0` si no hay marcas).
3. `annotations` se devuelve completa.
4. La respuesta resumida debe ocupar menos del 25 % de la respuesta `full` sobre la misma sesión.

**200 — vista completa (`full`)**

Documento completo, con `transcription.segments[*].words`, equivalente al que devolvía `002` antes de
esta feature (salvo `session_id`, que ahora es el UUID).

**Errores**

| Código | `code` | Cuándo |
|---|---|---|
| 404 | `session_not_initialized` | No hay sesión creada |
| 422 | `invalid_view` | `view` distinto de `summary` o `full` |

### `GET /api/session/segments/{segment_id}/words`

Devuelve las marcas por palabra de un único segmento para que el editor las solicite bajo demanda.

**200**

```json
{
  "segment_id": "segment-001",
  "words": [
    { "text": "Texto", "start_time": 0.0, "end_time": 0.9 },
    { "text": "del", "start_time": 0.9, "end_time": 1.1 },
    { "text": "segmento.", "start_time": 1.1, "end_time": 1.8 }
  ]
}
```

- Si el segmento existe pero no tiene marcas: `200` con `words: []`.
- No devuelve el resto del documento ni las palabras de otros segmentos.

**Errores**

| Código | `code` | Cuándo |
|---|---|---|
| 404 | `session_not_initialized` | No hay sesión creada |
| 404 | `segment_not_found` | El `segment_id` no existe en la transcripción vigente |

## Endpoints sin cambios

| Endpoint | Contrato | Nota |
|---|---|---|
| `GET /health` | Sin cambios | — |
| `GET /api/session/audio` | Sin cambios | Sigue soportando `Range` y `Accept-Ranges: bytes` (`RF-007`) |
| `POST /api/session/audio` | Sin cambios | Sigue devolviendo `{session, cancelled}` con el documento completo |
| `POST /api/session/cancel` | Sin cambios | Cancelación cooperativa |
| `PUT /api/session/transcription` | Sin cambios | Sigue devolviendo el documento completo y conservando/redistribuyendo `words` |
| `POST /api/session/export` | Sin cambios | Sigue persistiendo el documento completo con `words` (`RF-016`) |

**Nota sobre mutaciones**: `POST /api/session/audio` y `PUT /api/session/transcription` mantienen la
respuesta completa en esta entrega. Cambiarlas a resumen queda fuera de alcance para no alterar
contratos y pruebas ya completadas de `002`.

## Contrato futuro de anotaciones (Fase 5 de `002`)

Las rutas `POST`, `PUT` y `DELETE /api/session/annotations` conservan los códigos y validaciones de
`002`, pero su implementación debe cumplir la restricción de persistencia:

1. Una sola sentencia `UPDATE` por operación.
2. `jsonb_set` o el operador `||` sobre `payload->'annotations'`.
3. Sin `get_document()` + `save_document()` en el camino de anotaciones.
4. Validación de pertenencia al segmento con consulta dirigida o `jsonb_path_exists`.

La verificación es de diseño en esta entrega y de prueba de contrato cuando se implemente `T036`.

## Fuera de este contrato

- Endpoints de historial, listado o recuperación de sesiones.
- Autenticación, roles, RLS o auditoría.
- Exportación en modo resumen.
- Cambios en el formato del audio o en el documento exportado.

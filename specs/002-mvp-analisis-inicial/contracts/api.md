# Contrato HTTP — API de sesión única

**Base**: `http://localhost:8000` · **Formato**: JSON UTF-8 · **Autenticación**: ninguna (MVP)
**Entrada binaria**: `multipart/form-data` en la carga de audio, con el campo `file`

## Convenciones

- Todos los errores devuelven el mismo sobre:

  ```json
  { "error": { "code": "invalid_audio", "message": "El archivo no contiene audio legible", "details": {} } }
  ```

- `details` es opcional y solo transporta información no sensible.
- Las fechas son ISO-8601 con zona (`2026-11-02T14:03:11Z`).
- Los tiempos de audio son decimales en segundos desde el inicio del archivo.
- CORS: solo el origen de la interfaz (`CORS_ORIGINS`, por defecto `http://localhost:5173`).
- Límite de entrada: 120 MB (`125829120` bytes). Por encima se responde `413` antes de leer el cuerpo
  completo cuando el servidor conoce el `Content-Length`.

## Endpoints

### `GET /health`

Comprobación de vida. Debe responder incluso durante una transcripción.

- **200**: `{ "status": "ok" }`

### `GET /api/session`

Documento de la sesión actual, incluido su `status`.

- **200**: documento de sesión (ver [data-model.md](../data-model.md))
- **404**: `session_not_initialized` — solo si la inicialización falló

### `GET /api/session/audio`

Entrega el audio de la sesión vigente para reproducción y para calcular la waveform en el cliente.

- **200**: bytes del archivo, con `Content-Type` real y `Accept-Ranges: bytes`
- **404**: `no_audio` — la sesión no tiene audio
- **500**: `audio_missing` — el documento apunta a un archivo inexistente (la sesión pasa a `error`)

### `POST /api/session/audio`

Carga, valida y transcribe un audio sintético. Operación **síncrona**: la respuesta llega cuando la
transcripción termina, falla o se cancela.

**Petición**: `multipart/form-data` con `file`.

**Respuestas**

| Código | `code` | Cuándo | Sesión |
|---|---|---|---|
| 200 | — | Transcripción completada y reemplazo confirmado | Nueva, `status: ready` |
| 400 | `missing_file` | No se envió el campo `file` | Sin cambios |
| 409 | `busy` | Ya hay una carga o transcripción activa | Sin cambios |
| 409 | `cancelled` | El usuario canceló durante la operación | Anterior, intacta |
| 413 | `payload_too_large` | Supera 120 MB | Sin cambios |
| 415 | `unsupported_format` | Extensión o MIME distinto de `.mp3`/`.wav` | Sin cambios |
| 422 | `invalid_audio` | Archivo vacío, corrupto o sin audio legible | Sin cambios |
| 500 | `persistence_error` | Falló la promoción del audio o el guardado del documento | Anterior, intacta |
| 503 | `transcription_unavailable` | El motor falló tras el único reintento | Anterior, intacta |

**Respuesta 200**:

```json
{
  "session": { "version": 1, "session_id": "session-current", "status": "ready", "audio": {}, "transcription": {}, "annotations": [] },
  "cancelled": false
}
```

**Respuesta 409 (`code: cancelled`)**:

```json
{
  "error": { "code": "cancelled", "message": "La carga se canceló y se conservó la sesión anterior" },
  "session": { "status": "ready" }
}
```

**Respuesta 409 (`code: busy`)**:

```json
{ "error": { "code": "busy", "message": "Ya hay una carga en curso" } }
```

### `POST /api/session/cancel`

Solicita la cancelación cooperativa de la operación activa. El aborto ocurre como muy tarde al
terminar el segmento en curso.

- **202**: `{ "status": "processing", "cancel_requested": true }`
- **409**: `not_processing` — no hay operación activa

### `PUT /api/session/transcription`

Sustituye los segmentos editados de la transcripción vigente.

**Petición**:

```json
{ "segments": [ { "id": "segment-001", "start_time": 0.0, "end_time": 3.2, "text": "Texto corregido.", "words": [ { "text": "Texto", "start_time": 0.0, "end_time": 0.9 } ] } ] }
```

**Validación**: los segmentos deben ser contiguos en orden, no solaparse, tener `start_time <
end_time` y quedar dentro de `duration_seconds`. Cada palabra debe quedar dentro de su segmento.

- **200**: documento actualizado, `status: reviewed`
- **409**: `not_editable` — la sesión no está en `ready` o `reviewed`
- **422**: `invalid_timestamps` (rangos negativos, invertidos, solapados o fuera del audio) o
  `empty_text` (algún segmento sin texto)

### `POST /api/session/annotations`

**Petición**:

```json
{ "text": "Observación", "segment_id": "segment-001", "start_time": 0.0, "end_time": 3.2 }
```

- **201**: anotación creada, `status: reviewed`
- **409**: `not_editable`
- **422**: `empty_annotation` (texto vacío), `annotation_too_long` (más de 500 caracteres),
  `unknown_segment`, `invalid_range` (fuera del segmento referenciado)

### `PUT /api/session/annotations/{id}`

Mismo cuerpo y mismas validaciones que la creación, sobre una anotación existente.

- **200**: anotación actualizada
- **404**: `annotation_not_found`
- **409**: `not_editable`
- **422**: los mismos códigos que la creación

### `DELETE /api/session/annotations/{id}`

- **204**: anotación eliminada; el audio no se toca
- **404**: `annotation_not_found`
- **409**: `not_editable`

### `POST /api/session/export`

Persiste el documento consolidado de la sesión en la ranura única de exportación.

- **201**:

  ```json
  { "exported_at": "2026-11-02T14:03:11Z", "document": { "version": 1, "audio": {}, "transcription": {}, "annotations": [] } }
  ```

- **409**: `session_not_ready` — no hay transcripción confirmada

## Fuera de este contrato

- Sin autenticación, sin sesión de usuario, sin roles ni permisos.
- Sin endpoints de historial, listado de sesiones ni recuperación de sesiones anteriores.
- Sin subida en streaming por trozos: un archivo por petición, un máximo de una petición activa.

# Contrato del adaptador de transcripción

**Ubicación**: `backend/app/transcription/`
**Consumidores**: únicamente `backend/app/api/session.py`
**Ejecución**: dentro del contenedor `api`, sin llamadas de red externas

## Propósito

Aislar al resto de la aplicación del motor concreto. El adaptador recibe un archivo de audio local,
invoca el motor, normaliza la salida y traduce cualquier fallo a una de cuatro categorías estables.

## Interfaz

```text
transcribe(
    audio_path: Path,
    duration_seconds: float,
    language: str = "es",
    on_segment: Callable[[int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> TranscriptionResult
```

| Parámetro | Contrato |
|---|---|
| `audio_path` | Ruta absoluta a un archivo ya validado y guardado como temporal |
| `duration_seconds` | Duración real del audio, calculada por `services/audio_validation.py`; se usa para recortar los segmentos |
| `language` | Código ISO-639-1; el MVP usa siempre `es` |
| `on_segment` | Se invoca con el índice del último segmento completado; permite persistir progreso observable |
| `should_cancel` | Se consulta **entre segmentos**; si devuelve `True`, el adaptador aborta y lanza `TranscriptionCancelled` |

## Salida normalizada

```json
{
  "language": "es",
  "provider": "local",
  "retry_count": 0,
  "segments": [
    {
      "id": "segment-001",
      "start_time": 0.0,
      "end_time": 3.2,
      "text": "Ejemplo de entrevista sintética.",
      "words": [ { "text": "Ejemplo", "start_time": 0.0, "end_time": 0.8 } ]
    }
  ]
}
```

Reglas de normalización:

1. Los segmentos se ordenan por `start_time` de forma ascendente.
2. Los solapamientos se recortan al límite del segmento anterior; si el recorte deja un segmento con
   duración nula, se descarta.
3. Todo `start_time` negativo se fija en `0.0`.
4. `end_time` se limita a `duration_seconds` del audio.
5. Cada palabra hereda los límites de su segmento si el motor devuelve valores fuera de rango.
6. Los segmentos sin texto se descartan.
7. Si tras la normalización no queda ningún segmento, se lanza `TranscriptionInvalidResponse`.

## Categorías de error

| Excepción | Se produce cuando | Código HTTP en la API |
|---|---|---|
| `TranscriptionRejected` | El motor rechaza el archivo (formato no soportado, audio corrupto) | `422 invalid_audio` |
| `TranscriptionTimeout` | El motor no responde dentro del límite configurado | `503 transcription_unavailable` |
| `TranscriptionUnavailable` | El motor falla al inicializarse o se queda sin recursos | `503 transcription_unavailable` |
| `TranscriptionInvalidResponse` | La salida no se puede normalizar (vacía, sin segmentos válidos) | `503 transcription_unavailable` |
| `TranscriptionCancelled` | `should_cancel` devolvió `True` entre segmentos | `409 cancelled` |

La API nunca presenta una respuesta parcial como transcripción válida.

## Política de reintentos

- Un **único** reintento automático, solo para `TranscriptionTimeout` y `TranscriptionUnavailable`.
- Sin reintento para `TranscriptionRejected` ni `TranscriptionCancelled`.
- `retry_count` refleja el número de reintentos efectivamente realizados (`0` o `1`).
- Tras el reintento, el fallo se propaga a la API, que conserva la sesión anterior.

## Ciclo de vida del motor

- El modelo se carga **de forma perezosa** la primera vez que se necesita y se reutiliza durante toda
  la vida del proceso, protegido por un candado de inicialización.
- Los pesos se descargan durante `docker build`; en tiempo de ejecución el contenedor no tiene red.
- `fake_engine.py` implementa la misma interfaz y **nunca** carga el modelo: devuelve una transcripción
  fija y permite inyectar cada una de las cinco excepciones.

## Límites de la responsabilidad del adaptador

- No valida formato, tamaño ni MIME: eso ocurre antes, en `services/audio_validation.py`.
- No mueve archivos ni confirma sesiones: eso ocurre después, en `services/session_store.py`.
- No conoce el esquema de la base de datos ni el modelo HTTP.

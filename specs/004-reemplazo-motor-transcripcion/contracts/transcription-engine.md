# Contrato del motor de transcripción

**Ubicación**: `backend/app/transcription/`
**Consumidores**: únicamente `backend/app/api/session.py`, a través de
`adapter.transcribe()`
**Ejecución**: dentro del contenedor `api`, sin llamadas de red externas
**Contrato del adaptador**: se mantiene el de
[`specs/002-mvp-analisis-inicial/contracts/transcription-adapter.md`](../../002-mvp-analisis-inicial/contracts/transcription-adapter.md).
Este documento fija solo la configuración y el comportamiento del motor real.

## Interfaz

La interfaz no cambia:

```text
BaseEngine.run(
    audio_path: Path,
    language: str,
    on_segment: Callable[[int], None] | None,
    should_cancel: Callable[[], bool] | None,
) -> list[dict]
```

Cada elemento de la lista debe tener:

```json
{
  "start_time": 0.0,
  "end_time": 2.5,
  "text": "Texto del segmento.",
  "words": [
    { "text": "Texto", "start_time": 0.0, "end_time": 0.4 }
  ]
}
```

El adaptador añade `id`, ordena, recorta solapamientos, limita las marcas a la duración y descarta
segmentos vacíos. El motor no debe devolver `id` ni modificar el audio.

## Configuración del motor

| Parámetro | Valor | Fuente |
|---|---|---|
| Modelo | `large-v3-turbo` | `WHISPER_MODEL` (por defecto) |
| Librería | `faster-whisper==1.2.1` | `requirements.txt` |
| Idioma | `es` | `adapter.LANGUAGE` |
| `beam_size` | `5` | constante del motor |
| `word_timestamps` | `True` | constante del motor |
| `vad_filter` | `True` | `WHISPER_VAD_FILTER` (por defecto `1`) |
| `initial_prompt` | contenido del glosario | `WHISPER_GLOSSARY_PATH` |
| `local_files_only` | `True` en ejecución | `WHISPER_LOCAL_FILES_ONLY` (por defecto `1`) |
| GPU | `device="cuda"`, `compute_type="float16"` | intento inicial |
| CPU | `device="cpu"`, `compute_type="int8"` | fallback |

`WHISPER_MODEL=base` sigue siendo válido para medir la línea base durante la evaluación. No se usa en
producción.

## Ciclo de vida del modelo

1. La primera transcripción carga el modelo de forma perezosa.
2. La carga se protege con un candado y se reutiliza durante toda la vida del proceso.
3. Se intenta GPU `float16`; si la carga falla, se intenta CPU `int8`.
4. Si ambas cargas fallan, se lanza `TranscriptionUnavailable`.
5. En ejecución, `local_files_only=True` impide cualquier descarga. Si el modelo no está en
   `HF_HOME=/opt/models`, se lanza `TranscriptionUnavailable`.
6. El modelo se descarga durante `docker build`, no en la primera petición.

## Glosario

| Aspecto | Contrato |
|---|---|
| Archivo por defecto | `backend/app/transcription/glosario-whisper.txt` |
| Override | `WHISPER_GLOSSARY_PATH` |
| Codificación | UTF-8 |
| Contenido | Términos técnicos y nombres sintéticos; sin nombres de personas reales |
| Tamaño | Debe caber en la ventana de contexto de Whisper (~224 tokens) |
| Archivo ausente | Se registra una advertencia y se transcribe sin `initial_prompt`; no se falla la operación |
| Archivo vacío | Igual que ausente |
| Trazabilidad | Se registra en logs un hash corto del contenido cargado |

El glosario es una ayuda, no una lista obligatoria: el motor puede ignorar términos o introducir
nombres que no están en el audio. La evaluación debe detectar ese riesgo.

## Llamada a `transcribe`

```text
model.transcribe(
    str(audio_path),
    language="es",
    word_timestamps=True,
    vad_filter=True,
    beam_size=5,
    initial_prompt=<glosario o None>,
)
```

No se usa `language=None`: el idioma está fijo en español (`RF-002`). No se usa `task="translate"`.

## Cancelación

- Se comprueba `should_cancel` antes de cargar el modelo.
- Se comprueba de nuevo inmediatamente después de cargar.
- Se comprueba entre segmentos, como ya hace el adaptador.
- La carga de pesos de CTranslate2 no es interrumpible; la cancelación se atiende en el primer punto
  seguro.

## Errores

| Situación | Excepción | HTTP |
|---|---|---|
| Audio corrupto, formato no soportado o decodificación fallida | `TranscriptionRejected` | `422 invalid_audio` |
| VAD o detección sin voz deja la transcripción sin segmentos | `TranscriptionRejected` | `422 invalid_audio` |
| Modelo no disponible o no está en la caché local | `TranscriptionUnavailable` | `503 transcription_unavailable` |
| Falta de memoria, OOM de GPU o error de recursos | `TranscriptionUnavailable` | `503 transcription_unavailable` |
| Timeout del motor | `TranscriptionTimeout` | `503 transcription_unavailable` |
| Salida vacía o no normalizable por otras causas | `TranscriptionInvalidResponse` | `503 transcription_unavailable` |
| Cancelación entre segmentos | `TranscriptionCancelled` | `409 cancelled` |

Reglas:

- Un error de recursos **no** se etiqueta como audio inválido.
- Un audio sin voz **no** produce una transcripción vacía ni texto inventado.
- La API nunca presenta una respuesta parcial como transcripción válida.
- El adaptador conserva la política de un único reintento para `TranscriptionTimeout` y
  `TranscriptionUnavailable`.

## Variables de entorno

| Variable | Por defecto | Uso |
|---|---|---|
| `WHISPER_MODEL` | `large-v3-turbo` | Modelo; `base` solo para evaluación |
| `WHISPER_GLOSSARY_PATH` | archivo incluido | Ruta alternativa al glosario |
| `WHISPER_LOCAL_FILES_ONLY` | `1` | `1` impide descargas en ejecución; `0` solo para desarrollo/evaluación |
| `WHISPER_VAD_FILTER` | `1` | `0` desactiva el VAD solo para diagnóstico |
| `HF_HOME` | `/opt/models` | Caché de pesos en la imagen |
| `TRANSCRIPTION_ENGINE` | `local` | `fake` para pruebas deterministas |

## Observabilidad

El motor registra en logs:

- modelo y tipo de cómputo (`cuda/float16` o `cpu/int8`);
- tiempo de carga del modelo;
- duración del audio y tiempo de transcripción;
- número de segmentos y de palabras;
- hash corto del glosario;
- si se usó GPU o CPU.

No se añade ningún campo al payload de la sesión ni a la exportación.

## Fuera de contrato

- No valida formato, tamaño ni MIME; eso ocurre en `services/audio_validation.py`.
- No mueve archivos ni confirma sesiones; eso ocurre en `services/session_store.py`.
- No cambia el esquema de la base de datos.
- No expone el nombre del modelo en la API.

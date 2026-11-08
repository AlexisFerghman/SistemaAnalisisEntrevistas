# Sistema de análisis de entrevistas

Prototipo experimental para transcribir y anotar entrevistas clínicas **sintéticas**. Esta versión no
está destinada a entornos clínicos reales.

## Stack

- Frontend: React + JavaScript + Vite.
- API: FastAPI + Python 3.12.
- Persistencia: PostgreSQL 16 con `payload` `jsonb` en `current_session` y `current_export`.
- Transcripción: `faster-whisper` con el modelo `large-v3-turbo`, en CPU con `int8` y GPU con
  `float16` cuando está disponible.
- Orquestación: Docker Compose.

## Arranque

Requisitos: Docker Engine y Docker Compose.

```bash
docker compose up --build
```

Servicios:

- Interfaz y único punto de entrada HTTP: **http://localhost:5173**
- API a través del proxy de Vite: `http://localhost:5173/api/...`
- Healthcheck: `http://localhost:5173/health`
- PostgreSQL dentro de Docker: `db:5432`; desde el host, `localhost:5433`

> `api` y `db` viven en redes `internal: true`. No publiques ni uses `http://localhost:8000` desde el
> host: el frontend reenvía `/api` y `/health` a la API.

## Modelo de transcripción

El contenedor `api` descarga el modelo `large-v3-turbo` de `faster-whisper` **durante `docker build`** y
lo deja en `HF_HOME=/opt/models`. El modelo pesa aproximadamente **1,6 GB**, por lo que la imagen y el
build son más grandes que con el antiguo `base`. En ejecución no necesita red: las redes `api_db` y
`frontend_api` son internas. La primera transcripción reutiliza el modelo ya precargado; no se descarga
nada al vuelo.

Configuración por defecto:

- Idioma fijo `es`; no se detecta automáticamente.
- `word_timestamps=True` para conservar marcas por palabra y por oración.
- `vad_filter=True` para descartar silencios y reducir texto inventado.
- Glosario del dominio en `backend/app/transcription/glosario-whisper.txt`, usado como
  `initial_prompt`. El archivo está saneado: no contiene nombres de personas reales.
- GPU `float16` con fallback a CPU `int8`.

Variables de entorno:

| Variable | Por defecto | Uso |
|---|---|---|
| `WHISPER_MODEL` | `large-v3-turbo` | Modelo; `base` solo para evaluación |
| `WHISPER_GLOSSARY_PATH` | archivo incluido | Ruta alternativa al glosario |
| `WHISPER_LOCAL_FILES_ONLY` | `1` | `1` impide descargas en ejecución |
| `WHISPER_VAD_FILTER` | `1` | `0` desactiva el VAD solo para diagnóstico |
| `HF_HOME` | `/opt/models` | Caché de pesos en la imagen |

### Evaluación de calidad

El script `backend/scripts/evaluate_transcription.py` calcula WER y aciertos de glosario sobre un audio
sintético con una transcripción de referencia corregida manualmente:

```bash
docker compose exec -T api python scripts/evaluate_transcription.py \
  --audio /data/audio/eval/audioCorto.wav \
  --reference /data/audio/eval/audioCorto.reference.txt \
  --model large-v3-turbo
```

Los resultados de la validación se registran en
[`docs/validacion-004.md`](docs/validacion-004.md).

> **Estado de validación**: sobre el audio clínico `Audio-Transcript-main/audioCorto.wav` con referencia
> humana, `large-v3-turbo` reduce el WER un **44,17 %** frente a `base` (0,2648 vs 0,4744). En la escena
> dialogada `tests_audio/audio_espanol.wav`, `base` obtiene un WER ligeramente mejor; se trata de un
> dominio distinto y no invalida el resultado clínico. El modelo por defecto validado es
> `large-v3-turbo`.

## Endpoints reales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio; responde incluso durante una transcripción |
| GET | `/api/session` | Documento de la sesión en vista resumen (`words_count`, sin `words`) |
| GET | `/api/session?view=full` | Documento completo, incluidas las marcas por palabra |
| GET | `/api/session/audio` | Audio vigente; admite `Range` para reproducción |
| POST | `/api/session/audio` | Carga y transcribe un `.mp3` o `.wav` de hasta 120 MB |
| POST | `/api/session/cancel` | Cancelación cooperativa de la operación activa |
| GET | `/api/session/segments/{id}/words` | Marcas por palabra de un segmento |
| PUT | `/api/session/transcription` | Sustituye los segmentos corregidos |
| POST | `/api/session/annotations` | Crea una anotación de 1 a 500 caracteres |
| PUT | `/api/session/annotations/{id}` | Edita una anotación |
| DELETE | `/api/session/annotations/{id}` | Elimina una anotación |
| POST | `/api/session/export` | Persiste la sesión como JSON en la ranura única de exportación |

No existen `PUT /api/session` ni `DELETE /api/session`: la sesión se modifica únicamente mediante los
endpoints funcionales anteriores.

La sesión es única (`session-current`, identificada por UUID). Una carga nueva reemplaza la anterior
solo al confirmarse; los fallos y la cancelación conservan la sesión previa. La exportación se
sobrescribe en `current_export` y se elimina al confirmar una sesión nueva. El documento exportado
incluye `words` para cumplir `RF-016`.

## Límites y datos

- Audio `.mp3` o `.wav`, con MIME coherente y estructura legible.
- Tamaño máximo: **120 MB** (`125 829 120` bytes).
- Sin tope de duración, sin autenticación y sin historial de sesiones.
- Solo datos ficticios o sintéticos; la interfaz muestra una advertencia permanente y exige
  confirmación antes de analizar.

## Pruebas

```bash
docker compose exec -T api pytest
docker compose exec -T frontend npm test
```

La validación manual de los 11 escenarios de `quickstart.md` está registrada en
[`docs/validacion-mvp.md`](docs/validacion-mvp.md).

## Verificaciones locales sin Docker

```bash
python3 -m py_compile backend/app/*.py
python3 -m json.tool frontend/package.json
```

El despliegue en un servidor cloud privado queda reservado para entregas finales.

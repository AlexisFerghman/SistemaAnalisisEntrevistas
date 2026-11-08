# Implementation Plan: Reemplazo del motor de transcripción por el enfoque validado en Audio-Transcript-main

**Branch**: `004-reemplazo-motor-transcripcion` | **Date**: 2026-11-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-reemplazo-motor-transcripcion/spec.md`

## Summary

Reemplazar el motor de transcripción actual (`faster-whisper` con modelo `base`) por
`faster-whisper` con el modelo `large-v3-turbo`, cuantización `int8` en CPU y `float16` en GPU,
idioma español fijo, glosario del dominio como `initial_prompt` y filtro de actividad de voz. Se
conservan el adaptador, la API, el modelo de datos, la interfaz, la sesión única y el flujo de
edición, anotaciones y exportación.

El objetivo es mejorar la fidelidad del texto sin añadir servicios ni cambiar contratos públicos. El
modelo se descarga durante `docker build` y queda disponible sin egreso de red en ejecución. La
calidad se valida contra un conjunto de referencia con una métrica de errores por palabra y una
métrica de aciertos del glosario.

## Technical Context

**Language/Version**: Python 3.12 (backend). El frontend no se modifica.

**Primary Dependencies**: `faster-whisper==1.2.1`, `av==16.1.0`, `ctranslate2` (transitiva),
`onnxruntime` (transitiva, usada por el VAD de Silero), `huggingface_hub` (transitiva), FastAPI
0.115.6, uvicorn 0.34.0, SQLAlchemy 2.0.36, psycopg 3.2.3.

**Storage**: PostgreSQL 16-alpine con `current_session.payload` y `current_export` sin cambios; audio
en `./data/audio`; pesos del modelo en `HF_HOME=/opt/models` dentro de la imagen; glosario versionado
como archivo de texto en el backend.

**Testing**: `pytest` para unit, integración y contrato. El motor real se prueba con `WhisperModel`
simulado para no descargar pesos; la integración usa `fake_engine`. La evaluación de calidad usa un
script local con audios sintéticos y transcripciones de referencia.

**Target Platform**: Linux con Docker Engine y Docker Compose. CPU x86_64 con `int8`; GPU NVIDIA con
CUDA 12 y cuDNN 9 opcional, con `float16`.

**Project Type**: aplicación web (backend + frontend), con el cambio concentrado en el backend.

**Performance Goals**: transcribir 10 minutos de audio en ≤ 15 minutos en el equipo de referencia
(CPU, sin GPU); `GET /health` responde en < 100 ms incluso durante una transcripción; la primera
transcripción incluye la carga perezosa del modelo y las siguientes reutilizan el modelo en memoria.

**Constraints**: audio `.mp3` o `.wav` de hasta 120 MB; una sola sesión; una sola carga concurrente;
sin autenticación ni roles; solo datos sintéticos; sin egreso de red en ejecución; español fijo; una
sola instancia de uvicorn para no duplicar el modelo.

**Scale/Scope**: un usuario conceptual, una sesión, una transcripción a la vez, un motor real y un
motor falso de pruebas, sin cambios en los 10 endpoints HTTP ni en la pantalla principal.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate verificable | Resultado |
|---|---|---|
| I. Supervisión humana (NO NEGOCIABLE) | El cambio solo mejora la transcripción; no añade diagnósticos, evaluaciones ni recomendaciones clínicas. La revisión y edición profesional siguen siendo obligatorias | PASS |
| II. Datos sintéticos y privacidad | El audio sigue procesándose localmente en `api`, sin egreso en ejecución. Los pesos se descargan solo durante `docker build`. El glosario debe sanearse: no puede contener nombres de personas reales ni datos identificables | PASS condicionado (ver Nota 1) |
| III. Sesión única y eliminación | No cambia el reemplazo atómico ni la conservación de la sesión anterior ante fallo o cancelación | PASS |
| IV. Calidad y trazabilidad | El nuevo motor entrega marcas de inicio y fin por palabra y por oración; el audio original no se modifica; la anotación sigue vinculada a un segmento existente | PASS |
| V. Simplicidad del MVP | No se añade servicio, cola, worker ni pantalla. El modelo más grande aumenta imagen y build, pero mantiene un único contenedor y un único motor | PASS (ver Nota 2) |

**Nota 1**: `Audio-Transcript-main/glosario-whisper.txt` contiene nombres de personas e instituciones
reales. Antes de incorporarlo a la imagen se debe revisar y sustituir los nombres personales por
equivalentes sintéticos o eliminarlos, conservando los términos técnicos. Sin esa sanitización, el
principio II no se cumple y la implementación no debe aprobarse.

**Nota 2**: el modelo `large-v3-turbo` pesa ~1,62 GB en FP16 (frente a ~150 MB del `base`). El impacto
se limita al tamaño de la imagen y al tiempo de `docker build`; no introduce servicios ni cambia la
topología de Docker Compose.

**Nota 3**: el cambio de proveedor/modelo queda documentado en este plan, como exige la sección
"Restricciones adicionales y de despliegue" de la constitución.

**Re-evaluación tras Fase 1**: sin cambios; el modelo de datos y los contratos no introducen
violaciones. La única condición pendiente es la sanitización del glosario.

## Project Structure

### Documentation (this feature)

```text
specs/004-reemplazo-motor-transcripcion/
├── plan.md                              # Este archivo
├── research.md                          # Fase 0: decisiones y alternativas
├── data-model.md                        # Fase 1: entidades, reglas y estados
├── quickstart.md                        # Fase 1: validación de extremo a extremo
├── contracts/
│   └── transcription-engine.md          # Configuración y comportamiento del motor
├── checklists/
│   └── requirements.md
└── tasks.md                             # Fase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── transcription/
│   │   ├── adapter.py                   # Contrato interno, normalización, reintento (sin cambios de interfaz)
│   │   ├── faster_whisper_engine.py     # Motor real: large-v3-turbo, glosario, VAD, word timestamps
│   │   ├── glosario-whisper.txt         # Glosario saneado, versionado con el código
│   │   └── fake_engine.py               # Motor determinista para pruebas (sin cambios)
│   └── api/
│       └── session.py                   # Carga y cancelación (sin cambios de contrato)
├── scripts/
│   └── evaluate_transcription.py        # WER y aciertos de glosario sobre un audio de referencia
├── tests/
│   ├── unit/
│   │   └── test_faster_whisper_engine.py
│   ├── integration/                     # Usa fake_engine; sin descargas
│   └── contract/                        # Contrato HTTP sin cambios
├── Dockerfile                           # Precarga large-v3-turbo en /opt/models
└── requirements.txt                     # Sin cambios de versiones; se mantiene av==16.1.0

frontend/                                # Sin cambios
docker-compose.yml                       # Sin cambios
```

**Structure Decision**: se conserva la aplicación web existente y se modifica únicamente el motor real
dentro de `backend/app/transcription/`, su archivo de glosario, la precarga del `Dockerfile` y las
pruebas. No se crea un servicio nuevo ni se altera la topología de `docker-compose.yml`.

## Phase 0 — Research

Decisiones consolidadas en [research.md](./research.md):

1. Modelo `large-v3-turbo` de `faster-whisper` en lugar de `base`, `large-v3` u `openai-whisper`.
2. Configuración de inferencia: español fijo, `beam_size=5`, `word_timestamps=True`, `vad_filter=True`
   y glosario como `initial_prompt`.
3. Glosario versionado en el backend, con override por variable de entorno y sanitización previa.
4. Carga perezosa única por proceso, GPU `float16` con fallback a CPU `int8`, y `local_files_only` en
   ejecución para garantizar el aislamiento.
5. Distinción de errores: audio inválido o sin voz → `TranscriptionRejected`; falta de recursos o
   modelo no disponible → `TranscriptionUnavailable`; salida no normalizable →
   `TranscriptionInvalidResponse`.
6. Evaluación reproducible con WER y aciertos de glosario; el `base` sigue disponible mediante
   `WHISPER_MODEL` para medir la línea base.

## Phase 1 — Design & Contracts

- [data-model.md](./data-model.md): confirma que el modelo persistido no cambia y describe las
  entidades no persistidas (glosario y conjunto de evaluación).
- [contracts/transcription-engine.md](./contracts/transcription-engine.md): fija la configuración del
  motor, el uso del glosario, el mapeo de errores y las variables de entorno.
- [quickstart.md](./quickstart.md): escenarios ejecutables para calidad, marcas, cancelación, fallos,
  aislamiento y rendimiento.

## Implementation Outline

1. **Motor**: cambiar el valor por defecto de `WHISPER_MODEL` a `large-v3-turbo`; cargar el glosario;
   pasar `initial_prompt`, `vad_filter=True`, `word_timestamps=True`, `beam_size=5`; usar
   `local_files_only=True` en ejecución.
2. **Errores**: separar audio inválido/sin voz de falta de recursos; no presentar una transcripción
   parcial.
3. **Glosario**: copiar el glosario saneado a `backend/app/transcription/glosario-whisper.txt`,
   permitir `WHISPER_GLOSSARY_PATH` y registrar su versión/hash en logs.
4. **Imagen**: precargar `large-v3-turbo` en el `Dockerfile` con `compute_type="int8"`; mantener
   `HF_HOME=/opt/models`; documentar el aumento de tamaño y tiempo de build.
5. **Pruebas**: unitarias con `WhisperModel` simulado para verificar modelo, idioma, glosario, VAD,
   word timestamps y `local_files_only`; integración con `fake_engine`; contrato HTTP sin cambios.
6. **Evaluación**: script `backend/scripts/evaluate_transcription.py` y referencia corregida
   manualmente; medir `base` vs `large-v3-turbo` y archivar resultados en `docs/validacion-004.md`.
7. **Documentación**: actualizar `README.md` con el nuevo modelo, el glosario, el tamaño de imagen y
   el procedimiento de evaluación.

## Complexity Tracking

| Desviación | Por qué es necesaria | Alternativa simple rechazada |
|---|---|---|
| Modelo `large-v3-turbo` de ~1,62 GB en la imagen | Es la variante validada que mejora la calidad sin exigir GPU | `base` (~150 MB): calidad insuficiente; `large-v3` (~3,1 GB): más lento y pesado |
| Referencia de evaluación corregida manualmente | El WER y los aciertos de glosario necesitan una verdad humana independiente | Usar `audioCorto.txt` como referencia: sesgo circular; revisión cualitativa: no medible |
| Carga perezosa del modelo en la primera petición | Evita retrasar el arranque y el healthcheck; el modelo se reutiliza después | Precargar en memoria al arrancar: retrasa el healthcheck y complica el ciclo de vida |
| Glosario saneado antes de incorporarlo | Cumple el principio II y evita nombres de personas reales | Usar el glosario tal cual: incumple la constitución; eliminar el glosario: pierde términos técnicos |
| Distinguir OOM de audio inválido | La spec exige informar la falta de recursos como servicio no disponible | Mantener todo como `422`: mensaje engañoso para el usuario |

## Risks and Mitigations

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El modelo `large-v3-turbo` no cumple el objetivo de 15 min en CPU | Alto | Medir temprano con el audio de 9 min 27 s; si falla, evaluar `int8` con más hilos o `distil-large-v3`, sin cambiar el contrato |
| Aumento de imagen (~1,6 GB) y tiempo de build | Medio | Aceptado por la mejora de calidad; cachear la capa del modelo y documentar el requisito de disco |
| El glosario contiene nombres reales | Alto (constitución) | Sanitizar antes de incorporarlo; conservar solo términos técnicos y nombres sintéticos |
| El glosario induce nombres inventados | Medio | Evaluar con el conjunto de referencia; limitar el prompt a términos esperados; no usarlo como diccionario obligatorio |
| VAD elimina pausas o todo el audio | Medio | Usar el valor conservador por defecto (2 s); probar con silencios; mapear “sin voz” a audio inválido, no a una transcripción vacía |
| Cancelación durante la carga del modelo | Bajo | Comprobar cancelación antes y después de cargar y entre segmentos; documentar que la carga de pesos no es interrumpible |
| Primera transcripción más lenta por carga perezosa | Bajo | Aceptado; el modelo se reutiliza; medir y documentar el tiempo de la primera carga |
| Referencia de evaluación inexistente o sesgada | Medio | Crear una transcripción de referencia corregida manualmente desde el audio, sin usar la salida del nuevo motor como verdad |

## Definition of Done

- El motor real usa `large-v3-turbo`, español fijo, glosario saneado, VAD y word timestamps.
- El modelo está disponible en la imagen y no hay egreso de red en ejecución.
- Las pruebas unitarias, de integración y de contrato pasan sin descargar el modelo.
- La evaluación documenta WER y aciertos de glosario contra la línea base `base`.
- El quickstart se ejecuta de extremo a extremo y demuestra calidad, marcas, cancelación, fallos,
  aislamiento y rendimiento.
- El glosario no contiene datos personales reales.

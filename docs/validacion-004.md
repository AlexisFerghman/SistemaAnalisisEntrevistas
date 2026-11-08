# Validación — Reemplazo del motor de transcripción (004)

**Fecha**: 2026-11-08
**Feature**: `004-reemplazo-motor-transcripcion`
**Alcance**: validación automática y manual del cambio de `base` a `large-v3-turbo`.

## Entorno

- Docker Engine 29.9.3 y Docker Compose v2.39.2.
- Imagen `sistemaanalisisentrevistas-api:latest` de **2,29 GB**; caché de pesos
  `HF_HOME=/opt/models` de **1,6 GB**.
- CPU x86_64, sin GPU. El motor usó el fallback `cpu/int8`.
- Audio de rendimiento: `Audio-Transcript-main/audioCorto.wav`, 9 min 27 s, 108 MB.
- Referencia humana del audio clínico: `tests_audio/transcripcion_audioCorto.txt`, 1.465 palabras,
  sin timestamps.
- Audios sintéticos de evaluación: `fixtures/audio/entrevista-sintetica.wav` y un audio generado con
  `espeak-ng` con términos del glosario.

## Construcción y disponibilidad del modelo

```bash
docker compose build api
docker compose run --rm api python -c "
from faster_whisper import WhisperModel
WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', local_files_only=True)
print('modelo disponible')
"
```

Resultado: `modelo disponible`, sin descargas en ejecución. El build terminó correctamente y la capa
del modelo quedó en la imagen.

## Pruebas automatizadas

```bash
docker compose run --rm api pytest -q
```

Resultado: **132 passed**, 1 warning de deprecación de Starlette. Incluye las nuevas pruebas de:

- configuración del motor (`large-v3-turbo`, español, VAD, `word_timestamps`, glosario,
  `local_files_only`);
- carga de glosario y hash;
- fallback GPU → CPU;
- cancelación antes de cargar y entre segmentos;
- mapeo de OOM a `TranscriptionUnavailable` y de errores de decodificación a `TranscriptionRejected`;
- palabras y marcas válidas en la carga;
- edición sin modificar el audio original.

## Calidad sobre el fixture corto

Referencia: `fixtures/audio/entrevista-sintetica.txt`, reconstruida a partir del audio sintético. Es una
prueba de humo, no la validación principal de `SC-001`.

| Modelo | WER | Glosario esperado | Aciertos |
|---|---:|---:|---:|
| `base` | 0,051282 | 0 | 1,0 |
| `large-v3-turbo` | 0,000000 | 0 | 1,0 |

El `base` omitió las tildes en “sintetica” y “Ultimamente”; `large-v3-turbo` produjo el texto
esperado. La referencia se derivó del audio sintético, por lo que este resultado es indicativo; la
comparación principal usa la referencia humana de `audioCorto`.

## Glosario sobre audio sintético controlado

Audio generado con `espeak-ng`: “En el laboratorio usamos WindowSHAP, BiGRU y FONDECYT para el
análisis.”

| Modelo | WER | Términos esperados | Aciertos de glosario |
|---|---:|---:|---:|
| `base` | 0,454545 | 3 | 3/3 (100 %) |
| `large-v3-turbo` | 0,000000 | 3 | 3/3 (100 %) |

Términos detectados: `WindowSHAP`, `BiGRU` y `FONDECYT`. `base` reconoce los términos, pero comete
errores en el resto de la frase; `large-v3-turbo` transcribe la frase completa. El glosario saneado no
contiene nombres de personas reales ni instituciones identificables.

## Rendimiento

```bash
docker run --rm --network none \
  -v "$PWD/backend:/app" -v "$PWD/Audio-Transcript-main:/audio:ro" \
  sistemaanalisisentrevistas-api python -c "
import time
from pathlib import Path
from app.transcription.faster_whisper_engine import FasterWhisperEngine
t = time.perf_counter()
segments = FasterWhisperEngine().run(Path('/audio/audioCorto.wav'), 'es', None, None)
print(len(segments), sum(len(s['words']) for s in segments), time.perf_counter() - t)
"
```

Resultado:

- **106 segmentos**, **1.155 palabras**.
- **449,33 s** de transcripción para 9 min 27 s de audio (≈ 7,5 min).
- Proyección para 10 min: ≈ 7,9 min, por debajo del objetivo de 15 min (`SC-007`).

## Aislamiento de red

```bash
docker compose run --rm api python -c "
import socket
s = socket.socket(); s.settimeout(2)
print('EGRESO' if s.connect_ex(('1.1.1.1', 443)) == 0 else 'SIN EGRESO')
"
```

Resultado: **SIN EGRESO**. La transcripción de rendimiento se ejecutó además con `--network none`.

## Comparación principal: audio clínico `audioCorto`

**Audio**: `Audio-Transcript-main/audioCorto.wav` (9 min 27 s).
**Referencia humana**: `tests_audio/transcripcion_audioCorto.txt` (1.465 palabras, sin timestamps,
corregida a mano).

| Modelo | WER | Reducción relativa | Segmentos | Palabras |
|---|---:|---:|---:|---:|
| `base` | 0,474403 | — | 120 | 1.002 |
| `large-v3-turbo` | **0,264846** | **44,17 %** | 106 | 1.155 |

Desglose de errores:

| Modelo | Sustituciones | Borrados | Inserciones |
|---|---:|---:|---:|
| `base` | 206 | 476 | 13 |
| `large-v3-turbo` | 64 | 317 | 7 |

`large-v3-turbo` reduce el WER un **44,17 % en términos relativos** frente a `base` sobre el audio
clínico, superando el umbral del 20 % de `SC-001`. También produce menos sustituciones, menos borrados
y un texto más completo (1.155 palabras frente a 1.002). El resultado se mantiene al ignorar las tildes
(`base` 46,76 % vs `large-v3-turbo` 26,01 %). Esta es la comparación principal por corresponder al
dominio objetivo. En el conjunto formal de evaluación (`audioCorto`, fixture corto y glosario
controlado), `large-v3-turbo` mejora en todos los audios; `tests_audio` es un contraste externo de otro
dominio. Las salidas completas están en `tests_audio/eval-base-audioCorto.json` y
`tests_audio/eval-turbo-audioCorto.json`.

## Comparación secundaria: escena dialogada (`tests_audio`)

**Audio**: `tests_audio/audio_espanol.wav` (7 min 12 s).
**Referencia**: `tests_audio/transcripcion.txt` (1.117 palabras, sin timestamps, corregida a mano).

| Modelo | WER | Reducción relativa | Segmentos | Palabras |
|---|---:|---:|---:|---:|
| `base` | 0,142346 | — | 48 | 1.089 |
| `large-v3-turbo` | 0,177261 | **-24,53 %** (empeora) | 133 | 1.084 |

Desglose de errores:

| Modelo | Sustituciones | Borrados | Inserciones |
|---|---:|---:|---:|
| `base` | 92 | 47 | 20 |
| `large-v3-turbo` | 131 | 49 | 18 |

La referencia contiene erratas y transliteraciones que `large-v3-turbo` corrige, pero que el WER
penaliza como sustituciones. Ejemplos: `cafi` → `Caffey`, `dani` → `Danny`, `retira` → `retire`,
`sientes, ¿eh?` → `siéntese`, `decería` → `agradecería`, `juezo` → `juez`, `budo` → `vuelo`,
`Andreus` → `Andrews`, `anteçal` → `antesala`, `El pie` → `¡En pie!`, `bion` → `avión`,
`Ros` → `Ross`.

Para separar ese efecto, se corrigieron esas erratas obvias en una copia de la referencia
(`tests_audio/transcripcion.corregida.txt`):

| Modelo | WER con referencia corregida | Reducción relativa |
|---|---:|---:|
| `base` | 0,143627 | — |
| `large-v3-turbo` | 0,152603 | **-6,25 %** (empeora) |

**Conclusión de esta comparación**: en esta escena dialogada, `base` obtiene un WER ligeramente mejor.
El audio tiene solapamientos y no representa el dominio clínico; se conserva como contraste y no
invalida el resultado principal sobre `audioCorto`.

## Escenarios manuales de `quickstart.md`

Ejecutados con `docker compose up -d` y el proxy en `http://localhost:5173`:

| Escenario | Resultado |
|---|---|
| 1. Sesión inicial vacía | `empty`, sin audio, 0 anotaciones |
| 2. Carga válida | `200`, `ready`, `language: es`, `provider: local`, 3 segmentos, primer segmento con 13 palabras |
| 3. Extensión falsa | `422 invalid_audio`; sesión previa intacta |
| 4. Formato no admitido | `415 unsupported_format`; el tamaño excedido devolvió `502` a través del proxy de Vite, mientras la prueba directa de la API cubre `413` |
| 5. Carga simultánea | `409 busy`; la sesión previa quedó `ready` |
| 6. Healthcheck durante la transcripción | 3 respuestas `200` en ~6–9 ms |
| 7. Cancelación | `202`; carga `409 cancelled`; sesión previa intacta; sin temporales |
| 8. Edición y marcas | Marca fuera de rango `422 invalid_timestamps`; edición válida `200 reviewed` |
| 9. Anotaciones 500/501 | `201` para 500 caracteres; `422 annotation_too_long` para 501 |
| 10. Exportación | `201` con `document` y `exported_at`; sin campo `model` |
| 11. Aislamiento | `SIN EGRESO` |

## Estado de los criterios

| Criterio | Estado | Evidencia |
|---|---|---|
| `SC-001` WER ≥20 % mejor | **PASS** | `audioCorto` con referencia humana: `base` 0,4744 vs `large-v3-turbo` 0,2648 (reducción relativa 44,17 %); mejora también en fixture corto y glosario controlado |
| `SC-002` ≥90 % glosario | **PASS (muestra controlada)** | 3/3 términos en audio sintético con `WindowSHAP`, `BiGRU` y `FONDECYT` |
| `SC-003` marcas por palabra/oración | PASS | Pruebas unitarias e integración; 1.155 palabras en `audioCorto` |
| `SC-004` todas las cargas usan el nuevo motor | PASS | `WHISPER_MODEL=large-v3-turbo` por defecto y pruebas de configuración |
| `SC-005` fallos/cancelación conservan sesión | PASS | Pruebas de integración existentes y nuevas |
| `SC-006` sin egreso de red | PASS | `SIN EGRESO` y ejecución con `--network none` |
| `SC-007` 10 min < 15 min | PASS | 449 s para 9 min 27 s |
| `SC-008` flujos existentes sin cambios | PASS | 132 pruebas de backend; frontend sin cambios |

## Pendientes

Sin pendientes bloqueantes. `large-v3-turbo` queda validado sobre el audio clínico `audioCorto` con
una reducción de WER del 44,17 %. La escena dialogada de `tests_audio` se conserva como contraste de
dominio; en ese audio `base` sigue siendo ligeramente mejor.

## Notas

- El glosario se redujo a términos técnicos y nombres sintéticos; se eliminaron los nombres de
  personas y la referencia institucional del archivo original.
- No se modificaron la API, el esquema de base de datos, la exportación ni el frontend.
- El audio original de la sesión no se modifica durante la edición ni la transcripción.

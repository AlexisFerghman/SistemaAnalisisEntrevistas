# Quickstart de validación — Reemplazo del motor de transcripción

**Propósito**: comprobar de extremo a extremo que el nuevo motor mejora la calidad sin romper el flujo
existente.
**Plan**: [plan.md](./plan.md) · **Contrato**: [contracts/transcription-engine.md](./contracts/transcription-engine.md) ·
**Modelo de datos**: [data-model.md](./data-model.md)

## Requisitos previos

- Docker Engine y Docker Compose.
- `curl`, `jq`, `ffmpeg` y `ffprobe` en la máquina anfitriona.
- Un audio **sintético** en español. Para la prueba de rendimiento se usa
  `Audio-Transcript-main/audioCorto.wav` (9 min 27 s, 108 MB), que ya está dentro del límite de 120 MB.
- La transcripción de referencia humana `tests_audio/transcripcion_audioCorto.txt` (sin timestamps,
  corregida a mano). No uses `Audio-Transcript-main/audioCorto.txt` como verdad: es la salida del motor
  nuevo. Cópiala en `data/audio/eval/audioCorto.reference.txt` para el contenedor.
- Nunca uses una grabación real: el MVP solo admite datos sintéticos.

> Todos los comandos de API usan `http://localhost:5173`, el proxy de Vite. `api` y `db` viven en
> redes `internal: true`; no publiques el puerto 8000.

## 1. Construir y arrancar

```bash
docker compose build api
docker compose up -d
curl -s http://localhost:5173/health | jq .
```

**Esperado**: `{"status":"ok"}`. El build descarga ~1,6 GB de pesos y puede tardar varios minutos.

Verifica que el modelo quedó en la caché de la imagen y que no requiere red:

```bash
docker compose run --rm api python -c "
from faster_whisper import WhisperModel
WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', local_files_only=True)
print('modelo disponible')
"
```

**Esperado**: `modelo disponible`, sin descargas.

## 2. Verificar el glosario saneado

```bash
test -s backend/app/transcription/glosario-whisper.txt && echo "glosario presente"
grep -Ei "César|Javiera|Ignacio|Felipe|Matías|Bastián|Daniel|Raúl|Hernán|Alexis|Bruno|Nicolás|Sergio|Rodrigo|Francisco|Hospital de Curicó" \
  backend/app/transcription/glosario-whisper.txt || echo "sin nombres reales"
```

**Esperado**: `glosario presente` y `sin nombres reales`. Si aparece algún nombre, la implementación no
debe aprobarse: la constitución prohíbe incorporar datos personales reales.

## 3. Carga corta y marcas por palabra

```bash
time curl -s -X POST http://localhost:5173/api/session/audio \
  -F "file=@fixtures/audio/entrevista-sintetica.wav;type=audio/wav" \
  | jq '{status: .session.status, cancelled, language: .session.transcription.language, provider: .session.transcription.provider, segments: (.session.transcription.segments | length)}'

curl -s http://localhost:5173/api/session \
  | jq '.transcription.segments[0] | {start_time, end_time, text, words: (.words | length)}'
```

**Esperado**: `status: "ready"`, `cancelled: false`, `language: "es"`, `provider: "local"`, al menos
un segmento, `start_time < end_time` y `words > 0`.

## 4. Audio sin voz

```bash
ffmpeg -y -f lavfi -i anullsrc=r=16000:cl=mono -t 5 -q:a 9 -acodec pcm_s16le /tmp/silencio.wav
curl -s -o /tmp/silencio.json -w '%{http_code}\n' \
  -X POST http://localhost:5173/api/session/audio \
  -F "file=@/tmp/silencio.wav;type=audio/wav"
jq -r '.error.code // .session.status' /tmp/silencio.json
curl -s http://localhost:5173/api/session | jq '{status, segments: (.transcription.segments | length)}'
```

**Esperado**: `422` con `invalid_audio`; la sesión anterior sigue en `ready` con sus segmentos. No debe
aparecer texto inventado ni una transcripción vacía presentada como válida.

## 5. Cancelación con audio largo

```bash
curl -s -X POST http://localhost:5173/api/session/audio \
  -F "file=@Audio-Transcript-main/audioCorto.wav;type=audio/wav" > /tmp/carga.json &
sleep 3
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:5173/api/session/cancel
wait
jq -r '.error.code // .session.status' /tmp/carga.json
curl -s http://localhost:5173/api/session | jq '{status, annotations: (.annotations | length)}'
```

**Esperado**: `202` al cancelar; la carga responde `409` con `cancelled`; la sesión previa sigue en
`ready` y sin temporales en `data/audio`.

## 6. Aislamiento de red

```bash
docker compose exec -T api python -c "
import socket
try:
    socket.create_connection(('1.1.1.1', 443), 2)
    print('EGRESO')
except OSError:
    print('SIN EGRESO')
"
```

**Esperado**: `SIN EGRESO`. La transcripción no debe depender de red en ejecución.

## 7. Rendimiento con audio de ~10 minutos

```bash
time curl -s -X POST http://localhost:5173/api/session/audio \
  -F "file=@Audio-Transcript-main/audioCorto.wav;type=audio/wav" \
  > /tmp/largo.json
jq '{status: .session.status, segments: (.session.transcription.segments | length)}' /tmp/largo.json
```

**Esperado**: `status: "ready"` en menos de 15 minutos en el equipo de referencia (CPU, sin GPU).
Registra el tiempo real y el hardware. Si supera el objetivo, revisa hilos de CPU, `int8` y el uso de
GPU antes de aceptar el cambio.

## 8. Evaluación de calidad contra la línea base

Prepara el audio y la referencia en el volumen montado:

```bash
mkdir -p data/audio/eval
cp Audio-Transcript-main/audioCorto.wav data/audio/eval/audioCorto.wav
cp tests_audio/transcripcion_audioCorto.txt data/audio/eval/audioCorto.reference.txt

docker compose exec -T api python scripts/evaluate_transcription.py \
  --audio /data/audio/eval/audioCorto.wav \
  --reference /data/audio/eval/audioCorto.reference.txt \
  --model base

docker compose exec -T api python scripts/evaluate_transcription.py \
  --audio /data/audio/eval/audioCorto.wav \
  --reference /data/audio/eval/audioCorto.reference.txt \
  --model large-v3-turbo
```

**Esperado**:

- `large-v3-turbo` reduce el WER al menos un 20 % en términos relativos frente a `base` sobre el audio
  clínico (resultado validado: 44,17 %).
- Ningún audio del conjunto formal empeora.
- Al menos el 90 % de los términos del glosario aparece correctamente escrito.

Como contraste de dominio, se puede repetir con `tests_audio/audio_espanol.wav` y
`tests_audio/transcripcion.txt`; en esa escena dialogada `base` obtiene un WER ligeramente mejor, pero
no representa el caso de uso clínico.

Archiva los resultados en `docs/validacion-004.md` con el hardware, la fecha y los comandos usados.

## 9. Pruebas automatizadas

```bash
docker compose exec -T api pytest -q
docker compose exec -T frontend npm test
```

**Esperado**: todas las pruebas en verde. Las pruebas del backend no descargan el modelo: usan
`WhisperModel` simulado o `fake_engine`.

## 10. Verificación de que no cambió el contrato

```bash
curl -s http://localhost:5173/api/session | jq 'keys'
curl -s http://localhost:5173/api/session | jq '.transcription | keys'
```

**Esperado**: las mismas claves que antes del cambio. No debe aparecer el nombre del modelo en el
payload ni en la exportación.

## Criterio de aceptación global

El cambio se acepta cuando:

1. Todas las pruebas existentes pasan.
2. La carga corta produce marcas por palabra y por oración.
3. El audio sin voz se rechaza sin inventar texto.
4. La cancelación conserva la sesión anterior.
5. No hay egreso de red en ejecución.
6. La evaluación documenta la mejora de WER y de aciertos de glosario.
7. El glosario no contiene nombres reales.

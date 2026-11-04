# Quickstart de validación — MVP de análisis inicial

**Propósito**: comprobar de extremo a extremo que la funcionalidad cumple la especificación, sin leer
código de implementación.
**Plan**: [plan.md](./plan.md) · **Contratos**: [contracts/api.md](./contracts/api.md) ·
**Modelo**: [data-model.md](./data-model.md)

## Requisitos previos

- Docker Engine y Docker Compose.
- `curl` y `jq` en la máquina anfitriona.
- Un audio **sintético** en español, `.wav` o `.mp3`, de 30 a 90 segundos, en
  `fixtures/audio/entrevista-sintetica.wav`. Si aún no existe, sigue las instrucciones de
  [`fixtures/audio/README.md`](../../fixtures/audio/README.md); en resumen:

  ```bash
  mkdir -p fixtures/audio
  command -v espeak-ng && espeak-ng -v es -s 140 -w /tmp/voz.wav \
    "Esta es una entrevista sintetica de prueba. No contiene datos reales."
  command -v ffmpeg && ffmpeg -y -i /tmp/voz.wav -ar 16000 -ac 1 fixtures/audio/entrevista-sintetica.wav
  ```

  Nunca uses una grabación real.

## Arranque

```bash
docker compose up --build
curl -s http://localhost:8000/health | jq .
```

**Esperado**: `{"status":"ok"}` y el frontend disponible en `http://localhost:5173`.

---

## Escenario 1 — Sesión inicial vacía

```bash
curl -s http://localhost:8000/api/session | jq '{status, has_audio: (.audio != null), annotations}'
```

**Esperado**: `status: "empty"`, `has_audio: false`, `annotations: []`.

## Escenario 2 — Carga válida con transcripción sincronizada

```bash
time curl -s -X POST http://localhost:8000/api/session/audio \
  -F "file=@fixtures/audio/entrevista-sintetica.wav" | jq '{status: .session.status, cancelled, segments: (.session.transcription.segments | length)}'
```

**Esperado**: `200`, `status: "ready"`, `cancelled: false`, al menos un segmento. Además:

```bash
curl -s http://localhost:8000/api/session | jq '.transcription.segments[0] | {start_time, end_time, text, words: (.words | length)}'
```

**Esperado**: `start_time < end_time`, texto no vacío y al menos una palabra con sus propias marcas.
Registra el tiempo total: el objetivo es ≤ 15 minutos para 10 minutos de audio.

## Escenario 3 — Archivo con extensión falsa

```bash
printf 'esto no es audio' > /tmp/falso.wav
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/session/audio -F "file=@/tmp/falso.wav"
curl -s http://localhost:8000/api/session | jq '.status'
```

**Esperado**: `422` con `code: invalid_audio`; la sesión sigue en `ready` y conserva la transcripción del
escenario 2.

## Escenario 4 — Formato no admitido y tamaño excedido

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/session/audio -F "file=@README.md;filename=notas.txt"
dd if=/dev/zero of=/tmp/grande.wav bs=1M count=130 2>/dev/null
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/session/audio -F "file=@/tmp/grande.wav"
```

**Esperado**: `415 unsupported_format` y `413 payload_too_large`. En ambos casos la sesión no cambia.

## Escenario 5 — Carga simultánea rechazada

En una terminal:

```bash
curl -s -X POST http://localhost:8000/api/session/audio -F "file=@fixtures/audio/entrevista-sintetica.wav" > /tmp/primera.json &
sleep 2
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/session/audio -F "file=@fixtures/audio/entrevista-sintetica.wav"
```

**Esperado**: la segunda petición responde `409` con `code: busy`. Al terminar la primera, la sesión
tiene exactamente un audio y una transcripción, sin archivos temporales en `./data/audio`.

## Escenario 6 — El healthcheck sobrevive a la transcripción

Con una carga en curso (escenario 5), en otra terminal:

```bash
for i in 1 2 3; do curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' http://localhost:8000/health; sleep 1; done
docker compose ps api
```

**Esperado**: tres respuestas `200` con tiempos bajos, y `api` en estado `healthy`. Si el event loop se
bloqueara, `api` aparecería como `unhealthy` y el frontend no arrancaría.

## Escenario 7 — Cancelación conserva la sesión anterior

```bash
curl -s -X POST http://localhost:8000/api/session/audio -F "file=@fixtures/audio/entrevista-sintetica.wav" > /tmp/carga.json &
sleep 2
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/session/cancel
wait
jq -r '.error.code // .session.status' /tmp/carga.json
curl -s http://localhost:8000/api/session | jq '{status, annotations: (.annotations | length)}'
```

**Esperado**: `202` al cancelar; la carga responde `409` con `code: cancelled`; la sesión previa sigue
en `ready` con sus anotaciones intactas y sin temporales en `./data/audio`.

## Escenario 8 — Edición y validación de marcas de tiempo

```bash
curl -s http://localhost:8000/api/session | jq '.transcription' > /tmp/transcripcion.json
jq '.segments[0].start_time = 999999' /tmp/transcripcion.json > /tmp/invalida.json
jq '{segments}' /tmp/invalida.json > /tmp/cuerpo.json
curl -s -o /dev/null -w '%{http_code}\n' -X PUT http://localhost:8000/api/session/transcription \
  -H 'Content-Type: application/json' -d @/tmp/cuerpo.json
```

**Esperado**: `422` con `code: invalid_timestamps`. Con un valor válido dentro de la duración, la
respuesta es `200` y `status: "reviewed"`, y el audio original no cambia de tamaño ni de contenido.

## Escenario 9 — Anotaciones: 500 caracteres sí, 501 no

```bash
SEG=$(curl -s http://localhost:8000/api/session | jq -r '.transcription.segments[0].id')
TEXTO500=$(python3 -c "print('a'*500)")
TEXTO501=$(python3 -c "print('a'*501)")
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/session/annotations \
  -H 'Content-Type: application/json' \
  -d "{\"text\":\"$TEXTO500\",\"segment_id\":\"$SEG\",\"start_time\":0,\"end_time\":1}"
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/session/annotations \
  -H 'Content-Type: application/json' \
  -d "{\"text\":\"$TEXTO501\",\"segment_id\":\"$SEG\",\"start_time\":0,\"end_time\":1}"
```

**Esperado**: `201` y luego `422` con `code: annotation_too_long`. La sesión queda con una sola
anotación.

## Escenario 10 — Exportación y reemplazo de sesión

```bash
curl -s -X POST http://localhost:8000/api/session/export | jq '{exported_at, claves: (.document | keys)}'
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/session/audio \
  -F "file=@fixtures/audio/entrevista-sintetica.wav"
curl -s http://localhost:8000/api/session | jq '{annotations: (.annotations | length), status}'
ls -1 data/audio
```

**Esperado**: la exportación devuelve `exported_at` y un documento con audio, transcripción y
anotaciones; la nueva carga responde `200`; la sesión queda con `annotations: []` y un único archivo
`current.*` en `data/audio` (más ningún temporal). La exportación anterior ya no existe.

## Escenario 11 — Aislamiento de red

```bash
docker compose exec api python -c "import socket; socket.setdefaulttimeout(3); socket.create_connection(('1.1.1.1', 443))" && echo "SALIDA ABIERTA" || echo "SIN EGRESO"
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/session
```

**Esperado**: `SIN EGRESO` y `200`. Confirma que el audio nunca sale del host y que el modelo tuvo que
precargarse en la imagen.

---

## Criterio de aceptación global

El flujo `cargar → transcribir → editar → anotar → exportar` se completa con audio sintético, los
errores no destruyen la sesión anterior y el reemplazo deja una única sesión. Cualquier fallo en un
escenario bloquea la fase de tareas hasta corregirlo.

## Limpieza

```bash
docker compose down
rm -f data/audio/current.* data/audio/*.tmp /tmp/falso.wav /tmp/grande.wav
```

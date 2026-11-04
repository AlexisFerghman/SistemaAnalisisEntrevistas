# Fixtures de audio

Audio **sintético** usado por los escenarios de `specs/002-mvp-analisis-inicial/quickstart.md`.

> No se versiona audio binario en este repositorio. Genera el archivo localmente con el comando de
> abajo; `fixtures/audio/*` está ignorado salvo `.gitkeep`.

## Requisito

El archivo esperado es `fixtures/audio/entrevista-sintetica.wav`.

## Generación

```bash
mkdir -p fixtures/audio

# Voz sintética en español (espeak-ng)
espeak-ng -v es -s 140 -w /tmp/voz.wav \
  "Esta es una entrevista sintetica de prueba. No contiene datos reales."

# Normalizar a 16 kHz mono, formato que el MVP admite
ffmpeg -y -i /tmp/voz.wav -ar 16000 -ac 1 fixtures/audio/entrevista-sintetica.wav
```

Si no tienes `espeak-ng`, sirve cualquier grabación propia de voz sintética o TTS. **Nunca uses una
grabación real**: el MVP solo admite datos ficticios o sintéticos (constitución, principio II).

## Verificación

```bash
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 \
  fixtures/audio/entrevista-sintetica.wav
```

Duración esperada: entre 2 y 8 segundos para el texto de ejemplo; el límite del MVP es de 120 MB.

# Research — Reemplazo del motor de transcripción

**Fase**: 0 (Outline & Research)
**Fecha**: 2026-11-07
**Plan**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md)

## Contexto

La comparación realizada por el usuario sobre `Audio-Transcript-main/audioCorto.wav` (9 min 27 s,
108 MB) produjo una transcripción más fiel que la del motor vigente (`faster-whisper` con modelo
`base`). La salida con formato `[hh:mm:ss] texto` corresponde a
`Audio-Transcript-main/transcribir_local.py`, que usa `faster-whisper` con `large-v3-turbo`,
`int8`, español fijo, glosario y VAD.

La spec deja la variante como decisión del plan y registra la recomendación. Este documento fija esa
decisión y resuelve los detalles técnicos necesarios para implementar y validar.

## D01. Modelo `large-v3-turbo` en lugar de `base`

**Decisión**: usar el modelo `large-v3-turbo` de Whisper, ejecutado con `faster-whisper`.

**Razón**: es la variante que produjo la mejora observada, con un coste de cómputo compatible con CPU.
`large-v3-turbo` tiene ~809 M parámetros frente a ~74 M de `base`; conserva el encoder de `large-v3` y
reduce el decoder a 4 capas, por lo que mejora sustancialmente la calidad sin el coste de `large-v3`
completo. El nombre `large-v3-turbo` está soportado por `faster-whisper==1.2.1` y el modelo CTranslate2
pesa ~1,62 GB en FP16.

**Alternativas consideradas**:

- `base` (actual): rápido y liviano, pero con demasiados errores para el objetivo de calidad.
- `large-v3` (~3,1 GB): más preciso, pero más lento y pesado; incumple el objetivo de 15 minutos en CPU
  con mayor probabilidad.
- `openai-whisper` con `large-v3`: requiere PyTorch y FFmpeg, es más lento en CPU y no integra VAD;
  además, el script `transcrip.py` no entrega marcas por palabra.
- `distil-large-v3`: más rápido, pero con menor calidad en español y sin la validación previa del
  usuario.

## D02. Mantener `faster-whisper` como motor

**Decisión**: conservar `faster-whisper==1.2.1` y cambiar solo el modelo y la configuración de
inferencia.

**Razón**: el adaptador, el manejo de errores, la cancelación entre segmentos y las pruebas ya existen.
`faster-whisper` es una reimplementación de Whisper con CTranslate2, hasta 4 veces más rápida que
`openai-whisper` con precisión similar, y no requiere FFmpeg ni PyTorch en el sistema. Mantener la
librería reduce el riesgo de integración y no altera el contrato interno.

**Alternativas consideradas**: migrar a `openai-whisper` (más dependencias y lento en CPU);
`whisper.cpp` (requiere compilación y otro adaptador).

## D03. Configuración de inferencia

**Decisión**: `language="es"`, `beam_size=5`, `word_timestamps=True`, `vad_filter=True`,
`initial_prompt=<glosario>`, `condition_on_previous_text=True` (valor por defecto).

**Razón**: replica la configuración que produjo la mejora, conserva las marcas por palabra que exige
la constitución y mantiene la calidad de decodificación. El VAD por defecto de `faster-whisper` es
conservador: elimina silencios mayores de 2 s y añade 400 ms de padding; es adecuado para entrevistas
con pausas naturales.

**Alternativas consideradas**: `beam_size=1` (más rápido, peor calidad); `vad_filter=False` (riesgo de
texto inventado en silencios); `vad_parameters={"min_silence_duration_ms": 500}` (más agresivo, puede
cortar pausas de la entrevista).

## D04. Glosario como `initial_prompt`

**Decisión**: incorporar el glosario saneado como `initial_prompt` en cada transcripción.

**Razón**: Whisper usa el prompt como contexto para nombres propios y términos técnicos. El archivo de
referencia tiene ~100 palabras, dentro de la ventana de ~224 tokens que Whisper usa como contexto. Es
una ayuda, no un diccionario obligatorio: el modelo puede ignorarla o introducir términos que no están
en el audio.

**Alternativas consideradas**: no usar glosario (peor reconocimiento de términos); postprocesar el
texto con reemplazos (puede introducir errores y no mejora la decodificación); fine-tuning (fuera de
alcance).

## D05. VAD para evitar texto inventado

**Decisión**: activar `vad_filter=True` con los valores conservadores por defecto y verificar que las
marcas de tiempo sigan referidas al audio completo.

**Razón**: el VAD de Silero descarta tramos sin habla y reduce alucinaciones en silencios. En
`faster-whisper`, los segmentos se mapean de vuelta a la línea temporal original. Si el VAD elimina
todo el audio, el motor debe informar “sin voz” como audio inválido, no devolver una transcripción
vacía ni inventada.

**Alternativas consideradas**: VAD agresivo de 500 ms (riesgo de cortar pausas); sin VAD (más
alucinaciones); VAD externo (dependencia y complejidad innecesarias).

## D06. Marcas por palabra y por oración

**Decisión**: mantener `word_timestamps=True` y la normalización existente del adaptador.

**Razón**: la constitución exige marcas de inicio y fin por palabra y por oración. El adaptador ya
ordena, recorta solapamientos, limita las marcas a la duración y descarta segmentos vacíos. El nuevo
motor no cambia el formato de salida normalizado.

**Alternativas consideradas**: confiar solo en marcas por segmento (incumple el principio IV);
alineación forzada externa (fuera de alcance).

## D07. Carga del modelo y aislamiento

**Decisión**: cargar el modelo de forma perezosa una vez por proceso, con `local_files_only=True` en
ejecución. En `docker build`, descargar `large-v3-turbo` con `compute_type="int8"` en
`HF_HOME=/opt/models`.

**Razón**: el contenedor `api` no tiene egreso de red en ejecución. La precarga durante el build
garantiza que el modelo esté disponible y que ninguna transcripción descargue pesos. La carga perezosa
evita retrasar el arranque y el healthcheck; el modelo se reutiliza en todas las peticiones.

**Alternativas consideradas**: descargar en la primera petición (imposible sin red); abrir egreso
temporal (rompe el aislamiento); precargar el modelo en memoria al arrancar (retrasa el healthcheck y
complica el ciclo de vida).

## D08. GPU con fallback a CPU

**Decisión**: intentar GPU con `compute_type="float16"`; si falla la carga, usar CPU con `int8`.

**Razón**: mantiene el comportamiento actual y aprovecha hardware disponible sin exigir GPU. El modelo
`large-v3-turbo` en `float16` ocupa ~1,62 GB de pesos, por lo que cabe en GPUs de 4 GB o más; en CPU
`int8` el consumo es menor.

**Alternativas consideradas**: exigir GPU (inviable en el equipo de desarrollo); fijar CPU (desperdicia
hardware); degradar silenciosamente a un modelo menor (rompe la promesa de calidad).

## D09. Taxonomía de errores

**Decisión**: mantener las cinco categorías existentes y precisar su uso:

| Situación | Categoría | HTTP |
|---|---|---|
| Audio corrupto, formato no soportado o sin voz | `TranscriptionRejected` | `422 invalid_audio` |
| Modelo no disponible, OOM o error de inicialización | `TranscriptionUnavailable` | `503 transcription_unavailable` |
| Salida vacía o no normalizable | `TranscriptionInvalidResponse` | `503 transcription_unavailable` |
| Timeout | `TranscriptionTimeout` | `503 transcription_unavailable` |
| Cancelación entre segmentos | `TranscriptionCancelled` | `409 cancelled` |

**Razón**: hoy el motor convierte cualquier excepción de `transcribe()` en `TranscriptionRejected`
(422), lo que etiqueta un OOM como audio inválido. La spec exige informar la falta de recursos como
servicio no disponible. La distinción mejora el mensaje al usuario y conserva el contrato HTTP.

**Alternativas consideradas**: añadir una categoría nueva (cambia el contrato); mantener todo como 422
(mensaje engañoso); reintentar OOM (puede empeorar la presión de memoria).

## D10. Cancelación

**Decisión**: comprobar `should_cancel` antes de cargar el modelo, después de cargarlo y entre
segmentos, como ya hace el adaptador.

**Razón**: la carga de pesos de CTranslate2 no es interrumpible; el punto seguro más temprano es
inmediatamente después de la carga. La cancelación durante la transcripción sigue funcionando entre
segmentos, que es el comportamiento observable actual.

**Alternativas consideradas**: cargar el modelo en un hilo cancelable (no es posible abortar
`WhisperModel`); precargar al arrancar (elimina la ventana, pero retrasa el healthcheck).

## D11. Evaluación de calidad

**Decisión**: crear `backend/scripts/evaluate_transcription.py` para calcular:

- **WER** (word error rate) tras normalizar mayúsculas, puntuación y espacios.
- **Aciertos de glosario**: proporción de términos del glosario que aparecen correctamente escritos
  en la transcripción, comparados con la referencia.

El script acepta un audio, una transcripción de referencia y un modelo (`WHISPER_MODEL`), de modo que
la misma medición se puede ejecutar con `base` y con `large-v3-turbo`.

**Razón**: la spec exige una reducción relativa de al menos 20 % en WER y 90 % de aciertos de
glosario. Sin una métrica reproducible, la mejora queda como impresión subjetiva.

**Alternativas consideradas**: revisión cualitativa (no medible); usar la salida del nuevo motor como
referencia (sesgo circular); confiar solo en la comparación manual del usuario (no reproducible).

## D12. Transcripción de referencia

**Decisión**: usar referencias corregidas manualmente, sin usar la salida del nuevo motor como verdad.
Para el fixture corto existe un texto conocido en `fixtures/audio/entrevista-sintetica.txt`; para el
audio clínico `audioCorto.wav` la referencia humana es `tests_audio/transcripcion_audioCorto.txt`.
Como contraste de dominio se usa `tests_audio/audio_espanol.wav` con
`tests_audio/transcripcion.txt`.

**Razón**: el WER necesita una verdad humana. `Audio-Transcript-main/audioCorto.txt` es la salida del
motor nuevo, no una referencia independiente. La referencia debe revisarse escuchando el audio. La
comparación principal es el audio clínico; la escena dialogada de `tests_audio` es un contraste y no
invalida el resultado del dominio objetivo.

**Alternativas consideradas**: usar `audioCorto.txt` como referencia (circular); no medir WER (no
cumple SC-001); usar solo el fixture corto (poco representativo).

## D13. Pruebas sin descargar el modelo

**Decisión**: simular `WhisperModel` en pruebas unitarias y usar `fake_engine` en integración.

**Razón**: el entorno de pruebas no debe descargar 1,6 GB ni depender de GPU. Las pruebas unitarias
verifican la configuración que se pasa al motor (modelo, idioma, prompt, VAD, word timestamps,
`local_files_only`); las de integración verifican el flujo HTTP y la conservación de sesión con el
motor falso.

**Alternativas consideradas**: descargar el modelo en CI (lento y frágil); mockear todo el adaptador
(no verifica la configuración real).

## D14. Impacto en imagen y build

**Decisión**: aceptar el aumento de ~1,6 GB y el tiempo de descarga durante `docker build`.

**Razón**: el modelo debe estar disponible sin red en ejecución. La capa de descarga se cachea mientras
no cambien las dependencias. El contenedor sigue siendo único y no se añaden servicios.

**Alternativas consideradas**: montar los pesos como volumen (traslada el problema al operador); abrir
egreso en ejecución (rompe el aislamiento); usar un modelo menor (pierde calidad).

## D15. Privacidad del glosario

**Decisión**: sanear el glosario antes de incorporarlo: eliminar o sustituir nombres de personas
reales y referencias institucionales identificables, conservando términos técnicos y nombres
sintéticos.

**Razón**: el glosario de referencia contiene nombres de personas reales. Aunque no son datos de
pacientes, la constitución prohíbe incorporar nombres reales al prototipo. La sanitización evita una
violación del principio II y no impide usar el glosario como contexto técnico.

**Alternativas consideradas**: usar el glosario tal cual (riesgo de incumplimiento); eliminar el
glosario (pierde la mejora en términos técnicos); usar solo términos técnicos (opción adoptada).

## D16. Sin cambios en API, datos ni interfaz

**Decisión**: mantener el contrato HTTP, el documento JSONB, los estados de sesión y la interfaz sin
cambios.

**Razón**: el reemplazo es interno al adaptador. El campo `provider` sigue siendo `local`; el modelo
concreto se registra en logs, no en el payload, para no alterar el contrato ni la exportación.

**Alternativas consideradas**: exponer el nombre del modelo en la API (cambio de contrato y de
exportación); añadir una pantalla de configuración (fuera de alcance).

## D17. Observabilidad

**Decisión**: registrar en logs el modelo, el tipo de cómputo, el tiempo de carga, la duración del
audio, el tiempo de transcripción, el número de segmentos y si se usó GPU o CPU.

**Razón**: permite diagnosticar lentitud, OOM y diferencias de calidad sin añadir métricas ni
endpoints nuevos.

**Alternativas consideradas**: endpoint de métricas (fuera de alcance); no registrar nada (dificulta
la validación de rendimiento).

## D18. Riesgo de alucinación con glosario

**Decisión**: mantener el glosario, pero evaluar su efecto con la referencia; si aumenta las
alucinaciones, reducirlo a términos técnicos o desactivarlo.

**Razón**: un `initial_prompt` largo o con nombres puede inducir al modelo a escribir nombres que no
se dijeron. La evaluación con referencia y el VAD permiten detectarlo.

**Alternativas consideradas**: confiar ciegamente en el glosario (riesgo de texto inventado); no
medirlo (no se detecta la regresión).

## Resumen de decisiones

| ID | Decisión |
|---|---|
| D01 | `large-v3-turbo` en lugar de `base` |
| D02 | Mantener `faster-whisper==1.2.1` |
| D03 | Español fijo, beam 5, word timestamps, VAD, glosario |
| D04 | Glosario como `initial_prompt` |
| D05 | VAD conservador por defecto |
| D06 | Conservar marcas por palabra y oración |
| D07 | Carga perezosa y `local_files_only` en ejecución |
| D08 | GPU `float16` con fallback a CPU `int8` |
| D09 | Precisar la taxonomía de errores |
| D10 | Cancelación antes/después de cargar y entre segmentos |
| D11 | Script de WER y aciertos de glosario |
| D12 | Referencia corregida manualmente |
| D13 | Pruebas con `WhisperModel` simulado y `fake_engine` |
| D14 | Aceptar +1,6 GB de imagen |
| D15 | Sanitizar el glosario |
| D16 | Sin cambios de API, datos ni interfaz |
| D17 | Logs de modelo, tiempos y dispositivo |
| D18 | Evaluar el riesgo de alucinación del glosario |

## Referencias consultadas

- `faster-whisper` v1.2.1: README, `utils.py`, `transcribe.py` y `vad.py` del repositorio oficial.
- Modelo `faster-whisper-large-v3-turbo` en Hugging Face: ~1,62 GB en FP16, licencia MIT.
- Documentación de Whisper sobre `word_timestamps`, `initial_prompt` y VAD.
- `Audio-Transcript-main/README.md`, `transcribir_local.py` y `glosario-whisper.txt`.
- Constitución del proyecto y validación previa del MVP (`docs/validacion-mvp.md`).

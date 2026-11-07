# Investigación técnica y decisiones — MVP de análisis inicial

**Fase**: 0 (Outline & Research)
**Fecha**: 2026-11-02
**Plan**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md)

No quedan `NEEDS CLARIFICATION` en el contexto técnico. Este documento consolida las decisiones del
plan anterior (`spec/01-analisis-inicial-general/plan.md`), normaliza las referencias obsoletas a un
proveedor en la nube y añade las decisiones derivadas del diseño B-lite.

---

## D01. Transcripción real en vez de una respuesta simulada

**Decisión**: el MVP procesa una grabación sintética real con `faster-whisper`. El motor falso queda
reservado para pruebas deterministas y escenarios de error.

**Razón**: una respuesta simulada no valida el objetivo del prototipo, que es comprobar si la
transcripción automática es utilizable en una entrevista clínica sintética.

**Alternativas consideradas**: transcripción simulada con texto fijo (descartada: no demuestra el
flujo real); servicio externo en la nube (descartada: rompe el aislamiento y el principio II).

## D02. Modelo `base` en vez de `tiny` o `small`

**Decisión**: modelo `base` con `int8` en CPU.

**Razón**: equilibrio entre calidad y consumo para desarrollo. `tiny` produce transcripciones
demasiado pobres para evaluar la edición; `small` multiplica el coste de CPU y memoria sin mejorar
de forma decisiva la demo.

**Alternativas consideradas**: `tiny` (calidad insuficiente); `small` (tiempo de transcripción y RAM
excesivos para un prototipo de un solo equipo).

## D03. GPU con fallback a CPU en vez de exigir GPU

**Decisión**: usar GPU cuando esté disponible y CPU como respaldo, con `compute_type="int8"` en CPU.

**Razón**: el prototipo debe arrancar en cualquier equipo de desarrollo sin bloquear la demostración.

**Alternativas consideradas**: exigir GPU (inviable en el entorno de trabajo); fijar CPU (desperdicia
hardware donde sí hay GPU).

## D04. Validación completa en vez de validar solo la extensión

**Decisión**: comprobar extensión, tipo MIME declarado y estructura real del audio.

**Razón**: un archivo renombrado o corrupto debe rechazarse antes de consumir tiempo de transcripción.

**Alternativas consideradas**: confiar en la extensión (trivial de burlar); confiar en el MIME del
cliente (declarado, no verificado).

## D05. Confirmación por carga y banner permanente en vez de un aviso único

**Decisión**: banner permanente en la interfaz y confirmación explícita antes de enviar cada archivo.

**Razón**: refuerza la restricción de datos sintéticos sin prometer detección automática de datos
personales, que está fuera del MVP (`RF-003`).

**Alternativas consideradas**: aviso único al iniciar la aplicación (se ignora con facilidad);
detección automática de datos personales (fuera de alcance y poco fiable).

## D06. Solo límite de tamaño (120 MB) en vez de límite de duración

**Decisión**: un único tope numérico de 120 MB. La duración se lee del archivo y se usa para validar
coherencia interna, pero no se impone un máximo de minutos.

**Razón**: la duración efectiva depende de códec, bitrate, canales y frecuencia de muestreo; un tope
fijo rechazaría audios válidos y obligaría a re-transcodificar.

**Alternativas consideradas**: tope de duración fijo (rechaza grabaciones legítimas); tope combinado
de tamaño y duración (más reglas sin beneficio claro).

**Nota de trazabilidad**: `RF-001`/`RF-002` y el caso límite "archivo que supera el límite de tamaño
o duración" siguen mencionando la duración. La diferencia queda registrada en *Complexity Tracking*
de `plan.md` y debe alinearse con un PATCH de la spec o en `/speckit.clarify`.

## D07. Conservar la sesión ante validación fallida en vez de cambiarla a `error`

**Decisión**: un archivo inválido se rechaza sin tocar la sesión confirmada.

**Razón**: la validación ocurre antes del procesamiento y no debe degradar una sesión utilizable.

**Alternativas consideradas**: marcar `error` (destruye un resultado válido por un intento fallido).

## D08. Confirmar antes de limpiar el audio anterior

**Decisión**: la nueva sesión se activa cuando su audio y su documento son legibles; solo después se
elimina el audio anterior.

**Razón**: si la limpieza falla, la sesión nueva ya es válida y el residuo se puede borrar luego.

**Alternativas consideradas**: borrar primero (un fallo deja el sistema sin sesión, viola el
principio III).

## D09. Rechazar cargas simultáneas en vez de encolarlas o mezclarlas

**Decisión**: si ya hay una operación activa, el segundo `POST` responde `409` con código `busy`.

**Razón**: una única operación de reemplazo activa evita carreras entre archivos temporales y
resultados de transcripción, y evita dos transcripciones compitiendo por la misma CPU.

**Alternativas consideradas**: encolar (requiere cola y worker); mezclar (corrompe temporales).

## D10. Transcripción en la misma petición (B-lite) en vez de `202` + polling

**Decisión**: `POST /api/session/audio` es un endpoint síncrono (`def`, ejecutado en el threadpool de
FastAPI) que devuelve la sesión lista, el error o la cancelación. El documento se marca `processing`
antes de empezar y se revierte si algo falla.

**Razón**: el polling exige un contrato adicional, reconciliación de trabajos huérfanos tras un
reinicio y coordinación con el reemplazo atómico; para un usuario, una sesión y una pantalla no
aporta valor proporcional. El estado persistido ya permite que la interfaz muestre "procesando" si la
página se recarga.

**Alternativas consideradas**: `202` + polling con tareas en segundo plano (más piezas, pensado para
trabajos largos y múltiples clientes); Celery/Redis (dos servicios extra por un único flujo).

## D11. Endpoint síncrono declarado como `def`, no `async def`

**Decisión**: la ruta de carga se declara síncrona y la llamada a `faster-whisper` se ejecuta en el
threadpool de FastAPI.

**Razón**: una llamada bloqueante dentro de `async def` congela el event loop, deja de responder
`/health` y provoca que el healthcheck de Docker marque `api` como `unhealthy`, impidiendo el arranque
del frontend por `depends_on: service_healthy`. `ctranslate2` libera el GIL durante la inferencia, por
lo que el hilo no ahoga al resto de la API.

**Alternativas consideradas**: `asyncio.to_thread` dentro de `async def` (equivalente, algo más
explícito pero más verboso); worker separado (contradice D10).

## D12. Cancelación cooperativa en vez de aborto forzado

**Decisión**: `POST /api/session/cancel` marca `cancel_requested` en el documento; el bucle de
segmentos lo consulta y aborta entre segmentos. El `POST` de carga en curso responde `409` con código
`cancelled`.

**Razón**: no existe forma segura de matar un hilo de inferencia en Python. Comprobar entre segmentos
es suficiente: el peor caso es esperar al segmento actual.

**Alternativas consideradas**: matar el proceso (tumba la sesión y el servidor); ignorar la
cancelación (el usuario cierra la pestaña y la CPU sigue trabajando).

## D13. Estado de operación persistido en el documento de sesión

**Decisión**: `status` recorre `empty`, `validating`, `processing`, `ready`, `reviewed`, `error` y se
persiste junto con el resto del documento.

**Razón**: permite ver el estado tras una recarga y da a `RF-006` un valor observable; no añade
infraestructura porque la sesión ya es un documento JSON.

**Alternativas consideradas**: estado solo en memoria (se pierde en cada recarga y con `--reload`).

## D14. Aplicación modular única en vez de microservicios

**Decisión**: un backend modular y un frontend, sin dividir el MVP en servicios.

**Razón**: solo hay un flujo, un usuario conceptual y una sesión; la separación lógica por módulos
permite extraer servicios más adelante.

**Alternativas consideradas**: microservicios (coste operativo desproporcionado).

## D15. Adaptador de transcripción en vez de acoplar la interfaz al motor

**Decisión**: `transcription/adapter.py` define entrada, normalización y categorías de error; el
motor real y el falso son intercambiables.

**Razón**: permite probar escenarios de error sin GPU ni modelo, y cambiar de motor sin tocar la API.

**Alternativas consideradas**: llamar a `faster-whisper` desde los endpoints (acopla y complica las
pruebas).

## D16. Formato interno normalizado en vez de conservar la respuesta del motor

**Decisión**: la salida se normaliza a un documento propio con `language`, `provider`, `retry_count`,
segmentos ordenados y palabras con marcas de tiempo.

**Razón**: el editor, el reproductor y el exportador no deben depender del formato de `faster-whisper`.

**Alternativas consideradas**: usar el JSON del motor directamente (acopla el modelo de datos a una
dependencia y complica la exportación).

## D17. Reemplazo atómico de una sesión en vez de borrar primero

**Decisión**: flujo de siete pasos con temporales: validar sin tocar la sesión, transcribir, escribir
temporales, verificar legibilidad, promover audio y documento, limpiar el audio anterior, y revertir
todo ante cualquier fallo o cancelación.

**Razón**: cumple `RF-013`, `RF-014` y `RF-015` sin ventanas en las que el sistema quede sin sesión.

**Alternativas consideradas**: borrar al iniciar la carga (un fallo deja al usuario sin nada).

## D18. PostgreSQL para la sesión única en vez de un archivo JSON como persistencia principal

**Decisión**: tabla `current_session` con una fila fija (`current`) y columna `payload JSON`.

**Razón**: forma parte del stack solicitado, valida el acceso real de la API a una base de datos y
permite persistir la exportación con el mismo mecanismo.

**Alternativas consideradas**: archivo JSON en disco (sin transacciones ni validación de esquema);
historial de sesiones (excluido por el principio III).

## D19. Anotaciones vinculadas a segmentos en vez de posiciones de texto

**Decisión**: la anotación referencia un `segment_id` existente y un rango temporal válido dentro de
ese segmento; el texto va de 1 a 500 caracteres.

**Razón**: los índices de caracteres dejan de ser válidos en cuanto se edita el texto.

**Alternativas consideradas**: índices de caracteres (se desplazan con cada edición).

## D20. Motor propio de pruebas y precarga del modelo en la imagen

**Decisión**: el contenedor `api` descarga los pesos de `faster-whisper` durante `docker build`; las
pruebas deterministas usan `fake_engine.py` y nunca cargan el modelo.

**Razón**: el contenedor no tiene egreso a red (redes `internal: true`), así que no puede descargar
pesos en tiempo de ejecución. La precarga es la única forma de cumplir el aislamiento del principio II.

**Alternativas consideradas**: descargar al primer arranque (imposible sin egreso); abrir egreso
temporal (rompe el aislamiento y la promesa de privacidad); montar los pesos como volumen (traslada el
problema al operador).

**Coste asumido**: ~150 MB adicionales en la imagen y un `build` más lento.

## D21. Modelo cargado una vez por proceso

**Decisión**: el motor real instancia el modelo de forma perezosa y lo reutiliza durante toda la vida
del proceso, protegido por un candado de inicialización.

**Razón**: cargar ~150 MB de pesos en cada petición haría insostenible el flujo.

**Alternativas consideradas**: recargar por petición (lento); cargar al importar el módulo (rompe las
pruebas que no necesitan el modelo).

## D22. Un solo worker de uvicorn

**Decisión**: se ejecuta un único proceso de uvicorn; el candado de concurrencia y el estado de
operación viven en él.

**Razón**: con varios workers se duplicaría el modelo en memoria y el candado dejaría de ser efectivo.

**Alternativas consideradas**: varios workers con bloqueo en base de datos (innecesario para un
usuario y una sesión).

## D23. Normalización de las referencias obsoletas a "cloud"

**Decisión**: donde el plan anterior decía "error cloud", "fallo cloud" o "proveedor falso para no
depender siempre de la nube", ahora dice "fallo del servicio de transcripción" y "motor falso para
pruebas deterministas".

**Razón**: el MVP transcribe en local; conservar el vocabulario de nube describe una arquitectura que
ya no existe y confunde la lectura de `RF-006`.

**Alternativas consideradas**: conservarlo literal (fidelidad al documento antiguo a costa de
contradecir la spec y el compose actual).

## D24. Exportación en una sola ranura, borrada al confirmar una nueva sesión

**Decisión**: la exportación se guarda en una fila fija (`current_export`) que se sobrescribe en cada
exportación y se elimina cuando se confirma una nueva sesión.

**Razón**: mantener exportaciones anteriores reintroduce un historial de sesiones, que el principio III
y `RF-016` excluyen. La copia descargada por el usuario sigue siendo el mecanismo de conservación.

**Alternativas consideradas**: conservar la exportación indefinidamente (historial encubierto); una
tabla por exportación (mismo problema con más estructura).

## D25. `av` fijado en 16.1.0 por compatibilidad con faster-whisper 1.2.1

**Decisión**: `av==16.1.0` y `python-multipart` como dependencias explícitas.

**Razón**: `faster-whisper 1.2.1` llama a `av.open(..., metadata_errors="ignore")`, pero PyAV 17
eliminó ese parámetro; con `av 19` la transcripción fallaba con
`TypeError: open() got an unexpected keyword argument 'metadata_errors'`. La serie 15–16 lo conserva y
publica ruedas `cp312` para Linux. `python-multipart` es obligatorio para recibir `multipart/form-data`.

**Alternativas consideradas**: `av 14.4.0` (solo código fuente: exigía compilar FFmpeg en la imagen);
monkeypatchear `av.open` para descartar el argumento (frágil ante otros cambios de API).

## D26. La API se consume a través del proxy del frontend

**Decisión**: todas las llamadas del navegador y de las pruebas manuales usan `http://localhost:5173`;
Vite reenvía `/api` y `/health` a `http://api:8000`.

**Razón**: `api` y `db` están solo en redes `internal: true`, y Docker no publica puertos de
contenedores que no tienen una red externa. El frontend sí está en `external_conectividad`, así que es
el único punto de entrada y mantiene el aislamiento del contenedor de la API (principio II).

**Alternativas consideradas**: publicar `8000` (requiere dar al contenedor `api` una red con salida a
internet, rompiendo el aislamiento); usar `docker compose exec` para cada prueba (incómodo).

## D27. Sin escritura directa del documento de sesión

**Decisión**: eliminar `PUT /api/session` y `DELETE /api/session`. La sesión solo cambia mediante los
endpoints funcionales: carga de audio, edición de transcripción, anotaciones y exportación.

**Razón**: una escritura genérica permite saltarse las validaciones de timestamps, anotaciones y
reemplazo atómico, y contradice el contrato HTTP. `GET /api/session` sigue siendo la única lectura
directa.

**Alternativas consideradas**: mantener las rutas para pruebas o herramientas internas (abre una vía de
mutación no validada); restringirlas por entorno (complejidad innecesaria para un MVP de un usuario).
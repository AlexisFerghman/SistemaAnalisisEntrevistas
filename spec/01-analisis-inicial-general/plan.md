# Plan técnico — MVP de análisis inicial

## Alcance técnico

El MVP se implementará como una aplicación modular sencilla, sin microservicios,
autenticación ni gestión multiusuario. El servidor mantendrá una única sesión y
utilizará un adaptador para comunicarse con un servicio local de transcripción
aislado en Docker. El despliegue en un servidor cloud privado queda reservado
para entregas finales. PostgreSQL queda definido como almacenamiento técnico de
la única sesión, sin ampliar el alcance funcional.

No se implementarán análisis afectivo, XAI, chatbot, pacientes, roles ni
historial de sesiones.

## Estructura de módulos

- **Carga y validación de audio:** recibe el archivo, valida extensión, tipo,
	tamaño y duración, y muestra la advertencia de uso exclusivo con datos
	sintéticos. Cubre RF-001, RF-002 y RF-003.
- **Adaptador de transcripción local:** encapsula la ejecución de
	`faster-whisper` en el servicio aislado de Docker, normaliza su respuesta al
	formato interno y traduce sus errores a estados comprensibles para la
	aplicación. Cubre RF-004, RF-005 y RF-006.
- **Sesión única:** crea, consulta, actualiza y elimina la única sesión
	persistida. Usa una operación de reemplazo temporal para conservar la sesión
	anterior hasta que la nueva se haya procesado y guardado correctamente. Cubre
	RF-012, RF-013, RF-014 y RF-015.
- **Reproductor y visor sincronizado:** reproduce el audio, permite pausar,
	cambiar velocidad, saltar a un timestamp y resaltar el segmento activo. Cubre
	RF-007.
- **Editor de transcripción:** permite editar el texto y sus marcas de tiempo,
	validando que sigan vinculadas al audio. Cubre RF-008.
- **Anotaciones:** crea, valida, actualiza y elimina anotaciones vinculadas a un
	fragmento o timestamp. Cubre RF-009, RF-010 y RF-011.
- **Exportación:** transforma la sesión actual al documento JSON definido y lo
	persiste en PostgreSQL con audio o metadatos, transcripción, timestamps y
	anotaciones. Cubre RF-016.
- **Interfaz de estados y errores:** comunica validaciones, advertencias,
	progreso, cancelación, errores cloud y conservación de la sesión anterior.
	Cubre RF-002, RF-003, RF-006, RF-014 y RF-015.

## Modelo de datos

La sesión se almacenará como un único documento lógico. El audio puede
persistirse como archivo asociado y el documento conservará su ruta o referencia
interna; no se guardarán identidades de pacientes ni datos clínicos reales.

```json
{
	"version": 1,
	"session_id": "session-current",
	"status": "empty",
	"audio": {
		"filename": "entrevista-sintetica.wav",
		"mime_type": "audio/wav",
		"size_bytes": 123456,
		"duration_seconds": 180.5,
		"storage_ref": "current-audio.wav"
	},
	"transcription": {
		"language": "es",
		"provider": "local",
		"retry_count": 0,
		"segments": [
			{
				"id": "segment-001",
				"start_time": 0.0,
				"end_time": 3.2,
				"text": "Ejemplo de entrevista sintética.",
				"words": [
					{"text": "Ejemplo", "start_time": 0.0, "end_time": 0.8}
				]
			}
		]
	},
	"annotations": [
		{
			"id": "annotation-001",
			"text": "Observación de prueba",
			"segment_id": "segment-001",
			"start_time": 0.0,
			"end_time": 3.2 
		}
	]
}
```

La sesión vacía inicial se representa así:

```json
{
	"version": 1,
	"session_id": "session-current",
	"status": "empty",
	"audio": null,
	"transcription": null,
	"annotations": []
}
```

Reglas del modelo:

- `version` permite evolucionar el formato sin mezclar estructuras.
- `session_id` siempre vale `session-current`; identifica la sesión actual, no a
	una persona ni una carga histórica.
- `status` usa `empty`, `validating`, `processing`, `ready`, `reviewed` o
	`error`. Los estados de operación pueden ser transitorios; un fallo al
	reemplazar una sesión no cambia el estado persistido de la sesión anterior.
- La sesión inicial siempre existe con `status: empty`, `audio: null`,
	`transcription: null` y `annotations: []`.
- El audio se almacena en la carpeta del host `./data/audio`, montada en la API
	como `/data/audio`; `storage_ref` contiene una ruta relativa, nunca una ruta
	absoluta del host.
- La API crea `session-current` al arrancar si todavía no existe.
- Si `storage_ref` apunta a un archivo inexistente, la API marca la sesión como
	`error` y conserva el JSON para diagnóstico; no la reemplaza silenciosamente
	por una sesión vacía.
- Los tiempos se expresan en segundos desde el inicio del audio.
- `start_time` debe ser menor que `end_time`; los segmentos deben estar ordenados,
	no solaparse y quedar dentro de la duración del audio.
- Cada segmento debe conservar su texto y sus timestamps. Cada palabra debe
	conservar `text`, `start_time` y `end_time`.
- Una anotación debe referenciar un segmento existente y no superar 500
	caracteres.
- No se conserva una colección de sesiones anteriores.

## Persistencia y reemplazo de sesión

La persistencia se organizará en PostgreSQL con un documento de sesión y una
referencia relativa al archivo de audio actual en `/data/audio`. Durante la
carga, el archivo se escribe como temporal; tras confirmar la transcripción se
renombra a `current.<ext>`.

El flujo de reemplazo será:

1. Validar el nuevo audio sin modificar la sesión actual.
2. Enviar el audio al servicio local y recibir una respuesta válida.
3. Guardar el audio como temporal y normalizar la nueva sesión en una ubicación
	temporal.
4. Confirmar que el documento y el audio pueden leerse correctamente.
5. Promover el audio temporal a `current.<ext>` y persistir el nuevo JSON en
	PostgreSQL; la nueva sesión se considera confirmada solo cuando ambos pasos
	terminan correctamente.
6. Después de confirmar, eliminar el audio anterior. Si esta limpieza falla, la
	nueva sesión permanece activa y el archivo anterior queda pendiente de
	limpieza.
7. Si cualquier paso anterior falla o se cancela, eliminar los temporales,
	restaurar la referencia anterior si fuese necesario y conservar la sesión
	anterior.

## Decisiones técnicas

- **Transcripción real en vez de una respuesta simulada:** el MVP procesa una
	grabación sintética real con `faster-whisper`; el proveedor falso queda
	reservado para pruebas deterministas y escenarios de error.
- **Modelo `base` en vez de `tiny` o `small`:** se elige un equilibrio entre
	calidad y consumo para desarrollo. Se descarta `tiny` por su menor calidad y
	`small` por su mayor coste de CPU y memoria en el MVP.
- **GPU con fallback a CPU en vez de exigir GPU:** se permite aprovechar GPU
	cuando exista sin bloquear equipos de desarrollo que solo tengan CPU.
- **Validación completa en vez de validar solo la extensión:** se comprueban
	extensión, MIME y estructura real del audio para evitar archivos renombrados o
	corruptos. Se descarta aceptar un archivo únicamente por su nombre.
- **Confirmación por carga y banner permanente en vez de un aviso único:** se
	refuerza que solo se permiten datos sintéticos sin pretender detectar datos
	personales automáticamente.
- **Solo límite de tamaño en vez de límite de duración:** se elige un máximo de
	120 MB porque la duración depende del códec, bitrate, canales y frecuencia de
	muestreo. Se descarta fijar una duración que pueda rechazar audios válidos.
- **Conservar la sesión ante validación fallida en vez de cambiarla a `error`:**
	la validación ocurre antes del procesamiento y no debe alterar una sesión
	confirmada.
- **Confirmar antes de limpiar el audio anterior:** la nueva sesión se activa
	cuando sus propios datos están completos; un fallo al borrar el audio antiguo
	no invalida la sesión nueva.
- **Rechazar cargas simultáneas en vez de encolarlas o mezclarlas:** una única
	operación de reemplazo activa evita carreras entre archivos temporales y
	resultados de transcripción.
- **Cancelar y limpiar temporales en vez de guardar resultados parciales:** una
	cancelación durante la transcripción conserva la sesión anterior.
- **Aplicación modular única en vez de microservicios:** se descarta dividir el
	MVP en servicios independientes porque solo hay un flujo, un usuario
	conceptual y una sesión. La separación lógica de módulos permitirá extraer
	servicios más adelante si fuese necesario.
- **Adaptador de transcripción local en vez de integrar el servicio directamente
	en la interfaz:** se descarta acoplar la interfaz a una API concreta para
	poder cambiar de servicio y probar mediante un servicio falso.
- **Formato interno normalizado en vez de conservar la respuesta propietaria del
	proveedor:** se descarta usar el JSON externo directamente para que el editor,
	reproductor y exportador no dependan del proveedor elegido.
- **Reemplazo atómico de una sesión en vez de borrar primero:** se descarta
	eliminar la sesión anterior al comenzar la carga porque un fallo cloud podría
	dejar el sistema sin sesión disponible. Cubre RF-013, RF-014 y RF-015.
- **PostgreSQL para la sesión única en vez de un archivo JSON como persistencia
	principal:** se elige PostgreSQL porque forma parte del stack solicitado y
	permite validar el acceso de la API a una base de datos real. Se descarta
	implementar historial, tablas de usuarios o consultas multiusuario; la base
	solo contiene la sesión actual.
- **Anotaciones vinculadas a segmentos y timestamps en vez de posiciones de
	texto solamente:** se descarta depender únicamente de índices de caracteres
	porque las ediciones pueden cambiar la longitud del texto. Cubre RF-009,
	RF-010 y RF-011.
- **Proveedor falso para desarrollo en vez de depender siempre de la nube:** se
	descarta hacer que todas las pruebas llamen al proveedor real para evitar
	costes, latencia, secretos y dependencia de red.

## Contratos internos

- **Entrada de audio:** archivo `.mp3` o `.wav`, de hasta 120 MB, sin límite
	independiente de duración y solo datos sintéticos. La validación comprueba
	extensión, MIME y estructura real del audio.
- **Advertencia de datos:** la interfaz muestra un banner permanente y exige una
	confirmación explícita antes de enviar cada archivo al servicio local. No se
	intenta detectar automáticamente información personal.
- **Respuesta normalizada de transcripción:** `language: "es"`, proveedor,
	`retry_count`, segmentos ordenados sin solapamientos, timestamps válidos,
	texto y palabras con timestamps obligatorios.
- **Error del servicio local:** categoría estable para timeout, rechazo,
	respuesta inválida o fallo inesperado, con un único reintento automático;
	nunca se presenta una respuesta parcial como transcripción válida.
- **Error de validación:** se informa el motivo, no se inicia el procesamiento,
	se conserva la sesión actual y se permite seleccionar otro archivo.
- **Motor de transcripción:** `faster-whisper` con el modelo `base`, idioma
	`es` y `word_timestamps=True`. Se usa GPU cuando está disponible y CPU como
	fallback, con `compute_type="int8"` en CPU.
- **Anotación:** texto de 1 a 500 caracteres, referencia a segmento existente y
	rango temporal válido.
- **Exportación:** documento JSON persistido en PostgreSQL que contiene la
	sesión actual, sin datos de sesiones reemplazadas.

## Estrategia de tests

- **Validación de audio:** unit tests para formato admitido, archivo vacío,
	archivo corrupto, tamaño excedido, duración excedida y audio sin contenido
	reconocible. Cubre RF-001 y RF-002.
- **Advertencia de datos:** tests de interfaz o integración que comprueben que
	la advertencia de datos sintéticos aparece antes del envío. La detección
	completa de datos personales no se probará como funcionalidad automática,
	porque está fuera del MVP. Cubre RF-003 y RNF-001.
- **Adaptador local:** unit tests con un servicio falso para respuesta válida en
	español, timestamps por palabra, timeout con un reintento, error definitivo,
	respuesta incompleta, segmentos solapados y timestamps inválidos. Cubre RF-004,
	RF-005 y RF-006.
- **Reproductor y sincronización:** tests de integración para reproducción,
	pausa, velocidades permitidas, salto temporal y selección del segmento activo.
	Cubre RF-007.
- **Editor:** unit tests para modificar texto, modificar timestamps y rechazar
	rangos negativos, invertidos o incompatibles con la duración. Cubre RF-008.
- **Anotaciones:** unit tests para crear, editar y eliminar anotaciones, vínculo
	a segmentos, texto vacío, 500 caracteres exactos y 501 caracteres. Cubre
	RF-009, RF-010 y RF-011.
- **Sesión única:** tests de integración con almacenamiento temporal para carga
	inicial, reemplazo correcto, fallo cloud, cancelación y fallo de persistencia.
	Deben comprobar que no se mezclan sesiones y que la sesión anterior sobrevive
	a cualquier fallo previo a la confirmación. Cubre RF-012, RF-013, RF-014 y
	RF-015.
- **Exportación:** tests de contrato que verifiquen el documento JSON persistido
	en PostgreSQL con audio o metadatos, transcripción corregida, timestamps y
	anotaciones, incluyendo sesiones sin anotaciones y con texto parcialmente
	editado. Cubre RF-016.
- **Prueba de aceptación:** recorrido completo con un audio sintético fijo:
	cargar, transcribir mediante `faster-whisper`, editar, anotar, reemplazar la
	sesión y persistir el JSON. Los escenarios de error se ejecutan con el
	proveedor falso y no requieren una llamada cloud.

## Matriz de cobertura

| Parte del plan | Requisitos cubiertos |
|---|---|
| Carga y validación | RF-001, RF-002, RF-003 |
| Adaptador local | RF-004, RF-005, RF-006 |
| Reproductor y visor | RF-007 |
| Editor | RF-008 |
| Anotaciones | RF-009, RF-010, RF-011 |
| Sesión única y persistencia | RF-012, RF-013, RF-014, RF-015 |
| Exportación | RF-016 |
| Advertencias y restricciones | RNF-001 a RNF-005 |

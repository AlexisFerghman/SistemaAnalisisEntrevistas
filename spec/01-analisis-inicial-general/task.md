- [x] **T1 — Cerrar decisiones abiertas del MVP** (20 min)
	- RF/RNF: RF-001, RF-004, RF-016, RNF-001, RNF-004.
	- Decisiones: servicios locales aislados en Docker para el MVP; despliegue en
		servidor cloud privado reservado para entregas finales; formatos `.mp3` y
		`.wav`; límite provisional de 120 MB; exportación como JSON en PostgreSQL.
	- **Hecho cuando:** las decisiones de proveedor, formatos, límite y
		exportación están documentadas y aprobadas, sin añadir funcionalidades fuera
		del MVP.

- [x] **T2 — Definir el contrato de la sesión única** (25 min)
	- RF/RNF: RF-012, RNF-003.
	- Decisiones: `session_id` fijo en `session-current`; estados `empty`,
		`validating`, `processing`, `ready`, `reviewed` y `error`; audio como archivo
		en volumen Docker; sesión vacía persistida desde el inicio; los fallos de una
		nueva carga se devuelven como error sin modificar la sesión anterior.
	- **Hecho cuando:** el plan contiene ejemplos de sesión vacía y completa,
		campos obligatorios, estados e invariantes de reemplazo seguro.

- [x] **T3 — Definir el contrato normalizado de transcripción** (25 min)
	- RF/RNF: RF-004, RF-005, RNF-004.
	- Decisiones: idioma `es` en el MVP; timestamps obligatorios por palabra y
		segmento; segmentos ordenados, dentro de la duración y sin solapamientos; un
		reintento automático; errores normalizados sin aceptar respuestas parciales.
	- **Hecho cuando:** el plan describe una respuesta válida, una respuesta
		inválida, las reglas de segmentos y el comportamiento del reintento.

- [x] **T4 — Diseñar la validación y advertencia de audio sintético** (20 min)
	- RF/RNF: RF-001, RF-002, RF-003, RNF-001.
	- Decisiones: validar extensión, MIME y estructura real; aceptar `.mp3` y
		`.wav` hasta 120 MB sin límite independiente de duración; mostrar banner
		permanente y exigir confirmación antes de cada envío; conservar la sesión ante
		un rechazo.
	- **Hecho cuando:** el plan documenta los estados de validación, mensajes de
		rechazo, confirmación y preservación de la sesión actual.

- [x] **T5 — Preparar transcripción real y escenarios de error** (25 min)
	- RF: RF-004, RF-005, RF-006.
	- Decisiones: grabación sintética real; `faster-whisper` con modelo `base`,
		idioma `es`, `word_timestamps=True`, GPU si está disponible y CPU como
		fallback. El proveedor falso se mantiene solo para pruebas deterministas.
	- **Hecho cuando:** el plan define el motor real, su configuración de
		ejecución, la respuesta normalizada y los escenarios de error cubiertos por
		pruebas reales y dobles de prueba.

- [x] **T6 — Definir la persistencia temporal de la sesión** (25 min)
	- RF: RF-012.
	- Decisiones: audio en `./data/audio` montado como `/data/audio`; archivo
		temporal antes de confirmarlo como `current.<ext>`; `session-current` se crea
		al arrancar; si falta el archivo referenciado, la sesión pasa a `error` y se
		conserva el JSON para diagnóstico.
	- **Hecho cuando:** el plan define el documento PostgreSQL, la referencia
		relativa al audio, la inicialización y la respuesta ante archivos ausentes.

- [x] **T7 — Diseñar el reemplazo seguro de sesión** (25 min)
	- RF: RF-013, RF-014, RF-015.
	- Decisiones: confirmar solo cuando audio y JSON estén guardados; limpiar el
		audio anterior después de confirmar; mantener la nueva sesión si esa limpieza
	 falla; cancelar limpiando temporales; rechazar cargas simultáneas.
	- **Hecho cuando:** el plan define el flujo temporal, confirmado y descartado,
		el rollback ante fallo y la protección frente a operaciones simultáneas.

- [ ] **T8 — Preparar el visor y reproductor sincronizado** (25 min)
	- RF: RF-007.
	- Definir el comportamiento de reproducción, pausa, velocidades permitidas,
		salto temporal y resaltado del segmento activo.
	- **Hecho cuando:** cada control tiene un estado esperado y un caso de prueba
		asociado.

- [ ] **T9 — Definir edición y validación de timestamps** (25 min)
	- RF: RF-008.
	- Especificar cómo se editan textos y tiempos, y cómo se rechazan valores
		negativos, invertidos, solapados o fuera de la duración del audio.
	- **Hecho cuando:** están descritas las reglas para editar un segmento y se
		conserva su vínculo con el audio.

- [ ] **T10 — Definir el ciclo de vida de anotaciones** (25 min)
	- RF: RF-009, RF-010, RF-011.
	- Establecer creación, edición, eliminación, vínculo a segmento o timestamp y
		límite de 500 caracteres.
	- **Hecho cuando:** existen casos definidos para texto vacío, 500 caracteres y
		501 caracteres, además de referencias inválidas.

- [ ] **T11 — Definir contrato de exportación** (20 min)
	- RF: RF-016.
	- Concretar campos, codificación y persistencia del documento JSON en
		PostgreSQL, incluyendo el audio o sus metadatos.
	- **Hecho cuando:** un ejemplo de JSON persistido contiene sesión,
		transcripción, timestamps y anotaciones, sin sesiones reemplazadas.

- [ ] **T12 — Integrar el flujo principal** (25 min)
	- RF: RF-001 a RF-016.
	- Ordenar el recorrido cargar -> validar -> transcribir con `faster-whisper` ->
		editar -> anotar -> persistir el JSON; reservar el proveedor falso para
		simular errores.
	- **Hecho cuando:** el recorrido completo funciona con un audio sintético y
		produce una exportación válida.

- [ ] **T13 — Verificar errores y conservación de datos** (25 min)
	- RF: RF-002, RF-006, RF-014, RF-015.
	- Ejecutar escenarios de archivo inválido, error cloud, cancelación y fallo de
		persistencia durante una segunda carga.
	- **Hecho cuando:** ningún escenario elimina o mezcla la sesión anterior de
		forma incorrecta.

- [ ] **T14 — Ejecutar validación final RF por RF** (25 min)
	- RF/RNF: RF-001 a RF-016, RNF-001 a RNF-005.
	- Relacionar cada requisito con su prueba y revisar los criterios de
		finalización de `spec.md`.
	- **Hecho cuando:** todos los RF tienen una prueba con resultado documentado y
		el flujo se ejecuta únicamente con datos sintéticos.

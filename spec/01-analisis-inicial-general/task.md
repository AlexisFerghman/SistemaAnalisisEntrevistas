- [ ] **T1 — Cerrar decisiones abiertas del MVP** (20 min)
	- RF/RNF: RF-001, RF-004, RF-016, RNF-001, RNF-004.
	- Decidir proveedor cloud, formatos admitidos, límites de tamaño y duración,
		y formato de exportación.
	- **Hecho cuando:** las tres dudas abiertas de `spec.md` tienen una decisión
		documentada y aprobada, sin añadir funcionalidades fuera del MVP.

- [ ] **T2 — Definir el contrato de la sesión única** (25 min)
	- RF/RNF: RF-012, RNF-003.
	- Formalizar el documento de sesión, sus campos obligatorios, estados de
		transcripción y referencia al audio.
	- **Hecho cuando:** existe un ejemplo válido del documento y una lista de
		invariantes que incluye `version`, `session_id` y como máximo una sesión.

- [ ] **T3 — Definir el contrato normalizado de transcripción** (25 min)
	- RF/RNF: RF-004, RF-005, RNF-004.
	- Especificar la respuesta independiente del proveedor: idioma, segmentos,
		palabras opcionales, timestamps y estados de error.
	- **Hecho cuando:** una respuesta válida y una respuesta inválida están
		descritas con sus campos y reglas de validación.

- [ ] **T4 — Diseñar la validación y advertencia de audio sintético** (20 min)
	- RF/RNF: RF-001, RF-002, RF-003, RNF-001.
	- Definir los estados de validación, mensajes de rechazo y advertencia visible
		antes del envío cloud.
	- **Hecho cuando:** están documentados los casos de formato, archivo vacío,
		tamaño, duración y advertencia de datos reales.

- [ ] **T5 — Preparar proveedor falso y escenarios de error** (25 min)
	- RF: RF-004, RF-005, RF-006.
	- Definir respuestas simuladas para éxito, timeout, rechazo remoto, respuesta
		incompleta y timestamps inválidos.
	- **Hecho cuando:** cada escenario produce un resultado esperado sin llamar a
		un proveedor cloud real.

- [ ] **T6 — Definir la persistencia temporal de la sesión** (25 min)
	- RF: RF-012.
	- Elegir la representación concreta del documento y del archivo de audio
		actual dentro del almacenamiento de prototipo.
	- **Hecho cuando:** se puede crear, leer y eliminar una sesión única sin
		conservar sesiones anteriores.

- [ ] **T7 — Diseñar el reemplazo seguro de sesión** (25 min)
	- RF: RF-013, RF-014, RF-015.
	- Detallar los estados temporal, confirmada y descartada, incluyendo fallos y
		cancelación durante carga, transcripción o persistencia.
	- **Hecho cuando:** una prueba o diagrama demuestra que la sesión anterior
		sobrevive hasta la confirmación de la nueva.

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
	- Concretar campos, codificación y tratamiento del audio o sus metadatos en el
		formato decidido en T1.
	- **Hecho cuando:** un ejemplo de exportación contiene sesión, transcripción,
		timestamps y anotaciones, sin sesiones reemplazadas.

- [ ] **T12 — Integrar el flujo principal** (25 min)
	- RF: RF-001 a RF-016.
	- Ordenar el recorrido cargar -> validar -> transcribir -> editar -> anotar ->
		exportar usando el proveedor falso.
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

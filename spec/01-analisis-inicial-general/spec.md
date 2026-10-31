# Especificación de Requisitos: MVP de análisis inicial

## 1. Contexto y objetivo

El proyecto es un prototipo experimental para apoyar a un profesional de salud
en la revisión y anotación de una entrevista clínica sintética. El MVP permite
cargar un audio, obtener una transcripción mediante un modelo en la nube,
revisarla, editarla y añadir anotaciones vinculadas a fragmentos o timestamps.
Esta entrega no se utilizará en entornos clínicos reales y no produce
diagnósticos ni conclusiones clínicas.

## 2. Usuario y actores

- **Profesional de salud:** único usuario conceptual del flujo. No necesita
	cuenta, autenticación ni asignación de rol en este MVP.
- **Proveedor cloud de transcripción:** servicio externo que recibe el audio
	sintético y devuelve una transcripción con marcas de tiempo.

## 3. Historias de usuario

- **H1:** Como profesional de salud, quiero cargar un audio sintético y obtener
	una transcripción sincronizada para revisarla.
- **H2:** Como profesional de salud, quiero editar la transcripción y sus marcas
	de tiempo para corregir errores.
- **H3:** Como profesional de salud, quiero añadir anotaciones a fragmentos de
	la entrevista para organizar mi revisión.
- **H4:** Como profesional de salud, quiero exportar la sesión para conservar
	el resultado de mi trabajo.

## 4. Requisitos funcionales

### Carga y transcripción

- **RF-001:** CUANDO el usuario seleccione un archivo de audio sintético en un
	formato admitido, EL SISTEMA DEBE validar su formato, tamaño y duración antes
	de iniciar el procesamiento.
- **RF-002:** SI el archivo no cumple el formato, tamaño o duración permitidos,
	ENTONCES EL SISTEMA DEBE rechazarlo y mostrar un motivo comprensible.
- **RF-003:** SI el usuario intenta cargar un audio que contiene datos reales o
	identificables, ENTONCES EL SISTEMA DEBE mostrar una advertencia de que esta
	versión solo admite datos sintéticos. La detección automática completa de
	datos personales queda fuera del MVP.
- **RF-004:** CUANDO se acepte un archivo válido, EL SISTEMA DEBE enviarlo al
	proveedor cloud configurado para generar una transcripción en español.
- **RF-005:** CUANDO el proveedor cloud responda correctamente, EL SISTEMA DEBE
	mostrar la transcripción con marcas `start_time` y `end_time` por palabra y
	oración.
- **RF-006:** SI el proveedor cloud no responde o devuelve un error, ENTONCES
	EL SISTEMA DEBE informar el fallo, conservar la sesión anterior y no presentar
	una transcripción como válida.

### Revisión, edición y anotación

- **RF-007:** MIENTRAS exista una transcripción, EL SISTEMA DEBE permitir
	reproducir el audio, pausar, cambiar la velocidad entre 1x, 1.25x y 1.5x,
	saltar a un timestamp y visualizar la sincronización con el texto.
- **RF-008:** CUANDO el usuario active la edición, EL SISTEMA DEBE permitir
	modificar el texto y ajustar sus marcas de tiempo, conservando la relación
	entre cada segmento y el audio.
- **RF-009:** CUANDO el usuario seleccione un fragmento, EL SISTEMA DEBE
	permitirle crear una anotación de texto libre vinculada al fragmento o
	timestamp seleccionado.
- **RF-010:** EL SISTEMA DEBE limitar cada anotación a un máximo estricto de 500
	caracteres y rechazar el guardado de anotaciones que superen ese límite.
- **RF-011:** MIENTRAS exista una anotación, EL SISTEMA DEBE permitir editarla o
	eliminarla sin modificar el audio original.

### Sesión única y exportación

- **RF-012:** EL SISTEMA DEBE conservar como máximo una sesión de entrevista,
	compuesta por el audio, la transcripción y sus anotaciones.
- **RF-013:** CUANDO una nueva carga y su transcripción se completen
	correctamente, EL SISTEMA DEBE reemplazar la sesión anterior y eliminar sus
	datos almacenados.
- **RF-014:** SI la nueva carga, transcripción o persistencia falla, ENTONCES EL
	SISTEMA DEBE conservar la sesión anterior sin mezclar datos de ambas sesiones.
- **RF-015:** SI el usuario cancela una nueva carga, ENTONCES EL SISTEMA DEBE
	conservar la sesión existente sin cambios.
- **RF-016:** CUANDO el usuario solicite exportar, EL SISTEMA DEBE generar un
	archivo estructurado que incluya el audio o sus metadatos disponibles, la
	transcripción corregida, sus timestamps y las anotaciones.

## 5. Requisitos no funcionales

- **RNF-001:** El MVP DEBE utilizar datos ficticios o sintéticos y mostrar una
	advertencia visible antes de enviar audio al proveedor cloud.
- **RNF-002:** El MVP NO DEBE requerir cuentas, autenticación, roles ni
	asignación de pacientes.
- **RNF-003:** El MVP DEBE conservar como máximo una sesión y eliminar la sesión
	anterior después de procesar correctamente la nueva.
- **RNF-004:** Las salidas del proveedor cloud DEBEN conservar suficiente
	información para sincronizar cada segmento con el audio.
- **RNF-005:** Esta versión DEBE identificarse como prototipo experimental no
	apto para uso clínico real.

## 6. Casos límite

- Archivo vacío, corrupto, con formato no admitido o sin audio reconocible.
- Archivo que supera el límite de tamaño o duración.
- Error, timeout o respuesta incompleta del proveedor cloud.
- Cancelación durante la carga o el procesamiento.
- Edición de timestamps con valores negativos, invertidos o solapados.
- Anotación vacía, de exactamente 500 caracteres o superior al límite.
- Fallo al guardar la nueva sesión después de procesar el audio.
- Intento de cargar una segunda entrevista mientras la primera está siendo
	procesada.
- Exportación sin anotaciones o con una transcripción parcialmente editada.

## 7. Fuera de alcance

- Uso de entrevistas clínicas reales o datos identificables.
- Uso en entornos clínicos, toma de decisiones profesionales o diagnóstico.
- Cuentas, autenticación, administradores, roles y permisos multiusuario.
- Gestión de pacientes, candidatos, historiales o asignaciones.
- Procesamiento local o selección entre modelos locales y cloud.
- Análisis afectivo, probabilidades emocionales, XAI y mapas de calor.
- Chatbot, generación de informes clínicos y decisiones automatizadas.
- Historial de sesiones, recuperación de sesiones anteriores o auditoría de
	eliminaciones.
- Funcionalidades de PostgreSQL que excedan la persistencia de la sesión actual.

## 8. Criterios de finalización

- El flujo cargar -> transcribir -> editar -> anotar -> exportar funciona con un
	audio sintético válido.
- La transcripción incluye timestamps por palabra y oración.
- El usuario puede editar texto, timestamps y anotaciones.
- Se rechazan archivos inválidos y anotaciones superiores a 500 caracteres.
- Un fallo o cancelación de la nueva sesión no elimina la sesión anterior.
- Una nueva sesión procesada correctamente reemplaza y elimina la anterior.
- La exportación incluye transcripción, timestamps y anotaciones.
- Las pruebas y la demostración utilizan exclusivamente datos sintéticos.

## 9. Dudas abiertas

- [NECESITA ACLARACIÓN] Proveedor cloud de transcripción.
- [NECESITA ACLARACIÓN] Límites concretos de tamaño y duración del audio.
- [NECESITA ACLARACIÓN] Formato exacto de exportación y almacenamiento temporal.
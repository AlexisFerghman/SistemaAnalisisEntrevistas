# Constitución del prototipo de análisis de entrevistas clínicas

## 1. Propósito y alcance

El proyecto es un prototipo experimental para explorar la transcripción y anotación de entrevistas clínicas mediante modelos de IA en la nube. Esta entrega no está destinada a entornos clínicos reales ni a la toma de decisiones profesionales.

El MVP trabaja únicamente con audios ficticios o sintéticos. No admite datos reales, identificables o sensibles.

## 2. Principios fundamentales

### P1. Supervisión humana obligatoria

- El sistema no emite diagnósticos, evaluaciones psiquiátricas ni decisiones 	clínicas.
- La transcripción y las anotaciones generadas o modificadas en el sistema son 	revisadas por el profesional antes de considerarse válidas.
- Las salidas de la IA se presentan como asistencia experimental, nunca como 	una conclusión profesional.

### P2. Datos sintéticos y límites de privacidad

- El MVP solo permite datos ficticios o sintéticos.
- El usuario no debe cargar entrevistas reales, nombres, identificadores, 	historias clínicas ni ningún otro dato sensible.
- En el MVP, el audio se procesa mediante un servicio local aislado en Docker.
- El despliegue en un servidor cloud privado se reserva para entregas finales y
	requerirá una revisión posterior de seguridad y arquitectura.
- Esta versión no implementa autenticación, cuentas, roles ni control de acceso multiusuario y no debe considerarse apta para producción.

### P3. Sesión única y eliminación de datos

- El prototipo conserva como máximo una sesión de entrevista.
- Cuando una nueva sesión se procesa correctamente, la sesión anterior se elimina para evitar el solapamiento de datos.
- Si la nueva carga, transcripción o persistencia falla, la sesión anterior se conserva.
- La eliminación de la sesión anterior no requiere historial ni recuperación en esta versión.

### P4. Calidad y trazabilidad de la transcripción

- La transcripción debe conservar marcas de tiempo por palabra y oración.
- El profesional debe poder revisar y editar el texto y sus marcas de tiempo.
- Las anotaciones deben permanecer vinculadas al fragmento o timestamp que les dio origen.
- El audio original no se modifica ni se sustituye por una versión editada.

### P5. Simplicidad del MVP

- El MVP se limita al flujo de carga, transcripción, edición, anotación y exportación.
- El análisis afectivo, la explicabilidad XAI, el chatbot, la gestión de usuarios y las funciones multiusuario quedan fuera de esta entrega.
- Ninguna decisión de arquitectura o proveedor cloud se considera aprobada hasta quedar documentada en el plan.
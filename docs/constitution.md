<!--
Sync Impact Report
==================
Versión: sin versión (borrador en formato libre) → 1.0.0
Tipo de cambio: adopción inicial de la versión formal bajo el scaffold de Spec Kit.

Principios modificados (título anterior → nuevo título):
  - P1. Supervisión humana obligatoria            → I. Supervisión humana obligatoria
  - P2. Datos sintéticos y límites de privacidad  → II. Datos sintéticos y privacidad del prototipo
  - P3. Sesión única y eliminación de datos       → III. Sesión única y eliminación de datos
  - P4. Calidad y trazabilidad de la transcripción→ IV. Calidad y trazabilidad de la transcripción
  - P5. Simplicidad del MVP                       → V. Simplicidad del MVP
  (Sin cambios de fondo en ninguno de los cinco principios: el texto se conserva; solo cambia la
   numeración a numerales romanos y se normalizan tabulaciones sueltas del borrador.)

Secciones añadidas:
  - Restricciones adicionales y de despliegue (recoge, sin alterarlos, los puntos de despliegue en
    cloud privado, ausencia de autenticación y no aptitud para producción que estaban dentro de P2).
  - Gobernanza (procedimiento de enmienda, versionado semántico y revisión de cumplimiento).

Secciones eliminadas:
  - Ninguna. "1. Propósito y alcance" se conserva íntegra y pasa a ser la sección "Propósito y
    alcance", ubicada después de los principios para respetar el orden del template resuelto.

Diferidos:
  - TODO(RATIFICATION_DATE): el borrador original no registra fecha de adopción; debe fijarse en la
    primera aprobación formal del equipo.
-->

# Constitución del prototipo de análisis de entrevistas clínicas

## Principios fundamentales

### I. Supervisión humana obligatoria (NO NEGOCIABLE)

- El sistema no emite diagnósticos, evaluaciones psiquiátricas ni decisiones clínicas.
- La transcripción y las anotaciones generadas o modificadas en el sistema son revisadas por el
  profesional antes de considerarse válidas.
- Las salidas de la IA se presentan como asistencia experimental, nunca como una conclusión
  profesional.

**Razón**: el valor del prototipo está en asistir la revisión de un profesional, no en sustituir su
criterio. Cualquier funcionalidad que emita juicio clínico queda fuera del alcance.

### II. Datos sintéticos y privacidad del prototipo

- El MVP solo permite datos ficticios o sintéticos.
- El usuario no debe cargar entrevistas reales, nombres, identificadores, historias clínicas ni
  ningún otro dato sensible.
- En el MVP, el audio se procesa mediante un servicio local aislado en Docker.
- Esta versión no implementa autenticación, cuentas, roles ni control de acceso multiusuario.

**Razón**: al no existir garantías de seguridad ni base legal para tratar datos reales, el prototipo
solo es defendible sobre material sintético y en un entorno local controlado.

### III. Sesión única y eliminación de datos

- El prototipo conserva como máximo una sesión de entrevista.
- Cuando una nueva sesión se procesa correctamente, la sesión anterior se elimina para evitar el
  solapamiento de datos.
- Si la nueva carga, transcripción o persistencia falla, la sesión anterior se conserva.
- La eliminación de la sesión anterior no requiere historial ni recuperación en esta versión.

**Razón**: una única sesión mantiene el modelo de datos y la interfaz simples, y reduce la
superficie donde podrían acumularse datos sensibles.

### IV. Calidad y trazabilidad de la transcripción

- La transcripción debe conservar marcas de tiempo por palabra y oración.
- El profesional debe poder revisar y editar el texto y sus marcas de tiempo.
- Las anotaciones deben permanecer vinculadas al fragmento o timestamp que les dio origen.
- El audio original no se modifica ni se sustituye por una versión editada.

**Razón**: sin marcas de tiempo fiables y sin vínculo entre anotación y audio, la revisión
profesional pierde verificabilidad y el resultado deja de ser auditable.

### V. Simplicidad del MVP

- El MVP se limita al flujo de carga, transcripción, edición, anotación y exportación.
- El análisis afectivo, la explicabilidad XAI, el chatbot, la gestión de usuarios y las funciones
  multiusuario quedan fuera de esta entrega.
- Ninguna decisión de arquitectura o proveedor cloud se considera aprobada hasta quedar
  documentada en el plan.

**Razón**: el objetivo de esta entrega es validar el flujo principal de extremo a extremo, no cubrir
funcionalidades diferenciales.

## Propósito y alcance

El proyecto es un prototipo experimental para explorar la transcripción y anotación de entrevistas
clínicas mediante modelos de IA en la nube. Esta entrega no está destinada a entornos clínicos
reales ni a la toma de decisiones profesionales.

El MVP trabaja únicamente con audios ficticios o sintéticos. No admite datos reales, identificables
o sensibles.

## Restricciones adicionales y de despliegue

- El despliegue en un servidor cloud privado se reserva para entregas finales y requerirá una
  revisión posterior de seguridad y arquitectura.
- Esta versión no debe considerarse apta para producción.
- Cualquier cambio de proveedor, servicio o infraestructura externa requiere quedar documentado en
  el plan de la entrega correspondiente antes de implementarse.

## Gobernanza

- Esta constitución prevalece sobre cualquier otra práctica, convención o preferencia técnica del
  repositorio. Especificaciones, planes y tareas deben verificar su cumplimiento.
- **Enmiendas**: requieren una propuesta documentada con la justificación del cambio, la aprobación
  del responsable del proyecto y la actualización de los artefactos afectados en `spec/`. Ninguna
  enmienda puede eliminar el principio I ni habilitar el uso de datos reales.
- **Versionado**: se aplica versionado semántico. MAJOR ante eliminación o redefinición incompatible
  de principios o reglas de gobernanza; MINOR ante nuevos principios, secciones o guía ampliada;
  PATCH ante aclaraciones, correcciones de redacción o ajustes no semánticos.
- **Revisión de cumplimiento**: toda revisión de especificación, plan o tarea debe comprobar los
  cinco principios. Una violación bloquea la aprobación salvo que exista una enmienda aprobada con
  anterioridad.
- **Guía de trabajo**: `README.md` y `spec/` describen el estado vigente del prototipo; ante
  conflicto con esta constitución, prevalece la constitución.

**Versión**: 1.0.0 | **Ratificada**: TODO(RATIFICATION_DATE) | **Última enmienda**: 2026-11-02

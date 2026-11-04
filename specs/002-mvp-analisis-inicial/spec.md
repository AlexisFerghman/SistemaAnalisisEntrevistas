<!--
Trazabilidad de la reformulación
================================
Origen: spec/01-analisis-inicial-general/spec.md (formato libre, secciones 1-9).
Destino: plantilla `spec-template` de Spec Kit (capa core).

Mapeo aplicado:
  - Sección 1 (Contexto y objetivo)          → "Contexto y objetivo" (sección opcional, único añadido estructural)
  - Sección 2 (Usuario y actores)            → "Supuestos > Actores y usuarios"
  - Sección 3 (Historias H1-H4)              → "Escenarios de usuario y pruebas" (Historias 1-4, Prioridad P1-P4)
  - Sección 4 (RF-001..RF-016)               → "Requisitos > Requisitos funcionales" (IDs y semántica conservados)
  - Sección 5 (RNF-001..RNF-005)             → "Requisitos > Requisitos no funcionales" (IDs y texto conservados)
  - Sección 6 (Casos límite)                 → "Escenarios de usuario y pruebas > Casos límite" (texto conservado)
  - Sección 7 (Fuera de alcance)             → "Supuestos > Fuera de alcance"
  - Sección 8 (Criterios de finalización)    → "Criterios de éxito > Resultados medibles" (SC-001..SC-008)
  - Sección 9 (Dudas abiertas)               → "Supuestos > Decisiones provisionales"

Ajustes deliberados, sin cambio de alcance:
  - RF-004, RF-005 y RF-016 dejan de nombrar Docker, PostgreSQL y los campos `start_time`/`end_time`;
    esos detalles pasan a "Supuestos > Supuestos técnicos y dependencias", por indicación del usuario.
  - Los IDs RF-*/RNF-* se conservan literales porque plan.md y task.md los referencian.
  - "Entidades clave" es nuevo y se deriva del modelo de datos de plan.md; no introduce requisitos.
-->

# Feature Specification: MVP de análisis inicial

**Feature Branch**: `002-mvp-analisis-inicial`

**Created**: 2026-11-02

**Status**: Borrador

**Input**: User description: "Reformatear a la plantilla de Spec Kit la especificación existente en spec/01-analisis-inicial-general/spec.md sin alterar su enfoque, su contenido importante ni el objetivo alcanzado."

## Contexto y objetivo

El proyecto es un prototipo experimental para apoyar a un profesional de salud en la revisión y
anotación de una entrevista clínica sintética. El MVP permite cargar un audio, obtener una
transcripción mediante un servicio local aislado, revisarla, editarla y añadir anotaciones
vinculadas a fragmentos o timestamps.

Esta entrega no se utilizará en entornos clínicos reales y no produce diagnósticos ni conclusiones
clínicas.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 — Cargar un audio sintético y obtener su transcripción (Prioridad: P1)

El profesional de salud carga un audio de una entrevista sintética y obtiene una transcripción en
español con marcas de tiempo que puede revisar.

**Por qué esta prioridad**: sin transcripción no hay nada que revisar, editar ni anotar. Es la base
del flujo y la primera porción demostrable de valor.

**Prueba independiente**: cargar un audio sintético válido y comprobar que aparece una transcripción
sincronizada demuestra la historia por sí sola, sin editor ni anotaciones implementados.

**Escenarios de aceptación**:

1. **Dado** un audio sintético en un formato admitido y dentro de los límites, **Cuando** el usuario
   lo selecciona, **Entonces** el sistema valida formato, tamaño y duración y genera una
   transcripción en español con marca de inicio y fin por palabra y por oración.
2. **Dado** un archivo vacío, corrupto, con formato no admitido o fuera de los límites, **Cuando** el
   usuario intenta cargarlo, **Entonces** el sistema lo rechaza y muestra un motivo comprensible.
3. **Dado** un audio que contiene datos reales o identificables, **Cuando** el usuario inicia la
   carga, **Entonces** el sistema le advierte de que esta versión solo admite datos sintéticos.
4. **Dado** un fallo, timeout o respuesta incompleta del servicio local de transcripción, **Cuando**
   el procesamiento no concluye, **Entonces** el sistema informa el fallo, conserva la sesión
   anterior y no presenta la transcripción como válida.
5. **Dado** que existía una sesión anterior, **Cuando** la nueva carga, transcripción y persistencia
   se completan correctamente, **Entonces** el sistema elimina la sesión anterior sin mezclar datos
   de ambas.
6. **Dado** que el usuario cancela una nueva carga, **Cuando** la operación se interrumpe,
   **Entonces** la sesión existente se conserva sin cambios.

---

### Historia de usuario 2 — Revisar y editar la transcripción (Prioridad: P2)

El profesional de salud reproduce el audio sincronizado con el texto y corrige errores de
transcripción y de marcas de tiempo.

**Por qué esta prioridad**: la transcripción automática es imperfecta; sin corrección el resultado
no es utilizable profesionalmente.

**Prueba independiente**: con una transcripción ya cargada, reproducir, pausar, cambiar de
velocidad, saltar a un timestamp y editar texto y marcas demuestra la historia sin anotaciones ni
exportación.

**Escenarios de aceptación**:

1. **Dado** una transcripción existente, **Cuando** el usuario reproduce el audio, **Entonces** puede
   pausar, cambiar la velocidad entre 1x, 1.25x y 1.5x, saltar a un timestamp y ver la
   sincronización con el texto.
2. **Dado** el modo de edición, **Cuando** el usuario modifica el texto o las marcas de tiempo,
   **Entonces** se conserva la relación entre cada segmento y el audio.
3. **Dado** una marca de tiempo con valores negativos, invertidos o solapados, **Cuando** el usuario
   intenta guardarla, **Entonces** el sistema la rechaza e indica el motivo.
4. **Dado** que el usuario edita la transcripción, **Cuando** guarda los cambios, **Entonces** el
   audio original permanece sin modificar.

---

### Historia de usuario 3 — Anotar fragmentos de la entrevista (Prioridad: P3)

El profesional de salud añade notas de texto libre a fragmentos o timestamps concretos para
organizar su revisión.

**Por qué esta prioridad**: las anotaciones aportan valor sobre una transcripción ya revisable, pero
el flujo sigue siendo demostrable sin ellas.

**Prueba independiente**: seleccionar un fragmento, crear una anotación y volver a leerla vinculada
al mismo fragmento demuestra la historia sin exportación.

**Escenarios de aceptación**:

1. **Dado** un fragmento seleccionado, **Cuando** el usuario crea una anotación de texto libre,
   **Entonces** queda vinculada al fragmento o timestamp que le dio origen.
2. **Dado** un texto de exactamente 500 caracteres, **Cuando** el usuario lo guarda, **Entonces** la
   anotación se guarda.
3. **Dado** un texto vacío o de más de 500 caracteres, **Cuando** el usuario intenta guardarlo,
   **Entonces** el sistema rechaza el guardado.
4. **Dado** una anotación existente, **Cuando** el usuario la edita o la elimina, **Entonces** el
   audio original no se modifica.

---

### Historia de usuario 4 — Exportar la sesión (Prioridad: P4)

El profesional de salud exporta la sesión actual para conservar el resultado de su trabajo.

**Por qué esta prioridad**: cierra el flujo y preserva el trabajo, pero depende de que existan
transcripción y anotaciones.

**Prueba independiente**: solicitar la exportación de una sesión lista y comprobar que el documento
resultante contiene audio o metadatos, transcripción corregida, timestamps y anotaciones demuestra
la historia por sí sola.

**Escenarios de aceptación**:

1. **Dado** una sesión con transcripción y anotaciones, **Cuando** el usuario solicita exportar,
   **Entonces** el sistema persiste el documento JSON de la sesión actual con el audio o sus
   metadatos disponibles, la transcripción corregida, sus marcas de tiempo y las anotaciones.
2. **Dado** una sesión sin anotaciones, **Cuando** el usuario exporta, **Entonces** el documento se
   genera con la transcripción íntegra y sin anotaciones.
3. **Dado** una transcripción parcialmente editada, **Cuando** el usuario exporta, **Entonces** se
   persiste la versión corregida y no la original.

### Casos límite

- Archivo vacío, corrupto, con formato no admitido o sin audio reconocible.
- Archivo que supera el límite de tamaño o duración.
- Error, timeout o respuesta incompleta del servicio local de transcripción.
- Cancelación durante la carga o el procesamiento.
- Edición de marcas de tiempo con valores negativos, invertidos o solapados.
- Anotación vacía, de exactamente 500 caracteres o superior al límite.
- Fallo al guardar la nueva sesión después de procesar el audio.
- Intento de cargar una segunda entrevista mientras la primera está siendo procesada.
- Exportación sin anotaciones o con una transcripción parcialmente editada.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **RF-001**: CUANDO el usuario seleccione un archivo de audio sintético en un formato admitido, el
  sistema DEBE validar su formato, tamaño y duración antes de iniciar el procesamiento.
- **RF-002**: SI el archivo no cumple el formato, tamaño o duración permitidos, ENTONCES el sistema
  DEBE rechazarlo y mostrar un motivo comprensible.
- **RF-003**: SI el usuario intenta cargar un audio que contiene datos reales o identificables,
  ENTONCES el sistema DEBE mostrar una advertencia de que esta versión solo admite datos sintéticos.
  La detección automática completa de datos personales queda fuera del MVP.
- **RF-004**: CUANDO se acepte un archivo válido, el sistema DEBE enviarlo al servicio local de
  transcripción aislado para generar una transcripción en español.
- **RF-005**: CUANDO el servicio local de transcripción responda correctamente, el sistema DEBE
  mostrar la transcripción con una marca de inicio y una marca de fin por palabra y por oración.
- **RF-006**: SI el servicio local de transcripción no responde o devuelve un error, ENTONCES el
  sistema DEBE informar el fallo, conservar la sesión anterior y no presentar una transcripción como
  válida.
- **RF-007**: MIENTRAS exista una transcripción, el sistema DEBE permitir reproducir el audio,
  pausar, cambiar la velocidad entre 1x, 1.25x y 1.5x, saltar a un timestamp y visualizar la
  sincronización con el texto.
- **RF-008**: CUANDO el usuario active la edición, el sistema DEBE permitir modificar el texto y
  ajustar sus marcas de tiempo, conservando la relación entre cada segmento y el audio.
- **RF-009**: CUANDO el usuario seleccione un fragmento, el sistema DEBE permitirle crear una
  anotación de texto libre vinculada al fragmento o timestamp seleccionado.
- **RF-010**: El sistema DEBE limitar cada anotación a un máximo estricto de 500 caracteres y
  rechazar el guardado de anotaciones que superen ese límite.
- **RF-011**: MIENTRAS exista una anotación, el sistema DEBE permitir editarla o eliminarla sin
  modificar el audio original.
- **RF-012**: El sistema DEBE conservar como máximo una sesión de entrevista, compuesta por el
  audio, la transcripción y sus anotaciones.
- **RF-013**: CUANDO una nueva carga y su transcripción se completen correctamente, el sistema DEBE
  reemplazar la sesión anterior y eliminar sus datos almacenados.
- **RF-014**: SI la nueva carga, transcripción o persistencia falla, ENTONCES el sistema DEBE
  conservar la sesión anterior sin mezclar datos de ambas sesiones.
- **RF-015**: SI el usuario cancela una nueva carga, ENTONCES el sistema DEBE conservar la sesión
  existente sin cambios.
- **RF-016**: CUANDO el usuario solicite exportar, el sistema DEBE persistir el documento JSON de la
  sesión actual, incluyendo el audio o sus metadatos disponibles, la transcripción corregida, sus
  marcas de tiempo y las anotaciones.

### Requisitos no funcionales

- **RNF-001**: El MVP DEBE utilizar datos ficticios o sintéticos y mostrar una advertencia visible
  antes de enviar audio al servicio local de transcripción.
- **RNF-002**: El MVP NO DEBE requerir cuentas, autenticación, roles ni asignación de pacientes.
- **RNF-003**: El MVP DEBE conservar como máximo una sesión y eliminar la sesión anterior después de
  procesar correctamente la nueva.
- **RNF-004**: Las salidas del servicio local DEBEN conservar suficiente información para
  sincronizar cada segmento con el audio.
- **RNF-005**: Esta versión DEBE identificarse como prototipo experimental no apto para uso clínico
  real.

### Entidades clave

- **Sesión de entrevista**: unidad única que conserva el sistema; agrupa un audio, su transcripción y
  sus anotaciones. Atributos: identificador de la sesión actual y estado (vacía, en validación, en
  proceso, lista, revisada o con error).
- **Audio**: archivo sintético cargado por el profesional. Atributos: nombre, tipo, tamaño, duración
  y referencia de almacenamiento.
- **Transcripción**: resultado de la transcripción automática en español. Atributos: idioma, origen
  y segmentos.
- **Segmento**: tramo de la transcripción. Atributos: identificador, marca de inicio, marca de fin,
  texto y palabras.
- **Palabra**: unidad mínima de la transcripción. Atributos: texto, marca de inicio y marca de fin.
- **Anotación**: nota de texto libre de hasta 500 caracteres vinculada a un segmento o timestamp.
  Atributos: identificador, texto y referencia al fragmento.
- **Exportación**: documento JSON que consolida la sesión para conservarla fuera de la aplicación.

Relaciones: una Sesión contiene como máximo un Audio y una Transcripción, y ninguna o varias
Anotaciones; una Transcripción contiene varios Segmentos; un Segmento contiene varias Palabras; cada
Anotación referencia exactamente un Segmento.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: Un usuario completa el flujo cargar → transcribir → editar → anotar → exportar con un
  audio sintético válido en una sola sesión de trabajo, sin pasos manuales fuera de la aplicación.
- **SC-002**: El 100% de las transcripciones mostradas incluye marca de inicio y fin tanto por
  palabra como por oración.
- **SC-003**: El 100% de los audios con formato, tamaño o duración no admitidos se rechaza con un
  motivo comprensible y ninguno inicia procesamiento.
- **SC-004**: El 100% de las anotaciones guardadas tiene 500 caracteres o menos y ninguna anotación
  de 501 caracteres o más llega a guardarse.
- **SC-005**: El 100% de los fallos y cancelaciones durante una nueva carga deja la sesión anterior
  disponible y sin datos mezclados.
- **SC-006**: Tras completarse una nueva sesión, el sistema conserva exactamente una sesión y ningún
  dato recuperable de la anterior.
- **SC-007**: El 100% de las exportaciones contiene la transcripción corregida, sus marcas de tiempo
  y las anotaciones de la sesión exportada.
- **SC-008**: El 100% de las pruebas y demostraciones se ejecuta con datos sintéticos y ninguna
  sesión contiene datos reales o identificables.

## Supuestos

### Actores y usuarios

- **Profesional de salud**: único usuario conceptual del flujo. No necesita cuenta, autenticación ni
  asignación de rol en este MVP.
- **Servicio local de transcripción**: componente aislado que recibe el audio sintético y devuelve
  una transcripción con marcas de tiempo.

### Fuera de alcance

- Uso de entrevistas clínicas reales o datos identificables.
- Uso en entornos clínicos, toma de decisiones profesionales o diagnóstico.
- Cuentas, autenticación, administradores, roles y permisos multiusuario.
- Gestión de pacientes, candidatos, historiales o asignaciones.
- Despliegue en un servidor cloud privado; se reserva para entregas futuras.
- Análisis afectivo, probabilidades emocionales, XAI y mapas de calor.
- Chatbot, generación de informes clínicos y decisiones automatizadas.
- Historial de sesiones, recuperación de sesiones anteriores o auditoría de eliminaciones.
- Funcionalidades de persistencia que excedan el almacenamiento de la sesión actual.

### Decisiones provisionales

- El MVP admite archivos `.mp3` y `.wav`, con un límite provisional de 120 MB por audio.
- La exportación se persiste como documento JSON.
- No quedan dudas abiertas para esta versión de la especificación.

### Supuestos técnicos y dependencias

- El servicio de transcripción se ejecuta de forma local y aislada en Docker.
- El documento de la única sesión se persiste en PostgreSQL, sin ampliar el alcance funcional.
- Las marcas de tiempo se expresan en segundos desde el inicio del audio y se nombran `start_time` y
  `end_time` en el modelo de datos.
- El despliegue en un servidor cloud privado se reserva para entregas finales y requiere una revisión
  posterior de seguridad y arquitectura.

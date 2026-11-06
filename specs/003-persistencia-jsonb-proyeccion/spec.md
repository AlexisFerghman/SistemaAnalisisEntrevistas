<!--
Trazabilidad de la reformulación
================================
Origen: requisitos R1-R5 de la tarea de refactorización de persistencia sobre la feature
`002-mvp-analisis-inicial`.

Alcance:
  - R1 json -> jsonb ......................... RF-017, RNF-006, RNF-010
  - R2 identificador UUID + created_at ....... RF-018
  - R3 actualizaciones parciales con jsonb_set RF-019
  - R4 proyección de lectura + endpoint words  RF-020, RF-021, RF-022, RNF-007
  - R5 evolución prevista (solo documentación) RF-023

Reglas de compatibilidad:
  - No se renumeran ni se redefinen RF-001..RF-016 ni RNF-001..RNF-005 de `002`.
  - Los nuevos identificadores empiezan en RF-017 y RNF-006 para no colisionar.
  - No se normaliza el modelo ni se cambia el motor de base de datos.
-->

# Feature Specification: Persistencia JSONB y proyección de lectura

**Feature Branch**: `003-persistencia-jsonb-proyeccion`

**Created**: 2026-11-06

**Status**: Borrador

**Input**: User description: "Reducir el tráfico y corregir el tipo de dato de la persistencia sin cambiar de motor y sin normalizar: json a jsonb, identificador de sesión UUID, actualizaciones parciales con jsonb_set y proyección de lectura resumida con endpoint de palabras por segmento."

## Contexto y objetivo

La feature `002-mvp-analisis-inicial` persiste toda la sesión en una única fila de PostgreSQL. La
medición real es de 144 818 bytes para unos 12 minutos de audio, y 118 006 bytes (81 %) corresponden
al array `words` de los segmentos. Ese array solo lo necesita el editor cuando trabaja con marcas por
palabra; la lista de segmentos, el reproductor y el encabezado no lo usan.

Esta feature reduce el tráfico de lectura y corrige el tipo de la columna `payload` sin cambiar de
motor, sin normalizar el modelo y sin alterar el comportamiento funcional de `RF-001`…`RF-016`:

1. `json` pasa a `jsonb` en `current_session` y `current_export`, con migración reversible.
2. `current_session.id` deja de ser el literal `current` y pasa a ser un UUID con `created_at`
   propio; el sistema sigue manteniendo una sola fila.
3. Las anotaciones se escribirán con `jsonb_set`/`||` en SQL. Como aún no están implementadas, esta
   entrega fija la restricción de diseño para la Fase 5 de `002`, sin escribir ese código.
4. `GET /api/session` devuelve por defecto una vista resumen sin `words` y con `words_count` por
   segmento; `?view=full` conserva la respuesta completa y se añade un endpoint para obtener las
   palabras de un segmento concreto.
5. Se documenta la evolución futura multi-médico, multi-paciente y multi-sesión, sin implementarla.

El audio (`GET /api/session/audio`) y el documento de exportación no cambian: la exportación sigue
incluyendo las marcas por palabra para cumplir `RF-016`.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 — Migrar la persistencia sin perder la sesión (Prioridad: P1)

El equipo despliega la nueva versión sobre una base de datos que ya contiene una sesión y comprueba
que la fila existente sobrevive con su contenido, que el tipo de `payload` es `jsonb` y que el
identificador de la sesión es un UUID estable.

**Por qué esta prioridad**: sin una migración segura no se puede tocar la proyección ni las
anotaciones; una pérdida de la sesión violaría el principio III y `RF-012`…`RF-014`.

**Prueba independiente**: sobre una base con una fila `current` de prueba, ejecutar la migración,
comprobar que `information_schema` reporta `jsonb`, que el audio, la transcripción y las anotaciones
siguen presentes, que `pg_column_size(payload)` no aumenta y que una segunda ejecución no falla ni
duplica filas.

**Escenarios de aceptación**:

1. **Dado** un `payload` de tipo `json` con una sesión completa, **Cuando** se ejecuta la migración,
   **Entonces** la columna pasa a `jsonb`, el contenido lógico se conserva y `pg_column_size` no
   aumenta.
2. **Dado** que la fila existente tiene `id = 'current'`, **Cuando** se ejecuta la migración,
   **Entonces** recibe un UUID único y una columna `created_at`, y el documento deja de contener el
   literal `session-current`.
3. **Dado** que la migración ya se aplicó, **Cuando** se ejecuta de nuevo, **Entonces** no falla, no
   duplica filas y no vuelve a modificar el contenido.
4. **Dado** que se necesita revertir, **Cuando** se aplica el reverso documentado, **Entonces** las
   columnas vuelven a `json` y `id = 'current'` sin pérdida del contenido.
5. **Dado** el sistema en funcionamiento, **Cuando** se consulta la sesión, **Entonces** sigue
   habiendo como máximo una fila y el `session_id` expuesto coincide con el UUID de la fila.

---

### Historia de usuario 2 — Consultar la sesión sin descargar todas las palabras (Prioridad: P1)

El profesional abre o recarga la pantalla de trabajo y recibe la sesión con audio, metadatos de
transcripción, segmentos y anotaciones, pero sin el array completo de marcas por palabra. Solo pide
las palabras de un segmento cuando el editor las necesita.

**Por qué esta prioridad**: es la reducción de tráfico que motiva la feature; el 81 % del documento
son marcas que la vista principal no consume.

**Prueba independiente**: sobre una sesión de prueba, medir los bytes de `GET /api/session` y de
`GET /api/session?view=full`; el resumen debe ser menos del 25 % del completo, no debe contener la
clave `words` en ningún segmento, debe incluir `words_count`, y el endpoint de palabras de un
segmento debe devolver exactamente sus palabras.

**Escenarios de aceptación**:

1. **Dado** una sesión con transcripción, **Cuando** se solicita `GET /api/session`, **Entonces** la
   respuesta incluye audio, metadatos de transcripción, segmentos sin `words` y `words_count` por
   segmento.
2. **Dado** la misma sesión, **Cuando** se solicita `GET /api/session?view=full`, **Entonces** la
   respuesta es equivalente al documento completo anterior, incluidas las marcas por palabra; la
   única diferencia admitida es `session_id`, que pasa a ser el UUID de la fila por `RF-018`.
3. **Dado** un segmento concreto, **Cuando** el editor solicita sus palabras, **Entonces** recibe
   únicamente las palabras de ese segmento y un `404` comprensible si el segmento no existe.
4. **Dado** que el usuario edita texto o marcas, **Cuando** guarda, **Entonces** las marcas por
   palabra se conservan o se recalculan como hoy y la vista resumida no las pierde en la base de
   datos.
5. **Dado** que el usuario exporta, **Cuando** se genera el documento, **Entonces** la exportación
   sigue conteniendo las marcas por palabra y no usa la proyección resumida (`RF-016`).
6. **Dado** una petición a `GET /api/session/audio`, **Cuando** se reproduce el audio, **Entonces** la
   respuesta y el soporte de rangos no cambian (`RF-007`).

---

### Historia de usuario 3 — Guardar anotaciones sin reescribir el documento (Prioridad: P2)

El equipo que implemente la Fase 5 de `002` dispone de una restricción de diseño verificable: crear,
editar y eliminar una anotación debe ejecutarse con una sentencia SQL que use `jsonb_set` o el
operador `||` sobre `payload->'annotations'`, sin leer el documento completo en la aplicación y
volver a escribirlo.

**Por qué esta prioridad**: el requisito R3 condiciona la implementación futura de `RF-009`…`RF-011`
y evita que la feature de persistencia nazca con el patrón de lectura-reescritura que se quiere
eliminar. No se implementa en esta entrega.

**Prueba independiente**: revisar el contrato de la Fase 5 y comprobar que cada operación de
anotación tiene una única sentencia `UPDATE ... jsonb_set(...)` o `UPDATE ... payload || ...` y que
ninguna ruta de anotaciones llama a la lectura y escritura completa del documento.

**Escenarios de aceptación**:

1. **Dado** el contrato de la Fase 5, **Cuando** se revisa el alta de una anotación, **Entonces**
   especifica un `UPDATE` con `jsonb_set`/`||` y sin `get_document()` + `save_document()`.
2. **Dado** el contrato de la Fase 5, **Cuando** se revisa la edición o el borrado, **Entonces**
   especifica la localización de la anotación por `id` dentro del array y una única escritura.
3. **Dado** el contrato de la Fase 5, **Cuando** se valida el segmento referenciado, **Entonces** la
   validación se hace con una consulta dirigida o `jsonb_path_exists`, no cargando el documento
   completo en memoria.
4. **Dado** que esta entrega no implementa anotaciones, **Cuando** se ejecutan las pruebas actuales,
   **Entonces** las 49 pruebas de backend y las 5 de frontend siguen pasando.

---

### Historia de usuario 4 — Documentar la evolución multi-médico y multi-paciente (Prioridad: P3)

El equipo dispone de una hoja de ruta escrita para pasar del prototipo de sesión única a un sistema
con médicos, pacientes, múltiples sesiones, permisos y auditoría, sin cambiar de motor de base de
datos.

**Por qué esta prioridad**: la decisión de mantener PostgreSQL y no normalizar ahora solo es
sostenible si queda documentado cómo se evolucionará después; no aporta valor funcional inmediato.

**Prueba independiente**: leer la sección "Evolución prevista" del plan y comprobar que cubre
normalización, RLS, enmienda mayor de la constitución, autenticación y auditoría, con su orden.

**Escenarios de aceptación**:

1. **Dado** el plan de la feature, **Cuando** se lee "Evolución prevista", **Entonces** describe la
   normalización futura de médicos, pacientes, sesiones, segmentos y anotaciones.
2. **Dado** el mismo apartado, **Cuando** se revisa la seguridad, **Entonces** incluye RLS,
   autenticación y auditoría como pasos posteriores a la normalización.
3. **Dado** el mismo apartado, **Cuando** se revisa la gobernanza, **Entonces** indica que el cambio
   exige una enmienda mayor de la constitución de `1.0.0` a `2.0.0`.

### Casos límite

- La fila existente tiene `id = 'current'`, `payload` de tipo `json` y `session_id =
  'session-current'`.
- La migración se ejecuta dos veces o sobre una base ya migrada.
- La migración falla a mitad: la transacción debe dejar el esquema y la fila en el estado anterior.
- La sesión está vacía (`audio = null`, `transcription = null`).
- Se solicita `?view=full` o un valor de `view` distinto de `summary`/`full`.
- Se solicita las palabras de un segmento inexistente o de una sesión sin transcripción.
- El editor guarda una transcripción construida a partir de la vista resumida.
- La exportación se genera después de una lectura resumida y debe seguir incluyendo `words`.
- El audio se reproduce con `Range` mientras la sesión se consulta en modo resumen.
- Dos operaciones intentan modificar anotaciones a la vez en la futura Fase 5.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **RF-017**: El sistema DEBE almacenar `current_session.payload` y `current_export.payload` como
  `jsonb`, migrando la fila existente con `ALTER COLUMN ... TYPE jsonb USING payload::jsonb` y
  ofreciendo un reverso documentado y ejecutable.
- **RF-018**: `current_session.id` DEBE ser un UUID único generado por la base de datos o la
  aplicación, con una columna `created_at` propia. El sistema DEBE seguir manteniendo como máximo una
  fila y el campo `session_id` del documento DEBE coincidir con ese UUID; el literal
  `session-current` DEBE dejar de usarse.
- **RF-019**: La futura implementación de anotaciones (`RF-009`…`RF-011` de `002`) DEBE persistir
  altas, ediciones y borrados con `jsonb_set` o el operador `||` en SQL, sin leer y reescribir el
  documento completo desde la aplicación. Esta entrega solo fija la restricción de diseño.
- **RF-020**: `GET /api/session` DEBE devolver por defecto una vista resumen con audio, metadatos de
  transcripción, segmentos sin el array `words` y un contador `words_count` por segmento.
  `GET /api/session?view=full` DEBE devolver el documento completo actual.
- **RF-021**: El sistema DEBE exponer un endpoint que devuelva las palabras de un único segmento,
  identificado por su `id`, para que el editor las solicite bajo demanda.
- **RF-022**: `GET /api/session/audio` y el documento de exportación NO DEBEN cambiar. La exportación
  DEBE seguir incluyendo las marcas por palabra para cumplir `RF-016`.
- **RF-023**: El plan DEBE incluir una sección "Evolución prevista" con la hoja de ruta para
  multi-médico, multi-paciente y multi-sesión: normalización, RLS, enmienda mayor de la constitución,
  autenticación y auditoría. No se implementa en esta entrega.

### Requisitos no funcionales

- **RNF-006**: `pg_column_size(payload)` NO DEBE aumentar tras la migración y el tipo reportado por
  `information_schema` DEBE ser `jsonb`.
- **RNF-007**: La respuesta de `GET /api/session` en modo resumen DEBE ocupar menos del 25 % de los
  bytes de `?view=full` sobre la misma sesión de prueba.
- **RNF-008**: NO DEBE cambiarse el motor de base de datos, NO DEBEN añadirse servicios a
  `docker-compose.yml` ni colas/caché, y NO DEBE normalizarse el modelo en tablas de pacientes,
  médicos, segmentos o anotaciones.
- **RNF-009**: Las 49 pruebas de backend y las 5 de frontend existentes DEBEN seguir pasando.
- **RNF-010**: La migración DEBE ser idempotente, transaccional y reversible; una segunda ejecución
  no debe fallar ni duplicar datos.

### Entidades clave

- **Sesión persistida** (`current_session`): una fila con `id` UUID, `created_at`, `payload` `jsonb` y
  `updated_at`. Sigue representando la única sesión vigente.
- **Exportación persistida** (`current_export`): ranura única con `payload` `jsonb` y `exported_at`;
  conserva el documento completo con `words`.
- **Documento de sesión**: contenido lógico con `version`, `session_id`, `status`, `audio`,
  `transcription`, `annotations` y `operation`.
- **Vista resumen**: proyección de lectura del documento que sustituye `words` por `words_count` en
  cada segmento.
- **Palabras de un segmento**: lista bajo demanda con `text`, `start_time` y `end_time`.
- **Anotación**: entidad futura de la Fase 5; su escritura se hará por ruta JSON parcial.

Relaciones: una Sesión contiene como máximo un Audio y una Transcripción, y ninguna o varias
Anotaciones; una Transcripción contiene varios Segmentos; un Segmento contiene varias Palabras; cada
Anotación referencia exactamente un Segmento. La normalización de estas relaciones queda para v2.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-009**: `information_schema.columns` reporta `jsonb` para `current_session.payload` y
  `current_export.payload`, y `pg_column_size(payload)` no aumenta respecto al valor previo.
- **SC-010**: La fila existente sobrevive a la migración con audio, transcripción, palabras y
  anotaciones íntegros; una segunda ejecución no cambia el contenido ni duplica filas.
- **SC-011**: `GET /api/session` en modo resumen devuelve menos del 25 % de los bytes de
  `?view=full` sobre la misma sesión de prueba.
- **SC-012**: Ningún segmento de la vista resumen contiene la clave `words` y todos incluyen
  `words_count`; `?view=full` devuelve el documento completo anterior, con la única diferencia
  admitida de `session_id`, que pasa a ser el UUID de la fila (`RF-018`).
- **SC-013**: El endpoint de palabras devuelve exactamente las palabras del segmento solicitado y
  responde `404` si no existe.
- **SC-014**: Las 49 pruebas de backend y las 5 de frontend siguen pasando, y la exportación conserva
  las marcas por palabra.
- **SC-015**: El contrato de la Fase 5 describe una única escritura SQL con `jsonb_set`/`||` por
  operación de anotación, verificable por revisión y por prueba de contrato cuando se implemente.

## Supuestos

### Actores y usuarios

- **Profesional de salud**: único usuario conceptual; no hay cuentas ni roles en esta entrega.
- **Equipo de desarrollo**: consume la migración, la proyección y la restricción de diseño para la
  Fase 5.

### Fuera de alcance

- Cambiar PostgreSQL por MongoDB o cualquier base NoSQL.
- Normalizar el modelo en tablas de pacientes, médicos, sesiones, segmentos o anotaciones.
- Implementar las anotaciones de la Fase 5 (`T032`–`T038`) o la exportación (`T039`–`T042`).
- Implementar autenticación, RLS, auditoría o multiusuario.
- Modificar `GET /api/session/audio`, el documento de exportación o el contrato de la carga.
- Añadir Alembic, servicios, colas o caché.

### Decisiones provisionales

- La migración se implementa como SQL explícito idempotente dentro de `init_db()`; no se introduce
  Alembic en esta entrega (ver `research.md` D27).
- El identificador de la fila es un UUID nativo de PostgreSQL y `session_id` del documento es su
  espejo, escrito por la capa de persistencia.
- El nombre del archivo de audio (`current.<ext>`) se mantiene como ranura de almacenamiento y no se
  interpreta como identidad de sesión.
- `?view` acepta `summary` (por defecto) y `full`; cualquier otro valor se rechaza con `422`.

### Supuestos técnicos y dependencias

- PostgreSQL 16-alpine, SQLAlchemy 2.0.36 y psycopg 3.2.3, ya presentes en `002`.
- `gen_random_uuid()` está disponible en PostgreSQL 16 sin extensión adicional.
- El orden de ejecución es: primero `003` completa y después `T032`–`T038` de la Fase 5 de `002`.
- El documento de exportación se construye desde el documento completo, nunca desde la vista resumen.

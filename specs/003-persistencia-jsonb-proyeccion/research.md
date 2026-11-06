# Investigación técnica y decisiones — Persistencia JSONB y proyección de lectura

**Fase**: 0 (Outline & Research)
**Fecha**: 2026-11-06
**Plan**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md)

No quedan `NEEDS CLARIFICATION` en el contexto técnico. Este documento registra las decisiones de la
refactorización de persistencia y las alternativas descartadas.

---

## D27. Migración con SQL idempotente en `init_db()` en vez de Alembic

**Decisión**: la migración se implementa como SQL explícito, idempotente y transaccional, invocado
desde `init_db()` después de `Base.metadata.create_all()`. El reverso se documenta y se expone como
una función de bajada que no se ejecuta en el arranque.

**Razón**: el proyecto no tiene Alembic, solo dos tablas y un despliegue de un único contenedor. Las
migraciones son cambios de tipo y de clave primaria sobre una fila; añadir Alembic obligaría a
versionar el historial completo, un `env.py`, una tabla `alembic_version` y un paso de despliegue
nuevo para un beneficio que aquí no compensa.

**Alternativas consideradas**: Alembic (más ceremonia y una dependencia nueva para dos tablas);
migración manual fuera del arranque (rompe el arranque limpio de `docker compose up` y deja bases
desactualizadas); recrear las tablas y copiar datos (pierde la fila si falla y complica el reverso).

**Idempotencia**: cada paso consulta `information_schema`/`pg_catalog` antes de ejecutar DDL. La
migración completa se ejecuta dentro de una transacción; si un paso falla, no queda un esquema a
medias.

## D28. `jsonb` en vez de `json`

**Decisión**: `current_session.payload` y `current_export.payload` pasan a `jsonb`.

**Razón**: `jsonb` elimina espacios y claves duplicadas, permite indexación y, sobre todo, habilita
`jsonb_set` y el operador `||` para actualizaciones parciales (R3). El contenido lógico se conserva.

**Alternativas consideradas**: mantener `json` (no soporta las operaciones de escritura parcial que
exige la Fase 5 y no corrige el tipo); añadir una columna `jsonb` paralela (duplica el dato y el
riesgo de deriva).

**Nota de tamaño**: `jsonb` puede cambiar el orden de las claves y el espaciado. La comparación de
contenido se hace por valor JSON, no por bytes textuales; el criterio `pg_column_size` no debe
aumentar.

## D29. UUID nativo y `created_at` en vez de `id = 'current'`

**Decisión**: `current_session.id` es `uuid PRIMARY KEY DEFAULT gen_random_uuid()` y se añade
`created_at timestamptz NOT NULL DEFAULT now()`. La aplicación sigue manteniendo exactamente una fila:
crea una si la tabla está vacía y reutiliza la fila existente en cada reemplazo.

**Razón**: el literal `current` mezcla identidad con "ranura única". Un UUID con `created_at` permite
que el esquema evolucione a varias sesiones sin una migración destructiva y sin cambiar de motor.

**Alternativas consideradas**: mantener `id text = 'current'` (no hay identidad real); usar un
contador entero (expone orden y no es único entre entornos); imponer una restricción única sobre un
booleano `is_current` (vuelve a codificar el singleton en el esquema y habría que retirarla en v2).

**Singleton**: el principio III se mantiene como invariante de aplicación y de pruebas (`SELECT
count(*) FROM current_session <= 1`), no como una restricción estructural que impida la evolución.

## D30. `session_id` como espejo del `id` de la fila

**Decisión**: el documento conserva el campo `session_id`, pero su valor es siempre el UUID de la
fila. La capa de persistencia lo escribe al crear y al guardar; nunca se confía en el valor que
llegue dentro del `payload`.

**Razón**: evita romper el contrato y el documento exportado, que ya exponen `session_id`, y mantiene
un único origen de verdad (la columna `id`). La duplicación es controlada porque la aplicación
sobrescribe el campo antes de persistir.

**Alternativas consideradas**: eliminar `session_id` del documento y derivarlo solo en la respuesta
(obliga a proyectar también la exportación y cambia la forma del documento); dejar el literal
`session-current` (identificador falso y ambiguo con varias sesiones).

## D31. Retirar `session-current` y conservar `current.<ext>` como ranura de audio

**Decisión**: el literal `session-current` desaparece del documento inicial, del documento de carga,
de la exportación y de las pruebas. El archivo de audio sigue llamándose `current.<ext>`.

**Razón**: `session-current` era un identificador ficticio; el nombre del archivo, en cambio, es una
ranura de almacenamiento de un único audio vigente y no se expone como identidad. Cambiarlo
obligaría a migrar archivos sin aportar valor.

**Alternativas consideradas**: renombrar el audio a `<uuid>.<ext>` (migración de archivos y limpieza
extra); conservar `session-current` dentro del documento (contradice R2).

## D32. Vista resumen por defecto y `?view=full`

**Decisión**: `GET /api/session` devuelve `summary` si no se indica `view`; `?view=full` devuelve el
documento completo. `?view=summary` es explícito y equivalente al valor por defecto. Cualquier otro
valor responde `422 invalid_view`.

**Razón**: el consumo principal (lista de segmentos, reproductor, encabezado) no necesita `words`.
Mantener `full` como opción conserva compatibilidad y permite pruebas de equivalencia.

**Alternativas consideradas**: cambiar el endpoint a `/api/session/summary` (rompe el contrato y el
frontend actual); eliminar `words` de todas las respuestas (rompe la edición y la exportación).

## D33. Endpoint `GET /api/session/segments/{segment_id}/words`

**Decisión**: devuelve `200 {"segment_id": "...", "words": [...]}` con las palabras del segmento;
`404 segment_not_found` si no existe y `404 session_not_initialized` si no hay sesión.

**Razón**: es una ruta anidada explícita, no ambigua con `GET /api/session/audio`, y devuelve solo lo
necesario. El editor puede pedir un segmento concreto sin descargar el resto.

**Alternativas consideradas**: `GET /api/session/transcription/segments/{id}/words` (más verboso);
devolver todas las palabras con `?include=words` (vuelve a descargar el 81 %); incluir las palabras
en el resumen bajo demanda por query param (mezcla dos vistas en un solo contrato).

## D34. Proyección calculada en la aplicación, no en SQL

**Decisión**: la vista resumen se construye en Python a partir del documento leído, copiando cada
segmento y sustituyendo `words` por `words_count`. No se usa `jsonb` para eliminar `words` en SQL.

**Razón**: el documento ya se lee para la respuesta; la proyección es una transformación de forma y
debe ser fácil de probar. La base de datos sigue guardando el documento completo.

**Alternativas consideradas**: `payload #- '{transcription,segments}'` en SQL (tendría que reconstruir
el array y añadir `words_count`, más frágil); dos columnas (duplica el dato).

## D35. Compatibilidad del frontend con resumen y completo

**Decisión**: `TranscriptList` muestra `segment.words_count ?? segment.words?.length ?? 0`. El editor
sigue enviando solo `id`, `start_time`, `end_time` y `text`; el backend conserva o redistribuye las
palabras como hoy. Si en el futuro el editor necesita editar palabras, las pide al endpoint D33.

**Razón**: la carga (`POST /api/session/audio`) y la edición (`PUT /api/session/transcription`)
mantienen sus respuestas completas en esta entrega; la interfaz debe funcionar con ambas formas sin
romper las 5 pruebas existentes.

**Alternativas consideradas**: cambiar también las respuestas de mutación a resumen (mayor ahorro,
pero amplía el alcance y puede romper pruebas y contratos ya completados de `002`).

## D36. La exportación no usa la proyección

**Decisión**: `POST /api/session/export` sigue construyendo el documento desde el documento completo
y lo persiste en `current_export.payload` como `jsonb`.

**Razón**: `RF-016` exige que la exportación contenga la transcripción corregida, sus marcas de
tiempo y las anotaciones; las marcas por palabra forman parte de esas marcas. La reducción de
tráfico aplica a la lectura de trabajo, no al documento de conservación.

**Alternativas consideradas**: exportar el resumen (pierde `words` y contradice `RF-016`); exportar
desde una consulta `jsonb` (no aporta nada mientras el documento ya se lee).

## D37. Actualizaciones de anotaciones con `jsonb_set`/`||` (restricción futura)

**Decisión**: el contrato de la Fase 5 fija estas formas, sin implementarlas ahora:

- Alta: `payload = jsonb_set(payload, '{annotations}', COALESCE(payload->'annotations', '[]'::jsonb) || to_jsonb(:annotation), true)`.
- Edición: localizar el índice por `id` con `jsonb_array_elements(...) WITH ORDINALITY` y aplicar
  `jsonb_set(payload, ARRAY['annotations', idx::text], to_jsonb(:annotation), false)`.
- Borrado: reconstruir el array sin la anotación y asignarlo con `jsonb_set`.
- Estado: `jsonb_set(payload, '{status}', '"reviewed"', true)` en la misma sentencia.

**Razón**: evita el patrón `get_document()` + `save_document()` que reescribe 144 KB por anotación y
pierde la ventaja de `jsonb`.

**Alternativas consideradas**: leer y reescribir el documento (simple hoy, inviable con el tamaño
medido); normalizar `anotaciones` en una tabla (excluido por RNF-008 y por el alcance de v2).

## D38. Sin cambio de motor y sin normalización

**Decisión**: se mantiene PostgreSQL 16. No se crean tablas de pacientes, médicos, sesiones,
segmentos ni anotaciones.

**Razón**: el escenario futuro es relacional y exige integridad referencial y RLS; un NoSQL trasladaría
esas garantías a la aplicación. La normalización es una decisión de v2 y requiere una enmienda mayor
de la constitución, no un atajo dentro de esta refactorización.

**Alternativas consideradas**: MongoDB u otro NoSQL (rompe la hoja de ruta relacional); normalizar ya
(aumenta el alcance, exige migración de datos y cambia el modelo de la Fase 5).

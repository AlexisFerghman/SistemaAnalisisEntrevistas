# Modelo de datos — Persistencia JSONB y proyección de lectura

**Fase**: 1 (Design)
**Fecha**: 2026-11-06
**Plan**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md) · **Decisiones**: [research.md](./research.md)

La sesión sigue siendo un **único documento lógico** en `current_session.payload`. Esta feature no
normaliza el modelo: solo cambia el tipo de la columna, la identidad de la fila y la forma en que se
lee y se escribe el documento. El audio sigue fuera de la base de datos, en `/data/audio`.

## Esquema antes y después

### Antes (`002`)

```text
current_session
├── id         text PRIMARY KEY        -- siempre 'current'
├── payload    json NOT NULL           -- documento completo, incluidas words
└── updated_at timestamptz

current_export
├── id          text PRIMARY KEY       -- siempre 'current'
├── payload     json NOT NULL          -- documento completo, incluidas words
└── exported_at timestamptz
```

### Después (`003`)

```text
current_session
├── id         uuid PRIMARY KEY DEFAULT gen_random_uuid()
├── created_at timestamptz NOT NULL DEFAULT now()
├── payload    jsonb NOT NULL          -- documento completo, incluidas words
└── updated_at timestamptz

current_export
├── id          text PRIMARY KEY       -- ranura única; no es una identidad de sesión
├── payload     jsonb NOT NULL          -- documento completo, incluidas words
└── exported_at timestamptz
```

`current_export.id` se mantiene como literal `current` a propósito: representa una ranura de
almacenamiento, no una sesión. El `session_id` que contiene su documento sí es el UUID de la sesión
exportada.

## Migración

### Arriba (idempotente, dentro de una transacción)

La implementación consulta `information_schema.columns` y `pg_constraint` antes de cada paso. El SQL
conceptual es:

```sql
-- 1. Fecha de creación de la sesión
ALTER TABLE current_session
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();

-- 2. Tipo de las dos columnas de documento (solo si hoy son json)
ALTER TABLE current_session ALTER COLUMN payload TYPE jsonb USING payload::jsonb;
ALTER TABLE current_export  ALTER COLUMN payload TYPE jsonb USING payload::jsonb;

-- 3. Identidad real de la fila (solo si id sigue siendo text)
ALTER TABLE current_session
  ADD COLUMN IF NOT EXISTS session_uuid uuid DEFAULT gen_random_uuid();
UPDATE current_session
  SET session_uuid = gen_random_uuid()
  WHERE session_uuid IS NULL;

UPDATE current_session
  SET payload = jsonb_set(payload, '{session_id}', to_jsonb(session_uuid::text), true)
  WHERE payload->>'session_id' IS DISTINCT FROM session_uuid::text;

ALTER TABLE current_session DROP CONSTRAINT IF EXISTS current_session_pkey;
ALTER TABLE current_session DROP COLUMN id;
ALTER TABLE current_session RENAME COLUMN session_uuid TO id;
ALTER TABLE current_session ALTER COLUMN id SET NOT NULL;
ALTER TABLE current_session ADD PRIMARY KEY (id);
```

Si la tabla está vacía, no se crea ninguna fila: `ensure_current_session()` la crea después con un
UUID nuevo y `created_at` por defecto.

### Abajo (reverso documentado, no automático)

El reverso solo es válido mientras se mantenga el invariante de una sola fila.

```sql
ALTER TABLE current_session DROP CONSTRAINT IF EXISTS current_session_pkey;
ALTER TABLE current_session ADD COLUMN legacy_id text;
UPDATE current_session SET legacy_id = 'current';
ALTER TABLE current_session DROP COLUMN id;
ALTER TABLE current_session RENAME COLUMN legacy_id TO id;
ALTER TABLE current_session ALTER COLUMN id SET NOT NULL;
ALTER TABLE current_session ADD PRIMARY KEY (id);

UPDATE current_session
  SET payload = jsonb_set(payload, '{session_id}', to_jsonb('session-current'::text), true);

ALTER TABLE current_session DROP COLUMN IF EXISTS created_at;
ALTER TABLE current_session ALTER COLUMN payload TYPE json USING payload::json;
ALTER TABLE current_export  ALTER COLUMN payload TYPE json USING payload::json;
```

**Comprobaciones de la migración**:

1. Antes de migrar se guarda el `payload` como valor JSON y su `pg_column_size`.
2. Después se compara el valor JSON (no los bytes textuales) para asegurar que audio, transcripción,
   palabras y anotaciones siguen presentes. El único campo que cambia a propósito es `session_id`,
   que pasa de `session-current` al UUID de la fila; el resto del contenido debe ser igual.
3. Se comprueba que `information_schema` reporta `jsonb`.
4. Se comprueba que `pg_column_size` no aumentó.
5. Una segunda ejecución no modifica nada.

## Documento de sesión

| Campo | Tipo | Reglas en `003` |
|---|---|---|
| `version` | entero | Se mantiene en `1`; el cambio de tipo no altera el formato lógico |
| `session_id` | texto (UUID) | Espejo de `current_session.id`; la persistencia lo sobrescribe siempre |
| `status` | enumerado | Sin cambios: `empty`, `validating`, `processing`, `ready`, `reviewed`, `error` |
| `audio` | objeto o `null` | Sin cambios; `storage_ref` sigue apuntando a `current.<ext>` |
| `transcription` | objeto o `null` | Sin cambios; conserva `language`, `provider`, `retry_count` y `segments` |
| `annotations` | lista | Sin cambios en esta entrega; su escritura futura usa `jsonb_set` |
| `operation` | objeto o `null` | Sin cambios |
| `updated_at` | fecha ISO-8601 | Columna de la fila, no campo del documento |

**Documento inicial** (creado por la API si la tabla está vacía):

```json
{
  "version": 1,
  "session_id": "<uuid generado>",
  "status": "empty",
  "audio": null,
  "transcription": null,
  "annotations": [],
  "operation": null
}
```

## Vista resumen

`GET /api/session` (sin `view` o con `view=summary`) devuelve una copia del documento con esta forma:

```json
{
  "version": 1,
  "session_id": "5f0c9a7e-3d2b-4a91-8c44-1b2f0d6e7a10",
  "status": "ready",
  "audio": {
    "filename": "entrevista.wav",
    "mime_type": "audio/wav",
    "size_bytes": 3210000,
    "duration_seconds": 721.4,
    "storage_ref": "current.wav"
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
        "text": "Texto del segmento.",
        "words_count": 6
      }
    ]
  },
  "annotations": [],
  "operation": null
}
```

Reglas de la proyección:

1. `transcription.segments[*].words` se elimina de la copia.
2. Cada segmento recibe `words_count` con la longitud del array original (`0` si no hay marcas).
3. `annotations` se conserva completa: es pequeña y la columna 3 la necesita.
4. `audio`, `status`, `version`, `session_id` y `operation` se conservan.
5. El documento persistido no se modifica; la proyección es solo de lectura.
6. `?view=full` devuelve el documento sin transformar, incluidas las `words`.

## Palabras de un segmento

`GET /api/session/segments/{segment_id}/words` devuelve:

```json
{
  "segment_id": "segment-001",
  "words": [
    { "text": "Texto", "start_time": 0.0, "end_time": 0.9 }
  ]
}
```

- Si el segmento no existe: `404 segment_not_found`.
- Si no hay sesión inicializada: `404 session_not_initialized`.
- Si el segmento existe pero no tiene marcas: `200` con `words: []`.
- El endpoint lee solo la transcripción necesaria; no devuelve el resto del documento.

## Escritura parcial de anotaciones (Fase 5, no implementada aquí)

El contrato de la Fase 5 debe usar una única sentencia por operación. Las formas de referencia son:

### Alta

```sql
UPDATE current_session
SET payload = jsonb_set(
      payload,
      '{annotations}',
      COALESCE(payload->'annotations', '[]'::jsonb) || %(annotation)s::jsonb,
      true
    ),
    updated_at = now()
WHERE id = %(session_id)s
RETURNING payload->'annotations'->-1 AS annotation;
```

### Edición

```sql
WITH target AS (
  SELECT (ordinality - 1)::int AS idx
  FROM current_session,
       LATERAL jsonb_array_elements(payload->'annotations') WITH ORDINALITY AS a(annotation, ordinality)
  WHERE current_session.id = %(session_id)s
    AND a.annotation->>'id' = %(annotation_id)s
)
UPDATE current_session
SET payload = jsonb_set(payload, ARRAY['annotations', target.idx::text], %(annotation)s::jsonb, false),
    updated_at = now()
FROM target
WHERE current_session.id = %(session_id)s
RETURNING payload->'annotations'->target.idx AS annotation;
```

### Borrado

```sql
UPDATE current_session
SET payload = jsonb_set(
      payload,
      '{annotations}',
      COALESCE((
        SELECT jsonb_agg(a.annotation)
        FROM jsonb_array_elements(payload->'annotations') AS a(annotation)
        WHERE a.annotation->>'id' <> %(annotation_id)s
      ), '[]'::jsonb),
      true
    ),
    updated_at = now()
WHERE id = %(session_id)s
  AND payload @> jsonb_build_object(
        'annotations', jsonb_build_array(jsonb_build_object('id', %(annotation_id)s))
      )
RETURNING payload->'annotations' AS annotations;
```

### Validación dirigida del segmento

```sql
SELECT 1
FROM current_session,
     LATERAL jsonb_array_elements(payload->'transcription'->'segments') AS s(segment)
WHERE current_session.id = %(session_id)s
  AND s.segment->>'id' = %(segment_id)s
  AND (s.segment->>'start_time')::numeric <= %(start_time)s
  AND (s.segment->>'end_time')::numeric >= %(end_time)s;
```

Reglas que la Fase 5 debe cumplir:

1. Ninguna ruta de anotaciones llama a `get_document()` + `save_document()`.
2. El estado `reviewed` se actualiza en la misma sentencia con `jsonb_set(payload, '{status}', ...)`.
3. Las validaciones de longitud y rango se hacen en el servicio antes de la sentencia; la pertenencia
   al segmento se comprueba con la consulta dirigida.
4. El array `annotations` nunca queda `null`: se usa `COALESCE(..., '[]'::jsonb)`.

## Invariantes

1. `SELECT count(*) FROM current_session` es `0` o `1` en todo momento (principio III, `RF-012`).
2. `current_session.id` es un UUID y `payload->>'session_id'` coincide con él.
3. `current_session.payload` y `current_export.payload` son `jsonb`.
4. El documento persistido conserva `transcription.segments[*].words`; solo la vista resumida lo
   sustituye por `words_count`.
5. Toda anotación referencia un segmento existente (invariante heredado de `002`).
6. `GET /api/session/audio` y el documento exportado no dependen de la proyección resumida.
7. La migración es idempotente y su reverso deja el esquema anterior sin pérdida de contenido.

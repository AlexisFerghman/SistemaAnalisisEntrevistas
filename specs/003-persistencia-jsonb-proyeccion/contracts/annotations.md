# Contrato de persistencia parcial de anotaciones (Fase 5 de `002`)

**Estado**: restricción de diseño. No se implementa en `003`.
**Referencias**: `RF-009`…`RF-011` y `RF-016` de `002`; `RF-019` y `SC-015` de `003`.

La Fase 5 (`T032`–`T038` de `002`) debe conservar los códigos y validaciones del contrato HTTP de
`002`, pero cada operación de escritura se resuelve con **una sola sentencia `UPDATE`** sobre
`current_session.payload`, usando `jsonb_set` o el operador `||`. No se permite leer el documento
completo en la aplicación y volver a escribirlo.

## Reglas obligatorias

1. Una sentencia `UPDATE` por alta, edición o borrado.
2. `jsonb_set` o `||` sobre `payload->'annotations'`.
3. Ninguna ruta de anotaciones llama a `get_document()` + `save_document()`.
4. La pertenencia del segmento se valida con una consulta dirigida o `jsonb_path_exists`.
5. `status = reviewed` se actualiza en la misma sentencia.
6. El array `annotations` nunca queda `null`: se usa `COALESCE(..., '[]'::jsonb)`.
7. No se crean tablas `anotaciones` ni `segmentos` (RNF-008).

## Alta

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

La aplicación valida antes de ejecutar:

- Texto de 1 a 500 caracteres Unicode.
- `segment_id` existente y rango contenido en el segmento.
- Estado `ready` o `reviewed`.

## Edición

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

Si `target` no devuelve filas, la ruta responde `404 annotation_not_found`.

## Borrado

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

Si no se actualiza ninguna fila, la ruta responde `404 annotation_not_found`.

## Validación dirigida del segmento

```sql
SELECT 1
FROM current_session,
     LATERAL jsonb_array_elements(payload->'transcription'->'segments') AS s(segment)
WHERE current_session.id = %(session_id)s
  AND s.segment->>'id' = %(segment_id)s
  AND (s.segment->>'start_time')::numeric <= %(start_time)s
  AND (s.segment->>'end_time')::numeric >= %(end_time)s;
```

## Verificación en la Fase 5

Cuando se implemente `T036`, la prueba de contrato debe comprobar:

- Que el número de sentencias de escritura por operación es uno.
- Que el documento completo no se lee ni se reescribe.
- Que una anotación de 501 caracteres no llega a la base de datos.
- Que editar o borrar no modifica el audio (`RF-011`).
- Que `status` pasa a `reviewed` en la misma sentencia.

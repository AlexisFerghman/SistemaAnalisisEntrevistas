# Validación de la feature 003 — Persistencia JSONB y proyección de lectura

**Fecha**: 2026-11-06
**Feature**: `003-persistencia-jsonb-proyeccion`

Este documento registra la línea base, las mediciones de aceptación y las comprobaciones manuales de
la refactorización. No sustituye a las pruebas automatizadas.

## Línea base (antes de la implementación)

| Suite | Comando | Resultado |
|---|---|---|
| Backend | `docker compose exec -T api pytest -q` | 49 passed, 1 warning |
| Frontend | `docker compose exec -T frontend npm test` | 5 passed (1 archivo) |

## Criterios de aceptación

| Criterio | Medición | Estado |
|---|---|---|
| Tipo `jsonb` en `current_session.payload` y `current_export.payload` | `information_schema`: `jsonb` en ambas | PASS |
| `pg_column_size(payload)` no aumenta | 140 826 bytes (`json` legado) → 136 081 bytes (`jsonb`) | PASS |
| Resumen < 25 % de los bytes de `?view=full` | 134 682 / 693 105 bytes = 19,43 % | PASS |
| Resumen sin `words` y con `words_count` | Verificado en pruebas unitarias, de integración y de contrato | PASS |
| Fila existente íntegra tras la migración | `test_schema_migration.py` y `test_schema_rollback.py` | PASS |
| Suite backend en verde | 74 passed (49 existentes + 25 nuevas) | PASS |
| Suite frontend en verde | 7 passed (5 existentes + 2 nuevas) | PASS |
| Restricción de anotaciones documentada para la Fase 5 | `contracts/annotations.md` | PASS |

**Sesión de medición**: documento sintético de 60 segmentos y 9 000 palabras, equivalente al orden de
magnitud de la sesión real de ~12 min (144 818 bytes, 81 % en `words`).

## Comprobaciones de la Fase 5 (US3)

La Fase 5 de `002` (`T032`–`T038`), implementada con `backend/app/services/annotations.py` y
`backend/app/api/annotations.py`:

- [x] Una sola sentencia `UPDATE` por operación de anotación.
- [x] Uso de `jsonb_set` o del operador `||` sobre `payload->'annotations'`.
- [x] Ninguna ruta de anotaciones llama a `get_document()` + `save_document()`.
- [x] Validación de pertenencia al segmento con consulta dirigida o `jsonb_path_exists`.
- [x] Sin tablas nuevas de anotaciones ni cambios en `docker-compose.yml`.
- [x] `status = reviewed` se actualiza en la misma sentencia.

Verificación de esta entrega: `grep -c "UPDATE current_session"` devuelve 3 (alta, edición y borrado,
una por operación) y no hay ninguna referencia a `get_document`/`save_document` en las rutas de
anotaciones. `git diff docker-compose.yml` no muestra cambios y la base sigue teniendo solo
`current_session` y `current_export`.

Suites tras la Fase 5: **102 pruebas de backend** (74 previas + 28 nuevas) y **12 de frontend**
(7 previas + 5 nuevas).

## Evolución prevista (US4)

- [x] La sección "Evolución prevista" de `plan.md` cubre normalización, RLS, enmienda `1.0.0 → 2.0.0`,
  autenticación, auditoría y compatibilidad de despliegue.
- [x] `specs/002-mvp-analisis-inicial/plan.md` remite a la hoja de ruta de `003`.
- [x] La hoja de ruta no introduce requisitos implementables en `003`.

## Verificación en vivo

Sobre la API en ejecución, con un documento sintético de 6 segmentos y 40 palabras por segmento:

| Petición | Resultado |
|---|---|
| `PUT /api/session` con el documento completo | `200`, `session_id` UUID |
| `GET /api/session` | `200`, 4 446 bytes |
| `GET /api/session?view=full` | `200`, 18 990 bytes |
| Relación resumen/full | 23,4 % (< 25 %) |
| `GET /api/session/segments/segment-003/words` | `200`, 40 palabras |
| `GET /api/session?view=bad` | `422 invalid_view` |

La sesión se dejó de nuevo en estado `empty` al terminar la comprobación.

## Resultado final

La feature `003` queda implementada sin tocar las tareas pendientes de `002`. La Fase 5 de `002`
(`T032`–`T038`) puede empezar sobre el esquema `jsonb` y debe respetar la restricción de escritura
parcial documentada.

### Comandos de verificación

```bash
docker compose exec -T api pytest -q
docker compose exec -T frontend npm test
```

### Nota sobre `docker-compose.yml`

El servicio `adminer` ya estaba presente en el árbol de trabajo antes de esta implementación. La
feature `003` no modificó `docker-compose.yml` ni añadió dependencias.

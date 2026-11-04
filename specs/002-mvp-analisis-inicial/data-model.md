# Modelo de datos — MVP de análisis inicial

**Fase**: 1 (Design)
**Fecha**: 2026-11-02
**Plan**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md) · **Decisiones**: [research.md](./research.md)

La sesión se persiste como un **único documento lógico** en la columna `payload` (JSON) de la tabla
`current_session`, con una sola fila de identificador fijo `current`. El audio no va dentro del
documento: se guarda como archivo en `/data/audio` y el documento conserva una referencia relativa.
No se almacenan identidades de pacientes ni datos clínicos reales.

## Relaciones

```text
Sesión (1) ──── (0..1) Audio
      │
      ├──── (0..1) Transcripción ──── (N) Segmento ──── (N) Palabra
      │
      └──── (0..N) Anotación ──── (1) Segmento

Exportación (1) ──── copia consolidada de la Sesión vigente
```

## Sesión

| Campo | Tipo | Reglas |
|---|---|---|
| `version` | entero | Siempre `1`; permite evolucionar el formato sin mezclar estructuras |
| `session_id` | texto | Siempre `session-current`; identifica la sesión actual, no a una persona ni a una carga histórica |
| `status` | enumerado | `empty`, `validating`, `processing`, `ready`, `reviewed`, `error` |
| `audio` | objeto o `null` | `null` únicamente en estado `empty` o tras un `error` sin audio válido |
| `transcription` | objeto o `null` | `null` mientras no exista transcripción confirmada |
| `annotations` | lista | Vacía por defecto; nunca `null` |
| `operation` | objeto | Estado de la operación en curso: `started_at`, `cancel_requested` |
| `updated_at` | fecha ISO-8601 | Gestionada por la base de datos |

**Documento inicial**, creado por la API al arrancar si no existe:

```json
{
  "version": 1,
  "session_id": "session-current",
  "status": "empty",
  "audio": null,
  "transcription": null,
  "annotations": [],
  "operation": null
}
```

## Audio

| Campo | Tipo | Reglas |
|---|---|---|
| `filename` | texto | Nombre original declarado por el usuario; solo informativo |
| `mime_type` | texto | Debe corresponder a `audio/mpeg` o `audio/wav` |
| `size_bytes` | entero | Mayor que 0 y menor o igual a 125 829 120 (120 MB) |
| `duration_seconds` | decimal | Mayor que 0; se lee del archivo, no se impone tope |
| `storage_ref` | texto | Ruta **relativa** dentro de `/data/audio`; nunca una ruta absoluta del host |

Reglas adicionales:

- La validación comprueba extensión, MIME declarado y estructura real del audio (no solo el nombre).
- El archivo vive en `./data/audio` del host, montado en `/data/audio` dentro del contenedor.
- El audio original nunca se sobrescribe con una versión editada.
- Si `storage_ref` apunta a un archivo inexistente, la sesión pasa a `error` y el documento se
  conserva para diagnóstico; no se sustituye en silencio por una sesión vacía.

## Transcripción

| Campo | Tipo | Reglas |
|---|---|---|
| `language` | texto | `es` |
| `provider` | texto | `local` o `fake` (solo pruebas) |
| `retry_count` | entero | `0` o `1`; el adaptador reintenta una única vez |
| `segments` | lista | Al menos un segmento; ordenados y sin solapamientos |

## Segmento

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | texto | Único dentro de la transcripción; estable frente a ediciones de texto |
| `start_time` | decimal | ≥ 0 y menor que `end_time` |
| `end_time` | decimal | ≤ `duration_seconds` del audio |
| `text` | texto | No vacío |
| `words` | lista | Puede estar vacía solo si el motor no devolvió marcas por palabra |

Los segmentos deben estar ordenados por `start_time` y no solaparse entre sí.

## Palabra

| Campo | Tipo | Reglas |
|---|---|---|
| `text` | texto | No vacío |
| `start_time` | decimal | ≥ `start_time` del segmento y menor que su `end_time` |
| `end_time` | decimal | Mayor que su `start_time` y ≤ `end_time` del segmento |

## Anotación

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | texto | Único dentro de la sesión |
| `text` | texto | Entre 1 y 500 caracteres, contando caracteres Unicode, no bytes |
| `segment_id` | texto | Debe referenciar un segmento existente |
| `start_time` | decimal | ≥ `start_time` del segmento referenciado |
| `end_time` | decimal | Mayor que `start_time` y ≤ `end_time` del segmento referenciado |

## Exportación

| Campo | Tipo | Reglas |
|---|---|---|
| `exported_at` | fecha ISO-8601 | Momento de la exportación |
| `document` | objeto | Copia consolidada de la sesión: audio o sus metadatos, transcripción corregida, marcas de tiempo y anotaciones |

Se persiste en una tabla de **una sola ranura** (`current_export`, fila `current`), sobrescrita en cada
exportación. Se elimina cuando se confirma una nueva sesión, para que la base de datos contenga datos de
una única sesión en todo momento (principio III). Alternativa descartada: conservar exportaciones
indefinidamente, que reintroduce un historial de sesiones fuera de alcance.

## Máquina de estados

```text
empty ──carga──▶ validating ──válido──▶ processing ──ok──▶ ready ──edición──▶ reviewed
  ▲                   │                     │                 │                  │
  │                   │ inválido            │ fallo/cancelación│                  │
  └───────────────────┴─────────────────────┴─────────────────┴──────────────────┘
                          (se conserva la sesión anterior; status vuelve a su valor previo)
```

| Transición | Disparador | Efecto persistido |
|---|---|---|
| `empty` → `validating` | Se recibe un archivo | Se registra `operation.started_at` |
| `validating` → `validating` | El archivo no cumple formato, tamaño o estructura | Sin cambios en audio, transcripción ni anotaciones |
| `validating` → `processing` | El archivo es válido | `operation.cancel_requested = false` |
| `processing` → `ready` | La transcripción termina y el reemplazo se confirma | Nuevo audio promovido, nuevo documento |
| `processing` → estado previo | Fallo del motor, error de persistencia o cancelación | Temporales eliminados, sesión anterior intacta |
| `ready` → `reviewed` | El usuario guarda una edición de texto, marcas o anotaciones | Documento actualizado |
| `reviewed` → `reviewed` | Ediciones posteriores | Documento actualizado |
| cualquiera → `error` | El audio referenciado no existe o el documento es ilegible | Documento conservado para diagnóstico |

Invariantes que deben cumplirse al confirmar una sesión:

1. Existe como máximo una fila en `current_session` y su `session_id` es `session-current`.
2. Existe como máximo un archivo de audio vigente referenciado por `storage_ref`.
3. Toda anotación referencia un segmento existente.
4. Todos los segmentos caben dentro de `duration_seconds`.
5. No queda ningún archivo temporal tras una confirmación, un fallo o una cancelación.
6. `status = processing` solo puede observarse mientras una operación está activa en el proceso.

## Flujo de reemplazo atómico

1. Validar el nuevo audio sin modificar la sesión actual.
2. Enviar el audio al adaptador de transcripción y recibir una respuesta válida.
3. Escribir el audio como temporal y normalizar el documento nuevo en una ubicación temporal.
4. Verificar que el documento y el audio temporales pueden leerse.
5. Promover el audio temporal a `current.<ext>` y persistir el nuevo documento; la sesión se considera
   confirmada solo cuando ambos pasos terminan correctamente.
6. Tras confirmar, eliminar el audio anterior y la exportación vigente. Si la limpieza falla, la sesión
   nueva permanece activa y el residuo queda pendiente de limpieza.
7. Ante cualquier fallo o cancelación previa a la confirmación: eliminar temporales, restaurar la
   referencia anterior si fue necesario y conservar la sesión previa.

## Reglas de validación derivadas de la spec

| Regla | Origen |
|---|---|
| Extensión `.mp3` o `.wav`, MIME coherente, estructura de audio legible | `RF-001`, `RF-002` |
| Tamaño ≤ 120 MB | `RF-001`, `RF-002` |
| Anotación de 1 a 500 caracteres | `RF-010` |
| Anotación vinculada a un segmento existente y a un rango temporal válido | `RF-009` |
| `start_time` < `end_time`, sin solapamientos, dentro de la duración | `RF-008`, `RNF-004` |
| Una sola sesión; sin colección de sesiones anteriores | `RF-012`, `RF-013` |
| La sesión anterior sobrevive a fallo o cancelación | `RF-014`, `RF-015` |
| El audio original no se modifica al editar o anotar | `RF-011` |

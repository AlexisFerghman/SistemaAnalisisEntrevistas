# Data Model: Experiencia de transcripción continua

**Fase**: 1 (Design) · **Fecha**: 2026-11-07 · **Plan**: [plan.md](./plan.md) · **Spec**: [spec.md](./spec.md)

Esta feature **no introduce cambios de persistencia**. El modelo describe entidades y estados de
interfaz que se derivan de los datos ya existentes de sesión, transcripción y anotaciones.

## Entidades de interfaz

### Segmento visible

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | texto | Identidad estable del segmento; no cambia al editar |
| `start_time` | decimal | ≥ 0 y menor que `end_time` |
| `end_time` | decimal | Mayor que `start_time` y dentro de la duración del audio |
| `text` | texto | No vacío para guardar |
| `words` / `words_count` | lista / entero | Se conserva o redistribuye al editar; no se inventa |

**Uso**: se muestra en el flujo continuo y en la vista de edición.

### Bloque de edición

| Campo | Tipo | Reglas |
|---|---|---|
| `segment_id` | texto | Referencia al segmento visible |
| `draft_text` | texto | Texto editable; no puede quedar vacío al guardar |
| `draft_start_time` | decimal | Validación de rango y solapamiento |
| `draft_end_time` | decimal | Validación de rango y duración |
| `dirty` | booleano | Indica cambios locales antes de guardar |

**Invariante**: cada bloque conserva la identidad del segmento; el guardado envía la lista completa.

### Observación

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | texto | Identificador existente de la anotación |
| `text` | texto | Entre 1 y 500 caracteres |
| `segment_id` | texto | Debe existir en la transcripción |
| `start_time` | decimal | Dentro del segmento referenciado |
| `end_time` | decimal | Mayor que `start_time` y dentro del segmento |

### Grupo de observaciones

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | texto | Identificador del grupo en la interfaz |
| `observations` | lista | Una o más observaciones |
| `anchor_time` | decimal | Tiempo representativo del grupo |
| `count` | entero | Igual al tamaño de `observations` |
| `position_ratio` | decimal | Posición horizontal normalizada en la waveform |

**Regla de agrupación**: dos o más marcadores cuya distancia horizontal sea ≤ 14 px forman un grupo.
Un grupo puede contener una sola observación y aun así usar el mismo popover.

### Perfil de waveform

| Campo | Tipo | Reglas |
|---|---|---|
| `session_seed` | texto | Identificador estable de la sesión |
| `peaks` | lista de decimales | Amplitud real normalizada |
| `fallback` | booleano | Verdadero si no se pudo decodificar el audio |

**Invariante**: el mismo `session_seed` y la misma lista de `peaks` producen el mismo perfil visual.

### Estado del seguimiento

| Estado | Significado |
|---|---|
| `following` | La transcripción sigue automáticamente al segmento activo |
| `paused_manual` | El usuario interrumpió el seguimiento con scroll manual |
| `paused_external` | “Ver fragmento” o revelado externo pausó el seguimiento |
| `resuming` | Quedan menos de 5 s para reanudar automáticamente |

**Transiciones**:

```text
following ──scroll manual──▶ paused_manual ──5 s──▶ following
following ──Ver fragmento──▶ paused_external ──5 s──▶ following
paused_manual ──Volver al audio──▶ following
paused_external ──Volver al audio──▶ following
```

### Estado del popover

| Estado | Significado |
|---|---|
| `closed` | No se muestra información |
| `open_hover` | Abierto por puntero sobre marcador o popover |
| `open_focus` | Abierto por foco de teclado |
| `closing_grace` | Puntero fuera; se cierra tras 150 ms si no vuelve a entrar |

**Invariante**: el popover no atrapa el foco ni bloquea la página.

## Relaciones

```text
Sesión actual
  └── Transcripción
        └── Segmento visible (1..N)
              ├── Bloque de edición (0..1 por segmento)
              └── Observación (0..N)

Observación (0..N) ──agrupación visual──▶ Grupo de observaciones
Perfil de waveform (1 por sesión)
```

## Reglas de validación

| Regla | Origen |
|---|---|
| El texto del segmento no puede quedar vacío | `RF-036`, validación existente de `002` |
| `start_time < end_time`, sin solapamientos y dentro de la duración | Validación existente de `002` |
| La observación conserva su vínculo con el segmento | `RF-034`, principio IV |
| El grupo contiene todas las observaciones de la zona | `RF-031`, `RF-034` |
| “Ver fragmento” no cambia `currentTime` | `RF-035`, `RF-028` |
| El perfil de waveform es estable por sesión | `RF-037` |

## Invariantes de interfaz

1. El scroll y el clic sobre texto no modifican la reproducción.
2. El `seek` solo ocurre por chip de tiempo, botón play o waveform.
3. El popover muestra todas las observaciones del grupo y nunca inventa datos.
4. El auto-scroll no re-renderiza toda la transcripción en cada actualización de tiempo.
5. La edición conserva `id`, `start_time`, `end_time` y el vínculo con las marcas por palabra.
6. El audio original no se modifica.
7. Se conservan el banner, la confirmación de datos sintéticos y las etiquetas actuales.

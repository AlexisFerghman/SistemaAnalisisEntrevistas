# Contrato de interfaz — Experiencia de transcripción continua

**Feature**: `005-transcripcion-continua` · **Fecha**: 2026-11-07
**Spec**: [spec.md](../spec.md) · **Plan**: [plan.md](../plan.md) · **API**: [api.md](./api.md)

Esta feature no cambia la estructura general de la pantalla ni elimina la columna de explicabilidad.
Se mantienen el banner, la confirmación de datos sintéticos y las etiquetas actuales.

## Layout

- Se conserva la pantalla de trabajo con header, módulo de audio y tres columnas.
- La columna de explicabilidad permanece visible y etiquetada como vista previa.
- La columna de anotaciones conserva sus contadores, acciones y exportación JSON.
- No se elimina ningún aviso obligatorio.

## Transcripción continua

### Estructura

- La transcripción se muestra en un único contenedor vertical con scroll propio.
- Cada segmento es un bloque visualmente identificable con su timestamp.
- El segmento activo se resalta con fondo y borde.
- Se mantienen visibles al menos un segmento anterior y dos posteriores cuando existan.

### Auto-scroll

- Mientras el audio avanza, el contenedor se desplaza suavemente para mantener visible el segmento activo.
- El auto-scroll **no** modifica `currentTime`, no pausa el audio y no hace `seek`.
- Si el usuario usa rueda, touch, barra de scroll, arrastre o teclado, el seguimiento se pausa.
- A los 5 segundos, el seguimiento se reanuda automáticamente.
- Mientras está pausado, aparece “Volver al audio”, que reanuda el seguimiento sin hacer `seek`.
- Con `prefers-reduced-motion`, el desplazamiento es instantáneo o se desactiva.

### Controles de `seek`

| Control | Acción |
|---|---|
| Chip de tiempo del segmento | `seek` al `start_time` |
| Botón con símbolo de play | `seek` al `start_time` y reproduce |
| Clic o arrastre sobre la waveform | `seek` al instante correspondiente |
| Clic sobre el texto del segmento | No hace `seek` |
| Scroll de la transcripción | No hace `seek` |
| Avance automático del audio | No hace `seek` |

## Marcadores de observaciones

### Agrupación

- Los marcadores cuya distancia horizontal sea ≤ 14 px se agrupan en un único marcador.
- El marcador agrupado muestra un contador visible.
- La agrupación se recalcula al cambiar el tamaño de la waveform.
- Un marcador con una sola observación usa el mismo popover que un grupo.

### Popover

- Se abre con hover sobre el marcador o con foco de teclado, sin clic obligatorio.
- No es modal: no usa backdrop, no atrapa el foco y no bloquea la página.
- Permanece abierto mientras el puntero esté en el marcador o en el popover.
- Tiene una tolerancia de 150 ms al cruzar entre marcador y popover.
- Se cierra al salir de esa zona, con el botón de cerrar, con `Esc` o al tocar fuera en táctil.

### Contenido

Cada observación muestra:

- hora o timestamp,
- texto completo de la observación,
- referencia al segmento asociado.

El popover es de solo lectura. No permite editar ni eliminar; esas acciones siguen en el chip del
segmento.

### “Ver fragmento”

- Desplaza la transcripción hasta el segmento asociado.
- No cambia `currentTime` ni el estado de reproducción.
- Pausa el auto-scroll durante 5 segundos.

## Edición unificada

- Al entrar en edición, se muestra la transcripción completa en un único flujo de bloques.
- Cada bloque conserva separador visual, timestamp y campos editables.
- El texto no se trunca ni se colapsa.
- Se mantienen las validaciones actuales: texto vacío, rangos negativos, invertidos, solapados o fuera
  de la duración.
- Al guardar se envía la lista completa de segmentos y se conserva la identidad de cada uno.
- Las marcas por palabra se conservan o se redistribuyen como hasta ahora.
- El audio original no se modifica.

## Waveform

- Conserva la amplitud real del audio.
- Aplica una variación determinista derivada de un identificador estable de la sesión.
- La misma sesión conserva el mismo perfil al recargar.
- Dos sesiones distintas producen perfiles visualmente distintos.
- Si la decodificación falla, se usa un perfil de respaldo estable y la reproducción sigue funcionando.
- El playhead, los ticks y el `seek` siguen correspondiendo a la duración real.

## Accesibilidad

- Los marcadores, el popover y el botón de cerrar son alcanzables con `Tab`.
- El popover se abre con foco o `Enter`/`Espacio`.
- `Esc` cierra el popover y devuelve el foco al marcador.
- Las observaciones se anuncian con hora y texto.
- El auto-scroll respeta `prefers-reduced-motion`.
- Ningún control depende solo del color.

## Criterios de aceptación visual

1. La transcripción se lee como un flujo continuo, no como tarjetas aisladas.
2. El segmento activo permanece visible mientras el audio avanza.
3. El scroll manual pausa el seguimiento y “Volver al audio” lo reanuda.
4. El clic sobre el texto no mueve la reproducción.
5. El chip de tiempo y el botón play sí mueven la reproducción.
6. Varias observaciones cercanas se ven como un único marcador con contador.
7. El popover muestra todas las observaciones y se cierra de forma no restrictiva.
8. “Ver fragmento” desplaza la transcripción sin mover el audio.
9. La edición muestra todos los segmentos y mantiene las validaciones.
10. La waveform cambia entre sesiones pero es estable en la misma sesión.
11. El banner, la confirmación y las etiquetas actuales siguen visibles.

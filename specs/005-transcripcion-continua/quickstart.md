# Quickstart de validación — Experiencia de transcripción continua

**Propósito**: comprobar de extremo a extremo las mejoras de la feature `005` sin leer código de
implementación.
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Contratos**: [contracts/ui.md](./contracts/ui.md)

## Requisitos previos

- Docker Engine y Docker Compose.
- Una sesión sintética cargada y transcrita, con varios segmentos y al menos dos observaciones.
- Navegador de escritorio actualizado.

## Arranque

```bash
docker compose up --build
```

Abrir `http://localhost:5173`.

## Pruebas automatizadas

```bash
docker compose exec frontend npm test
docker compose exec api pytest -q
```

**Esperado**: todas las pruebas de frontend en verde y el backend sin regresiones.

---

## Escenario 1 — Flujo continuo y segmento activo

1. Abrir una sesión transcrita.
2. Pulsar reproducir.
3. Observar la transcripción durante al menos 30 segundos.

**Esperado**:

- La transcripción se lee como un flujo continuo.
- El segmento activo se resalta y permanece visible.
- Se ven al menos un segmento anterior y dos posteriores cuando existen.
- La reproducción no se corta ni salta por el desplazamiento.

## Escenario 2 — Scroll manual y reanudación

1. Con el audio reproduciéndose, hacer scroll manual en la transcripción.
2. Comprobar que el seguimiento se detiene.
3. Esperar 5 segundos.

**Esperado**:

- El audio sigue sonando y no cambia de posición.
- El seguimiento se pausa.
- A los 5 segundos, la transcripción vuelve a seguir al audio.
- “Volver al audio” reanuda antes de los 5 segundos sin hacer `seek`.

## Escenario 3 — Controles de `seek`

1. Hacer clic sobre el texto de un segmento.
2. Pulsar el chip de tiempo de un segmento.
3. Pulsar el botón con símbolo de play de otro segmento.
4. Hacer clic y arrastrar sobre la waveform.

**Esperado**:

- El clic sobre el texto no mueve la reproducción.
- El chip de tiempo salta al inicio del segmento.
- El botón play salta al inicio y comienza a reproducir.
- El clic y el arrastre sobre la waveform saltan al instante correspondiente.

## Escenario 4 — Observaciones agrupadas

1. Crear o localizar al menos tres observaciones cercanas en el tiempo.
2. Mirar la barra de reproducción.

**Esperado**:

- Se muestra un único marcador con un contador.
- Al pasar el puntero, aparece un popover con las tres observaciones.
- El popover muestra hora, texto y segmento.
- Una observación aislada usa el mismo popover.

## Escenario 5 — Cierre no restrictivo del popover

1. Abrir el popover de un marcador.
2. Mover el puntero del marcador al popover.
3. Salir de la zona.
4. Volver a abrirlo y pulsar el botón de cerrar.
5. Volver a abrirlo y pulsar `Esc`.
6. En una pantalla táctil, tocar fuera.

**Esperado**:

- El popover permanece abierto al cruzar del marcador al popover.
- Se cierra al salir de la zona.
- Se cierra con el botón y con `Esc`.
- En táctil, se cierra al tocar fuera.
- La página sigue siendo interactiva mientras el popover está abierto.

## Escenario 6 — “Ver fragmento” sin `seek`

1. Abrir el popover de una observación.
2. Pulsar “Ver fragmento”.

**Esperado**:

- La transcripción se desplaza hasta el segmento asociado.
- La posición del audio no cambia.
- El auto-scroll se pausa durante 5 segundos.

## Escenario 7 — Edición unificada

1. Entrar en modo edición.
2. Recorrer la transcripción completa.
3. Modificar un texto y guardar.
4. Intentar guardar un texto vacío y un rango fuera de la duración.

**Esperado**:

- Todos los segmentos se ven en un único flujo con separadores y timestamps.
- El texto no se trunca.
- La edición válida se guarda y el audio no cambia.
- Los textos vacíos y rangos inválidos siguen bloqueando el guardado con el mensaje actual.

## Escenario 8 — Waveform estable y distinta por sesión

1. Anotar el perfil visual de la sesión actual.
2. Recargar la pantalla.

**Esperado**:

- El perfil se mantiene igual para la misma sesión.

3. Cargar otra sesión sintética.

**Esperado**:

- El perfil visual es distinto al de la sesión anterior.
- El playhead, los ticks y el `seek` siguen funcionando.

## Escenario 9 — Accesibilidad y movimiento reducido

1. Navegar por los marcadores y el popover usando solo `Tab`, `Enter`/`Espacio` y `Esc`.
2. Activar `prefers-reduced-motion` en el navegador.
3. Reproducir y hacer scroll manual.

**Esperado**:

- El popover se abre, recorre y cierra con teclado.
- El foco vuelve al marcador al cerrar.
- El auto-scroll no usa animación o se desactiva.
- No se pierde ningún control ni información.

## Escenario 10 — Sin regresiones funcionales

1. Verificar que el banner de datos sintéticos y la confirmación siguen presentes.
2. Verificar que la columna XAI y las etiquetas de vista previa siguen visibles.
3. Exportar la sesión y comprobar que conserva transcripción, marcas y anotaciones.

**Esperado**:

- Los avisos y etiquetas actuales se mantienen.
- La exportación conserva las marcas por palabra.
- No cambian la sesión única, el audio ni el límite de 120 MB.

## Criterio de aceptación global

La feature se considera completa cuando los diez escenarios pasan, la suite de frontend está en verde,
el backend no presenta regresiones y no se ha modificado ningún aviso obligatorio ni la persistencia.

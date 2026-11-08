# Research: Experiencia de transcripción continua

**Fase**: 0 (Research) · **Fecha**: 2026-11-07 · **Plan**: [plan.md](./plan.md)

Este documento resuelve las decisiones técnicas de la feature `005`. No se añaden dependencias,
servicios ni cambios de backend.

## D39. Flujo continuo en un único contenedor con scroll

**Decisión**: renderizar todos los segmentos de la sesión en un único contenedor vertical con scroll,
manteniendo cada segmento como bloque identificable con su timestamp.

**Razón**: con un máximo esperado de 200 segmentos, no hace falta virtualización. Un único contenedor
simplifica el auto-scroll, el resaltado del activo y la lectura continua sin introducir una librería
nueva.

**Alternativas consideradas**:

- Lista virtualizada: añade complejidad y dificulta el scroll suave y la búsqueda visual.
- Tarjetas independientes: es el estado actual y no cumple la lectura continua.

## D40. Auto-scroll con pausa manual de 5 segundos

**Decisión**: el contenedor sigue al segmento activo mientras el audio avanza. Cualquier interacción
manual de scroll (rueda, touch, arrastre de barra, teclado o `scroll` no programático) pausa el
seguimiento; a los 5 segundos se reanuda automáticamente. La acción “Volver al audio” reanuda antes.

**Razón**: el usuario necesita poder leer otra parte sin que la vista vuelva a saltar de inmediato,
pero tampoco quiere quedarse permanentemente fuera del seguimiento.

**Alternativas consideradas**:

- Reanudar inmediatamente: la vista pelea con el usuario.
- Pausar hasta acción explícita: obliga a un clic extra y rompe el flujo de escucha.
- Auto-scroll permanente sin pausa: impide leer otros fragmentos.

## D41. `seek` solo por controles explícitos

**Decisión**: el `seek` ocurre únicamente al pulsar el chip de tiempo, al pulsar el botón con símbolo
de play o al hacer clic/arrastrar sobre la waveform. El scroll, el paso del tiempo y el clic sobre el
texto no cambian la reproducción. El botón play hace `seek` al inicio del segmento y comienza a
reproducir.

**Razón**: separar lectura de reproducción evita saltos accidentales y cumple la decisión del usuario.
El botón play es una acción explícita y satisface la política de reproducción iniciada por gesto.

**Alternativas consideradas**:

- Hacer `seek` al hacer clic en el segmento: produce saltos accidentales al seleccionar texto.
- Hacer `seek` al cambiar el segmento activo: mezcla seguimiento visual con control de audio.

## D42. Agrupación de observaciones por proximidad visual

**Decisión**: agrupar marcadores cuya distancia horizontal sea menor o igual a 14 px, calculada sobre
el ancho real de la waveform. El grupo muestra un contador. La agrupación se recalcula al cambiar el
tamaño del contenedor.

**Razón**: la proximidad relevante es visual, no temporal; dos observaciones pueden estar cerca en
segundos pero lejos en pantalla, o al contrario en audios largos.

**Alternativas consideradas**:

- Agrupar por ventana fija de tiempo: no se adapta al zoom ni al ancho de pantalla.
- No agrupar: los marcadores se solapan y se vuelven inaccesibles.

## D43. Popover no modal con zona de seguridad

**Decisión**: el popover se abre con hover o foco, no bloquea la página y se cierra al salir de la
zona formada por el marcador y el popover, con un margen de gracia de 150 ms para cruzar de uno a
otro. También se cierra con el botón de cerrar, con `Esc` o al tocar fuera en táctil. En teclado, el
foco puede entrar al popover y salir sin quedar atrapado.

**Razón**: el usuario pidió un comportamiento no restrictivo. La zona compartida y el margen de gracia
evitan que el popover desaparezca al mover el puntero desde el marcador.

**Alternativas consideradas**:

- Modal con backdrop y foco atrapado: demasiado restrictivo para una consulta rápida.
- Tooltip nativo: no permite listar varias observaciones ni incluir acciones.
- Cierre inmediato al salir del marcador: impide llegar al popover.

## D44. “Ver fragmento” sin `seek`

**Decisión**: el popover es de solo lectura y ofrece “Ver fragmento”, que desplaza la transcripción
hasta el segmento asociado, pausa el auto-scroll 5 segundos y no cambia la posición del audio.

**Razón**: el usuario quiere inspeccionar el contexto textual de la observación sin interrumpir ni
mover la reproducción.

**Alternativas consideradas**:

- Hacer `seek` al pulsar la observación: contradice la separación entre lectura y reproducción.
- No ofrecer acceso al fragmento: obliga a buscar manualmente el segmento.

## D45. Edición en bloques continuos

**Decisión**: la edición muestra todos los segmentos en un flujo continuo, con separadores visuales,
timestamps y campos editables por bloque. No se usa un único `textarea` libre.

**Razón**: un bloque por segmento conserva la relación con el audio, permite validar rangos y mantiene
la identidad necesaria para conservar o redistribuir las marcas por palabra. El flujo continuo mejora
la lectura sin romper el contrato existente de guardado.

**Alternativas consideradas**:

- Un `textarea` único: fácil de leer, pero difícil de mapear a segmentos y timestamps.
- Editor de texto enriquecido: añade dependencia y complejidad innecesaria.

## D46. Waveform real con variación determinista

**Decisión**: conservar la amplitud real calculada desde el audio y aplicar una modulación visual
determinista derivada de un identificador estable de la sesión. La misma sesión produce el mismo
perfil; sesiones distintas producen perfiles distintos. Si la decodificación falla, se usa un perfil
de respaldo estable.

**Razón**: cambia la apariencia entre sesiones sin mentir sobre el audio ni romper la relación entre
la barra, el playhead y el tiempo.

**Alternativas consideradas**:

- Onda aleatoria en cada render: inestable y sin relación con el audio.
- Onda decorativa fija: no distingue sesiones.

## D47. Sin cambios de backend

**Decisión**: no se añaden ni modifican endpoints, esquemas, migraciones ni servicios. La vista
continua, los grupos de observaciones, el popover y la variación de la waveform se calculan en el
cliente con los datos existentes.

**Razón**: la feature es de presentación y navegación; el backend ya entrega segmentos, timestamps,
anotaciones y audio.

**Alternativas consideradas**:

- Endpoint de agrupación: introduce estado y complejidad sin necesidad.
- Persistir preferencias de scroll o waveform: fuera del alcance del MVP.

## D48. Accesibilidad y movimiento reducido

**Decisión**: los marcadores y el popover son alcanzables con `Tab`; el popover se abre con foco o
`Enter`/`Espacio`, se recorre con `Tab`/flechas, se cierra con `Esc` y devuelve el foco al marcador. Se
usan `aria-expanded`, `aria-controls` y etiquetas descriptivas. El auto-scroll y las transiciones
respetan `prefers-reduced-motion`.

**Razón**: el comportamiento de hover no debe excluir a usuarios de teclado y el movimiento continuo
puede afectar a personas sensibles al movimiento.

**Alternativas consideradas**:

- Solo hover: inaccesible por teclado.
- Auto-scroll siempre animado: ignora la preferencia de movimiento reducido.

## D49. Estrategia de pruebas

**Decisión**: usar Vitest + Testing Library con temporizadores falsos para la pausa de 5 segundos,
mocks de `scrollIntoView`/`getBoundingClientRect` y pruebas de componente para los flujos de teclado,
hover y edición. Añadir pruebas unitarias puras para la agrupación y la semilla de waveform.

**Razón**: el proyecto ya usa este stack; no se añaden dependencias. Los mocks permiten validar
comportamiento de layout en jsdom sin un navegador real.

**Alternativas consideradas**:

- Pruebas end-to-end con navegador: mayor coste y nueva dependencia.
- Solo pruebas manuales: no protegen contra regresiones.

## D50. Rendimiento sin re-render global

**Decisión**: mantener el tiempo actual y el seguimiento en refs/estado local del componente de
transcripción, memoizar los bloques de segmento y evitar que cada actualización de tiempo re-renderice
toda la lista.

**Razón**: el reproductor actualiza el tiempo con frecuencia; con 200 segmentos, un re-render completo
por tick degrada la lectura y el scroll.

**Alternativas consideradas**:

- Re-render completo por tick: simple pero costoso.
- Virtualización: innecesaria para el tamaño objetivo y complica el scroll continuo.

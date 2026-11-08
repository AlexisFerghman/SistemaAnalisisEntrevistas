# Feature Specification: Experiencia de transcripción continua

**Feature Branch**: `005-transcripcion-continua`

**Created**: 2026-11-07

**Status**: Draft

**Input**: Mejoras de interfaz acordadas a partir de `propuestas.md`: transcripción en flujo continuo sincronizado con el audio, botón explícito de reproducción por segmento, agrupación de observaciones en un popover no modal, edición unificada de subtítulos y variación determinista de la waveform entre sesiones. Se mantienen el banner y las etiquetas actuales para no vulnerar la constitución.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Leer la transcripción como un flujo continuo (Priority: P1)

El profesional reproduce la entrevista y sigue la transcripción como un texto continuo que avanza con el audio. El segmento activo permanece visible con contexto suficiente para no perder el hilo, pero la interfaz nunca cambia la posición de reproducción por el simple hecho de desplazar la vista.

**Why this priority**: es la mejora con mayor impacto en la lectura y la navegación de la entrevista.

**Independent Test**: con una sesión de más de 50 segmentos, reproducir el audio y comprobar que el segmento activo se mantiene visible, que el scroll manual pausa el seguimiento y que ningún desplazamiento ni clic sobre el texto provoca un salto de audio.

**Acceptance Scenarios**:

1. **Given** una entrevista con muchos segmentos, **When** el audio avanza, **Then** el segmento activo se resalta y la transcripción se desplaza suavemente para mantenerlo visible.
2. **Given** el audio en reproducción, **When** la transcripción se desplaza automáticamente, **Then** la posición de reproducción no cambia.
3. **Given** el audio en reproducción, **When** el usuario hace scroll manual, **Then** el seguimiento automático se pausa y no se modifica el audio.
4. **Given** el seguimiento pausado por scroll manual, **When** transcurren 5 segundos, **Then** el seguimiento se reanuda automáticamente.
5. **Given** el seguimiento pausado, **When** el usuario pulsa "Volver al audio", **Then** el seguimiento se reanuda sin cambiar la posición del audio.
6. **Given** un segmento visible, **When** el usuario hace clic sobre su texto, **Then** no se produce ningún salto en la reproducción.
7. **Given** un segmento visible, **When** el usuario pulsa su chip de tiempo, **Then** el audio salta al inicio del segmento.
8. **Given** un segmento visible, **When** el usuario pulsa el botón con símbolo de play, **Then** el audio salta al inicio del segmento y comienza a reproducirse.
9. **Given** la waveform, **When** el usuario hace clic o arrastra sobre ella, **Then** el audio salta al instante correspondiente.

---

### User Story 2 - Consultar observaciones agrupadas (Priority: P2)

El profesional ve varias observaciones cercanas en la barra de reproducción. En lugar de marcadores amontonados o tooltips de texto plano, la interfaz los agrupa y muestra un popover con la información de cada observación, sin bloquear el resto del trabajo.

**Why this priority**: evita perder observaciones cuando varias están próximas en el tiempo y mejora la lectura de las anotaciones existentes.

**Independent Test**: con tres observaciones separadas por menos del 1 % del ancho de la barra, comprobar que se muestra un único marcador con contador, que el popover lista las tres y que "Ver fragmento" desplaza la transcripción sin hacer seek.

**Acceptance Scenarios**:

1. **Given** varias observaciones visualmente próximas, **When** se renderiza la waveform, **Then** aparece un único marcador con un contador que indica cuántas observaciones agrupa.
2. **Given** un marcador individual o agrupado, **When** el puntero entra en el marcador, **Then** se abre el popover sin necesidad de clic.
3. **Given** un marcador individual o agrupado, **When** recibe foco mediante teclado, **Then** se abre el mismo popover.
4. **Given** el popover abierto, **When** el puntero permanece en el marcador o en el popover, **Then** el popover sigue visible.
5. **Given** el popover abierto, **When** el puntero sale de la zona formada por el marcador y el popover, **Then** el popover se cierra.
6. **Given** el popover abierto, **When** el usuario pulsa el botón de cerrar o `Esc`, **Then** el popover se cierra.
7. **Given** una pantalla táctil, **When** el usuario toca el marcador, **Then** el popover se abre; **When** toca fuera, **Then** se cierra.
8. **Given** una única observación, **When** se abre su marcador, **Then** se usa el mismo popover, no un tooltip distinto.
9. **Given** el popover abierto, **When** el usuario pulsa "Ver fragmento", **Then** la transcripción se desplaza hasta el segmento asociado sin cambiar la posición del audio, y el seguimiento automático se pausa 5 segundos.

---

### User Story 3 - Editar subtítulos en una vista unificada (Priority: P3)

El profesional edita la transcripción completa en un único flujo de bloques continuos, con separadores visuales por segmento y timestamps siempre visibles. Puede revisar el texto con más contexto sin perder la relación entre cada fragmento y el audio.

**Why this priority**: mejora la revisión y reduce la sensación de editar tarjetas aisladas, manteniendo las validaciones existentes.

**Independent Test**: entrar en edición, comprobar que todos los segmentos están visibles en un solo flujo, guardar un cambio válido y verificar que un rango inválido sigue bloqueando el guardado.

**Acceptance Scenarios**:

1. **Given** una transcripción existente, **When** el usuario entra en edición, **Then** ve todos los segmentos en un único flujo vertical.
2. **Given** la vista de edición, **When** el usuario recorre la transcripción, **Then** cada segmento conserva un separador visual y su timestamp.
3. **Given** la vista de edición, **When** el usuario modifica texto o marcas, **Then** el texto completo permanece visible y no se trunca.
4. **Given** una edición con texto vacío, rangos invertidos, negativos o solapados, **When** el usuario intenta guardar, **Then** el guardado se bloquea con el mensaje correspondiente.
5. **Given** una edición válida, **When** el usuario guarda, **Then** la transcripción se actualiza y el audio original no cambia.
6. **Given** una edición de texto, **When** se guarda, **Then** las marcas por palabra se conservan o se redistribuyen como hasta ahora.

---

### User Story 4 - Identificar visualmente cada sesión por su waveform (Priority: P4)

El profesional distingue visualmente una sesión de otra por el perfil de la waveform, sin que ello altere la relación entre la barra, el tiempo y la reproducción.

**Why this priority**: es una mejora de identificación visual; no bloquea el flujo principal.

**Independent Test**: cargar dos sesiones distintas y comprobar que sus perfiles visuales no son idénticos; recargar la misma sesión y comprobar que el perfil se mantiene.

**Acceptance Scenarios**:

1. **Given** dos sesiones distintas, **When** se muestran sus waveforms, **Then** los perfiles visuales son diferentes.
2. **Given** una misma sesión, **When** se recarga la pantalla, **Then** la waveform conserva el mismo perfil.
3. **Given** una waveform visible, **When** el usuario hace clic o arrastra, **Then** el `seek` sigue correspondiendo a la duración real.
4. **Given** un fallo al obtener la forma de onda, **When** se muestra el reproductor, **Then** la reproducción sigue funcionando con una representación de respaldo.

---

### Edge Cases

- El usuario hace scroll manual mientras el audio está en pausa: el seguimiento se pausa y se reanuda a los 5 segundos si el audio vuelve a reproducirse.
- El segmento activo es el primero o el último: se muestra contexto disponible sin forzar desplazamientos imposibles.
- Un segmento es más alto que la ventana visible: se prioriza mostrar su inicio y el usuario puede desplazarse dentro de él.
- Varias observaciones comparten el mismo timestamp: se agrupan en un único marcador y el popover las lista todas.
- El popover queda cerca del borde de la pantalla o del último segmento: se reposiciona para no salir del área visible.
- El puntero sale del popover hacia la ventana del navegador: el popover se cierra.
- El usuario navega con teclado: puede abrir, recorrer, cerrar y volver al marcador sin ratón.
- El usuario prefiere movimiento reducido: el auto-scroll y las transiciones se desactivan o se vuelven instantáneos.
- La transcripción contiene muchos segmentos y anotaciones: la navegación sigue siendo fluida.
- El usuario pulsa "Ver fragmento" mientras el audio está reproduciéndose: la transcripción se desplaza, el audio sigue sonando y el seguimiento automático se pausa 5 segundos.
- La edición contiene un rango fuera de la duración del audio: se bloquea con el error actual.
- La waveform no se puede calcular: se usa un perfil de respaldo estable para esa sesión.

## Requirements *(mandatory)*

### Functional Requirements

- **RF-024**: La transcripción DEBE presentarse como un flujo vertical continuo con un único desplazamiento.
- **RF-025**: El segmento activo DEBE permanecer visible junto con al menos un segmento anterior y dos posteriores cuando existan.
- **RF-026**: El seguimiento automático DEBE pausarse tras un desplazamiento manual y reanudarse automáticamente a los 5 segundos.
- **RF-027**: El usuario DEBE poder reanudar el seguimiento antes de los 5 segundos mediante una acción explícita "Volver al audio".
- **RF-028**: El desplazamiento de la transcripción, el clic sobre el texto de un segmento y el paso del tiempo NO DEBEN cambiar la posición de reproducción.
- **RF-029**: El `seek` DEBE ocurrir únicamente mediante controles explícitos: el chip de tiempo del segmento, el botón con símbolo de play o la waveform.
- **RF-030**: El botón con símbolo de play DEBE situar la reproducción al inicio del segmento y comenzar a reproducir.
- **RF-031**: Las observaciones visualmente próximas DEBEN agruparse en un único marcador con un contador visible.
- **RF-032**: El marcador de observaciones DEBE abrir un popover no modal al recibir hover o foco, sin exigir un clic.
- **RF-033**: El popover DEBE permanecer abierto mientras el puntero esté en el marcador o en el popover, y cerrarse al salir de esa zona, con el botón de cerrar, con `Esc` o al tocar fuera en una pantalla táctil.
- **RF-034**: El popover DEBE mostrar la hora, el texto y el segmento asociado de cada observación, en modo de solo lectura.
- **RF-035**: El popover DEBE ofrecer "Ver fragmento", que desplaza la transcripción al segmento asociado sin cambiar la posición del audio y pausa el seguimiento automático durante 5 segundos.
- **RF-036**: La edición DEBE mostrar la transcripción completa en bloques continuos, con separadores visuales, timestamps y las mismas validaciones actuales.
- **RF-037**: La waveform DEBE conservar la amplitud real del audio y variar de forma determinista entre sesiones, manteniendo estable el perfil de una misma sesión.
- **RF-038**: La interfaz DEBE conservar el banner, la confirmación de datos sintéticos y las etiquetas actuales de funciones no disponibles.

### Non-Functional Requirements

- **RNF-011**: Todos los controles nuevos DEBEN ser accesibles por teclado, con foco visible y nombres accesibles.
- **RNF-012**: El auto-scroll y las transiciones DEBEN respetar la preferencia de movimiento reducido.
- **RNF-013**: La mejora NO DEBE añadir dependencias, endpoints, tablas ni servicios nuevos.
- **RNF-014**: La actualización del tiempo de reproducción NO DEBE volver a renderizar toda la transcripción.
- **RNF-015**: NO DEBE haber regresión en marcas por palabra, anotaciones, exportación, sesión única, audio original ni límite de 120 MB.
- **RNF-016**: La navegación DEBE mantenerse fluida con al menos 200 segmentos y 500 anotaciones.

### Key Entities *(include if feature involves data)*

- **Segmento visible**: fragmento de transcripción con identificador, texto, marca de inicio y marca de fin; conserva su identidad al editar.
- **Observación**: anotación de texto vinculada a un segmento y a un rango temporal.
- **Grupo de observaciones**: conjunto de observaciones que se muestran juntas por proximidad visual en la barra de reproducción.
- **Perfil de waveform**: representación visual estable de una sesión, asociada a su audio y a su duración.
- **Vista de edición unificada**: presentación continua de todos los segmentos editables, con separadores y timestamps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-016**: El segmento activo permanece visible al menos el 95 % del tiempo de reproducción sin que el usuario tenga que desplazarse manualmente.
- **SC-017**: Tras un desplazamiento manual, el seguimiento automático se reanuda en 5 segundos o antes si el usuario pulsa "Volver al audio".
- **SC-018**: El 100 % de las pruebas de interacción confirman que el scroll y el clic sobre el texto no provocan saltos de audio.
- **SC-019**: El popover muestra el 100 % de las observaciones de un grupo, incluidas las agrupaciones con una sola observación.
- **SC-020**: Un usuario puede abrir, recorrer, cerrar y volver al marcador del popover usando solo el teclado.
- **SC-021**: La edición conserva el 100 % de los segmentos y timestamps y sigue bloqueando textos vacíos y rangos inválidos.
- **SC-022**: La waveform de una misma sesión es estable y la de dos sesiones distintas resulta visualmente distinta en al menos 9 de cada 10 comparaciones.
- **SC-023**: La suite existente sigue en verde y la exportación continúa incluyendo las marcas por palabra.
- **SC-024**: La interfaz mantiene visibles el banner, la confirmación de datos sintéticos y las etiquetas actuales de funciones no disponibles.

## Assumptions

- La mejora es exclusivamente de interfaz: reutiliza los datos y endpoints existentes de sesión, transcripción y anotaciones.
- El sistema existente ya entrega segmentos, timestamps y anotaciones suficientes para construir la vista continua y los grupos de observaciones.
- La aplicación es de escritorio como objetivo principal, con soporte táctil para abrir y cerrar el popover.
- La reproducción del audio siempre requiere una acción explícita del usuario; el botón play de un segmento cuenta como esa acción.
- La sesión sigue siendo única y el audio original no se modifica.
- La variación de la waveform se deriva de datos ya disponibles de la sesión; no requiere un servicio nuevo.
- Se mantienen el banner actual, la confirmación de datos sintéticos y las etiquetas `Próximamente`/`CSV próximamente`.
- Los módulos de explicabilidad y emoción se conservan con su etiqueta de vista previa; no se presentan como análisis real.

### Out of Scope

- Eliminar banners, avisos de datos sintéticos o etiquetas de funciones no disponibles.
- Implementar explicabilidad XAI o análisis afectivo real.
- Cambiar el modelo de datos, la API o el motor de transcripción.
- Añadir historial de sesiones, autenticación, roles o multiusuario.
- Implementar exportación CSV.
- Reproducir audio automáticamente sin una acción del usuario.
- Hacer `seek` al hacer clic sobre el texto de un segmento o al desplazar la transcripción.

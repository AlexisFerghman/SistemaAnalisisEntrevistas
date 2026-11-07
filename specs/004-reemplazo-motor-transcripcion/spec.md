# Feature Specification: Reemplazo del motor de transcripción por el enfoque validado en Audio-Transcript-main

**Feature Branch**: `004-reemplazo-motor-transcripcion`

**Created**: 2026-11-07

**Status**: Borrador

**Input**: User description: "agregue el directorio Audio-Transcript-Main que contiene una manera de transcripción de audio, donde probe y compare los resultados con nuestro transcriptor acutal y funciona mejor que fasterwhiper. Asique genera una nueva especificación para reeplazar el modelo actual con este nuevo modelo"

## Contexto y objetivo

El prototipo ya transcribe entrevistas sintéticas con un motor local, pero la calidad del texto
obtenido obliga al profesional a corregir demasiados errores. En el directorio
`Audio-Transcript-main` se incorporó y probó una forma alternativa de transcribir audio que, sobre la
misma entrevista de referencia, produjo resultados mejores que el motor vigente.

Esta entrega reemplaza el motor de transcripción actual por el enfoque validado en
`Audio-Transcript-main`. El resto del flujo —carga, reproducción sincronizada, edición,
anotaciones, exportación y sesión única— se conserva sin cambios funcionales. No se incorporan
nuevos usuarios, pantallas ni formatos de salida.

En esta especificación, **motor de transcripción** designa el modelo y la forma de ejecutarlo. La
variante concreta se decide en el plan; esta spec fija el resultado de calidad esperado.

## Clarifications

### Session 2026-11-07

- Q: ¿Se fija en la especificación la variante concreta del nuevo motor o se deja como decisión del plan? → A: Se deja como decisión del plan, registrando como recomendación `faster-whisper` + `large-v3-turbo` + `int8` + español fijo + glosario + VAD.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 — Obtener transcripciones más fieles con el nuevo motor (Prioridad: P1)

El profesional de salud carga una entrevista sintética y recibe una transcripción en español con
menos errores que la del motor anterior, incluyendo mejor reconocimiento de nombres propios y
términos técnicos del dominio.

**Por qué esta prioridad**: la mejora de calidad es la razón de ser de esta entrega. Sin una
transcripción más fiel, el reemplazo no aporta valor y no se justifica el mayor coste de cómputo.

**Prueba independiente**: transcribir el conjunto de audios de referencia con el motor vigente y con
el nuevo, y comparar errores por palabra y aciertos de términos del glosario. La prueba no requiere
editor, anotaciones ni exportación.

**Escenarios de aceptación**:

1. **Dado** el conjunto de audios sintéticos de referencia, **Cuando** se transcribe con el nuevo
   motor, **Entonces** la tasa de errores por palabra es al menos un 20 % menor en términos
   relativos que con el motor vigente y ningún audio del conjunto empeora.
2. **Dado** un audio que contiene nombres propios y términos técnicos incluidos en el glosario del
   dominio, **Cuando** se transcribe, **Entonces** al menos el 90 % de esos términos aparece
   correctamente escrito.
3. **Dado** un audio en español, **Cuando** se inicia la transcripción, **Entonces** el resultado se
   genera siempre en español, sin cambiar de idioma ni mezclar idiomas.
4. **Dado** un audio con silencios, ruido o tramos sin habla, **Cuando** se transcribe, **Entonces**
   el sistema no inventa frases en esos tramos y las marcas de tiempo siguen referidas al audio
   completo.

---

### Historia de usuario 2 — Mantener la sincronización y el flujo de revisión (Prioridad: P2)

El profesional de salud revisa la nueva transcripción con la misma experiencia que antes: texto
sincronizado con el audio, marcas por palabra y por oración, edición de texto y de tiempos, y
reproducción desde cualquier fragmento.

**Por qué esta prioridad**: una transcripción más precisa solo es útil si conserva la trazabilidad y
la posibilidad de corrección que exige el flujo actual.

**Prueba independiente**: con una transcripción generada por el nuevo motor, reproducir el audio,
saltar a una marca, editar el texto y ajustar un tiempo demuestra la historia sin usar anotaciones ni
exportación.

**Escenarios de aceptación**:

1. **Dado** un audio transcrito con el nuevo motor, **Cuando** el usuario lo reproduce, **Entonces**
   cada segmento y cada palabra conserva una marca de inicio y una de fin dentro de la duración del
   audio.
2. **Dado** un segmento de la nueva transcripción, **Cuando** el usuario edita su texto o sus marcas
   de tiempo, **Entonces** puede guardarlo con las mismas reglas de validación que antes y el audio
   original no se modifica.
3. **Dado** que el usuario ya editó una transcripción, **Cuando** la consulta o reproduce,
   **Entonces** el sistema no vuelve a transcribir el audio ni descarta las correcciones.
4. **Dado** un segmento con marcas invertidas, negativas o fuera de la duración, **Cuando** el
   usuario intenta guardarlo, **Entonces** el sistema lo rechaza con un motivo comprensible.

---

### Historia de usuario 3 — Conservar las garantías operativas y de privacidad (Prioridad: P3)

El profesional de salud sigue usando el sistema en un entorno local y aislado: puede cancelar una
carga, un fallo no destruye la sesión anterior y no se envía audio a ningún servicio externo.

**Por qué esta prioridad**: el nuevo motor es más exigente en recursos; sin estas garantías el
reemplazo pondría en riesgo la privacidad y la continuidad del flujo.

**Prueba independiente**: iniciar una transcripción, cancelarla; provocar un fallo del motor; y
comprobar que no hay egreso de red y que la sesión anterior sigue disponible. No requiere edición ni
anotaciones.

**Escenarios de aceptación**:

1. **Dado** un audio en proceso de transcripción, **Cuando** el usuario cancela, **Entonces** la
   operación se detiene, no se presenta una transcripción parcial y la sesión anterior se conserva.
2. **Dado** un fallo, timeout o falta de recursos del nuevo motor, **Cuando** la transcripción no
   concluye, **Entonces** el sistema informa el fallo, conserva la sesión anterior y no mezcla datos.
3. **Dado** el entorno de ejecución, **Cuando** se transcribe un audio, **Entonces** el proceso
   ocurre sin llamadas de red externas y con el modelo ya disponible localmente.
4. **Dado** un audio de 10 minutos, **Cuando** se transcribe en el equipo de referencia, **Entonces**
   el resultado está disponible en menos de 15 minutos.

### Casos límite

- Audio con silencios prolongados, ruido de fondo o música: no debe generar texto inventado.
- Nombres propios o términos técnicos que no están en el glosario: se transcriben con el mejor
  esfuerzo disponible, sin fallar la operación.
- Audio en un idioma distinto del español o con cambio de idioma: el sistema no lo detecta
  automáticamente ni cambia de idioma; produce la mejor transcripción en español o informa que el
  audio no es utilizable.
- Audio largo (cerca del límite de duración o tamaño admitido): debe completar o fallar de forma
  explícita, sin dejar una sesión a medio actualizar.
- Memoria o GPU insuficiente para cargar el nuevo modelo: debe informarse como servicio de
  transcripción no disponible, conservando la sesión anterior.
- Cancelación durante la carga del modelo o entre segmentos: debe respetarse en ambos momentos.
- Construcción de la imagen sin acceso a red: el modelo debe quedar disponible durante la
  construcción, no en la primera transcripción.
- Audio ya transcrito y editado: una nueva consulta no debe relanzar la transcripción automática.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **RF-001**: CUANDO se cargue un audio válido, el sistema DEBE transcribirlo con el enfoque validado
  en `Audio-Transcript-main` en lugar del motor actual, para todas las cargas nuevas.
- **RF-002**: El sistema DEBE transcribir siempre en español, sin detección automática de idioma.
- **RF-003**: El sistema DEBE usar el glosario de nombres propios y términos técnicos del dominio
  como contexto de la transcripción, sin modificar el audio ni el texto una vez generado.
- **RF-004**: El sistema DEBE ignorar tramos sin habla para evitar texto inventado, manteniendo las
  marcas de tiempo referidas al audio completo.
- **RF-005**: CUANDO la transcripción concluya, el sistema DEBE entregar marcas de inicio y fin por
  palabra y por oración, normalizadas según el contrato vigente del adaptador.
- **RF-006**: El sistema DEBE conservar las categorías de error, la política de un único reintento y
  la cancelación cooperativa entre segmentos del flujo actual.
- **RF-007**: SI el nuevo motor no puede inicializarse o no dispone de recursos suficientes, ENTONCES
  el sistema DEBE informar el fallo como servicio de transcripción no disponible y conservar la
  sesión anterior.
- **RF-008**: CUANDO una nueva transcripción se complete correctamente, el sistema DEBE reemplazar la
  sesión anterior con las mismas reglas de sesión única ya vigentes.
- **RF-009**: SI la nueva carga, transcripción o persistencia falla, ENTONCES el sistema DEBE
  conservar la sesión anterior sin mezclar datos de ambas sesiones.
- **RF-010**: El sistema DEBE mantener sin cambios el contrato de la API, el modelo de datos, la
  experiencia de la interfaz, la edición, las anotaciones y la exportación.
- **RF-011**: El sistema DEBE dejar el modelo disponible localmente durante la construcción de la
  imagen, de modo que en ejecución no requiera descargas ni acceso a red.
- **RF-012**: El sistema DEBE permitir actualizar el glosario del dominio sin cambiar el código del
  motor ni el contrato de la API.
- **RF-013**: El sistema NO DEBE volver a transcribir automáticamente un audio que ya tiene una
  transcripción confirmada o editada.
- **RF-014**: El sistema DEBE conservar el audio original sin modificarlo ni sustituirlo por una
  versión procesada.

### Requisitos no funcionales

- **RNF-001**: La calidad de transcripción del nuevo motor DEBE ser medible contra el motor vigente
  sobre el mismo conjunto de audios de referencia.
- **RNF-002**: El nuevo motor DEBE ejecutarse localmente y sin egreso de red en tiempo de ejecución.
- **RNF-003**: El sistema DEBE informar de forma explícita cualquier fallo por falta de memoria,
  GPU o modelo no disponible, sin degradar silenciosamente la calidad.
- **RNF-004**: La transcripción de 10 minutos de audio DEBE completarse en menos de 15 minutos en el
  equipo de referencia.
- **RNF-005**: El cambio NO DEBE alterar el principio de sesión única, la supervisión humana
  obligatoria ni el uso exclusivo de datos sintéticos.
- **RNF-006**: El nuevo motor DEBE quedar cubierto por pruebas automatizadas que no dependan de
  descargar el modelo en tiempo de prueba.

### Entidades clave

- **Transcripción**: resultado del nuevo motor para un audio. Atributos: idioma, origen del motor,
  número de reintentos y segmentos.
- **Segmento**: tramo de la transcripción. Atributos: identificador, marca de inicio, marca de fin,
  texto y palabras.
- **Palabra**: unidad mínima de la transcripción. Atributos: texto, marca de inicio y marca de fin.
- **Glosario del dominio**: lista versionada de nombres propios y términos técnicos que orienta la
  transcripción. Atributos: contenido y versión.
- **Conjunto de evaluación**: audios sintéticos con su transcripción de referencia y las métricas
  calculadas para el motor vigente y el nuevo. Atributos: audio, referencia, tasa de errores por
  palabra y aciertos de términos.
- **Sesión de entrevista**: unidad única del sistema que agrupa audio, transcripción y anotaciones;
  conserva las relaciones y reglas ya definidas en la entrega anterior.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: Sobre el conjunto de audios de referencia, la tasa de errores por palabra del nuevo
  motor es al menos un 20 % menor en términos relativos que la del motor vigente, y ningún audio del
  conjunto empeora.
- **SC-002**: Al menos el 90 % de los nombres propios y términos técnicos del glosario se transcribe
  correctamente en el conjunto de referencia.
- **SC-003**: El 100 % de las transcripciones generadas incluye marca de inicio y fin por palabra y
  por oración, dentro de la duración del audio.
- **SC-004**: El 100 % de las cargas nuevas utiliza el nuevo motor; ninguna carga nueva recurre al
  motor anterior.
- **SC-005**: El 100 % de las cancelaciones y fallos deja la sesión anterior disponible, sin
  transcripción parcial ni datos mezclados.
- **SC-006**: El 100 % de las transcripciones se realiza dentro del entorno local, sin que el audio
  salga del equipo ni se consulte un servicio externo.
- **SC-007**: Un audio de 10 minutos se transcribe en menos de 15 minutos en el equipo de referencia.
- **SC-008**: El 100 % de los flujos existentes de carga, reproducción, edición, anotación y
  exportación mantiene su comportamiento observable sin cambios.

## Supuestos

### Actores y usuarios

- **Profesional de salud**: único usuario conceptual; no necesita cuenta ni autenticación.
- **Servicio local de transcripción**: componente aislado que recibe el audio sintético y devuelve
  la transcripción con marcas de tiempo.

### Fuera de alcance

- Cambios en la interfaz, la API, el modelo de datos, la edición, las anotaciones o la exportación.
- Detección automática de idioma, traducción o soporte de idiomas distintos del español.
- Diarización de hablantes, separación de voces o identificación de participantes.
- Transcripción en tiempo real o por streaming.
- Uso de servicios de transcripción en la nube o con egreso de red.
- Entrenamiento o ajuste fino del modelo con datos del proyecto.
- Uso de entrevistas reales o datos identificables.

### Decisiones provisionales

- La variante concreta del nuevo motor se decide en `/speckit.plan`. La recomendación registrada es
  `faster-whisper` con el modelo `large-v3-turbo`, cuantización `int8` en CPU, español fijo, glosario
  como contexto inicial y filtro de actividad de voz. Cualquier variante elegida debe cumplir los
  criterios de calidad de esta especificación.
- La referencia de calidad es la salida con marcas de tiempo observada en
  `Audio-Transcript-main/audioCorto.txt`, generada por el script local del directorio. Si la
  comparación registrada por el usuario corresponde a otra variante del mismo directorio, se ajusta
  en el plan sin cambiar los requisitos de calidad de esta especificación.
- El glosario inicial es `Audio-Transcript-main/glosario-whisper.txt`; su contenido puede ampliarse
  sin alterar el alcance funcional.
- El conjunto de evaluación se compone del audio de referencia de 9 min 27 s y de los audios
  sintéticos ya disponibles en `fixtures/`.
- El objetivo de rendimiento se mantiene en 15 minutos para 10 minutos de audio, igual que en la
  entrega anterior.

### Supuestos técnicos y dependencias

- El enfoque recomendado para el plan usa `faster-whisper` con el modelo `large-v3-turbo`,
  cuantización `int8` en CPU y aceleración por GPU cuando esté disponible, idioma español fijo,
  glosario como contexto inicial y filtro de actividad de voz. La variante final se fija en el plan.
- El adaptador de transcripción vigente (`backend/app/transcription/`) se conserva como frontera: el
  resto de la aplicación no conoce el motor concreto.
- El modelo se descarga durante `docker build` y se reutiliza durante toda la vida del proceso.
- El contenedor `api` mantiene un único proceso para no duplicar el modelo en memoria.
- La política de un único reintento para timeout o indisponibilidad se conserva.
- El audio se mantiene en el almacenamiento local de la sesión y no se envía a terceros.
- El cambio no requiere una enmienda a la constitución: refuerza el principio IV de calidad y
  trazabilidad y no altera los principios de privacidad, sesión única ni supervisión humana.

# Contrato de interfaz — Pantalla de trabajo

**Fase**: 1 (Design)
**Fecha**: 2026-11-04
**Referencias visuales**: [`docs/ui/main.png`](../../../docs/ui/main.png), [`docs/ui/main2.png`](../../../docs/ui/main2.png)
**Spec**: [spec.md](../spec.md) · **Plan**: [plan.md](../plan.md) · **API**: [api.md](./api.md)

Aplicación de una sola pantalla, en español, para escritorio. No hay autenticación ni navegación
entre vistas: el botón de retroceso, el perfil y "Salir" son decorativos en este MVP.

## Principios visuales

1. **Una sola vista**: todo el trabajo ocurre en la pantalla de trabajo. Lo único que se superpone es
   el modal de carga.
2. **El audio manda**: la barra de reproducción ocupa todo el ancho y es el eje temporal de la
   pantalla; la transcripción se sincroniza con ella.
3. **Sin datos identificables**: no se muestran nombres de pacientes, códigos ni historiales. El
   encabezado identifica la **sesión**, no a una persona.
4. **Lo no implementado se ve, no engaña**: los módulos futuros son maquetas estáticas o están
   deshabilitados con la etiqueta "Próximamente". Nunca muestran datos inventados de la entrevista.

## Maqueta del layout

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ HEADER   logo · título de sesión · estado       [Nueva entrevista] [Exportar] │
│                                              perfil decorativo · Salir       │
├──────────────────────────────────────────────────────────────────────────────┤
│ MÓDULO AUDIO                                                                 │
│   Audio de la entrevista · archivo.wav · 42:16        leyenda ● etiqueta ● obs│
│   ┌──────────────── wavebar full width + playhead + puntos ─────────────────┐│
│   └─────────────────────────────────────────────────────────────────────────┘│
│              ⟲  ⏵/⏸  ⟳      07:36 / 42:16      [1x] [1.25x] [1.5x]          │
├───────────────────────────────┬──────────────────────────┬───────────────────┤
│ TRANSCRIPCIÓN SINCRONIZADA    │ EXPLICABILIDAD LOCAL     │ ANOTACIONES       │
│ 58%                           │ 21%                      │ 21%               │
│ tarjetas por segmento         │ maqueta estática (XAI)   │ placeholder vacío │
│ edición en línea              │                          │ contadores en 0   │
│ etiquetas y observaciones     │                          │                   │
└───────────────────────────────┴──────────────────────────┴───────────────────┘
```

Anchos de columna en escritorio: `58% / 21% / 21%`, con `gap` de 24 px y altura independiente con
scroll propio. Por debajo de 1024 px las tres columnas se apilan en orden 1 → 2 → 3.

## Header

| Elemento | Contenido | Funcional en el MVP |
|---|---|---|
| Logo | Marca de onda en cuadrado redondeado | No |
| Chevron de retroceso | — | No (deshabilitado, `aria-disabled`) |
| Título | `Sesión actual` | — |
| Badge de estado | `Sin audio` / `Analizando` / `Analizada` / `Error` según `status` | — |
| Subtítulo | `<nombre-de-archivo> · <duración> · <fecha de carga>` | — |
| Botón "Nueva entrevista" | Abre el modal de carga | **Sí** |
| Botón "Exportar datos" | Exporta la sesión como JSON | **Sí** (ver nota 1) |
| Perfil | `Profesional de salud` / `Sesión local` con iniciales | No |
| "Salir" | — | No |

**Nota 1 — desviación consciente**: pediste que el único botón funcional sea el de subir audio. El
botón de exportar también funciona porque `RF-016` exige que el usuario pueda exportar y no existe
otro punto de entrada en la pantalla. Si prefieres que sea decorativo, la exportación quedaría sin
interfaz y habría que moverla a una tarea aparte.

**Nota 2 — datos del perfil**: la maqueta muestra "Dra. Ana Morales · Psiquiatra" y `PAC-8F2A`. El
MVP no admite datos identificables (principio II), así que el perfil es un marcador estático
(`Profesional de salud`) y el subtítulo muestra **el nombre del archivo**, nunca un código de
paciente. Es la única diferencia deliberada respecto a la maqueta en la cabecera.

### Estados por `status`

| `status` | Badge | Módulo de audio | Columnas |
|---|---|---|---|
| `empty` | `Sin audio` | Oculto, solo ilustración y CTA | Ocultas |
| `validating` | `Analizando` | Visible, sin waveform | Visibles pero vacías |
| `processing` | `Analizando` | Visible, sin waveform | Visibles pero vacías |
| `ready` | `Analizada` | Completo | Pobladas |
| `reviewed` | `Analizada` | Completo | Pobladas |
| `error` | `Error` | Visible si hay audio, con aviso | Se conserva lo previo |

## Modal "Nueva entrevista"

Se abre desde el header o desde la ilustración de la vista vacía. Mientras está abierto:

- El resto de la página queda inerte: `backdrop-filter: blur(6px)` sobre `rgba(15, 23, 42, 0.45)`,
  `aria-modal="true"`, foco atrapado en el modal y `Esc` cierra si no hay una operación en curso.
- No se puede iniciar una segunda carga: el botón principal se deshabilita y el backend responde
  `409 busy` si ocurre.

### Contenido

```text
┌─ Nueva entrevista ────────────────────────────────────────────── ✕ ┐
│  Formatos admitidos: .mp3, .wav · máximo 120 MB                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Arrastra tu archivo aquí o haz clic para seleccionarlo       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  archivo.wav · 3.2 MB · 01:12                                        │
│                                                                      │
│  Modelo de transcripción                                             │
│  (•) Nube · faster-whisper base          — disponible                │
│  ( ) Local · en el dispositivo           — Próximamente (deshab.)    │
│                                                                      │
│  [x] Confirmo que este audio es sintético y no contiene datos        │
│      reales ni identificables                                        │
│                                                                      │
│  [ Cancelar ]                                    [ Analizar audio ]  │
└──────────────────────────────────────────────────────────────────────┘
```

### Reglas del modal

1. **Selector de modelo**: dos opciones. `Nube · faster-whisper base` habilitada y preseleccionada
   (es el modelo que corre dentro de los contenedores). `Local · en el dispositivo` visible pero
   deshabilitada, con distintivo `Próximamente`. La elección viaja como `model=nube`; el backend
   ignora hoy el campo y usa el adaptador local (research D01).
2. **Archivo**: arrastrar y soltar o selector nativo. Se valida en cliente (extensión, tamaño) y en
   servidor. Un rechazo del cliente no llama a la API.
3. **Confirmación de datos sintéticos**: obligatoria, no preseleccionada. Sin ella el botón principal
   permanece deshabilitado (`RF-003`, `RNF-001`).
4. **Progreso**: el botón principal pasa a `Analizando…` con indicador indeterminado y aparece
   `Cancelar análisis`, que llama a `POST /api/session/cancel`.
5. **Éxito**: el modal se cierra y la pantalla de trabajo se puebla con la nueva sesión.
6. **Error**: se muestra dentro del modal, sobre el botón, con el mensaje asociado al `code` y sin
   cerrar la ventana, de modo que el usuario pueda reintentar.
7. **Cancelación**: mensaje `Análisis cancelado. Se conservó la sesión anterior.`; el modal permanece
   abierto listo para un nuevo intento.

### Mensajes por `code`

| `code` | Mensaje |
|---|---|
| `missing_file` | Selecciona un archivo antes de continuar. |
| `unsupported_format` | Solo se admiten archivos .mp3 o .wav. |
| `payload_too_large` | El archivo supera el límite de 120 MB. |
| `invalid_audio` | El archivo no contiene audio legible. |
| `busy` | Ya hay un análisis en curso. Espera a que termine. |
| `cancelled` | Análisis cancelado. Se conservó la sesión anterior. |
| `transcription_unavailable` | El servicio de transcripción no está disponible. Inténtalo de nuevo. |
| `persistence_error` | No se pudo guardar la sesión. Se conservó la anterior. |

## Módulo de audio

### Waveform

- Amplitud calculada en el navegador con `AudioContext.decodeAudioData` sobre el archivo descargado
  de `GET /api/session/audio` (o del `blob` local mientras el backend no exponga el archivo), agregada
  en ~300 barras de 2 px con 1 px de separación.
- Tramo reproducido en azul primario; el resto en gris claro.
- Playhead: línea vertical de 2 px con un punto en la parte superior.
- Marcas de tiempo cada 25 % del ancho: `00:00`, `10:34`, `21:08`, `31:42`, `42:16`, en formato
  `mm:ss`.
- Clic o arrastre sobre la barra hace `seek` al instante correspondiente. Accesible con teclado:
  flechas ±5 s, `Home`/`End` a los extremos (`role="slider"`, `aria-valuetext` con el tiempo actual).
- Si la decodificación falla, se degrada a barra de progreso sólida sin romper la reproducción.

### Puntos de anotación

- Se posicionan por `start_time` del segmento o de la anotación, sobre el eje de la waveform.
- **Ámbar**: observaciones reales de la sesión. Al pasar el ratón o enfocar con teclado, muestran un
  tooltip con hora y los primeros 120 caracteres del texto.
- **Azul**: etiquetas clínicas. En este MVP no existen, así que no se renderizan; la leyenda las
  muestra atenuadas con "Próximamente".
- Los puntos deben ser alcanzables con `Tab` y anunciados con `aria-label` (hora + tipo).

### Controles

| Control | Comportamiento |
|---|---|
| Retroceder | −10 s, sin bajar de `0` |
| Reproducir / pausar | Alterna; icono grande y circular con `aria-label` dinámico |
| Adelantar | +10 s, sin pasar la duración |
| Tiempo | `mm:ss` actual / total, `aria-live="off"` para no saturar al lector de pantalla |
| Velocidad | Chips `1x`, `1.25x`, `1.5x`; solo uno activo (`aria-pressed`) |

## Columna 1 — Transcripción sincronizada (funcional)

Encabezado: `TRANSCRIPCIÓN SINCRONIZADA`, subtítulo `N segmentos · Español` y botón `Editar texto`
que alterna el modo edición del bloque completo.

Cada segmento es una tarjeta:

```text
┌───────────────────────────────────────────────────────────────┐
│ (02:31)                              [Tristeza · 85%]   │
│                                                               │
│ Me despierto varias veces durante la noche y cuando llega la   │
│ mañana estoy completamente agotado.                           │
│                                                               │
│ [ Etiqueta clínica ]  [ Observación ]                         │
│ ┌ chips de anotaciones existentes ──────────────────────────┐ │
│ │ 18:40 · Explorar red de apoyo…                    ✎  🗑   │ │
│ └───────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

Reglas:

1. **Timestamp**: chip `mm:ss` en azul relleno para el segmento activo y gris para el resto. Clic
   sobre el chip hace `seek` al inicio del segmento.
2. **Sin etiqueta de hablante**: el MVP transcribe un único hablante y no hace diarización, así que
   el fragmento no muestra "Paciente" ni ningún rol. Solo el timestamp y el texto.
3. **Badge de emoción**: **maqueta estática**. Muestra un valor de ejemplo atenuado con
   `title="Análisis afectivo fuera del alcance del MVP"`. No depende de la entrevista y no se
   actualiza.
4. **Avance en tiempo real**: el segmento cuyo rango contiene el tiempo actual se resalta (fondo azul
   muy claro y borde). La lista hace scroll suave para mantenerlo visible solo si el usuario no ha
   desplazado manualmente en los últimos 5 s.
5. **Modo edición**: el texto del segmento se vuelve `contenteditable` o `textarea`; los timestamps
   se editan en dos campos numéricos. Al guardar se envía la lista completa a
   `PUT /api/session/transcription`. Errores `invalid_timestamps` y `empty_text` se muestran junto al
   campo culpable.
6. **Acciones por segmento**: `Etiqueta clínica` está deshabilitada con `Próximamente`.
   `Observación` abre el formulario en línea (texto de 1 a 500 caracteres, contador visible).
7. **Anotaciones previas**: bajo el texto se listan los chips de anotaciones del segmento, con hora,
   texto truncado, editar y eliminar. Es la única forma de gestionar observaciones en este MVP.
8. **Accesibilidad de acciones**: nunca dependen solo de `hover`; aparecen también al enfocar con
   teclado y en pantallas táctiles.

## Columna 2 — Explicabilidad local (maqueta estática)

- Renderiza el título, un párrafo introductorio, dos frases de ejemplo con fragmentos resaltados, tres
  barras de confianza y un bloque "Resultado del modelo".
- Todos los datos son de ejemplo y están marcados visualmente como tal con la etiqueta
  `Vista previa · no disponible en este MVP`.
- No consume endpoints, no se recalcula y no reacciona al audio.
- Motivo: la explicabilidad XAI está fuera del alcance (`spec.md`, sección "Fuera de alcance"; `RF`).

## Columna 3 — Anotaciones (placeholder)

- Cabecera `Anotaciones` con botón `+` **deshabilitado** y tooltip `Disponible en una próxima
  iteración`.
- Contadores `0 Etiquetas` y `0 Observaciones`, calculados del estado real (siempre 0 en el MVP
  porque las etiquetas no existen y las observaciones no se agregan aquí).
- Secciones `Etiquetas clínicas` y `Observaciones` con estado vacío:
  `Las observaciones se gestionan desde cada fragmento.`
- Pie: botón `Exportar JSON / CSV` deshabilitado con `CSV próximamente`; la exportación real vive en
  la cabecera y produce JSON.

## Inventario de componentes

| Componente | Archivo | Responsabilidad |
|---|---|---|
| `WorkspaceLayout` | `frontend/src/components/WorkspaceLayout.jsx` | Grid de header + audio + tres columnas |
| `WorkspaceHeader` | `frontend/src/components/WorkspaceHeader.jsx` | Título, badge de estado, acciones y perfil |
| `NewInterviewModal` | `frontend/src/components/NewInterviewModal.jsx` | Carga, selector de modelo, confirmación y progreso |
| `SyntheticBanner` | `frontend/src/components/SyntheticBanner.jsx` | Aviso permanente de datos sintéticos |
| `AudioWaveform` | `frontend/src/components/AudioWaveform.jsx` | Barras, playhead, marcas y puntos |
| `PlayerControls` | `frontend/src/components/PlayerControls.jsx` | Transporte, tiempo y velocidades |
| `TranscriptList` | `frontend/src/components/TranscriptList.jsx` | Tarjetas, resaltado y scroll |
| `TranscriptEditor` | `frontend/src/components/TranscriptEditor.jsx` | Edición de texto y marcas |
| `AnnotationChip` | `frontend/src/components/AnnotationChip.jsx` | Anotación existente con editar/eliminar |
| `AnnotationForm` | `frontend/src/components/AnnotationForm.jsx` | Alta y edición con límite de 500 |
| `AnnotationPanel` | `frontend/src/components/AnnotationPanel.jsx` | Placeholder de la columna 3 |
| `ExplainabilityPreview` | `frontend/src/components/ExplainabilityPreview.jsx` | Maqueta estática XAI |
| `EmotionBadge` | `frontend/src/components/EmotionBadge.jsx` | Badge estático de emoción |
| `ExportPanel` | `frontend/src/components/ExportPanel.jsx` | Acción de exportación JSON |

## Accesibilidad

- Contraste mínimo AA en textos y controles.
- El modal atrapa el foco, lo devuelve al botón que lo abrió al cerrarse y responde a `Esc`.
- La barra de audio es un `slider` accesible; los puntos de anotación son `button` con `aria-label`.
- Los estados se anuncian con una región `aria-live="polite"` (`Analizando…`, `Análisis completado`,
  errores).
- Ningún control depende exclusivamente del color: los puntos llevan forma distinta (círculo vs
  rombo) además del color.

## Criterios de aceptación visual

1. Con la sesión vacía se ve solo el header y el CTA; las columnas no aparecen.
2. "Nueva entrevista" abre el modal con el fondo difuminado y el foco dentro de la tarjeta.
3. El botón `Analizar audio` está deshabilitado sin archivo o sin la confirmación marcada.
4. El selector muestra `Nube` habilitado y `Local` deshabilitado con `Próximamente`.
5. Durante el análisis se ve el indicador, el botón de cancelar y el badge `Analizando`.
6. Al completar, el modal se cierra y aparecen las tres columnas con la transcripción poblada.
7. La reproducción resalta el segmento activo y mueve el playhead y los puntos.
8. Al crear una observación desde un segmento, el chip aparece bajo ese segmento y un punto ámbar
   aparece en la barra.
9. El panel de explicabilidad y los badges de emoción se ven, pero llevan la marca de "vista previa"
   y no cambian con la entrevista.
10. Un error de carga muestra su mensaje dentro del modal y no borra la sesión anterior.

## Fuera de alcance en esta interfaz

- Análisis afectivo real y probabilidades emocionales.
- Explicabilidad XAI con datos reales.
- Etiquetas clínicas como entidad propia.
- Exportación CSV.
- Autenticación, perfiles, roles, navegación entre sesiones e historial.
- Múltiples hablantes y diarización.

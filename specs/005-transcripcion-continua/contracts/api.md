# Contrato API — sin cambios

**Feature**: `005-transcripcion-continua` · **Fecha**: 2026-11-07

Esta feature no añade, elimina ni modifica endpoints, esquemas de petición, códigos de respuesta ni
persistencia. El backend de `002` y `003` se mantiene intacto.

## Endpoints reutilizados

| Método | Ruta | Uso en esta feature |
|---|---|---|
| GET | `/api/session` | Obtener segmentos, timestamps y anotaciones para la vista continua |
| GET | `/api/session/audio` | Reproducir el audio y calcular la waveform |
| PUT | `/api/session/transcription` | Guardar la edición unificada con la lista completa de segmentos |
| POST | `/api/session/annotations` | Crear observaciones que luego se agrupan en el popover |
| PUT | `/api/session/annotations/{id}` | Editar observaciones desde el flujo actual |
| DELETE | `/api/session/annotations/{id}` | Eliminar observaciones desde el flujo actual |

## Sin cambios

- No se añaden campos nuevos al documento de sesión.
- No se añaden tablas ni migraciones.
- No se modifica el contrato de audio, exportación, carga ni cancelación.
- No se modifica el límite de 120 MB ni la sesión única.
- No se añaden dependencias ni servicios.

## Datos derivados en el cliente

La agrupación de observaciones, el perfil determinista de la waveform, el estado del auto-scroll y la
posición del popover se calculan en el frontend. No requieren persistencia ni endpoints adicionales.

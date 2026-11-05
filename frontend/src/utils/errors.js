const MESSAGES = {
  missing_file: 'Selecciona un archivo antes de continuar.',
  unsupported_format: 'Solo se admiten archivos .mp3 o .wav.',
  payload_too_large: 'El archivo supera el límite de 120 MB.',
  invalid_audio: 'El archivo no contiene audio legible.',
  busy: 'Ya hay un análisis en curso. Espera a que termine.',
  cancelled: 'Análisis cancelado. Se conservó la sesión anterior.',
  transcription_unavailable: 'El servicio de transcripción no está disponible. Inténtalo de nuevo.',
  persistence_error: 'No se pudo guardar la sesión. Se conservó la anterior.',
}

export function errorMessage(error) {
  if (!error) return ''
  return MESSAGES[error.code] ?? error.message ?? 'Error inesperado.'
}

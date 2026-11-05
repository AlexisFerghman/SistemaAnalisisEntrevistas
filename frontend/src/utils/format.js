export function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '00:00'
  const total = Math.floor(seconds)
  const minutes = Math.floor(total / 60)
  const rest = total % 60
  return `${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`
}

export function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** index
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

export const STATUS_LABELS = {
  empty: 'Sin audio',
  validating: 'Analizando',
  processing: 'Analizando',
  ready: 'Analizada',
  reviewed: 'Analizada',
  error: 'Error',
}

export function statusLabel(status) {
  return STATUS_LABELS[status] ?? 'Sin audio'
}

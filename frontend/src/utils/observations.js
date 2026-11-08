export const CLUSTER_THRESHOLD_PX = 14

function timeOf(marker) {
  const value = Number(marker?.time ?? 0)
  return Number.isFinite(value) ? Math.max(0, value) : 0
}

/**
 * Agrupa marcadores por proximidad horizontal en la waveform.
 *
 * @param {Array} markers marcadores con `id`, `time`, `text` y `segmentId`
 * @param {number} width ancho real de la waveform en píxeles
 * @param {number} duration duración total del audio en segundos
 * @param {number} threshold distancia máxima en píxeles
 */
export function groupObservations(
  markers = [],
  width = 0,
  duration = 0,
  threshold = CLUSTER_THRESHOLD_PX,
) {
  if (!Array.isArray(markers) || markers.length === 0) return []

  const sorted = [...markers].sort((left, right) => timeOf(left) - timeOf(right))
  const hasScale = width > 0 && duration > 0
  const xOf = (time) =>
    hasScale ? Math.min(Math.max(time / duration, 0), 1) * width : 0

  const groups = []

  for (const marker of sorted) {
    const time = timeOf(marker)
    const x = xOf(time)
    const last = groups[groups.length - 1]
    const closeEnough = hasScale
      ? Math.abs(x - last?._lastX) <= threshold
      : Math.abs(time - last?.anchor_time) < 1e-9

    if (last && closeEnough) {
      last.observations.push(marker)
      last.count = last.observations.length
      last._lastX = x
      continue
    }

    groups.push({
      id: `group-${marker.id}`,
      observations: [marker],
      count: 1,
      anchor_time: time,
      position_ratio: hasScale ? Math.min(Math.max(time / duration, 0), 1) : 0,
      _lastX: x,
    })
  }

  return groups.map(({ _lastX, ...group }) => group)
}

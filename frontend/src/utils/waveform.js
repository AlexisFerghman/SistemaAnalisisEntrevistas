function hashSeed(seed) {
  const text = String(seed ?? '')
  let hash = 2166136261
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function createSeededRandom(seed) {
  let state = hashSeed(seed) || 1
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0
    return state / 4294967296
  }
}

function clamp(value) {
  if (!Number.isFinite(value)) return 0
  return Math.min(1, Math.max(0, value))
}

/**
 * Aplica una modulación determinista a la amplitud real de la waveform.
 * La misma semilla produce siempre el mismo perfil.
 */
export function applyDeterministicVariation(peaks, seed = '') {
  if (!Array.isArray(peaks) || peaks.length === 0) return []

  const random = createSeededRandom(seed)
  const phase = (hashSeed(seed) % 360) * (Math.PI / 180)

  return peaks.map((peak, index) => {
    const base = clamp(Number(peak))
    const factor = 0.85 + random() * 0.3
    const wave =
      0.96 + 0.04 * Math.sin((index / peaks.length) * Math.PI * 4 + phase)
    return clamp(base * factor * wave)
  })
}

/**
 * Perfil de respaldo cuando no se puede decodificar el audio.
 */
export function buildFallbackPeaks(count = 120, seed = '') {
  const random = createSeededRandom(seed)
  return Array.from({ length: count }, (_, index) => {
    const base = 0.25 + 0.6 * Math.abs(Math.sin(index / 3))
    return clamp(base * (0.85 + random() * 0.3))
  })
}

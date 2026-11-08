import { describe, expect, it } from 'vitest'

import {
  applyDeterministicVariation,
  buildFallbackPeaks,
} from '../../src/utils/waveform'

const peaks = [0.1, 0.4, 0.9, 0.6, 0.2]

describe('waveform utils', () => {
  it('mantiene el mismo perfil para la misma semilla', () => {
    const first = applyDeterministicVariation(peaks, 'session-a')
    const second = applyDeterministicVariation(peaks, 'session-a')

    expect(first).toEqual(second)
  })

  it('genera perfiles distintos para sesiones distintas', () => {
    const first = applyDeterministicVariation(peaks, 'session-a')
    const second = applyDeterministicVariation(peaks, 'session-b')

    expect(first).not.toEqual(second)
  })

  it('conserva la longitud y no muta la entrada', () => {
    const original = [...peaks]
    const result = applyDeterministicVariation(peaks, 'session-a')

    expect(result).toHaveLength(peaks.length)
    expect(peaks).toEqual(original)
  })

  it('mantiene los valores dentro del rango visual', () => {
    const result = applyDeterministicVariation(peaks, 'session-a')

    for (const value of result) {
      expect(value).toBeGreaterThanOrEqual(0)
      expect(value).toBeLessThanOrEqual(1)
    }
  })

  it('genera un perfil de respaldo estable', () => {
    const first = buildFallbackPeaks(24, 'session-a')
    const second = buildFallbackPeaks(24, 'session-a')

    expect(first).toHaveLength(24)
    expect(first).toEqual(second)
  })
})

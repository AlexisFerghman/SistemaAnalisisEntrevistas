import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import AudioWaveform from '../src/components/AudioWaveform'

const PEAKS = [0.2, 0.8, 0.4, 0.6, 0.3]

function heights(container) {
  return Array.from(container.querySelectorAll('.waveform__bar')).map(
    (bar) => bar.style.height,
  )
}

describe('AudioWaveform estable por sesión', () => {
  it('mantiene el mismo perfil con la misma semilla', () => {
    const { container, rerender } = render(
      <AudioWaveform peaks={PEAKS} duration={10} visualSeed="session-a" />,
    )
    const first = heights(container)

    rerender(<AudioWaveform peaks={PEAKS} duration={10} visualSeed="session-a" />)

    expect(heights(container)).toEqual(first)
  })

  it('genera un perfil distinto para otra sesión', () => {
    const { container, rerender } = render(
      <AudioWaveform peaks={PEAKS} duration={10} visualSeed="session-a" />,
    )
    const first = heights(container)

    rerender(<AudioWaveform peaks={PEAKS} duration={10} visualSeed="session-b" />)

    expect(heights(container)).not.toEqual(first)
  })

  it('usa un perfil de respaldo estable si no hay peaks', () => {
    const { container, rerender } = render(
      <AudioWaveform peaks={null} duration={10} visualSeed="session-a" />,
    )
    const first = heights(container)

    rerender(<AudioWaveform peaks={null} duration={10} visualSeed="session-a" />)

    expect(heights(container)).toEqual(first)
    expect(first).toHaveLength(120)
  })
})

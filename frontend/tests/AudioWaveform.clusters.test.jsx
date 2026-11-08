import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import AudioWaveform from '../src/components/AudioWaveform'
import { stubRect } from './helpers/interactions'

const marker = (id, time, segmentId = `segment-${id}`) => ({
  id,
  time,
  text: `Observación ${id}`,
  segmentId,
  type: 'observacion',
})

async function renderWithWidth(markers, { width = 100, duration = 100 } = {}) {
  render(<AudioWaveform peaks={[0.5]} duration={duration} markers={markers} />)
  stubRect(screen.getByRole('slider'), { width })
  fireEvent(window, new Event('resize'))
  return screen.findByRole('slider')
}

describe('AudioWaveform clustering', () => {
  it('muestra un marcador agrupado con contador', async () => {
    await renderWithWidth([marker('a', 0), marker('b', 0.5), marker('c', 50)])

    expect(screen.getByRole('button', { name: '2 observaciones en 00:00' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '1 observación en 00:50' })).toBeInTheDocument()
  })

  it('usa el mismo marcador para una sola observación', async () => {
    await renderWithWidth([marker('a', 10)])

    expect(screen.getByRole('button', { name: '1 observación en 00:10' })).toBeInTheDocument()
  })

  it('recalcula los grupos al cambiar el ancho', async () => {
    render(
      <AudioWaveform
        peaks={[0.5]}
        duration={100}
        markers={[marker('a', 0), marker('b', 10)]}
      />,
    )
    const slider = screen.getByRole('slider')
    stubRect(slider, { width: 100 })
    fireEvent(window, new Event('resize'))

    expect(await screen.findByRole('button', { name: '2 observaciones en 00:00' })).toBeInTheDocument()

    stubRect(slider, { width: 1000 })
    fireEvent(window, new Event('resize'))

    expect(await screen.findByRole('button', { name: '1 observación en 00:00' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '1 observación en 00:10' })).toBeInTheDocument()
  })
})

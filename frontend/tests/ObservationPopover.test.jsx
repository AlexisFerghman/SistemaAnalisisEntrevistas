import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import AudioWaveform from '../src/components/AudioWaveform'
import { stubRect } from './helpers/interactions'

const MARKERS = [
  {
    id: 'annotation-1',
    time: 0,
    start_time: 0,
    text: 'Primera observación',
    segmentId: 'segment-001',
    type: 'observacion',
  },
  {
    id: 'annotation-2',
    time: 0.5,
    start_time: 0.5,
    text: 'Segunda observación',
    segmentId: 'segment-002',
    type: 'observacion',
  },
]

async function openPopover() {
  render(<AudioWaveform peaks={[0.5]} duration={100} markers={MARKERS} />)
  const slider = screen.getByRole('slider')
  stubRect(slider, { width: 100 })
  fireEvent(window, new Event('resize'))
  const marker = await screen.findByRole('button', { name: '2 observaciones en 00:00' })
  fireEvent.mouseEnter(marker)
  return { marker, popover: await screen.findByRole('dialog') }
}

describe('ObservationPopover', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('se abre con hover y lista todas las observaciones', async () => {
    const { popover } = await openPopover()

    expect(popover).toHaveTextContent('Primera observación')
    expect(popover).toHaveTextContent('Segunda observación')
  })

  it('se abre con foco de teclado', async () => {
    render(<AudioWaveform peaks={[0.5]} duration={100} markers={MARKERS} />)
    const slider = screen.getByRole('slider')
    stubRect(slider, { width: 100 })
    fireEvent(window, new Event('resize'))
    const marker = await screen.findByRole('button', { name: '2 observaciones en 00:00' })

    act(() => {
      marker.focus()
    })

    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    expect(marker).toHaveAttribute('aria-expanded', 'true')
  })

  it('se cierra con el botón de cerrar', async () => {
    const { popover } = await openPopover()

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar observaciones' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(popover).not.toBeInTheDocument()
  })

  it('se cierra con Escape y devuelve el foco al marcador', async () => {
    render(<AudioWaveform peaks={[0.5]} duration={100} markers={MARKERS} />)
    const slider = screen.getByRole('slider')
    stubRect(slider, { width: 100 })
    fireEvent(window, new Event('resize'))
    const marker = await screen.findByRole('button', { name: '2 observaciones en 00:00' })
    act(() => {
      marker.focus()
    })
    await screen.findByRole('dialog')

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(document.activeElement).toBe(marker)
  })

  it('se cierra al salir de la zona tras la tolerancia', async () => {
    const { marker } = await openPopover()
    vi.useFakeTimers()
    const wrapper = marker.closest('.waveform__marker-wrap')

    fireEvent.mouseLeave(wrapper)
    act(() => {
      vi.advanceTimersByTime(150)
    })

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

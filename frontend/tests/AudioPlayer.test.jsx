import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import AudioPlayer from '../src/components/AudioPlayer'

const SEGMENTS = [
  { id: 'segment-001', start_time: 0, end_time: 4, text: 'Primer fragmento', words: [] },
  { id: 'segment-002', start_time: 4, end_time: 10, text: 'Segundo fragmento', words: [] },
]

function renderPlayer(props = {}) {
  return render(
    <AudioPlayer
      src="/api/session/audio"
      duration={10}
      currentTime={0}
      segments={SEGMENTS}
      annotations={[]}
      onTimeUpdate={vi.fn()}
      {...props}
    />,
  )
}

describe('AudioPlayer', () => {
  it('empieza en 1x y cambia de velocidad', () => {
    renderPlayer()

    expect(screen.getByRole('button', { name: '1x' })).toHaveAttribute('aria-pressed', 'true')

    fireEvent.click(screen.getByRole('button', { name: '1.25x' }))

    expect(screen.getByRole('button', { name: '1.25x' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '1x' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: '1.5x' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('reproduce cuando se pulsa el botón de reproducción', () => {
    renderPlayer()

    fireEvent.click(screen.getByRole('button', { name: 'Reproducir' }))

    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled()
  })

  it('adelanta y retrocede sin salir de los límites', () => {
    const onTimeUpdate = vi.fn()
    renderPlayer({ currentTime: 5, onTimeUpdate })

    fireEvent.click(screen.getByRole('button', { name: 'Adelantar 10 segundos' }))
    expect(onTimeUpdate).toHaveBeenLastCalledWith(10)

    fireEvent.click(screen.getByRole('button', { name: 'Retroceder 10 segundos' }))
    expect(onTimeUpdate).toHaveBeenLastCalledWith(0)
  })

  it('aplica una solicitud de salto externa', () => {
    const onTimeUpdate = vi.fn()
    const { rerender } = renderPlayer({ onTimeUpdate })

    rerender(
      <AudioPlayer
        src="/api/session/audio"
        duration={10}
        currentTime={0}
        segments={SEGMENTS}
        annotations={[]}
        onTimeUpdate={onTimeUpdate}
        seekRequest={{ time: 6, id: 1 }}
      />,
    )

    expect(onTimeUpdate).toHaveBeenCalledWith(6)
  })

  it('hace seek y reproduce con una solicitud de play', () => {
    const onTimeUpdate = vi.fn()
    HTMLMediaElement.prototype.play.mockClear()
    const { rerender } = renderPlayer({ onTimeUpdate })

    rerender(
      <AudioPlayer
        src="/api/session/audio"
        duration={10}
        currentTime={0}
        segments={SEGMENTS}
        annotations={[]}
        onTimeUpdate={onTimeUpdate}
        playRequest={{ time: 4, id: 1 }}
      />,
    )

    expect(onTimeUpdate).toHaveBeenCalledWith(4)
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled()
  })

  it('muestra el tiempo actual y la duración', () => {
    renderPlayer({ currentTime: 90, duration: 120 })

    expect(screen.getByText('01:30 / 02:00')).toBeInTheDocument()
  })
})

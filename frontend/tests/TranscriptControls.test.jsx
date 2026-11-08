import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import TranscriptList from '../src/components/TranscriptList'

const SEGMENTS = [
  { id: 'segment-001', start_time: 0, end_time: 4, text: 'Primero', words_count: 2 },
  { id: 'segment-002', start_time: 4, end_time: 8, text: 'Segundo', words_count: 2 },
]

describe('TranscriptList controles explícitos', () => {
  it('hace seek al pulsar el chip de tiempo', () => {
    const onSeek = vi.fn()
    render(<TranscriptList segments={SEGMENTS} onSeek={onSeek} />)

    fireEvent.click(screen.getByRole('button', { name: 'Ir a 00:00' }))

    expect(onSeek).toHaveBeenCalledWith(0)
  })

  it('hace seek y reproduce al pulsar el botón play', () => {
    const onPlay = vi.fn()
    render(<TranscriptList segments={SEGMENTS} onPlay={onPlay} />)

    fireEvent.click(screen.getByRole('button', { name: 'Reproducir desde 00:04' }))

    expect(onPlay).toHaveBeenCalledWith(4)
  })

  it('no hace seek al hacer clic sobre el texto del segmento', () => {
    const onSeek = vi.fn()
    const onPlay = vi.fn()
    render(<TranscriptList segments={SEGMENTS} onSeek={onSeek} onPlay={onPlay} />)

    fireEvent.click(screen.getByText('Primero'))

    expect(onSeek).not.toHaveBeenCalled()
    expect(onPlay).not.toHaveBeenCalled()
  })
})

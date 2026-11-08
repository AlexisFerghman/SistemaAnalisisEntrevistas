import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import TranscriptList from '../src/components/TranscriptList'
import {
  installMatchMedia,
  installScrollIntoViewMock,
} from './helpers/interactions'

const SEGMENTS = [
  { id: 'segment-001', start_time: 0, end_time: 4, text: 'Primero', words_count: 2 },
  { id: 'segment-002', start_time: 4, end_time: 8, text: 'Segundo', words_count: 2 },
  { id: 'segment-003', start_time: 8, end_time: 12, text: 'Tercero', words_count: 2 },
]

describe('TranscriptList continuo', () => {
  let scroll
  let media

  afterEach(() => {
    scroll?.restore()
    media?.restore()
    vi.useRealTimers()
  })

  it('desplaza el segmento activo con comportamiento suave', () => {
    scroll = installScrollIntoViewMock()
    media = installMatchMedia({ reducedMotion: false })

    render(<TranscriptList segments={SEGMENTS} currentTime={0} />)

    expect(scroll.spy).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' })
  })

  it('pausa el seguimiento tras scroll manual y lo reanuda a los 5 s', () => {
    scroll = installScrollIntoViewMock()
    media = installMatchMedia({ reducedMotion: false })
    vi.useFakeTimers()

    const { rerender } = render(<TranscriptList segments={SEGMENTS} currentTime={0} />)
    scroll.spy.mockClear()

    fireEvent.wheel(screen.getByRole('list'))
    rerender(<TranscriptList segments={SEGMENTS} currentTime={5} />)

    expect(scroll.spy).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Volver al audio' })).toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(5000)
    })

    expect(scroll.spy).toHaveBeenCalled()
  })

  it('reanuda el seguimiento sin hacer seek al pulsar Volver al audio', () => {
    scroll = installScrollIntoViewMock()
    media = installMatchMedia({ reducedMotion: false })
    const onSeek = vi.fn()

    render(<TranscriptList segments={SEGMENTS} currentTime={0} onSeek={onSeek} />)
    fireEvent.wheel(screen.getByRole('list'))
    scroll.spy.mockClear()

    fireEvent.click(screen.getByRole('button', { name: 'Volver al audio' }))

    expect(onSeek).not.toHaveBeenCalled()
    expect(scroll.spy).toHaveBeenCalled()
  })

  it('respeta prefers-reduced-motion', () => {
    scroll = installScrollIntoViewMock()
    media = installMatchMedia({ reducedMotion: true })

    render(<TranscriptList segments={SEGMENTS} currentTime={0} />)

    expect(scroll.spy).toHaveBeenCalledWith({ behavior: 'auto', block: 'center' })
  })

  it('revela un fragmento sin hacer seek y pausa el seguimiento', () => {
    scroll = installScrollIntoViewMock()
    media = installMatchMedia({ reducedMotion: false })
    const onSeek = vi.fn()

    const { rerender } = render(
      <TranscriptList segments={SEGMENTS} currentTime={0} onSeek={onSeek} />,
    )
    scroll.spy.mockClear()

    rerender(
      <TranscriptList
        segments={SEGMENTS}
        currentTime={0}
        onSeek={onSeek}
        revealRequest={{ segmentId: 'segment-003', id: 1 }}
      />,
    )

    expect(scroll.spy).toHaveBeenCalled()
    expect(onSeek).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Volver al audio' })).toBeInTheDocument()
  })
})

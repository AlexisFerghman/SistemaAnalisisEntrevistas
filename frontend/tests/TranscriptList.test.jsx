import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import TranscriptList from '../src/components/TranscriptList'

const SEGMENTS = [
  {
    id: 'segment-001',
    start_time: 0,
    end_time: 4,
    text: 'Primer fragmento',
    words_count: 7,
  },
  {
    id: 'segment-002',
    start_time: 4,
    end_time: 10,
    text: 'Segundo fragmento',
    words: [{ text: 'Segundo', start_time: 4, end_time: 5 }],
  },
]

describe('TranscriptList', () => {
  it('muestra words_count cuando la respuesta es resumida', () => {
    render(<TranscriptList segments={SEGMENTS} />)

    expect(screen.getByText('7 palabras con marcas')).toBeInTheDocument()
  })

  it('usa words.length cuando la respuesta es completa', () => {
    render(<TranscriptList segments={SEGMENTS} />)

    expect(screen.getByText('1 palabras con marcas')).toBeInTheDocument()
  })

  it('desplaza el segmento activo cuando el usuario no ha hecho scroll manual', () => {
    const original = Element.prototype.scrollIntoView
    const scrollIntoView = vi.fn()
    Element.prototype.scrollIntoView = scrollIntoView

    try {
      render(<TranscriptList segments={SEGMENTS} currentTime={0} />)

      expect(scrollIntoView).toHaveBeenCalled()
    } finally {
      Element.prototype.scrollIntoView = original
    }
  })

  it('respeta el scroll manual reciente y no fuerza el segmento activo', () => {
    const original = Element.prototype.scrollIntoView
    const scrollIntoView = vi.fn()
    Element.prototype.scrollIntoView = scrollIntoView

    try {
      const { rerender } = render(<TranscriptList segments={SEGMENTS} currentTime={0} />)
      scrollIntoView.mockClear()

      fireEvent.wheel(screen.getByRole('list'))
      rerender(<TranscriptList segments={SEGMENTS} currentTime={5} />)

      expect(scrollIntoView).not.toHaveBeenCalled()
    } finally {
      Element.prototype.scrollIntoView = original
    }
  })
})

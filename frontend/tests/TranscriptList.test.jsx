import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

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
})

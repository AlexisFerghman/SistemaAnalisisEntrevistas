import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import TranscriptEditor from '../src/components/TranscriptEditor'

const SEGMENTS = [
  { id: 'segment-001', start_time: 0, end_time: 4, text: 'Primer fragmento completo' },
  { id: 'segment-002', start_time: 4, end_time: 8, text: 'Segundo fragmento completo' },
  { id: 'segment-003', start_time: 8, end_time: 12, text: 'Tercer fragmento completo' },
]

describe('TranscriptEditor unificado', () => {
  it('muestra todos los segmentos en un único flujo con timestamps', () => {
    render(<TranscriptEditor segments={SEGMENTS} duration={12} onSave={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getAllByTestId('editor-block')).toHaveLength(3)
    expect(screen.getByDisplayValue('Primer fragmento completo')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Segundo fragmento completo')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Tercer fragmento completo')).toBeInTheDocument()
    expect(screen.getByText('00:00')).toBeInTheDocument()
    expect(screen.getByText('00:04')).toBeInTheDocument()
    expect(screen.getByText('00:08')).toBeInTheDocument()
  })

  it('conserva el texto completo sin truncarlo', () => {
    const longText = 'Texto completo '.repeat(40)
    render(
      <TranscriptEditor
        segments={[{ ...SEGMENTS[0], text: longText }]}
        duration={12}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
    )

    expect(screen.getByLabelText('Texto del segmento 1')).toHaveValue(longText)
  })
})

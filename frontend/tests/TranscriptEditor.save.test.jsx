import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import TranscriptEditor from '../src/components/TranscriptEditor'

const SEGMENTS = [
  { id: 'segment-001', start_time: 0, end_time: 4, text: 'Primero' },
  { id: 'segment-002', start_time: 4, end_time: 8, text: 'Segundo' },
]

function editor(props = {}) {
  return render(
    <TranscriptEditor
      segments={SEGMENTS}
      duration={12}
      onSave={vi.fn()}
      onCancel={vi.fn()}
      {...props}
    />,
  )
}

describe('TranscriptEditor guardado', () => {
  it('envía la lista completa con identidad y timestamps', () => {
    const onSave = vi.fn()
    editor({ onSave })

    fireEvent.change(screen.getByLabelText('Texto del segmento 1'), {
      target: { value: 'Texto corregido' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect(onSave).toHaveBeenCalledWith([
      { id: 'segment-001', start_time: 0, end_time: 4, text: 'Texto corregido' },
      { id: 'segment-002', start_time: 4, end_time: 8, text: 'Segundo' },
    ])
  })

  it('bloquea el guardado con texto vacío', () => {
    const onSave = vi.fn()
    editor({ onSave })

    fireEvent.change(screen.getByLabelText('Texto del segmento 1'), {
      target: { value: '   ' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect(onSave).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent('El texto no puede estar vacío')
  })

  it('bloquea el guardado con timestamps solapados', () => {
    const onSave = vi.fn()
    editor({ onSave })

    fireEvent.change(screen.getByLabelText('Inicio del segmento 2'), {
      target: { value: '2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect(onSave).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent('se solapa')
  })
})

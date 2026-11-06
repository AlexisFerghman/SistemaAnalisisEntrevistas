import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import AnnotationForm from '../src/components/AnnotationForm'

describe('AnnotationForm', () => {
  it('muestra el contador de caracteres', () => {
    render(<AnnotationForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Texto de la observación'), {
      target: { value: 'Hola' },
    })

    expect(screen.getByText('4/500')).toBeInTheDocument()
  })

  it('bloquea el guardado con el texto vacío', () => {
    render(<AnnotationForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getByRole('button', { name: 'Guardar' })).toBeDisabled()
  })

  it('bloquea el guardado por encima de 500 caracteres', () => {
    const onSubmit = vi.fn()
    render(<AnnotationForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Texto de la observación'), {
      target: { value: 'a'.repeat(501) },
    })

    expect(screen.getByText('501/500')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('no puede superar los 500 caracteres')
    expect(screen.getByRole('button', { name: 'Guardar' })).toBeDisabled()

    fireEvent.submit(screen.getByRole('button', { name: 'Guardar' }).closest('form'))
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('permite guardar con 500 caracteres exactos', () => {
    const onSubmit = vi.fn()
    render(<AnnotationForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Texto de la observación'), {
      target: { value: 'a'.repeat(500) },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(onSubmit).toHaveBeenCalledWith('a'.repeat(500))
  })

  it('parte del texto existente al editar', () => {
    render(<AnnotationForm initialText="Original" onSubmit={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getByLabelText('Texto de la observación')).toHaveValue('Original')
  })
})

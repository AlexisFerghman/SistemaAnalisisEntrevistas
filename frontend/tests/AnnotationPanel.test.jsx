import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import AnnotationPanel from '../src/components/AnnotationPanel'

describe('AnnotationPanel', () => {
  it('deshabilita la exportación mientras no hay una sesión lista', () => {
    render(<AnnotationPanel canExport={false} />)

    expect(screen.getByRole('button', { name: 'Exportar JSON' })).toBeDisabled()
  })

  it('exporta JSON cuando la sesión está lista', () => {
    const onExport = vi.fn()
    render(<AnnotationPanel canExport onExport={onExport} />)

    fireEvent.click(screen.getByRole('button', { name: 'Exportar JSON' }))

    expect(onExport).toHaveBeenCalledTimes(1)
  })

  it('bloquea el botón mientras la exportación está en curso', () => {
    render(<AnnotationPanel canExport exporting />)

    expect(screen.getByRole('button', { name: 'Exportando…' })).toBeDisabled()
  })
})

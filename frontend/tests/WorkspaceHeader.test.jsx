import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import WorkspaceHeader from '../src/components/WorkspaceHeader'

const READY_SESSION = {
  status: 'ready',
  audio: {
    filename: 'entrevista.wav',
    duration_seconds: 120,
  },
}

describe('WorkspaceHeader', () => {
  it('habilita la exportación con una sesión lista', () => {
    const onExport = vi.fn()
    render(<WorkspaceHeader session={READY_SESSION} onExport={onExport} />)

    const button = screen.getByRole('button', { name: 'Exportar datos' })
    expect(button).toBeEnabled()

    fireEvent.click(button)
    expect(onExport).toHaveBeenCalledTimes(1)
  })

  it('deshabilita la exportación sin una sesión lista', () => {
    render(<WorkspaceHeader session={{ status: 'empty' }} />)

    expect(screen.getByRole('button', { name: 'Exportar datos' })).toBeDisabled()
  })

  it('bloquea la exportación mientras está en curso', () => {
    render(<WorkspaceHeader session={READY_SESSION} exporting />)

    expect(screen.getByRole('button', { name: 'Exportando…' })).toBeDisabled()
  })
})

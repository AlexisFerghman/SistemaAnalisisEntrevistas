import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import AudioWaveform from '../src/components/AudioWaveform'
import { stubRect } from './helpers/interactions'

const MARKER = {
  id: 'annotation-1',
  time: 3,
  start_time: 3,
  text: 'Observación con fragmento',
  segmentId: 'segment-003',
  type: 'observacion',
}

describe('ObservationPopover — Ver fragmento', () => {
  it('revela el segmento sin hacer seek y cierra el popover', async () => {
    const onRevealSegment = vi.fn()
    const onSeek = vi.fn()
    render(
      <AudioWaveform
        peaks={[0.5]}
        duration={100}
        markers={[MARKER]}
        onSeek={onSeek}
        onRevealSegment={onRevealSegment}
      />,
    )
    const slider = screen.getByRole('slider')
    stubRect(slider, { width: 100 })
    fireEvent(window, new Event('resize'))
    const marker = await screen.findByRole('button', { name: '1 observación en 00:03' })

    fireEvent.mouseEnter(marker)
    fireEvent.click(await screen.findByRole('button', { name: 'Ver fragmento' }))

    expect(onRevealSegment).toHaveBeenCalledWith('segment-003')
    expect(onSeek).not.toHaveBeenCalled()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import AudioWaveform from '../src/components/AudioWaveform'

function stubRect(element, width = 100) {
  element.getBoundingClientRect = () => ({
    left: 0,
    top: 0,
    right: width,
    bottom: 20,
    width,
    height: 20,
    x: 0,
    y: 0,
    toJSON: () => {},
  })
}

describe('AudioWaveform', () => {
  it('hace seek al hacer clic', () => {
    const onSeek = vi.fn()
    render(<AudioWaveform peaks={[0.5]} duration={100} currentTime={0} onSeek={onSeek} />)
    const slider = screen.getByRole('slider')
    stubRect(slider)

    fireEvent.click(slider, { clientX: 25 })

    expect(onSeek).toHaveBeenLastCalledWith(25)
  })

  it('hace seek al arrastrar con el puntero', () => {
    const onSeek = vi.fn()
    render(<AudioWaveform peaks={[0.5]} duration={100} currentTime={0} onSeek={onSeek} />)
    const slider = screen.getByRole('slider')
    stubRect(slider)

    fireEvent.pointerDown(slider, { clientX: 10, button: 0, pointerId: 1 })
    fireEvent.pointerMove(slider, { clientX: 45, pointerId: 1 })
    fireEvent.pointerUp(slider, { clientX: 70, pointerId: 1 })

    expect(onSeek).toHaveBeenLastCalledWith(70)
  })

  it('mantiene el seek por teclado', () => {
    const onSeek = vi.fn()
    render(<AudioWaveform peaks={[0.5]} duration={100} currentTime={40} onSeek={onSeek} />)
    const slider = screen.getByRole('slider')

    fireEvent.keyDown(slider, { key: 'ArrowRight' })

    expect(onSeek).toHaveBeenLastCalledWith(45)
  })
})

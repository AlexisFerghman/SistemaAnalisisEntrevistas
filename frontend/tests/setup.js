import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'

// jsdom no implementa la reproducción de audio: se simulan los métodos mínimos.
Object.defineProperty(HTMLMediaElement.prototype, 'play', {
  configurable: true,
  writable: true,
  value: vi.fn().mockResolvedValue(undefined),
})

Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
  configurable: true,
  writable: true,
  value: vi.fn(),
})

Object.defineProperty(HTMLMediaElement.prototype, 'currentTime', {
  configurable: true,
  writable: true,
  value: 0,
})

// jsdom no implementa PointerEvent: se usa MouseEvent para las pruebas de arrastre.
if (typeof window.PointerEvent === 'undefined') {
  window.PointerEvent = window.MouseEvent
}

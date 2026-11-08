import { vi } from 'vitest'

export function stubRect(element, { left = 0, width = 100, height = 20 } = {}) {
  element.getBoundingClientRect = () => ({
    left,
    top: 0,
    right: left + width,
    bottom: height,
    width,
    height,
    x: left,
    y: 0,
    toJSON: () => {},
  })
}

export function installScrollIntoViewMock() {
  const original = Element.prototype.scrollIntoView
  const spy = vi.fn()
  Element.prototype.scrollIntoView = spy
  return {
    spy,
    restore() {
      Element.prototype.scrollIntoView = original
    },
  }
}

export function installMatchMedia({ reducedMotion = false } = {}) {
  const original = window.matchMedia
  window.matchMedia = vi.fn().mockImplementation((query) => ({
    matches: query.includes('prefers-reduced-motion') ? reducedMotion : false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }))
  return {
    restore() {
      window.matchMedia = original
    },
  }
}

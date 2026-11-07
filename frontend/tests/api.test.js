import { afterEach, describe, expect, it, vi } from 'vitest'

import { uploadAudio } from '../src/services/api'

describe('uploadAudio', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('envía el archivo y el modelo seleccionado', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ session: { status: 'ready' } }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const file = new File(['contenido'], 'entrevista.wav', { type: 'audio/wav' })
    await uploadAudio(file, 'nube')

    const body = fetchMock.mock.calls[0][1].body
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('file')).toBe(file)
    expect(body.get('model')).toBe('nube')
  })
})

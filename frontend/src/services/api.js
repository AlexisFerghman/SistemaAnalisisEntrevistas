const BASE = import.meta.env.VITE_API_URL || ''

async function parseError(response) {
  try {
    const body = await response.json()
    return body?.error ?? { code: `http_${response.status}`, message: 'Error inesperado' }
  } catch {
    return { code: `http_${response.status}`, message: 'Error inesperado' }
  }
}

export async function getSession() {
  const response = await fetch(`${BASE}/api/session`)
  if (response.status === 404) return null
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function getSegmentWords(segmentId) {
  const response = await fetch(
    `${BASE}/api/session/segments/${encodeURIComponent(segmentId)}/words`,
  )
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function uploadAudio(file, model = 'nube') {
  const body = new FormData()
  body.append('file', file)
  body.append('model', model)

  const response = await fetch(`${BASE}/api/session/audio`, { method: 'POST', body })
  if (!response.ok) {
    const error = await parseError(response)
    throw error
  }
  const data = await response.json()
  return data.session
}

export async function cancelUpload() {
  const response = await fetch(`${BASE}/api/session/cancel`, { method: 'POST' })
  if (!response.ok && response.status !== 409) throw await parseError(response)
  return response.status
}

export async function updateTranscription(segments) {
  const response = await fetch(`${BASE}/api/session/transcription`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ segments }),
  })
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function createAnnotation(payload) {
  const response = await fetch(`${BASE}/api/session/annotations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function updateAnnotation(annotationId, payload) {
  const response = await fetch(`${BASE}/api/session/annotations/${annotationId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function deleteAnnotation(annotationId) {
  const response = await fetch(`${BASE}/api/session/annotations/${annotationId}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw await parseError(response)
  return true
}

export async function exportSession() {
  const response = await fetch(`${BASE}/api/session/export`, { method: 'POST' })
  if (!response.ok) throw await parseError(response)
  return response.json()
}

import { useCallback, useEffect, useState } from 'react'
import AnnotationPanel from './components/AnnotationPanel'
import AudioPlayer from './components/AudioPlayer'
import ExplainabilityPreview from './components/ExplainabilityPreview'
import NewInterviewModal from './components/NewInterviewModal'
import TranscriptEditor from './components/TranscriptEditor'
import TranscriptList from './components/TranscriptList'
import WorkspaceLayout from './components/WorkspaceLayout'
import {
  createAnnotation,
  deleteAnnotation,
  exportSession,
  getSession,
  updateAnnotation,
  updateTranscription,
} from './services/api'
import { errorMessage } from './utils/errors'

function downloadJson(payload) {
  if (
    typeof window === 'undefined' ||
    typeof URL === 'undefined' ||
    typeof URL.createObjectURL !== 'function'
  ) {
    return
  }

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = window.document.createElement('a')
  link.href = url
  link.download = 'sesion-exportada.json'
  window.document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function EmptyState({ onNewInterview }) {
  return (
    <section className="empty-state">
      <span className="empty-state__icon" aria-hidden="true">↑</span>
      <h2>Aún no hay ninguna entrevista</h2>
      <p>Carga un audio sintético para transcribirlo, revisarlo y anotarlo.</p>
      <button type="button" className="button button--primary" onClick={onNewInterview}>
        Subir audio
      </button>
    </section>
  )
}

export default function App() {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [notice, setNotice] = useState(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [seekRequest, setSeekRequest] = useState(null)
  const [playRequest, setPlayRequest] = useState(null)
  const [revealRequest, setRevealRequest] = useState(null)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editError, setEditError] = useState(null)
  const [annotationSaving, setAnnotationSaving] = useState(false)
  const [exporting, setExporting] = useState(false)

  const refresh = useCallback(async () => {
    const data = await getSession()
    setSession(data)
    return data
  }, [])

  useEffect(() => {
    refresh()
      .catch(() => setNotice('No se pudo conectar con la API.'))
      .finally(() => setLoading(false))
  }, [refresh])

  const handleSeek = useCallback((time) => {
    setCurrentTime(time)
    setSeekRequest({ time, id: Date.now() })
  }, [])

  const handlePlayFrom = useCallback((time) => {
    setCurrentTime(time)
    setPlayRequest({ time, id: Date.now() })
  }, [])

  const handleRevealSegment = useCallback((segmentId) => {
    setRevealRequest({ segmentId, id: Date.now() })
  }, [])

  function handleCompleted(nextSession) {
    setSession(nextSession)
    setModalOpen(false)
    setNotice(null)
    setCurrentTime(0)
    setSeekRequest(null)
    setPlayRequest(null)
    setRevealRequest(null)
    setEditing(false)
  }

  async function handleSave(segments) {
    setSaving(true)
    setEditError(null)
    try {
      const updated = await updateTranscription(segments)
      setSession(updated)
      setEditing(false)
    } catch (problem) {
      setEditError(errorMessage(problem))
    } finally {
      setSaving(false)
    }
  }

  async function handleExport() {
    setExporting(true)
    setNotice(null)
    try {
      const result = await exportSession()
      downloadJson(result.document)
      setNotice('Sesión exportada correctamente. El documento JSON se guardó en la ranura de exportación.')
    } catch (problem) {
      setNotice(errorMessage(problem))
    } finally {
      setExporting(false)
    }
  }

  async function runAnnotation(action) {
    setAnnotationSaving(true)
    try {
      await action()
      await refresh()
      setNotice(null)
    } catch (problem) {
      setNotice(errorMessage(problem))
      throw problem
    } finally {
      setAnnotationSaving(false)
    }
  }

  function handleCreateAnnotation(segmentId, text, startTime, endTime) {
    return runAnnotation(() =>
      createAnnotation({
        text,
        segment_id: segmentId,
        start_time: startTime,
        end_time: endTime,
      }),
    )
  }

  function handleUpdateAnnotation(annotationId, text, segmentId, startTime, endTime) {
    return runAnnotation(() =>
      updateAnnotation(annotationId, {
        text,
        segment_id: segmentId,
        start_time: startTime,
        end_time: endTime,
      }),
    )
  }

  function handleDeleteAnnotation(annotation) {
    return runAnnotation(() => deleteAnnotation(annotation.id))
  }

  const hasAudio = Boolean(session?.audio && session?.transcription)
  const canExport = session?.status === 'ready' || session?.status === 'reviewed'
  const segments = session?.transcription?.segments ?? []

  return (
    <>
      <WorkspaceLayout
        session={session}
        onNewInterview={() => setModalOpen(true)}
        onExport={handleExport}
        exporting={exporting}
      >
        {notice && (
          <p className="notice" role="status">
            {notice}
          </p>
        )}

        {loading ? (
          <p className="notice">Cargando sesión…</p>
        ) : hasAudio ? (
          <>
            <AudioPlayer
              src="/api/session/audio"
              duration={session.audio.duration_seconds}
              currentTime={currentTime}
              segments={segments}
              annotations={session.annotations ?? []}
              seekRequest={seekRequest}
              playRequest={playRequest}
              onTimeUpdate={setCurrentTime}
              onRevealSegment={handleRevealSegment}
              visualSeed={session.session_id || session.audio?.storage_ref || 'session'}
            />

            <div className="workspace-grid">
              <div className="workspace-grid__transcript">
                {editing ? (
                  <TranscriptEditor
                    segments={segments}
                    duration={session.audio.duration_seconds}
                    saving={saving}
                    error={editError}
                    onSave={handleSave}
                    onCancel={() => {
                      setEditing(false)
                      setEditError(null)
                    }}
                  />
                ) : (
                  <TranscriptList
                    segments={segments}
                    currentTime={currentTime}
                    annotations={session.annotations ?? []}
                    saving={annotationSaving}
                    revealRequest={revealRequest}
                    onSeek={handleSeek}
                    onPlay={handlePlayFrom}
                    onStartEdit={() => {
                      setEditing(true)
                      setEditError(null)
                    }}
                    onCreate={handleCreateAnnotation}
                    onUpdate={handleUpdateAnnotation}
                    onDelete={handleDeleteAnnotation}
                  />
                )}
              </div>

              <ExplainabilityPreview />

              <AnnotationPanel
                annotations={session.annotations ?? []}
                onExport={handleExport}
                exporting={exporting}
                canExport={canExport}
              />
            </div>
          </>
        ) : (
          <EmptyState onNewInterview={() => setModalOpen(true)} />
        )}
      </WorkspaceLayout>

      {modalOpen && (
        <NewInterviewModal onClose={() => setModalOpen(false)} onCompleted={handleCompleted} />
      )}
    </>
  )
}

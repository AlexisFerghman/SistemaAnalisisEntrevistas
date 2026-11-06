import { useCallback, useEffect, useState } from 'react'
import AnnotationPanel from './components/AnnotationPanel'
import AudioPlayer from './components/AudioPlayer'
import NewInterviewModal from './components/NewInterviewModal'
import TranscriptEditor from './components/TranscriptEditor'
import TranscriptList from './components/TranscriptList'
import WorkspaceLayout from './components/WorkspaceLayout'
import {
  createAnnotation,
  deleteAnnotation,
  getSession,
  updateAnnotation,
  updateTranscription,
} from './services/api'
import { errorMessage } from './utils/errors'

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
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editError, setEditError] = useState(null)
  const [annotationSaving, setAnnotationSaving] = useState(false)

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

  function handleCompleted(nextSession) {
    setSession(nextSession)
    setModalOpen(false)
    setNotice(null)
    setCurrentTime(0)
    setSeekRequest(null)
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

  function handleExport() {
    setNotice('La exportación se habilita en la fase de exportación del proyecto.')
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
  const segments = session?.transcription?.segments ?? []

  return (
    <>
      <WorkspaceLayout
        session={session}
        onNewInterview={() => setModalOpen(true)}
        onExport={handleExport}
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
              onTimeUpdate={setCurrentTime}
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
                    onSeek={handleSeek}
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

              <div className="workspace-grid__xai" aria-label="Explicabilidad local">
                <h2 className="grid-title">EXPLICABILIDAD LOCAL</h2>
                <p className="annotation-panel__empty">Vista previa · no disponible en este MVP</p>
              </div>

              <AnnotationPanel annotations={session.annotations ?? []} />
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

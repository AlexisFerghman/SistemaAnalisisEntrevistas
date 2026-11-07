import { useEffect, useRef, useState } from 'react'
import UploadPanel from './UploadPanel'
import { cancelUpload, uploadAudio } from '../services/api'
import { errorMessage } from '../utils/errors'

const MODELS = [
  { id: 'nube', label: 'Nube', detail: 'faster-whisper base', enabled: true },
  { id: 'local', label: 'Local', detail: 'en el dispositivo', enabled: false },
]

export default function NewInterviewModal({ onClose, onCompleted }) {
  const [file, setFile] = useState(null)
  const [model, setModel] = useState('nube')
  const [confirmed, setConfirmed] = useState(false)
  const [phase, setPhase] = useState('idle')
  const [error, setError] = useState(null)
  const cardRef = useRef(null)

  const uploading = phase === 'uploading'

  useEffect(() => {
    cardRef.current?.querySelector('input[type="file"]')?.focus()
    const previous = document.activeElement

    function onKeyDown(event) {
      if (event.key === 'Escape' && !uploading) {
        onClose()
        return
      }
      if (event.key !== 'Tab' || !cardRef.current) return

      const focusable = cardRef.current.querySelectorAll(
        'button:not([disabled]), input:not([disabled]), [tabindex="0"]',
      )
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      if (previous instanceof HTMLElement) previous.focus()
    }
  }, [onClose, uploading])

  function handleSelect(selected, problem) {
    setError(problem)
    setFile(problem ? null : selected)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!file || !confirmed || uploading) return

    setPhase('uploading')
    setError(null)
    try {
      const session = await uploadAudio(file, model)
      setPhase('done')
      onCompleted(session)
    } catch (problem) {
      setPhase('idle')
      setError(problem)
    }
  }

  async function handleCancelUpload() {
    try {
      await cancelUpload()
    } catch (problem) {
      setError(problem)
    }
  }

  const canSubmit = Boolean(file) && confirmed && !uploading

  return (
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !uploading) onClose()
      }}
    >
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-title" ref={cardRef}>
        <div className="modal-card__header">
          <h2 id="modal-title">Nueva entrevista</h2>
          <button type="button" className="icon-button" onClick={onClose} disabled={uploading} aria-label="Cerrar">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-card__body">
          <UploadPanel file={file} onSelect={handleSelect} disabled={uploading} />

          <fieldset className="model-selector" disabled={uploading}>
            <legend>Modelo de transcripción</legend>
            {MODELS.map((option) => (
              <label key={option.id} className={`model-option${option.enabled ? '' : ' model-option--disabled'}`}>
                <input
                  type="radio"
                  name="model"
                  value={option.id}
                  checked={model === option.id}
                  disabled={!option.enabled}
                  onChange={() => setModel(option.id)}
                />
                <span className="model-option__label">
                  {option.label} <small>· {option.detail}</small>
                </span>
                <span className="model-option__tag">
                  {option.enabled ? 'disponible' : 'Próximamente'}
                </span>
              </label>
            ))}
          </fieldset>

          <label className="checkbox">
            <input
              type="checkbox"
              checked={confirmed}
              disabled={uploading}
              onChange={(event) => setConfirmed(event.target.checked)}
            />
            <span>
              Confirmo que este audio es sintético y no contiene datos reales ni identificables.
            </span>
          </label>

          {error && (
            <p className="form-error" role="alert">
              {errorMessage(error)}
            </p>
          )}

          {uploading && (
            <div className="progress" role="status">
              <span className="progress__spinner" aria-hidden="true" />
              <span>Analizando audio…</span>
              <button type="button" className="link-button" onClick={handleCancelUpload}>
                Cancelar análisis
              </button>
            </div>
          )}

          <div className="modal-card__actions">
            <button type="button" className="button button--ghost" onClick={onClose} disabled={uploading}>
              Cancelar
            </button>
            <button type="submit" className="button button--primary" disabled={!canSubmit}>
              {uploading ? 'Analizando…' : 'Analizar audio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

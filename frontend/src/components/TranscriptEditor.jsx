import { useState } from 'react'
import { formatTime } from '../utils/format'

function validate(segment, duration) {
  if (!segment.text.trim()) return 'El texto no puede estar vacío.'
  if (!Number.isFinite(segment.start_time) || !Number.isFinite(segment.end_time)) {
    return 'Las marcas deben ser números.'
  }
  if (segment.start_time < 0 || segment.end_time <= segment.start_time) {
    return 'El fin debe ser mayor que el inicio.'
  }
  if (duration > 0 && segment.end_time > duration) return 'El segmento termina después del audio.'
  return null
}

export default function TranscriptEditor({ segments, duration = 0, saving, error, onSave, onCancel }) {
  const [draft, setDraft] = useState(() => segments.map((segment) => ({ ...segment })))
  const [localError, setLocalError] = useState(null)

  function update(index, field, value) {
    setDraft((current) =>
      current.map((segment, position) =>
        position === index
          ? {
              ...segment,
              [field]:
                field === 'text' ? value : field === 'start_time' || field === 'end_time' ? Number(value) : value,
            }
          : segment,
      ),
    )
  }

  function handleSubmit(event) {
    event.preventDefault()

    for (let index = 0; index < draft.length; index += 1) {
      const problem = validate(draft[index], duration)
      if (problem) {
        setLocalError(`${formatTime(draft[index].start_time)}: ${problem}`)
        return
      }
      if (index > 0 && draft[index].start_time < draft[index - 1].end_time) {
        setLocalError(`${formatTime(draft[index].start_time)}: se solapa con el fragmento anterior.`)
        return
      }
    }

    setLocalError(null)
    onSave(draft.map(({ id, start_time, end_time, text }) => ({ id, start_time, end_time, text })))
  }

  return (
    <section className="transcript transcript--editing" aria-label="Edición de la transcripción">
      <header className="section-header">
        <div>
          <h2>EDITANDO TRANSCRIPCIÓN</h2>
          <p>{draft.length} segmentos · Texto completo · Español</p>
        </div>
      </header>

      <form onSubmit={handleSubmit} className="editor">
        <ol className="segment-list editor__flow">
          {draft.map((segment, index) => (
            <li key={segment.id} className="segment segment--editing editor-block" data-testid="editor-block">
              <div className="segment__meta">
                <span className="segment__time">{formatTime(segment.start_time)}</span>
              </div>
              <textarea
                className="editor__text"
                value={segment.text}
                rows={3}
                aria-label={`Texto del segmento ${index + 1}`}
                onChange={(event) => update(index, 'text', event.target.value)}
              />
              <div className="editor__times">
                <label>
                  Inicio (s)
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={segment.start_time}
                    aria-label={`Inicio del segmento ${index + 1}`}
                    onChange={(event) => update(index, 'start_time', event.target.value)}
                  />
                </label>
                <label>
                  Fin (s)
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={segment.end_time}
                    aria-label={`Fin del segmento ${index + 1}`}
                    onChange={(event) => update(index, 'end_time', event.target.value)}
                  />
                </label>
              </div>
            </li>
          ))}
        </ol>

        {(localError || error) && (
          <p className="form-error" role="alert">
            {localError || error}
          </p>
        )}

        <div className="editor__actions">
          <button type="button" className="button button--ghost" onClick={onCancel} disabled={saving}>
            Descartar
          </button>
          <button type="submit" className="button button--primary" disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </section>
  )
}

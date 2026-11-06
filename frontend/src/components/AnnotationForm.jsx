import { useState } from 'react'

export const MAX_LENGTH = 500

export default function AnnotationForm({ initialText = '', onSubmit, onCancel, saving = false }) {
  const [text, setText] = useState(initialText)
  const length = text.length
  const tooLong = length > MAX_LENGTH
  const empty = text.trim().length === 0
  const canSave = !tooLong && !empty && !saving

  function handleSubmit(event) {
    event.preventDefault()
    if (!canSave) return
    onSubmit(text.trim())
  }

  return (
    <form className="annotation-form" onSubmit={handleSubmit}>
      <textarea
        className="annotation-form__input"
        value={text}
        rows={3}
        autoFocus
        placeholder="Escribe una observación sobre este fragmento"
        aria-label="Texto de la observación"
        onChange={(event) => setText(event.target.value)}
      />

      <div className="annotation-form__meta">
        <span
          className={`annotation-form__counter${tooLong ? ' annotation-form__counter--error' : ''}`}
          aria-live="polite"
        >
          {length}/{MAX_LENGTH}
        </span>
        <div className="annotation-form__actions">
          <button type="button" className="button button--ghost" onClick={onCancel} disabled={saving}>
            Cancelar
          </button>
          <button type="submit" className="button button--primary" disabled={!canSave}>
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
      </div>

      {tooLong && (
        <p className="form-error" role="alert">
          La observación no puede superar los {MAX_LENGTH} caracteres.
        </p>
      )}
    </form>
  )
}

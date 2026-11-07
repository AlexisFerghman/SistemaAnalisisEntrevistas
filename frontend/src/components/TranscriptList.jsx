import { useState } from 'react'
import AnnotationForm from './AnnotationForm'
import AnnotationList from './AnnotationList'
import EmotionBadge from './EmotionBadge'
import { formatTime } from '../utils/format'

export default function TranscriptList({
  segments,
  currentTime = 0,
  annotations = [],
  saving = false,
  onSeek,
  onStartEdit,
  onCreate,
  onUpdate,
  onDelete,
}) {
  const [form, setForm] = useState(null)
  const activeIndex = segments.findIndex(
    (segment) => currentTime >= segment.start_time && currentTime < segment.end_time,
  )

  async function submit(text) {
    if (!form) return
    try {
      if (form.mode === 'create') {
        await onCreate?.(form.segment.id, text, form.segment.start_time, form.segment.end_time)
      } else {
        await onUpdate?.(
          form.annotation.id,
          text,
          form.annotation.segment_id,
          form.annotation.start_time,
          form.annotation.end_time,
        )
      }
      setForm(null)
    } catch {
      // El aviso de error lo muestra App; el formulario permanece abierto para reintentar.
    }
  }

  return (
    <section className="transcript" aria-label="Transcripción sincronizada">
      <header className="section-header">
        <div>
          <h2>TRANSCRIPCIÓN SINCRONIZADA</h2>
          <p>
            {segments.length} segmentos · {annotations.length} observaciones · Español
          </p>
        </div>
        <button type="button" className="button button--ghost" onClick={onStartEdit}>
          ✎ Editar texto
        </button>
      </header>

      <ol className="segment-list">
        {segments.map((segment, index) => {
          const segmentAnnotations = annotations.filter(
            (annotation) => annotation.segment_id === segment.id,
          )
          const editing = form && form.segment?.id === segment.id

          return (
            <li
              key={segment.id}
              className={`segment${index === activeIndex ? ' segment--active' : ''}`}
              data-testid="segment"
            >
              <div className="segment__meta">
                <button
                  type="button"
                  className={`segment__time${index === activeIndex ? ' segment__time--active' : ''}`}
                  onClick={() => onSeek?.(segment.start_time)}
                  aria-label={`Ir a ${formatTime(segment.start_time)}`}
                >
                  {formatTime(segment.start_time)}
                </button>
                <EmotionBadge />
              </div>

              <p className="segment__text">{segment.text}</p>
              <p className="segment__words">
                {segment.words_count ?? segment.words?.length ?? 0} palabras con marcas
              </p>

              <div className="segment__actions">
                <button type="button" className="chip-button" disabled title="Próximamente">
                  🔖 Etiqueta clínica
                </button>
                <button
                  type="button"
                  className="chip-button"
                  onClick={() => setForm({ mode: 'create', segment })}
                >
                  ✎ Observación
                </button>
              </div>

              <AnnotationList
                annotations={segmentAnnotations}
                onEdit={(annotation) => setForm({ mode: 'edit', segment, annotation })}
                onDelete={onDelete}
              />

              {editing && (
                <AnnotationForm
                  initialText={form.mode === 'edit' ? form.annotation.text : ''}
                  onSubmit={submit}
                  onCancel={() => setForm(null)}
                  saving={saving}
                />
              )}
            </li>
          )
        })}
      </ol>
    </section>
  )
}

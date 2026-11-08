import { useEffect, useRef, useState } from 'react'
import AnnotationForm from './AnnotationForm'
import AnnotationList from './AnnotationList'
import EmotionBadge from './EmotionBadge'
import { formatTime } from '../utils/format'

const FOLLOW_PAUSE_MS = 5000

function prefersReducedMotion() {
  return (
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

export default function TranscriptList({
  segments,
  currentTime = 0,
  annotations = [],
  saving = false,
  revealRequest = null,
  onSeek,
  onPlay,
  onStartEdit,
  onCreate,
  onUpdate,
  onDelete,
}) {
  const [form, setForm] = useState(null)
  const [followPaused, setFollowPaused] = useState(false)
  const listRef = useRef(null)
  const lastManualScrollRef = useRef(0)
  const autoScrollingRef = useRef(false)
  const autoScrollTimerRef = useRef(null)
  const resumeTimerRef = useRef(null)
  const lastRevealIdRef = useRef(null)
  const activeIndex = segments.findIndex(
    (segment) => currentTime >= segment.start_time && currentTime < segment.end_time,
  )

  function clearResumeTimer() {
    globalThis.clearTimeout(resumeTimerRef.current)
  }

  function pauseFollow() {
    lastManualScrollRef.current = Date.now()
    setFollowPaused(true)
    clearResumeTimer()
    resumeTimerRef.current = globalThis.setTimeout(() => {
      setFollowPaused(false)
    }, FOLLOW_PAUSE_MS)
  }

  function resumeFollow() {
    clearResumeTimer()
    lastManualScrollRef.current = 0
    setFollowPaused(false)
  }

  function scrollToIndex(index) {
    const list = listRef.current
    if (!list || index < 0) return
    const item = list.children[index]
    if (!item || typeof item.scrollIntoView !== 'function') return

    autoScrollingRef.current = true
    item.scrollIntoView({
      behavior: prefersReducedMotion() ? 'auto' : 'smooth',
      block: 'center',
    })
    globalThis.clearTimeout(autoScrollTimerRef.current)
    autoScrollTimerRef.current = globalThis.setTimeout(() => {
      autoScrollingRef.current = false
    }, 600)
  }

  useEffect(() => {
    if (followPaused) return
    scrollToIndex(activeIndex)
  }, [activeIndex, followPaused])

  useEffect(() => {
    if (!revealRequest || lastRevealIdRef.current === revealRequest.id) return
    lastRevealIdRef.current = revealRequest.id
    const index = segments.findIndex((segment) => segment.id === revealRequest.segmentId)
    if (index < 0) return

    pauseFollow()
    scrollToIndex(index)
  }, [revealRequest, segments])

  useEffect(
    () => () => {
      globalThis.clearTimeout(autoScrollTimerRef.current)
      clearResumeTimer()
    },
    [],
  )

  function handleScroll() {
    if (!autoScrollingRef.current) {
      pauseFollow()
    }
  }

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
        <div className="transcript__actions">
          {followPaused && (
            <button type="button" className="button button--ghost" onClick={resumeFollow}>
              Volver al audio
            </button>
          )}
          <button type="button" className="button button--ghost" onClick={onStartEdit}>
            ✎ Editar texto
          </button>
        </div>
      </header>

      <ol
        className="segment-list transcript-flow"
        ref={listRef}
        onScroll={handleScroll}
        onWheel={pauseFollow}
      >
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
                <button
                  type="button"
                  className="segment__play"
                  onClick={() => onPlay?.(segment.start_time)}
                  aria-label={`Reproducir desde ${formatTime(segment.start_time)}`}
                >
                  ▶
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

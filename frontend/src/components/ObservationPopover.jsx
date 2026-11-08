import { useEffect } from 'react'
import { formatTime } from '../utils/format'

export default function ObservationPopover({
  id,
  group,
  align = 'center',
  onClose,
  onReveal,
}) {
  const title =
    group.count === 1 ? '1 observación' : `${group.count} observaciones`

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose?.()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  return (
    <div
      id={id}
      className={`observation-popover observation-popover--${align}`}
      role="dialog"
      aria-modal="false"
      aria-label={title}
      onPointerDown={(event) => event.stopPropagation()}
      onClick={(event) => event.stopPropagation()}
    >
      <header className="observation-popover__header">
        <strong>{title}</strong>
        <button
          type="button"
          className="observation-popover__close"
          onClick={() => onClose?.()}
          aria-label="Cerrar observaciones"
        >
          ✕
        </button>
      </header>

      <ul className="observation-popover__list">
        {group.observations.map((observation) => {
          const time = observation.start_time ?? observation.time ?? group.anchor_time
          const segmentId = observation.segmentId ?? observation.segment_id

          return (
            <li key={observation.id} className="observation-popover__item">
              <div className="observation-popover__content">
                <time className="observation-popover__time" dateTime={`PT${time}S`}>
                  {formatTime(time)}
                </time>
                <p className="observation-popover__text">{observation.text}</p>
              </div>
              {segmentId && (
                <button
                  type="button"
                  className="chip-button observation-popover__reveal"
                  onClick={() => {
                    onReveal?.(segmentId)
                    onClose?.()
                  }}
                >
                  Ver fragmento
                </button>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

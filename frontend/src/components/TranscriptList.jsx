import { formatTime } from '../utils/format'

export default function TranscriptList({ segments, currentTime = 0, onSeek, onStartEdit }) {
  const activeIndex = segments.findIndex(
    (segment) => currentTime >= segment.start_time && currentTime < segment.end_time,
  )

  return (
    <section className="transcript" aria-label="Transcripción sincronizada">
      <header className="section-header">
        <div>
          <h2>TRANSCRIPCIÓN SINCRONIZADA</h2>
          <p>{segments.length} segmentos · Español</p>
        </div>
        <button type="button" className="button button--ghost" onClick={onStartEdit}>
          ✎ Editar texto
        </button>
      </header>

      <ol className="segment-list">
        {segments.map((segment, index) => (
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
            </div>
            <p className="segment__text">{segment.text}</p>
            <p className="segment__words">{segment.words?.length ?? 0} palabras con marcas</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

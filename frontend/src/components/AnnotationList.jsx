import { formatTime } from '../utils/format'

export default function AnnotationList({ annotations, onEdit, onDelete }) {
  if (!annotations || annotations.length === 0) return null

  return (
    <ul className="annotation-list">
      {annotations.map((annotation) => (
        <li key={annotation.id} className="annotation-chip">
          <span className="annotation-chip__time">{formatTime(annotation.start_time)}</span>
          <span className="annotation-chip__text">{annotation.text}</span>
          <button
            type="button"
            className="annotation-chip__action"
            onClick={() => onEdit?.(annotation)}
            aria-label={`Editar anotación de ${formatTime(annotation.start_time)}`}
          >
            ✎
          </button>
          <button
            type="button"
            className="annotation-chip__action"
            onClick={() => onDelete?.(annotation)}
            aria-label={`Eliminar anotación de ${formatTime(annotation.start_time)}`}
          >
            🗑
          </button>
        </li>
      ))}
    </ul>
  )
}

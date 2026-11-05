import { formatTime, statusLabel } from '../utils/format'

const STATUS_CLASS = {
  empty: 'badge',
  validating: 'badge badge--progress',
  processing: 'badge badge--progress',
  ready: 'badge badge--ok',
  reviewed: 'badge badge--ok',
  error: 'badge badge--error',
}

export default function WorkspaceHeader({ session, onNewInterview, onExport }) {
  const status = session?.status ?? 'empty'
  const audio = session?.audio
  const subtitle = audio
    ? `${audio.filename} · ${formatTime(audio.duration_seconds)}`
    : 'Sin audio cargado'
  const canExport = status === 'ready' || status === 'reviewed'

  return (
    <header className="workspace-header">
      <div className="workspace-header__brand">
        <button type="button" className="icon-button" aria-label="Volver" disabled>
          <span aria-hidden="true">‹</span>
        </button>
        <span className="logo" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 12h2l2-6 3 12 3-9 2 5h4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        <div className="workspace-header__titles">
          <div className="workspace-header__title-row">
            <h1>Sesión actual</h1>
            <span className={STATUS_CLASS[status] ?? 'badge'}>{statusLabel(status)}</span>
          </div>
          <p className="workspace-header__subtitle">{subtitle}</p>
        </div>
      </div>

      <div className="workspace-header__actions">
        <button type="button" className="button button--ghost" onClick={onNewInterview}>
          <span aria-hidden="true">+</span> Nueva entrevista
        </button>
        <button
          type="button"
          className="button button--dark"
          onClick={onExport}
          disabled={!canExport}
          title={canExport ? 'Exportar la sesión' : 'Disponible al completar el análisis'}
        >
          <span aria-hidden="true">↓</span> Exportar datos
        </button>

        <div className="profile">
          <span className="profile__avatar" aria-hidden="true">PS</span>
          <span className="profile__text">
            <strong>Profesional de salud</strong>
            <small>Sesión local</small>
          </span>
        </div>
        <button type="button" className="link-button" disabled>
          Salir
        </button>
      </div>
    </header>
  )
}

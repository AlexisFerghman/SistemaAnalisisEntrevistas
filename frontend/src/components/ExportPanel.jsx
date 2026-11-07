export default function ExportPanel({ onExport, disabled = false, exporting = false }) {
  return (
    <button
      type="button"
      className="button button--dark export-panel__button"
      onClick={onExport}
      disabled={disabled || exporting}
      title={disabled ? 'Disponible al completar el análisis' : 'Exportar la sesión como JSON'}
    >
      <span aria-hidden="true">↓</span> {exporting ? 'Exportando…' : 'Exportar datos'}
    </button>
  )
}

export default function AnnotationPanel({ annotations = [] }) {
  const observations = annotations.length

  return (
    <aside className="annotation-panel" aria-label="Anotaciones">
      <header className="annotation-panel__header">
        <h2>Anotaciones</h2>
        <button
          type="button"
          className="annotation-panel__add"
          disabled
          title="Disponible en una próxima iteración"
          aria-label="Añadir etiqueta clínica"
        >
          +
        </button>
      </header>

      <div className="annotation-panel__counters">
        <div className="counter-card">
          <strong>0</strong>
          <span>Etiquetas</span>
        </div>
        <div className="counter-card">
          <strong>{observations}</strong>
          <span>Observaciones</span>
        </div>
      </div>

      <section className="annotation-panel__section">
        <h3>Etiquetas clínicas</h3>
        <p className="annotation-panel__empty">Próximamente</p>
      </section>

      <section className="annotation-panel__section">
        <h3>Observaciones</h3>
        <p className="annotation-panel__empty">
          {observations > 0
            ? 'Las observaciones se gestionan desde cada fragmento.'
            : 'Todavía no hay observaciones en esta sesión.'}
        </p>
      </section>

      <button type="button" className="button button--dark annotation-panel__export" disabled>
        Exportar JSON / CSV
      </button>
    </aside>
  )
}

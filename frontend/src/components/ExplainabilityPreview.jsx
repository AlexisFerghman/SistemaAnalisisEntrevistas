const CONFIDENCE_BARS = [
  { label: 'Ansiedad', value: 0.72 },
  { label: 'Estado de ánimo', value: 0.46 },
  { label: 'Sueño', value: 0.31 },
]

export default function ExplainabilityPreview() {
  return (
    <section className="xai-preview" aria-label="Explicabilidad local (vista previa)">
      <header className="xai-preview__header">
        <h2 className="grid-title">EXPLICABILIDAD LOCAL</h2>
        <span className="preview-badge">Vista previa · no disponible en este MVP</span>
      </header>

      <p className="xai-preview__intro">
        Ejemplo estático de cómo se explicaría el resultado del modelo. No consume datos de la
        entrevista.
      </p>

      <ul className="xai-preview__sentences">
        <li>
          «<mark>Me despierto varias veces durante la noche</mark> y llego agotado a la mañana».
        </li>
        <li>
          «Últimamente <mark>evito quedar con amigos</mark> y me cuesta empezar tareas».
        </li>
      </ul>

      <div className="xai-preview__bars" aria-hidden="true">
        {CONFIDENCE_BARS.map((item) => (
          <div className="confidence-bar" key={item.label}>
            <span>{item.label}</span>
            <span className="confidence-bar__track">
              <span
                className="confidence-bar__fill"
                style={{ width: `${Math.round(item.value * 100)}%` }}
              />
            </span>
            <strong>{Math.round(item.value * 100)}%</strong>
          </div>
        ))}
      </div>

      <p className="xai-preview__result">
        <strong>Resultado del modelo:</strong> ejemplo ilustrativo, no calculado.
      </p>
    </section>
  )
}

export default function SyntheticBanner() {
  return (
    <div className="synthetic-banner" role="note">
      <span className="synthetic-banner__icon" aria-hidden="true">!</span>
      <p>
        <strong>Prototipo experimental.</strong> Solo admite audios ficticios o sintéticos. No cargues
        entrevistas reales, nombres ni datos identificables.
      </p>
    </div>
  )
}

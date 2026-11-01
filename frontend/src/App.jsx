import { useEffect, useState } from 'react'

const apiUrl = import.meta.env.VITE_API_URL || ''

function App() {
  const [apiStatus, setApiStatus] = useState('comprobando')

  useEffect(() => {
    fetch(`${apiUrl}/health`)
      .then((response) => {
        if (!response.ok) throw new Error('API no disponible')
        return response.json()
      })
      .then(() => setApiStatus('conectada'))
      .catch(() => setApiStatus('sin conexión'))
  }, [])

  return (
    <main className="shell">
      <section className="intro">
        <p className="eyebrow">Prototipo experimental</p>
        <h1>Analisis de entrevistas</h1>
        <p className="lede">
          Espacio de trabajo para transcribir, revisar y anotar una sesión sintética.
        </p>
      </section>
      <section className="status-panel" aria-live="polite">
        <span className={`status-dot ${apiStatus === 'conectada' ? 'online' : ''}`} />
        <span>API {apiStatus}</span>
      </section>
    </main>
  )
}

export default App

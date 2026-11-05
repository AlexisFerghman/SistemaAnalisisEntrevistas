import { useRef, useState } from 'react'
import { formatBytes } from '../utils/format'

const MAX_BYTES = 125829120
const ALLOWED = ['.mp3', '.wav']

function validate(file) {
  if (!file) return { code: 'missing_file' }
  const name = file.name.toLowerCase()
  if (!ALLOWED.some((extension) => name.endsWith(extension))) {
    return { code: 'unsupported_format' }
  }
  if (file.size > MAX_BYTES) return { code: 'payload_too_large' }
  if (file.size === 0) return { code: 'invalid_audio' }
  return null
}

export default function UploadPanel({ file, onSelect, disabled }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  function handleFiles(files) {
    const selected = files?.[0]
    if (!selected) return
    onSelect(selected, validate(selected))
  }

  return (
    <div className="upload-panel">
      <div
        className={`dropzone${dragging ? ' dropzone--active' : ''}${disabled ? ' dropzone--disabled' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          if (!disabled) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          if (!disabled) handleFiles(event.dataTransfer.files)
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(event) => {
          if (disabled) return
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-label="Seleccionar archivo de audio"
      >
        <span className="dropzone__icon" aria-hidden="true">↑</span>
        <p className="dropzone__title">Arrastra tu archivo aquí o haz clic para seleccionarlo</p>
        <p className="dropzone__hint">.mp3 o .wav · máximo 120 MB</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".mp3,.wav,audio/mpeg,audio/wav"
        hidden
        disabled={disabled}
        onChange={(event) => handleFiles(event.target.files)}
      />

      {file && (
        <p className="upload-panel__file">
          <strong>{file.name}</strong> · {formatBytes(file.size)}
        </p>
      )}
    </div>
  )
}

import { formatTime } from '../utils/format'

const TICKS = [0, 0.25, 0.5, 0.75, 1]

export default function AudioWaveform({ peaks, duration, currentTime = 0, markers = [], onSeek }) {
  const progress = duration > 0 ? Math.min(Math.max(currentTime / duration, 0), 1) : 0

  function seekFromEvent(event) {
    const rect = event.currentTarget.getBoundingClientRect()
    if (rect.width === 0) return
    const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1)
    onSeek?.(ratio * duration)
  }

  function handleKeyDown(event) {
    const step = event.shiftKey ? 15 : 5
    if (event.key === 'ArrowRight') {
      event.preventDefault()
      onSeek?.(Math.min(currentTime + step, duration))
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault()
      onSeek?.(Math.max(currentTime - step, 0))
    } else if (event.key === 'Home') {
      event.preventDefault()
      onSeek?.(0)
    } else if (event.key === 'End') {
      event.preventDefault()
      onSeek?.(duration)
    }
  }

  return (
    <div className="waveform-wrap">
      <div
        className="waveform"
        role="slider"
        tabIndex={0}
        aria-label="Posición del audio"
        aria-valuemin={0}
        aria-valuemax={Math.round(duration)}
        aria-valuenow={Math.round(currentTime)}
        aria-valuetext={formatTime(currentTime)}
        onClick={seekFromEvent}
        onKeyDown={handleKeyDown}
      >
        <div className="waveform__bars" aria-hidden="true">
          {(peaks ?? Array.from({ length: 120 }, (_, index) => 0.25 + 0.6 * Math.abs(Math.sin(index / 3))))
            .map((peak, index) => {
              const height = Math.max(6, Math.round(peak * 100))
              const played = index / (peaks?.length ?? 120) <= progress
              return (
                <span
                  key={index}
                  className={`waveform__bar${played ? ' waveform__bar--played' : ''}`}
                  style={{ height: `${height}%` }}
                />
              )
            })}
        </div>

        <div className="waveform__playhead" style={{ left: `${progress * 100}%` }} aria-hidden="true" />

        {markers.map((marker) => {
          const ratio = duration > 0 ? Math.min(Math.max(marker.time / duration, 0), 1) : 0
          return (
            <button
              key={marker.id}
              type="button"
              className={`waveform__marker waveform__marker--${marker.type ?? 'observacion'}`}
              style={{ left: `${ratio * 100}%` }}
              title={`${formatTime(marker.time)} · ${marker.text}`}
              aria-label={`${marker.type ?? 'observación'} en ${formatTime(marker.time)}: ${marker.text}`}
              onClick={(event) => {
                event.stopPropagation()
                onSeek?.(marker.time)
              }}
            />
          )
        })}
      </div>

      <div className="waveform__ticks" aria-hidden="true">
        {TICKS.map((tick) => (
          <span key={tick} style={{ left: `${tick * 100}%` }}>
            {formatTime(duration * tick)}
          </span>
        ))}
      </div>
    </div>
  )
}

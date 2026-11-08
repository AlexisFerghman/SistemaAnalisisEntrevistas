import { useEffect, useRef, useState } from 'react'
import AudioWaveform from './AudioWaveform'
import { formatTime } from '../utils/format'

const SPEEDS = [1, 1.25, 1.5]
const BAR_COUNT = 220

function usePeaks(src, cacheKey) {
  const [peaks, setPeaks] = useState(null)

  useEffect(() => {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!src || !AudioCtx || typeof fetch !== 'function') return undefined

    let cancelled = false
    let context
    const load = async () => {
      try {
        const separator = src.includes('?') ? '&' : '?'
        const response = await fetch(
          `${src}${separator}v=${encodeURIComponent(cacheKey ?? '')}`,
        )
        const buffer = await response.arrayBuffer()
        context = new AudioCtx()
        const decoded = await context.decodeAudioData(buffer)
        const channel = decoded.getChannelData(0)
        const block = Math.max(1, Math.floor(channel.length / BAR_COUNT))
        const values = []
        for (let index = 0; index < BAR_COUNT; index += 1) {
          let sum = 0
          for (let offset = 0; offset < block; offset += 1) {
            sum += Math.abs(channel[index * block + offset] ?? 0)
          }
          values.push(sum / block)
        }
        const max = Math.max(...values, 0.0001)
        if (!cancelled) setPeaks(values.map((value) => value / max))
      } catch {
        if (!cancelled) setPeaks(null)
      } finally {
        context?.close?.()
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [src, cacheKey])

  return peaks
}

export default function AudioPlayer({
  src,
  duration = 0,
  currentTime = 0,
  segments = [],
  annotations = [],
  seekRequest = null,
  playRequest = null,
  onTimeUpdate,
  onRevealSegment,
  visualSeed = '',
}) {
  const audioRef = useRef(null)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const peaks = usePeaks(src, visualSeed)

  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = speed
  }, [speed])

  useEffect(() => {
    if (!seekRequest || !audioRef.current) return
    audioRef.current.currentTime = seekRequest.time
    onTimeUpdate?.(seekRequest.time)
  }, [seekRequest, onTimeUpdate])

  useEffect(() => {
    if (!playRequest || !audioRef.current) return
    const target = Math.min(Math.max(playRequest.time, 0), duration || 0)
    audioRef.current.currentTime = target
    onTimeUpdate?.(target)
    audioRef.current.play?.().catch(() => setPlaying(false))
  }, [playRequest, duration, onTimeUpdate])

  const markers = annotations.map((annotation) => ({
    id: annotation.id,
    time: annotation.start_time ?? 0,
    text: annotation.text,
    segmentId: annotation.segment_id,
    type: 'observacion',
  }))

  function seek(time) {
    const target = Math.min(Math.max(time, 0), duration || 0)
    if (audioRef.current) audioRef.current.currentTime = target
    onTimeUpdate?.(target)
  }

  function togglePlay() {
    const audio = audioRef.current
    if (!audio) return
    if (audio.paused) {
      audio.play?.().catch(() => setPlaying(false))
    } else {
      audio.pause?.()
    }
  }

  function skip(delta) {
    const audio = audioRef.current
    const base = audio ? audio.currentTime : currentTime
    seek(base + delta)
  }

  const activeSegment = segments.find(
    (segment) => currentTime >= segment.start_time && currentTime < segment.end_time,
  )

  return (
    <section className="audio-module" aria-label="Audio de la entrevista">
      <header className="audio-module__header">
        <div>
          <h2>Audio de la entrevista</h2>
          <p>{formatTime(duration)} · {segments.length} segmentos</p>
        </div>
        <ul className="legend">
          <li><span className="legend__dot legend__dot--tag" aria-hidden="true" />Etiqueta clínica</li>
          <li><span className="legend__dot legend__dot--note" aria-hidden="true" />Observación</li>
        </ul>
      </header>

      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onTimeUpdate={(event) => onTimeUpdate?.(event.currentTarget.currentTime)}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
      />

      <AudioWaveform
        peaks={peaks}
        duration={duration}
        currentTime={currentTime}
        markers={markers}
        onSeek={seek}
        onRevealSegment={onRevealSegment}
        visualSeed={visualSeed}
      />

      <div className="player-controls">
        <button type="button" className="player-controls__skip" onClick={() => skip(-10)} aria-label="Retroceder 10 segundos">
          ⟲ 10
        </button>
        <button
          type="button"
          className="player-controls__play"
          onClick={togglePlay}
          aria-label={playing ? 'Pausar' : 'Reproducir'}
        >
          {playing ? '❚❚' : '▶'}
        </button>
        <button type="button" className="player-controls__skip" onClick={() => skip(10)} aria-label="Adelantar 10 segundos">
          10 ⟳
        </button>

        <span className="player-controls__time">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        <div className="speed-chips" role="group" aria-label="Velocidad de reproducción">
          {SPEEDS.map((value) => (
            <button
              key={value}
              type="button"
              className={`speed-chips__chip${speed === value ? ' speed-chips__chip--active' : ''}`}
              aria-pressed={speed === value}
              onClick={() => setSpeed(value)}
            >
              {value}x
            </button>
          ))}
        </div>
      </div>

      <p className="audio-module__hint">
        {activeSegment ? `Escuchando: ${formatTime(activeSegment.start_time)}` : 'Pulsa un fragmento para saltar a su inicio.'}
      </p>
    </section>
  )
}

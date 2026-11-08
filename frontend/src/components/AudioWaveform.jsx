import { useEffect, useMemo, useRef, useState } from 'react'
import ObservationPopover from './ObservationPopover'
import { formatTime } from '../utils/format'
import { groupObservations } from '../utils/observations'
import {
  applyDeterministicVariation,
  buildFallbackPeaks,
} from '../utils/waveform'

const TICKS = [0, 0.25, 0.5, 0.75, 1]
const CLOSE_GRACE_MS = 150

export default function AudioWaveform({
  peaks,
  duration,
  currentTime = 0,
  markers = [],
  onSeek,
  onRevealSegment,
  visualSeed = '',
}) {
  const progress = duration > 0 ? Math.min(Math.max(currentTime / duration, 0), 1) : 0
  const draggingRef = useRef(false)
  const suppressClickRef = useRef(false)
  const waveformRef = useRef(null)
  const markerRefs = useRef({})
  const closeTimerRef = useRef(null)
  const [width, setWidth] = useState(0)
  const [openGroupId, setOpenGroupId] = useState(null)

  const sourcePeaks = useMemo(
    () => peaks ?? buildFallbackPeaks(120, visualSeed),
    [peaks, visualSeed],
  )
  const displayPeaks = useMemo(
    () => applyDeterministicVariation(sourcePeaks, visualSeed),
    [sourcePeaks, visualSeed],
  )

  const groups = useMemo(
    () => groupObservations(markers, width, duration),
    [markers, width, duration],
  )

  useEffect(() => {
    const element = waveformRef.current
    if (!element) return undefined

    const updateWidth = () => setWidth(element.getBoundingClientRect().width)
    updateWidth()

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(updateWidth)
      observer.observe(element)
      return () => observer.disconnect()
    }

    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [])

  useEffect(() => {
    if (!openGroupId) return undefined

    function closeOnOutsidePointer(event) {
      const target = event.target
      if (target?.closest?.('.waveform__marker-wrap')) return
      setOpenGroupId(null)
    }

    document.addEventListener('pointerdown', closeOnOutsidePointer)
    return () => document.removeEventListener('pointerdown', closeOnOutsidePointer)
  }, [openGroupId])

  useEffect(
    () => () => {
      globalThis.clearTimeout(closeTimerRef.current)
    },
    [],
  )

  function seekFromEvent(event) {
    const rect = event.currentTarget.getBoundingClientRect()
    if (rect.width === 0) return
    const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1)
    onSeek?.(ratio * duration)
  }

  function handlePointerDown(event) {
    if (event.button !== undefined && event.button !== 0) return
    draggingRef.current = true
    suppressClickRef.current = true
    event.currentTarget.setPointerCapture?.(event.pointerId)
    seekFromEvent(event)
  }

  function handlePointerMove(event) {
    if (!draggingRef.current) return
    seekFromEvent(event)
  }

  function handlePointerUp(event) {
    if (!draggingRef.current) return
    draggingRef.current = false
    seekFromEvent(event)
    event.currentTarget.releasePointerCapture?.(event.pointerId)
  }

  function handlePointerCancel() {
    draggingRef.current = false
  }

  function handleClick(event) {
    if (suppressClickRef.current) {
      suppressClickRef.current = false
      return
    }
    seekFromEvent(event)
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

  function clearCloseTimer() {
    globalThis.clearTimeout(closeTimerRef.current)
    closeTimerRef.current = null
  }

  function openGroup(groupId) {
    clearCloseTimer()
    setOpenGroupId(groupId)
  }

  function scheduleClose() {
    clearCloseTimer()
    closeTimerRef.current = globalThis.setTimeout(() => {
      setOpenGroupId(null)
      closeTimerRef.current = null
    }, CLOSE_GRACE_MS)
  }

  function closeGroup(restoreFocus = true) {
    clearCloseTimer()
    if (restoreFocus && openGroupId) {
      markerRefs.current[openGroupId]?.focus?.()
    }
    setOpenGroupId(null)
  }

  return (
    <div className="waveform-wrap">
      <div
        ref={waveformRef}
        className="waveform"
        role="slider"
        tabIndex={0}
        aria-label="Posición del audio"
        aria-valuemin={0}
        aria-valuemax={Math.round(duration)}
        aria-valuenow={Math.round(currentTime)}
        aria-valuetext={formatTime(currentTime)}
        onClick={handleClick}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerCancel}
        onKeyDown={handleKeyDown}
      >
        <div className="waveform__bars" aria-hidden="true">
          {displayPeaks.map((peak, index) => {
            const height = Math.max(6, Math.round(peak * 100))
            const played = index / (displayPeaks.length || 1) <= progress
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

        {groups.map((group) => {
          const ratio = group.position_ratio
          const align = ratio < 0.15 ? 'left' : ratio > 0.85 ? 'right' : 'center'
          const isOpen = openGroupId === group.id
          const label = `${group.count} ${
            group.count === 1 ? 'observación' : 'observaciones'
          } en ${formatTime(group.anchor_time)}`

          return (
            <div
              key={group.id}
              className="waveform__marker-wrap"
              style={{ left: `${ratio * 100}%` }}
              onMouseEnter={() => openGroup(group.id)}
              onMouseLeave={scheduleClose}
              onFocus={() => openGroup(group.id)}
              onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget)) scheduleClose()
              }}
            >
              <button
                ref={(node) => {
                  if (node) markerRefs.current[group.id] = node
                  else delete markerRefs.current[group.id]
                }}
                type="button"
                className="waveform__marker waveform__marker--observacion"
                title={label}
                aria-label={label}
                aria-expanded={isOpen}
                aria-controls={isOpen ? `observations-${group.id}` : undefined}
                onPointerDown={(event) => event.stopPropagation()}
                onClick={(event) => {
                  event.stopPropagation()
                  if (isOpen) closeGroup(false)
                  else openGroup(group.id)
                }}
              >
                {group.count > 1 && (
                  <span className="waveform__marker-count" aria-hidden="true">
                    {group.count}
                  </span>
                )}
              </button>

              {isOpen && (
                <ObservationPopover
                  id={`observations-${group.id}`}
                  group={group}
                  align={align}
                  onClose={() => closeGroup(true)}
                  onReveal={onRevealSegment}
                />
              )}
            </div>
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

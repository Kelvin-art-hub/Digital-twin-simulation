/**
 * Hook for WebSocket connection to a simulation job.
 */
import { useEffect, useRef, useCallback } from 'react'
import { createSimulationWebSocket } from '../api/client'
import { useSimulationStore } from '../store/simulationStore'

export function useSimulationWebSocket(jobId) {
  const wsRef = useRef(null)
  const { updateJobStatus, addLiveEvent, updateLiveMetrics, setResults } = useSimulationStore()

  const connect = useCallback(() => {
    if (!jobId) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = createSimulationWebSocket(jobId)
    wsRef.current = ws

    ws.onopen = () => {
      addLiveEvent({ type: 'connected', message: 'Connected to simulation stream', time: Date.now() })
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'status':
            updateJobStatus(data.status, data.progress ?? 0)
            break

          case 'progress':
            updateJobStatus('running', data.progress)
            addLiveEvent({
              type: 'progress',
              message: `Progress: ${data.progress}%`,
              time: Date.now(),
            })
            break

          case 'sim_event':
            addLiveEvent({
              type: data.event,
              station: data.station,
              message: formatEvent(data),
              time: Date.now(),
            })
            if (data.event === 'buffer_update') {
              updateLiveMetrics({
                buffer_levels: { [data.station]: data.occupancy },
              })
            }
            break

          case 'complete':
            updateJobStatus('complete', 100)
            if (data.metrics) setResults({ scenarios: [data.metrics] })
            addLiveEvent({ type: 'complete', message: 'Simulation complete!', time: Date.now() })
            break

          case 'error':
            updateJobStatus('failed', 0)
            addLiveEvent({ type: 'error', message: `Error: ${data.message}`, time: Date.now() })
            break

          default:
            break
        }
      } catch (e) {
        console.warn('Failed to parse WebSocket message', e)
      }
    }

    ws.onerror = () => {
      addLiveEvent({ type: 'error', message: 'WebSocket connection error', time: Date.now() })
    }

    ws.onclose = () => {
      addLiveEvent({ type: 'disconnected', message: 'Disconnected from simulation stream', time: Date.now() })
    }
  }, [jobId, updateJobStatus, addLiveEvent, updateLiveMetrics, setResults])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  return { ws: wsRef.current }
}

function formatEvent(data) {
  const t = data.time ? `[${data.time.toFixed(1)}s]` : ''
  switch (data.event) {
    case 'breakdown':
      return `${t} ${data.station}: BREAKDOWN — repair ${data.repair_time?.toFixed(1)}s`
    case 'repair_complete':
      return `${t} ${data.station}: Repair complete`
    case 'processing_start':
      return `${t} ${data.station}: Part #${data.part_id} processing started`
    case 'processing_complete':
      return `${t} ${data.station}: Part #${data.part_id} done (${data.duration?.toFixed(1)}s)`
    case 'part_complete':
      return `${t} Part #${data.part_id} completed — lead time ${(data.lead_time / 60)?.toFixed(2)}min`
    case 'buffer_update':
      return `${t} ${data.station}: Buffer ${data.occupancy}/${data.capacity}`
    default:
      return `${t} ${data.station ?? ''}: ${data.event}`
  }
}

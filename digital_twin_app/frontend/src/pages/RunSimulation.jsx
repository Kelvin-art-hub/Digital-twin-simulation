/**
 * Run Simulation page — live visualizer, progress, event log.
 */
import { useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import LineVisualizer from '../components/LineVisualizer'
import { useSimulationWebSocket } from '../hooks/useWebSocket'
import { useSimulationStore } from '../store/simulationStore'
import { useSimulationStatus } from '../hooks/useSimulation'

const EVENT_COLORS = {
  breakdown: 'text-red-600',
  repair_complete: 'text-green-600',
  part_complete: 'text-blue-600',
  error: 'text-red-700 font-semibold',
  complete: 'text-green-700 font-semibold',
  connected: 'text-gray-400',
  disconnected: 'text-gray-400',
  progress: 'text-gray-500',
}

export default function RunSimulation() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const { jobStatus, jobProgress, liveEvents, liveBufferLevels } = useSimulationStore()

  // Connect WebSocket
  useSimulationWebSocket(jobId)

  // Also poll status as fallback
  const { data: statusData } = useSimulationStatus(jobId, jobStatus !== 'complete' && jobStatus !== 'failed')

  const isComplete = jobStatus === 'complete' || statusData?.status === 'complete'
  const isFailed = jobStatus === 'failed' || statusData?.status === 'failed'
  const progress = jobProgress || statusData?.progress || 0

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Simulation Running</h1>
          <p className="text-gray-500 text-sm mt-1">Job ID: {jobId}</p>
        </div>
        <Link to="/" className="text-gray-500 hover:text-gray-700 text-sm">← Dashboard</Link>
      </div>

      {/* Progress bar */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            {isComplete ? '✅ Complete' : isFailed ? '❌ Failed' : '⚙️ Running...'}
          </span>
          <span className="text-sm font-bold text-gray-800">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${
              isComplete ? 'bg-green-500' : isFailed ? 'bg-red-500' : 'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Assembly line visualizer */}
      <div className="mb-6">
        <LineVisualizer
          utilizations={liveBufferLevels}
          bufferLevels={liveBufferLevels}
          isRunning={!isComplete && !isFailed}
        />
      </div>

      {/* Event log */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-800">Live Event Log</h3>
          <span className="text-xs text-gray-400">{liveEvents.length} events</span>
        </div>
        <div className="h-64 overflow-y-auto p-4 font-mono text-xs space-y-1">
          {liveEvents.length === 0 && (
            <p className="text-gray-400 text-center py-8">Waiting for events...</p>
          )}
          {[...liveEvents].reverse().map((event, i) => (
            <div key={i} className={`${EVENT_COLORS[event.type] || 'text-gray-600'}`}>
              {event.message}
            </div>
          ))}
        </div>
      </div>

      {/* Complete CTA */}
      {isComplete && (
        <div className="mt-6 bg-green-50 border border-green-200 rounded-xl p-6 text-center">
          <p className="text-green-700 font-semibold text-lg mb-3">Simulation Complete!</p>
          <button
            onClick={() => navigate(`/reports/${jobId}`)}
            className="bg-green-600 text-white px-6 py-2.5 rounded-lg font-semibold hover:bg-green-700 transition-colors"
          >
            View Full Report →
          </button>
        </div>
      )}

      {isFailed && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700 font-semibold">Simulation failed. Check the event log for details.</p>
          <Link to="/configure" className="mt-3 inline-block text-red-600 hover:underline">
            ← Back to Configure
          </Link>
        </div>
      )}
    </div>
  )
}

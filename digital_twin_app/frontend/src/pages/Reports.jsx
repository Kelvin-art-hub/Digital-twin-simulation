/**
 * Reports page — full results with charts and export.
 */
import { useParams, Link } from 'react-router-dom'
import { useSimulationResults } from '../hooks/useSimulation'
import ScenarioComparison from '../components/ScenarioComparison'
import ExportPanel from '../components/ExportPanel'

export default function Reports() {
  const { jobId } = useParams()
  const { data, isLoading, error } = useSimulationResults(jobId, !!jobId)

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center">
        <div className="animate-spin text-4xl mb-4">⚙️</div>
        <p className="text-gray-500">Loading results...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center">
        <p className="text-red-500 text-lg mb-4">{error.message}</p>
        <Link to="/" className="text-blue-600 hover:underline">← Back to Dashboard</Link>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{data.name}</h1>
          <p className="text-gray-500 mt-1">
            Completed {data.completed_at ? new Date(data.completed_at).toLocaleString() : ''}
            {' · '}{data.scenarios?.length ?? 0} scenario(s)
          </p>
        </div>
        <Link to="/" className="text-gray-500 hover:text-gray-700 text-sm">← Dashboard</Link>
      </div>

      {/* Export panel */}
      <div className="mb-8">
        <ExportPanel jobId={jobId} />
      </div>

      {/* Scenario comparison */}
      {data.scenarios?.length > 0 ? (
        <ScenarioComparison scenarios={data.scenarios} />
      ) : (
        <div className="text-center py-12 text-gray-400">No scenario results available.</div>
      )}
    </div>
  )
}

/**
 * Dashboard page — summary stats and recent simulation history.
 */
import { Link } from 'react-router-dom'
import { useSimulationHistory } from '../hooks/useSimulation'

const STATUS_COLORS = {
  complete: 'bg-green-100 text-green-700',
  running: 'bg-blue-100 text-blue-700',
  queued: 'bg-gray-100 text-gray-600',
  failed: 'bg-red-100 text-red-700',
}

export default function Dashboard() {
  const { data: history = [], isLoading, error } = useSimulationHistory()

  const completed = history.filter((r) => r.status === 'complete')
  const running = history.filter((r) => r.status === 'running' || r.status === 'queued')

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Digital Twin Dashboard</h1>
          <p className="text-gray-500 mt-1">Assembly line discrete-event simulation</p>
        </div>
        <Link
          to="/configure"
          className="bg-brand-900 text-white px-5 py-2.5 rounded-lg font-semibold hover:bg-brand-700 transition-colors"
        >
          + New Simulation
        </Link>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
        <StatCard
          label="Total Runs"
          value={history.length}
          icon="🔬"
          color="bg-blue-50 border-blue-200"
        />
        <StatCard
          label="Completed"
          value={completed.length}
          icon="✅"
          color="bg-green-50 border-green-200"
        />
        <StatCard
          label="Active"
          value={running.length}
          icon="⚡"
          color="bg-amber-50 border-amber-200"
        />
      </div>

      {/* Recent runs table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Recent Simulation Runs</h2>
        </div>

        {isLoading && (
          <div className="p-8 text-center text-gray-400">
            <div className="animate-spin text-3xl mb-2">⚙️</div>
            Loading history...
          </div>
        )}

        {error && (
          <div className="p-6 text-center text-red-500">
            Failed to load history: {error.message}
          </div>
        )}

        {!isLoading && !error && history.length === 0 && (
          <div className="p-12 text-center">
            <p className="text-gray-400 text-lg mb-4">No simulations yet</p>
            <Link
              to="/configure"
              className="text-blue-600 hover:underline font-medium"
            >
              Run your first simulation →
            </Link>
          </div>
        )}

        {!isLoading && history.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                  <th className="text-left px-6 py-3">Name</th>
                  <th className="text-left px-6 py-3">Status</th>
                  <th className="text-left px-6 py-3">Progress</th>
                  <th className="text-left px-6 py-3">Created</th>
                  <th className="text-left px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((run) => (
                  <tr key={run.id} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="px-6 py-3 font-medium text-gray-800">{run.name}</td>
                    <td className="px-6 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${STATUS_COLORS[run.status] || 'bg-gray-100 text-gray-600'}`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${run.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{run.progress}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-3 text-gray-500">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3">
                      {run.status === 'complete' && (
                        <Link
                          to={`/reports/${run.id}`}
                          className="text-blue-600 hover:underline text-xs font-medium"
                        >
                          View Report →
                        </Link>
                      )}
                      {(run.status === 'running' || run.status === 'queued') && (
                        <Link
                          to={`/run/${run.id}`}
                          className="text-amber-600 hover:underline text-xs font-medium"
                        >
                          Watch Live →
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, icon, color }) {
  return (
    <div className={`rounded-xl border p-5 ${color}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{label}</p>
          <p className="text-3xl font-bold text-gray-800 mt-1">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  )
}

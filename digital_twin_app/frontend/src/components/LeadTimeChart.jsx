/**
 * Lead time distribution histogram using Recharts.
 */
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['#2563eb', '#f59e0b', '#10b981']

function buildHistogram(values, bins = 20) {
  if (!values?.length) return []
  const min = Math.min(...values)
  const max = Math.max(...values)
  const binWidth = (max - min) / bins || 1
  const counts = Array(bins).fill(0)
  values.forEach((v) => {
    const idx = Math.min(Math.floor((v - min) / binWidth), bins - 1)
    counts[idx]++
  })
  return counts.map((count, i) => ({
    range: `${((min + i * binWidth) / 60).toFixed(1)}`,
    count,
  }))
}

export default function LeadTimeChart({ scenarios = [] }) {
  if (!scenarios.length) return null

  // Show histogram for first scenario
  const first = scenarios[0]
  const histData = buildHistogram(first?.all_lead_times ?? [])

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h3 className="font-semibold text-gray-800 mb-1">Lead Time Distribution</h3>
      <p className="text-xs text-gray-500 mb-4">
        {first?.scenario_name} — {first?.all_lead_times?.length ?? 0} parts
      </p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={histData} margin={{ top: 5, right: 20, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="range"
            label={{ value: 'Lead Time (min)', position: 'insideBottom', offset: -10, fontSize: 12 }}
            tick={{ fontSize: 10 }}
          />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(v) => [`${v} parts`, 'Count']}
            labelFormatter={(l) => `~${l} min`}
          />
          <Bar dataKey="count" fill={COLORS[0]} radius={[3, 3, 0, 0]} name="Parts" />
        </BarChart>
      </ResponsiveContainer>

      {/* Summary stats */}
      <div className="mt-3 grid grid-cols-3 gap-3">
        {scenarios.slice(0, 3).map((s, i) => {
          const lts = s.all_lead_times ?? []
          const avg = lts.length ? lts.reduce((a, b) => a + b, 0) / lts.length : 0
          const sorted = [...lts].sort((a, b) => a - b)
          const p95 = sorted[Math.floor(sorted.length * 0.95)] ?? 0
          return (
            <div key={s.scenario_name} className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-gray-600 mb-1" style={{ color: COLORS[i] }}>
                {s.scenario_name}
              </p>
              <p className="text-xs text-gray-500">Avg: <span className="font-medium text-gray-800">{(avg / 60).toFixed(1)} min</span></p>
              <p className="text-xs text-gray-500">P95: <span className="font-medium text-gray-800">{(p95 / 60).toFixed(1)} min</span></p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

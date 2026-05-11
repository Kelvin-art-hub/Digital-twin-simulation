/**
 * Throughput comparison bar chart using Recharts.
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, LabelList,
} from 'recharts'

const COLORS = ['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']

export default function ThroughputChart({ scenarios = [] }) {
  if (!scenarios.length) return null

  const data = scenarios.map((s) => ({
    name: s.scenario_name,
    throughput: parseFloat(s.throughput_per_hour?.toFixed(2)),
  }))

  const baseline = data[0]?.throughput || 1

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h3 className="font-semibold text-gray-800 mb-4">Throughput Comparison (parts/hr)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value, name, props) => {
              const pct = ((value - baseline) / baseline * 100).toFixed(1)
              const sign = pct >= 0 ? '+' : ''
              return [
                `${value} parts/hr${props.payload.name !== data[0].name ? ` (${sign}${pct}% vs base)` : ''}`,
                'Throughput',
              ]
            }}
          />
          <Bar dataKey="throughput" radius={[6, 6, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
            ))}
            <LabelList dataKey="throughput" position="top" style={{ fontSize: 12, fontWeight: 600 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

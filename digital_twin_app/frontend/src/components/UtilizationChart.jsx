/**
 * Station utilization grouped bar chart + radar chart.
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts'

const COLORS = ['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']
const STATION_ORDER = ['Feeding', 'Drilling', 'Inspection', 'Assembly', 'Packing']

export default function UtilizationChart({ scenarios = [], variant = 'bar' }) {
  if (!scenarios.length) return null

  const stations = scenarios[0]?.station_metrics
    ? Object.keys(scenarios[0].station_metrics)
    : STATION_ORDER

  const barData = stations.map((sname) => {
    const row = { station: sname }
    scenarios.forEach((s) => {
      row[s.scenario_name] = parseFloat(
        ((s.station_metrics?.[sname]?.utilization ?? 0) * 100).toFixed(1)
      )
    })
    return row
  })

  const radarData = stations.map((sname) => {
    const row = { station: sname }
    scenarios.forEach((s) => {
      row[s.scenario_name] = parseFloat(
        ((s.station_metrics?.[sname]?.utilization ?? 0) * 100).toFixed(1)
      )
    })
    return row
  })

  if (variant === 'radar') {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <h3 className="font-semibold text-gray-800 mb-4">Station Utilization Radar</h3>
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="station" tick={{ fontSize: 12 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
            {scenarios.map((s, i) => (
              <Radar
                key={s.scenario_name}
                name={s.scenario_name}
                dataKey={s.scenario_name}
                stroke={COLORS[i % COLORS.length]}
                fill={COLORS[i % COLORS.length]}
                fillOpacity={0.15}
              />
            ))}
            <Legend />
            <Tooltip formatter={(v) => `${v}%`} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h3 className="font-semibold text-gray-800 mb-4">Station Utilization (%)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={barData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="station" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 110]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => `${v}%`} />
          <Legend />
          {scenarios.map((s, i) => (
            <Bar
              key={s.scenario_name}
              dataKey={s.scenario_name}
              fill={COLORS[i % COLORS.length]}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

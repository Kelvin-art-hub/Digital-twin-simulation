/**
 * Scenario comparison metrics table.
 */
const STATION_ORDER = ['Feeding', 'Drilling', 'Inspection', 'Assembly', 'Packing']

export default function MetricsTable({ scenarios = [] }) {
  if (!scenarios.length) return null

  const stations = scenarios[0]?.station_metrics
    ? Object.keys(scenarios[0].station_metrics)
    : STATION_ORDER

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-brand-900 text-white">
            <th className="text-left px-4 py-3 font-semibold w-48">Metric</th>
            {scenarios.map((s) => (
              <th key={s.scenario_name} className="text-center px-4 py-3 font-semibold">
                {s.scenario_name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <SectionRow label="Production" colSpan={scenarios.length + 1} />
          <DataRow
            label="Parts Produced"
            values={scenarios.map((s) => s.parts_produced?.toFixed(1))}
          />
          <DataRow
            label="Throughput (parts/hr)"
            values={scenarios.map((s) => s.throughput_per_hour?.toFixed(2))}
            highlight
          />
          <DataRow
            label="Avg Lead Time (min)"
            values={scenarios.map((s) => (s.average_lead_time / 60)?.toFixed(2))}
          />
          <DataRow
            label="Bottleneck Station"
            values={scenarios.map((s) => s.bottleneck_station)}
          />

          <SectionRow label="Station Utilization" colSpan={scenarios.length + 1} />
          {stations.map((sname) => (
            <DataRow
              key={sname}
              label={`${sname}`}
              values={scenarios.map((s) => {
                const util = s.station_metrics?.[sname]?.utilization ?? 0
                return (
                  <UtilBadge value={util} />
                )
              })}
            />
          ))}

          <SectionRow label="Avg Waiting Time (s)" colSpan={scenarios.length + 1} />
          {stations.map((sname) => (
            <DataRow
              key={sname}
              label={`${sname}`}
              values={scenarios.map((s) =>
                (s.station_metrics?.[sname]?.average_waiting_time ?? 0).toFixed(1)
              )}
            />
          ))}

          <SectionRow label="Breakdowns" colSpan={scenarios.length + 1} />
          {stations.map((sname) => (
            <DataRow
              key={sname}
              label={`${sname}`}
              values={scenarios.map((s) => {
                const bd = s.station_metrics?.[sname]?.breakdown_count ?? 0
                const dt = s.station_metrics?.[sname]?.total_downtime ?? 0
                return `${bd.toFixed(1)} (${(dt / 60).toFixed(1)}min)`
              })}
            />
          ))}

          {scenarios.some((s) => s.throughput_improvement != null) && (
            <>
              <SectionRow label="vs Base Case" colSpan={scenarios.length + 1} />
              <DataRow
                label="Throughput Δ"
                values={scenarios.map((s) =>
                  s.throughput_improvement != null ? (
                    <ImprovementBadge value={s.throughput_improvement} />
                  ) : (
                    <span className="text-gray-400 text-xs">baseline</span>
                  )
                )}
              />
              <DataRow
                label="Lead Time Δ"
                values={scenarios.map((s) =>
                  s.lead_time_improvement != null ? (
                    <ImprovementBadge value={s.lead_time_improvement} />
                  ) : (
                    <span className="text-gray-400 text-xs">baseline</span>
                  )
                )}
              />
            </>
          )}
        </tbody>
      </table>
    </div>
  )
}

function SectionRow({ label, colSpan }) {
  return (
    <tr className="bg-gray-100">
      <td colSpan={colSpan} className="px-4 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
        {label}
      </td>
    </tr>
  )
}

function DataRow({ label, values, highlight }) {
  return (
    <tr className={`border-b border-gray-100 ${highlight ? 'bg-blue-50' : 'hover:bg-gray-50'}`}>
      <td className="px-4 py-2.5 text-gray-700 font-medium">{label}</td>
      {values.map((v, i) => (
        <td key={i} className="px-4 py-2.5 text-center text-gray-800">
          {v}
        </td>
      ))}
    </tr>
  )
}

function UtilBadge({ value }) {
  const pct = (value * 100).toFixed(1)
  const color =
    value >= 0.9 ? 'bg-red-100 text-red-700' :
    value >= 0.7 ? 'bg-amber-100 text-amber-700' :
    'bg-green-100 text-green-700'
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${color}`}>
      {pct}%
    </span>
  )
}

function ImprovementBadge({ value }) {
  const color = value >= 0 ? 'text-green-600' : 'text-red-600'
  const sign = value >= 0 ? '+' : ''
  return (
    <span className={`font-semibold ${color}`}>
      {sign}{value.toFixed(1)}%
    </span>
  )
}

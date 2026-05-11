/**
 * Full scenario comparison section combining table and charts.
 */
import MetricsTable from './MetricsTable'
import ThroughputChart from './ThroughputChart'
import UtilizationChart from './UtilizationChart'
import LeadTimeChart from './LeadTimeChart'

export default function ScenarioComparison({ scenarios = [] }) {
  if (!scenarios.length) return null

  return (
    <div className="space-y-6">
      <MetricsTable scenarios={scenarios} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ThroughputChart scenarios={scenarios} />
        <UtilizationChart scenarios={scenarios} variant="radar" />
      </div>
      <UtilizationChart scenarios={scenarios} variant="bar" />
      <LeadTimeChart scenarios={scenarios} />
    </div>
  )
}

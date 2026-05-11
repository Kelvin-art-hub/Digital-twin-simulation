import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MetricsTable from '../components/MetricsTable'

const mockScenarios = [
  {
    scenario_name: 'Base Case',
    parts_produced: 644.0,
    throughput_per_hour: 85.87,
    average_lead_time: 599.4,
    bottleneck_station: 'Drilling',
    station_metrics: {
      Feeding: { utilization: 0.43, average_waiting_time: 233.6, breakdown_count: 26.8, total_downtime: 1602 },
      Drilling: { utilization: 0.999, average_waiting_time: 233.6, breakdown_count: 11.5, total_downtime: 690 },
    },
    all_lead_times: [500, 600, 700],
    num_replications: 10,
    throughput_variance: 0.5,
    lead_time_variance: 100,
    parts_produced_variance: 4,
    throughput_improvement: null,
    lead_time_improvement: null,
  },
  {
    scenario_name: 'Bottleneck Fix',
    parts_produced: 899.8,
    throughput_per_hour: 119.97,
    average_lead_time: 751.9,
    bottleneck_station: 'Inspection',
    station_metrics: {
      Feeding: { utilization: 0.60, average_waiting_time: 162.1, breakdown_count: 27.2, total_downtime: 1644 },
      Drilling: { utilization: 0.40, average_waiting_time: 162.1, breakdown_count: 21.6, total_downtime: 1290 },
    },
    all_lead_times: [700, 750, 800],
    num_replications: 10,
    throughput_variance: 0.3,
    lead_time_variance: 80,
    parts_produced_variance: 3,
    throughput_improvement: 39.7,
    lead_time_improvement: -25.5,
  },
]

describe('MetricsTable', () => {
  it('renders without crashing', () => {
    render(<MetricsTable scenarios={mockScenarios} />)
  })

  it('renders scenario names as column headers', () => {
    render(<MetricsTable scenarios={mockScenarios} />)
    expect(screen.getByText('Base Case')).toBeInTheDocument()
    expect(screen.getByText('Bottleneck Fix')).toBeInTheDocument()
  })

  it('renders parts produced', () => {
    render(<MetricsTable scenarios={mockScenarios} />)
    expect(screen.getByText('644.0')).toBeInTheDocument()
    expect(screen.getByText('899.8')).toBeInTheDocument()
  })

  it('renders throughput values', () => {
    render(<MetricsTable scenarios={mockScenarios} />)
    expect(screen.getByText('85.87')).toBeInTheDocument()
    expect(screen.getByText('119.97')).toBeInTheDocument()
  })

  it('renders bottleneck stations', () => {
    render(<MetricsTable scenarios={mockScenarios} />)
    // Drilling appears as both a station name and bottleneck value — use getAllByText
    const drillingElements = screen.getAllByText('Drilling')
    expect(drillingElements.length).toBeGreaterThan(0)
    expect(screen.getAllByText('Inspection').length).toBeGreaterThan(0)
  })

  it('renders improvement section when improvements present', () => {
    render(<MetricsTable scenarios={mockScenarios} />)
    expect(screen.getByText('vs Base Case')).toBeInTheDocument()
  })

  it('renders nothing when no scenarios', () => {
    const { container } = render(<MetricsTable scenarios={[]} />)
    expect(container.firstChild).toBeNull()
  })
})

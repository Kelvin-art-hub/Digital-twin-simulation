import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ThroughputChart from '../components/ThroughputChart'

const mockScenarios = [
  { scenario_name: 'Base Case', throughput_per_hour: 85.87 },
  { scenario_name: 'Bottleneck Fix', throughput_per_hour: 119.97 },
]

describe('ThroughputChart', () => {
  it('renders without crashing', () => {
    render(<ThroughputChart scenarios={mockScenarios} />)
  })

  it('renders chart title', () => {
    render(<ThroughputChart scenarios={mockScenarios} />)
    expect(screen.getByText('Throughput Comparison (parts/hr)')).toBeInTheDocument()
  })

  it('renders nothing when no scenarios', () => {
    const { container } = render(<ThroughputChart scenarios={[]} />)
    expect(container.firstChild).toBeNull()
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Configure from '../pages/Configure'

// Mock the simulation hook
vi.mock('../hooks/useSimulation', () => ({
  useRunSimulation: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ job_id: 'test-job-123' }),
    isPending: false,
  }),
}))

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderConfigure() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Configure />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Configure page', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })

  it('renders the form', () => {
    renderConfigure()
    expect(screen.getByText('Configure Simulation')).toBeInTheDocument()
  })

  it('renders preset buttons', () => {
    renderConfigure()
    expect(screen.getByText('Base Case')).toBeInTheDocument()
    expect(screen.getByText('Extra Buffer')).toBeInTheDocument()
    expect(screen.getByText('Bottleneck Fix')).toBeInTheDocument()
  })

  it('renders station cards', () => {
    renderConfigure()
    expect(screen.getByText('Feeding')).toBeInTheDocument()
    expect(screen.getByText('Drilling')).toBeInTheDocument()
    expect(screen.getByText('Inspection')).toBeInTheDocument()
  })

  it('renders run simulation button', () => {
    renderConfigure()
    expect(screen.getByText('▶ Run Simulation')).toBeInTheDocument()
  })

  it('shows validation error when name is empty', async () => {
    renderConfigure()
    // Clear the name field
    const nameInput = screen.getAllByPlaceholderText('My Simulation')[0]
    fireEvent.change(nameInput, { target: { value: '' } })

    const submitBtn = screen.getByText('▶ Run Simulation')
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument()
    })
  })

  it('loads base case preset', () => {
    renderConfigure()
    const baseCaseBtn = screen.getAllByText('Base Case')[0]
    fireEvent.click(baseCaseBtn)
    // After loading preset, form should still be visible
    expect(screen.getByText('Configure Simulation')).toBeInTheDocument()
  })
})

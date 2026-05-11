/**
 * Hook for running simulations and polling status.
 * Compatible with React Query v5 (no onSuccess/onError callbacks on useQuery).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { simulationApi } from '../api/client'
import { useSimulationStore } from '../store/simulationStore'

export function useRunSimulation() {
  const { setActiveJob } = useSimulationStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (config) => simulationApi.run(config).then((r) => r.data),
    onSuccess: (data) => {
      setActiveJob(data.job_id)
      queryClient.invalidateQueries({ queryKey: ['history'] })
    },
  })
}

export function useSimulationStatus(jobId, enabled = true) {
  const { updateJobStatus } = useSimulationStore()

  const query = useQuery({
    queryKey: ['simulation', 'status', jobId],
    queryFn: () => simulationApi.getStatus(jobId).then((r) => r.data),
    enabled: !!jobId && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'complete' || status === 'failed') return false
      return 2000
    },
  })

  // React Query v5: use useEffect instead of onSuccess
  useEffect(() => {
    if (query.data) {
      updateJobStatus(query.data.status, query.data.progress)
    }
  }, [query.data, updateJobStatus])

  return query
}

export function useSimulationResults(jobId, enabled = true) {
  const { setResults } = useSimulationStore()

  const query = useQuery({
    queryKey: ['simulation', 'results', jobId],
    queryFn: () => simulationApi.getResults(jobId).then((r) => r.data),
    enabled: !!jobId && enabled,
    retry: (failureCount, error) => {
      // Don't retry on 202 (still running) or 404
      if (error?.message?.includes('202') || error?.message?.includes('404')) return false
      return failureCount < 2
    },
  })

  useEffect(() => {
    if (query.data) {
      setResults(query.data)
    }
  }, [query.data, setResults])

  return query
}

export function useSimulationHistory() {
  return useQuery({
    queryKey: ['history'],
    queryFn: () => simulationApi.getHistory().then((r) => r.data),
    staleTime: 30000,
  })
}

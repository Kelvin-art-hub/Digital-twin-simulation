/**
 * Zustand global state store for simulation state.
 */
import { create } from 'zustand'

const DEFAULT_STATIONS = [
  { name: 'Feeding', cycle_time_mean: 18, cycle_time_std: 1.8, buffer_capacity: 5, operators: 1, breakdown_probability: 0.02, repair_time_min: 30, repair_time_max: 90 },
  { name: 'Drilling', cycle_time_mean: 42, cycle_time_std: 4.2, buffer_capacity: 5, operators: 1, breakdown_probability: 0.02, repair_time_min: 30, repair_time_max: 90 },
  { name: 'Inspection', cycle_time_mean: 22, cycle_time_std: 2.2, buffer_capacity: 5, operators: 1, breakdown_probability: 0.02, repair_time_min: 30, repair_time_max: 90 },
  { name: 'Assembly', cycle_time_mean: 30, cycle_time_std: 3.0, buffer_capacity: 5, operators: 2, breakdown_probability: 0.02, repair_time_min: 30, repair_time_max: 90 },
  { name: 'Packing', cycle_time_mean: 20, cycle_time_std: 2.0, buffer_capacity: 5, operators: 1, breakdown_probability: 0.02, repair_time_min: 30, repair_time_max: 90 },
]

export const PRESETS = {
  base_case: {
    name: 'Base Case',
    stations: DEFAULT_STATIONS,
    shift_duration_hours: 8,
    warmup_period_minutes: 30,
    num_replications: 10,
    seed_base: 42,
  },
  extra_buffer: {
    name: 'Extra Buffer',
    stations: DEFAULT_STATIONS.map((s) =>
      s.name === 'Drilling' ? { ...s, buffer_capacity: 10 } : s
    ),
    shift_duration_hours: 8,
    warmup_period_minutes: 30,
    num_replications: 10,
    seed_base: 42,
  },
  bottleneck_fix: {
    name: 'Bottleneck Fix',
    stations: DEFAULT_STATIONS.map((s) =>
      s.name === 'Drilling' ? { ...s, operators: 2, cycle_time_mean: 24, cycle_time_std: 2.4 } : s
    ),
    shift_duration_hours: 8,
    warmup_period_minutes: 30,
    num_replications: 10,
    seed_base: 42,
  },
}

export const useSimulationStore = create((set, get) => ({
  // Current simulation config being edited
  config: { ...PRESETS.base_case },

  // Active job tracking
  activeJobId: null,
  jobStatus: null,   // 'queued' | 'running' | 'complete' | 'failed'
  jobProgress: 0,

  // Live WebSocket data
  liveEvents: [],
  liveBufferLevels: {},
  liveThroughput: 0,
  livePartsProduced: 0,

  // Results
  results: null,

  // Actions
  setConfig: (config) => set({ config }),

  updateStation: (index, updates) =>
    set((state) => {
      const stations = [...state.config.stations]
      stations[index] = { ...stations[index], ...updates }
      return { config: { ...state.config, stations } }
    }),

  loadPreset: (presetKey) => {
    const preset = PRESETS[presetKey]
    if (preset) set({ config: { ...preset } })
  },

  setActiveJob: (jobId) => set({ activeJobId: jobId, jobStatus: 'queued', jobProgress: 0, liveEvents: [], results: null }),

  updateJobStatus: (status, progress) => set({ jobStatus: status, jobProgress: progress }),

  addLiveEvent: (event) =>
    set((state) => ({
      liveEvents: [...state.liveEvents.slice(-99), event],
    })),

  updateLiveMetrics: (data) =>
    set((state) => ({
      liveBufferLevels: data.buffer_levels ?? state.liveBufferLevels,
      liveThroughput: data.throughput ?? state.liveThroughput,
      livePartsProduced: data.parts_produced ?? state.livePartsProduced,
    })),

  setResults: (results) => set({ results }),

  reset: () =>
    set({
      activeJobId: null,
      jobStatus: null,
      jobProgress: 0,
      liveEvents: [],
      liveBufferLevels: {},
      liveThroughput: 0,
      livePartsProduced: 0,
      results: null,
    }),
}))

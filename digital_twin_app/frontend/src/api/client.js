/**
 * Axios API client — base URL from environment variable.
 * All API calls go through this client for consistent error handling.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,  // 10s — just for the initial POST, simulation runs in background
})

// Response interceptor — normalize errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const message =
      detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'

    // Attach status to the error so callers can check it
    const err = new Error(message)
    err.status = status
    err.response = error.response
    return Promise.reject(err)
  }
)

// ─── Simulation API ──────────────────────────────────────────────────────────

export const simulationApi = {
  run: (config) => apiClient.post('/api/simulations/run', config),
  getStatus: (jobId) => apiClient.get(`/api/simulations/${jobId}/status`),
  getResults: (jobId) => apiClient.get(`/api/simulations/${jobId}/results`),
  getHistory: () => apiClient.get('/api/simulations/history'),
}

// ─── Scenarios API ───────────────────────────────────────────────────────────

export const scenariosApi = {
  list: () => apiClient.get('/api/scenarios'),
  save: (payload) => apiClient.post('/api/scenarios', payload),
  get: (id) => apiClient.get(`/api/scenarios/${id}`),
  delete: (id) => apiClient.delete(`/api/scenarios/${id}`),
}

// ─── Reports API ─────────────────────────────────────────────────────────────

export const reportsApi = {
  downloadCsv: (jobId) =>
    apiClient.get(`/api/reports/${jobId}/csv`, { responseType: 'blob' }),
  downloadLeadTimesCsv: (jobId) =>
    apiClient.get(`/api/reports/${jobId}/csv/lead_times`, { responseType: 'blob' }),
  downloadPdf: (jobId) =>
    apiClient.get(`/api/reports/${jobId}/pdf`, { responseType: 'blob' }),
}

// ─── Health API ──────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => apiClient.get('/health'),
}

// ─── WebSocket helper ────────────────────────────────────────────────────────

export function createSimulationWebSocket(jobId) {
  // In dev, Vite proxies /api → backend, so use the same host as the page.
  // In production, use VITE_WS_URL if set.
  const wsBase = import.meta.env.VITE_WS_URL
    ? import.meta.env.VITE_WS_URL
    : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
  return new WebSocket(`${wsBase}/api/simulations/ws/${jobId}`)
}

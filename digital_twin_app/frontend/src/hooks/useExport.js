/**
 * Hook for downloading CSV and PDF reports.
 */
import { useState } from 'react'
import { reportsApi } from '../api/client'

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function useExport(jobId) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const downloadCsv = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await reportsApi.downloadCsv(jobId)
      triggerDownload(resp.data, `simulation_${jobId}_metrics.csv`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadLeadTimesCsv = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await reportsApi.downloadLeadTimesCsv(jobId)
      triggerDownload(resp.data, `simulation_${jobId}_lead_times.csv`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadPdf = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await reportsApi.downloadPdf(jobId)
      triggerDownload(resp.data, `simulation_${jobId}_report.pdf`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return { downloadCsv, downloadLeadTimesCsv, downloadPdf, loading, error }
}

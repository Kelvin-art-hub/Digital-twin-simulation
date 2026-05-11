/**
 * Export buttons for CSV and PDF downloads.
 */
import { useExport } from '../hooks/useExport'

export default function ExportPanel({ jobId }) {
  const { downloadCsv, downloadLeadTimesCsv, downloadPdf, loading, error } = useExport(jobId)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h3 className="font-semibold text-gray-800 mb-4">Export Results</h3>

      {error && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <ExportButton
          onClick={downloadCsv}
          loading={loading}
          icon="📊"
          label="Metrics CSV"
          description="All scenario metrics"
        />
        <ExportButton
          onClick={downloadLeadTimesCsv}
          loading={loading}
          icon="📈"
          label="Lead Times CSV"
          description="Per-part lead time data"
        />
        <ExportButton
          onClick={downloadPdf}
          loading={loading}
          icon="📄"
          label="PDF Report"
          description="Full formatted report"
          primary
        />
      </div>
    </div>
  )
}

function ExportButton({ onClick, loading, icon, label, description, primary }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all text-left ${
        primary
          ? 'bg-brand-900 text-white border-brand-900 hover:bg-brand-700 disabled:opacity-50'
          : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50'
      }`}
    >
      <span className="text-xl">{icon}</span>
      <div>
        <p className="text-sm font-semibold">{label}</p>
        <p className={`text-xs ${primary ? 'text-blue-200' : 'text-gray-400'}`}>{description}</p>
      </div>
      {loading && (
        <svg className="animate-spin h-4 w-4 ml-2" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      )}
    </button>
  )
}

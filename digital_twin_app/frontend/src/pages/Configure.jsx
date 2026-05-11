/**
 * Configure page — simulation setup form with validation.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StationCard from '../components/StationCard'
import { useSimulationStore, PRESETS } from '../store/simulationStore'
import { useRunSimulation } from '../hooks/useSimulation'

function validate(config) {
  const errors = {}
  if (!config.name?.trim()) errors.name = 'Name is required'
  if (config.shift_duration_hours <= 0) errors.shift_duration_hours = 'Must be > 0'
  if (config.warmup_period_minutes < 0) errors.warmup_period_minutes = 'Must be >= 0'
  if (config.num_replications < 1) errors.num_replications = 'Must be >= 1'

  config.stations?.forEach((s, i) => {
    if (!s.name?.trim()) errors[`stations.${i}.name`] = 'Required'
    if (s.cycle_time_mean <= 0) errors[`stations.${i}.cycle_time_mean`] = 'Must be > 0'
    if (s.cycle_time_std < 0) errors[`stations.${i}.cycle_time_std`] = 'Must be >= 0'
    if (s.buffer_capacity < 1) errors[`stations.${i}.buffer_capacity`] = 'Must be >= 1'
    if (s.operators < 1) errors[`stations.${i}.operators`] = 'Must be >= 1'
    if (s.breakdown_probability < 0 || s.breakdown_probability > 1)
      errors[`stations.${i}.breakdown_probability`] = '0–1'
    if (s.repair_time_max < s.repair_time_min)
      errors[`stations.${i}.repair_time_max`] = 'Max >= Min'
  })

  const names = config.stations?.map((s) => s.name) ?? []
  if (new Set(names).size !== names.length) errors.stations = 'Station names must be unique'

  return errors
}

export default function Configure() {
  const navigate = useNavigate()
  const { config, setConfig, updateStation, loadPreset } = useSimulationStore()
  const [errors, setErrors] = useState({})
  const [saveScenarioName, setSaveScenarioName] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)

  const runMutation = useRunSimulation()

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate(config)
    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      return
    }
    setErrors({})

    try {
      const result = await runMutation.mutateAsync(config)
      navigate(`/run/${result.job_id}`)
    } catch (err) {
      console.error('Simulation run failed:', err)
      setErrors({ submit: `Failed to start simulation: ${err.message}` })
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Configure Simulation</h1>
        <p className="text-gray-500 mt-1">Set up your assembly line parameters</p>
      </div>

      {/* Preset loader */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
        <h2 className="font-semibold text-gray-700 mb-3">Load Preset</h2>
        <div className="flex flex-wrap gap-3">
          {Object.entries(PRESETS).map(([key, preset]) => (
            <button
              key={key}
              onClick={() => loadPreset(key)}
              className="px-4 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-700 hover:bg-blue-50 hover:border-blue-300 transition-colors"
            >
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        {/* Global settings */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
          <h2 className="font-semibold text-gray-700 mb-4">Simulation Settings</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Run Name</label>
              <input
                type="text"
                value={config.name}
                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.name ? 'border-red-400' : 'border-gray-300'}`}
                placeholder="My Simulation"
              />
              {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Shift Duration (hrs)</label>
              <input
                type="number"
                value={config.shift_duration_hours}
                onChange={(e) => setConfig({ ...config, shift_duration_hours: parseFloat(e.target.value) || 8 })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0.1" max="24" step="0.5"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Warm-up (min)</label>
              <input
                type="number"
                value={config.warmup_period_minutes}
                onChange={(e) => setConfig({ ...config, warmup_period_minutes: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0" max="120"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Replications</label>
              <input
                type="number"
                value={config.num_replications}
                onChange={(e) => setConfig({ ...config, num_replications: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1" max="50"
              />
            </div>
          </div>
        </div>

        {/* Station cards */}
        {errors.stations && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {errors.stations}
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 mb-6">
          {config.stations?.map((station, i) => (
            <StationCard
              key={i}
              station={station}
              index={i}
              onChange={updateStation}
              errors={errors}
            />
          ))}
        </div>

        {/* Submit */}
        {errors.submit && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {errors.submit}
          </div>
        )}

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={runMutation.isPending}
            className="bg-brand-900 text-white px-8 py-3 rounded-lg font-semibold hover:bg-brand-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {runMutation.isPending ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Starting...
              </>
            ) : (
              '▶ Run Simulation'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

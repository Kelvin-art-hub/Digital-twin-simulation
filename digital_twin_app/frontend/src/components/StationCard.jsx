/**
 * Editable station configuration card.
 */
export default function StationCard({ station, index, onChange, errors = {} }) {
  const field = (name) => `stations.${index}.${name}`

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-800 text-lg">{station.name}</h3>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
          Station {index + 1}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <FormField
          label="Cycle Time Mean (s)"
          value={station.cycle_time_mean}
          onChange={(v) => onChange(index, { cycle_time_mean: parseFloat(v) || 0 })}
          error={errors[field('cycle_time_mean')]}
          type="number"
          min="0.1"
          step="0.5"
        />
        <FormField
          label="Std Dev (s)"
          value={station.cycle_time_std}
          onChange={(v) => onChange(index, { cycle_time_std: parseFloat(v) || 0 })}
          error={errors[field('cycle_time_std')]}
          type="number"
          min="0"
          step="0.1"
        />
        <FormField
          label="Buffer Capacity"
          value={station.buffer_capacity}
          onChange={(v) => onChange(index, { buffer_capacity: parseInt(v) || 1 })}
          error={errors[field('buffer_capacity')]}
          type="number"
          min="1"
          max="100"
        />
        <FormField
          label="Operators"
          value={station.operators}
          onChange={(v) => onChange(index, { operators: parseInt(v) || 1 })}
          error={errors[field('operators')]}
          type="number"
          min="1"
          max="10"
        />
        <FormField
          label="Breakdown Prob."
          value={station.breakdown_probability}
          onChange={(v) => onChange(index, { breakdown_probability: parseFloat(v) || 0 })}
          error={errors[field('breakdown_probability')]}
          type="number"
          min="0"
          max="1"
          step="0.01"
        />
        <div className="col-span-2 grid grid-cols-2 gap-3">
          <FormField
            label="Repair Min (s)"
            value={station.repair_time_min}
            onChange={(v) => onChange(index, { repair_time_min: parseFloat(v) || 0 })}
            type="number"
            min="1"
          />
          <FormField
            label="Repair Max (s)"
            value={station.repair_time_max}
            onChange={(v) => onChange(index, { repair_time_max: parseFloat(v) || 0 })}
            type="number"
            min="1"
          />
        </div>
      </div>
    </div>
  )
}

function FormField({ label, value, onChange, error, type = 'text', ...props }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? 'border-red-400 bg-red-50' : 'border-gray-300'
        }`}
        {...props}
      />
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  )
}

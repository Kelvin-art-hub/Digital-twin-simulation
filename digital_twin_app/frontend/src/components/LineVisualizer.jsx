/**
 * SVG assembly line visualizer with animated parts and real-time buffer levels.
 */
import { useEffect, useRef, useState } from 'react'

const STATIONS = ['Feeding', 'Drilling', 'Inspection', 'Assembly', 'Packing']
const SVG_W = 900
const SVG_H = 200
const STATION_W = 100
const STATION_H = 70
const GAP = 60
const Y_CENTER = SVG_H / 2
const TOTAL_STATIONS = STATIONS.length

function stationX(i) {
  const totalWidth = TOTAL_STATIONS * STATION_W + (TOTAL_STATIONS - 1) * GAP
  const startX = (SVG_W - totalWidth) / 2
  return startX + i * (STATION_W + GAP)
}

function utilizationColor(util) {
  if (util >= 0.9) return '#ef4444'
  if (util >= 0.7) return '#f59e0b'
  return '#22c55e'
}

export default function LineVisualizer({ utilizations = {}, bufferLevels = {}, bufferCapacities = {}, isRunning = false, bottleneck = '' }) {
  const [parts, setParts] = useState([])
  const partIdRef = useRef(0)
  const animFrameRef = useRef(null)

  // Spawn animated parts when running
  useEffect(() => {
    if (!isRunning) return

    const interval = setInterval(() => {
      partIdRef.current += 1
      const id = partIdRef.current
      setParts((prev) => [
        ...prev.slice(-8),
        { id, x: stationX(0) + STATION_W / 2, stationIndex: 0, progress: 0 },
      ])
    }, 2500)

    return () => clearInterval(interval)
  }, [isRunning])

  // Animate parts along the line
  useEffect(() => {
    if (!isRunning) return

    let last = performance.now()
    function animate(now) {
      const dt = (now - last) / 1000
      last = now
      setParts((prev) =>
        prev
          .map((p) => {
            const newProgress = p.progress + dt * 0.3
            if (newProgress >= 1) {
              const nextStation = p.stationIndex + 1
              if (nextStation >= TOTAL_STATIONS) return null
              return { ...p, stationIndex: nextStation, progress: 0 }
            }
            const fromX = stationX(p.stationIndex) + STATION_W
            const toX = stationX(p.stationIndex + 1 < TOTAL_STATIONS ? p.stationIndex + 1 : p.stationIndex)
            return { ...p, x: fromX + (toX - fromX) * newProgress, progress: newProgress }
          })
          .filter(Boolean)
      )
      animFrameRef.current = requestAnimationFrame(animate)
    }
    animFrameRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animFrameRef.current)
  }, [isRunning])

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm overflow-x-auto">
      <h3 className="font-semibold text-gray-800 mb-3">Assembly Line</h3>
      <svg viewBox={`0 0 ${SVG_W} ${SVG_H}`} className="w-full" style={{ minWidth: 600 }}>
        {/* Conveyor belts */}
        {STATIONS.slice(0, -1).map((_, i) => {
          const x1 = stationX(i) + STATION_W
          const x2 = stationX(i + 1)
          return (
            <g key={i}>
              <line
                x1={x1} y1={Y_CENTER} x2={x2} y2={Y_CENTER}
                stroke="#d1d5db" strokeWidth={8} strokeLinecap="round"
              />
              {/* Conveyor dashes */}
              <line
                x1={x1 + 4} y1={Y_CENTER} x2={x2 - 4} y2={Y_CENTER}
                stroke="#9ca3af" strokeWidth={2} strokeDasharray="6 4"
              />
            </g>
          )
        })}

        {/* Stations */}
        {STATIONS.map((name, i) => {
          const x = stationX(i)
          const util = utilizations[name] ?? 0
          const color = utilizationColor(util)
          const isBottleneck = name === bottleneck
          const bufLevel = bufferLevels[name] ?? 0
          const bufCap = bufferCapacities[name] ?? 5

          return (
            <g key={name}>
              {/* Bottleneck pulsing border */}
              {isBottleneck && (
                <rect
                  x={x - 4} y={Y_CENTER - STATION_H / 2 - 4}
                  width={STATION_W + 8} height={STATION_H + 8}
                  rx={10} fill="none"
                  stroke="#ef4444" strokeWidth={3}
                  opacity={0.7}
                >
                  <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite" />
                </rect>
              )}

              {/* Station box */}
              <rect
                x={x} y={Y_CENTER - STATION_H / 2}
                width={STATION_W} height={STATION_H}
                rx={8} fill={color} fillOpacity={0.15}
                stroke={color} strokeWidth={2}
              />

              {/* Station name */}
              <text
                x={x + STATION_W / 2} y={Y_CENTER - 12}
                textAnchor="middle" fontSize={11} fontWeight="600" fill="#374151"
              >
                {name}
              </text>

              {/* Utilization % */}
              <text
                x={x + STATION_W / 2} y={Y_CENTER + 4}
                textAnchor="middle" fontSize={13} fontWeight="700" fill={color}
              >
                {(util * 100).toFixed(0)}%
              </text>

              {/* Buffer dots */}
              <text
                x={x + STATION_W / 2} y={Y_CENTER + 20}
                textAnchor="middle" fontSize={9} fill="#6b7280"
              >
                buf: {bufLevel}/{bufCap}
              </text>

              {/* Buffer bar */}
              <rect
                x={x + 8} y={Y_CENTER + 24}
                width={STATION_W - 16} height={5}
                rx={2} fill="#e5e7eb"
              />
              <rect
                x={x + 8} y={Y_CENTER + 24}
                width={Math.max(0, ((STATION_W - 16) * bufLevel) / Math.max(bufCap, 1))}
                height={5}
                rx={2} fill={color}
              />
            </g>
          )
        })}

        {/* Animated parts */}
        {parts.map((p) => (
          <circle
            key={p.id}
            cx={p.x}
            cy={Y_CENTER}
            r={7}
            fill="#2563eb"
            stroke="white"
            strokeWidth={2}
            opacity={0.85}
          />
        ))}
      </svg>

      {/* Legend */}
      <div className="flex gap-4 mt-3 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500 inline-block" /> &lt;70% util</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-amber-500 inline-block" /> 70–90%</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> &gt;90% (bottleneck)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-500 inline-block" /> part in transit</span>
      </div>
    </div>
  )
}

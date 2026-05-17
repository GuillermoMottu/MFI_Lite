interface Signal {
  label: string
  value: number
  max: number
  unit: string
  weight: string
}

interface InferenceStatus {
  signals?: {
    stockout_hours?: number
    oee?: number
    consumption_rate?: number
    idle_risk?: boolean
    cycle_time?: number
  }
  risk_score?: number
  threshold?: number
  is_critical?: boolean
  severity?: string
  model?: string
  inference_ms?: number
  timestamp?: string
}

interface EdgeInferencePanelProps {
  data: InferenceStatus | null
}

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'text-red-400 bg-red-950 border-red-700',
  high: 'text-orange-400 bg-orange-950 border-orange-700',
  medium: 'text-yellow-400 bg-yellow-950 border-yellow-700',
  low: 'text-green-400 bg-green-950 border-green-700',
}

function SignalBar({ label, value, max, unit, weight, danger = false }: Signal & { danger?: boolean }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400 mb-0.5">
        <span>{label} <span className="text-slate-600 font-mono">({weight})</span></span>
        <span className={`font-mono ${danger ? 'text-red-400' : 'text-slate-300'}`}>
          {value.toFixed(1)} {unit}
        </span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${danger ? 'bg-red-500' : 'bg-cyan-600'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function EdgeInferencePanel({ data }: EdgeInferencePanelProps) {
  if (!data) {
    return (
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
        <h3 className="text-sm font-semibold text-slate-300 mb-2">Edge Inference — Isolation Forest</h3>
        <p className="text-slate-500 text-xs">Sin datos. Ejecuta el demo o llama a /api/aiml/inference-status.</p>
      </div>
    )
  }

  const signals = data.signals ?? {}
  const score = data.risk_score ?? 0
  const threshold = data.threshold ?? 0.72
  const scorePct = Math.round(score * 100)
  const thresholdPct = Math.round(threshold * 100)
  const isCritical = data.is_critical ?? false
  const severity = data.severity ?? 'low'

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-300">Edge Inference — Isolation Forest</h3>
          <p className="text-xs text-slate-500 font-mono">{data.model} · {data.inference_ms}ms</p>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${SEVERITY_COLOR[severity] ?? SEVERITY_COLOR.low}`}>
          {severity.toUpperCase()}
        </span>
      </div>

      {/* Gauge de risk_score */}
      <div className="mb-4">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-slate-400">Risk Score</span>
          <span className={`font-bold font-mono ${isCritical ? 'text-red-400' : 'text-green-400'}`}>
            {scorePct}% {isCritical ? '⚠ CRÍTICO' : ''}
          </span>
        </div>
        <div className="relative h-4 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${isCritical ? 'bg-red-500' : score > 0.5 ? 'bg-yellow-500' : 'bg-green-500'}`}
            style={{ width: `${scorePct}%` }}
          />
          {/* Línea del umbral */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-white opacity-60"
            style={{ left: `${thresholdPct}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-slate-600 mt-0.5">
          <span>0</span>
          <span className="text-white/40">▲ umbral {thresholdPct}%</span>
          <span>100</span>
        </div>
      </div>

      {/* Señales individuales */}
      <div className="space-y-2">
        <SignalBar
          label="Stockout" value={signals.stockout_hours ?? 0} max={72} unit="h" weight="40%"
          danger={(signals.stockout_hours ?? 72) < 24}
        />
        <SignalBar
          label="OEE" value={Math.round((signals.oee ?? 0.78) * 100)} max={100} unit="%" weight="25%"
          danger={(signals.oee ?? 0.78) < 0.70}
        />
        <SignalBar
          label="Consumo" value={signals.consumption_rate ?? 0} max={25} unit="u/h" weight="15%"
          danger={false}
        />
        <SignalBar
          label="Cycle Time" value={signals.cycle_time ?? 0} max={12} unit="s" weight="5%"
          danger={(signals.cycle_time ?? 0) > 8}
        />
        <div className="flex justify-between text-xs">
          <span className="text-slate-400">Idle Risk <span className="text-slate-600">(15%)</span></span>
          <span className={`font-mono font-bold ${signals.idle_risk ? 'text-red-400' : 'text-green-400'}`}>
            {signals.idle_risk ? '⚠ SÍ' : 'NO'}
          </span>
        </div>
      </div>

      {data.timestamp && (
        <p className="text-xs text-slate-600 font-mono mt-3">
          Última inferencia: {data.timestamp.slice(11, 19)} UTC
        </p>
      )}
    </div>
  )
}

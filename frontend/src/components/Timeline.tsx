import { useState } from 'react'
import { api } from '../api'

interface IESEvent {
  event_id: string
  timestamp: string
  platform_version: string
  module: { id: string; version: string }
  asset: { asset_id: string; plant_id: string; line_id: string }
  event: { type: string; category: string; severity: string }
  data: Record<string, unknown>
  metadata: Record<string, unknown>
}

interface TimelineProps {
  events: IESEvent[]
  onSelect: (e: IESEvent) => void
}

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'bg-red-600 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-yellow-500 text-slate-900',
  low: 'bg-slate-600 text-white',
}

const MODULE_LABEL: Record<string, string> = {
  erp_material_planning: 'ERP',
  advanced_production_planning: 'Producción',
  materialflow_intelligence: 'AI/ML',
  edge_material_runtime: 'Edge',
}

export default function Timeline({ events, onSelect }: TimelineProps) {
  const [chainFilter, setChainFilter] = useState<string | null>(null)
  const [chainCount, setChainCount] = useState<number>(0)
  const [loadingChain, setLoadingChain] = useState(false)

  const handleViewChain = async (e: React.MouseEvent, correlationId: string) => {
    e.stopPropagation()
    if (chainFilter === correlationId) {
      setChainFilter(null)
      return
    }
    setLoadingChain(true)
    try {
      const result = await api.getEventChain(correlationId)
      setChainCount(result.count ?? 0)
      setChainFilter(correlationId)
    } finally {
      setLoadingChain(false)
    }
  }

  const displayed = chainFilter
    ? events.filter(ev => (ev.metadata?.correlation_id as string) === chainFilter)
    : events

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-300">
          Timeline IES v2.0
          <span className="ml-2 text-xs text-slate-500 font-normal">({events.length} eventos)</span>
        </h3>
        {chainFilter && (
          <button
            onClick={() => setChainFilter(null)}
            className="text-xs text-blue-400 bg-blue-950 border border-blue-700 px-2 py-0.5 rounded-full hover:bg-blue-900 transition-colors"
          >
            ⛓ Cadena ({chainCount}) — Limpiar filtro ×
          </button>
        )}
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
        {displayed.length === 0 && !chainFilter && (
          <p className="text-slate-500 text-sm text-center py-8">
            Ejecuta el demo para ver eventos en tiempo real
          </p>
        )}
        {displayed.length === 0 && chainFilter && (
          <p className="text-slate-500 text-sm text-center py-8">
            No hay eventos con este correlation_id
          </p>
        )}

        {displayed.map((ev, idx) => {
          const correlationId = ev.metadata?.correlation_id as string | undefined
          const isLast = idx === displayed.length - 1

          return (
            <div key={ev.event_id} className="relative">
              {/* Línea de cadena vertical */}
              {chainFilter && !isLast && (
                <div className="absolute left-3 top-full w-0.5 h-2 bg-blue-700 z-10" />
              )}
              <button
                onClick={() => onSelect(ev)}
                className="w-full text-left bg-slate-900 hover:bg-slate-700 rounded-lg p-3 border border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {/* IES v2.0 badge */}
                    <span
                      title="IES v2.0 Validado — platform_version 2.0.0, timestamp UTC, UUID v4"
                      className="text-green-500 text-xs shrink-0"
                    >✓</span>
                    <span className="text-xs text-slate-500 font-mono whitespace-nowrap">
                      {ev.timestamp.slice(11, 19)}
                    </span>
                    <span className="text-xs bg-slate-700 text-cyan-400 px-1.5 py-0.5 rounded font-mono whitespace-nowrap">
                      {MODULE_LABEL[ev.module?.id] ?? ev.module?.id}
                    </span>
                    <span className="text-xs text-slate-300 truncate font-mono">
                      {ev.event?.type}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {correlationId && (
                      <button
                        onClick={(e) => handleViewChain(e, correlationId)}
                        disabled={loadingChain}
                        title={`Ver cadena causal (correlation_id: ${correlationId.slice(0, 8)}...)`}
                        className={`text-xs px-1.5 py-0.5 rounded transition-colors
                          ${chainFilter === correlationId
                            ? 'bg-blue-700 text-blue-100'
                            : 'bg-slate-700 text-slate-400 hover:bg-blue-900 hover:text-blue-300'}`}
                      >
                        ⛓
                      </button>
                    )}
                    <span className="text-xs text-slate-500">{ev.asset?.asset_id}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded font-bold ${SEVERITY_COLOR[ev.event?.severity] ?? 'bg-slate-600'}`}>
                      {ev.event?.severity}
                    </span>
                  </div>
                </div>
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

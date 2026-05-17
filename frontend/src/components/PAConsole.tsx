import { useState } from 'react'
import { api } from '../api'

interface DemoStatus {
  current_stock_units?: number
  daily_demand_units?: number
  reorder_point_units?: number
  oee_pct?: number
  risk_score_pct?: number
  loss_prevented_mxn?: number
  idle_minutes_prevented?: number
  last_correlation_id?: string | null
}

interface Recommendation {
  recommendation_id: string
  type: string
  priority: string
  status: string
  sku_id: string
  line_id: string
  reason: string
  recommended_action: string
  alternative_actions: string[]
  estimated_impact_mxn: number
  risk_score: number
  correlation_id: string
  created_at: string
  decided_by?: string | null
  decision_comment?: string | null
}

interface PAConsoleProps {
  status: DemoStatus
  recommendation: Recommendation | null
  onDecision: () => void
}

const priorityStyles: Record<string, string> = {
  critical: 'bg-red-950 text-red-200 border-red-700',
  high: 'bg-orange-950 text-orange-200 border-orange-700',
  medium: 'bg-yellow-950 text-yellow-200 border-yellow-700',
  low: 'bg-slate-900 text-slate-300 border-slate-700',
}

function getRiskLabel(status: DemoStatus): string {
  const stock = status.current_stock_units ?? 0
  const reorder = status.reorder_point_units ?? 0
  const risk = status.risk_score_pct ?? 0
  if ((reorder > 0 && stock < reorder) || risk >= 75) return 'Crítico'
  if (risk >= 45) return 'Riesgo'
  return 'Normal'
}

export default function PAConsole({ status, recommendation, onDecision }: PAConsoleProps) {
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const riskLabel = getRiskLabel(status)
  const dailyDemand = status.daily_demand_units ?? 0
  const stock = status.current_stock_units ?? 0
  const stockoutHours = dailyDemand > 0 ? stock / (dailyDemand / 24) : 0

  const decide = async (action: 'approve' | 'reject') => {
    if (!recommendation) return
    setError(null)
    setBusy(true)
    try {
      if (action === 'approve') {
        await api.approveRecommendation(recommendation.recommendation_id, comment || undefined)
      } else {
        await api.rejectRecommendation(recommendation.recommendation_id, comment)
      }
      setComment('')
      onDecision()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar la decisión')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-300">Consola PA</h2>
          <p className="text-xs text-slate-500 mt-1">
            Decisión operativa para abastecimiento y continuidad de LINE-1
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full border text-xs font-bold ${
          riskLabel === 'Crítico' ? 'bg-red-950 text-red-200 border-red-700'
            : riskLabel === 'Riesgo' ? 'bg-yellow-950 text-yellow-200 border-yellow-700'
              : 'bg-green-950 text-green-200 border-green-700'
        }`}>
          {riskLabel}
        </span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <Metric label="SKU" value={recommendation?.sku_id ?? 'SKU-ACERO-M8'} />
        <Metric label="Stockout estimado" value={`${stockoutHours.toFixed(1)} h`} />
        <Metric label="Impacto" value={`$${((recommendation?.estimated_impact_mxn ?? status.loss_prevented_mxn ?? 0) / 1000).toFixed(1)}k MXN`} />
        <Metric label="Riesgo AI/ML" value={`${(status.risk_score_pct ?? 0).toFixed(1)}%`} />
      </div>

      {recommendation ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 bg-slate-900 rounded-lg border border-slate-700 p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-0.5 rounded-full border text-xs font-bold ${priorityStyles[recommendation.priority] ?? priorityStyles.low}`}>
                {recommendation.priority}
              </span>
              <span className="text-xs text-slate-500 font-mono">{recommendation.recommendation_id}</span>
              <span className="text-xs text-slate-400 ml-auto">{recommendation.status}</span>
            </div>
            <p className="text-sm text-slate-200 font-semibold">{recommendation.recommended_action}</p>
            <p className="text-sm text-slate-400 mt-2">{recommendation.reason}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {recommendation.alternative_actions.map(action => (
                <span key={action} className="text-xs bg-slate-800 border border-slate-700 rounded-full px-2 py-1 text-slate-300">
                  {action}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 rounded-lg border border-slate-700 p-4">
            <label className="block text-xs text-slate-400 mb-2" htmlFor="pa-comment">
              Comentario del PA
            </label>
            <textarea
              id="pa-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              className="w-full rounded-lg bg-slate-950 border border-slate-700 text-sm text-slate-200 p-2 focus:outline-none focus:border-cyan-600"
              placeholder="Motivo, proveedor preferido o instrucción al equipo"
            />
            {error && <p className="text-xs text-red-300 mt-2">{error}</p>}
            <div className="flex gap-2 mt-3">
              <button
                disabled={busy || recommendation.status !== 'pending'}
                onClick={() => decide('approve')}
                className="flex-1 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold disabled:opacity-40"
              >
                Aprobar
              </button>
              <button
                disabled={busy || recommendation.status !== 'pending'}
                onClick={() => decide('reject')}
                className="flex-1 px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm font-semibold disabled:opacity-40"
              >
                Rechazar
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 text-sm text-slate-400">
          Sin recomendación pendiente. Ejecuta el demo o simula stock bajo para que los agentes generen una decisión operativa.
        </div>
      )}
    </section>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3">
      <div className="text-xs text-slate-500 uppercase">{label}</div>
      <div className="text-lg font-bold text-slate-100 mt-1">{value}</div>
    </div>
  )
}

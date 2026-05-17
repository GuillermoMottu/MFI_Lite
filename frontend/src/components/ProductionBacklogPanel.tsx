import { useState } from 'react'
import { api } from '../api'

interface ProductionJob {
  job_id: string
  product: string
  sku_id: string
  line_id: string
  planned_units: number
  priority: number
  sequence: number
  status: string
  required_start: string
  estimated_duration_min: number
  material_risk_status: 'critical' | 'low_stock' | 'normal' | 'unknown'
  material_risk_score: number
  stockout_hours: number | null
  shortage_units: number
  estimated_impact_mxn: number
  suggested_action: string
}

interface BacklogSuggestion {
  strategy: string
  summary: {
    jobs_total: number
    jobs_impacted: number
    critical_jobs: number
  }
  suggested_sequence: Array<{
    job_id: string
    from_sequence: number
    to_sequence: number
    sku_id: string
    material_risk_status: string
    suggested_action: string
  }>
}

interface ProductionBacklogPanelProps {
  jobs: ProductionJob[]
  suggestion: BacklogSuggestion | null
  onChange: () => void
}

export default function ProductionBacklogPanel({ jobs, suggestion, onChange }: ProductionBacklogPanelProps) {
  const [comment, setComment] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const impacted = jobs.filter(job => job.material_risk_status === 'critical' || job.material_risk_status === 'low_stock')

  const applySuggestion = async () => {
    setBusy(true)
    setError(null)
    try {
      await api.resequenceBacklog(comment || undefined)
      setComment('')
      onChange()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo reprogramar backlog')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-300">Backlog de Produccion</h2>
          <p className="text-xs text-slate-500 mt-1">Jobs impactados por riesgo de material y secuencia sugerida</p>
        </div>
        <div className="grid grid-cols-3 gap-2 min-w-[260px]">
          <Metric label="Jobs" value={String(suggestion?.summary.jobs_total ?? jobs.length)} />
          <Metric label="Impactados" value={String(suggestion?.summary.jobs_impacted ?? impacted.length)} />
          <Metric label="Criticos" value={String(suggestion?.summary.critical_jobs ?? impacted.filter(j => j.material_risk_status === 'critical').length)} />
        </div>
      </div>

      {error && <p className="text-xs text-red-300 mb-3">{error}</p>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
        {jobs.map(job => {
          const suggested = suggestion?.suggested_sequence.find(item => item.job_id === job.job_id)
          return (
            <article key={job.job_id} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-bold text-slate-100">{job.job_id}</div>
                  <div className="text-xs text-slate-500 mt-1">{job.product} - {job.line_id}</div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full border ${riskStyle(job.material_risk_status)}`}>
                  {riskLabel(job.material_risk_status)}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 mt-4">
                <Metric label="Seq." value={`${job.sequence}${suggested && suggested.to_sequence !== job.sequence ? ` -> ${suggested.to_sequence}` : ''}`} />
                <Metric label="Prioridad" value={String(job.priority)} />
                <Metric label="Unidades" value={job.planned_units.toLocaleString('es-MX')} />
              </div>

              <div className="mt-4 text-xs text-slate-400">
                <div>SKU: <span className="text-slate-200">{job.sku_id}</span></div>
                <div>Estado: <span className="text-slate-200">{job.status}</span></div>
                <div>Stockout: <span className="text-slate-200">{job.stockout_hours === null ? 'n/a' : `${job.stockout_hours} h`}</span></div>
              </div>

              <div className="mt-3 bg-slate-950 border border-slate-800 rounded-lg p-3">
                <div className="text-[10px] text-slate-500 uppercase">Accion sugerida</div>
                <div className="text-xs text-slate-200 mt-1">{actionLabel(job.suggested_action)}</div>
              </div>
            </article>
          )
        })}
      </div>

      <div className="mt-4 bg-slate-900 border border-slate-700 rounded-lg p-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          <div className="lg:col-span-2">
            <label className="block text-xs text-slate-500 uppercase mb-1" htmlFor="backlog-comment">Comentario</label>
            <input
              id="backlog-comment"
              value={comment}
              onChange={event => setComment(event.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
              placeholder="Motivo de reprogramacion"
            />
          </div>
          <button
            disabled={busy || jobs.length === 0}
            onClick={applySuggestion}
            className="self-end px-3 py-2 rounded-lg bg-green-700 hover:bg-green-600 text-white text-sm font-semibold disabled:opacity-40"
          >
            Aplicar secuencia sugerida
          </button>
        </div>
      </div>
    </section>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg p-2">
      <div className="text-[10px] text-slate-500 uppercase">{label}</div>
      <div className="text-sm font-bold text-slate-100 mt-1">{value}</div>
    </div>
  )
}

function riskLabel(status: ProductionJob['material_risk_status']): string {
  if (status === 'critical') return 'Critico'
  if (status === 'low_stock') return 'Bajo stock'
  if (status === 'normal') return 'Normal'
  return 'Sin dato'
}

function riskStyle(status: ProductionJob['material_risk_status']): string {
  if (status === 'critical') return 'bg-red-950 text-red-200 border-red-700'
  if (status === 'low_stock') return 'bg-yellow-950 text-yellow-200 border-yellow-700'
  if (status === 'normal') return 'bg-green-950 text-green-200 border-green-700'
  return 'bg-slate-950 text-slate-300 border-slate-700'
}

function actionLabel(action: string): string {
  if (action === 'defer_or_expedite_material') return 'Diferir job o acelerar material antes de liberar produccion.'
  if (action === 'monitor_and_prepare_po') return 'Mantener programado, monitorear cobertura y preparar compra.'
  return 'Ejecutar segun plan.'
}

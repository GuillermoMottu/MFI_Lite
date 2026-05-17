import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'

interface AuditRecord {
  timestamp: string
  source: string
  entity_type: 'recommendation' | 'purchase_order' | 'event'
  entity_id: string
  action: string
  status: string
  sku_id?: string | null
  correlation_id?: string | null
  user?: string | null
  summary: string
}

interface AuditTrailPanelProps {
  defaultSkuId?: string
  defaultCorrelationId?: string | null
  refreshKey: number
}

type EntityFilter = '' | 'recommendation' | 'purchase_order' | 'event'

export default function AuditTrailPanel({ defaultSkuId = '', defaultCorrelationId, refreshKey }: AuditTrailPanelProps) {
  const [records, setRecords] = useState<AuditRecord[]>([])
  const [entityType, setEntityType] = useState<EntityFilter>('')
  const [skuId, setSkuId] = useState(defaultSkuId)
  const [correlationId, setCorrelationId] = useState(defaultCorrelationId ?? '')
  const [entityId, setEntityId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const params = useMemo(() => ({
    entity_type: entityType || undefined,
    entity_id: entityId || undefined,
    sku_id: skuId || undefined,
    correlation_id: correlationId || undefined,
    limit: 80,
  }), [entityType, entityId, skuId, correlationId])

  useEffect(() => {
    api.getAudit(params)
      .then((r: { audit: AuditRecord[] }) => {
        setRecords(r.audit ?? [])
        setError(null)
      })
      .catch(err => setError(err instanceof Error ? err.message : 'No se pudo cargar auditoria'))
  }, [params, refreshKey])

  const exportParams = {
    entity_type: entityType || undefined,
    entity_id: entityId || undefined,
    sku_id: skuId || undefined,
    correlation_id: correlationId || undefined,
  }

  const exportAudit = async (format: 'json' | 'csv') => {
    try {
      const blob = await api.exportAudit({ ...exportParams, format })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `audit.${format}`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo exportar auditoria')
    }
  }

  return (
    <section className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-300">Historial y Auditoria</h2>
          <p className="text-xs text-slate-500 mt-1">Decisiones, ordenes, recomendaciones y eventos IES trazables</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => exportAudit('json')} className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold">
            Export JSON
          </button>
          <button onClick={() => exportAudit('csv')} className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold">
            Export CSV
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-4">
        <label className="block">
          <span className="block text-xs text-slate-500 uppercase mb-1">Tipo</span>
          <select
            value={entityType}
            onChange={event => setEntityType(event.target.value as EntityFilter)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-2 text-sm text-slate-200"
          >
            <option value="">Todo</option>
            <option value="recommendation">Recomendaciones</option>
            <option value="purchase_order">Ordenes</option>
            <option value="event">Eventos IES</option>
          </select>
        </label>
        <Input label="SKU" value={skuId} onChange={setSkuId} placeholder="SKU-ACERO-M8" />
        <Input label="Entidad" value={entityId} onChange={setEntityId} placeholder="REC / PO / event_id" />
        <Input label="Correlation" value={correlationId} onChange={setCorrelationId} placeholder="correlation_id" />
      </div>

      {error && <p className="text-xs text-red-300 mb-3">{error}</p>}

      <div className="space-y-2 max-h-[460px] overflow-auto pr-1">
        {records.length === 0 ? (
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-sm text-slate-400">
            Sin registros para los filtros seleccionados.
          </div>
        ) : records.map(record => (
          <article key={`${record.source}-${record.entity_id}-${record.timestamp}-${record.action}`} className="bg-slate-900 border border-slate-700 rounded-lg p-3">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`text-xs px-2 py-1 rounded-full border ${typeStyle(record.entity_type)}`}>{labelType(record.entity_type)}</span>
                  <span className="text-xs text-slate-400 font-mono">{record.entity_id}</span>
                  <span className="text-xs text-slate-500">{record.action}</span>
                </div>
                <p className="text-sm text-slate-200 mt-2">{record.summary}</p>
              </div>
              <div className="text-left md:text-right text-xs text-slate-500">
                <div>{record.timestamp}</div>
                <div>{record.sku_id ?? 'sin SKU'}</div>
              </div>
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
              <span>source: {record.source}</span>
              <span>status: {record.status}</span>
              {record.user && <span>user: {record.user}</span>}
              {record.correlation_id && <span className="font-mono">corr: {record.correlation_id.slice(0, 8)}</span>}
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function Input({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (value: string) => void; placeholder: string }) {
  return (
    <label className="block">
      <span className="block text-xs text-slate-500 uppercase mb-1">{label}</span>
      <input
        value={value}
        onChange={event => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-2 text-sm text-slate-200"
      />
    </label>
  )
}

function labelType(type: AuditRecord['entity_type']): string {
  if (type === 'purchase_order') return 'PO'
  if (type === 'recommendation') return 'REC'
  return 'IES'
}

function typeStyle(type: AuditRecord['entity_type']): string {
  if (type === 'purchase_order') return 'bg-green-950 text-green-200 border-green-700'
  if (type === 'recommendation') return 'bg-cyan-950 text-cyan-200 border-cyan-700'
  return 'bg-slate-950 text-slate-300 border-slate-700'
}

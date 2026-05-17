import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'

interface Supplier {
  supplier_id: string
  name: string
  sku_ids: string[]
  lead_time_days: number
  unit_cost_mxn: number
  reliability_score: number
  minimum_order_quantity: number
  selection_score?: number
  selection_reason?: string
}

interface SupplierCatalogPanelProps {
  suppliers: Supplier[]
  skuId?: string
  onChange: () => void
}

type Strategy = 'urgency' | 'cost'

const emptyDraft = {
  name: '',
  sku_ids: 'SKU-ACERO-M8',
  lead_time_days: '2',
  unit_cost_mxn: '35',
  reliability_score: '0.9',
  minimum_order_quantity: '500',
}

export default function SupplierCatalogPanel({ suppliers, skuId = 'SKU-ACERO-M8', onChange }: SupplierCatalogPanelProps) {
  const [strategy, setStrategy] = useState<Strategy>('urgency')
  const [recommended, setRecommended] = useState<Supplier | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [draft, setDraft] = useState(emptyDraft)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const maxCost = useMemo(() => Math.max(...suppliers.map(s => s.unit_cost_mxn), 1), [suppliers])
  const maxLead = useMemo(() => Math.max(...suppliers.map(s => s.lead_time_days), 1), [suppliers])

  useEffect(() => {
    api.getSupplierRecommendation(skuId, strategy)
      .then((r: { supplier: Supplier }) => setRecommended(r.supplier))
      .catch(() => setRecommended(null))
  }, [skuId, strategy, suppliers])

  const startCreate = () => {
    setEditingId('new')
    setDraft(emptyDraft)
    setError(null)
  }

  const startEdit = (supplier: Supplier) => {
    setEditingId(supplier.supplier_id)
    setDraft({
      name: supplier.name,
      sku_ids: supplier.sku_ids.join(', '),
      lead_time_days: String(supplier.lead_time_days),
      unit_cost_mxn: String(supplier.unit_cost_mxn),
      reliability_score: String(supplier.reliability_score),
      minimum_order_quantity: String(supplier.minimum_order_quantity),
    })
    setError(null)
  }

  const cancel = () => {
    setEditingId(null)
    setDraft(emptyDraft)
    setError(null)
  }

  const save = async () => {
    const payload = {
      name: draft.name,
      sku_ids: draft.sku_ids.split(',').map(sku => sku.trim()).filter(Boolean),
      lead_time_days: Number(draft.lead_time_days),
      unit_cost_mxn: Number(draft.unit_cost_mxn),
      reliability_score: Number(draft.reliability_score),
      minimum_order_quantity: Number(draft.minimum_order_quantity),
    }
    setBusy(true)
    setError(null)
    try {
      if (editingId === 'new') {
        await api.createSupplier(payload)
      } else if (editingId) {
        await api.updateSupplier(editingId, payload)
      }
      cancel()
      onChange()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar proveedor')
    } finally {
      setBusy(false)
    }
  }

  const remove = async (supplierId: string) => {
    setBusy(true)
    setError(null)
    try {
      await api.deleteSupplier(supplierId)
      onChange()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo eliminar proveedor')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-300">Catalogo de Proveedores</h2>
          <p className="text-xs text-slate-500 mt-1">Comparacion para {skuId}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="flex rounded-lg border border-slate-700 overflow-hidden">
            <button
              onClick={() => setStrategy('urgency')}
              className={`px-3 py-2 text-xs font-semibold ${strategy === 'urgency' ? 'bg-cyan-600 text-white' : 'bg-slate-900 text-slate-300'}`}
            >
              Urgencia
            </button>
            <button
              onClick={() => setStrategy('cost')}
              className={`px-3 py-2 text-xs font-semibold ${strategy === 'cost' ? 'bg-cyan-600 text-white' : 'bg-slate-900 text-slate-300'}`}
            >
              Costo
            </button>
          </div>
          <button
            onClick={startCreate}
            className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold"
          >
            Nuevo proveedor
          </button>
        </div>
      </div>

      {recommended && (
        <div className="mb-4 bg-cyan-950 border border-cyan-800 rounded-lg p-3">
          <div className="text-xs text-cyan-300 uppercase">Seleccion sugerida</div>
          <div className="mt-1 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <div className="text-sm font-bold text-slate-100">{recommended.name}</div>
            <div className="text-xs text-cyan-100">{recommended.selection_reason}</div>
          </div>
        </div>
      )}

      {error && <p className="text-xs text-red-300 mb-3">{error}</p>}

      {editingId && (
        <div className="mb-4 bg-slate-900 border border-slate-700 rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
            <Input label="Nombre" value={draft.name} onChange={value => setDraft({ ...draft, name: value })} />
            <Input label="SKUs" value={draft.sku_ids} onChange={value => setDraft({ ...draft, sku_ids: value })} />
            <Input label="Lead time" type="number" value={draft.lead_time_days} onChange={value => setDraft({ ...draft, lead_time_days: value })} />
            <Input label="Costo unit." type="number" value={draft.unit_cost_mxn} onChange={value => setDraft({ ...draft, unit_cost_mxn: value })} />
            <Input label="Confiabilidad" type="number" value={draft.reliability_score} onChange={value => setDraft({ ...draft, reliability_score: value })} />
            <Input label="MOQ" type="number" value={draft.minimum_order_quantity} onChange={value => setDraft({ ...draft, minimum_order_quantity: value })} />
          </div>
          <div className="flex gap-2 mt-3">
            <button disabled={busy} onClick={save} className="px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold disabled:opacity-40">
              Guardar
            </button>
            <button disabled={busy} onClick={cancel} className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm font-semibold disabled:opacity-40">
              Cancelar
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {suppliers.map(supplier => {
          const isRecommended = supplier.supplier_id === recommended?.supplier_id
          return (
            <article key={supplier.supplier_id} className={`bg-slate-900 border rounded-lg p-4 ${isRecommended ? 'border-cyan-600' : 'border-slate-700'}`}>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-sm font-bold text-slate-100">{supplier.name}</div>
                  <div className="text-xs text-slate-500 mt-1">{supplier.supplier_id}</div>
                </div>
                {isRecommended && <span className="text-xs px-2 py-1 rounded-full bg-cyan-950 text-cyan-200 border border-cyan-700">Sugerido</span>}
              </div>

              <div className="space-y-3 mt-4">
                <Bar label="Costo" value={`$${supplier.unit_cost_mxn.toFixed(2)}`} pct={(supplier.unit_cost_mxn / maxCost) * 100} tone="cyan" />
                <Bar label="Lead time" value={`${supplier.lead_time_days} dias`} pct={(supplier.lead_time_days / maxLead) * 100} tone="amber" />
                <Bar label="Confiabilidad" value={`${Math.round(supplier.reliability_score * 100)}%`} pct={supplier.reliability_score * 100} tone="green" />
              </div>

              <div className="mt-4 flex items-center justify-between gap-2">
                <span className="text-xs text-slate-500">MOQ {supplier.minimum_order_quantity} uds</span>
                <div className="flex gap-2">
                  <button disabled={busy} onClick={() => startEdit(supplier)} className="px-2 py-1 rounded-md bg-slate-700 hover:bg-slate-600 text-white text-xs disabled:opacity-40">
                    Editar
                  </button>
                  <button disabled={busy || suppliers.length <= 1} onClick={() => remove(supplier.supplier_id)} className="px-2 py-1 rounded-md bg-red-950 hover:bg-red-900 text-red-100 text-xs disabled:opacity-40">
                    Baja
                  </button>
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}

function Input({ label, value, onChange, type = 'text' }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="block text-xs text-slate-500 uppercase mb-1">{label}</span>
      <input
        type={type}
        value={value}
        onChange={event => onChange(event.target.value)}
        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-2 text-sm text-slate-200"
      />
    </label>
  )
}

function Bar({ label, value, pct, tone }: { label: string; value: string; pct: number; tone: 'cyan' | 'amber' | 'green' }) {
  const color = tone === 'green' ? 'bg-green-500' : tone === 'amber' ? 'bg-amber-500' : 'bg-cyan-500'
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-500 uppercase">{label}</span>
        <span className="text-slate-300">{value}</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${Math.max(6, Math.min(100, pct))}%` }} />
      </div>
    </div>
  )
}

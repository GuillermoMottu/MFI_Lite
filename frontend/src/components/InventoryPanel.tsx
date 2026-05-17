import { useState } from 'react'
import { api } from '../api'

interface Material {
  sku_id: string
  name: string
  line_id: string
  warehouse: string
  current_stock_units: number
  reorder_point_units: number
  daily_demand_units: number
  unit_cost_mxn: number
  criticality: string
  stockout_hours: number | null
  shortage_units: number
  risk_score: number
  risk_status: 'critical' | 'low_stock' | 'normal'
  estimated_impact_mxn: number
}

interface InventoryPanelProps {
  materials: Material[]
  onChange: () => void
}

type Filter = 'all' | 'critical' | 'low_stock' | 'normal'

const filterLabels: Record<Filter, string> = {
  all: 'Todos',
  critical: 'Critico',
  low_stock: 'Bajo stock',
  normal: 'Normal',
}

export default function InventoryPanel({ materials, onChange }: InventoryPanelProps) {
  const [filter, setFilter] = useState<Filter>('all')
  const [editing, setEditing] = useState<Record<string, string>>({})
  const [busySku, setBusySku] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const visible = filter === 'all' ? materials : materials.filter(material => material.risk_status === filter)

  const saveStock = async (material: Material) => {
    const value = editing[material.sku_id]
    if (value === undefined) return
    setBusySku(material.sku_id)
    setError(null)
    try {
      await api.updateMaterial(material.sku_id, { current_stock_units: Number(value) })
      setEditing(({ [material.sku_id]: _removed, ...rest }) => rest)
      onChange()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo actualizar inventario')
    } finally {
      setBusySku(null)
    }
  }

  const createRecommendation = async (material: Material) => {
    setBusySku(material.sku_id)
    setError(null)
    try {
      await api.createMaterialRecommendation(material.sku_id)
      onChange()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo generar recomendacion')
    } finally {
      setBusySku(null)
    }
  }

  return (
    <section className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-300">Inventario Multi-SKU</h2>
          <p className="text-xs text-slate-500 mt-1">Riesgo, stockout e impacto estimado por material</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(filterLabels).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setFilter(key as Filter)}
              className={`px-3 py-2 rounded-lg border text-xs font-semibold ${
                filter === key
                  ? 'bg-cyan-600 border-cyan-500 text-white'
                  : 'bg-slate-900 border-slate-700 text-slate-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-xs text-red-300 mb-3">{error}</p>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
        {visible.map(material => {
          const stockPct = Math.min(100, (material.current_stock_units / Math.max(material.reorder_point_units, 1)) * 100)
          const editingValue = editing[material.sku_id]
          return (
            <article key={material.sku_id} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-bold text-slate-100">{material.sku_id}</div>
                  <div className="text-xs text-slate-500 mt-1">{material.name} - {material.line_id}</div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full border ${statusStyle(material.risk_status)}`}>
                  {statusLabel(material.risk_status)}
                </span>
              </div>

              <div className="mt-4">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-500 uppercase">Stock vs reorden</span>
                  <span className="text-slate-300">{material.current_stock_units} / {material.reorder_point_units}</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className={material.risk_status === 'critical' ? 'h-full bg-red-500' : 'h-full bg-cyan-500'} style={{ width: `${Math.max(4, stockPct)}%` }} />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 mt-4">
                <Metric label="Stockout" value={material.stockout_hours === null ? 'n/a' : `${material.stockout_hours} h`} />
                <Metric label="Riesgo" value={`${material.risk_score}%`} />
                <Metric label="Impacto" value={`$${Math.round(material.estimated_impact_mxn).toLocaleString('es-MX')}`} />
              </div>

              <div className="mt-4 flex flex-col sm:flex-row gap-2">
                {editingValue === undefined ? (
                  <button
                    disabled={busySku === material.sku_id}
                    onClick={() => setEditing({ ...editing, [material.sku_id]: String(material.current_stock_units) })}
                    className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold disabled:opacity-40"
                  >
                    Editar stock
                  </button>
                ) : (
                  <>
                    <input
                      type="number"
                      min="0"
                      value={editingValue}
                      onChange={event => setEditing({ ...editing, [material.sku_id]: event.target.value })}
                      className="w-full sm:w-28 bg-slate-950 border border-slate-700 rounded-lg px-2 py-2 text-sm text-slate-200"
                    />
                    <button
                      disabled={busySku === material.sku_id}
                      onClick={() => saveStock(material)}
                      className="px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold disabled:opacity-40"
                    >
                      Guardar
                    </button>
                  </>
                )}
                <button
                  disabled={material.risk_status === 'normal' || busySku === material.sku_id}
                  onClick={() => createRecommendation(material)}
                  className="px-3 py-2 rounded-lg bg-green-700 hover:bg-green-600 text-white text-xs font-semibold disabled:opacity-40"
                >
                  Recomendar compra
                </button>
              </div>
            </article>
          )
        })}
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

function statusLabel(status: Material['risk_status']): string {
  if (status === 'critical') return 'Critico'
  if (status === 'low_stock') return 'Bajo stock'
  return 'Normal'
}

function statusStyle(status: Material['risk_status']): string {
  if (status === 'critical') return 'bg-red-950 text-red-200 border-red-700'
  if (status === 'low_stock') return 'bg-yellow-950 text-yellow-200 border-yellow-700'
  return 'bg-green-950 text-green-200 border-green-700'
}

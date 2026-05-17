import { useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../api'

interface PurchaseOrder {
  po_id: string
  sku_id: string
  supplier_id: string
  supplier_name: string
  supplier_lead_time_days: number
  quantity_units: number
  unit_cost_mxn: number
  total_cost_mxn: number
  required_date: string
  estimated_arrival_date: string
  status: string
  source_recommendation_id: string
  correlation_id: string
  pa_comment?: string | null
}

interface Supplier {
  supplier_id: string
  name: string
  lead_time_days: number
  unit_cost_mxn: number
  reliability_score: number
  minimum_order_quantity: number
}

interface PurchaseOrdersPanelProps {
  orders: PurchaseOrder[]
  suppliers: Supplier[]
  onChange: () => void
}

export default function PurchaseOrdersPanel({ orders, suppliers, onChange }: PurchaseOrdersPanelProps) {
  const [editing, setEditing] = useState<Record<string, { supplier_id: string; quantity_units: string; required_date: string; comment: string }>>({})
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  const startEdit = (order: PurchaseOrder) => {
    setEditing({
      ...editing,
      [order.po_id]: {
        supplier_id: order.supplier_id,
        quantity_units: String(order.quantity_units),
        required_date: order.required_date,
        comment: order.pa_comment ?? '',
      },
    })
  }

  const save = async (order: PurchaseOrder) => {
    const draft = editing[order.po_id]
    if (!draft) return
    setError(null)
    setBusyId(order.po_id)
    try {
      await api.updatePurchaseOrder(order.po_id, {
        supplier_id: draft.supplier_id,
        quantity_units: Number(draft.quantity_units),
        required_date: draft.required_date,
        comment: draft.comment,
      })
      setEditing(({ [order.po_id]: _removed, ...rest }) => rest)
      onChange()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo actualizar la orden')
    } finally {
      setBusyId(null)
    }
  }

  const approve = async (order: PurchaseOrder) => {
    setError(null)
    setBusyId(order.po_id)
    try {
      await api.approvePurchaseOrder(order.po_id, order.pa_comment ?? undefined)
      onChange()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo aprobar la orden')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <section className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-300">Ordenes de Compra</h2>
          <p className="text-xs text-slate-500 mt-1">Borradores generados desde recomendaciones aprobadas</p>
        </div>
        <span className="text-xs bg-slate-900 border border-slate-700 rounded-full px-2 py-1 text-slate-400">
          {orders.length} ordenes
        </span>
      </div>

      {error && <p className="text-xs text-red-300 mb-3">{error}</p>}

      {orders.length === 0 ? (
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 text-sm text-slate-400">
          Aun no hay ordenes operativas. Aprueba una recomendacion para crear una PO draft.
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map(order => {
            const draft = editing[order.po_id]
            const editable = order.status === 'draft' || order.status === 'pending_approval'
            return (
              <article key={order.po_id} className="bg-slate-900 rounded-lg border border-slate-700 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-100">{order.po_id}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${order.status === 'approved' ? 'bg-green-950 text-green-200 border-green-700' : 'bg-yellow-950 text-yellow-200 border-yellow-700'}`}>
                        {order.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {order.sku_id} · ETA {order.estimated_arrival_date} · {order.correlation_id.slice(0, 8)}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-slate-100">${order.total_cost_mxn.toLocaleString('es-MX')} MXN</div>
                    <div className="text-xs text-slate-500">{order.quantity_units} uds</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-4">
                  <Field label="Proveedor">
                    {draft ? (
                      <select
                        value={draft.supplier_id}
                        onChange={(e) => setEditing({ ...editing, [order.po_id]: { ...draft, supplier_id: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-2 text-sm text-slate-200"
                      >
                        {suppliers.map(supplier => (
                          <option key={supplier.supplier_id} value={supplier.supplier_id}>
                            {supplier.name} · {supplier.lead_time_days}d · ${supplier.unit_cost_mxn}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-sm text-slate-200">{order.supplier_name}</span>
                    )}
                  </Field>

                  <Field label="Cantidad">
                    {draft ? (
                      <input
                        type="number"
                        min="1"
                        value={draft.quantity_units}
                        onChange={(e) => setEditing({ ...editing, [order.po_id]: { ...draft, quantity_units: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-2 text-sm text-slate-200"
                      />
                    ) : (
                      <span className="text-sm text-slate-200">{order.quantity_units} uds</span>
                    )}
                  </Field>

                  <Field label="Fecha requerida">
                    {draft ? (
                      <input
                        type="date"
                        value={draft.required_date}
                        onChange={(e) => setEditing({ ...editing, [order.po_id]: { ...draft, required_date: e.target.value } })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-2 text-sm text-slate-200"
                      />
                    ) : (
                      <span className="text-sm text-slate-200">{order.required_date}</span>
                    )}
                  </Field>

                  <Field label="Lead time">
                    <span className="text-sm text-slate-200">{order.supplier_lead_time_days} dias</span>
                  </Field>
                </div>

                {draft && (
                  <textarea
                    value={draft.comment}
                    onChange={(e) => setEditing({ ...editing, [order.po_id]: { ...draft, comment: e.target.value } })}
                    rows={2}
                    placeholder="Comentario para compras o aprobacion"
                    className="mt-3 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                  />
                )}

                <div className="flex gap-2 mt-4">
                  {draft ? (
                    <>
                      <button
                        disabled={busyId === order.po_id}
                        onClick={() => save(order)}
                        className="px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold disabled:opacity-40"
                      >
                        Guardar cambios
                      </button>
                      <button
                        disabled={busyId === order.po_id}
                        onClick={() => setEditing(({ [order.po_id]: _removed, ...rest }) => rest)}
                        className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm font-semibold disabled:opacity-40"
                      >
                        Cancelar
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        disabled={!editable || busyId === order.po_id}
                        onClick={() => startEdit(order)}
                        className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm font-semibold disabled:opacity-40"
                      >
                        Editar
                      </button>
                      <button
                        disabled={!editable || busyId === order.po_id}
                        onClick={() => approve(order)}
                        className="px-3 py-2 rounded-lg bg-green-700 hover:bg-green-600 text-white text-sm font-semibold disabled:opacity-40"
                      >
                        Aprobar orden
                      </button>
                    </>
                  )}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <div className="text-xs text-slate-500 uppercase mb-1">{label}</div>
      {children}
    </div>
  )
}

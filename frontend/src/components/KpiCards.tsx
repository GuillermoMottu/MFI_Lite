interface Status {
  current_stock_units?: number
  reorder_point_units?: number
  daily_demand_units?: number
  oee_pct?: number
  risk_score_pct?: number
  buffer_pending?: number
  loss_prevented_mxn?: number
  idle_minutes_prevented?: number
  adjusted_plan_units?: number
}

interface KpiCardsProps { status: Status }

function KpiCard({
  label, value, unit, color, sub, formula,
}: {
  label: string
  value: string | number
  unit?: string
  color: string
  sub?: string
  formula?: string
}) {
  return (
    <div className={`bg-slate-800 rounded-xl p-4 border ${color} flex flex-col gap-1`}>
      <div className="flex items-center gap-1">
        <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
        {formula && (
          <span
            title={formula}
            className="text-slate-500 hover:text-slate-300 cursor-help text-xs ml-auto transition-colors"
          >
            ℹ
          </span>
        )}
      </div>
      <span className="text-2xl font-bold text-white">
        {value}{unit && <span className="text-base font-normal text-slate-400 ml-1">{unit}</span>}
      </span>
      {sub && <span className="text-xs text-slate-500">{sub}</span>}
    </div>
  )
}

export default function KpiCards({ status }: KpiCardsProps) {
  const stock = status.current_stock_units ?? 0
  const reorder = status.reorder_point_units ?? 0
  const dailyDemand = status.daily_demand_units ?? 0
  const riskPct = status.risk_score_pct ?? 0

  const riskColor = riskPct >= 75 ? 'border-red-700' : riskPct >= 40 ? 'border-yellow-700' : 'border-slate-700'
  const stockColor = stock < reorder && reorder > 0 ? 'border-red-700' : 'border-slate-700'
  const stockoutH = dailyDemand > 0 ? (stock / (dailyDemand / 24)).toFixed(1) : '—'

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
      <KpiCard
        label="Stock Actual" value={stock} unit="uds" color={stockColor}
        sub={`Reorden: ${reorder} uds`}
        formula={`Stockout estimado: ${stockoutH}h\nStockout = stock ÷ (demanda_diaria ÷ 24)`}
      />
      <KpiCard
        label="Demanda Diaria" value={dailyDemand.toFixed(0)} unit="uds/día"
        color="border-slate-700"
        formula="Promedio móvil de consumo diario del SKU-ACERO-M8. Base para reorder_point = demanda × lead_time + safety_stock."
      />
      <KpiCard
        label="OEE" value={status.oee_pct?.toFixed(1) ?? 78} unit="%"
        color="border-slate-700"
        formula="OEE = Disponibilidad × Rendimiento × Calidad&#10;= 0.92 × 0.88 × 0.96 = ~77.8%&#10;Impacto por idle: ΔOEE × factor_línea"
      />
      <KpiCard
        label="Riesgo AI/ML" value={riskPct.toFixed(1)} unit="%"
        color={riskColor} sub="score acumulado"
        formula="Isolation Forest heurístico (Edge)&#10;Score = 0.40×stockout + 0.25×OEE_inv + 0.15×consumo + 0.15×idle + 0.05×cycle&#10;Umbral crítico: 72% (0.72)"
      />
      <KpiCard
        label="Buffer Edge" value={status.buffer_pending ?? 0} unit="eventos"
        color={(status.buffer_pending ?? 0) > 0 ? 'border-amber-700' : 'border-slate-700'}
        formula="Eventos IES almacenados en edge_buffer.db (SQLite) cuando Cloud offline.&#10;Replay FIFO con deduplicación por event_id."
      />
      <KpiCard
        label="Pérdida Evitada" value={`$${((status.loss_prevented_mxn ?? 0) / 1000).toFixed(1)}k`}
        unit="MXN" color="border-green-800"
        formula="Pérdida evitada = ΔOEE × factor_línea × $480/hora&#10;Factor LINE-1: 3.5 (turnos × capacidad instalada)&#10;ΔOEE = diferencia entre OEE sin vs con intervención"
      />
      <KpiCard
        label="Idle Prevenido" value={status.idle_minutes_prevented ?? 0} unit="min"
        color="border-slate-700"
        formula="Minutos de idle evitados en LINE-1.&#10;Idle = tiempo sin material disponible en CONVEYOR-1.&#10;Idle_min = (plan_original - plan_ajustado) ÷ 12 piezas/min"
      />
      <KpiCard
        label="Plan Ajustado" value={status.adjusted_plan_units ?? 1200} unit="uds"
        color="border-slate-700" sub="Turno A"
        formula="Unidades planificadas para Turno A ajustadas por stock disponible.&#10;Plan_ajustado = min(plan_original, stock × factor_seguridad)"
      />
    </div>
  )
}

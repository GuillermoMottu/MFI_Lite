interface StockPoint { timestamp: string; stock: number; reorder_point: number }

interface StockChartProps {
  currentStock: number
  reorderPoint: number
  dailyDemand: number
  history?: StockPoint[]
}

export default function StockChart({ currentStock, reorderPoint, dailyDemand, history = [] }: StockChartProps) {
  const allStocks = [currentStock, reorderPoint, dailyDemand * 5, 100, ...history.map(h => h.stock)]
  const max = Math.max(...allStocks, 1)
  const stockPct = Math.min(100, (currentStock / max) * 100)
  const reorderPct = Math.min(100, (reorderPoint / max) * 100)
  const stockoutH = dailyDemand > 0 ? (currentStock / (dailyDemand / 24)).toFixed(1) : '—'
  const isRisk = reorderPoint > 0 && currentStock < reorderPoint

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">
        Stock vs Punto de Reorden — SKU-ACERO-M8
      </h3>

      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>Stock Actual</span>
            <span className={isRisk ? 'text-red-400 font-bold' : 'text-green-400 font-bold'}>
              {currentStock} uds
            </span>
          </div>
          <div className="h-6 bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${isRisk ? 'bg-red-500' : 'bg-green-500'}`}
              style={{ width: `${stockPct}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>Punto de Reorden</span>
            <span className="text-yellow-400 font-bold">{reorderPoint} uds</span>
          </div>
          <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-yellow-500 rounded-full transition-all duration-700"
              style={{ width: `${reorderPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Historial de puntos */}
      {history.length > 0 && (
        <div className="mt-4">
          <div className="text-xs text-slate-500 mb-2">Evolución durante el demo</div>
          <div className="relative h-16 flex items-end gap-1">
            {/* Línea de reorden */}
            <div
              className="absolute inset-x-0 border-t border-dashed border-yellow-600 opacity-60"
              style={{ bottom: `${Math.min(100, (reorderPoint / max) * 100)}%` }}
            />
            {history.map((point, i) => {
              const pct = Math.min(100, (point.stock / max) * 100)
              const atRisk = point.reorder_point > 0 && point.stock < point.reorder_point
              return (
                <div
                  key={i}
                  title={`${point.timestamp.slice(11, 19)}: ${point.stock} uds`}
                  className={`flex-1 rounded-sm transition-all duration-500 min-w-[6px]
                    ${atRisk ? 'bg-red-500' : 'bg-green-500'}`}
                  style={{ height: `${pct}%` }}
                />
              )
            })}
            {/* Punto actual */}
            <div
              title={`Ahora: ${currentStock} uds`}
              className={`flex-1 rounded-sm min-w-[6px] ring-1 ring-white/50
                ${isRisk ? 'bg-red-400' : 'bg-green-400'}`}
              style={{ height: `${stockPct}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-600 mt-1">
            <span>inicio</span>
            <span className="text-yellow-600">— reorden</span>
            <span>ahora</span>
          </div>
        </div>
      )}

      <div className="mt-3 flex gap-4 text-xs text-slate-400">
        <span>Stockout estimado: <span className={`font-bold ${parseFloat(stockoutH) < 24 ? 'text-red-400' : 'text-slate-300'}`}>{stockoutH} h</span></span>
        {isRisk && (
          <span className="text-red-400 font-semibold animate-pulse">⚠ RIESGO CRÍTICO</span>
        )}
      </div>
    </div>
  )
}

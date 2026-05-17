const FLOW_STEPS = [
  { id: 'material_demand_forecasted', label: 'ERP: Pronosticar Demanda', agent: 'ERP', color: 'cyan' },
  { id: 'stock_risk_detected', label: 'ERP: Detectar Riesgo Stock', agent: 'ERP', color: 'cyan' },
  { id: 'production_plan_adjusted', label: 'Prod: Ajustar Plan', agent: 'PROD', color: 'blue' },
  { id: 'material_related_idle_risk_detected', label: 'Edge: Idle Risk', agent: 'EDGE', color: 'purple' },
  { id: 'material_lifecycle_risk_detected', label: 'AI/ML: Desviación', agent: 'AI/ML', color: 'rose' },
  { id: 'material_bottleneck_identified', label: 'AI/ML: Bottleneck 🔥', agent: 'AI/ML', color: 'red' },
  { id: 'production_flow_optimized', label: 'Prod: Optimizar Flujo', agent: 'PROD', color: 'blue' },
  { id: 'urgent_purchase_order_created', label: 'ERP: Orden Urgente', agent: 'ERP', color: 'cyan' },
  { id: 'operational_recommendation_generated', label: 'AI/ML: Recomendación', agent: 'AI/ML', color: 'rose' },
]

const AGENT_COLORS: Record<string, string> = {
  cyan: 'border-cyan-600 bg-cyan-950 text-cyan-300',
  blue: 'border-blue-600 bg-blue-950 text-blue-300',
  purple: 'border-purple-600 bg-purple-950 text-purple-300',
  rose: 'border-rose-600 bg-rose-950 text-rose-300',
  red: 'border-red-500 bg-red-950 text-red-300 ring-2 ring-red-500',
}

interface FlowDiagramProps {
  completedEventTypes: Set<string>
  activeStep: number  // 1-9, 0 = sin paso activo
}

export default function FlowDiagram({ completedEventTypes, activeStep }: FlowDiagramProps) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-300">
          Flujo Cross-Agent
          <span className="ml-2 text-xs text-slate-500 font-normal">
            ERP → Producción → AI/ML → Producción → ERP → AI/ML
          </span>
        </h3>
        {activeStep > 0 && (
          <span className="text-xs text-blue-300 bg-blue-950 border border-blue-700 px-2 py-0.5 rounded-full animate-pulse font-mono">
            Paso {activeStep} / {FLOW_STEPS.length} — {FLOW_STEPS[activeStep - 1]?.agent}
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {FLOW_STEPS.map((step, i) => {
          const done = completedEventTypes.has(step.id)
          const isActive = activeStep === i + 1
          return (
            <div key={step.id} className="flex items-center gap-1">
              <div className={`px-3 py-2 rounded-lg border text-xs font-mono transition-all duration-500
                ${isActive
                  ? 'border-blue-400 bg-blue-900 text-blue-200 ring-2 ring-blue-400 animate-pulse'
                  : done
                  ? AGENT_COLORS[step.color]
                  : 'border-slate-700 bg-slate-900 text-slate-600'}`}>
                <div className="flex items-center gap-1.5">
                  {isActive
                    ? <span className="w-2 h-2 rounded-full bg-blue-400 inline-block animate-ping" />
                    : done
                    ? <span className="text-green-400">✓</span>
                    : <span className="w-3 h-3 rounded-full border border-slate-600 inline-block" />}
                  <span>{step.label}</span>
                </div>
              </div>
              {i < FLOW_STEPS.length - 1 && (
                <span className={`text-slate-600 text-xs ${done || isActive ? 'text-slate-400' : ''}`}>→</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

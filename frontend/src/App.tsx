import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import KpiCards from './components/KpiCards'
import StockChart from './components/StockChart'
import Timeline from './components/Timeline'
import JsonPanel from './components/JsonPanel'
import FlowDiagram from './components/FlowDiagram'
import ActionButtons from './components/ActionButtons'
import EdgeInferencePanel from './components/EdgeInferencePanel'
import PAConsole from './components/PAConsole'
import PurchaseOrdersPanel from './components/PurchaseOrdersPanel'
import SupplierCatalogPanel from './components/SupplierCatalogPanel'
import InventoryPanel from './components/InventoryPanel'
import ProductionBacklogPanel from './components/ProductionBacklogPanel'
import AuditTrailPanel from './components/AuditTrailPanel'
import ProtectedRoute from './components/ProtectedRoute'
import { useEventSource } from './hooks/useEventSource'
import { api } from './api'
import { useAuth } from './AuthContext'

interface IESEvent {
  event_id: string
  timestamp: string
  platform_version: string
  module: { id: string; version: string }
  asset: { asset_id: string; plant_id: string; line_id: string; location?: string }
  event: { type: string; category: string; severity: string }
  data: Record<string, unknown>
  metadata: Record<string, unknown>
}

interface DemoStatus {
  demo_running?: boolean
  current_demo_step?: number
  cloud_connected?: boolean
  buffer_pending?: number
  events_replayed?: number
  last_replay_at?: string | null
  current_stock_units?: number
  daily_demand_units?: number
  reorder_point_units?: number
  oee_pct?: number
  risk_score_pct?: number
  loss_prevented_mxn?: number
  adjusted_plan_units?: number
  idle_minutes_prevented?: number
  purchase_orders?: string[]
  last_bottleneck?: string | null
  last_correlation_id?: string | null
}

interface StockPoint { timestamp: string; stock: number; reorder_point: number }

interface InferenceStatus {
  signals?: Record<string, number | boolean>
  risk_score?: number
  threshold?: number
  is_critical?: boolean
  severity?: string
  model?: string
  inference_ms?: number
  timestamp?: string
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
  sku_ids: string[]
  lead_time_days: number
  unit_cost_mxn: number
  reliability_score: number
  minimum_order_quantity: number
}

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

type AppView = 'pa' | 'technical'

function viewFromPath(pathname: string): AppView {
  return pathname.startsWith('/technical') ? 'technical' : 'pa'
}

export default function App() {
  const { user, logout } = useAuth()
  const [events, setEvents] = useState<IESEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<IESEvent | null>(null)
  const [status, setStatus] = useState<DemoStatus>({})
  const [completedTypes, setCompletedTypes] = useState<Set<string>>(new Set())
  const [activeStep, setActiveStep] = useState<number>(0)
  const [stockHistory, setStockHistory] = useState<StockPoint[]>([])
  const [inferenceData, setInferenceData] = useState<InferenceStatus | null>(null)
  const [activeRecommendation, setActiveRecommendation] = useState<Recommendation | null>(null)
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [materials, setMaterials] = useState<Material[]>([])
  const [productionJobs, setProductionJobs] = useState<ProductionJob[]>([])
  const [backlogSuggestion, setBacklogSuggestion] = useState<BacklogSuggestion | null>(null)
  const [auditRefreshKey, setAuditRefreshKey] = useState(0)
  const [view, setView] = useState<AppView>(() => viewFromPath(window.location.pathname))

  const navigate = useCallback((nextView: AppView) => {
    const nextPath = nextView === 'pa' ? '/pa' : '/technical'
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, '', nextPath)
    }
    setView(nextView)
  }, [])

  useEffect(() => {
    if (window.location.pathname === '/') {
      window.history.replaceState({}, '', '/pa')
    }
    const onPopState = () => setView(viewFromPath(window.location.pathname))
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    if (!user) return
    if (user.role === 'supervisor') {
      window.history.replaceState({}, '', '/technical')
      setView('technical')
    }
    if ((user.role === 'pa' || user.role === 'admin') && window.location.pathname === '/') {
      window.history.replaceState({}, '', '/pa')
      setView('pa')
    }
  }, [user])

  const refreshStatus = useCallback(() => {
    api.getDemoStatus().then(setStatus).catch(console.error)
  }, [])

  const refreshStockHistory = useCallback(() => {
    api.getStockHistory().then((r: { history: StockPoint[] }) => {
      if (r.history) setStockHistory(r.history)
    }).catch(console.error)
  }, [])

  const refreshInference = useCallback(() => {
    api.getInferenceStatus().then(setInferenceData).catch(console.error)
  }, [])

  const refreshRecommendation = useCallback(() => {
    api.getActiveRecommendation()
      .then((r: { recommendation: Recommendation | null }) => setActiveRecommendation(r.recommendation))
      .catch(console.error)
  }, [])

  const refreshPurchaseOrders = useCallback(() => {
    api.getPurchaseOrders()
      .then((r: { purchase_orders: PurchaseOrder[] }) => setPurchaseOrders(r.purchase_orders ?? []))
      .catch(console.error)
  }, [])

  const refreshSuppliers = useCallback(() => {
    api.getSuppliers()
      .then((r: { suppliers: Supplier[] }) => setSuppliers(r.suppliers ?? []))
      .catch(console.error)
  }, [])

  const refreshMaterials = useCallback(() => {
    api.getMaterials()
      .then((r: { materials: Material[] }) => setMaterials(r.materials ?? []))
      .catch(console.error)
  }, [])

  const refreshBacklog = useCallback(() => {
    api.getProductionBacklog()
      .then((r: { jobs: ProductionJob[] }) => setProductionJobs(r.jobs ?? []))
      .catch(console.error)
    api.getBacklogSuggestion()
      .then((r: BacklogSuggestion) => setBacklogSuggestion(r))
      .catch(console.error)
  }, [])

  useEffect(() => {
    refreshStatus()
    refreshInference()
    refreshRecommendation()
    refreshPurchaseOrders()
    refreshSuppliers()
    refreshMaterials()
    refreshBacklog()
    api.getEvents(50).then((evts: IESEvent[]) => {
      setEvents(evts.reverse())
      const types = new Set(evts.map((e) => e.event?.type))
      setCompletedTypes(types)
    }).catch(console.error)
  }, [refreshStatus, refreshInference, refreshRecommendation, refreshPurchaseOrders, refreshSuppliers, refreshMaterials, refreshBacklog])

  // Refresco periódico
  useEffect(() => {
    const id = setInterval(() => {
      refreshStatus()
      refreshInference()
      refreshRecommendation()
      refreshPurchaseOrders()
      refreshMaterials()
      refreshBacklog()
    }, 3000)
    return () => clearInterval(id)
  }, [refreshStatus, refreshInference, refreshRecommendation, refreshPurchaseOrders, refreshMaterials, refreshBacklog])

  useEventSource('/api/events/stream', (data) => {
    // Mensajes de sistema (step indicator, offline narrative)
    if ((data as Record<string, unknown>).__type === 'demo_step') {
      const sd = data as { started: boolean; step_number: number }
      if (sd.started && sd.step_number === 1) {
        // Nuevo run: limpiar estado visual anterior
        setCompletedTypes(new Set())
        setActiveStep(1)
      } else if (sd.started) {
        setActiveStep(sd.step_number)
      } else {
        setActiveStep(0)
      }
      return
    }
    if ((data as Record<string, unknown>).__type === 'offline_narrative') {
      refreshStatus()
      return
    }

    // Evento IES normal
    const ev = data as IESEvent
    if (!ev?.event_id) return
    setEvents((prev) => {
      if (prev.some((e) => e.event_id === ev.event_id)) return prev
      return [ev, ...prev]
    })
    setCompletedTypes((prev) => {
      const next = new Set(prev)
      next.add(ev.event?.type)
      return next
    })
    refreshStatus()
    refreshStockHistory()
    refreshRecommendation()
    refreshPurchaseOrders()
    refreshMaterials()
    refreshBacklog()
  })

  const handleAction = useCallback(() => {
    setTimeout(refreshStatus, 800)
    setTimeout(refreshStockHistory, 1000)
    setTimeout(refreshRecommendation, 1000)
    setTimeout(refreshPurchaseOrders, 1000)
    setTimeout(refreshMaterials, 1000)
    setTimeout(refreshBacklog, 1000)
    setTimeout(() => {
      api.getEvents(50).then((evts: IESEvent[]) => {
        setEvents(evts.reverse())
        setCompletedTypes(new Set(evts.map((e) => e.event?.type)))
      })
    }, 1200)
    setAuditRefreshKey(key => key + 1)
  }, [refreshStatus, refreshStockHistory, refreshRecommendation, refreshPurchaseOrders, refreshMaterials, refreshBacklog])

  const handleViewChain = useCallback((correlationId: string) => {
    const filtered = events.filter(
      e => (e.metadata?.correlation_id as string) === correlationId
    )
    if (filtered.length > 0) setSelectedEvent(filtered[0])
  }, [events])

  return (
    <ProtectedRoute>
    <div className="min-h-screen bg-slate-950">
      <Header
        cloudConnected={status.cloud_connected ?? true}
        bufferPending={status.buffer_pending ?? 0}
        demoRunning={status.demo_running ?? false}
        user={user}
        onLogout={logout}
      />

      <main className="p-4 space-y-4 max-w-screen-2xl mx-auto">
        <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex gap-2">
            <button
              onClick={() => navigate('pa')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold border transition-colors ${
                view === 'pa'
                  ? 'bg-cyan-600 border-cyan-500 text-white'
                  : 'bg-slate-900 border-slate-700 text-slate-300 hover:border-slate-500'
              }`}
            >
              Consola PA
            </button>
            <button
              onClick={() => navigate('technical')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold border transition-colors ${
                view === 'technical'
                  ? 'bg-cyan-600 border-cyan-500 text-white'
                  : 'bg-slate-900 border-slate-700 text-slate-300 hover:border-slate-500'
              }`}
            >
              Dashboard Tecnico
            </button>
          </div>
          <span className="text-xs text-slate-500 font-mono truncate">
            {status.last_correlation_id ? `correlation_id: ${status.last_correlation_id}` : 'Sin flujo activo'}
          </span>
        </div>

        {view === 'pa' ? (
          <>
            <PAConsole
              status={status}
              recommendation={activeRecommendation}
              onDecision={handleAction}
            />
            <InventoryPanel
              materials={materials}
              onChange={handleAction}
            />
            <ProductionBacklogPanel
              jobs={productionJobs}
              suggestion={backlogSuggestion}
              onChange={handleAction}
            />
            <PurchaseOrdersPanel
              orders={purchaseOrders}
              suppliers={suppliers}
              onChange={handleAction}
            />
            <SupplierCatalogPanel
              suppliers={suppliers}
              onChange={() => {
                refreshSuppliers()
                refreshPurchaseOrders()
              }}
            />
            <AuditTrailPanel
              defaultCorrelationId={status.last_correlation_id}
              refreshKey={auditRefreshKey}
            />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <KpiCards status={status} />
              </div>
              <div className="lg:col-span-1">
                <ActionButtons
                  onAction={handleAction}
                  cloudConnected={status.cloud_connected ?? true}
                  isRunning={status.demo_running ?? false}
                />
              </div>
            </div>
          </>
        ) : (
          <>
            <KpiCards status={status} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-1">
                <StockChart
                  currentStock={status.current_stock_units ?? 0}
                  reorderPoint={status.reorder_point_units ?? 0}
                  dailyDemand={status.daily_demand_units ?? 250}
                  history={stockHistory}
                />
              </div>
              <div className="lg:col-span-1">
                <EdgeInferencePanel data={inferenceData} />
              </div>
              <div className="lg:col-span-1">
                <ActionButtons
                  onAction={handleAction}
                  cloudConnected={status.cloud_connected ?? true}
                  isRunning={status.demo_running ?? false}
                />
              </div>
            </div>

            <FlowDiagram completedEventTypes={completedTypes} activeStep={activeStep} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Timeline events={events} onSelect={setSelectedEvent} />
              <JsonPanel
                event={selectedEvent as Record<string, unknown> | null}
                allEvents={events}
                onViewChain={handleViewChain}
              />
            </div>
          </>
        )}
      </main>
    </div>
    </ProtectedRoute>
  )
}

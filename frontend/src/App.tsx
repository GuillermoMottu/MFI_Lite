import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import KpiCards from './components/KpiCards'
import StockChart from './components/StockChart'
import Timeline from './components/Timeline'
import JsonPanel from './components/JsonPanel'
import FlowDiagram from './components/FlowDiagram'
import ActionButtons from './components/ActionButtons'
import EdgeInferencePanel from './components/EdgeInferencePanel'
import { useEventSource } from './hooks/useEventSource'
import { api } from './api'

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

export default function App() {
  const [events, setEvents] = useState<IESEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<IESEvent | null>(null)
  const [status, setStatus] = useState<DemoStatus>({})
  const [completedTypes, setCompletedTypes] = useState<Set<string>>(new Set())
  const [activeStep, setActiveStep] = useState<number>(0)
  const [stockHistory, setStockHistory] = useState<StockPoint[]>([])
  const [inferenceData, setInferenceData] = useState<InferenceStatus | null>(null)

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

  useEffect(() => {
    refreshStatus()
    refreshInference()
    api.getEvents(50).then((evts: IESEvent[]) => {
      setEvents(evts.reverse())
      const types = new Set(evts.map((e) => e.event?.type))
      setCompletedTypes(types)
    }).catch(console.error)
  }, [refreshStatus, refreshInference])

  // Refresco periódico
  useEffect(() => {
    const id = setInterval(() => {
      refreshStatus()
      refreshInference()
    }, 3000)
    return () => clearInterval(id)
  }, [refreshStatus, refreshInference])

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
  })

  const handleAction = useCallback(() => {
    setTimeout(refreshStatus, 800)
    setTimeout(refreshStockHistory, 1000)
    setTimeout(() => {
      api.getEvents(50).then((evts: IESEvent[]) => {
        setEvents(evts.reverse())
        setCompletedTypes(new Set(evts.map((e) => e.event?.type)))
      })
    }, 1200)
  }, [refreshStatus, refreshStockHistory])

  const handleViewChain = useCallback((correlationId: string) => {
    const filtered = events.filter(
      e => (e.metadata?.correlation_id as string) === correlationId
    )
    if (filtered.length > 0) setSelectedEvent(filtered[0])
  }, [events])

  return (
    <div className="min-h-screen bg-slate-950">
      <Header
        cloudConnected={status.cloud_connected ?? true}
        bufferPending={status.buffer_pending ?? 0}
        demoRunning={status.demo_running ?? false}
      />

      <main className="p-4 space-y-4 max-w-screen-2xl mx-auto">
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
      </main>
    </div>
  )
}

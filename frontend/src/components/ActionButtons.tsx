import { useState } from 'react'
import { api } from '../api'

interface ActionButtonsProps {
  onAction: () => void
  cloudConnected: boolean
  isRunning: boolean
}

const OFFLINE_PHASES = [
  { key: 'cloud_down', label: 'Edge detectando...' },
  { key: 'edge_detecting', label: 'Bufferizando en SQLite...' },
  { key: 'buffering', label: 'Cloud recuperando...' },
  { key: 'replaying', label: 'Replay sincronizando...' },
]

function Btn({
  label, onClick, variant = 'default', disabled = false
}: {
  label: string; onClick: () => void; variant?: 'primary' | 'danger' | 'warning' | 'success' | 'default' | 'ghost'; disabled?: boolean
}) {
  const colors = {
    primary: 'bg-cyan-600 hover:bg-cyan-500 text-white',
    danger: 'bg-red-700 hover:bg-red-600 text-white',
    warning: 'bg-yellow-600 hover:bg-yellow-500 text-slate-900',
    success: 'bg-green-700 hover:bg-green-600 text-white',
    default: 'bg-slate-700 hover:bg-slate-600 text-white',
    ghost: 'bg-transparent border border-slate-600 hover:border-slate-400 text-slate-300',
  }
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${colors[variant]}`}
    >
      {label}
    </button>
  )
}

export default function ActionButtons({ onAction, cloudConnected, isRunning }: ActionButtonsProps) {
  const [offlinePhase, setOfflinePhase] = useState<number>(-1) // -1 = idle
  const act = (fn: () => Promise<unknown>) => fn().then(onAction).catch(console.error)

  const runOfflineNarrative = async () => {
    setOfflinePhase(0)
    const interval = setInterval(() => {
      setOfflinePhase(prev => {
        if (prev >= OFFLINE_PHASES.length - 1) {
          clearInterval(interval)
          return prev
        }
        return prev + 1
      })
    }, 600)
    try {
      await api.runOfflineNarrative()
      onAction()
    } finally {
      clearInterval(interval)
      setTimeout(() => setOfflinePhase(-1), 1500)
    }
  }

  const isOfflineRunning = offlinePhase >= 0

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">Acciones Manuales</h3>
      <div className="flex flex-wrap gap-2">
        <Btn label="▶ Ejecutar Demo" variant="primary" disabled={isRunning || isOfflineRunning}
          onClick={() => act(api.runDemo)} />
        <Btn label="📉 Simular Stock Bajo" variant="warning" disabled={isOfflineRunning}
          onClick={() => act(api.simulateLowStock)} />
        <Btn label="⏸ Simular Idle" variant="default" disabled={isOfflineRunning}
          onClick={() => act(api.detectIdle)} />
        <Btn label="🔴 Cloud Down" variant="danger" disabled={!cloudConnected || isOfflineRunning}
          onClick={() => act(api.simulateCloudDown)} />
        <Btn label="🟢 Restaurar Cloud" variant="success" disabled={cloudConnected || isOfflineRunning}
          onClick={() => act(api.simulateCloudUp)} />
        <Btn label="🔄 Replay Offline" variant="default" disabled={!cloudConnected || isOfflineRunning}
          onClick={() => act(api.replay)} />
        <Btn label="🛒 Orden Urgente" variant="default" disabled={isOfflineRunning}
          onClick={() => act(api.generatePO)} />
        <Btn label="↺ Reset Demo" variant="ghost" disabled={isOfflineRunning}
          onClick={() => act(api.resetDemo)} />

        {/* Botón narrativa offline */}
        <button
          onClick={runOfflineNarrative}
          disabled={isRunning || isOfflineRunning}
          className="px-4 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed
            bg-violet-700 hover:bg-violet-600 text-white"
        >
          📡 Demo Offline Narrativa
        </button>
      </div>

      {/* Barra de progreso offline */}
      {isOfflineRunning && (
        <div className="mt-3 space-y-1">
          <div className="flex gap-1">
            {OFFLINE_PHASES.map((phase, i) => (
              <div
                key={phase.key}
                className={`h-1.5 flex-1 rounded-full transition-all duration-500
                  ${i <= offlinePhase ? 'bg-violet-500' : 'bg-slate-700'}`}
              />
            ))}
          </div>
          <p className="text-xs text-violet-300 animate-pulse">
            {OFFLINE_PHASES[offlinePhase]?.label ?? 'Completado ✓'}
          </p>
        </div>
      )}
    </div>
  )
}

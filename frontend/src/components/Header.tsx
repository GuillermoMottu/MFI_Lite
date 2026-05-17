interface HeaderProps {
  cloudConnected: boolean
  bufferPending: number
  demoRunning: boolean
  user?: { display_name: string; role: string } | null
  onLogout?: () => void
}

export default function Header({ cloudConnected, bufferPending, demoRunning, user, onLogout }: HeaderProps) {
  return (
    <header className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold text-cyan-400 tracking-tight">
          MaterialFlow Intelligence <span className="text-slate-400 font-normal text-sm">Lite</span>
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          PLT-JUAREZ-01 · LINE-1 · SKU-ACERO-M8 · IES v2.0
        </p>
      </div>

      <div className="flex items-center gap-4 text-sm">
        {demoRunning && (
          <span className="flex items-center gap-1.5 text-yellow-400">
            <span className="inline-block w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
            Ejecutando demo...
          </span>
        )}

        <div className="flex items-center gap-1.5">
          <span className={`w-2.5 h-2.5 rounded-full ${cloudConnected ? 'bg-green-400' : 'bg-red-500'}`} />
          <span className="text-slate-300">Cloud</span>
          {!cloudConnected && (
            <span className="ml-1 text-xs bg-red-900 text-red-300 px-1.5 py-0.5 rounded">OFFLINE</span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-green-400" />
          <span className="text-slate-300">Edge</span>
        </div>

        {bufferPending > 0 && (
          <span className="bg-amber-900 text-amber-300 text-xs px-2 py-1 rounded-full font-mono">
            Buffer: {bufferPending} pendientes
          </span>
        )}

        {user && (
          <div className="flex items-center gap-2">
            <span className="bg-cyan-950 border border-cyan-700 text-cyan-100 text-xs px-2 py-1 rounded-full">
              {user.display_name} {roleLabel(user.role)}
            </span>
            <button
              onClick={onLogout}
              className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs px-2 py-1 rounded-lg"
            >
              Salir
            </button>
          </div>
        )}
      </div>
    </header>
  )
}

function roleLabel(role: string): string {
  if (role === 'pa') return 'PA'
  if (role === 'supervisor') return 'Supervisor'
  return 'Admin'
}

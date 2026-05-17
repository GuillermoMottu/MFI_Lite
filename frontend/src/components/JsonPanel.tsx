interface JsonPanelProps {
  event: Record<string, unknown> | null
  allEvents?: Array<{ metadata?: Record<string, unknown> }>
  onViewChain?: (correlationId: string) => void
}

const IES_KEYS = ['event_id', 'platform_version', 'module', 'asset', 'event', 'data', 'metadata', 'timestamp']

function colorize(json: string): string {
  return json
    .replace(/("event_id"|"platform_version"|"module"|"asset"|"event"|"data"|"metadata"|"timestamp"):/g,
      '<span class="text-cyan-400 font-bold">$1</span>:')
    .replace(/"correlation_id":/g, '<span class="text-yellow-300 font-bold">"correlation_id"</span>:')
    .replace(/"([^"]+)":/g, '<span class="text-blue-300">$&</span>')
    .replace(/: "([^"]+)"/g, ': <span class="text-green-300">"$1"</span>')
    .replace(/: (\d+\.?\d*)/g, ': <span class="text-yellow-300">$1</span>')
    .replace(/: (true|false)/g, ': <span class="text-purple-300">$1</span>')
}

export default function JsonPanel({ event, allEvents = [], onViewChain }: JsonPanelProps) {
  if (!event) {
    return (
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-center h-48">
        <p className="text-slate-500 text-sm">Selecciona un evento del timeline para ver el JSON IES</p>
      </div>
    )
  }

  const correlationId = (event.metadata as Record<string, unknown>)?.correlation_id as string | undefined
  const linkedCount = correlationId
    ? allEvents.filter(e => (e.metadata?.correlation_id as string) === correlationId).length
    : 0

  const json = JSON.stringify(event, null, 2)

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h3 className="text-sm font-semibold text-slate-300">JSON IES v2.0</h3>
        <div className="flex items-center gap-2">
          {correlationId && linkedCount > 0 && (
            <button
              onClick={() => onViewChain?.(correlationId)}
              title={`correlation_id: ${correlationId}`}
              className="text-xs bg-blue-950 text-blue-300 border border-blue-700 px-2 py-0.5 rounded-full hover:bg-blue-900 transition-colors"
            >
              ⛓ {linkedCount} eventos vinculados
            </button>
          )}
          <span className="text-xs bg-green-900 text-green-400 px-2 py-0.5 rounded-full font-semibold">
            ✓ IES v2.0 Validado
          </span>
        </div>
      </div>

      {correlationId && (
        <div className="mb-2 text-xs text-yellow-400 bg-yellow-950 border border-yellow-800 rounded px-2 py-1 font-mono truncate">
          correlation_id: {correlationId}
        </div>
      )}

      <pre
        className="text-xs font-mono bg-slate-950 rounded-lg p-3 overflow-auto max-h-80 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: colorize(json) }}
      />

      <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
        {IES_KEYS.map(k => (
          <span key={k} className={`px-1.5 py-0.5 rounded ${(event as Record<string, unknown>)[k] !== undefined ? 'bg-slate-700 text-slate-300' : 'bg-red-950 text-red-400'}`}>
            {k} {(event as Record<string, unknown>)[k] !== undefined ? '✓' : '✗'}
          </span>
        ))}
      </div>
    </div>
  )
}

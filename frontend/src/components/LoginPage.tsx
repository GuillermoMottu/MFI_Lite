import { FormEvent, useState } from 'react'
import { useAuth } from '../AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('carlos')
  const [password, setPassword] = useState('demo123')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const user = await login(username, password)
      const nextPath = user.role === 'supervisor' ? '/technical' : '/pa'
      window.history.replaceState({}, '', nextPath)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar sesion')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <form onSubmit={submit} className="w-full max-w-sm bg-slate-900 border border-slate-700 rounded-xl p-6">
        <h1 className="text-xl font-bold text-cyan-400">MaterialFlow Lite</h1>
        <p className="text-sm text-slate-500 mt-1">Acceso operativo PA</p>

        <label className="block mt-6">
          <span className="block text-xs text-slate-500 uppercase mb-1">Usuario</span>
          <input
            value={username}
            onChange={event => setUsername(event.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100"
            autoComplete="username"
          />
        </label>

        <label className="block mt-3">
          <span className="block text-xs text-slate-500 uppercase mb-1">Contrasena</span>
          <input
            value={password}
            onChange={event => setPassword(event.target.value)}
            type="password"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100"
            autoComplete="current-password"
          />
        </label>

        {error && <p className="text-xs text-red-300 mt-3">{error}</p>}

        <button
          disabled={busy}
          className="w-full mt-5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold disabled:opacity-40"
        >
          Entrar
        </button>
      </form>
    </main>
  )
}

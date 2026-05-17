import type { ReactNode } from 'react'
import { useAuth } from '../AuthContext'
import LoginPage from './LoginPage'

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center text-sm text-slate-400">
        Cargando sesion...
      </main>
    )
  }

  if (!user) return <LoginPage />
  return <>{children}</>
}

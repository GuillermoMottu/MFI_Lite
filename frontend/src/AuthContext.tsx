import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api, setAuthToken } from './api'

export interface AuthUser {
  username: string
  display_name: string
  role: 'pa' | 'supervisor' | 'admin'
}

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  loading: boolean
  login: (username: string, password: string) => Promise<AuthUser>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)
const TOKEN_KEY = 'mfi_auth_token'
const USER_KEY = 'mfi_auth_user'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) as AuthUser : null
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setAuthToken(token)
    if (!token) {
      setLoading(false)
      return
    }
    api.me()
      .then((response: { user: AuthUser }) => {
        setUser(response.user)
        localStorage.setItem(USER_KEY, JSON.stringify(response.user))
      })
      .catch(() => {
        setToken(null)
        setUser(null)
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setAuthToken(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    loading,
    login: async (username: string, password: string) => {
      const response = await api.login(username, password) as { token: string; user: AuthUser }
      setAuthToken(response.token)
      setToken(response.token)
      setUser(response.user)
      localStorage.setItem(TOKEN_KEY, response.token)
      localStorage.setItem(USER_KEY, JSON.stringify(response.user))
      return response.user
    },
    logout: async () => {
      await api.logout().catch(() => null)
      setToken(null)
      setUser(null)
      setAuthToken(null)
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  }), [user, token, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}

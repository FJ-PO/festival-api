import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, decodeJwt, login as apiLogin, setUnauthorizedHandler, tokenStore } from './api'
import type { User } from './types'

interface AuthState {
  user: User | null
  ready: boolean
  login: (username: string, password: string) => Promise<User>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    setUser(await api<User>('/auth/me'))
  }, [])

  // Al cargar: si hay un token sin caducar, recupera el usuario
  useEffect(() => {
    setUnauthorizedHandler(logout)
    const token = tokenStore.get()
    const payload = token ? decodeJwt(token) : null
    if (!payload || payload.exp * 1000 < Date.now()) {
      tokenStore.clear()
      setReady(true)
      return
    }
    refreshUser().catch(logout).finally(() => setReady(true))
    return () => setUnauthorizedHandler(null)
  }, [logout, refreshUser])

  // Cierra la sesión del cliente en cuanto el token caduca
  useEffect(() => {
    const token = tokenStore.get()
    const payload = token ? decodeJwt(token) : null
    if (!user || !payload) return
    const ms = payload.exp * 1000 - Date.now()
    const timer = setTimeout(logout, Math.max(ms, 0))
    return () => clearTimeout(timer)
  }, [user, logout])

  const login = useCallback(async (username: string, password: string) => {
    const { access_token, user } = await apiLogin(username, password)
    tokenStore.set(access_token)
    setUser(user)
    return user
  }, [])

  const value = useMemo(() => ({ user, ready, login, logout, refreshUser }), [user, ready, login, logout, refreshUser])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return ctx
}

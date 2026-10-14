import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, decodeJwt, login as apiLogin, setUnauthorizedHandler, tokenStore } from './api'
import type { Role, User } from './types'

/** Roles con acceso al panel. Los clientes no pueden entrar. */
const PANEL_ROLES: Role[] = ['admin', 'organizer', 'staff']

interface AuthState {
  user: User | null
  ready: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  can: (...roles: Role[]) => boolean
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

  useEffect(() => {
    setUnauthorizedHandler(logout)
    const token = tokenStore.get()
    const payload = token ? decodeJwt(token) : null
    if (!payload || payload.exp * 1000 < Date.now() || !PANEL_ROLES.includes(payload.role as Role)) {
      tokenStore.clear()
      setReady(true)
      return
    }
    refreshUser().catch(logout).finally(() => setReady(true))
    return () => setUnauthorizedHandler(null)
  }, [logout, refreshUser])

  // El token es la única "sesión": cuando caduca, se sale del panel
  useEffect(() => {
    const payload = decodeJwt(tokenStore.get() ?? '')
    if (!user || !payload) return
    const timer = setTimeout(logout, Math.max(payload.exp * 1000 - Date.now(), 0))
    return () => clearTimeout(timer)
  }, [user, logout])

  const login = useCallback(async (username: string, password: string) => {
    const { access_token, user } = await apiLogin(username, password)
    if (!PANEL_ROLES.includes(user.role)) throw new Error('Tu cuenta no tiene acceso al panel de administración')
    tokenStore.set(access_token)
    setUser(user)
  }, [])

  const can = useCallback((...roles: Role[]) => Boolean(user && roles.includes(user.role)), [user])

  const value = useMemo(() => ({ user, ready, login, logout, refreshUser, can }), [user, ready, login, logout, refreshUser, can])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return ctx
}

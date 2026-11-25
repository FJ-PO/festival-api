import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, decodeJwt, login as apiLogin, refreshToken, setUnauthorizedHandler, tokenStore } from './api'
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

/** Margen antes de `exp` en el que se renueva el token si el usuario está activo. */
const RENEW_MARGIN_MS = 5 * 60_000
const ACTIVITY_EVENTS = ['pointerdown', 'keydown', 'mousemove', 'scroll', 'touchstart'] as const

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

  // Renovación deslizante: poco antes de caducar, si ha habido actividad, se cambia el token por uno nuevo.
  // Sin actividad, la sesión se cierra al llegar a su `exp`.
  useEffect(() => {
    const token = tokenStore.get()
    const payload = token ? decodeJwt(token) : null
    if (!user || !token || !payload) return
    const expMs = payload.exp * 1000
    const renewAt = expMs - Math.min(RENEW_MARGIN_MS, (expMs - payload.iat * 1000) / 2)
    let active = false
    let renewing = false

    const renew = () => {
      if (renewing) return
      renewing = true
      refreshToken()
        .then(({ access_token, user }) => {
          if (!PANEL_ROLES.includes(user.role)) return logout()
          tokenStore.set(access_token)
          setUser(user)
        })
        // Un 401 ya cierra la sesión; si falla la red, se reintenta con la siguiente actividad
        .catch(() => {
          renewing = false
        })
    }
    const onActivity = () => {
      active = true
      if (Date.now() >= renewAt) renew()
    }
    const renewTimer = setTimeout(() => {
      if (active) renew()
    }, Math.max(renewAt - Date.now(), 0))
    const expireTimer = setTimeout(() => {
      // Si otra pestaña ya renovó el token, se adopta en vez de cerrar la sesión
      const current = tokenStore.get()
      const next = current && current !== token ? decodeJwt(current) : null
      if (next && next.exp * 1000 > Date.now()) refreshUser().catch(logout)
      else logout()
    }, Math.max(expMs - Date.now(), 0))
    ACTIVITY_EVENTS.forEach((e) => window.addEventListener(e, onActivity, { passive: true }))
    return () => {
      clearTimeout(renewTimer)
      clearTimeout(expireTimer)
      ACTIVITY_EVENTS.forEach((e) => window.removeEventListener(e, onActivity))
    }
  }, [user, logout, refreshUser])

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

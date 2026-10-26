/**
 * Cliente HTTP de la API. La autenticación es exclusivamente un JWT que se envía en la cabecera
 * `Authorization: Bearer <token>`. No se usan cookies ni sesiones (credentials: 'omit').
 */

const BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')
export const API = `${BASE}/api/v1`

const TOKEN_KEY = 'festival.admin.token'

export const tokenStore = {
  get: (): string | null => {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set: (token: string) => {
    try {
      localStorage.setItem(TOKEN_KEY, token)
    } catch {
      /* almacenamiento no disponible: el token vive solo en memoria */
    }
  },
  clear: () => {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* nada que limpiar */
    }
  },
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

let onUnauthorized: (() => void) | null = null
export const setUnauthorizedHandler = (fn: (() => void) | null) => {
  onUnauthorized = fn
}

function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown })?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d: { msg?: string }) => d.msg?.replace(/^Value error, /, '')).filter(Boolean).join('. ')
  }
  return status >= 500 ? 'Error del servidor. Inténtalo de nuevo.' : 'No se pudo completar la operación.'
}

export async function api<T>(path: string, options: RequestInit & { json?: unknown } = {}): Promise<T> {
  const headers = new Headers(options.headers)
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let body = options.body
  if (options.json !== undefined) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(options.json)
  }
  const res = await fetch(`${API}${path}`, { ...options, headers, body, credentials: 'omit' })
  if (res.status === 204) return undefined as T
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized?.()
    throw new ApiError(res.status, errorMessage(data, res.status))
  }
  return data as T
}

export function login(username: string, password: string) {
  return api<{ access_token: string; expires_in: number; user: import('./types').User }>('/auth/login', {
    method: 'POST',
    body: new URLSearchParams({ username, password }),
  })
}

/** Indica qué inicios de sesión externos están activos en la API (p. ej. GitHub). */
export function authProviders() {
  return api<{ github: boolean }>('/auth/providers')
}

/** Pide a la API la URL de GitHub a la que redirigir al usuario para autorizar la app. */
export function githubAuthorizeUrl(redirectUri: string, state: string) {
  const params = new URLSearchParams({ redirect_uri: redirectUri, state })
  return api<{ url: string }>(`/auth/github/authorize?${params}`)
}

/** Completa el login con GitHub: envía el `code` recibido y obtiene el JWT propio del proyecto. */
export function githubLogin(code: string, redirectUri: string) {
  return api<{ access_token: string; expires_in: number; user: import('./types').User }>('/auth/github', {
    method: 'POST',
    json: { code, redirect_uri: redirectUri },
  })
}

/** Cambia el JWT actual (todavía válido) por uno nuevo. Con uno caducado la API responde 401. */
export function refreshToken() {
  return api<{ access_token: string; expires_in: number; user: import('./types').User }>('/auth/refresh', {
    method: 'POST',
  })
}

/** Lee el payload de un JWT (sin verificar la firma: eso lo hace el servidor). */
export function decodeJwt(token: string): { sub: string; role: string; iat: number; exp: number } | null {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(decodeURIComponent(escape(atob(payload))))
  } catch {
    return null
  }
}

export function mediaUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined
  return url.startsWith('/') ? `${BASE}${url}` : url
}

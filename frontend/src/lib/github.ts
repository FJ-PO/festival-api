/**
 * Flujo de inicio de sesión con GitHub (OAuth2, Authorization Code).
 *
 * El navegador genera un `state` aleatorio y lo guarda para comprobarlo al volver (protección CSRF).
 * El `code` que devuelve GitHub se canjea en la API, que es quien tiene el `client_secret` y emite el JWT.
 */
import { githubAuthorizeUrl } from './api'

const STATE_KEY = 'festival.github.state'
const NEXT_KEY = 'festival.github.next'

export const GITHUB_REDIRECT_PATH = '/oauth/github/callback'

export function githubRedirectUri(): string {
  return `${window.location.origin}${GITHUB_REDIRECT_PATH}`
}

function randomState(): string {
  const bytes = new Uint8Array(16)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}

/** Arranca el flujo: guarda el `state` y el destino, pide la URL a la API y redirige a GitHub. */
export async function startGithubLogin(next: string): Promise<void> {
  const state = randomState()
  try {
    sessionStorage.setItem(STATE_KEY, state)
    sessionStorage.setItem(NEXT_KEY, next)
  } catch {
    /* sin sessionStorage no se puede validar el state con seguridad */
  }
  const { url } = await githubAuthorizeUrl(githubRedirectUri(), state)
  window.location.assign(url)
}

/** Comprueba el `state` devuelto por GitHub contra el guardado y lo consume. */
export function consumeState(returnedState: string | null): boolean {
  let saved: string | null = null
  try {
    saved = sessionStorage.getItem(STATE_KEY)
    sessionStorage.removeItem(STATE_KEY)
  } catch {
    return false
  }
  return !!returnedState && !!saved && returnedState === saved
}

/** Recupera (y limpia) el destino al que volver tras completar el login. */
export function takeNext(): string {
  try {
    const next = sessionStorage.getItem(NEXT_KEY)
    sessionStorage.removeItem(NEXT_KEY)
    if (next && next.startsWith('/') && !next.startsWith('//')) return next
  } catch {
    /* sin sessionStorage: destino por defecto */
  }
  return '/mi-cuenta'
}

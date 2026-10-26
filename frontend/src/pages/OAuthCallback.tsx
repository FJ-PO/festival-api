import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { githubLogin } from '../lib/api'
import { useAuth } from '../lib/auth'
import { consumeState, githubRedirectUri, takeNext } from '../lib/github'

/** Pantalla a la que GitHub devuelve al usuario con `?code=&state=`. Canjea el código y entra. */
export function GithubCallback() {
  const { adoptSession } = useAuth()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const done = useRef(false)

  useEffect(() => {
    if (done.current) return // StrictMode monta dos veces: el código de GitHub es de un solo uso
    done.current = true

    const next = takeNext()
    const ghError = params.get('error_description') || params.get('error')
    if (ghError) {
      setError('No se pudo autorizar con GitHub. Inténtalo de nuevo.')
      return
    }
    const code = params.get('code')
    if (!consumeState(params.get('state'))) {
      setError('La verificación de seguridad falló. Vuelve a iniciar sesión.')
      return
    }
    if (!code) {
      setError('GitHub no devolvió ningún código de autorización.')
      return
    }
    githubLogin(code, githubRedirectUri())
      .then(({ access_token, user }) => {
        adoptSession(access_token, user)
        navigate(next, { replace: true })
      })
      .catch((err) => setError((err as Error).message))
  }, [params, navigate, adoptSession])

  if (error) {
    return (
      <section className="auth">
        <div className="auth-card">
          <h1>No se pudo entrar con GitHub</h1>
          <p className="form-error">{error}</p>
          <Link to="/login" className="btn btn-accent btn-block">Volver a iniciar sesión</Link>
        </div>
      </section>
    )
  }

  return (
    <section className="auth">
      <div className="auth-card">
        <h1>Entrando con GitHub…</h1>
        <p className="muted">Un momento, estamos completando tu inicio de sesión.</p>
      </div>
    </section>
  )
}

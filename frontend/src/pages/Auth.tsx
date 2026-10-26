import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { api, authProviders } from '../lib/api'
import { useAuth } from '../lib/auth'
import { startGithubLogin } from '../lib/github'

function safeNext(next: string | null) {
  // Solo rutas internas, para no convertir el login en una redirección abierta
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/mi-cuenta'
}

/** Botón "Continuar con GitHub". Solo se muestra si la API tiene el proveedor configurado. */
function GithubButton({ next, label }: { next: string; label: string }) {
  const [enabled, setEnabled] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    authProviders()
      .then((p) => alive && setEnabled(p.github))
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [])

  if (!enabled) return null

  async function click() {
    setBusy(true)
    setError(null)
    try {
      await startGithubLogin(next) // redirige a GitHub; no vuelve de aquí
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <>
      <div className="auth-sep"><span>o</span></div>
      <button type="button" className="btn btn-ghost btn-block btn-lg" onClick={click} disabled={busy}>
        <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
            0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53
            .63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95
            0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.42 7.42 0 0 1 2-.27c.68 0
            1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0
            3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01
            8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
        </svg>
        {busy ? 'Redirigiendo…' : label}
      </button>
      {error && <p className="form-error">{error}</p>}
    </>
  )
}

export function Login() {
  const { user, login } = useAuth()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const next = safeNext(params.get('next'))

  if (user) return <Navigate to={next} replace />

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setBusy(true)
    setError(null)
    try {
      await login(String(form.get('username')), String(form.get('password')))
      navigate(next, { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="auth">
      <form className="auth-card" onSubmit={submit}>
        <p className="kicker">Bienvenido de nuevo</p>
        <h1>Entrar</h1>
        <label>
          Email o usuario
          <input name="username" required autoComplete="username" autoFocus />
        </label>
        <label>
          Contraseña
          <input name="password" type="password" required autoComplete="current-password" />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-accent btn-block btn-lg" disabled={busy}>{busy ? 'Entrando…' : 'Entrar'}</button>
        <GithubButton next={next} label="Entrar con GitHub" />
        <p className="muted center">
          ¿No tienes cuenta? <Link to={`/registro?next=${encodeURIComponent(next)}`}>Regístrate</Link>
        </p>
      </form>
    </section>
  )
}

export function Register() {
  const { user, login } = useAuth()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const next = safeNext(params.get('next'))

  if (user) return <Navigate to={next} replace />

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const email = String(form.get('email'))
    const password = String(form.get('password'))
    if (password !== form.get('password2')) {
      setError('Las contraseñas no coinciden')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await api('/auth/register', { method: 'POST', json: { email, password, full_name: form.get('full_name') } })
      await login(email, password)
      navigate(next, { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="auth">
      <form className="auth-card" onSubmit={submit}>
        <p className="kicker">Crea tu cuenta</p>
        <h1>Registro</h1>
        <label>Nombre completo<input name="full_name" required minLength={2} autoComplete="name" /></label>
        <label>Email<input name="email" type="email" required autoComplete="email" /></label>
        <label>Contraseña<input name="password" type="password" required minLength={8} autoComplete="new-password" /></label>
        <label>Repite la contraseña<input name="password2" type="password" required minLength={8} autoComplete="new-password" /></label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-accent btn-block btn-lg" disabled={busy}>{busy ? 'Creando…' : 'Crear cuenta'}</button>
        <GithubButton next={next} label="Registrarme con GitHub" />
        <p className="muted center">¿Ya tienes cuenta? <Link to={`/login?next=${encodeURIComponent(next)}`}>Entra</Link></p>
      </form>
    </section>
  )
}

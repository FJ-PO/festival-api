import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

function safeNext(next: string | null) {
  // Solo rutas internas, para no convertir el login en una redirección abierta
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/mi-cuenta'
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
        <p className="muted center">¿Ya tienes cuenta? <Link to={`/login?next=${encodeURIComponent(next)}`}>Entra</Link></p>
      </form>
    </section>
  )
}

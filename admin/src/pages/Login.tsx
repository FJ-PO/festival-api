import { useState, type FormEvent } from 'react'
import { useAuth } from '../lib/auth'

export default function Login() {
  const { login } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setBusy(true)
    setError(null)
    try {
      await login(String(form.get('username')), String(form.get('password')))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={submit}>
        <div className="login-brand">
          <svg viewBox="0 0 40 40" aria-hidden="true">
            <circle cx="20" cy="20" r="16" fill="none" stroke="currentColor" strokeWidth="3" />
            <circle cx="20" cy="20" r="8" fill="var(--accent)" />
          </svg>
          <div>
            <strong>Las Palomas Festival</strong>
            <span>Panel de administración</span>
          </div>
        </div>
        <label className="field">
          <span className="field-label">Usuario o email</span>
          <input name="username" required autoComplete="username" autoFocus />
        </label>
        <label className="field">
          <span className="field-label">Contraseña</span>
          <input name="password" type="password" required autoComplete="current-password" />
        </label>
        {error && <div className="alert alert-error">{error}</div>}
        <button className="btn btn-primary btn-block" disabled={busy}>{busy ? 'Accediendo…' : 'Acceder'}</button>
        <p className="muted small center">Acceso con token JWT · sin cookies ni sesiones</p>
      </form>
    </div>
  )
}

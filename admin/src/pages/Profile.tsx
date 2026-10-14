import { type FormEvent } from 'react'
import { Card, Field, PageHeader } from '../components/ui'
import { api, decodeJwt, tokenStore } from '../lib/api'
import { useAuth } from '../lib/auth'
import { ROLE } from '../lib/format'
import { useToast } from '../lib/toast'

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const toast = useToast()
  const exp = decodeJwt(tokenStore.get() ?? '')?.exp

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const f = new FormData(form)
    const body: Record<string, unknown> = { full_name: f.get('full_name') }
    if (f.get('new_password')) {
      if (f.get('new_password') !== f.get('repeat')) return toast('Las contraseñas nuevas no coinciden', 'error')
      body.current_password = f.get('current_password')
      body.new_password = f.get('new_password')
    }
    try {
      await api('/auth/me', { method: 'PATCH', json: body })
      await refreshUser()
      toast('Perfil actualizado')
      form.reset()
    } catch (err) {
      toast((err as Error).message, 'error')
    }
  }

  return (
    <>
      <PageHeader title="Mi perfil" />
      <div className="grid-2-1">
        <Card>
          <form onSubmit={submit} className="form-grid">
            <Field label="Usuario"><input value={user?.username ?? '—'} disabled /></Field>
            <Field label="Email"><input value={user?.email} disabled /></Field>
            <Field label="Nombre completo" span={2}><input name="full_name" defaultValue={user?.full_name} required minLength={2} /></Field>
            <Field label="Contraseña actual" span={2}><input name="current_password" type="password" autoComplete="current-password" /></Field>
            <Field label="Nueva contraseña"><input name="new_password" type="password" minLength={8} autoComplete="new-password" /></Field>
            <Field label="Repite la nueva contraseña"><input name="repeat" type="password" minLength={8} autoComplete="new-password" /></Field>
            <div className="form-actions span-2"><button className="btn btn-primary">Guardar</button></div>
          </form>
        </Card>
        <Card title="Sesión">
          <dl className="meta">
            <dt>Rol</dt><dd>{user && ROLE[user.role]}</dd>
            <dt>Autenticación</dt><dd>JWT (Bearer)</dd>
            <dt>Token caduca</dt><dd>{exp ? new Date(exp * 1000).toLocaleString('es-ES') : '—'}</dd>
          </dl>
          <p className="muted small">El panel no usa cookies ni sesiones de servidor: el token se guarda en este navegador y se borra al cerrar sesión o al caducar.</p>
        </Card>
      </div>
    </>
  )
}

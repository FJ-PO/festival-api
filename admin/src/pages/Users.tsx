import { useState, type FormEvent } from 'react'
import Icon from '../components/Icon'
import { Badge, Empty, Field, Loader, Modal, PageHeader, Switch } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { ROLE, utcToLocal } from '../lib/format'
import { useToast } from '../lib/toast'
import type { PageOf, Role, User } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function Users() {
  const [role, setRole] = useState('')
  const [q, setQ] = useState('')
  const query = new URLSearchParams({ limit: '100' })
  if (role) query.set('role', role)
  if (q) query.set('q', q)
  const { data, loading, reload } = useFetch<PageOf<User>>(`/users?${query}`)
  const [creating, setCreating] = useState(false)
  const { user: me } = useAuth()
  const toast = useToast()

  async function update(u: User, changes: Partial<Pick<User, 'role' | 'is_active'>>) {
    try {
      await api(`/users/${u.id}`, { method: 'PATCH', json: changes })
      toast('Usuario actualizado')
      reload()
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  async function create(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    try {
      await api('/users', {
        method: 'POST',
        json: { email: f.get('email'), full_name: f.get('full_name'), username: f.get('username') || null, password: f.get('password'), role: f.get('role') },
      })
      toast('Usuario creado')
      setCreating(false)
      reload()
    } catch (err) {
      toast((err as Error).message, 'error')
    }
  }

  return (
    <>
      <PageHeader title="Usuarios" subtitle={`${data?.total ?? 0} cuentas`}
        actions={<button className="btn btn-primary" onClick={() => setCreating(true)}><Icon name="plus" /> Añadir usuario</button>} />
      <div className="toolbar">
        <div className="segmented">
          {['', 'admin', 'organizer', 'staff', 'customer'].map((r) => (
            <button key={r} className={role === r ? 'is-active' : ''} onClick={() => setRole(r)}>{r ? ROLE[r] : 'Todos'}</button>
          ))}
        </div>
        <input type="search" className="search" placeholder="Buscar por nombre, email o usuario…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {loading && <Loader />}
      {data && data.items.length === 0 && <Empty>No hay usuarios.</Empty>}
      {data && data.items.length > 0 && (
        <div className="table-wrap card">
          <table className="table">
            <thead><tr><th>Nombre</th><th>Usuario</th><th>Email</th><th>Rol</th><th>Alta</th><th>Activo</th></tr></thead>
            <tbody>
              {data.items.map((u) => {
                const self = u.id === me?.id
                return (
                  <tr key={u.id}>
                    <td><strong>{u.full_name}</strong>{self && <> <Badge value="draft" label="Tú" /></>}</td>
                    <td>{u.username ?? '—'}</td>
                    <td>{u.email}</td>
                    <td>
                      <select value={u.role} disabled={self} onChange={(e) => update(u, { role: e.target.value as Role })} className="select-sm">
                        {Object.entries(ROLE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                      </select>
                    </td>
                    <td className="nowrap">{utcToLocal(u.created_at, false)}</td>
                    <td>{self ? <Badge value="true" label="Sí" /> : <Switch checked={u.is_active} onChange={(v) => update(u, { is_active: v })} label="" />}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      {creating && (
        <Modal title="Nuevo usuario" onClose={() => setCreating(false)}>
          <form onSubmit={create} className="form-grid">
            <Field label="Nombre completo" span={2}><input name="full_name" required minLength={2} /></Field>
            <Field label="Email"><input name="email" type="email" required /></Field>
            <Field label="Usuario" hint="Opcional, para entrar sin email"><input name="username" pattern="[A-Za-z0-9_.\-]{3,50}" /></Field>
            <Field label="Contraseña" hint="Mínimo 8 caracteres"><input name="password" type="password" minLength={8} required autoComplete="new-password" /></Field>
            <Field label="Rol">
              <select name="role" defaultValue="staff">{Object.entries(ROLE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
            </Field>
            <div className="form-actions span-2">
              <button type="button" className="btn btn-secondary" onClick={() => setCreating(false)}>Cancelar</button>
              <button className="btn btn-primary">Crear usuario</button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}

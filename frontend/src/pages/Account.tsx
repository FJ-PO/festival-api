import { useState, type FormEvent } from 'react'
import { Link, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import QRCode from '../components/QRCode'
import { Empty, ErrorBox, Loader, PageHero } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { euros, longDay, ORDER_STATUS, TICKET_STATUS, utcToLocal } from '../lib/format'
import type { Order, PageOf, Ticket } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function Account() {
  const { user, ready, logout } = useAuth()
  if (!ready) return <div className="container section"><Loader /></div>
  if (!user) return <Navigate to="/login?next=/mi-cuenta" replace />

  return (
    <>
      <PageHero kicker="Mi cuenta" title={`Hola, ${user.full_name.split(' ')[0]}`}>
        <nav className="tabs">
          <NavLink to="/mi-cuenta" end>Mis entradas</NavLink>
          <NavLink to="/mi-cuenta/pedidos">Mis pedidos</NavLink>
          <NavLink to="/mi-cuenta/perfil">Perfil</NavLink>
          <button className="btn btn-link" onClick={logout}>Cerrar sesión</button>
        </nav>
      </PageHero>
      <section className="section">
        <div className="container">
          <Routes>
            <Route index element={<Tickets />} />
            <Route path="pedidos" element={<Orders />} />
            <Route path="perfil" element={<Profile />} />
          </Routes>
        </div>
      </section>
    </>
  )
}

function Tickets() {
  const { data, error, loading, reload } = useFetch<PageOf<Ticket>>('/tickets?limit=100')
  if (loading) return <Loader />
  if (error) return <ErrorBox message={error} onRetry={reload} />
  if (!data?.items.length) return <Empty>Aún no tienes entradas. <Link to="/programacion">Echa un vistazo a la programación</Link>.</Empty>
  return (
    <div className="grid-tickets">
      {data.items.map((t) => <TicketCard key={t.id} ticket={t} onChange={reload} />)}
    </div>
  )
}

function TicketCard({ ticket, onChange }: { ticket: Ticket; onChange: () => void }) {
  const [mode, setMode] = useState<'view' | 'name' | 'transfer'>('view')
  const [error, setError] = useState<string | null>(null)

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setError(null)
    try {
      if (mode === 'name') {
        await api(`/tickets/${ticket.id}`, { method: 'PATCH', json: { attendee_name: form.get('name') } })
      } else {
        await api(`/tickets/${ticket.id}/transfer`, {
          method: 'POST',
          json: { email: form.get('email'), attendee_name: form.get('name') || null },
        })
      }
      setMode('view')
      onChange()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <article className={`ticket ticket-${ticket.status}`}>
      <div className="ticket-head">
        <span className="tag">{ticket.ticket_type_name}</span>
        <span className={`status status-${ticket.status}`}>{TICKET_STATUS[ticket.status]}</span>
      </div>
      <h3>{ticket.festival_name}</h3>
      <p className="muted">{longDay(ticket.festival_start_date)} · Plaza de Toros de Algeciras</p>
      <div className="ticket-qr">
        <QRCode value={ticket.code} />
        <code>{ticket.code}</code>
      </div>
      <p><span className="muted">A nombre de</span> <strong>{ticket.attendee_name}</strong></p>
      {ticket.status === 'valid' && mode === 'view' && (
        <div className="ticket-actions">
          <button className="btn btn-ghost btn-sm" onClick={() => setMode('name')}>Cambiar nombre</button>
          <button className="btn btn-ghost btn-sm" onClick={() => setMode('transfer')}>Transferir</button>
        </div>
      )}
      {mode !== 'view' && (
        <form className="ticket-form" onSubmit={submit}>
          {mode === 'transfer' && <input name="email" type="email" required placeholder="Email del destinatario (registrado)" />}
          <input name="name" required={mode === 'name'} minLength={2} placeholder={mode === 'name' ? 'Nombre del asistente' : 'Nombre (opcional)'} />
          {mode === 'transfer' && <p className="muted small">Al transferirla se genera un QR nuevo y el actual deja de valer.</p>}
          {error && <p className="form-error">{error}</p>}
          <div className="ticket-actions">
            <button className="btn btn-accent btn-sm">{mode === 'name' ? 'Guardar' : 'Transferir'}</button>
            <button type="button" className="btn btn-link" onClick={() => setMode('view')}>Cancelar</button>
          </div>
        </form>
      )}
    </article>
  )
}

function Orders() {
  const { data, error, loading, reload } = useFetch<PageOf<Order>>('/orders?limit=100')
  const [actionError, setActionError] = useState<string | null>(null)

  async function cancel(order: Order) {
    const verb = order.status === 'paid' ? 'solicitar el reembolso de' : 'cancelar'
    if (!confirm(`¿Seguro que quieres ${verb} este pedido?`)) return
    setActionError(null)
    try {
      await api(`/orders/${order.id}/cancel`, { method: 'POST' })
      reload()
    } catch (e) {
      setActionError((e as Error).message)
    }
  }

  if (loading) return <Loader />
  if (error) return <ErrorBox message={error} onRetry={reload} />
  if (!data?.items.length) return <Empty>No tienes pedidos todavía.</Empty>
  return (
    <>
      {actionError && <ErrorBox message={actionError} />}
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr><th>Pedido</th><th>Espectáculo</th><th>Fecha</th><th>Total</th><th>Estado</th><th /></tr>
          </thead>
          <tbody>
            {data.items.map((o) => (
              <tr key={o.id}>
                <td>#{o.id}</td>
                <td>{o.festival_name}<br /><span className="muted small">{o.items.map((i) => `${i.quantity}× ${i.ticket_type_name}`).join(', ')}</span></td>
                <td>{utcToLocal(o.created_at)}</td>
                <td>{euros(o.total)}</td>
                <td><span className={`status status-${o.status}`}>{ORDER_STATUS[o.status]}</span></td>
                <td className="right">
                  {o.status === 'pending' && <Link to={`/checkout/${o.id}`} className="btn btn-accent btn-sm">Pagar</Link>}
                  {(o.status === 'pending' || o.status === 'paid') && (
                    <button className="btn btn-link" onClick={() => cancel(o)}>{o.status === 'paid' ? 'Reembolsar' : 'Cancelar'}</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function Profile() {
  const { user, refreshUser } = useAuth()
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const body: Record<string, unknown> = { full_name: form.get('full_name') }
    if (form.get('new_password')) {
      body.current_password = form.get('current_password')
      body.new_password = form.get('new_password')
    }
    try {
      await api('/auth/me', { method: 'PATCH', json: body })
      await refreshUser()
      setMsg({ ok: true, text: 'Datos guardados' })
      e.currentTarget?.reset()
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message })
    }
  }

  return (
    <form className="form-card" onSubmit={submit}>
      <label>Email<input value={user?.email} disabled /></label>
      <label>Nombre completo<input name="full_name" defaultValue={user?.full_name} required minLength={2} /></label>
      <fieldset>
        <legend>Cambiar contraseña</legend>
        <label>Contraseña actual<input name="current_password" type="password" autoComplete="current-password" /></label>
        <label>Nueva contraseña<input name="new_password" type="password" minLength={8} autoComplete="new-password" /></label>
      </fieldset>
      {msg && <p className={msg.ok ? 'ok-text' : 'form-error'}>{msg.text}</p>}
      <button className="btn btn-accent">Guardar cambios</button>
    </form>
  )
}

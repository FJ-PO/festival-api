import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Icon from '../components/Icon'
import { ImageField } from '../components/MediaPicker'
import { Badge, Card, Empty, ErrorBox, Field, Loader, Modal, PageHeader, Switch } from '../components/ui'
import { api } from '../lib/api'
import { euros, hour, toInput, utcToLocal } from '../lib/format'
import { useToast } from '../lib/toast'
import type { Artist, DiscountCode, FestivalDetail, FestivalStats, Order, PageOf, TicketType, Venue } from '../lib/types'
import { useFetch } from '../lib/useFetch'

const PUBLIC_SITE = import.meta.env.VITE_PUBLIC_SITE ?? 'http://localhost:5173'
type Tab = 'datos' | 'entradas' | 'cartel' | 'descuentos' | 'pedidos' | 'estadisticas'

export default function FestivalEdit() {
  const { id } = useParams()
  const isNew = id === 'nuevo'
  const { data: festival, error, loading, reload, setData } = useFetch<FestivalDetail>(isNew ? null : `/festivals/${id}`)
  const [tab, setTab] = useState<Tab>('datos')
  const toast = useToast()
  const navigate = useNavigate()

  if (loading) return <Loader />
  if (error) return <ErrorBox message={error} />

  async function action(path: 'publish' | 'cancel' | 'finish') {
    const msg = {
      publish: '¿Publicar esta noche? Será visible en la web y se podrán comprar entradas.',
      cancel: '¿Cancelar esta noche? Se reembolsarán automáticamente todos los pedidos pagados.',
      finish: '¿Marcar esta noche como finalizada?',
    }[path]
    if (!confirm(msg)) return
    try {
      await api(`/festivals/${id}/${path}`, { method: 'POST' })
      toast({ publish: 'Noche publicada', cancel: 'Noche cancelada y pedidos reembolsados', finish: 'Noche finalizada' }[path])
      reload()
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  async function remove() {
    if (!confirm('¿Eliminar definitivamente este borrador?')) return
    try {
      await api(`/festivals/${id}`, { method: 'DELETE' })
      toast('Borrador eliminado')
      navigate('/festivales')
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  const tabs: [Tab, string][] = [
    ['datos', 'Datos'], ['entradas', 'Entradas'], ['cartel', 'Cartel'],
    ['descuentos', 'Descuentos'], ['pedidos', 'Pedidos'], ['estadisticas', 'Estadísticas'],
  ]

  return (
    <>
      <PageHeader
        title={isNew ? 'Nueva noche' : festival!.name}
        subtitle={festival && <><Badge value={festival.status} /> <Link to="/festivales" className="muted">← Todas las noches</Link></>}
        actions={festival && (
          <>
            <a className="btn btn-secondary" href={`${PUBLIC_SITE}/festivales/${festival.slug}`} target="_blank" rel="noreferrer">
              <Icon name="external" /> {festival.status === 'draft' ? 'Previsualizar' : 'Ver en la web'}
            </a>
            {festival.status === 'draft' && <button className="btn btn-primary" onClick={() => action('publish')}>Publicar</button>}
            {festival.status === 'published' && <button className="btn btn-secondary" onClick={() => action('finish')}>Finalizar</button>}
            {(festival.status === 'draft' || festival.status === 'published') && <button className="btn btn-danger-ghost" onClick={() => action('cancel')}>Cancelar noche</button>}
            {festival.status === 'draft' && <button className="btn btn-danger-ghost" onClick={remove}><Icon name="trash" /></button>}
          </>
        )}
      />
      {!isNew && (
        <nav className="tabs">
          {tabs.map(([key, label]) => (
            <button key={key} className={tab === key ? 'is-active' : ''} onClick={() => setTab(key)}>{label}</button>
          ))}
        </nav>
      )}
      {tab === 'datos' && (
        <DetailsForm festival={festival} onSaved={(f) => {
          if (isNew) navigate(`/festivales/${f.id}`, { replace: true })
          else setData({ ...festival!, ...f })
        }} />
      )}
      {festival && tab === 'entradas' && <TicketTypes festival={festival} onChange={reload} />}
      {festival && tab === 'cartel' && <Lineup festival={festival} onChange={reload} />}
      {festival && tab === 'descuentos' && <Discounts festivalId={festival.id} />}
      {festival && tab === 'pedidos' && <Orders festivalId={festival.id} />}
      {festival && tab === 'estadisticas' && <Stats festivalId={festival.id} />}
    </>
  )
}

function DetailsForm({ festival, onSaved }: { festival: FestivalDetail | null; onSaved: (f: FestivalDetail) => void }) {
  const venues = useFetch<PageOf<Venue>>('/venues?limit=100')
  const toast = useToast()
  const [image, setImage] = useState<string | null>(festival?.image_url ?? null)
  const [busy, setBusy] = useState(false)
  const locked = festival?.status === 'cancelled' || festival?.status === 'finished'

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    const body = {
      name: f.get('name'),
      description: f.get('description') || null,
      genre: f.get('genre') || null,
      start_date: f.get('start_date'),
      end_date: f.get('end_date') || f.get('start_date'),
      min_age: Number(f.get('min_age') || 0),
      venue_id: Number(f.get('venue_id')),
      image_url: image,
    }
    setBusy(true)
    try {
      const saved = await api<FestivalDetail>(festival ? `/festivals/${festival.id}` : '/festivals', {
        method: festival ? 'PATCH' : 'POST',
        json: body,
      })
      toast(festival ? 'Cambios guardados' : 'Noche creada en borrador. Añade sus entradas para publicarla.')
      onSaved(saved)
    } catch (err) {
      toast((err as Error).message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="editor-layout">
      <Card>
        <fieldset disabled={locked} className="form-grid">
          <Field label="Nombre (artista o espectáculo)" span={2}><input name="name" defaultValue={festival?.name} required minLength={2} /></Field>
          <Field label="Descripción" span={2}><textarea name="description" rows={5} defaultValue={festival?.description ?? ''} /></Field>
          <Field label="Género" hint="Usa «Humor» para las noches de humor"><input name="genre" defaultValue={festival?.genre ?? ''} list="genres" /></Field>
          <datalist id="genres">{['Pop', 'Flamenco', 'Flamenco pop', 'Urbano', 'Pop urbano', 'Rock', 'Humor'].map((g) => <option key={g} value={g} />)}</datalist>
          <Field label="Recinto">
            <select name="venue_id" defaultValue={festival?.venue.id} required>
              {venues.data?.items.map((v) => <option key={v.id} value={v.id}>{v.name} · {v.municipality}</option>)}
            </select>
          </Field>
          <Field label="Fecha"><input type="date" name="start_date" defaultValue={festival?.start_date} required /></Field>
          <Field label="Fecha de fin" hint="Igual que la fecha si es una sola noche"><input type="date" name="end_date" defaultValue={festival?.end_date} /></Field>
          <Field label="Edad mínima"><input type="number" name="min_age" min={0} max={99} defaultValue={festival?.min_age ?? 0} /></Field>
        </fieldset>
        {locked && <p className="muted">Una noche cancelada o finalizada ya no se puede editar.</p>}
      </Card>
      <div className="editor-side">
        <Card title="Publicación">
          <p className="muted small">{festival ? `Slug: /festivales/${festival.slug}` : 'Se creará como borrador.'}</p>
          <button className="btn btn-primary btn-block" disabled={busy || locked}>{busy ? 'Guardando…' : festival ? 'Guardar cambios' : 'Crear noche'}</button>
        </Card>
        <Card title="Imagen del cartel">
          <ImageField value={image} onChange={setImage} />
        </Card>
      </div>
    </form>
  )
}

function TicketTypes({ festival, onChange }: { festival: FestivalDetail; onChange: () => void }) {
  const { data, loading, reload } = useFetch<TicketType[]>(`/festivals/${festival.id}/ticket-types`)
  const [editing, setEditing] = useState<TicketType | 'new' | null>(null)
  const toast = useToast()

  async function toggle(t: TicketType) {
    await api(`/ticket-types/${t.id}`, { method: 'PATCH', json: { is_active: !t.is_active } })
    reload()
    onChange()
  }

  async function remove(t: TicketType) {
    if (!confirm(`¿Eliminar «${t.name}»?`)) return
    try {
      await api(`/ticket-types/${t.id}`, { method: 'DELETE' })
      reload()
      onChange()
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  return (
    <Card title="Zonas y tipos de entrada" actions={<button className="btn btn-primary btn-sm" onClick={() => setEditing('new')}><Icon name="plus" /> Añadir</button>}>
      {loading && <Loader />}
      {data && data.length === 0 && <Empty>Sin entradas. Añade al menos una para poder publicar.</Empty>}
      {data && data.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Nombre</th><th>Precio</th><th>Vendidas</th><th>Ocupación</th><th>Máx./pedido</th><th>Activa</th><th /></tr></thead>
            <tbody>
              {data.map((t) => (
                <tr key={t.id}>
                  <td><strong>{t.name}</strong>{t.description && <div className="muted small">{t.description}</div>}</td>
                  <td>{euros(t.price)}</td>
                  <td className="nowrap">{t.quantity_sold} / {t.quantity_total}</td>
                  <td><div className="progress"><span style={{ width: `${(t.quantity_sold / t.quantity_total) * 100}%` }} /></div></td>
                  <td>{t.max_per_order}</td>
                  <td><Switch checked={t.is_active} onChange={() => toggle(t)} label="" /></td>
                  <td className="right nowrap">
                    <button className="btn btn-secondary btn-sm" onClick={() => setEditing(t)}><Icon name="edit" /></button>{' '}
                    <button className="btn btn-danger-ghost btn-sm" onClick={() => remove(t)}><Icon name="trash" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {editing && (
        <TicketTypeModal festivalId={festival.id} ticket={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload(); onChange() }} />
      )}
    </Card>
  )
}

function TicketTypeModal({ festivalId, ticket, onClose, onSaved }: { festivalId: number; ticket: TicketType | null; onClose: () => void; onSaved: () => void }) {
  const toast = useToast()
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    const body = {
      name: f.get('name'),
      description: f.get('description') || null,
      price: String(f.get('price')),
      quantity_total: Number(f.get('quantity_total')),
      max_per_order: Number(f.get('max_per_order')),
      sale_start: f.get('sale_start') || null,
      sale_end: f.get('sale_end') || null,
    }
    try {
      await api(ticket ? `/ticket-types/${ticket.id}` : `/festivals/${festivalId}/ticket-types`, { method: ticket ? 'PATCH' : 'POST', json: body })
      toast('Entrada guardada')
      onSaved()
    } catch (err) {
      toast((err as Error).message, 'error')
    }
  }
  return (
    <Modal title={ticket ? `Editar «${ticket.name}»` : 'Nueva zona de entrada'} onClose={onClose}>
      <form onSubmit={submit} className="form-grid">
        <Field label="Nombre" span={2}><input name="name" defaultValue={ticket?.name} required placeholder="Pista, Grada, Front Stage…" /></Field>
        <Field label="Descripción" span={2}><input name="description" defaultValue={ticket?.description ?? ''} /></Field>
        <Field label="Precio (€)"><input name="price" type="number" step="0.01" min="0" defaultValue={ticket?.price} required /></Field>
        <Field label="Aforo de la zona"><input name="quantity_total" type="number" min={1} defaultValue={ticket?.quantity_total} required /></Field>
        <Field label="Máximo por pedido"><input name="max_per_order" type="number" min={1} max={50} defaultValue={ticket?.max_per_order ?? 8} required /></Field>
        <div />
        <Field label="Inicio de venta (UTC)" hint="Vacío = ya a la venta"><input name="sale_start" type="datetime-local" defaultValue={toInput(ticket?.sale_start)} /></Field>
        <Field label="Fin de venta (UTC)"><input name="sale_end" type="datetime-local" defaultValue={toInput(ticket?.sale_end)} /></Field>
        <div className="form-actions span-2">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary">Guardar</button>
        </div>
      </form>
    </Modal>
  )
}

function Lineup({ festival, onChange }: { festival: FestivalDetail; onChange: () => void }) {
  const artists = useFetch<PageOf<Artist>>('/artists?limit=100')
  const toast = useToast()
  const [artistId, setArtistId] = useState('')

  async function add(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    try {
      await api(`/festivals/${festival.id}/lineup`, {
        method: 'POST',
        json: { artist_id: Number(artistId), stage: f.get('stage'), start_time: f.get('start_time'), end_time: f.get('end_time') },
      })
      toast('Actuación añadida al cartel')
      e.currentTarget.reset()
      setArtistId('')
      onChange()
    } catch (err) {
      toast((err as Error).message, 'error')
    }
  }

  async function remove(perfId: number) {
    if (!confirm('¿Quitar esta actuación del cartel?')) return
    await api(`/festivals/${festival.id}/lineup/${perfId}`, { method: 'DELETE' })
    onChange()
  }

  return (
    <div className="grid-2-1">
      <Card title="Cartel y horarios">
        {festival.performances.length === 0 ? <Empty>Todavía no hay actuaciones.</Empty> : (
          <ul className="lineup-admin">
            {festival.performances.map((p) => (
              <li key={p.id}>
                <time>{hour(p.start_time)}–{hour(p.end_time)}</time>
                <div><strong>{p.artist.name}</strong><span className="muted small">{p.stage} · {p.start_time.slice(0, 10)}</span></div>
                <button className="btn btn-danger-ghost btn-sm" onClick={() => remove(p.id)} aria-label="Quitar"><Icon name="trash" /></button>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card title="Añadir actuación">
        <form onSubmit={add} className="form-stack">
          <Field label="Artista">
            <select value={artistId} onChange={(e) => setArtistId(e.target.value)} required>
              <option value="">Elige un artista…</option>
              {artists.data?.items.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </Field>
          <p className="small muted">¿No está? <Link to="/artistas">Créalo en Artistas</Link>.</p>
          <Field label="Escenario"><input name="stage" defaultValue="Escenario Las Palomas" required /></Field>
          <Field label="Inicio"><input name="start_time" type="datetime-local" defaultValue={`${festival.start_date}T22:00`} required /></Field>
          <Field label="Fin"><input name="end_time" type="datetime-local" defaultValue={`${festival.start_date}T23:59`} required /></Field>
          <button className="btn btn-primary">Añadir al cartel</button>
        </form>
      </Card>
    </div>
  )
}

function Discounts({ festivalId }: { festivalId: number }) {
  const { data, loading, reload } = useFetch<DiscountCode[]>(`/festivals/${festivalId}/discount-codes`)
  const toast = useToast()

  async function create(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    try {
      await api(`/festivals/${festivalId}/discount-codes`, {
        method: 'POST',
        json: {
          code: f.get('code'),
          percent_off: Number(f.get('percent_off')),
          max_uses: f.get('max_uses') ? Number(f.get('max_uses')) : null,
          valid_until: f.get('valid_until') || null,
        },
      })
      toast('Código creado')
      e.currentTarget.reset()
      reload()
    } catch (err) {
      toast((err as Error).message, 'error')
    }
  }

  async function toggle(d: DiscountCode) {
    await api(`/discount-codes/${d.id}`, { method: 'PATCH', json: { is_active: !d.is_active } })
    reload()
  }

  return (
    <div className="grid-2-1">
      <Card title="Códigos de descuento">
        {loading && <Loader />}
        {data && data.length === 0 && <Empty>No hay códigos.</Empty>}
        {data && data.length > 0 && (
          <table className="table">
            <thead><tr><th>Código</th><th>Descuento</th><th>Usos</th><th>Válido hasta</th><th>Activo</th></tr></thead>
            <tbody>
              {data.map((d) => (
                <tr key={d.id}>
                  <td><code>{d.code}</code></td><td>−{d.percent_off}%</td>
                  <td>{d.times_used}{d.max_uses ? ` / ${d.max_uses}` : ''}</td>
                  <td>{d.valid_until ? utcToLocal(d.valid_until) : 'Sin límite'}</td>
                  <td><Switch checked={d.is_active} onChange={() => toggle(d)} label="" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
      <Card title="Nuevo código">
        <form onSubmit={create} className="form-stack">
          <Field label="Código"><input name="code" required pattern="[A-Za-z0-9_-]{3,40}" placeholder="VERANO10" /></Field>
          <Field label="Descuento (%)"><input name="percent_off" type="number" min={1} max={100} required /></Field>
          <Field label="Usos máximos" hint="Vacío = ilimitado"><input name="max_uses" type="number" min={1} /></Field>
          <Field label="Válido hasta (UTC)"><input name="valid_until" type="datetime-local" /></Field>
          <button className="btn btn-primary">Crear código</button>
        </form>
      </Card>
    </div>
  )
}

function Orders({ festivalId }: { festivalId: number }) {
  const [status, setStatus] = useState('')
  const { data, loading } = useFetch<PageOf<Order>>(`/festivals/${festivalId}/orders?limit=100${status ? `&status=${status}` : ''}`)
  return (
    <Card title="Pedidos" actions={
      <select value={status} onChange={(e) => setStatus(e.target.value)} className="select-sm">
        <option value="">Todos</option><option value="paid">Pagados</option><option value="pending">Pendientes</option>
        <option value="refunded">Reembolsados</option><option value="cancelled">Cancelados</option><option value="expired">Caducados</option>
      </select>
    }>
      {loading && <Loader />}
      {data && data.items.length === 0 && <Empty>No hay pedidos.</Empty>}
      {data && data.items.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>#</th><th>Fecha</th><th>Entradas</th><th>Descuento</th><th>Total</th><th>Pago</th><th>Estado</th></tr></thead>
            <tbody>
              {data.items.map((o) => (
                <tr key={o.id}>
                  <td>{o.id}</td><td className="nowrap">{utcToLocal(o.created_at)}</td>
                  <td>{o.items.map((i) => `${i.quantity}× ${i.ticket_type_name}`).join(', ')}</td>
                  <td>{Number(o.discount_amount) ? `−${euros(o.discount_amount)}` : '—'}</td>
                  <td>{euros(o.total)}</td><td>{o.payment_method ?? '—'}</td><td><Badge value={o.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

function Stats({ festivalId }: { festivalId: number }) {
  const { data, loading, error } = useFetch<FestivalStats>(`/festivals/${festivalId}/stats`)
  if (loading) return <Loader />
  if (error || !data) return <ErrorBox message={error ?? 'Sin datos'} />
  const sold = data.ticket_types.reduce((s, t) => s + t.quantity_sold, 0)
  const total = data.ticket_types.reduce((s, t) => s + t.quantity_total, 0)
  return (
    <>
      <div className="kpis">
        <div className="kpi"><div><p className="kpi-label">Recaudación</p><p className="kpi-value">{euros(data.revenue)}</p></div></div>
        <div className="kpi"><div><p className="kpi-label">Entradas emitidas</p><p className="kpi-value">{data.tickets_issued}</p></div></div>
        <div className="kpi"><div><p className="kpi-label">Validadas en puerta</p><p className="kpi-value">{data.tickets_checked_in}</p><p className="kpi-hint">{(data.attendance_rate * 100).toFixed(1)}% de asistencia</p></div></div>
        <div className="kpi"><div><p className="kpi-label">Ocupación</p><p className="kpi-value">{total ? ((sold / total) * 100).toFixed(1) : 0}%</p><p className="kpi-hint">{sold} de {total}</p></div></div>
      </div>
      <Card title="Ventas por zona">
        <ul className="bars">
          {data.ticket_types.map((t) => (
            <li key={t.ticket_type_id}>
              <span>{t.name}</span>
              <div className="progress progress-lg"><span style={{ width: `${(t.quantity_sold / t.quantity_total) * 100}%` }} /></div>
              <strong>{t.quantity_sold} / {t.quantity_total}</strong>
            </li>
          ))}
        </ul>
      </Card>
    </>
  )
}

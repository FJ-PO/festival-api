import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Markdown from '../components/Markdown'
import Poster from '../components/Poster'
import { BackLink, ErrorBox, Loader } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { euros, hour, longDay } from '../lib/format'
import type { FestivalDetail, Order, TicketType } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function FestivalPage() {
  const { slug } = useParams()
  const { data: festival, error, loading, reload } = useFetch<FestivalDetail>(`/festivals/slug/${slug}`)
  const types = useFetch<TicketType[]>(festival ? `/festivals/${festival.id}/ticket-types` : null)

  if (loading) return <div className="container section"><Loader /></div>
  if (error || !festival) return <div className="container section"><ErrorBox message={error ?? 'No encontrado'} onRetry={reload} /></div>

  const headliner = festival.performances[0]?.artist
  const mapUrl = `https://www.openstreetmap.org/search?query=${encodeURIComponent(`${festival.venue.name}, ${festival.venue.municipality}`)}`

  return (
    <>
      <section className="festival-hero">
        <Poster name={festival.name} image={festival.image_url ?? headliner?.image_url} className="festival-hero-bg" wide plain />
        <div className="container festival-hero-inner">
          <BackLink to="/programacion">Programación</BackLink>
          {festival.genre && <span className="tag tag-accent">{festival.genre}</span>}
          <h1 className="display">{festival.name}</h1>
          <p className="festival-when">
            {longDay(festival.start_date)} · {festival.performances[0] ? hour(festival.performances[0].start_time) : '22:00'} h
            <span> · {festival.venue.name}</span>
          </p>
          {festival.status === 'cancelled' && <p className="tag tag-danger">Espectáculo cancelado · pedidos reembolsados</p>}
          {festival.status === 'draft' && <p className="tag">Borrador · solo visible para la organización</p>}
        </div>
      </section>

      <section className="section">
        <div className="container festival-layout">
          <div className="festival-main">
            {festival.description && <p className="lead">{festival.description}</p>}
            {headliner?.bio && !festival.description?.includes(headliner.bio) && <Markdown source={headliner.bio} />}

            {festival.performances.length > 0 && (
              <>
                <h2 className="h-sub">Horario</h2>
                <ul className="timetable">
                  {festival.performances.map((p) => (
                    <li key={p.id}>
                      <time>{hour(p.start_time)}</time>
                      <div>
                        <strong>{p.artist.name}</strong>
                        <span className="muted">{p.stage}{p.artist.country ? ` · ${p.artist.country}` : ''}</span>
                      </div>
                      <time className="muted">{hour(p.end_time)}</time>
                    </li>
                  ))}
                </ul>
              </>
            )}

            <h2 className="h-sub">Información</h2>
            <dl className="facts">
              <div><dt>Recinto</dt><dd>{festival.venue.name}</dd></div>
              <div><dt>Dirección</dt><dd>{festival.venue.address}</dd></div>
              <div><dt>Puertas</dt><dd>20:30 h</dd></div>
              <div><dt>Edad mínima</dt><dd>{festival.min_age ? `+${festival.min_age} años` : 'Todos los públicos'}</dd></div>
            </dl>
            <p>
              <a href={mapUrl} target="_blank" rel="noreferrer noopener" className="link-arrow">Ver en el mapa →</a>
              {'  '}
              <Link to="/p/como-llegar" className="link-arrow">Cómo llegar →</Link>
            </p>
          </div>

          <aside className="festival-aside">
            {festival.status === 'published' && types.data && (
              <TicketPicker festivalId={festival.id} types={types.data} />
            )}
            {types.loading && <Loader />}
          </aside>
        </div>
      </section>
    </>
  )
}

function TicketPicker({ festivalId, types }: { festivalId: number; types: TicketType[] }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [qty, setQty] = useState<Record<number, number>>({})
  const [code, setCode] = useState('')
  const [discount, setDiscount] = useState<{ code: string; percent_off: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const now = Date.now()
  const onSale = (t: TicketType) =>
    t.quantity_available > 0 &&
    (!t.sale_start || new Date(`${t.sale_start}Z`).getTime() <= now) &&
    (!t.sale_end || new Date(`${t.sale_end}Z`).getTime() > now)

  const subtotal = types.reduce((sum, t) => sum + (qty[t.id] ?? 0) * Number(t.price), 0)
  const total = discount ? subtotal * (1 - discount.percent_off / 100) : subtotal
  const count = Object.values(qty).reduce((a, b) => a + b, 0)

  const change = (t: TicketType, delta: number) =>
    setQty((q) => ({ ...q, [t.id]: Math.min(Math.max((q[t.id] ?? 0) + delta, 0), Math.min(t.max_per_order, t.quantity_available)) }))

  async function checkCode() {
    setError(null)
    try {
      setDiscount(await api(`/festivals/${festivalId}/discount-codes/check?code=${encodeURIComponent(code)}`))
    } catch (e) {
      setDiscount(null)
      setError((e as Error).message)
    }
  }

  async function buy() {
    if (!user) {
      navigate(`/login?next=${encodeURIComponent(location.pathname)}`)
      return
    }
    setBusy(true)
    setError(null)
    try {
      const order = await api<Order>('/orders', {
        method: 'POST',
        json: {
          festival_id: festivalId,
          items: Object.entries(qty).filter(([, n]) => n > 0).map(([id, n]) => ({ ticket_type_id: Number(id), quantity: n })),
          discount_code: discount?.code ?? null,
        },
      })
      navigate(`/checkout/${order.id}`)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="ticket-box">
      <h2>Entradas</h2>
      <ul className="ticket-list">
        {types.map((t) => {
          const available = onSale(t)
          return (
            <li key={t.id} className={available ? '' : 'is-disabled'}>
              <div>
                <strong>{t.name}</strong>
                {t.description && <span className="muted">{t.description}</span>}
                <span className="price">{euros(t.price)}</span>
              </div>
              {available ? (
                <div className="stepper">
                  <button onClick={() => change(t, -1)} aria-label={`Quitar ${t.name}`} disabled={!qty[t.id]}>−</button>
                  <output aria-live="polite">{qty[t.id] ?? 0}</output>
                  <button onClick={() => change(t, 1)} aria-label={`Añadir ${t.name}`}>+</button>
                </div>
              ) : (
                <span className="tag">{t.quantity_available === 0 ? 'Agotado' : 'No disponible'}</span>
              )}
            </li>
          )
        })}
      </ul>
      <div className="discount">
        <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} placeholder="Código de descuento" aria-label="Código de descuento" />
        <button className="btn btn-ghost btn-sm" onClick={checkCode} disabled={!code}>Aplicar</button>
      </div>
      {discount && <p className="ok-text">Código {discount.code}: −{discount.percent_off}%</p>}
      <div className="ticket-total">
        <span>{count} {count === 1 ? 'entrada' : 'entradas'}</span>
        <strong>{euros(total.toFixed(2))}</strong>
      </div>
      {error && <p className="form-error">{error}</p>}
      <button className="btn btn-accent btn-block btn-lg" disabled={!count || busy} onClick={buy}>
        {busy ? 'Reservando…' : user ? 'Comprar' : 'Inicia sesión para comprar'}
      </button>
      <p className="muted small">Al continuar reservamos tus entradas durante 15 minutos.</p>
    </div>
  )
}

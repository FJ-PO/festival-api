import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ErrorBox, Loader, PageHero } from '../components/ui'
import { api } from '../lib/api'
import { euros, ORDER_STATUS, utcMillis } from '../lib/format'
import type { Order } from '../lib/types'
import { useFetch } from '../lib/useFetch'

function useRemaining(expiresAt: string | undefined) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  return expiresAt ? Math.max(0, Math.floor((utcMillis(expiresAt) - now) / 1000)) : 0
}

export default function Checkout() {
  const { orderId } = useParams()
  const { data: order, error, loading, setData } = useFetch<Order>(`/orders/${orderId}`)
  const remaining = useRemaining(order?.expires_at)
  const [method, setMethod] = useState<'card' | 'bizum' | 'paypal'>('card')
  const [payError, setPayError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) return <div className="container section"><Loader /></div>
  if (error || !order) return <div className="container section"><ErrorBox message={error ?? 'Pedido no encontrado'} /></div>

  async function pay(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const card = String(new FormData(e.currentTarget).get('card') ?? '').replace(/\s/g, '')
    setBusy(true)
    setPayError(null)
    try {
      setData(await api<Order>(`/orders/${orderId}/pay`, {
        method: 'POST',
        json: { payment_method: method, card_number: method === 'card' ? card : null },
      }))
    } catch (err) {
      setPayError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function cancel() {
    setData(await api<Order>(`/orders/${orderId}/cancel`, { method: 'POST' }))
  }

  const expired = order.status === 'pending' && remaining === 0

  return (
    <>
      <PageHero kicker={`Pedido #${order.id}`} title={order.status === 'paid' ? '¡Nos vemos en la plaza!' : 'Finalizar compra'} />
      <section className="section">
        <div className="container checkout">
          <div className="summary">
            <h2>{order.festival_name}</h2>
            <ul>
              {order.items.map((i) => (
                <li key={i.id}><span>{i.quantity} × {i.ticket_type_name}</span><span>{euros(Number(i.unit_price) * i.quantity)}</span></li>
              ))}
              {Number(order.discount_amount) > 0 && <li className="ok-text"><span>Descuento</span><span>−{euros(order.discount_amount)}</span></li>}
              <li className="summary-total"><span>Total</span><strong>{euros(order.total)}</strong></li>
            </ul>
            <p className="muted">Estado: {ORDER_STATUS[order.status]}</p>
          </div>

          {order.status === 'paid' ? (
            <div className="pay-done">
              <div className="check-icon" aria-hidden="true">✓</div>
              <p>Pago confirmado. Referencia <code>{order.payment_reference}</code>.</p>
              <p className="muted">Tus entradas con QR ya están en tu cuenta.</p>
              <Link to="/mi-cuenta" className="btn btn-accent btn-lg">Ver mis entradas</Link>
            </div>
          ) : order.status !== 'pending' || expired ? (
            <div className="pay-done">
              <p>{expired ? 'La reserva ha caducado y las entradas se han liberado.' : `Este pedido está ${ORDER_STATUS[order.status].toLowerCase()}.`}</p>
              <Link to="/programacion" className="btn btn-ghost">Volver a la programación</Link>
            </div>
          ) : (
            <form className="pay-form" onSubmit={pay}>
              <p className={`timer ${remaining < 120 ? 'is-urgent' : ''}`}>
                Reserva activa durante <strong>{Math.floor(remaining / 60)}:{String(remaining % 60).padStart(2, '0')}</strong>
              </p>
              <div className="chips" role="radiogroup" aria-label="Método de pago">
                {(['card', 'bizum', 'paypal'] as const).map((m) => (
                  <button type="button" key={m} role="radio" aria-checked={method === m}
                    className={`chip ${method === m ? 'is-active' : ''}`} onClick={() => setMethod(m)}>
                    {{ card: 'Tarjeta', bizum: 'Bizum', paypal: 'PayPal' }[m]}
                  </button>
                ))}
              </div>
              {method === 'card' && (
                <label>
                  Número de tarjeta
                  <input name="card" inputMode="numeric" required pattern="[0-9 ]{12,23}" placeholder="4242 4242 4242 4242" autoComplete="cc-number" />
                </label>
              )}
              <p className="muted small">Pago simulado de demostración: una tarjeta acabada en 0000 se rechaza.</p>
              {payError && <p className="form-error">{payError}</p>}
              <button className="btn btn-accent btn-block btn-lg" disabled={busy}>{busy ? 'Procesando…' : `Pagar ${euros(order.total)}`}</button>
              <button type="button" className="btn btn-link" onClick={cancel}>Cancelar pedido</button>
            </form>
          )}
        </div>
      </section>
    </>
  )
}

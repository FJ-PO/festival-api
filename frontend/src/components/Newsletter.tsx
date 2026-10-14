import { useState, type FormEvent } from 'react'
import { api } from '../lib/api'

export default function Newsletter() {
  const [state, setState] = useState<'idle' | 'sending' | 'done' | 'error'>('idle')
  const [message, setMessage] = useState('')

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setState('sending')
    try {
      const r = await api<{ detail: string }>('/newsletter', {
        method: 'POST',
        json: { email: form.get('email'), name: form.get('name') || null },
      })
      setMessage(r.detail)
      setState('done')
    } catch (err) {
      setMessage((err as Error).message)
      setState('error')
    }
  }

  return (
    <section className="newsletter">
      <div className="container newsletter-inner">
        <div>
          <p className="kicker">Newsletter</p>
          <h2>¡Lo último de la plaza, antes que nadie!</h2>
          <p className="muted">Confirmaciones, preventas y sorpresas. Sin spam.</p>
        </div>
        {state === 'done' ? (
          <p className="newsletter-ok">{message}</p>
        ) : (
          <form onSubmit={submit} className="newsletter-form">
            <input name="name" placeholder="Nombre" aria-label="Nombre" autoComplete="given-name" />
            <input name="email" type="email" required placeholder="Email" aria-label="Email" autoComplete="email" />
            <button className="btn btn-accent" disabled={state === 'sending'}>
              {state === 'sending' ? 'Enviando…' : 'Suscribirme'}
            </button>
            {state === 'error' && <p className="form-error">{message}</p>}
          </form>
        )}
      </div>
    </section>
  )
}

import { useRef, useState, type FormEvent } from 'react'
import { Card, PageHeader } from '../components/ui'
import { api } from '../lib/api'
import type { CheckInResult, Festival, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'

/** Control de acceso en puerta: se escribe o escanea (lector de códigos) el código del QR. */
export default function Checkin() {
  const festivals = useFetch<PageOf<Festival>>('/festivals?limit=100&include_past=true')
  const [festivalId, setFestivalId] = useState('')
  const [result, setResult] = useState<CheckInResult | null>(null)
  const [history, setHistory] = useState<CheckInResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const input = useRef<HTMLInputElement>(null)

  async function submit(e: FormEvent<HTMLFormElement>, validate: boolean) {
    e.preventDefault()
    const code = input.current?.value.trim()
    if (!code) return
    setError(null)
    try {
      const r = validate
        ? await api<CheckInResult>('/checkin', { method: 'POST', json: { code, festival_id: festivalId ? Number(festivalId) : null } })
        : await api<CheckInResult>(`/checkin/${encodeURIComponent(code)}${festivalId ? `?festival_id=${festivalId}` : ''}`)
      setResult(r)
      if (validate) setHistory((h) => [r, ...h].slice(0, 15))
      if (input.current) input.current.value = ''
    } catch (err) {
      setError((err as Error).message)
    }
    input.current?.focus()
  }

  return (
    <>
      <PageHeader title="Control de acceso" subtitle="Escanea o escribe el código de la entrada. «Validar» la marca como usada." />
      <div className="grid-2-1">
        <Card>
          <form className="checkin-form" onSubmit={(e) => submit(e, true)}>
            <label className="field">
              <span className="field-label">Puerta de la noche</span>
              <select value={festivalId} onChange={(e) => setFestivalId(e.target.value)}>
                <option value="">Cualquier noche</option>
                {festivals.data?.items.map((f) => <option key={f.id} value={f.id}>{f.start_date} · {f.name}</option>)}
              </select>
            </label>
            <input ref={input} className="code-input" placeholder="CÓDIGO DE LA ENTRADA" autoFocus autoComplete="off"
              onInput={(e) => (e.currentTarget.value = e.currentTarget.value.toUpperCase())} />
            <div className="form-actions">
              <button type="button" className="btn btn-secondary" onClick={(e) => submit(e as unknown as FormEvent<HTMLFormElement>, false)}>Solo comprobar</button>
              <button className="btn btn-primary">Validar entrada</button>
            </div>
          </form>
          {error && <div className="alert alert-error">{error}</div>}
          {result && (
            <div className={`checkin-result ${result.accepted ? 'is-ok' : 'is-ko'}`} role="status">
              <strong>{result.accepted ? '✓ ACCESO PERMITIDO' : '✕ ACCESO DENEGADO'}</strong>
              <p>{result.message}</p>
              {result.ticket && <p className="small">{result.ticket.festival_name} · {result.ticket.ticket_type_name} · {result.ticket.attendee_name}</p>}
            </div>
          )}
        </Card>
        <Card title="Últimas validaciones">
          {history.length === 0 ? <p className="muted">Aún no se ha validado ninguna entrada.</p> : (
            <ul className="history">
              {history.map((h, i) => (
                <li key={i} className={h.accepted ? 'ok' : 'ko'}>
                  <span>{h.accepted ? '✓' : '✕'}</span>
                  <div><strong>{h.ticket?.attendee_name ?? 'Desconocida'}</strong><small>{h.message}</small></div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  )
}

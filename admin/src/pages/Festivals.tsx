import { useState } from 'react'
import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import { Badge, Empty, ErrorBox, Loader, PageHeader } from '../components/ui'
import { mediaUrl } from '../lib/api'
import { dateRange, euros, FESTIVAL_STATUS } from '../lib/format'
import type { Festival, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function Festivals() {
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const { data, error, loading } = useFetch<PageOf<Festival>>(`/festivals/manage?limit=100${status ? `&status=${status}` : ''}`)
  const items = (data?.items ?? [])
    .filter((f) => f.name.toLowerCase().includes(q.toLowerCase()))
    .sort((a, b) => a.start_date.localeCompare(b.start_date))

  return (
    <>
      <PageHeader title="Noches" subtitle="Cada noche del ciclo es un evento con su cartel, sus entradas y sus pedidos."
        actions={<Link to="/festivales/nuevo" className="btn btn-primary"><Icon name="plus" /> Nueva noche</Link>} />
      <div className="toolbar">
        <div className="segmented">
          {['', 'published', 'draft', 'cancelled', 'finished'].map((s) => (
            <button key={s} className={status === s ? 'is-active' : ''} onClick={() => setStatus(s)}>
              {s ? FESTIVAL_STATUS[s] : 'Todas'}
            </button>
          ))}
        </div>
        <input type="search" placeholder="Buscar…" value={q} onChange={(e) => setQ(e.target.value)} className="search" />
      </div>
      {loading && <Loader />}
      {error && <ErrorBox message={error} />}
      {data && items.length === 0 && <Empty>No hay noches con este filtro.</Empty>}
      {items.length > 0 && (
        <div className="table-wrap card">
          <table className="table table-hover">
            <thead><tr><th /><th>Nombre</th><th>Fecha</th><th>Género</th><th>Desde</th><th>Estado</th><th /></tr></thead>
            <tbody>
              {items.map((f) => (
                <tr key={f.id}>
                  <td className="thumb-cell">{f.image_url ? <img src={mediaUrl(f.image_url)} alt="" className="thumb" /> : <span className="thumb thumb-empty">{f.name[0]}</span>}</td>
                  <td><Link to={`/festivales/${f.id}`} className="row-title">{f.name}</Link><div className="muted small">{f.venue.name}</div></td>
                  <td className="nowrap">{dateRange(f.start_date, f.end_date)}</td>
                  <td>{f.genre}</td>
                  <td>{f.price_from ? euros(f.price_from) : '—'}</td>
                  <td><Badge value={f.status} /></td>
                  <td className="right"><Link to={`/festivales/${f.id}`} className="btn btn-secondary btn-sm"><Icon name="edit" /> Editar</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

import { useState } from 'react'
import Icon from '../components/Icon'
import { Empty, Loader, PageHeader } from '../components/ui'
import { api } from '../lib/api'
import { utcToLocal } from '../lib/format'
import type { PageOf, Subscriber } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function Newsletter() {
  const [q, setQ] = useState('')
  const { data, loading, reload } = useFetch<PageOf<Subscriber>>(`/newsletter?limit=500${q ? `&q=${encodeURIComponent(q)}` : ''}`)

  function exportCsv() {
    const rows = [['email', 'nombre', 'fecha'], ...(data?.items ?? []).map((s) => [s.email, s.name ?? '', s.created_at])]
    const csv = rows.map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(',')).join('\n')
    const url = URL.createObjectURL(new Blob([String.fromCharCode(0xfeff) + csv], { type: 'text/csv;charset=utf-8' }))
    const a = Object.assign(document.createElement('a'), { href: url, download: 'suscriptores.csv' })
    a.click()
    URL.revokeObjectURL(url)
  }

  async function remove(s: Subscriber) {
    if (!confirm(`¿Dar de baja a ${s.email}?`)) return
    await api(`/newsletter/${s.id}`, { method: 'DELETE' })
    reload()
  }

  return (
    <>
      <PageHeader title="Newsletter" subtitle={`${data?.total ?? 0} suscriptores`}
        actions={<button className="btn btn-secondary" onClick={exportCsv} disabled={!data?.items.length}>Exportar CSV</button>} />
      <div className="toolbar"><input type="search" className="search" placeholder="Buscar email…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
      {loading && <Loader />}
      {data && data.items.length === 0 && <Empty>Todavía no hay suscriptores.</Empty>}
      {data && data.items.length > 0 && (
        <div className="table-wrap card">
          <table className="table">
            <thead><tr><th>Email</th><th>Nombre</th><th>Fecha</th><th /></tr></thead>
            <tbody>
              {data.items.map((s) => (
                <tr key={s.id}>
                  <td>{s.email}</td><td>{s.name ?? '—'}</td><td>{utcToLocal(s.created_at)}</td>
                  <td className="right"><button className="btn btn-danger-ghost btn-sm" onClick={() => remove(s)} aria-label="Dar de baja"><Icon name="trash" /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

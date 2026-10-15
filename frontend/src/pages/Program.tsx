import { useSearchParams } from 'react-router-dom'
import NightCard from '../components/NightCard'
import { Empty, ErrorBox, Loader, PageHero } from '../components/ui'
import { shortTown } from '../lib/format'
import type { Festival, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'

const MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

export default function Program() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const genre = params.get('genre') ?? ''
  const municipality = params.get('municipality') ?? ''
  const query = new URLSearchParams({ limit: '100' })
  if (q) query.set('q', q)
  if (genre) query.set('genre', genre)
  if (municipality) query.set('municipality', municipality)
  const { data, error, loading, reload } = useFetch<PageOf<Festival>>(`/festivals?${query}`)
  const all = useFetch<PageOf<Festival>>('/festivals?limit=100')
  const genres = [...new Set((all.data?.items ?? []).map((f) => f.genre).filter(Boolean))] as string[]
  const towns = [...new Set((all.data?.items ?? []).map((f) => f.venue.municipality))]

  const byMonth = new Map<string, Festival[]>()
  for (const f of data?.items ?? []) {
    const key = f.start_date.slice(0, 7)
    byMonth.set(key, [...(byMonth.get(key) ?? []), f])
  }

  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  return (
    <>
      <PageHero kicker="Algeciras · La Línea · Los Barrios" title="Programación">
        <div className="filters">
          <input type="search" placeholder="Buscar artista…" defaultValue={q} aria-label="Buscar artista"
            onChange={(e) => update('q', e.target.value)} />
          <div className="chips" aria-label="Plaza">
            <button className={`chip ${!municipality ? 'is-active' : ''}`} onClick={() => update('municipality', '')}>Todas las plazas</button>
            {towns.map((t) => (
              <button key={t} className={`chip ${municipality === t ? 'is-active' : ''}`} onClick={() => update('municipality', t)}>{shortTown(t)}</button>
            ))}
          </div>
          <div className="chips" aria-label="Género">
            <button className={`chip ${!genre ? 'is-active' : ''}`} onClick={() => update('genre', '')}>Todo</button>
            {genres.map((g) => (
              <button key={g} className={`chip ${genre === g ? 'is-active' : ''}`} onClick={() => update('genre', g)}>{g}</button>
            ))}
          </div>
        </div>
      </PageHero>
      <section className="section">
        <div className="container">
          {loading && <Loader />}
          {error && <ErrorBox message={error} onRetry={reload} />}
          {data && data.items.length === 0 && <Empty>No hay noches que coincidan con tu búsqueda.</Empty>}
          {[...byMonth.entries()].map(([month, items]) => (
            <div key={month} className="month-block">
              <h2 className="month-title">
                {MONTHS[Number(month.slice(5)) - 1]} <span>{month.slice(0, 4)}</span>
              </h2>
              <div className="grid-nights">
                {items.map((f) => <NightCard key={f.id} festival={f} />)}
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  )
}

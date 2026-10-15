import { Link } from 'react-router-dom'
import Poster from '../components/Poster'
import { ErrorBox, Loader, PageHero } from '../components/ui'
import { dayNumber, shortMonth, shortTown } from '../lib/format'
import type { Festival, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'

/** Artistas del cartel, a partir de las noches publicadas (cada noche tiene su cabeza de cartel). */
export default function Artists() {
  const { data, error, loading, reload } = useFetch<PageOf<Festival>>('/festivals?limit=100')
  // Un artista puede actuar en varias plazas: se agrupan sus noches
  const groups = [...(data?.items ?? []).reduce((map, f) => map.set(f.name, [...(map.get(f.name) ?? []), f]), new Map<string, Festival[]>())]
  return (
    <>
      <PageHero kicker="Cartel 2027" title="Artistas" />
      <section className="section">
        <div className="container">
          {loading && <Loader />}
          {error && <ErrorBox message={error} onRetry={reload} />}
          <div className="grid-artists">
            {groups.map(([name, nights]) => (
              <Link key={name} to={`/festivales/${nights[0].slug}`} className="artist-card">
                <Poster name={name} image={nights[0].image_url} plain />
                <div className="artist-overlay">
                  <span className="tag">{nights[0].genre}</span>
                  <h3>{name}</h3>
                  {nights.map((f) => (
                    <span key={f.id} className="artist-date">
                      {dayNumber(f.start_date)} {shortMonth(f.start_date)} · {shortTown(f.venue.municipality)}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}

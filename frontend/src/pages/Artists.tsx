import { Link } from 'react-router-dom'
import Poster from '../components/Poster'
import { ErrorBox, Loader, PageHero } from '../components/ui'
import { dayNumber, shortMonth } from '../lib/format'
import type { Festival, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'

/** Artistas del cartel, a partir de las noches publicadas (cada noche tiene su cabeza de cartel). */
export default function Artists() {
  const { data, error, loading, reload } = useFetch<PageOf<Festival>>('/festivals?limit=100')
  return (
    <>
      <PageHero kicker="Cartel 2027" title="Artistas" />
      <section className="section">
        <div className="container">
          {loading && <Loader />}
          {error && <ErrorBox message={error} onRetry={reload} />}
          <div className="grid-artists">
            {data?.items.map((f) => (
              <Link key={f.id} to={`/festivales/${f.slug}`} className="artist-card">
                <Poster name={f.name} image={f.image_url} />
                <div className="artist-overlay">
                  <span className="tag">{f.genre}</span>
                  <h3>{f.name}</h3>
                  <span>{dayNumber(f.start_date)} {shortMonth(f.start_date)}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}

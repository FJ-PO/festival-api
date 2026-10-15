import { Link } from 'react-router-dom'
import { dayNumber, shortMonth, shortTown } from '../lib/format'
import type { Festival, PageOf, Venue } from '../lib/types'
import { useFetch } from '../lib/useFetch'

/** Tarjetas de las plazas del ciclo con su aforo, número de noches y la próxima fecha. */
export default function Plazas({ nights }: { nights: Festival[] }) {
  const venues = useFetch<PageOf<Venue>>('/venues?limit=100')
  const withNights = (venues.data?.items ?? [])
    .map((v) => ({ venue: v, nights: nights.filter((f) => f.venue.id === v.id) }))
    .filter((v) => v.nights.length > 0)

  return (
    <div className="plazas">
      {withNights.map(({ venue, nights }) => {
        const next = nights[0]
        return (
          <Link key={venue.id} to={`/programacion?municipality=${encodeURIComponent(venue.municipality)}`} className="plaza-card">
            <div className="plaza-ring" aria-hidden="true">
              <div>
                <strong>{nights.length}</strong>
                <span>{nights.length === 1 ? 'noche' : 'noches'}</span>
              </div>
            </div>
            <div className="plaza-body">
              <p className="kicker">{shortTown(venue.municipality)}</p>
              <h3>{venue.name}</h3>
              <p className="muted">Aforo {venue.capacity.toLocaleString('es-ES')} personas</p>
              <p className="plaza-next">
                Próxima: <strong>{next.name}</strong> · {dayNumber(next.start_date)} {shortMonth(next.start_date)}
              </p>
              <span className="night-cta">Ver sus noches →</span>
            </div>
          </Link>
        )
      })}
    </div>
  )
}

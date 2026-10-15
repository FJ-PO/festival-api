import { Link } from 'react-router-dom'
import { dayNumber, euros, parts, shortMonth, shortTown } from '../lib/format'
import type { Festival } from '../lib/types'
import Poster from './Poster'

const WEEKDAY = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb']

/** Tarjeta de una noche del ciclo (un festival de la API). */
export default function NightCard({ festival }: { festival: Festival }) {
  const soldOut = festival.status === 'published' && festival.price_from === null
  return (
    <Link to={`/festivales/${festival.slug}`} className="night-card">
      <div className="night-media">
        <Poster name={festival.name} image={festival.image_url} />
        <div className="night-date">
          <span>{WEEKDAY[parts(festival.start_date).weekday]}</span>
          <strong>{String(dayNumber(festival.start_date)).padStart(2, '0')}</strong>
          <span>{shortMonth(festival.start_date)}</span>
        </div>
        {festival.genre && <span className="tag night-genre">{festival.genre}</span>}
        <span className="tag night-town">{shortTown(festival.venue.municipality)}</span>
      </div>
      <div className="night-body">
        <h3>{festival.name}</h3>
        <p className="muted">{festival.venue.name}</p>
        <div className="night-foot">
          {festival.status === 'cancelled' ? (
            <span className="tag tag-danger">Cancelado</span>
          ) : soldOut ? (
            <span className="tag">Agotado</span>
          ) : (
            <span>
              Desde <strong>{festival.price_from ? euros(festival.price_from) : '—'}</strong>
            </span>
          )}
          <span className="night-cta">Entradas →</span>
        </div>
      </div>
    </Link>
  )
}

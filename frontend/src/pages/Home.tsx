import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import NightCard from '../components/NightCard'
import Poster from '../components/Poster'
import { ErrorBox, Loader } from '../components/ui'
import { mediaUrl } from '../lib/api'
import { dateRange, euros, longDay, utcToLocal } from '../lib/format'
import { useSite } from '../lib/site'
import type { Festival, PageOf, Post } from '../lib/types'
import { useFetch } from '../lib/useFetch'

function useCountdown(target: string | undefined) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  if (!target) return null
  // El espectáculo empieza a las 22:00 hora de Algeciras
  const diff = new Date(`${target}T22:00:00`).getTime() - now
  if (diff <= 0) return null
  const s = Math.floor(diff / 1000)
  return { d: Math.floor(s / 86400), h: Math.floor((s % 86400) / 3600), m: Math.floor((s % 3600) / 60), s: s % 60 }
}

export default function Home() {
  const { settings } = useSite()
  const nights = useFetch<PageOf<Festival>>('/festivals?limit=100')
  const posts = useFetch<PageOf<Post>>('/posts?limit=3')
  const [filter, setFilter] = useState<'all' | 'music' | 'humor'>('all')

  const all = useMemo(() => nights.data?.items ?? [], [nights.data])
  const featured = all.find((f) => f.id === settings?.featured_festival_id) ?? all[0]
  const countdown = useCountdown(featured?.start_date)
  const shown = all.filter((f) => filter === 'all' || (filter === 'humor') === (f.genre === 'Humor')).slice(0, 8)
  const heroImage = mediaUrl(settings?.hero_image_url)

  return (
    <>
      <section className="hero">
        {heroImage && <img className="hero-bg" src={heroImage} alt="" />}
        <div className="hero-rings" aria-hidden="true">
          <span /><span /><span /><span />
        </div>
        <div className="container hero-inner">
          <div className="hero-copy">
            <p className="kicker">{settings?.hero_kicker}</p>
            <h1 className="display">{settings?.hero_title}</h1>
            <p className="lead">{settings?.hero_subtitle}</p>
            <div className="hero-actions">
              <Link to={settings?.hero_cta_link ?? '/programacion'} className="btn btn-accent btn-lg">
                {settings?.hero_cta_text ?? 'Ver programación'}
              </Link>
              <Link to="/p/info-de-interes" className="btn btn-ghost btn-lg">Info de interés</Link>
            </div>
          </div>
          {featured && (
            <Link to={`/festivales/${featured.slug}`} className="hero-feature">
              <Poster name={featured.name} image={featured.image_url} wide />
              <div className="hero-feature-body">
                <span className="tag tag-accent">Próxima noche</span>
                <h2>{featured.name}</h2>
                <p>{longDay(featured.start_date)} · 22:00</p>
                {countdown && (
                  <div className="countdown" aria-label="Cuenta atrás">
                    {(['d', 'h', 'm', 's'] as const).map((k) => (
                      <div key={k}>
                        <strong>{String(countdown[k]).padStart(2, '0')}</strong>
                        <span>{{ d: 'días', h: 'horas', m: 'min', s: 'seg' }[k]}</span>
                      </div>
                    ))}
                  </div>
                )}
                {featured.price_from && <p className="muted">Entradas desde {euros(featured.price_from)}</p>}
              </div>
            </Link>
          )}
        </div>
      </section>

      {all.length > 0 && (
        <section className="lineup-poster" aria-labelledby="cartel">
          <div className="container">
            <h2 id="cartel" className="section-label">El cartel</h2>
            <p className="lineup-names">
              {all.map((f, i) => (
                <span key={f.id}>
                  <Link to={`/festivales/${f.slug}`} className={i < 6 ? 'big' : f.genre === 'Humor' ? 'humor' : ''}>
                    {f.name}
                  </Link>
                  {i < all.length - 1 && <i aria-hidden="true">●</i>}
                </span>
              ))}
            </p>
            <p className="muted lineup-dates">
              {dateRange(all[0].start_date, all[all.length - 1].end_date)} · Un sábado, una estrella
            </p>
          </div>
        </section>
      )}

      <section className="section">
        <div className="container">
          <div className="section-head">
            <div>
              <p className="kicker">Programación</p>
              <h2 className="h-section">Próximas noches</h2>
            </div>
            <div className="chips" role="tablist" aria-label="Filtrar">
              {([['all', 'Todo'], ['music', 'Música'], ['humor', 'Humor']] as const).map(([key, label]) => (
                <button key={key} role="tab" aria-selected={filter === key} className={`chip ${filter === key ? 'is-active' : ''}`}
                  onClick={() => setFilter(key)}>{label}</button>
              ))}
            </div>
          </div>
          {nights.loading && <Loader />}
          {nights.error && <ErrorBox message={nights.error} onRetry={nights.reload} />}
          <div className="grid-nights">
            {shown.map((f) => <NightCard key={f.id} festival={f} />)}
          </div>
          <div className="center"><Link to="/programacion" className="btn btn-ghost">Ver toda la programación</Link></div>
        </div>
      </section>

      <section className="section venue">
        <div className="container venue-inner">
          <div className="venue-ring" aria-hidden="true">
            <div><strong>{all[0]?.venue.capacity?.toLocaleString('es-ES') ?? '6.000'}</strong><span>personas</span></div>
          </div>
          <div>
            <p className="kicker">El recinto</p>
            <h2 className="h-section">{settings?.about_title ?? 'Plaza de Toros de Algeciras'}</h2>
            <p className="lead">{settings?.about_text}</p>
            <ul className="venue-facts">
              <li><strong>Pista</strong><span>De pie, en el ruedo</span></li>
              <li><strong>Grada</strong><span>Asiento numerado</span></li>
              <li><strong>Front Stage</strong><span>Junto al escenario</span></li>
            </ul>
            <Link to="/p/como-llegar" className="btn btn-ghost">Cómo llegar</Link>
          </div>
        </div>
      </section>

      {posts.data && posts.data.items.length > 0 && (
        <section className="section">
          <div className="container">
            <div className="section-head">
              <div>
                <p className="kicker">Actualidad</p>
                <h2 className="h-section">Noticias</h2>
              </div>
              <Link to="/noticias" className="link-arrow">Todas las noticias →</Link>
            </div>
            <div className="grid-posts">
              {posts.data.items.map((p) => (
                <Link key={p.id} to={`/noticias/${p.slug}`} className="post-card">
                  <Poster name={p.title} image={p.cover_image_url} className="post-cover" wide />
                  <div>
                    <time className="muted">{p.published_at && utcToLocal(p.published_at, false)}</time>
                    <h3>{p.title}</h3>
                    {p.excerpt && <p className="muted">{p.excerpt}</p>}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  )
}

import { Link } from 'react-router-dom'
import { useSite } from '../lib/site'
import Logo from './Logo'
import Newsletter from './Newsletter'
import { SocialIcon } from './SocialIcon'

export default function Footer() {
  const { settings, menuPages } = useSite()
  const social = Object.entries(settings?.social ?? {}).filter(([, url]) => url) as [string, string][]

  return (
    <footer className="site-footer">
      <Newsletter />
      <div className="container footer-grid">
        <div>
          <Logo name={settings?.site_name ?? 'Las Palomas Festival'} />
          <p className="muted footer-tagline">{settings?.tagline}</p>
          {social.length > 0 && (
            <ul className="social">
              {social.map(([network, url]) => (
                <li key={network}>
                  <a href={url} target="_blank" rel="noreferrer noopener" aria-label={network}>
                    <SocialIcon network={network} />
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <h4>Festival</h4>
          <ul>
            <li><Link to="/programacion">Programación</Link></li>
            <li><Link to="/artistas">Artistas</Link></li>
            <li><Link to="/noticias">Noticias</Link></li>
            {menuPages.map((p) => <li key={p.id}><Link to={`/p/${p.slug}`}>{p.title}</Link></li>)}
          </ul>
        </div>
        <div>
          <h4>Tu cuenta</h4>
          <ul>
            <li><Link to="/mi-cuenta">Mis entradas</Link></li>
            <li><Link to="/mi-cuenta/pedidos">Mis pedidos</Link></li>
            <li><Link to="/registro">Crear cuenta</Link></li>
          </ul>
        </div>
        <div>
          <h4>Contacto</h4>
          <ul>
            {settings?.contact_email && <li><a href={`mailto:${settings.contact_email}`}>{settings.contact_email}</a></li>}
            {settings?.contact_phone && <li><a href={`tel:${settings.contact_phone}`}>{settings.contact_phone}</a></li>}
            <li className="muted">Plaza de Toros de Algeciras</li>
          </ul>
        </div>
      </div>
      <div className="container footer-bottom">
        <span>{settings?.footer_text}</span>
        <span>
          <Link to="/p/aviso-legal">Aviso legal y privacidad</Link> · Esta web no usa cookies
        </span>
      </div>
    </footer>
  )
}

import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { useSite } from '../lib/site'
import Logo from './Logo'
import Marquee from './Marquee'

export default function Header() {
  const { settings, menuPages } = useSite()
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setOpen(false)
  }, [location.pathname, location.search])
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  useEffect(() => {
    document.body.classList.toggle('menu-open', open)
  }, [open])

  return (
    <>
      {settings?.announcement && <Marquee text={settings.announcement} />}
      <header className={`site-header ${scrolled ? 'is-scrolled' : ''}`}>
        <div className="container header-inner">
          <Link to="/" className="brand" aria-label="Inicio">
            <Logo name={settings?.site_name ?? 'Las Palomas Festival'} />
          </Link>
          <nav className={`main-nav ${open ? 'is-open' : ''}`} aria-label="Principal">
            <NavLink to="/" end>Inicio</NavLink>
            <NavLink to="/programacion">Programación</NavLink>
            <NavLink to="/artistas">Artistas</NavLink>
            <NavLink to="/noticias">Noticias</NavLink>
            {menuPages.map((p) => (
              <NavLink key={p.id} to={`/p/${p.slug}`}>{p.title}</NavLink>
            ))}
            <span className="nav-sep" />
            {user ? (
              <NavLink to="/mi-cuenta" className="nav-account">Mi cuenta</NavLink>
            ) : (
              <NavLink to="/login" className="nav-account">Entrar</NavLink>
            )}
            <Link to="/programacion" className="btn btn-accent btn-sm">Entradas</Link>
          </nav>
          <button
            className={`burger ${open ? 'is-open' : ''}`}
            aria-label={open ? 'Cerrar menú' : 'Abrir menú'}
            aria-expanded={open}
            onClick={() => setOpen((o) => !o)}
          >
            <span /><span /><span />
          </button>
        </div>
      </header>
    </>
  )
}

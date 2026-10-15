import { useEffect, useState, type ReactNode } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { ROLE } from '../lib/format'
import type { Role } from '../lib/types'
import Icon from './Icon'

const PUBLIC_SITE = import.meta.env.VITE_PUBLIC_SITE ?? 'http://localhost:5173'

const NAV: { group: string; items: { to: string; label: string; icon: string; roles: Role[] }[] }[] = [
  {
    group: '',
    items: [{ to: '/', label: 'Escritorio', icon: 'dashboard', roles: ['admin', 'organizer'] }],
  },
  {
    group: 'Programación',
    items: [
      { to: '/festivales', label: 'Noches', icon: 'festival', roles: ['admin', 'organizer'] },
      { to: '/artistas', label: 'Artistas', icon: 'artist', roles: ['admin', 'organizer'] },
      { to: '/recintos', label: 'Recintos', icon: 'venue', roles: ['admin', 'organizer'] },
      { to: '/puerta', label: 'Control de acceso', icon: 'scan', roles: ['admin', 'organizer', 'staff'] },
    ],
  },
  {
    group: 'Contenido',
    items: [
      { to: '/paginas', label: 'Páginas', icon: 'page', roles: ['admin'] },
      { to: '/noticias', label: 'Noticias', icon: 'post', roles: ['admin'] },
      { to: '/medios', label: 'Medios', icon: 'media', roles: ['admin', 'organizer'] },
    ],
  },
  {
    group: 'Administración',
    items: [
      { to: '/usuarios', label: 'Usuarios', icon: 'users', roles: ['admin'] },
      { to: '/newsletter', label: 'Newsletter', icon: 'mail', roles: ['admin'] },
      { to: '/ajustes', label: 'Apariencia y ajustes', icon: 'settings', roles: ['admin'] },
    ],
  },
]

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const location = useLocation()
  useEffect(() => {
    setOpen(false)
  }, [location.pathname])

  if (!user) return null
  return (
    <div className={`shell ${open ? 'nav-open' : ''}`}>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <svg viewBox="0 0 40 40" aria-hidden="true">
            <circle cx="20" cy="20" r="16" fill="none" stroke="currentColor" strokeWidth="3" />
            <circle cx="20" cy="20" r="8" fill="var(--accent)" />
          </svg>
          <div>
            <strong>Las Palomas</strong>
            <span>Panel de administración</span>
          </div>
        </div>
        <nav>
          {NAV.map((section) => {
            const items = section.items.filter((i) => i.roles.includes(user.role))
            if (!items.length) return null
            return (
              <div key={section.group} className="nav-group">
                {section.group && <p className="nav-title">{section.group}</p>}
                {items.map((i) => (
                  <NavLink key={i.to} to={i.to} end={i.to === '/'}>
                    <Icon name={i.icon} /> {i.label}
                  </NavLink>
                ))}
              </div>
            )
          })}
        </nav>
        <div className="sidebar-foot">
          <a href={PUBLIC_SITE} target="_blank" rel="noreferrer"><Icon name="external" /> Ver la web</a>
        </div>
      </aside>
      <div className="backdrop" onClick={() => setOpen(false)} />
      <div className="main">
        <header className="topbar">
          <button className="icon-btn burger" onClick={() => setOpen(true)} aria-label="Abrir menú"><Icon name="menu" /></button>
          <div className="topbar-spacer" />
          <NavLink to="/perfil" className="user-chip">
            <span className="avatar">{user.full_name[0]}</span>
            <span><strong>{user.username ?? user.full_name}</strong><small>{ROLE[user.role]}</small></span>
          </NavLink>
          <button className="icon-btn" onClick={logout} title="Cerrar sesión" aria-label="Cerrar sesión"><Icon name="logout" /></button>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  )
}

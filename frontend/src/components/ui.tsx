import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export function Loader({ label = 'Cargando…' }: { label?: string }) {
  return (
    <div className="loader" role="status">
      <span className="spinner" aria-hidden="true" />
      {label}
    </div>
  )
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error-box" role="alert">
      <p>{message}</p>
      {onRetry && <button className="btn btn-ghost btn-sm" onClick={onRetry}>Reintentar</button>}
    </div>
  )
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>
}

export function PageHero({ kicker, title, children }: { kicker?: string; title: string; children?: ReactNode }) {
  return (
    <section className="page-hero">
      <div className="container">
        {kicker && <p className="kicker">{kicker}</p>}
        <h1>{title}</h1>
        {children}
      </div>
    </section>
  )
}

export function BackLink({ to, children }: { to: string; children: ReactNode }) {
  return <Link to={to} className="back-link">← {children}</Link>
}

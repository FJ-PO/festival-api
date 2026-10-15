import { useEffect, useRef, type ReactNode } from 'react'
import { FESTIVAL_STATUS, ORDER_STATUS } from '../lib/format'

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

export function Card({ title, actions, children, className = '' }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="card-head">
          {title && <h2>{title}</h2>}
          {actions}
        </header>
      )}
      <div className="card-body">{children}</div>
    </section>
  )
}

export function Loader() {
  return <div className="loader"><span className="spinner" /> Cargando…</div>
}

export function ErrorBox({ message }: { message: string }) {
  return <div className="alert alert-error" role="alert">{message}</div>
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>
}

const BADGE: Record<string, string> = {
  published: 'green', paid: 'green', valid: 'green', true: 'green',
  draft: 'grey', pending: 'amber', expired: 'grey', used: 'blue', finished: 'blue',
  cancelled: 'red', refunded: 'red', false: 'red',
}

export function Badge({ value, label }: { value: string; label?: string }) {
  const text = label ?? FESTIVAL_STATUS[value] ?? ORDER_STATUS[value] ?? value
  return <span className={`badge badge-${BADGE[value] ?? 'grey'}`}>{text}</span>
}

export function Modal({ title, onClose, children, wide = false }: { title: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    ref.current?.querySelector<HTMLElement>('input, textarea, select, button')?.focus()
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title} ref={ref}>
        <header className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Cerrar">✕</button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}

export function Field({ label, hint, children, span = 1 }: { label: string; hint?: string; children: ReactNode; span?: 1 | 2 }) {
  return (
    <label className={`field ${span === 2 ? 'span-2' : ''}`}>
      <span className="field-label">{label}</span>
      {children}
      {hint && <small className="muted">{hint}</small>}
    </label>
  )
}

export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="switch">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="switch-track" aria-hidden="true" />
      {label}
    </label>
  )
}

import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import { Badge, Card, ErrorBox, Loader, PageHeader } from '../components/ui'
import { useAuth } from '../lib/auth'
import { euros, FESTIVAL_STATUS, ROLE, utcToLocal } from '../lib/format'
import type { Dashboard as DashboardData } from '../lib/types'
import { useFetch } from '../lib/useFetch'

function SalesChart({ points }: { points: DashboardData['sales_last_30_days'] }) {
  const max = Math.max(...points.map((p) => Number(p.revenue)), 1)
  const W = 600
  const H = 160
  const bw = W / points.length
  return (
    <svg viewBox={`0 0 ${W} ${H + 24}`} className="chart" role="img" aria-label="Ventas de los últimos 30 días">
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <line key={f} x1="0" x2={W} y1={H - H * f} y2={H - H * f} className="chart-grid" />
      ))}
      {points.map((p, i) => {
        const h = (Number(p.revenue) / max) * (H - 8)
        return (
          <g key={p.day}>
            <rect x={i * bw + 3} y={H - h} width={bw - 6} height={Math.max(h, 1.5)} rx="3" className={Number(p.revenue) ? 'chart-bar' : 'chart-bar-empty'}>
              <title>{`${p.day}: ${euros(p.revenue)} · ${p.orders} pedidos`}</title>
            </rect>
            {i % 5 === 2 && <text x={i * bw + bw / 2} y={H + 18} className="chart-label" textAnchor="middle">{p.day.slice(8)}/{p.day.slice(5, 7)}</text>}
          </g>
        )
      })}
    </svg>
  )
}

export default function Dashboard() {
  const { user, can } = useAuth()
  const { data, error, loading } = useFetch<DashboardData>('/admin/dashboard')
  if (loading) return <Loader />
  if (error || !data) return <ErrorBox message={error ?? 'Sin datos'} />

  const monthRevenue = data.sales_last_30_days.reduce((s, p) => s + Number(p.revenue), 0)
  const kpis = [
    { label: 'Ingresos totales', value: euros(data.revenue), icon: 'euro', hint: `${euros(monthRevenue)} en 30 días` },
    { label: 'Entradas vendidas', value: data.tickets_sold.toLocaleString('es-ES'), icon: 'ticket', hint: `${data.tickets_checked_in} validadas en puerta` },
    { label: 'Pedidos pagados', value: data.orders_paid.toLocaleString('es-ES'), icon: 'check', hint: 'Desde el inicio' },
    { label: 'Noches publicadas', value: data.festivals_by_status.published, icon: 'festival', hint: `${data.festivals_by_status.draft} en borrador` },
  ]

  return (
    <>
      <PageHeader title={`Hola, ${user?.full_name.split(' ')[0]}`} subtitle="Resumen de la actividad de Las Palomas Festival" actions={
        <Link to="/festivales/nuevo" className="btn btn-primary"><Icon name="plus" /> Nueva noche</Link>
      } />
      <div className="kpis">
        {kpis.map((k) => (
          <div key={k.label} className="kpi">
            <span className="kpi-icon"><Icon name={k.icon} size={20} /></span>
            <div>
              <p className="kpi-label">{k.label}</p>
              <p className="kpi-value">{k.value}</p>
              <p className="kpi-hint">{k.hint}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="grid-2-1">
        <Card title="Ventas · últimos 30 días">
          <SalesChart points={data.sales_last_30_days} />
        </Card>
        <Card title="Noches por estado">
          <ul className="stat-list">
            {Object.entries(data.festivals_by_status).map(([k, v]) => (
              <li key={k}><Badge value={k} label={FESTIVAL_STATUS[k]} /><strong>{v}</strong></li>
            ))}
          </ul>
          <ul className="stat-list stat-list-plain">
            <li><span>Artistas</span><strong>{data.artists}</strong></li>
            <li><span>Recintos</span><strong>{data.venues}</strong></li>
            {can('admin') && <li><span>Páginas</span><strong>{data.pages}</strong></li>}
            {can('admin') && <li><span>Noticias</span><strong>{data.posts}</strong></li>}
          </ul>
        </Card>
      </div>
      <div className="grid-2-1">
        <Card title="Últimos pedidos">
          {data.recent_orders.length === 0 ? <p className="muted">Todavía no hay pedidos.</p> : (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>#</th><th>Noche</th><th>Cliente</th><th>Fecha</th><th>Total</th><th>Estado</th></tr></thead>
                <tbody>
                  {data.recent_orders.map((o) => (
                    <tr key={o.id}>
                      <td>{o.id}</td><td>{o.festival_name}</td><td>{o.customer}</td>
                      <td className="nowrap">{utcToLocal(o.created_at)}</td><td>{euros(o.total)}</td><td><Badge value={o.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
        {can('admin') ? (
          <Card title="Usuarios">
            <ul className="stat-list stat-list-plain">
              {Object.entries(data.users_by_role).map(([k, v]) => <li key={k}><span>{ROLE[k]}</span><strong>{v}</strong></li>)}
            </ul>
            <Link to="/usuarios" className="btn btn-secondary btn-sm">Gestionar usuarios</Link>
          </Card>
        ) : <div />}
      </div>
    </>
  )
}

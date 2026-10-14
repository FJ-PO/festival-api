import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { Loader } from './components/ui'
import { useAuth } from './lib/auth'
import type { Role } from './lib/types'
import Artists from './pages/Artists'
import Checkin from './pages/Checkin'
import { ContentEdit, ContentList } from './pages/Content'
import Dashboard from './pages/Dashboard'
import FestivalEdit from './pages/FestivalEdit'
import Festivals from './pages/Festivals'
import Login from './pages/Login'
import Media from './pages/Media'
import Newsletter from './pages/Newsletter'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import Users from './pages/Users'
import Venues from './pages/Venues'

function Only({ roles, children }: { roles: Role[]; children: React.ReactElement }) {
  const { can } = useAuth()
  return can(...roles) ? children : <Navigate to="/" replace />
}

export default function App() {
  const { user, ready } = useAuth()
  if (!ready) return <div className="login-screen"><Loader /></div>
  if (!user) return <Login />

  const managers: Role[] = ['admin', 'organizer']
  return (
    <Layout>
      <Routes>
        <Route path="/" element={user.role === 'staff' ? <Navigate to="/puerta" replace /> : <Dashboard />} />
        <Route path="/festivales" element={<Only roles={managers}><Festivals /></Only>} />
        <Route path="/festivales/:id" element={<Only roles={managers}><FestivalEdit /></Only>} />
        <Route path="/artistas" element={<Only roles={managers}><Artists /></Only>} />
        <Route path="/recintos" element={<Only roles={managers}><Venues /></Only>} />
        <Route path="/puerta" element={<Checkin />} />
        <Route path="/paginas" element={<Only roles={['admin']}><ContentList kind="paginas" /></Only>} />
        <Route path="/paginas/:id" element={<Only roles={['admin']}><ContentEdit kind="paginas" /></Only>} />
        <Route path="/noticias" element={<Only roles={['admin']}><ContentList kind="noticias" /></Only>} />
        <Route path="/noticias/:id" element={<Only roles={['admin']}><ContentEdit kind="noticias" /></Only>} />
        <Route path="/medios" element={<Only roles={managers}><Media /></Only>} />
        <Route path="/usuarios" element={<Only roles={['admin']}><Users /></Only>} />
        <Route path="/newsletter" element={<Only roles={['admin']}><Newsletter /></Only>} />
        <Route path="/ajustes" element={<Only roles={['admin']}><Settings /></Only>} />
        <Route path="/perfil" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

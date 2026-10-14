import { useEffect } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import Footer from './components/Footer'
import Header from './components/Header'
import { PageHero } from './components/ui'
import Account from './pages/Account'
import Artists from './pages/Artists'
import { Login, Register } from './pages/Auth'
import Checkout from './pages/Checkout'
import FestivalPage from './pages/Festival'
import Home from './pages/Home'
import { CmsPageView, NewsDetail, NewsList } from './pages/News'
import PlazasPage from './pages/PlazasPage'
import Program from './pages/Program'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function NotFound() {
  return (
    <PageHero kicker="Error 404" title="Esta página no está en el cartel">
      <Link to="/" className="btn btn-accent">Volver al inicio</Link>
    </PageHero>
  )
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <a href="#main" className="skip-link">Saltar al contenido</a>
      <Header />
      <main id="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/programacion" element={<Program />} />
          <Route path="/festivales/:slug" element={<FestivalPage />} />
          <Route path="/artistas" element={<Artists />} />
          <Route path="/plazas" element={<PlazasPage />} />
          <Route path="/noticias" element={<NewsList />} />
          <Route path="/noticias/:slug" element={<NewsDetail />} />
          <Route path="/p/:slug" element={<CmsPageView />} />
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Register />} />
          <Route path="/checkout/:orderId" element={<Checkout />} />
          <Route path="/mi-cuenta/*" element={<Account />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </>
  )
}

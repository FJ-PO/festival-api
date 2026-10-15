import Plazas from '../components/Plazas'
import { ErrorBox, Loader, PageHero } from '../components/ui'
import { useSite } from '../lib/site'
import type { Festival, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function PlazasPage() {
  const { settings } = useSite()
  const { data, error, loading, reload } = useFetch<PageOf<Festival>>('/festivals?limit=100')
  return (
    <>
      <PageHero kicker="Las sedes" title="Las plazas">
        <p className="lead">{settings?.about_text}</p>
      </PageHero>
      <section className="section">
        <div className="container">
          {loading && <Loader />}
          {error && <ErrorBox message={error} onRetry={reload} />}
          {data && <Plazas nights={data.items} />}
        </div>
      </section>
    </>
  )
}

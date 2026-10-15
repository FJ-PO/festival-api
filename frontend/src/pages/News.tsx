import { Link, useParams } from 'react-router-dom'
import Markdown from '../components/Markdown'
import Poster from '../components/Poster'
import { BackLink, Empty, ErrorBox, Loader, PageHero } from '../components/ui'
import { utcToLocal } from '../lib/format'
import type { CmsPage, PageOf, Post } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export function NewsList() {
  const { data, error, loading, reload } = useFetch<PageOf<Post>>('/posts?limit=50')
  return (
    <>
      <PageHero kicker="Actualidad" title="Noticias" />
      <section className="section">
        <div className="container">
          {loading && <Loader />}
          {error && <ErrorBox message={error} onRetry={reload} />}
          {data && data.items.length === 0 && <Empty>Todavía no hay noticias.</Empty>}
          <div className="grid-posts">
            {data?.items.map((p) => (
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
    </>
  )
}

function Article({ item, back, backLabel }: { item: Post | CmsPage; back?: string; backLabel?: string }) {
  return (
    <article>
      <PageHero kicker={'published_at' in item && item.published_at && back ? utcToLocal(item.published_at, false) : undefined} title={item.title}>
        {back && <BackLink to={back}>{backLabel}</BackLink>}
        {item.status === 'draft' && <p className="tag">Borrador · vista previa</p>}
      </PageHero>
      <section className="section">
        <div className="container narrow">
          {item.cover_image_url && <Poster name={item.title} image={item.cover_image_url} className="article-cover" wide />}
          {item.excerpt && <p className="lead">{item.excerpt}</p>}
          <Markdown source={item.content} />
        </div>
      </section>
    </article>
  )
}

export function NewsDetail() {
  const { slug } = useParams()
  const { data, error, loading } = useFetch<Post>(`/posts/slug/${slug}`)
  if (loading) return <div className="container section"><Loader /></div>
  if (error || !data) return <div className="container section"><ErrorBox message={error ?? 'Noticia no encontrada'} /></div>
  return <Article item={data} back="/noticias" backLabel="Noticias" />
}

export function CmsPageView() {
  const { slug } = useParams()
  const { data, error, loading } = useFetch<CmsPage>(`/pages/slug/${slug}`)
  if (loading) return <div className="container section"><Loader /></div>
  if (error || !data) return <div className="container section"><ErrorBox message={error ?? 'Página no encontrada'} /></div>
  return <Article item={data} />
}

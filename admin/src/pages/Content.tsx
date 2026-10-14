import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Icon from '../components/Icon'
import MarkdownEditor from '../components/MarkdownEditor'
import { ImageField } from '../components/MediaPicker'
import { Badge, Card, Empty, ErrorBox, Field, Loader, PageHeader, Switch } from '../components/ui'
import { api } from '../lib/api'
import { utcToLocal } from '../lib/format'
import { useToast } from '../lib/toast'
import type { CmsPage, Festival, PageOf, Post } from '../lib/types'
import { useFetch } from '../lib/useFetch'

const PUBLIC_SITE = import.meta.env.VITE_PUBLIC_SITE ?? 'http://localhost:5173'

export type Kind = 'paginas' | 'noticias'
const CFG = {
  paginas: { api: '/pages', title: 'Páginas', one: 'página', publicPath: '/p/' },
  noticias: { api: '/posts', title: 'Noticias', one: 'noticia', publicPath: '/noticias/' },
}

export function ContentList({ kind }: { kind: Kind }) {
  const cfg = CFG[kind]
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const query = new URLSearchParams({ limit: '100' })
  if (status) query.set('status', status)
  if (q) query.set('q', q)
  const { data, loading, error, reload } = useFetch<PageOf<CmsPage & Post>>(`${cfg.api}/manage?${query}`)
  const toast = useToast()

  async function remove(item: CmsPage | Post) {
    if (!confirm(`¿Eliminar «${item.title}»? No se puede deshacer.`)) return
    await api(`${cfg.api}/${item.id}`, { method: 'DELETE' })
    toast('Eliminado')
    reload()
  }

  return (
    <>
      <PageHeader title={cfg.title} actions={<Link to={`/${kind}/nueva`} className="btn btn-primary"><Icon name="plus" /> Añadir {cfg.one}</Link>} />
      <div className="toolbar">
        <div className="segmented">
          {[['', 'Todas'], ['published', 'Publicadas'], ['draft', 'Borradores']].map(([v, l]) => (
            <button key={v} className={status === v ? 'is-active' : ''} onClick={() => setStatus(v)}>{l}</button>
          ))}
        </div>
        <input type="search" className="search" placeholder="Buscar…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {loading && <Loader />}
      {error && <ErrorBox message={error} />}
      {data && data.items.length === 0 && <Empty>No hay {cfg.title.toLowerCase()}.</Empty>}
      {data && data.items.length > 0 && (
        <div className="table-wrap card">
          <table className="table table-hover">
            <thead><tr><th>Título</th>{kind === 'paginas' && <th>Menú</th>}<th>Autor</th><th>Actualizada</th><th>Estado</th><th /></tr></thead>
            <tbody>
              {data.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <Link to={`/${kind}/${item.id}`} className="row-title">{item.title}</Link>
                    <div className="muted small">{cfg.publicPath}{item.slug}</div>
                  </td>
                  {kind === 'paginas' && <td>{item.show_in_menu ? `Sí (${item.menu_order})` : '—'}</td>}
                  <td>{item.author?.full_name ?? '—'}</td>
                  <td className="nowrap">{utcToLocal(item.updated_at)}</td>
                  <td><Badge value={item.status} label={item.status === 'published' ? 'Publicada' : 'Borrador'} /></td>
                  <td className="right nowrap">
                    <Link to={`/${kind}/${item.id}`} className="btn btn-secondary btn-sm"><Icon name="edit" /></Link>{' '}
                    <button className="btn btn-danger-ghost btn-sm" onClick={() => remove(item)}><Icon name="trash" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

interface Draft {
  title: string
  slug: string
  excerpt: string
  content: string
  cover_image_url: string | null
  status: 'draft' | 'published'
  show_in_menu: boolean
  menu_order: number
  festival_id: number | null
}

const EMPTY: Draft = { title: '', slug: '', excerpt: '', content: '', cover_image_url: null, status: 'draft', show_in_menu: false, menu_order: 0, festival_id: null }

export function ContentEdit({ kind }: { kind: Kind }) {
  const cfg = CFG[kind]
  const { id } = useParams()
  const isNew = id === 'nueva'
  const { data, loading, error } = useFetch<CmsPage & Post>(isNew ? null : `${cfg.api}/${id}`)
  const festivals = useFetch<PageOf<Festival>>(kind === 'noticias' ? '/festivals/manage?limit=100' : null)
  const [draft, setDraft] = useState<Draft>(EMPTY)
  const [busy, setBusy] = useState(false)
  const toast = useToast()
  const navigate = useNavigate()

  useEffect(() => {
    if (data) {
      setDraft({
        title: data.title, slug: data.slug, excerpt: data.excerpt ?? '', content: data.content,
        cover_image_url: data.cover_image_url, status: data.status, show_in_menu: data.show_in_menu ?? false,
        menu_order: data.menu_order ?? 0, festival_id: data.festival_id ?? null,
      })
    }
  }, [data])

  if (loading) return <Loader />
  if (error) return <ErrorBox message={error} />

  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setDraft((d) => ({ ...d, [k]: v }))

  async function save(status: Draft['status']) {
    const body: Record<string, unknown> = {
      title: draft.title, slug: draft.slug || null, excerpt: draft.excerpt || null, content: draft.content,
      cover_image_url: draft.cover_image_url, status,
    }
    if (kind === 'paginas') Object.assign(body, { show_in_menu: draft.show_in_menu, menu_order: draft.menu_order })
    else body.festival_id = draft.festival_id
    setBusy(true)
    try {
      const saved = await api<CmsPage>(isNew ? cfg.api : `${cfg.api}/${id}`, { method: isNew ? 'POST' : 'PATCH', json: body })
      setDraft((d) => ({ ...d, slug: saved.slug, status: saved.status }))
      toast(status === 'published' ? 'Publicado' : 'Borrador guardado')
      if (isNew) navigate(`/${kind}/${saved.id}`, { replace: true })
    } catch (e) {
      toast((e as Error).message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title={isNew ? `Añadir ${cfg.one}` : `Editar ${cfg.one}`}
        subtitle={<Link to={`/${kind}`} className="muted">← {cfg.title}</Link>} />
      <div className="editor-layout">
        <div className="editor-main">
          <input className="title-input" placeholder="Añade un título" value={draft.title} onChange={(e) => set('title', e.target.value)} aria-label="Título" />
          {!isNew && <p className="muted small permalink">Enlace permanente: <a href={`${PUBLIC_SITE}${cfg.publicPath}${draft.slug}`} target="_blank" rel="noreferrer">{PUBLIC_SITE}{cfg.publicPath}{draft.slug}</a></p>}
          <MarkdownEditor value={draft.content} onChange={(v) => set('content', v)} />
          <Card title="Extracto">
            <textarea rows={3} value={draft.excerpt} onChange={(e) => set('excerpt', e.target.value)} placeholder="Resumen breve que aparece en listados y buscadores" maxLength={500} />
          </Card>
        </div>
        <div className="editor-side">
          <Card title="Publicar">
            <p className="publish-row">Estado: <Badge value={draft.status} label={draft.status === 'published' ? 'Publicada' : 'Borrador'} /></p>
            {data?.published_at && <p className="muted small">Publicada el {utcToLocal(data.published_at)}</p>}
            <div className="publish-actions">
              <button className="btn btn-secondary" disabled={busy || !draft.title} onClick={() => save('draft')}>
                {draft.status === 'published' ? 'Pasar a borrador' : 'Guardar borrador'}
              </button>
              <button className="btn btn-primary" disabled={busy || !draft.title} onClick={() => save('published')}>
                {draft.status === 'published' ? 'Actualizar' : 'Publicar'}
              </button>
            </div>
            {!isNew && draft.status === 'draft' && (
              <a className="btn btn-link btn-sm" href={`${PUBLIC_SITE}${cfg.publicPath}${draft.slug}`} target="_blank" rel="noreferrer">Vista previa en la web ↗</a>
            )}
          </Card>
          <Card title="Ajustes">
            <Field label="Slug (URL)" hint="Vacío = se genera desde el título">
              <input value={draft.slug} onChange={(e) => set('slug', e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-'))} />
            </Field>
            {kind === 'paginas' ? (
              <>
                <Switch checked={draft.show_in_menu} onChange={(v) => set('show_in_menu', v)} label="Mostrar en el menú" />
                <Field label="Orden en el menú"><input type="number" value={draft.menu_order} onChange={(e) => set('menu_order', Number(e.target.value))} /></Field>
              </>
            ) : (
              <Field label="Noche relacionada">
                <select value={draft.festival_id ?? ''} onChange={(e) => set('festival_id', e.target.value ? Number(e.target.value) : null)}>
                  <option value="">Ninguna</option>
                  {festivals.data?.items.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
                </select>
              </Field>
            )}
          </Card>
          <Card title="Imagen destacada">
            <ImageField value={draft.cover_image_url} onChange={(v) => set('cover_image_url', v)} />
          </Card>
        </div>
      </div>
    </>
  )
}

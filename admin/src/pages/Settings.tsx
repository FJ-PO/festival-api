import { useEffect, useState } from 'react'
import { ImageField } from '../components/MediaPicker'
import { Card, ErrorBox, Field, Loader, PageHeader } from '../components/ui'
import { api } from '../lib/api'
import { useToast } from '../lib/toast'
import type { Festival, PageOf, SiteSettings } from '../lib/types'
import { useFetch } from '../lib/useFetch'

const SOCIAL = ['instagram', 'facebook', 'tiktok', 'youtube', 'x', 'spotify'] as const

/** Apariencia y textos de la web pública (equivalente a "Personalizar" de WordPress). */
export default function Settings() {
  const { data, error, loading } = useFetch<SiteSettings & { updated_at?: string }>('/site')
  const festivals = useFetch<PageOf<Festival>>('/festivals/manage?limit=100')
  const [s, setS] = useState<SiteSettings | null>(null)
  const [busy, setBusy] = useState(false)
  const toast = useToast()

  useEffect(() => {
    if (data) {
      const { updated_at: _ignored, ...rest } = data
      void _ignored
      setS(rest)
    }
  }, [data])

  if (loading || !s) return error ? <ErrorBox message={error} /> : <Loader />
  const set = <K extends keyof SiteSettings>(k: K, v: SiteSettings[K]) => setS({ ...s, [k]: v })
  const text = (k: keyof SiteSettings) => ({
    value: (s[k] as string | null) ?? '',
    onChange: (e: { target: { value: string } }) => set(k, (e.target.value || null) as never),
  })

  async function save() {
    setBusy(true)
    try {
      await api('/site', { method: 'PUT', json: s })
      toast('Ajustes guardados. Recarga la web para ver los cambios.')
    } catch (e) {
      toast((e as Error).message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="Apariencia y ajustes" subtitle="Textos, portada, colores y redes sociales de la web pública"
        actions={<button className="btn btn-primary" onClick={save} disabled={busy}>{busy ? 'Guardando…' : 'Guardar cambios'}</button>} />
      <div className="editor-layout">
        <div className="editor-main">
          <Card title="Identidad">
            <div className="form-grid">
              <Field label="Nombre del sitio"><input {...text('site_name')} required /></Field>
              <Field label="Lema"><input {...text('tagline')} /></Field>
              <Field label="Banda de avisos" hint="Texto animado sobre la cabecera. Vacío = oculta" span={2}><input {...text('announcement')} /></Field>
            </div>
          </Card>
          <Card title="Portada">
            <div className="form-grid">
              <Field label="Antetítulo"><input {...text('hero_kicker')} /></Field>
              <Field label="Noche destacada">
                <select value={s.featured_festival_id ?? ''} onChange={(e) => set('featured_festival_id', e.target.value ? Number(e.target.value) : null)}>
                  <option value="">La próxima automáticamente</option>
                  {festivals.data?.items.filter((f) => f.status === 'published').map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
                </select>
              </Field>
              <Field label="Titular" span={2}><input {...text('hero_title')} /></Field>
              <Field label="Subtítulo" span={2}><textarea rows={2} {...text('hero_subtitle')} /></Field>
              <Field label="Texto del botón"><input {...text('hero_cta_text')} /></Field>
              <Field label="Enlace del botón"><input {...text('hero_cta_link')} /></Field>
              <Field label="Imagen de fondo" span={2}><ImageField value={s.hero_image_url} onChange={(v) => set('hero_image_url', v)} /></Field>
            </div>
          </Card>
          <Card title="Sección «El recinto»">
            <div className="form-grid">
              <Field label="Título" span={2}><input {...text('about_title')} /></Field>
              <Field label="Texto" span={2}><textarea rows={4} {...text('about_text')} /></Field>
            </div>
          </Card>
        </div>
        <div className="editor-side">
          <Card title="Color de marca">
            <div className="color-row">
              <input type="color" value={s.accent_color} onChange={(e) => set('accent_color', e.target.value)} aria-label="Color de acento" />
              <input value={s.accent_color} onChange={(e) => set('accent_color', e.target.value)} pattern="#[0-9a-fA-F]{6}" />
            </div>
            <div className="swatches">
              {['#ff3366', '#ff6b00', '#e6b422', '#00b894', '#3d7bff', '#9b5de5'].map((c) => (
                <button key={c} style={{ background: c }} onClick={() => set('accent_color', c)} aria-label={c} />
              ))}
            </div>
            <div className="accent-preview" style={{ background: s.accent_color }}>Entradas</div>
          </Card>
          <Card title="Contacto">
            <Field label="Email"><input type="email" {...text('contact_email')} /></Field>
            <Field label="Teléfono"><input {...text('contact_phone')} /></Field>
            <Field label="Pie de página"><input {...text('footer_text')} /></Field>
          </Card>
          <Card title="Redes sociales">
            {SOCIAL.map((n) => (
              <Field key={n} label={n === 'x' ? 'X (Twitter)' : n[0].toUpperCase() + n.slice(1)}>
                <input type="url" placeholder="https://" value={s.social[n] ?? ''} onChange={(e) => set('social', { ...s.social, [n]: e.target.value || null })} />
              </Field>
            ))}
          </Card>
        </div>
      </div>
    </>
  )
}

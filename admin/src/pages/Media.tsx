import { useRef, useState, type DragEvent } from 'react'
import Icon from '../components/Icon'
import { Empty, Loader, Modal, PageHeader } from '../components/ui'
import { api, mediaUrl } from '../lib/api'
import { useAuth } from '../lib/auth'
import { uploadFile } from '../lib/media'
import { bytes, utcToLocal } from '../lib/format'
import { useToast } from '../lib/toast'
import type { MediaItem, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function Media() {
  const { data, loading, reload } = useFetch<PageOf<MediaItem>>('/media?limit=100')
  const [selected, setSelected] = useState<MediaItem | null>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(0)
  const input = useRef<HTMLInputElement>(null)
  const toast = useToast()
  const { can } = useAuth()

  async function upload(files: FileList | File[]) {
    const list = Array.from(files)
    setUploading(list.length)
    for (const file of list) {
      try {
        await uploadFile(file)
      } catch (e) {
        toast(`${file.name}: ${(e as Error).message}`, 'error')
      }
      setUploading((n) => n - 1)
    }
    reload()
  }

  function onDrop(e: DragEvent) {
    e.preventDefault()
    setDragging(false)
    upload(e.dataTransfer.files)
  }

  async function saveAlt(alt: string) {
    if (!selected) return
    await api(`/media/${selected.id}`, { method: 'PATCH', json: { alt } })
    toast('Texto alternativo guardado')
    reload()
  }

  async function remove() {
    if (!selected || !confirm('¿Eliminar este archivo? Las páginas que lo usen dejarán de mostrarlo.')) return
    await api(`/media/${selected.id}`, { method: 'DELETE' })
    setSelected(null)
    reload()
  }

  const absolute = (m: MediaItem) => new URL(mediaUrl(m.url)!, location.origin).href

  return (
    <>
      <PageHeader title="Biblioteca de medios" subtitle={`${data?.total ?? 0} archivos`}
        actions={<button className="btn btn-primary" onClick={() => input.current?.click()}><Icon name="upload" /> Subir archivos</button>} />
      <input ref={input} type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,application/pdf" hidden onChange={(e) => e.target.files && upload(e.target.files)} />
      <div className={`dropzone ${dragging ? 'is-dragging' : ''}`} onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)} onDrop={onDrop} onClick={() => input.current?.click()} role="button" tabIndex={0}>
        <Icon name="upload" size={28} />
        <p>{uploading ? `Subiendo ${uploading} archivo(s)…` : 'Arrastra aquí tus imágenes o haz clic para elegirlas'}</p>
        <span className="muted small">JPG, PNG, WEBP, GIF o PDF · máx. 8 MB</span>
      </div>
      {loading && <Loader />}
      {data && data.items.length === 0 && <Empty>Aún no hay archivos.</Empty>}
      <div className="media-grid media-grid-lg">
        {data?.items.map((m) => (
          <button key={m.id} className="media-tile" onClick={() => setSelected(m)} title={m.original_name}>
            {m.content_type.startsWith('image/') ? <img src={mediaUrl(m.url)} alt={m.alt ?? ''} loading="lazy" /> : <span className="file-tile">PDF</span>}
          </button>
        ))}
      </div>
      {selected && (
        <Modal title="Detalles del archivo" onClose={() => setSelected(null)} wide>
          <div className="media-detail">
            {selected.content_type.startsWith('image/') ? <img src={mediaUrl(selected.url)} alt={selected.alt ?? ''} /> : <span className="file-tile">PDF</span>}
            <div className="form-stack">
              <dl className="meta">
                <dt>Nombre</dt><dd>{selected.original_name}</dd>
                <dt>Tipo</dt><dd>{selected.content_type}</dd>
                <dt>Tamaño</dt><dd>{bytes(selected.size)}</dd>
                <dt>Subido</dt><dd>{utcToLocal(selected.created_at)}</dd>
              </dl>
              <label className="field">
                <span className="field-label">Texto alternativo</span>
                <input defaultValue={selected.alt ?? ''} onBlur={(e) => e.target.value !== (selected.alt ?? '') && saveAlt(e.target.value)} placeholder="Describe la imagen (accesibilidad)" />
              </label>
              <label className="field">
                <span className="field-label">URL del archivo</span>
                <div className="input-group">
                  <input readOnly value={absolute(selected)} />
                  <button className="btn btn-secondary btn-sm" onClick={() => { navigator.clipboard.writeText(absolute(selected)); toast('URL copiada') }}><Icon name="copy" /></button>
                </div>
              </label>
              {can('admin') && <button className="btn btn-danger-ghost" onClick={remove}><Icon name="trash" /> Eliminar permanentemente</button>}
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}

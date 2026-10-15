import { useRef, useState } from 'react'
import { mediaUrl } from '../lib/api'
import { uploadFile } from '../lib/media'
import type { MediaItem, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'
import { useToast } from '../lib/toast'
import Icon from './Icon'
import { Empty, Loader, Modal } from './ui'

/** Campo de imagen: muestra la imagen elegida y abre la biblioteca de medios para cambiarla. */
export function ImageField({ value, onChange }: { value: string | null | undefined; onChange: (url: string | null) => void }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="image-field">
      {value ? <img src={mediaUrl(value)} alt="" /> : <div className="image-placeholder"><Icon name="media" size={28} /></div>}
      <div className="image-actions">
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => setOpen(true)}>
          {value ? 'Cambiar imagen' : 'Elegir imagen'}
        </button>
        {value && <button type="button" className="btn btn-link btn-sm" onClick={() => onChange(null)}>Quitar</button>}
        <input value={value ?? ''} onChange={(e) => onChange(e.target.value || null)} placeholder="o pega una URL" aria-label="URL de la imagen" />
      </div>
      {open && <MediaPicker onClose={() => setOpen(false)} onSelect={(m) => { onChange(m.url); setOpen(false) }} />}
    </div>
  )
}

export function MediaPicker({ onClose, onSelect }: { onClose: () => void; onSelect: (m: MediaItem) => void }) {
  const { data, loading, reload } = useFetch<PageOf<MediaItem>>('/media?limit=100')
  const input = useRef<HTMLInputElement>(null)
  const toast = useToast()
  const [busy, setBusy] = useState(false)

  async function upload(files: FileList | null) {
    if (!files?.length) return
    setBusy(true)
    try {
      const m = await uploadFile(files[0])
      reload()
      onSelect(m)
    } catch (e) {
      toast((e as Error).message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Biblioteca de medios" onClose={onClose} wide>
      <div className="picker-toolbar">
        <button className="btn btn-primary" onClick={() => input.current?.click()} disabled={busy}>
          <Icon name="upload" /> {busy ? 'Subiendo…' : 'Subir archivo'}
        </button>
        <input ref={input} type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden onChange={(e) => upload(e.target.files)} />
        <span className="muted">JPG, PNG, WEBP o GIF · máx. 8 MB</span>
      </div>
      {loading && <Loader />}
      {data && data.items.length === 0 && <Empty>La biblioteca está vacía. Sube la primera imagen.</Empty>}
      <div className="media-grid">
        {data?.items.filter((m) => m.content_type.startsWith('image/')).map((m) => (
          <button key={m.id} className="media-tile" onClick={() => onSelect(m)} title={m.original_name}>
            <img src={mediaUrl(m.url)} alt={m.alt ?? ''} loading="lazy" />
          </button>
        ))}
      </div>
    </Modal>
  )
}

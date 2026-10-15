import { useState, type FormEvent } from 'react'
import Icon from '../components/Icon'
import { ImageField } from '../components/MediaPicker'
import { Empty, Field, Loader, Modal, PageHeader } from '../components/ui'
import { api, mediaUrl } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useToast } from '../lib/toast'
import type { Artist, PageOf } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function Artists() {
  const [q, setQ] = useState('')
  const { data, loading, reload } = useFetch<PageOf<Artist>>(`/artists?limit=100${q ? `&q=${encodeURIComponent(q)}` : ''}`)
  const [editing, setEditing] = useState<Artist | 'new' | null>(null)
  const { can } = useAuth()
  const toast = useToast()

  async function remove(a: Artist) {
    if (!confirm(`¿Eliminar a ${a.name}?`)) return
    try {
      await api(`/artists/${a.id}`, { method: 'DELETE' })
      toast('Artista eliminado')
      reload()
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  return (
    <>
      <PageHeader title="Artistas" subtitle={`${data?.total ?? 0} artistas y humoristas`}
        actions={<button className="btn btn-primary" onClick={() => setEditing('new')}><Icon name="plus" /> Añadir artista</button>} />
      <div className="toolbar"><input type="search" className="search" placeholder="Buscar artista…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
      {loading && <Loader />}
      {data && data.items.length === 0 && <Empty>No hay artistas.</Empty>}
      <div className="artist-grid">
        {data?.items.map((a) => (
          <article key={a.id} className="artist-tile card">
            {a.image_url ? <img src={mediaUrl(a.image_url)} alt="" /> : <div className="artist-initial">{a.name[0]}</div>}
            <div className="artist-tile-body">
              <strong>{a.name}</strong>
              <span className="muted small">{[a.genre, a.country].filter(Boolean).join(' · ')}</span>
              <div className="row-actions">
                <button className="btn btn-secondary btn-sm" onClick={() => setEditing(a)}><Icon name="edit" /> Editar</button>
                {can('admin') && <button className="btn btn-danger-ghost btn-sm" onClick={() => remove(a)}><Icon name="trash" /></button>}
              </div>
            </div>
          </article>
        ))}
      </div>
      {editing && <ArtistModal artist={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload() }} />}
    </>
  )
}

function ArtistModal({ artist, onClose, onSaved }: { artist: Artist | null; onClose: () => void; onSaved: () => void }) {
  const [image, setImage] = useState(artist?.image_url ?? null)
  const toast = useToast()
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    const body = { name: f.get('name'), genre: f.get('genre') || null, country: f.get('country') || null, bio: f.get('bio') || null, image_url: image }
    try {
      await api(artist ? `/artists/${artist.id}` : '/artists', { method: artist ? 'PATCH' : 'POST', json: body })
      toast('Artista guardado')
      onSaved()
    } catch (err) {
      toast((err as Error).message, 'error')
    }
  }
  return (
    <Modal title={artist ? `Editar ${artist.name}` : 'Nuevo artista'} onClose={onClose} wide>
      <form onSubmit={submit} className="form-grid">
        <Field label="Nombre"><input name="name" defaultValue={artist?.name} required /></Field>
        <Field label="Género"><input name="genre" defaultValue={artist?.genre ?? ''} /></Field>
        <Field label="Procedencia"><input name="country" defaultValue={artist?.country ?? ''} /></Field>
        <div />
        <Field label="Biografía" span={2}><textarea name="bio" rows={4} defaultValue={artist?.bio ?? ''} /></Field>
        <Field label="Foto" span={2}><ImageField value={image} onChange={setImage} /></Field>
        <div className="form-actions span-2">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary">Guardar</button>
        </div>
      </form>
    </Modal>
  )
}

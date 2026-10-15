import { useState, type FormEvent } from 'react'
import Icon from '../components/Icon'
import { Card, Empty, Field, Loader, Modal, PageHeader } from '../components/ui'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useToast } from '../lib/toast'
import type { PageOf, Venue } from '../lib/types'
import { useFetch } from '../lib/useFetch'

export default function Venues() {
  const { data, loading, reload } = useFetch<PageOf<Venue>>('/venues?limit=100')
  const municipalities = useFetch<string[]>('/venues/municipalities')
  const [editing, setEditing] = useState<Venue | 'new' | null>(null)
  const { can } = useAuth()
  const toast = useToast()

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    const num = (k: string) => (f.get(k) ? Number(f.get(k)) : null)
    const body = { name: f.get('name'), address: f.get('address'), municipality: f.get('municipality'), capacity: Number(f.get('capacity')), latitude: num('latitude'), longitude: num('longitude') }
    const current = editing === 'new' ? null : editing
    try {
      await api(current ? `/venues/${current.id}` : '/venues', { method: current ? 'PATCH' : 'POST', json: body })
      toast('Recinto guardado')
      setEditing(null)
      reload()
    } catch (err) {
      toast((err as Error).message, 'error')
    }
  }

  async function remove(v: Venue) {
    if (!confirm(`¿Eliminar ${v.name}?`)) return
    try {
      await api(`/venues/${v.id}`, { method: 'DELETE' })
      reload()
    } catch (e) {
      toast((e as Error).message, 'error')
    }
  }

  const current = editing === 'new' ? null : editing
  return (
    <>
      <PageHeader title="Recintos" actions={<button className="btn btn-primary" onClick={() => setEditing('new')}><Icon name="plus" /> Añadir recinto</button>} />
      {loading && <Loader />}
      {data && data.items.length === 0 && <Empty>No hay recintos.</Empty>}
      <div className="venue-list">
        {data?.items.map((v) => (
          <Card key={v.id} title={v.name} actions={
            <div className="row-actions">
              {can('admin') && <button className="btn btn-secondary btn-sm" onClick={() => setEditing(v)}><Icon name="edit" /> Editar</button>}
              {can('admin') && <button className="btn btn-danger-ghost btn-sm" onClick={() => remove(v)}><Icon name="trash" /></button>}
            </div>
          }>
            <p>{v.address}<br /><span className="muted">{v.municipality}</span></p>
            <p className="muted small">Aforo: {v.capacity.toLocaleString('es-ES')} personas</p>
          </Card>
        ))}
      </div>
      {editing && (
        <Modal title={current ? `Editar ${current.name}` : 'Nuevo recinto'} onClose={() => setEditing(null)}>
          <form onSubmit={submit} className="form-grid">
            <Field label="Nombre" span={2}><input name="name" defaultValue={current?.name} required /></Field>
            <Field label="Dirección" span={2}><input name="address" defaultValue={current?.address} required /></Field>
            <Field label="Municipio">
              <select name="municipality" defaultValue={current?.municipality ?? 'Algeciras'}>
                {municipalities.data?.map((m) => <option key={m}>{m}</option>)}
              </select>
            </Field>
            <Field label="Aforo"><input name="capacity" type="number" min={1} defaultValue={current?.capacity} required /></Field>
            <Field label="Latitud"><input name="latitude" type="number" step="any" defaultValue={current?.latitude ?? ''} /></Field>
            <Field label="Longitud"><input name="longitude" type="number" step="any" defaultValue={current?.longitude ?? ''} /></Field>
            <div className="form-actions span-2">
              <button type="button" className="btn btn-secondary" onClick={() => setEditing(null)}>Cancelar</button>
              <button className="btn btn-primary">Guardar</button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}

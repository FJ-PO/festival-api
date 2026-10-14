import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { useMemo, useRef, useState } from 'react'
import { MediaPicker } from './MediaPicker'

const TOOLS: { label: string; title: string; wrap?: [string, string]; line?: string }[] = [
  { label: 'H2', title: 'Título', line: '## ' },
  { label: 'H3', title: 'Subtítulo', line: '### ' },
  { label: 'B', title: 'Negrita', wrap: ['**', '**'] },
  { label: 'I', title: 'Cursiva', wrap: ['*', '*'] },
  { label: '• Lista', title: 'Lista', line: '- ' },
  { label: '1. Lista', title: 'Lista numerada', line: '1. ' },
  { label: '❝', title: 'Cita', line: '> ' },
  { label: 'Enlace', title: 'Enlace', wrap: ['[', '](https://)'] },
]

/** Editor de contenido estilo WordPress: barra de herramientas + Markdown + vista previa. */
export default function MarkdownEditor({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const area = useRef<HTMLTextAreaElement>(null)
  const [tab, setTab] = useState<'write' | 'preview' | 'split'>('split')
  const [picker, setPicker] = useState(false)
  const html = useMemo(() => DOMPurify.sanitize(marked.parse(value || '', { async: false }) as string), [value])

  function apply(tool: (typeof TOOLS)[number] | { wrap: [string, string]; line?: undefined }) {
    const el = area.current
    if (!el) return
    const { selectionStart: s, selectionEnd: e } = el
    let next: string
    let cursor: number
    if (tool.wrap) {
      const [a, b] = tool.wrap
      next = value.slice(0, s) + a + value.slice(s, e) + b + value.slice(e)
      cursor = e + a.length + b.length
    } else {
      const lineStart = value.lastIndexOf('\n', s - 1) + 1
      next = value.slice(0, lineStart) + tool.line + value.slice(lineStart)
      cursor = e + tool.line!.length
    }
    onChange(next)
    requestAnimationFrame(() => {
      el.focus()
      el.setSelectionRange(cursor, cursor)
    })
  }

  return (
    <div className="md-editor">
      <div className="md-toolbar">
        {TOOLS.map((t) => (
          <button type="button" key={t.label} title={t.title} onClick={() => apply(t)} disabled={tab === 'preview'}>{t.label}</button>
        ))}
        <button type="button" title="Insertar imagen" onClick={() => setPicker(true)} disabled={tab === 'preview'}>Imagen</button>
        <span className="md-spacer" />
        {(['write', 'split', 'preview'] as const).map((t) => (
          <button type="button" key={t} className={tab === t ? 'is-active' : ''} onClick={() => setTab(t)}>
            {{ write: 'Escribir', split: 'Dividido', preview: 'Vista previa' }[t]}
          </button>
        ))}
      </div>
      <div className={`md-panes md-${tab}`}>
        {tab !== 'preview' && (
          <textarea ref={area} value={value} onChange={(e) => onChange(e.target.value)} spellCheck
            placeholder="Escribe aquí el contenido. Admite Markdown: ## títulos, **negrita**, listas, enlaces…" />
        )}
        {tab !== 'write' && <div className="md-preview prose" dangerouslySetInnerHTML={{ __html: html || '<p class="muted">Vista previa</p>' }} />}
      </div>
      {picker && (
        <MediaPicker onClose={() => setPicker(false)} onSelect={(m) => {
          apply({ wrap: [`![${m.alt ?? ''}](${m.url}`, ')'] })
          setPicker(false)
        }} />
      )}
    </div>
  )
}

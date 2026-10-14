import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { useMemo } from 'react'

/** Renderiza el Markdown del CMS saneado con DOMPurify (evita XSS aunque el contenido lo edite un admin). */
export default function Markdown({ source, className = 'prose' }: { source: string; className?: string }) {
  const html = useMemo(() => DOMPurify.sanitize(marked.parse(source, { async: false }) as string), [source])
  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />
}

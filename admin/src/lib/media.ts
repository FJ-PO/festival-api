import { api } from './api'
import type { MediaItem } from './types'

export async function uploadFile(file: File, alt?: string) {
  const body = new FormData()
  body.append('file', file)
  if (alt) body.append('alt', alt)
  return api<MediaItem>('/media', { method: 'POST', body })
}

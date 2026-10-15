import { useCallback, useEffect, useState } from 'react'
import { api } from './api'

/** Carga un recurso de la API y expone loading / error / reload. `path = null` no hace nada. */
export function useFetch<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(Boolean(path))
  const [tick, setTick] = useState(0)

  useEffect(() => {
    if (!path) return
    let alive = true
    setLoading(true)
    setError(null)
    api<T>(path)
      .then((d) => alive && setData(d))
      .catch((e: Error) => alive && setError(e.message))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [path, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { data, error, loading, reload, setData }
}

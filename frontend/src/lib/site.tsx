import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from './api'
import type { CmsPage, PageOf, SiteSettings } from './types'

interface SiteState {
  settings: SiteSettings | null
  menuPages: CmsPage[]
  municipalities: string[]
}

const SiteContext = createContext<SiteState>({ settings: null, menuPages: [], municipalities: [] })

export function SiteProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SiteState>({ settings: null, menuPages: [], municipalities: [] })

  useEffect(() => {
    Promise.all([
      api<SiteSettings>('/site'),
      api<PageOf<CmsPage>>('/pages?menu=true&limit=10').then((p) => p.items).catch(() => []),
      api<string[]>('/venues/municipalities').catch(() => []),
    ])
      .then(([settings, menuPages, municipalities]) => {
        setState({ settings, menuPages, municipalities })
        document.documentElement.style.setProperty('--accent', settings.accent_color)
        document.title = `${settings.site_name} · ${settings.tagline}`
      })
      .catch(() => setState((s) => s))
  }, [])

  return <SiteContext.Provider value={state}>{children}</SiteContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useSite = () => useContext(SiteContext)

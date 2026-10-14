const ICONS: Record<string, string> = {
  dashboard: 'M3 13h8V3H3zm0 8h8v-6H3zm10 0h8V11h-8zm0-18v6h8V3z',
  festival: 'M12 2 2 7l10 5 10-5zm-8 9v6l8 4 8-4v-6l-8 4z',
  artist: 'M12 3a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm0 10c4.4 0 8 1.8 8 4v3H4v-3c0-2.2 3.6-4 8-4z',
  venue: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 4a6 6 0 1 1 0 12 6 6 0 0 1 0-12zm0 3a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  page: 'M6 2h9l5 5v15H6zm8 1.5V8h4.5M9 12h8M9 16h8',
  post: 'M4 4h16v4H4zm0 6h10v10H4zm12 0h4v4h-4zm0 6h4v4h-4z',
  media: 'M4 5h16v14H4zm2 12h12l-4-5-3 4-2-2z',
  users: 'M9 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm8 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM1 20c0-3 3.6-5 8-5s8 2 8 5zm17 0c0-1.6-.6-3-1.8-4 3 .3 5.8 1.6 5.8 4z',
  mail: 'M3 5h18v14H3zm1.5 1.5L12 12l7.5-5.5',
  scan: 'M3 3h6v2H5v4H3zm12 0h6v6h-2V5h-4zM3 15h2v4h4v2H3zm16 0h2v6h-6v-2h4zM7 11h10v2H7z',
  settings: 'M19.4 13a7.5 7.5 0 0 0 0-2l2.1-1.6-2-3.5-2.5 1a7 7 0 0 0-1.7-1L15 3h-4l-.4 2.9a7 7 0 0 0-1.7 1l-2.5-1-2 3.5L6.6 11a7.5 7.5 0 0 0 0 2l-2.1 1.6 2 3.5 2.5-1a7 7 0 0 0 1.7 1L11 21h4l.4-2.9a7 7 0 0 0 1.7-1l2.5 1 2-3.5zM13 15.5a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7z',
  external: 'M14 3h7v7h-2V6.4l-9.3 9.3-1.4-1.4L17.6 5H14zM5 5h6v2H5v12h12v-6h2v8H3V5z',
  logout: 'M10 3H4v18h6v-2H6V5h4zm6 4-1.4 1.4 2.6 2.6H9v2h8.2l-2.6 2.6L16 17l5-5z',
  plus: 'M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6z',
  trash: 'M9 3h6l1 2h4v2H4V5h4zm-3 6h12l-1 12H7z',
  edit: 'M4 17.2V20h2.8l8.3-8.3-2.8-2.8zM19.7 7.3a1 1 0 0 0 0-1.4l-1.6-1.6a1 1 0 0 0-1.4 0l-1.3 1.3 2.8 2.8z',
  copy: 'M8 8h12v12H8zM4 4h12v2H6v10H4z',
  menu: 'M3 6h18v2H3zm0 5h18v2H3zm0 5h18v2H3z',
  upload: 'M12 3l5 5h-3v6h-4V8H7zM5 18h14v2H5z',
  euro: 'M15 4c2 0 3.5.6 4.5 1.5l-1.4 1.6A5 5 0 0 0 15 6a5 5 0 0 0-4.6 3H15v2H9.9v2H15v2h-4.6A5 5 0 0 0 15 18c1.2 0 2.3-.4 3.1-1.1l1.4 1.6C18.5 19.4 17 20 15 20a7 7 0 0 1-6.7-5H5v-2h3v-2H5V9h3.3A7 7 0 0 1 15 4z',
  ticket: 'M3 7a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-3a2 2 0 0 0 0-4z',
  check: 'M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z',
}

export default function Icon({ name, size = 18 }: { name: string; size?: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="currentColor" aria-hidden="true" className="icon">
      <path d={ICONS[name] ?? ICONS.page} fillRule="evenodd" />
    </svg>
  )
}

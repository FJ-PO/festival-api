import { mediaUrl } from '../lib/api'

/** Paletas de cartel. Se elige una de forma estable a partir del nombre. */
const PALETTES = [
  ['#ff3366', '#5b2bff'],
  ['#ff8a00', '#e5007e'],
  ['#00c2a8', '#1a3cff'],
  ['#ffd23f', '#ff3d00'],
  ['#b620e0', '#ff5470'],
  ['#2de2e6', '#7a04eb'],
  ['#f72585', '#3a0ca3'],
  ['#fb5607', '#8338ec'],
]

function hash(text: string) {
  let h = 0
  for (const ch of text) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return h
}

function initials(name: string) {
  return name
    .replace(/&.*/, '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}

/**
 * Imagen del cartel: la foto subida desde el panel o, si no hay, una composición generada
 * (degradado + anillos que evocan el ruedo de la plaza + iniciales).
 */
export default function Poster({ name, image, className = '', wide = false, plain = false }: {
  name: string
  image?: string | null
  className?: string
  /** Formato apaisado (portadas, cabeceras) en lugar de vertical */
  wide?: boolean
  /** Sin iniciales: solo color y anillos (fondos detrás de un titular) */
  plain?: boolean
}) {
  const src = mediaUrl(image)
  if (src) return <img className={`poster ${className}`} src={src} alt={name} loading="lazy" />
  const h = hash(name)
  const [a, b] = PALETTES[h % PALETTES.length]
  const id = `g${h}`
  const rot = h % 360
  const w = wide ? 800 : 400
  return (
    <svg className={`poster ${className}`} viewBox={`0 0 ${w} 500`} role="img" aria-label={name} preserveAspectRatio="xMidYMid slice">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1" gradientTransform={`rotate(${rot % 90} .5 .5)`}>
          <stop offset="0" stopColor={a} />
          <stop offset="1" stopColor={b} />
        </linearGradient>
      </defs>
      <rect width={w} height="500" fill={`url(#${id})`} />
      <g fill="none" stroke="#fff" strokeOpacity=".18">
        {[60, 110, 160, 210, 260].map((r) => (
          <circle key={r} cx={h % 2 ? w - 70 : 70} cy={h % 3 ? 120 : 400} r={r} strokeWidth={r % 100 === 10 ? 14 : 2} />
        ))}
      </g>
      {!plain && <text x="28" y="470" fill="#fff" fillOpacity=".92" fontFamily="Anton, Impact, sans-serif" fontSize="190" letterSpacing="-4">
        {initials(name)}
      </text>}
    </svg>
  )
}

const money = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' })

export const euros = (value: string | number) => money.format(Number(value))

const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
const MONTHS_LONG = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]
const WEEKDAYS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']

/** Fechas "YYYY-MM-DD" sin zona horaria: se leen tal cual, sin conversiones. */
export function parts(isoDate: string) {
  const [y, m, d] = isoDate.slice(0, 10).split('-').map(Number)
  return { y, m, d, weekday: new Date(y, m - 1, d).getDay() }
}

export function dateRange(start: string, end: string): string {
  const a = parts(start)
  const b = parts(end)
  if (start === end) return `${a.d} ${MONTHS_LONG[a.m - 1]} ${a.y}`
  if (a.m === b.m && a.y === b.y) return `${a.d}–${b.d} ${MONTHS_LONG[a.m - 1]} ${a.y}`
  return `${a.d} ${MONTHS[a.m - 1]} – ${b.d} ${MONTHS[b.m - 1]} ${b.y}`
}

export const shortMonth = (iso: string) => MONTHS[parts(iso).m - 1]
export const dayNumber = (iso: string) => parts(iso).d
export const longDay = (iso: string) => {
  const p = parts(iso)
  return `${WEEKDAYS[p.weekday]} ${p.d} de ${MONTHS_LONG[p.m - 1]}`
}

/** Hora "HH:MM" de un datetime del cartel (hora local del festival). */
export const hour = (iso: string) => iso.slice(11, 16)

/** Fecha/hora en UTC (sin "Z" en la API) a texto local del navegador. */
export function utcToLocal(iso: string, withTime = true): string {
  const d = new Date(iso.endsWith('Z') ? iso : `${iso}Z`)
  return d.toLocaleString('es-ES', withTime
    ? { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }
    : { day: 'numeric', month: 'long', year: 'numeric' })
}

export const utcMillis = (iso: string) => new Date(iso.endsWith('Z') ? iso : `${iso}Z`).getTime()

export const ORDER_STATUS: Record<string, string> = {
  pending: 'Pendiente de pago',
  paid: 'Pagado',
  cancelled: 'Cancelado',
  expired: 'Caducado',
  refunded: 'Reembolsado',
}

export const TICKET_STATUS: Record<string, string> = { valid: 'Válida', used: 'Utilizada', cancelled: 'Anulada' }

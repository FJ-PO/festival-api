export default function Logo({ name }: { name: string }) {
  const [first, ...rest] = name.split(' ')
  return (
    <span className="logo">
      <svg viewBox="0 0 40 40" aria-hidden="true">
        <circle cx="20" cy="20" r="17" fill="none" stroke="currentColor" strokeWidth="3" />
        <circle cx="20" cy="20" r="9" fill="var(--accent)" />
      </svg>
      <span className="logo-text">
        <strong>{first} {rest[0] ?? ''}</strong>
        <small>{rest.slice(1).join(' ')}</small>
      </span>
    </span>
  )
}

export default function Marquee({ text }: { text: string }) {
  const items = Array.from({ length: 8 }, (_, i) => (
    <span key={i}>
      {text}
      <i aria-hidden="true">✦</i>
    </span>
  ))
  return (
    <div className="marquee" role="note" aria-label={text}>
      <div className="marquee-track" aria-hidden="true">
        {items}
        {items}
      </div>
    </div>
  )
}

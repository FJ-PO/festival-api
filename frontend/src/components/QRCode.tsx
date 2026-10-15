import QR from 'qrcode'
import { useEffect, useState } from 'react'

export default function QRCode({ value, size = 180 }: { value: string; size?: number }) {
  const [src, setSrc] = useState<string>()
  useEffect(() => {
    QR.toDataURL(value, { width: size * 2, margin: 1, errorCorrectionLevel: 'M' }).then(setSrc)
  }, [value, size])
  return src ? <img src={src} width={size} height={size} alt={`Código QR ${value}`} className="qr" /> : <div className="qr" style={{ width: size, height: size }} />
}

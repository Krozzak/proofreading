// Renders one page of a PDF File onto a canvas (litho viewer + thumbnails).
import { useEffect, useRef, useState } from 'react'
import { renderPdfPage } from '../lib/pdfEngine'

interface Props {
  file: File
  pageNumber: number // 1-based
  maxWidth: number
  className?: string
}

export function PdfCanvas({ file, pageNumber, maxWidth, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    const canvas = canvasRef.current
    if (!canvas) return
    file
      .arrayBuffer()
      .then((buffer) => {
        if (cancelled) return
        return renderPdfPage(buffer, pageNumber, canvas, maxWidth)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })
    return () => {
      cancelled = true
    }
  }, [file, pageNumber, maxWidth])

  if (error) {
    return (
      <div className="flex h-48 items-center justify-center rounded border border-red-200 bg-red-50 text-sm text-red-600">
        Impossible d'afficher le PDF : {error}
      </div>
    )
  }

  return <canvas ref={canvasRef} className={className} />
}

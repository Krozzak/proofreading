/**
 * pdf.js bootstrap for the single-file build.
 *
 * The worker is inlined into the bundle (`?worker&inline` → base64 → Blob URL)
 * so the app works offline and under file://. If the environment refuses Blob
 * workers, pdf.js falls back to its "fake worker" (main-thread) mode, which is
 * functionally identical, just slower on large PDFs.
 */
import * as pdfjs from 'pdfjs-dist'
// Vite inline worker: no network fetch at runtime, works under file://
// eslint-disable-next-line import/no-unresolved
import PdfWorker from 'pdfjs-dist/build/pdf.worker.mjs?worker&inline'

let initialized = false

function ensureWorker(): void {
  if (initialized) return
  initialized = true
  try {
    pdfjs.GlobalWorkerOptions.workerPort = new PdfWorker()
  } catch {
    // Blob workers blocked (strict corporate policy): let pdf.js use its
    // main-thread fake worker. `workerSrc` must be non-empty for that path.
    pdfjs.GlobalWorkerOptions.workerSrc = 'inline-fallback'
  }
}

export interface PdfPageSize {
  widthMm: number
  heightMm: number
  /**
   * 'trimbox' when a /TrimBox was found in the raw PDF (the finished cut
   * size), 'cropbox' otherwise (page size — may include bleed/marks).
   * True dieline (cut-line) detection is a future feature.
   */
  source: 'trimbox' | 'cropbox'
}

export interface PdfDocumentInfo {
  pageCount: number
  /** Concatenated text of ALL pages (mirrors the desktop PDFProcessor). */
  text: string
  /** First-page dimensions in millimetres, null if unreadable. */
  pageSize: PdfPageSize | null
}

const PT_TO_MM = 25.4 / 72

/**
 * Best-effort /TrimBox scan of the raw PDF bytes. pdf.js does not expose the
 * TrimBox through its public API, but many print PDFs keep the page dict
 * uncompressed, where the box is greppable. Returns [w, h] in points.
 */
function scanTrimBox(data: ArrayBuffer): [number, number] | null {
  // Only decode up to 20 MB to bound the cost on huge files
  const bytes = new Uint8Array(data, 0, Math.min(data.byteLength, 20_000_000))
  let raw = ''
  const CHUNK = 65536
  for (let i = 0; i < bytes.length; i += CHUNK) {
    raw += String.fromCharCode(...bytes.subarray(i, Math.min(i + CHUNK, bytes.length)))
  }
  const match = /\/TrimBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*\]/.exec(raw)
  if (!match) return null
  const [x1, y1, x2, y2] = match.slice(1).map(Number)
  const w = Math.abs(x2 - x1)
  const h = Math.abs(y2 - y1)
  if (!Number.isFinite(w) || !Number.isFinite(h) || w <= 0 || h <= 0) return null
  return [w, h]
}

/** Ligatures and special spaces that PyMuPDF expands but pdf.js may not. */
const LIGATURES: Record<string, string> = {
  'ﬀ': 'ff',
  'ﬁ': 'fi',
  'ﬂ': 'fl',
  'ﬃ': 'ffi',
  'ﬄ': 'ffl',
  'ﬅ': 'st',
  'ﬆ': 'st',
  ' ': ' ',
  '‘': "'",
  '’': "'",
  '“': '"',
  '”': '"',
}

export function normalizeExtractedText(raw: string): string {
  let text = raw.normalize('NFKC')
  for (const [from, to] of Object.entries(LIGATURES)) {
    text = text.replaceAll(from, to)
  }
  return text
}

async function loadDocument(data: ArrayBuffer) {
  ensureWorker()
  return pdfjs.getDocument({ data, useSystemFonts: true }).promise
}

/**
 * Extracts the text of every page, joined with newlines — the web equivalent
 * of the desktop `page.get_text()` loop over all pages.
 */
export async function extractPdfText(data: ArrayBuffer): Promise<PdfDocumentInfo> {
  const trimBoxPt = scanTrimBox(data)
  const doc = await loadDocument(data)
  const parts: string[] = []
  let pageSize: PdfPageSize | null = null
  for (let i = 1; i <= doc.numPages; i++) {
    const page = await doc.getPage(i)
    if (i === 1) {
      // page.view is the CropBox [x1, y1, x2, y2] in PDF units (userUnit × pt)
      const unit = (page.userUnit || 1) * PT_TO_MM
      let [w, h] = trimBoxPt ?? [page.view[2] - page.view[0], page.view[3] - page.view[1]]
      if (page.rotate === 90 || page.rotate === 270) [w, h] = [h, w]
      if (w > 0 && h > 0) {
        pageSize = { widthMm: w * unit, heightMm: h * unit, source: trimBoxPt ? 'trimbox' : 'cropbox' }
      }
    }
    const content = await page.getTextContent()
    let pageText = ''
    for (const item of content.items) {
      if ('str' in item) {
        pageText += item.str
        pageText += item.hasEOL ? '\n' : ' '
      }
    }
    parts.push(pageText)
    page.cleanup()
  }
  const pageCount = doc.numPages
  await doc.destroy()
  return { pageCount, text: normalizeExtractedText(parts.join('\n')), pageSize }
}

/**
 * Renders one page (1-based) to a JPEG base64 string (no data: prefix),
 * capped at maxDim on the longest side — the input format for AI vision.
 */
export async function renderPdfPageToJpeg(
  data: ArrayBuffer,
  pageNumber: number,
  maxDim = 1568,
): Promise<string> {
  const doc = await loadDocument(data)
  try {
    const page = await doc.getPage(pageNumber)
    const base = page.getViewport({ scale: 1 })
    const scale = Math.min(maxDim / Math.max(base.width, base.height), 4)
    const viewport = page.getViewport({ scale })
    const canvas = document.createElement('canvas')
    canvas.width = Math.ceil(viewport.width)
    canvas.height = Math.ceil(viewport.height)
    const ctx = canvas.getContext('2d')!
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    await page.render({ canvasContext: ctx, viewport }).promise
    page.cleanup()
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85)
    return dataUrl.slice(dataUrl.indexOf(',') + 1)
  } finally {
    await doc.destroy()
  }
}

/**
 * Renders one page (1-based) onto a canvas at the given scale.
 * Used for the litho viewer and overview thumbnails.
 */
export async function renderPdfPage(
  data: ArrayBuffer,
  pageNumber: number,
  canvas: HTMLCanvasElement,
  maxWidth: number,
): Promise<void> {
  const doc = await loadDocument(data)
  try {
    const page = await doc.getPage(pageNumber)
    const baseViewport = page.getViewport({ scale: 1 })
    const scale = (maxWidth / baseViewport.width) * (window.devicePixelRatio || 1)
    const viewport = page.getViewport({ scale })
    canvas.width = viewport.width
    canvas.height = viewport.height
    canvas.style.width = `${viewport.width / (window.devicePixelRatio || 1)}px`
    const ctx = canvas.getContext('2d')!
    await page.render({ canvasContext: ctx, viewport }).promise
    page.cleanup()
  } finally {
    await doc.destroy()
  }
}

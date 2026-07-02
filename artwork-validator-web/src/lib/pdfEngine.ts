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

export interface PdfDocumentInfo {
  pageCount: number
  /** Concatenated text of ALL pages (mirrors the desktop PDFProcessor). */
  text: string
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
  const doc = await loadDocument(data)
  const parts: string[] = []
  for (let i = 1; i <= doc.numPages; i++) {
    const page = await doc.getPage(i)
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
  return { pageCount, text: normalizeExtractedText(parts.join('\n')) }
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

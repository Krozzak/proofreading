// Dimension helpers for the "taille du visuel" feature: mm formatting and
// comparison against the expected size configured in Paramètres. The measured
// size comes from the PDF page boxes (TrimBox/CropBox) — real dieline
// (cut-line) detection is a planned follow-up.
import type { PdfPageSize } from './pdfEngine'

export interface ExpectedSize {
  widthMm: number | null
  heightMm: number | null
  toleranceMm: number
}

export const DEFAULT_EXPECTED_SIZE: ExpectedSize = {
  widthMm: null,
  heightMm: null,
  toleranceMm: 2,
}

const STORAGE_KEY = 'avw:ui:expectedSize'

export function loadExpectedSize(): ExpectedSize {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_EXPECTED_SIZE
    const parsed = JSON.parse(raw) as Partial<ExpectedSize>
    return {
      widthMm: typeof parsed.widthMm === 'number' ? parsed.widthMm : null,
      heightMm: typeof parsed.heightMm === 'number' ? parsed.heightMm : null,
      toleranceMm: typeof parsed.toleranceMm === 'number' ? parsed.toleranceMm : 2,
    }
  } catch {
    return DEFAULT_EXPECTED_SIZE
  }
}

export function saveExpectedSize(size: ExpectedSize): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(size))
  } catch {
    // localStorage unavailable (private mode): setting stays session-only
  }
}

function fmtMm(value: number): string {
  return (Math.round(value * 10) / 10).toLocaleString('fr-FR')
}

export function formatPageSize(size: PdfPageSize): string {
  return `${fmtMm(size.widthMm)} × ${fmtMm(size.heightMm)} mm`
}

export function sizeSourceLabel(size: PdfPageSize): string {
  return size.source === 'trimbox' ? 'TrimBox (format fini)' : 'CropBox (taille de page)'
}

/**
 * Compares measured vs expected size, ignoring orientation (a litho scanned
 * in landscape must not fail against a portrait expectation). Returns null
 * when no expectation is configured.
 */
export function checkExpectedSize(size: PdfPageSize, expected: ExpectedSize): boolean | null {
  if (expected.widthMm === null || expected.heightMm === null) return null
  const tol = expected.toleranceMm
  const [mLo, mHi] = [size.widthMm, size.heightMm].sort((a, b) => a - b)
  const [eLo, eHi] = [expected.widthMm, expected.heightMm].sort((a, b) => a - b)
  return Math.abs(mLo - eLo) <= tol && Math.abs(mHi - eHi) <= tol
}

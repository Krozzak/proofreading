// Shared core types (mirrors the implicit dict shapes of the Python code).

/** Raw cell value handed over by the Excel IO adapter (null = empty cell / NaN). */
export type CellValue = string | number | null

/** A sheet as parsed by the IO layer: header row + data rows keyed by column name. */
export interface RawSheet {
  columns: string[]
  rows: Record<string, CellValue>[]
}

/**
 * A row returned by getDataForLitho: numeric cells with integral values are
 * numbers (already int-ified), everything else is a trimmed string, empty = ''.
 */
export type LithoRecord = Record<string, string | number>

export type ValidationStatus = 'pending' | 'approved' | 'rejected'

export interface LithoValidation {
  status: ValidationStatus
  date: string
  comment: string
}

export interface SessionData {
  session_name: string
  pdf_folder: string
  excel_file: string
  last_litho_index: number
  validations: Record<string, LithoValidation>
  created_date: string
  last_updated: string
  session_type: string
  check_digits: boolean
  validation_method: 'legacy' | 'enhanced'
  brand_code: string
  session_version: string
  /**
   * Snapshot of the brand definition when the session uses a custom (non
   * built-in) brand, so an exported session is importable on another machine.
   * Shape: BrandDefinition (validated on import).
   */
  custom_brand?: unknown
}

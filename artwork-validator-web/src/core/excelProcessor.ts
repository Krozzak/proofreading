// Port of core/excel_processor.py (IO-free: consumes a pre-parsed RawSheet;
// the exceljs read adapter lives in src/lib/excelIO.ts).
import type { BrandConfig } from './brandConfigs'
import { mnyConfig } from './brandConfigs'
import type { CellValue, LithoRecord, RawSheet } from './types'

export interface ExcelFormatReport {
  is_valid: boolean
  found_columns: string[]
  missing_columns: string[]
  missing_optional_columns: string[]
  extra_columns: string[]
  total_rows: number
  error_message: string | null
}

export interface DataQualityReport {
  litho_issues: string[]
  upc_issues: number
}

/** pandas.to_numeric(errors='coerce') equivalent — null result plays the role of NaN. */
function toNumeric(value: CellValue): number | null {
  if (value === null || value === undefined) return null
  if (typeof value === 'number') return Number.isNaN(value) ? null : value
  const t = String(value).trim()
  if (t === '') return null
  const n = Number(t)
  return Number.isNaN(n) ? null : n
}

/**
 * pandas `.astype(str)` on a column: floats keep their repr. A column that
 * contains only numbers but has at least one empty cell is float64 in pandas,
 * so integral values stringify as '110.0'. Mirrored here for parity.
 */
function pandasColumnToString(
  values: CellValue[],
): string[] {
  const nonNull = values.filter((v) => v !== null)
  const allNumeric = nonNull.length > 0 && nonNull.every((v) => typeof v === 'number')
  const hasNull = nonNull.length !== values.length
  const isFloatColumn =
    allNumeric && (hasNull || nonNull.some((v) => !Number.isInteger(v as number)))
  return values.map((v) => {
    if (v === null) return ''
    if (typeof v === 'number') {
      if (Number.isNaN(v)) return ''
      if (Number.isInteger(v) && isFloatColumn) return `${v}.0`
      return String(v)
    }
    return String(v).trim()
  })
}

/**
 * Validates the workbook columns against the brand's contract.
 * `is_valid` depends ONLY on required columns; optional/extra are informational.
 */
export function validateExcelFormat(sheet: RawSheet, brandConfig: BrandConfig): ExcelFormatReport {
  const required = brandConfig.getRequiredColumns()
  const optional = brandConfig.getOptionalColumns()
  const found = sheet.columns
  const missingRequired = required.filter((c) => !found.includes(c))
  const missingOptional = optional.filter((c) => !found.includes(c))
  const allKnown = new Set([...required, ...optional])
  const extra = found.filter((c) => !allKnown.has(c))
  return {
    is_valid: missingRequired.length === 0,
    found_columns: found,
    missing_columns: missingRequired,
    missing_optional_columns: missingOptional,
    extra_columns: extra,
    total_rows: sheet.rows.length,
    error_message: null,
  }
}

export class ExcelProcessor {
  brandConfig: BrandConfig
  /** Converted rows: 'str' columns hold strings, 'numeric' columns hold number|null (NaN). */
  data: Record<string, string | number | null>[] | null = null
  columns: string[] = []

  constructor(brandConfig: BrandConfig = mnyConfig) {
    this.brandConfig = brandConfig
  }

  setBrandConfig(brandConfig: BrandConfig): void {
    this.brandConfig = brandConfig
  }

  /** Port of load_file: fails only when a REQUIRED column is missing. */
  loadSheet(sheet: RawSheet): boolean {
    const missingRequired = this.brandConfig
      .getRequiredColumns()
      .filter((c) => !sheet.columns.includes(c))
    if (missingRequired.length > 0) {
      this.data = null
      this.columns = []
      return false
    }
    this.columns = [...sheet.columns]
    this.data = this.convertDataTypes(sheet)
    return true
  }

  /** Port of _convert_data_types: converts the columns that are PRESENT only. */
  private convertDataTypes(sheet: RawSheet): Record<string, string | number | null>[] {
    const columnTypes = this.brandConfig.getColumnTypes()
    const converted: Record<string, string | number | null>[] = sheet.rows.map(() => ({}))
    for (const column of sheet.columns) {
      const expected = columnTypes[column] ?? 'str'
      const values = sheet.rows.map((r) => r[column] ?? null)
      if (expected === 'numeric') {
        values.forEach((v, i) => {
          converted[i][column] = toNumeric(v)
        })
      } else {
        const strings = pandasColumnToString(values)
        strings.forEach((s, i) => {
          converted[i][column] = s.trim()
        })
      }
    }
    return converted
  }

  /** Port of _validate_data_quality — returns the warnings instead of logging them. */
  validateDataQuality(): DataQualityReport {
    const report: DataQualityReport = { litho_issues: [], upc_issues: 0 }
    if (this.data === null) return report
    this.data.forEach((row, idx) => {
      const lithoStr = String(row['LITHO'] ?? '').trim()
      if (!this.brandConfig.isValidLithoCode(lithoStr)) {
        report.litho_issues.push(`Ligne ${idx + 2}: '${lithoStr}'`)
      }
    })
    for (const row of this.data) {
      const v = row['UPC']
      const upcStr = (v === null ? '' : String(v)).trim()
      if (upcStr.length !== 11 || !/^[0-9]+$/.test(upcStr)) {
        report.upc_issues += 1
      }
    }
    return report
  }

  /** Port of get_data_for_litho: rows whose trimmed LITHO equals the code. */
  getDataForLitho(lithoCode: string): LithoRecord[] {
    if (this.data === null) return []
    const target = String(lithoCode).trim()
    const records: LithoRecord[] = []
    for (const row of this.data) {
      const litho = row['LITHO']
      const lithoStr = (litho === null ? '' : String(litho)).trim()
      if (lithoStr !== target) continue
      const record: LithoRecord = {}
      for (const column of this.columns) {
        const value = row[column]
        if (value === null || value === undefined || (typeof value === 'number' && Number.isNaN(value))) {
          record[column] = ''
        } else if (typeof value === 'number') {
          record[column] = value // integral values stay numbers (Python int()s them)
        } else {
          record[column] = String(value).trim()
        }
      }
      records.push(record)
    }
    return records
  }

  getUniqueValues(columnName: string): string[] {
    if (this.data === null || !this.columns.includes(columnName)) return []
    const seen = new Set<string>()
    const out: string[] = []
    for (const row of this.data) {
      const v = row[columnName]
      if (v === null || v === undefined) continue
      const s = String(v)
      if (!seen.has(s)) {
        seen.add(s)
        out.push(s)
      }
    }
    return out
  }

  getUniqueLithoCount(): number {
    if (this.data === null) return 0
    return new Set(this.data.map((r) => String(r['LITHO'] ?? ''))).size
  }
}

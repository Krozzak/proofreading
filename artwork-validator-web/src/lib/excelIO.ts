// exceljs adapters: read the .xlsx brief into a RawSheet (pandas.read_excel
// semantics) and serialize a ReportModel into a styled multi-sheet workbook.
import ExcelJS from 'exceljs'
import type { CellValue, RawSheet } from '../core/types'
import type { ReportModel } from '../core/reportGenerator'

/** Normalizes an exceljs cell value to our CellValue (pandas semantics). */
function normalizeCell(value: ExcelJS.CellValue): CellValue {
  if (value === null || value === undefined) return null
  if (typeof value === 'number' || typeof value === 'string') {
    return typeof value === 'string' && value === '' ? null : value
  }
  if (typeof value === 'boolean') return value ? 'True' : 'False' // pandas keeps bool; str-coerced later
  if (value instanceof Date) return value.toISOString()
  if (typeof value === 'object') {
    if ('richText' in value) {
      return (value as ExcelJS.CellRichTextValue).richText.map((r) => r.text).join('')
    }
    if ('result' in value) {
      const result = (value as ExcelJS.CellFormulaValue).result
      if (result === null || result === undefined) return null
      if (result instanceof Date) return result.toISOString()
      if (typeof result === 'object') return null // error result
      return result as CellValue
    }
    if ('text' in value) {
      return (value as ExcelJS.CellHyperlinkValue).text ?? null
    }
    if ('error' in value) return null
  }
  return String(value)
}

/**
 * Reads the first worksheet like pandas.read_excel: row 1 = header, empty
 * cells → null (NaN). Duplicate/empty headers are ignored (first wins).
 */
export async function readBrief(data: ArrayBuffer): Promise<RawSheet> {
  const workbook = new ExcelJS.Workbook()
  await workbook.xlsx.load(data)
  const worksheet = workbook.worksheets[0]
  if (!worksheet) return { columns: [], rows: [] }

  const headerRow = worksheet.getRow(1)
  const columns: string[] = []
  const columnIndex = new Map<number, string>()
  headerRow.eachCell({ includeEmpty: false }, (cell, colNumber) => {
    const name = String(normalizeCell(cell.value) ?? '').trim()
    if (name && !columns.includes(name)) {
      columns.push(name)
      columnIndex.set(colNumber, name)
    }
  })

  const rows: Record<string, CellValue>[] = []
  for (let r = 2; r <= worksheet.rowCount; r++) {
    const excelRow = worksheet.getRow(r)
    const row: Record<string, CellValue> = {}
    let hasValue = false
    for (const [colNumber, name] of columnIndex.entries()) {
      const value = normalizeCell(excelRow.getCell(colNumber).value)
      row[name] = value
      if (value !== null) hasValue = true
    }
    // pandas drops fully-empty trailing rows
    if (hasValue) rows.push(row)
  }

  return { columns, rows }
}

/**
 * Serializes the report model: one worksheet per sheet, bold header row
 * (pandas to_excel parity) + auto column widths.
 */
export async function writeReport(model: ReportModel): Promise<ArrayBuffer> {
  const workbook = new ExcelJS.Workbook()
  workbook.created = new Date()

  for (const sheet of model.sheets) {
    // Excel sheet names are capped at 31 chars
    const worksheet = workbook.addWorksheet(sheet.name.slice(0, 31))

    const header = worksheet.addRow(sheet.columns)
    header.font = { bold: true }

    for (const row of sheet.rows) {
      worksheet.addRow(row.map((cell) => (cell === null ? undefined : cell)))
    }

    // Auto width: longest value per column, clamped
    sheet.columns.forEach((col, i) => {
      let width = col.length
      for (const row of sheet.rows) {
        const len = String(row[i] ?? '').length
        if (len > width) width = len
      }
      worksheet.getColumn(i + 1).width = Math.min(Math.max(width + 2, 10), 60)
    })
  }

  return workbook.xlsx.writeBuffer() as Promise<ArrayBuffer>
}

/** Triggers a browser download of the given bytes. */
export function downloadBlob(data: ArrayBuffer | string, fileName: string, mimeType: string): void {
  const blob = new Blob([data], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

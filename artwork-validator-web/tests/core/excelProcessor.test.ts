// Excel processor: format validation (misspelled DECRIPTION!), pandas-style
// type coercion, getDataForLitho cell normalization, exceljs round-trip.
import { describe, expect, it } from 'vitest'
import ExcelJS from 'exceljs'
import { ExcelProcessor, validateExcelFormat } from '../../src/core/excelProcessor'
import { mnyConfig, essieConfig } from '../../src/core/brandConfigs'
import { readBrief } from '../../src/lib/excelIO'
import type { RawSheet } from '../../src/core/types'

const MNY_COLUMNS = [
  'LITHO', 'DECRIPTION', 'UPC SEQUENCE', 'UPC POSITION', 'UPC',
  'PRODUCT DESCRIPTION', 'SHADE NAME', 'SHADE NUMBER', 'PRODUCT FACING SL', '4 DIGITS',
]

function sheet(rows: Record<string, string | number | null>[], columns = MNY_COLUMNS): RawSheet {
  return { columns, rows }
}

describe('validateExcelFormat', () => {
  it('is_valid depends only on required columns', () => {
    const report = validateExcelFormat(sheet([]), mnyConfig)
    expect(report.is_valid).toBe(true)
    expect(report.missing_optional_columns).toContain('NEW')
  })

  it('fails when DECRIPTION is spelled correctly (DESCRIPTION)', () => {
    const cols = MNY_COLUMNS.map((c) => (c === 'DECRIPTION' ? 'DESCRIPTION' : c))
    const report = validateExcelFormat(sheet([], cols), mnyConfig)
    expect(report.is_valid).toBe(false)
    expect(report.missing_columns).toEqual(['DECRIPTION'])
    expect(report.extra_columns).toEqual(['DESCRIPTION'])
  })

  it('ESSIE does not require 4 DIGITS', () => {
    const cols = MNY_COLUMNS.filter((c) => c !== '4 DIGITS')
    expect(validateExcelFormat(sheet([], cols), essieConfig).is_valid).toBe(true)
    expect(validateExcelFormat(sheet([], cols), mnyConfig).is_valid).toBe(false)
  })
})

describe('ExcelProcessor', () => {
  const baseRow = {
    LITHO: 'YCA12345',
    DECRIPTION: 'DISPLAY',
    'UPC SEQUENCE': '',
    'UPC POSITION': 1,
    UPC: '12345678901',
    'PRODUCT DESCRIPTION': 'LIPSTICK',
    'SHADE NAME': 'FOREST BROWN',
    'SHADE NUMBER': 110,
    'PRODUCT FACING SL': 2,
    '4 DIGITS': 4501,
  }

  it('coerces numeric columns and rejects non-numeric as NaN → empty', () => {
    const processor = new ExcelProcessor(mnyConfig)
    expect(
      processor.loadSheet(
        sheet([{ ...baseRow, 'SHADE NUMBER': 'not-a-number' }]),
      ),
    ).toBe(true)
    const records = processor.getDataForLitho('YCA12345')
    expect(records[0]['SHADE NUMBER']).toBe('') // NaN → ''
  })

  it('normalizes cells: null → "", numbers stay numbers, strings trimmed', () => {
    const processor = new ExcelProcessor(mnyConfig)
    processor.loadSheet(sheet([{ ...baseRow, 'SHADE NAME': '  PADDED  ', UPC: null }]))
    const records = processor.getDataForLitho('YCA12345')
    expect(records[0]['SHADE NAME']).toBe('PADDED')
    expect(records[0]['UPC']).toBe('')
    expect(records[0]['SHADE NUMBER']).toBe(110)
  })

  it('matches lithos on trimmed string equality', () => {
    const processor = new ExcelProcessor(mnyConfig)
    processor.loadSheet(sheet([{ ...baseRow, LITHO: ' YCA12345 ' }, { ...baseRow, LITHO: 'YCA99999' }]))
    expect(processor.getDataForLitho('YCA12345')).toHaveLength(1)
    expect(processor.getDataForLitho('YCA00000')).toHaveLength(0)
  })

  it('fails loadSheet when a required column is missing', () => {
    const processor = new ExcelProcessor(mnyConfig)
    expect(processor.loadSheet(sheet([], ['LITHO', 'UPC']))).toBe(false)
    expect(processor.data).toBeNull()
  })

  it('reports data-quality warnings without blocking', () => {
    const processor = new ExcelProcessor(mnyConfig)
    processor.loadSheet(sheet([{ ...baseRow, LITHO: 'BADCODE', UPC: '123' }]))
    const quality = processor.validateDataQuality()
    expect(quality.litho_issues).toHaveLength(1)
    expect(quality.upc_issues).toBe(1)
  })
})

describe('exceljs round-trip (readBrief)', () => {
  it('reads a generated workbook with pandas semantics', async () => {
    const workbook = new ExcelJS.Workbook()
    const ws = workbook.addWorksheet('Sheet1')
    ws.addRow(MNY_COLUMNS)
    ws.addRow(['YCA12345', 'CUBBY 10F2T', 'UPC.1, UPC.2', 1, 'UPC.1', 'LIPSTICK', 'FOREST BROWN', 110, 2, 4501])
    ws.addRow(['YCA12345', 'CUBBY 10F2T', 'UPC.1, UPC.2', 2, 'UPC.2', 'LIPSTICK', null, 120, 2, null])
    const buffer = await workbook.xlsx.writeBuffer()

    const raw = await readBrief(buffer as ArrayBuffer)
    expect(raw.columns).toEqual(MNY_COLUMNS)
    expect(raw.rows).toHaveLength(2)
    expect(raw.rows[0]['SHADE NUMBER']).toBe(110)
    expect(raw.rows[1]['SHADE NAME']).toBeNull()

    const processor = new ExcelProcessor(mnyConfig)
    expect(processor.loadSheet(raw)).toBe(true)
    const records = processor.getDataForLitho('YCA12345')
    expect(records).toHaveLength(2)
    expect(records[0]['SHADE NAME']).toBe('FOREST BROWN')
    expect(records[1]['SHADE NAME']).toBe('')
    expect(records[1]['4 DIGITS']).toBe('')
  })
})

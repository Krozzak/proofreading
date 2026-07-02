// dataCollector + reportGenerator: formats, sheet structure, helper logic.
import { describe, expect, it } from 'vitest'
import { collectAllValidationData, round1 } from '../../src/core/dataCollector'
import {
  categorizePdfSize,
  extractPdfDescription,
  generateReportModel,
  getPdfValidationStatus,
  mapSessionToValidationStatus,
} from '../../src/core/reportGenerator'
import { LithoValidator } from '../../src/core/validator'
import { mnyConfig } from '../../src/core/brandConfigs'
import type { LithoRecord, LithoValidation } from '../../src/core/types'

const EXCEL: Record<string, LithoRecord[]> = {
  YCA11111: [
    {
      LITHO: 'YCA11111', DECRIPTION: 'STANDARD DISPLAY', 'UPC SEQUENCE': '', UPC: '12345678901',
      'PRODUCT DESCRIPTION': 'LIPSTICK', 'SHADE NAME': 'FOREST BROWN', 'SHADE NUMBER': 110,
      'PRODUCT FACING SL': 2, '4 DIGITS': 4501,
    },
    {
      LITHO: 'YCA11111', DECRIPTION: 'STANDARD DISPLAY', 'UPC SEQUENCE': '', UPC: '12345678902',
      'PRODUCT DESCRIPTION': 'LIPSTICK', 'SHADE NAME': 'MISSING SHADE', 'SHADE NUMBER': 999,
      'PRODUCT FACING SL': 2, '4 DIGITS': 4502,
    },
  ],
  YCA22222: [
    {
      LITHO: 'YCA22222', DECRIPTION: 'MNY CUBBY 10F2T', 'UPC SEQUENCE': '', UPC: 'UPC.1',
      'PRODUCT DESCRIPTION': 'CUBBY', 'SHADE NAME': 'A', 'SHADE NUMBER': 1,
      'PRODUCT FACING SL': 'CUBBY', '4 DIGITS': '',
    },
  ],
}

const TEXTS: Record<string, string> = {
  YCA11111: 'this litho contains the shade 110 FOREST BROWN for the loreal beauty collection',
  YCA22222: '',
}

const STATUSES: Record<string, LithoValidation> = {
  YCA11111: { status: 'approved', date: '2026-07-02T10:00:00', comment: 'ok' },
}

function collect() {
  const validator = new LithoValidator(mnyConfig)
  return collectAllValidationData({
    getSessionInfo: () => ({
      name: 'Test', created: '2026-07-01T08:00:00', updated: '2026-07-02T09:00:00',
      pdf_folder: 'FOLDER', excel_file: 'brief.xlsx', validations_count: 1, file_path: null,
    }),
    getAllLithoCodes: () => ['YCA11111', 'YCA22222'],
    getDataForLitho: (code) => EXCEL[code] ?? [],
    getTextForLitho: (code) => TEXTS[code] ?? '',
    validate: (text, data) => validator.validate(text, data),
    getLithoStatus: (code) => STATUSES[code] ?? null,
    checkDigits: false,
    now: () => '2026-07-02T12:00:00',
  })
}

describe('round1 (Python round half-to-even)', () => {
  it('matches Python rounding', () => {
    expect(round1(66.666)).toBe(66.7)
    expect(round1(50.0)).toBe(50)
    expect(round1(0.25)).toBe(0.2) // banker's rounding
    expect(round1(0.35)).toBe(0.4)
  })
})

describe('dataCollector', () => {
  it('produces "ok/total" strings and 1-decimal percentages', () => {
    const data = collect()
    const std = data.litho_summaries.find((l) => l['litho_code'] === 'YCA11111')!
    expect(std['overall_success']).toBe('1/2')
    expect(std['overall_percentage']).toBe(50)
    expect(std['type']).toBe('Standard')
    expect(std['session_status']).toBe('approved')
    expect(std['digits_success']).toBe('N/A') // checkDigits off
  })

  it('summarizes CUBBY lithos with dimensions and N/A fields', () => {
    const data = collect()
    const cubby = data.litho_summaries.find((l) => l['litho_code'] === 'YCA22222')!
    expect(cubby['type']).toBe('CUBBY')
    expect(cubby['dimensions']).toBe('10F x 2T')
    expect(cubby['total_positions']).toBe(20)
    expect(cubby['overall_success']).toBe(true)
    expect(cubby['shade_number_success']).toBe('N/A')
  })

  it('computes global statistics', () => {
    const g = collect().global_statistics
    expect(g['total_lithos']).toBe(2)
    expect(g['approved_lithos']).toBe(1)
    expect(g['pending_lithos']).toBe(1)
    expect(g['cubby_lithos']).toBe(1)
    expect(g['avg_digits_success']).toBe('N/A')
  })
})

describe('reportGenerator helpers', () => {
  it('categorizes PDF sizes at the exact thresholds', () => {
    expect(categorizePdfSize(0)).toBe('Vide')
    expect(categorizePdfSize(49)).toBe('Très petit')
    expect(categorizePdfSize(50)).toBe('Petit')
    expect(categorizePdfSize(199)).toBe('Petit')
    expect(categorizePdfSize(200)).toBe('Moyen')
    expect(categorizePdfSize(500)).toBe('Grand')
    expect(categorizePdfSize(1000)).toBe('Très grand')
  })

  it('maps session statuses to emoji labels', () => {
    expect(mapSessionToValidationStatus('approved')).toBe('✅ Approuvé')
    expect(mapSessionToValidationStatus('rejected')).toBe('❌ Rejeté')
    expect(mapSessionToValidationStatus('pending')).toBe('⏳ En Attente')
    expect(mapSessionToValidationStatus(null)).toBe('❓ Indéterminé')
  })

  it('extracts descriptions: 3 significant lines, 200-char truncation', () => {
    const deps = { getTextForLitho: () => 'short\n' + 'A LINE THAT IS LONG ENOUGH\n'.repeat(5) }
    const desc = extractPdfDescription('X', deps)
    expect(desc.split(' | ')).toHaveLength(3)

    const longDeps = { getTextForLitho: () => `${'X'.repeat(300)}\n` }
    const truncated = extractPdfDescription('X', longDeps)
    expect(truncated).toHaveLength(200)
    expect(truncated.endsWith('...')).toBe(true)

    expect(extractPdfDescription('X', { getTextForLitho: () => '' })).toBe('PDF vide ou illisible')
    expect(extractPdfDescription('', { getTextForLitho: () => 'x' })).toBe('PDF non disponible')
  })

  it('derives PDF validation statuses from keywords', () => {
    expect(getPdfValidationStatus('PDF vide ou illisible')).toBe('❌ PDF Invalide')
    expect(getPdfValidationStatus('the loreal shade collection')).toBe('✅ PDF Valide')
    expect(getPdfValidationStatus('contains the word erreur here')).toBe('❌ Contenu Problématique')
    expect(getPdfValidationStatus('nothing special')).toBe('⚠️ À Vérifier')
  })
})

describe('generateReportModel', () => {
  it('builds the 8 sheets with exact French names', () => {
    const data = collect()
    const model = generateReportModel(data, { getTextForLitho: (c) => TEXTS[c] ?? '' })
    const names = model.sheets.map((s) => s.name)
    expect(names).toEqual([
      'Résumé Session',
      'Statistiques Globales',
      'Résumé par Litho',
      'Détails Complets',
      'Lithos en Attente',
      'Analyse PDFs',
      'Statuts Validation',
    ]) // no 'Lithos Rejetées' — none rejected in the fixture
  })

  it('orders the litho summary columns per the desktop column_order', () => {
    const data = collect()
    const model = generateReportModel(data, { getTextForLitho: (c) => TEXTS[c] ?? '' })
    const sheet = model.sheets.find((s) => s.name === 'Résumé par Litho')!
    expect(sheet.columns.slice(0, 4)).toEqual(['litho_code', 'type', 'session_status', 'validation_status'])
    expect(sheet.columns).not.toContain('dimensions') // dropped by reindex, like pandas
  })

  it('includes Lithos Rejetées only when a litho is rejected', () => {
    const data = collect()
    data.litho_summaries[1]['session_status'] = 'rejected'
    const model = generateReportModel(data, { getTextForLitho: (c) => TEXTS[c] ?? '' })
    expect(model.sheets.map((s) => s.name)).toContain('Lithos Rejetées')
  })
})

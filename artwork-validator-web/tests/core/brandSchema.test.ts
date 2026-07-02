// JSON brand definitions: schema validation + runtime adapter behavior parity
// with the historical hardcoded configs.
import { describe, expect, it } from 'vitest'
import {
  BRAND_SCHEMA_VERSION,
  ESSIE_DEFINITION,
  MNY_DEFINITION,
  STANDARD_COLUMNS,
  brandFromDefinition,
  describeBrandDefinition,
  essieConfig,
  mnyConfig,
  validateBrandDefinition,
  type BrandDefinition,
} from '../../src/core/brandConfigs'

const NYX_DEF: BrandDefinition = {
  schema_version: BRAND_SCHEMA_VERSION,
  brand_code: 'NYX',
  brand_name: 'NYX Professional Makeup',
  filename: { type: 'prefix', literal: 'NYX', digits: 6 },
  columns: STANDARD_COLUMNS,
  validation: { requires_upc: false, requires_digits: true },
  created_by: 'wizard',
}

describe('validateBrandDefinition', () => {
  it('accepts a valid prefix definition', () => {
    const { errors, definition } = validateBrandDefinition(NYX_DEF)
    expect(errors).toEqual([])
    expect(definition?.brand_code).toBe('NYX')
  })

  it('accepts a valid regex definition (ESSIE builtin)', () => {
    const { errors } = validateBrandDefinition(ESSIE_DEFINITION)
    expect(errors).toEqual([])
  })

  it('rejects bad brand codes', () => {
    const { errors } = validateBrandDefinition({ ...NYX_DEF, brand_code: 'n!' })
    expect(errors.some((e) => e.includes('brand_code'))).toBe(true)
  })

  it('requires the LITHO column', () => {
    const { errors } = validateBrandDefinition({
      ...NYX_DEF,
      columns: NYX_DEF.columns.filter((c) => c.name !== 'LITHO'),
    })
    expect(errors.some((e) => e.includes('LITHO'))).toBe(true)
  })

  it('rejects requires_digits without a 4 DIGITS column', () => {
    const { errors } = validateBrandDefinition({
      ...NYX_DEF,
      columns: NYX_DEF.columns.filter((c) => c.name !== '4 DIGITS'),
    })
    expect(errors.some((e) => e.includes('4 DIGITS'))).toBe(true)
  })

  it('rejects invalid regexes with a readable message', () => {
    const { errors } = validateBrandDefinition({
      ...NYX_DEF,
      filename: { type: 'regex', filenamePattern: '([', extractPattern: '^(A)', codePattern: '^A$' },
    })
    expect(errors.some((e) => e.includes('regex invalide'))).toBe(true)
  })

  it('rejects duplicate columns', () => {
    const { errors } = validateBrandDefinition({
      ...NYX_DEF,
      columns: [...NYX_DEF.columns, { name: 'LITHO', required: true, type: 'str' }],
    })
    expect(errors.some((e) => e.includes('double'))).toBe(true)
  })
})

describe('brandFromDefinition (prefix)', () => {
  const nyx = brandFromDefinition(NYX_DEF)

  it('validates and extracts prefix codes like the MNY logic', () => {
    expect(nyx.isValidFilename('NYX123456_v2.pdf')).toBe(true)
    expect(nyx.isValidFilename('NYX12345.pdf')).toBe(false) // only 5 digits
    expect(nyx.extractLithoCode('NYX123456_v2.pdf')).toBe('NYX123456')
    expect(nyx.isValidLithoCode('NYX123456')).toBe(true)
    expect(nyx.isValidLithoCode('NYX1234567')).toBe(false) // too long
  })
})

describe('builtin definitions generate the historical behavior', () => {
  it('MNY: same filename/code behavior as before', () => {
    const fromDef = brandFromDefinition(MNY_DEFINITION)
    for (const name of ['YCA12345_version.pdf', 'CARE_S26_1_3.pdf', 'YCA123', 'YCA12345.pdf']) {
      expect(fromDef.isValidFilename(name)).toBe(mnyConfig.isValidFilename(name))
      expect(fromDef.extractLithoCode(name)).toBe(mnyConfig.extractLithoCode(name))
    }
    expect(fromDef.getRequiredColumns()).toEqual(mnyConfig.getRequiredColumns())
    expect(fromDef.getColumnTypes()).toEqual(mnyConfig.getColumnTypes())
    expect(fromDef.requiresDigitsValidation()).toBe(true)
  })

  it('ESSIE: same filename/code behavior as before', () => {
    const fromDef = brandFromDefinition(ESSIE_DEFINITION)
    for (const name of [
      'CARE_S26_1_3.pdf',
      'GEL_S26_2_6_SHADESTRIPS.pdf',
      'care_s26_1_3.pdf',
      'YCA12345.pdf',
      'INVALID_S26_1_3.pdf',
    ]) {
      expect(fromDef.isValidFilename(name)).toBe(essieConfig.isValidFilename(name))
      expect(fromDef.extractLithoCode(name)).toBe(essieConfig.extractLithoCode(name))
    }
    expect(fromDef.getColumnTypes()['SHADE NUMBER']).toBe('str')
    expect(fromDef.requiresDigitsValidation()).toBe(false)
  })
})

describe('describeBrandDefinition', () => {
  it('uses the explicit description when present', () => {
    expect(describeBrandDefinition(MNY_DEFINITION)).toContain('Format Maybelline New York')
  })

  it('auto-generates a French description otherwise', () => {
    const text = describeBrandDefinition(NYX_DEF)
    expect(text).toContain('NYX + 6 chiffres')
    expect(text).toContain('Colonnes requises')
  })
})

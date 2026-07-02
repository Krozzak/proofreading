// Brand config contracts — every docstring example from mny_config.py and
// essie_config.py is pinned here.
import { describe, expect, it } from 'vitest'
import { mnyConfig, essieConfig } from '../../src/core/brandConfigs'

describe('MNY brand config', () => {
  it('keeps the intentionally misspelled DECRIPTION required column', () => {
    expect(mnyConfig.getRequiredColumns()).toContain('DECRIPTION')
    expect(mnyConfig.getRequiredColumns()).toContain('4 DIGITS')
  })

  it('validates filenames (YCA + 5 digits)', () => {
    expect(mnyConfig.isValidFilename('YCA12345_version.pdf')).toBe(true)
    expect(mnyConfig.isValidFilename('CARE_S26_1_3.pdf')).toBe(false)
    expect(mnyConfig.isValidFilename('YCA123')).toBe(false)
  })

  it('extracts the 8-char litho code', () => {
    expect(mnyConfig.extractLithoCode('YCA12345_version2.pdf')).toBe('YCA12345')
    expect(mnyConfig.extractLithoCode('invalid.pdf')).toBeNull()
  })

  it('validates litho codes strictly (exactly 8 chars)', () => {
    expect(mnyConfig.isValidLithoCode('YCA12345')).toBe(true)
    expect(mnyConfig.isValidLithoCode('YCA123')).toBe(false)
    expect(mnyConfig.isValidLithoCode('YCA123456')).toBe(false)
    expect(mnyConfig.isValidLithoCode('CARE_S26_1_3')).toBe(false)
  })

  it('flags digit validation support', () => {
    expect(mnyConfig.requiresDigitsValidation()).toBe(true)
    expect(mnyConfig.requiresUpcValidation()).toBe(false)
  })
})

describe('ESSIE brand config', () => {
  it('validates filenames with gammes and optional _SHADESTRIPS', () => {
    expect(essieConfig.isValidFilename('CARE_S26_1_3.pdf')).toBe(true)
    expect(essieConfig.isValidFilename('GEL_S26_2_6_SHADESTRIPS.pdf')).toBe(true)
    expect(essieConfig.isValidFilename('YCA12345.pdf')).toBe(false)
    expect(essieConfig.isValidFilename('care_s26_1_3.pdf')).toBe(true) // case-insensitive
  })

  it('extracts the code without the _SHADESTRIPS suffix', () => {
    expect(essieConfig.extractLithoCode('CARE_S26_1_3_SHADESTRIPS.pdf')).toBe('CARE_S26_1_3')
    expect(essieConfig.extractLithoCode('GEL_S26_2_6.pdf')).toBe('GEL_S26_2_6')
    expect(essieConfig.extractLithoCode('YCA12345.pdf')).toBeNull()
  })

  it('validates litho codes strictly ($-anchored)', () => {
    expect(essieConfig.isValidLithoCode('CARE_S26_1_3')).toBe(true)
    expect(essieConfig.isValidLithoCode('GEL_S26_2_6')).toBe(true)
    expect(essieConfig.isValidLithoCode('INVALID_S26_1_3')).toBe(false)
    expect(essieConfig.isValidLithoCode('YCA12345')).toBe(false)
    expect(essieConfig.isValidLithoCode('CARE_S26_1_3_SHADESTRIPS')).toBe(false)
  })

  it('has no 4 DIGITS column and treats SHADE NUMBER as text', () => {
    expect(essieConfig.getRequiredColumns()).not.toContain('4 DIGITS')
    expect(essieConfig.getColumnTypes()['SHADE NUMBER']).toBe('str')
    expect(essieConfig.requiresDigitsValidation()).toBe(false)
  })
})

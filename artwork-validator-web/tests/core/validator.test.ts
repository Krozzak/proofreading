// Unit tests for the legacy engine + CUBBY logic (behaviors pinned from
// core/validator.py).
import { describe, expect, it } from 'vitest'
import { LithoValidator, isCubbyResult, type LegacyEntryResult } from '../../src/core/validator'
import { mnyConfig, essieConfig } from '../../src/core/brandConfigs'
import { safeStr } from '../../src/core/textSafe'
import type { LithoRecord } from '../../src/core/types'

function row(overrides: Partial<Record<string, string | number>> = {}): LithoRecord {
  return {
    LITHO: 'YCA12345',
    DECRIPTION: 'MNY DISPLAY',
    'UPC SEQUENCE': '',
    'UPC POSITION': 1,
    UPC: '12345678901',
    'PRODUCT DESCRIPTION': 'LIPSTICK',
    'SHADE NAME': 'FOREST BROWN',
    'SHADE NUMBER': 110,
    'PRODUCT FACING SL': 2,
    '4 DIGITS': 4501,
    ...overrides,
  }
}

describe('safeStr', () => {
  it('int-ifies integral floats like Python _safe_str', () => {
    expect(safeStr(110)).toBe('110')
    expect(safeStr(110.5)).toBe('110.5')
    expect(safeStr(' padded ')).toBe('padded')
    expect(safeStr(null)).toBe('')
    expect(safeStr(undefined)).toBe('')
    expect(safeStr(Number.NaN)).toBe('')
  })
})

describe('extractCubbyDimensions', () => {
  const v = new LithoValidator(mnyConfig)
  it('parses XFYT patterns', () => {
    expect(v.extractCubbyDimensions('MNY CUBBY 10F2T FALL')).toEqual([10, 2])
    expect(v.extractCubbyDimensions('mny 10f4t')).toEqual([10, 4])
  })
  it('falls back to default (10,2) for bare CUBBY', () => {
    expect(v.extractCubbyDimensions('CUBBY DISPLAY')).toEqual([10, 2])
  })
  it('parses split F/T tokens after CUBBY keyword', () => {
    // '8F3T' is caught by the primary regex; a weird token exercises the fallback
    expect(v.extractCubbyDimensions('CUBBY XX 8F3T')).toEqual([8, 3])
  })
  it('returns null for non-cubby descriptions', () => {
    expect(v.extractCubbyDimensions('REGULAR DISPLAY')).toBeNull()
  })
})

describe('WTP ↔ WATERPROOF equivalence', () => {
  const v = new LithoValidator(mnyConfig)
  it('accepts exact match first', () => {
    expect(v.validateShadeName('GREAT LASH', 'XX GREAT LASH XX')).toBe(true)
  })
  it('replaces ALL WTP occurrences (Python str.replace semantics)', () => {
    expect(v.validateShadeName('A WTP B WTP', 'A WATERPROOF B WATERPROOF')).toBe(true)
  })
  it('WATERPROOF → WTP direction', () => {
    expect(v.validateShadeName('LASH WATERPROOF', 'THE LASH WTP MASCARA')).toBe(true)
  })
  it('fails when neither variant is present', () => {
    expect(v.validateShadeName('LASH WTP', 'NOTHING HERE')).toBe(false)
  })
})

describe('legacy validation rules', () => {
  it('FRAME and SPACE_SAVER rows are always overall-true', () => {
    const v = new LithoValidator(mnyConfig)
    const results = v.validate('IRRELEVANT TEXT', [
      row({ 'PRODUCT FACING SL': 'FRAME', 'SHADE NAME': 'ABSENT' }),
      row({ 'SHADE NAME': 'SPACE_SAVER' }),
    ]) as LegacyEntryResult[]
    expect(results[0].is_frame).toBe(true)
    expect(results[0].overall).toBe(true)
    expect(results[1].is_space_saver).toBe(true)
    expect(results[1].overall).toBe(true)
  })

  it('detects MIXED only with >1 distinct integer facing', () => {
    const v = new LithoValidator(mnyConfig)
    const mixed = v.validate('110 FOREST BROWN', [
      row({ 'PRODUCT FACING SL': 2 }),
      row({ 'PRODUCT FACING SL': 3 }),
    ]) as LegacyEntryResult[]
    expect(mixed[0].is_mixed).toBe(true)

    const notMixed = v.validate('110 FOREST BROWN', [
      row({ 'PRODUCT FACING SL': 2 }),
      row({ 'PRODUCT FACING SL': 2 }),
      row({ 'PRODUCT FACING SL': 'FRAME' }),
    ]) as LegacyEntryResult[]
    expect(notMixed[0].is_mixed).toBe(false)
  })

  it('gates 4 DIGITS on checkDigits × brand support × non-empty value', () => {
    const text = 'MNY 110 FOREST BROWN NO DIGITS HERE'
    // checkDigits off → digits always true
    const off = new LithoValidator(mnyConfig)
    expect((off.validate(text, [row({ '4 DIGITS': 4501 })]) as LegacyEntryResult[])[0].digits).toBe(true)

    // checkDigits on + MNY → digits actually checked
    const on = new LithoValidator(mnyConfig)
    on.checkDigits = true
    const checked = on.validate(text, [row({ '4 DIGITS': 4501 })]) as LegacyEntryResult[]
    expect(checked[0].digits).toBe(false)
    expect(checked[0].overall).toBe(false)

    // empty digits → not included in overall criteria
    const empty = on.validate(text, [row({ '4 DIGITS': '' })]) as LegacyEntryResult[]
    expect(empty[0].digits).toBe(true)
    expect(empty[0].overall).toBe(true)

    // ESSIE never validates digits
    const essie = new LithoValidator(essieConfig)
    essie.checkDigits = true
    const essieRes = essie.validate(text, [row({ '4 DIGITS': 4501 })]) as LegacyEntryResult[]
    expect(essieRes[0].digits).toBe(true)
  })

  it('probes description columns in DECRIPTION-first order', () => {
    const v = new LithoValidator(mnyConfig)
    // DECRIPTION says CUBBY, DESCRIPTION would not — DECRIPTION must win
    const results = v.validate('TEXT', [
      row({ DECRIPTION: 'CUBBY 4F2T', DESCRIPTION: 'NOT A CUBBY' }),
    ])
    expect(isCubbyResult(results[0])).toBe(true)
  })
})

describe('CUBBY matrix organization', () => {
  const v = new LithoValidator(mnyConfig)

  it('sorts rows by UPC SEQUENCE of the first row, unknown UPCs last', () => {
    const data = [
      row({ 'UPC SEQUENCE': 'B, A', UPC: 'UNKNOWN' }),
      row({ 'UPC SEQUENCE': 'B, A', UPC: 'A' }),
      row({ 'UPC SEQUENCE': 'B, A', UPC: 'B' }),
    ]
    const sorted = v.sortByUpcSequence(data)
    expect(sorted.map((r) => r['UPC'])).toEqual(['B', 'A', 'UNKNOWN'])
  })

  it('rolls over to the next tier when UPC.1 reappears', () => {
    const matrix = v.organizeCubbyMatrix(
      [
        row({ UPC: 'UPC.1', 'SHADE NUMBER': 1 }),
        row({ UPC: 'UPC.2', 'SHADE NUMBER': 2 }),
        row({ UPC: 'UPC.1', 'SHADE NUMBER': 3 }),
      ],
      3,
      2,
    )
    expect(matrix[0].map((c) => c.upc)).toEqual(['UPC.1', 'UPC.2', 'EMPTY'])
    expect(matrix[1].map((c) => c.upc)).toEqual(['UPC.1', 'EMPTY', 'EMPTY'])
  })

  it('places non-pattern UPCs sequentially and fills EMPTY cells', () => {
    const matrix = v.organizeCubbyMatrix([row({ UPC: 'X' }), row({ UPC: 'Y' })], 2, 2)
    expect(matrix[0].map((c) => c.upc)).toEqual(['X', 'Y'])
    expect(matrix[1].map((c) => c.upc)).toEqual(['EMPTY', 'EMPTY'])
  })

  it('flags FRAME cells', () => {
    const matrix = v.organizeCubbyMatrix([row({ UPC: 'FRAME' })], 2, 1)
    expect(matrix[0][0].is_frame).toBe(true)
  })

  it('skips out-of-bounds rows', () => {
    const matrix = v.organizeCubbyMatrix(
      [row({ UPC: 'UPC.1' }), row({ UPC: 'UPC.5' })], // position 5 > 2 faces
      2,
      1,
    )
    expect(matrix[0].map((c) => c.upc)).toEqual(['UPC.1', 'EMPTY'])
  })
})

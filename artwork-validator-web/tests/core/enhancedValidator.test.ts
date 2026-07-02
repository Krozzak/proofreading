// Enhanced engine unit tests — tokenizer classification, token consumption,
// substring rule, and the pinned duplicate-allowance bug.
import { describe, expect, it } from 'vitest'
import { EnhancedValidator } from '../../src/core/enhancedValidator'
import type { LithoRecord } from '../../src/core/types'

function row(overrides: Partial<Record<string, string | number>> = {}): LithoRecord {
  return {
    'SHADE NAME': 'FOREST BROWN',
    'SHADE NUMBER': 110,
    'PRODUCT FACING SL': 2,
    UPC: '12345678901',
    'PRODUCT DESCRIPTION': 'LIPSTICK',
    '4 DIGITS': 4501,
    ...overrides,
  }
}

describe('tokenizer', () => {
  const v = new EnhancedValidator()

  it('classifies tokens like Python', () => {
    expect(v.classifyToken('4501')).toBe('digits_4')
    expect(v.classifyToken('110')).toBe('shade_number')
    expect(v.classifyToken('42')).toBe('shade_number')
    expect(v.classifyToken('12345')).toBe('number')
    expect(v.classifyToken('WATERPROOF')).toBe('waterproof_tag')
    expect(v.classifyToken('WTP')).toBe('waterproof_tag')
    expect(v.classifyToken('BROWN')).toBe('shade_name')
    expect(v.classifyToken('A')).toBe('letter')
    expect(v.classifyToken('AB12')).toBe('mixed')
  })

  it('keeps accented words as one token (Python \\w is Unicode)', () => {
    const tokens = v.tokenizePdfText('ROSÉ NUDE')
    expect(tokens.map((t) => t.text)).toEqual(['ROSÉ', 'NUDE'])
  })
})

describe('token matching', () => {
  it('consumes matched tokens so they cannot match twice', () => {
    const v = new EnhancedValidator()
    const result = v.validateEnhanced('110 FOREST BROWN', [row(), row()])
    expect(result.results[0].overall).toBe(true)
    // Second identical row: row_index 1, first row's tokens consumed and the
    // duplicate check compares {} vs the row → not a duplicate → fails
    expect(result.results[1].overall).toBe(false)
  })

  it('matches multi-word shade names on consecutive tokens', () => {
    const v = new EnhancedValidator()
    const result = v.validateEnhanced('XX 110 FOREST BROWN YY', [row()])
    expect(result.results[0].shade_name).toBe(true)
    const used = result.results[0].validation_details.tokens_used
    expect(used.find((u) => u.field === 'SHADE_NAME')?.num_tokens).toBe(2)
  })

  it('applies the substring rule only for searches longer than 3 chars', () => {
    const v = new EnhancedValidator()
    const tokens = v.tokenizePdfText('SUPERBROWN 42')
    expect(v.findTokenMatch(tokens, 'BROWN', 0, null)).not.toBeNull() // len 5 substring ok
    expect(v.findTokenMatch(tokens, 'UPE', 0, null)).toBeNull() // len 3 no substring
  })

  it('PARITY: rows with index >= 2 are always treated as legitimate duplicates', () => {
    const v = new EnhancedValidator()
    // Only ONE occurrence of the pair in the text, but three identical rows:
    // row 2+ passes because the padded-empty-rows bug marks it duplicate.
    const result = v.validateEnhanced('110 FOREST BROWN 110 FOREST BROWN 110 FOREST BROWN', [
      row(),
      row(),
      row(),
    ])
    expect(result.stats.duplicate_allowances).toBe(1) // only row index 2 (row 1 fails the {} compare)
    expect(result.results[2].overall).toBe(true)
  })

  it('counts orphan tokens', () => {
    const v = new EnhancedValidator()
    const result = v.validateEnhanced('110 FOREST BROWN EXTRA WORDS', [row()])
    expect(result.orphan_tokens).toContain('EXTRA')
    expect(result.orphan_tokens).toContain('WORDS')
  })

  it('normalizes WTP in Excel shade names to WATERPROOF', () => {
    const v = new EnhancedValidator()
    // Number placed BEFORE the name: validation is sequential within an entry
    const result = v.validateEnhanced('401 GREAT LASH WATERPROOF', [
      row({ 'SHADE NAME': 'LASH WTP', 'SHADE NUMBER': 401 }),
    ])
    expect(result.results[0].shade_name).toBe(true)
  })

  it('PARITY: cross-row position never advances (Python top-level .get bug)', () => {
    const v = new EnhancedValidator()
    // Row 2's shade number appears BEFORE row 1's in the text; with the bug,
    // row 2 restarts at position 0 and still finds it.
    const result = v.validateEnhanced('120 CRIMSON RED 110 FOREST BROWN', [
      row(),
      row({ 'SHADE NAME': 'CRIMSON RED', 'SHADE NUMBER': 120 }),
    ])
    expect(result.results[0].overall).toBe(true)
    expect(result.results[1].overall).toBe(true)
    expect(result.results[1].validation_details.start_position).toBe(0)
  })
})

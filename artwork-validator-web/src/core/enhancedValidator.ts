// Port of core/enhanced_validator.py — token-based sequential validation with
// progressive token consumption for 1:1 matching.
import { safeStr } from './textSafe'
import type { LithoRecord } from './types'

export interface PdfToken {
  text: string
  start_pos: number
  end_pos: number
  consumed: boolean
  consumed_by: string | null
  type: TokenType
}

export type TokenType =
  | 'digits_4'
  | 'shade_number'
  | 'number'
  | 'waterproof_tag'
  | 'shade_name'
  | 'letter'
  | 'mixed'

export interface TokenUsage {
  field: string
  token: string
  position: number
  num_tokens: number
}

export interface EnhancedEntryResult {
  shade_number: boolean
  shade_name: boolean
  digits: boolean
  facing: string | number
  is_mixed: boolean
  is_cubby: boolean
  is_frame: boolean
  is_space_saver: boolean
  overall: boolean
  validation_details: {
    method: 'enhanced'
    tokens_used: TokenUsage[]
    start_position: number
    last_token_position: number | null
  }
}

export interface ValidationStats {
  total_tokens: number
  consumed_tokens: number
  orphan_tokens: number
  exact_matches: number
  partial_matches: number
  failed_matches: number
  duplicate_allowances: number
}

export interface EnhancedValidationResult {
  results: EnhancedEntryResult[]
  stats: ValidationStats
  errors: string[]
  orphan_tokens?: string[]
  summary?: {
    expected_validations: number
    actual_validations: number
    success_rate: number
  }
}

interface NormalizedRow {
  row: LithoRecord
  SHADE_NAME_NORMALIZED: string
  _is_frame: boolean
  _is_space_saver: boolean
  _should_validate: boolean
}

/** Python str.isdigit() approximation for our uppercase-ASCII token stream. */
function isDigits(s: string): boolean {
  return /^[0-9]+$/.test(s)
}

/** Python str.isalpha() — Unicode letters only. */
function isAlpha(s: string): boolean {
  return /^\p{L}+$/u.test(s)
}

export class EnhancedValidator {
  checkDigits = false
  validationStats: ValidationStats = this.freshStats()

  private freshStats(): ValidationStats {
    return {
      total_tokens: 0,
      consumed_tokens: 0,
      orphan_tokens: 0,
      exact_matches: 0,
      partial_matches: 0,
      failed_matches: 0,
      duplicate_allowances: 0,
    }
  }

  /**
   * Tokenizes the PDF text. Python uses `\b\w+\b|\d+|[A-Z]+` where `\w` is
   * Unicode-aware; the JS equivalent is `[\p{L}\p{N}_]+` so accented shade
   * names (ROSÉ) stay one token like in Python.
   */
  tokenizePdfText(pdfText: string): PdfToken[] {
    const text = pdfText.toUpperCase().trim()
    const tokens: PdfToken[] = []
    const pattern = /[\p{L}\p{N}_]+/gu
    let match: RegExpExecArray | null
    while ((match = pattern.exec(text)) !== null) {
      tokens.push({
        text: match[0],
        start_pos: match.index,
        end_pos: match.index + match[0].length,
        consumed: false,
        consumed_by: null,
        type: this.classifyToken(match[0]),
      })
    }
    this.validationStats.total_tokens = tokens.length
    return tokens
  }

  classifyToken(token: string): TokenType {
    if (isDigits(token)) {
      if (token.length === 4) return 'digits_4'
      if (token.length === 2 || token.length === 3) return 'shade_number'
      return 'number'
    }
    if (isAlpha(token)) {
      if (token === 'WATERPROOF' || token === 'WTP') return 'waterproof_tag'
      if (token.length > 1) return 'shade_name'
      return 'letter'
    }
    return 'mixed'
  }

  private normalizeExcelData(excelData: LithoRecord[]): NormalizedRow[] {
    return excelData.map((row) => {
      const facingValue = safeStr(row['PRODUCT FACING SL'])
      const isFrame = facingValue === 'FRAME'
      const isSpaceSaver = ['UPC', 'PRODUCT DESCRIPTION', 'SHADE NAME'].some(
        (field) => safeStr(row[field]) === 'SPACE_SAVER',
      )
      const shadeName = safeStr(row['SHADE NAME'])
      const normalized =
        shadeName && shadeName.includes('WTP')
          ? shadeName.replaceAll('WTP', 'WATERPROOF')
          : shadeName
      return {
        row,
        SHADE_NAME_NORMALIZED: normalized,
        _is_frame: isFrame,
        _is_space_saver: isSpaceSaver,
        _should_validate: !(isFrame || isSpaceSaver),
      }
    })
  }

  /**
   * Finds the first match of `searchText` in the tokens starting at `startIndex`.
   * Returns [startIdx, firstToken, numTokensConsumed] or null.
   */
  findTokenMatch(
    tokens: PdfToken[],
    searchText: string,
    startIndex = 0,
    tokenTypes: TokenType[] | null = null,
  ): [number, PdfToken, number] | null {
    if (!searchText) return null

    const search = searchText.toUpperCase().trim()
    const searchWords = search.split(/\s+/).filter((w) => w.length > 0)

    // CASE 1: multi-token search (compound names like "FOREST BROWN")
    if (searchWords.length > 1) {
      for (let i = startIndex; i <= tokens.length - searchWords.length; i++) {
        const slice = tokens.slice(i, i + searchWords.length)
        if (slice.some((t) => t.consumed)) continue
        let match = true
        for (let j = 0; j < searchWords.length; j++) {
          if (tokens[i + j].text !== searchWords[j]) {
            match = false
            break
          }
        }
        if (match) return [i, tokens[i], searchWords.length]
      }
    }

    // CASE 2: single-token search
    for (let i = startIndex; i < tokens.length; i++) {
      const token = tokens[i]
      if (token.consumed) continue
      if (tokenTypes && !tokenTypes.includes(token.type)) continue
      if (token.text === search) return [i, token, 1]
      // Partial match for long names
      if (search.length > 3 && token.text.includes(search)) return [i, token, 1]
    }

    return null
  }

  private consumeToken(tokens: PdfToken[], tokenIndex: number, consumedBy: string, numTokens = 1): void {
    for (let i = tokenIndex; i < Math.min(tokenIndex + numTokens, tokens.length); i++) {
      if (i >= 0 && i < tokens.length) {
        tokens[i].consumed = true
        tokens[i].consumed_by = consumedBy
        this.validationStats.consumed_tokens += 1
      }
    }
  }

  /** Same-shade-number + same-shade-name rows count as legitimate duplicates. */
  checkDuplicateAllowance(excelData: LithoRecord[], currentIndex: number): boolean {
    if (currentIndex === 0) return false
    const currentRow = excelData[currentIndex]
    for (let i = 0; i < currentIndex; i++) {
      const prevRow = excelData[i]
      if (
        safeStr(currentRow['SHADE NUMBER']) === safeStr(prevRow['SHADE NUMBER']) &&
        safeStr(currentRow['SHADE NAME']) === safeStr(prevRow['SHADE NAME'])
      ) {
        return true
      }
    }
    return false
  }

  validateEnhanced(pdfText: string, excelData: LithoRecord[]): EnhancedValidationResult {
    this.validationStats = this.freshStats()

    if (!excelData.length || !pdfText) {
      return { results: [], stats: this.validationStats, errors: ['Données manquantes'] }
    }

    const tokens = this.tokenizePdfText(pdfText)
    const normalizedExcel = this.normalizeExcelData(excelData)

    const results: EnhancedEntryResult[] = []
    let currentPosition = 0
    const errors: string[] = []

    normalizedExcel.forEach((row, idx) => {
      const result = this.validateSingleEntry(tokens, row, idx, currentPosition)
      results.push(result)
      // PARITY: reproduces a Python bug — validate_enhanced reads
      // `result.get('last_token_position')` at the TOP level of the dict, but
      // the key only exists inside validation_details, so the cross-row
      // position never advances (every row starts searching at 0). Token
      // consumption still prevents double-matching.
    })

    const orphanTokens = tokens.filter((t) => !t.consumed)
    this.validationStats.orphan_tokens = orphanTokens.length

    const expectedValidations = normalizedExcel.filter((r) => r._should_validate).length
    const actualValidations = results.filter((r) => r.overall).length
    if (expectedValidations !== actualValidations) {
      errors.push(`Décompte incorrect: ${actualValidations}/${expectedValidations} validations`)
    }

    return {
      results,
      stats: this.validationStats,
      errors,
      orphan_tokens: orphanTokens.map((t) => t.text),
      summary: {
        expected_validations: expectedValidations,
        actual_validations: actualValidations,
        success_rate: expectedValidations > 0 ? (actualValidations / expectedValidations) * 100 : 0,
      },
    }
  }

  private validateSingleEntry(
    tokens: PdfToken[],
    row: NormalizedRow,
    rowIndex: number,
    startPosition: number,
  ): EnhancedEntryResult {
    const entryId = `Row_${rowIndex + 1}`

    const result: EnhancedEntryResult = {
      shade_number: true,
      shade_name: true,
      digits: true,
      facing: (row.row['PRODUCT FACING SL'] ?? '') as string | number,
      is_mixed: false,
      is_cubby: false,
      is_frame: row._is_frame,
      is_space_saver: row._is_space_saver,
      overall: true,
      validation_details: {
        method: 'enhanced',
        tokens_used: [],
        start_position: startPosition,
        last_token_position: null,
      },
    }

    if (!row._should_validate) return result

    // PARITY: reproduces a Python bug — the duplicate check receives
    // `[row] + [{}] * row_index`, so every row with index >= 2 is treated as a
    // legitimate duplicate ('' == ''). Kept 1:1 so web results match desktop.
    const paddedData: LithoRecord[] = [row.row, ...Array.from({ length: rowIndex }, () => ({}) as LithoRecord)]
    const isDuplicate = this.checkDuplicateAllowance(paddedData, rowIndex)
    if (isDuplicate) this.validationStats.duplicate_allowances += 1

    let currentPos = startPosition

    // 1. Shade number
    const shadeNumber = safeStr(row.row['SHADE NUMBER'])
    if (shadeNumber) {
      const match = this.findTokenMatch(tokens, shadeNumber, currentPos, ['shade_number', 'number'])
      if (match) {
        const [tokenIdx, token, numTokens] = match
        if (!isDuplicate) this.consumeToken(tokens, tokenIdx, `${entryId}_SHADE_NUMBER`, numTokens)
        result.validation_details.tokens_used.push({
          field: 'SHADE_NUMBER',
          token: token.text,
          position: tokenIdx,
          num_tokens: numTokens,
        })
        currentPos = tokenIdx + numTokens
        result.validation_details.last_token_position = tokenIdx + numTokens - 1
        this.validationStats.exact_matches += 1
      } else {
        result.shade_number = false
        this.validationStats.failed_matches += 1
      }
    }

    // 2. Shade name
    const shadeName = row.SHADE_NAME_NORMALIZED
    if (shadeName) {
      const match = this.findTokenMatch(tokens, shadeName, currentPos, ['shade_name', 'mixed'])
      if (match) {
        const [tokenIdx, token, numTokens] = match
        if (!isDuplicate) this.consumeToken(tokens, tokenIdx, `${entryId}_SHADE_NAME`, numTokens)
        result.validation_details.tokens_used.push({
          field: 'SHADE_NAME',
          token: token.text,
          position: tokenIdx,
          num_tokens: numTokens,
        })
        currentPos = tokenIdx + numTokens
        result.validation_details.last_token_position = tokenIdx + numTokens - 1
        this.validationStats.exact_matches += 1
      } else {
        result.shade_name = false
        this.validationStats.failed_matches += 1
      }
    }

    // 3. 4 DIGITS (when enabled)
    if (this.checkDigits) {
      const digits = safeStr(row.row['4 DIGITS'])
      if (digits) {
        const match = this.findTokenMatch(tokens, digits, currentPos, ['digits_4', 'number'])
        if (match) {
          const [tokenIdx, token, numTokens] = match
          if (!isDuplicate) this.consumeToken(tokens, tokenIdx, `${entryId}_4DIGITS`, numTokens)
          result.validation_details.tokens_used.push({
            field: '4_DIGITS',
            token: token.text,
            position: tokenIdx,
            num_tokens: numTokens,
          })
          currentPos = tokenIdx + numTokens
          result.validation_details.last_token_position = tokenIdx + numTokens - 1
          this.validationStats.exact_matches += 1
        } else {
          result.digits = false
          this.validationStats.failed_matches += 1
        }
      }
    }

    const criteria = [result.shade_number, result.shade_name]
    if (this.checkDigits && safeStr(row.row['4 DIGITS'])) {
      criteria.push(result.digits)
    }
    result.overall = criteria.every(Boolean)

    return result
  }
}

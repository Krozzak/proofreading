// Port of core/validator.py — legacy validation engine (default) + CUBBY
// matrix handling, with the enhanced engine available as a toggle.
import type { BrandConfig } from './brandConfigs'
import { mnyConfig } from './brandConfigs'
import { EnhancedValidator, type EnhancedEntryResult, type EnhancedValidationResult } from './enhancedValidator'
import { safeStr } from './textSafe'
import type { LithoRecord } from './types'

export interface CubbyItem {
  upc: string
  shade_name: string
  shade_number: string
  is_frame: boolean
}

export interface LegacyEntryResult {
  shade_number: boolean
  shade_name: boolean
  digits: boolean
  facing: string | number
  is_mixed: boolean
  is_cubby: boolean
  is_frame: boolean
  is_space_saver: boolean
  overall: boolean
}

export interface CubbyResult {
  is_cubby: true
  cubby_dimensions: [number, number]
  matrix_data: CubbyItem[][]
  description: string
}

export type ValidationResult = LegacyEntryResult | CubbyResult | EnhancedEntryResult

export function isCubbyResult(r: ValidationResult): r is CubbyResult {
  return r.is_cubby === true && 'matrix_data' in r
}

export interface ComparisonStats {
  comparison_possible?: boolean
  reason?: string
  total_entries?: number
  legacy_success?: number
  enhanced_success?: number
  agreements?: number
  disagreements?: number
  detailed_differences?: unknown[]
  agreement_rate?: number
  legacy_success_rate?: number
  enhanced_success_rate?: number
}

export class LithoValidator {
  checkDigits = false
  useEnhancedValidation = false
  brandConfig: BrandConfig
  enhancedValidator = new EnhancedValidator()

  constructor(brandConfig: BrandConfig = mnyConfig) {
    this.brandConfig = brandConfig
  }

  setBrandConfig(brandConfig: BrandConfig): void {
    this.brandConfig = brandConfig
  }

  setEnhancedValidation(enabled: boolean): void {
    this.useEnhancedValidation = enabled
  }

  getValidationMethod(): 'legacy' | 'enhanced' {
    return this.useEnhancedValidation ? 'enhanced' : 'legacy'
  }

  /** Extracts CUBBY dimensions (faces, tiers) from the description, e.g. '10F2T'. */
  extractCubbyDimensions(description: string): [number, number] | null {
    const match = /(\d+)F(\d+)T/.exec(description.toUpperCase())
    if (match) {
      const faces = parseInt(match[1], 10)
      const tiers = parseInt(match[2], 10)
      if (!Number.isNaN(faces) && !Number.isNaN(tiers)) return [faces, tiers]
    }

    // Fallback: explicit 'CUBBY' keyword with separate dimension tokens.
    // strictInt mirrors Python int(): whole string must be an integer literal.
    const strictInt = (s: string): number | null =>
      /^[+-]?\d+$/.test(s.trim()) ? parseInt(s.trim(), 10) : null
    if (description.toUpperCase().includes('CUBBY')) {
      for (const part of description.split(/\s+/)) {
        if (part.includes('F') && part.includes('T')) {
          const faces = strictInt(part.split('F')[0])
          const afterF = part.split('F')[1] ?? ''
          const tiers = strictInt(afterF.split('T')[0])
          if (faces !== null && tiers !== null) return [faces, tiers]
        }
      }
      // Default CUBBY dimensions when unspecified
      return [10, 2]
    }

    return null
  }

  /** Sorts the rows by the comma-separated 'UPC SEQUENCE' of the first row. */
  sortByUpcSequence(excelData: LithoRecord[]): LithoRecord[] {
    if (!excelData.length || !('UPC SEQUENCE' in excelData[0])) return excelData

    const upcSequenceStr = String(excelData[0]['UPC SEQUENCE'] ?? '').trim()
    if (!upcSequenceStr) return excelData

    const targetSequence = upcSequenceStr
      .split(',')
      .map((u) => u.trim())
      .filter((u) => u.length > 0)

    const upcOrderMap = new Map<string, number>()
    targetSequence.forEach((upc, i) => {
      if (!upcOrderMap.has(upc)) upcOrderMap.set(upc, i)
    })

    // Array.prototype.sort is stable (like Python sorted), unknown UPCs go last.
    return [...excelData].sort((a, b) => {
      const ka = upcOrderMap.get(String(a['UPC'] ?? '').trim()) ?? targetSequence.length
      const kb = upcOrderMap.get(String(b['UPC'] ?? '').trim()) ?? targetSequence.length
      return ka - kb
    })
  }

  /** Log-only in the desktop app: checks Excel row order against the target sequence. */
  validateUpcSequenceOrder(excelData: LithoRecord[], targetSequence: string[]): boolean {
    const excelUpcs = excelData.map((row) => String(row['UPC'] ?? '').trim())
    const mismatches: string[] = []
    const minLength = Math.min(targetSequence.length, excelUpcs.length)
    for (let i = 0; i < minLength; i++) {
      if (targetSequence[i] !== excelUpcs[i]) {
        mismatches.push(`Position ${i + 1}: attendu '${targetSequence[i]}', trouvé '${excelUpcs[i]}'`)
      }
    }
    if (targetSequence.length !== excelUpcs.length) {
      mismatches.push(`Longueurs différentes: séquence=${targetSequence.length}, excel=${excelUpcs.length}`)
    }
    return mismatches.length === 0
  }

  validate(
    pdfText: string,
    excelData: LithoRecord[],
  ): ValidationResult[] {
    this.enhancedValidator.checkDigits = this.checkDigits
    if (this.useEnhancedValidation) {
      return this.validateEnhancedAdapter(pdfText, excelData)
    }
    return this.validateLegacy(pdfText, excelData)
  }

  /** Runs both engines and returns them with agreement metrics (debug feature). */
  validateComparisonMode(pdfText: string, excelData: LithoRecord[]): {
    legacy_results: ValidationResult[]
    enhanced_results: ValidationResult[]
    comparison_stats: ComparisonStats
    mode: 'comparison'
  } {
    this.enhancedValidator.checkDigits = this.checkDigits
    const legacyResults = this.validateLegacy(pdfText, excelData)
    const enhancedResults = this.validateEnhancedAdapter(pdfText, excelData)
    return {
      legacy_results: legacyResults,
      enhanced_results: enhancedResults,
      comparison_stats: this.compareValidationResults(legacyResults, enhancedResults),
      mode: 'comparison',
    }
  }

  /** Full enhanced result (stats, orphan tokens) for the UI hint text. */
  validateEnhancedFull(pdfText: string, excelData: LithoRecord[]): EnhancedValidationResult {
    this.enhancedValidator.checkDigits = this.checkDigits
    return this.enhancedValidator.validateEnhanced(pdfText, excelData)
  }

  private validateEnhancedAdapter(pdfText: string, excelData: LithoRecord[]): ValidationResult[] {
    const enhancedResult = this.enhancedValidator.validateEnhanced(pdfText, excelData)
    return enhancedResult.results ?? []
  }

  private validateLegacy(pdfText: string, excelData: LithoRecord[]): ValidationResult[] {
    const results: ValidationResult[] = []
    if (!excelData.length) return results

    const upperText = pdfText.toUpperCase()

    // Description column probe order matters ('DECRIPTION' first, as in the briefs)
    let description = ''
    for (const colName of ['DECRIPTION', 'DESCRIPTION', 'PRODUCT DESCRIPTION', 'DESC']) {
      if (colName in excelData[0]) {
        description = String(excelData[0][colName] ?? '')
        break
      }
    }

    const cubbyDimensions = this.extractCubbyDimensions(description)
    const isCubby = cubbyDimensions !== null

    if (isCubby && cubbyDimensions) {
      const [faces, tiers] = cubbyDimensions
      const sortedExcelData = this.sortByUpcSequence(excelData)

      if ('UPC SEQUENCE' in excelData[0]) {
        const upcSequenceStr = String(excelData[0]['UPC SEQUENCE'] ?? '').trim()
        if (upcSequenceStr) {
          const targetSequence = upcSequenceStr
            .split(',')
            .map((u) => u.trim())
            .filter((u) => u.length > 0)
          this.validateUpcSequenceOrder(sortedExcelData, targetSequence)
        }
      }

      const matrixData = this.organizeCubbyMatrix(sortedExcelData, faces, tiers)
      return [
        {
          is_cubby: true,
          cubby_dimensions: cubbyDimensions,
          matrix_data: matrixData,
          description,
        },
      ]
    }

    // Facing check (real products only): MIXED = more than one distinct integer facing
    const facings = new Set<number>()
    for (const row of excelData) {
      const facing = safeStr(row['PRODUCT FACING SL'])
      if (facing && !['FRAME', 'SPACE_SAVER', 'CUBBY'].includes(facing)) {
        if (/^[+-]?\d+$/.test(facing)) {
          facings.add(parseInt(facing, 10))
        }
      }
    }
    const isMixed = facings.size > 1

    for (const row of excelData) {
      const facingValue = safeStr(row['PRODUCT FACING SL'])
      const isFrame = facingValue === 'FRAME'
      const isSpaceSaver = ['UPC', 'PRODUCT DESCRIPTION', 'SHADE NAME'].some(
        (field) => safeStr(row[field]) === 'SPACE_SAVER',
      )

      const validationDetails: LegacyEntryResult = {
        shade_number: true,
        shade_name: true,
        digits: true,
        facing: (row['PRODUCT FACING SL'] ?? '') as string | number,
        is_mixed: isMixed,
        is_cubby: isCubby,
        is_frame: isFrame,
        is_space_saver: isSpaceSaver,
        overall: true, // FRAME and SPACE_SAVER rows stay true unconditionally
      }

      if (!(isFrame || isSpaceSaver)) {
        const shadeNumber = safeStr(row['SHADE NUMBER'])
        if (shadeNumber) {
          validationDetails.shade_number = upperText.includes(shadeNumber)
        }

        const shadeName = safeStr(row['SHADE NAME'])
        if (shadeName) {
          validationDetails.shade_name = this.validateShadeName(shadeName, upperText)
        }

        const digits = safeStr(row['4 DIGITS'])
        const shouldValidateDigits = this.brandConfig.requiresDigitsValidation()

        if (digits && this.checkDigits && shouldValidateDigits) {
          validationDetails.digits = upperText.includes(digits)
        } else {
          validationDetails.digits = true
        }

        const validationCriteria = [validationDetails.shade_number, validationDetails.shade_name]
        if (this.checkDigits && shouldValidateDigits && digits) {
          validationCriteria.push(validationDetails.digits)
        }
        validationDetails.overall = validationCriteria.every(Boolean)
      }

      results.push(validationDetails)
    }

    return results
  }

  /** Shade name matching with the WTP ↔ WATERPROOF equivalence. */
  validateShadeName(shadeName: string, upperPdfText: string): boolean {
    const upper = shadeName.toUpperCase()
    if (upperPdfText.includes(upper)) return true
    // Python str.replace replaces ALL occurrences → replaceAll; 'WTP' branch
    // wins when both tags are present (if/elif).
    if (upper.includes('WTP')) {
      return upperPdfText.includes(upper.replaceAll('WTP', 'WATERPROOF'))
    } else if (upper.includes('WATERPROOF')) {
      return upperPdfText.includes(upper.replaceAll('WATERPROOF', 'WTP'))
    }
    return false
  }

  /** Lays the CUBBY rows out as a faces × tiers matrix with automatic tier rollover. */
  organizeCubbyMatrix(excelData: LithoRecord[], faces: number, tiers: number): CubbyItem[][] {
    const matrix: (CubbyItem | null)[][] = Array.from({ length: tiers }, () =>
      Array.from({ length: faces }, () => null),
    )

    let currentTier = 0
    let currentPosition = 0
    const upcPositionPattern = /UPC\.(\d+)/i

    for (const row of excelData) {
      const upc = String(row['UPC'] ?? '').trim()

      const item: CubbyItem = {
        upc,
        shade_name: String(row['SHADE NAME'] ?? '').trim(),
        shade_number: String(row['SHADE NUMBER'] ?? '').trim(),
        is_frame: upc.toUpperCase() === 'FRAME',
      }

      let targetPosition: number
      const upcMatch = upcPositionPattern.exec(upc)
      if (upcMatch) {
        const detectedPosition = parseInt(upcMatch[1], 10)
        // Tier change: sequence went back to UPC.1 while we were past position 1
        if (detectedPosition === 1 && currentPosition > 1) {
          currentTier += 1
          currentPosition = 0
        }
        targetPosition = detectedPosition - 1
      } else {
        targetPosition = currentPosition
      }

      if (currentTier < tiers && targetPosition < faces) {
        matrix[currentTier][targetPosition] = item
        currentPosition = targetPosition + 1
        if (currentPosition >= faces) {
          currentTier += 1
          currentPosition = 0
        }
      }
      // Out-of-bounds rows are skipped (desktop logs them only)
    }

    // Fill empty cells
    for (let tier = 0; tier < tiers; tier++) {
      for (let pos = 0; pos < faces; pos++) {
        if (matrix[tier][pos] === null) {
          matrix[tier][pos] = { upc: 'EMPTY', shade_name: '', shade_number: '', is_frame: false }
        }
      }
    }

    return matrix as CubbyItem[][]
  }

  private compareValidationResults(
    legacyResults: ValidationResult[],
    enhancedResults: ValidationResult[],
  ): ComparisonStats {
    if (!legacyResults.length || !enhancedResults.length) {
      return { comparison_possible: false, reason: 'Résultats manquants' }
    }

    const getOverall = (r: ValidationResult): boolean =>
      'overall' in r ? Boolean(r.overall) : false
    const getDetail = (r: ValidationResult, key: 'shade_number' | 'shade_name' | 'digits'): boolean =>
      key in r ? Boolean((r as LegacyEntryResult)[key]) : false

    const stats: ComparisonStats = {
      total_entries: legacyResults.length,
      legacy_success: legacyResults.filter(getOverall).length,
      enhanced_success: enhancedResults.filter(getOverall).length,
      agreements: 0,
      disagreements: 0,
      detailed_differences: [],
    }

    const minLength = Math.min(legacyResults.length, enhancedResults.length)
    for (let i = 0; i < minLength; i++) {
      const legacy = legacyResults[i]
      const enhanced = enhancedResults[i]
      if (getOverall(legacy) === getOverall(enhanced)) {
        stats.agreements! += 1
      } else {
        stats.disagreements! += 1
        stats.detailed_differences!.push({
          entry_index: i,
          legacy_result: getOverall(legacy),
          enhanced_result: getOverall(enhanced),
          legacy_details: {
            shade_number: getDetail(legacy, 'shade_number'),
            shade_name: getDetail(legacy, 'shade_name'),
            digits: getDetail(legacy, 'digits'),
          },
          enhanced_details: {
            shade_number: getDetail(enhanced, 'shade_number'),
            shade_name: getDetail(enhanced, 'shade_name'),
            digits: getDetail(enhanced, 'digits'),
          },
        })
      }
    }

    stats.agreement_rate = minLength > 0 ? (stats.agreements! / minLength) * 100 : 0
    stats.legacy_success_rate = (stats.legacy_success! / legacyResults.length) * 100
    stats.enhanced_success_rate = (stats.enhanced_success! / enhancedResults.length) * 100

    return stats
  }
}

// Port of core/data_collector.py — aggregates validation results into the
// structure the report generator consumes. Dependencies are injected as plain
// functions so the module stays framework-free.
import type { LithoRecord, LithoValidation } from './types'
import type { ValidationResult } from './validator'
import { isCubbyResult } from './validator'

/** Shape returned by SessionManager.get_session_info() in the desktop app. */
export interface SessionInfo {
  name: string
  created: string
  updated: string
  pdf_folder: string
  excel_file: string
  validations_count: number
  file_path: string | null
}

export interface CollectorDeps {
  getSessionInfo(): SessionInfo
  getAllLithoCodes(): string[]
  getDataForLitho(code: string): LithoRecord[]
  getTextForLitho(code: string): string
  validate(pdfText: string, excelData: LithoRecord[]): ValidationResult[]
  getLithoStatus(code: string): LithoValidation | null
  checkDigits: boolean
  /** Injected so tests stay deterministic (Date.now is fine in the app). */
  now?: () => string
}

export type LithoSummary = Record<string, string | number | boolean>
export type DetailRow = Record<string, string | number | boolean>

export interface CollectedData {
  session_info: SessionInfo
  global_statistics: Record<string, string | number | boolean>
  litho_summaries: LithoSummary[]
  litho_details: DetailRow[]
  generation_date: string
  validator_settings: { check_digits: boolean }
}

/** Python round(x, 1) — round-half-to-even at 1 decimal. */
export function round1(x: number): number {
  const scaled = x * 10
  const floor = Math.floor(scaled)
  const diff = scaled - floor
  if (Math.abs(diff - 0.5) < 1e-9) {
    return (floor % 2 === 0 ? floor : floor + 1) / 10
  }
  return Math.round(scaled) / 10
}

type EntryLike = {
  is_cubby?: boolean
  is_mixed?: boolean
  is_frame?: boolean
  is_space_saver?: boolean
  shade_number?: boolean
  shade_name?: boolean
  digits?: boolean
  overall?: boolean
}

export function collectAllValidationData(deps: CollectorDeps): CollectedData {
  const sessionInfo = deps.getSessionInfo()
  const allLithoCodes = deps.getAllLithoCodes()

  const validationResults: LithoSummary[] = []
  const lithoDetails: DetailRow[] = []

  for (const lithoCode of allLithoCodes) {
    const excelData = deps.getDataForLitho(lithoCode)
    if (!excelData.length) continue

    const pdfText = deps.getTextForLitho(lithoCode)
    const validationResult = deps.validate(pdfText, excelData)
    const sessionStatus = deps.getLithoStatus(lithoCode)

    validationResults.push(
      analyzeLithoResults(lithoCode, excelData, validationResult, sessionStatus, deps.checkDigits),
    )

    const count = Math.min(excelData.length, validationResult.length)
    for (let i = 0; i < count; i++) {
      lithoDetails.push(
        createDetailRow(
          lithoCode,
          i,
          excelData[i],
          validationResult[i] as EntryLike,
          sessionStatus,
          deps.checkDigits,
        ),
      )
    }
  }

  return {
    session_info: sessionInfo,
    global_statistics: calculateGlobalStatistics(validationResults, deps.checkDigits),
    litho_summaries: validationResults,
    litho_details: lithoDetails,
    generation_date: deps.now ? deps.now() : new Date().toISOString(),
    validator_settings: { check_digits: deps.checkDigits },
  }
}

function analyzeLithoResults(
  lithoCode: string,
  excelData: LithoRecord[],
  validationResult: ValidationResult[],
  sessionStatus: LithoValidation | null,
  checkDigits: boolean,
): LithoSummary {
  const first = validationResult[0] as EntryLike | undefined
  const isCubby = Boolean(first?.is_cubby)
  const isMixed = Boolean(first?.is_mixed)
  const hasSpaceSavers = validationResult.some((v) => (v as EntryLike).is_space_saver)

  if (isCubby && validationResult.length && isCubbyResult(validationResult[0])) {
    const cubby = validationResult[0]
    const [faces, tiers] = cubby.cubby_dimensions
    return {
      litho_code: lithoCode,
      type: 'CUBBY',
      description: cubby.description,
      dimensions: `${faces}F x ${tiers}T`,
      total_positions: faces * tiers,
      validation_status: 'N/A',
      session_status: sessionStatus ? sessionStatus.status : 'pending',
      session_comment: sessionStatus ? sessionStatus.comment : '',
      session_date: sessionStatus ? sessionStatus.date : '',
      products_count: excelData.length,
      overall_success: true, // CUBBYs are considered valid
      shade_number_success: 'N/A',
      shade_name_success: 'N/A',
      digits_success: 'N/A',
    }
  }

  const validProducts = validationResult.filter(
    (v) => !(v as EntryLike).is_frame && !(v as EntryLike).is_space_saver,
  ) as EntryLike[]

  if (validProducts.length) {
    const totalValid = validProducts.length
    const shadeNumberOk = validProducts.filter((v) => v.shade_number).length
    const shadeNameOk = validProducts.filter((v) => v.shade_name).length
    const digitsOk = validProducts.filter((v) => v.digits).length
    const overallOk = validProducts.filter((v) => v.overall).length

    const lithoTypes: string[] = []
    if (isMixed) lithoTypes.push('MIXED')
    if (hasSpaceSavers) lithoTypes.push('SPACE_SAVER')
    const lithoType = lithoTypes.length ? lithoTypes.join(' + ') : 'Standard'

    return {
      litho_code: lithoCode,
      type: lithoType,
      description: String(excelData[0]?.['DECRIPTION'] ?? ''),
      products_count: excelData.length,
      valid_products_count: totalValid,
      session_status: sessionStatus ? sessionStatus.status : 'pending',
      session_comment: sessionStatus ? sessionStatus.comment : '',
      session_date: sessionStatus ? sessionStatus.date : '',
      overall_success: `${overallOk}/${totalValid}`,
      overall_percentage: round1((overallOk / totalValid) * 100),
      shade_number_success: `${shadeNumberOk}/${totalValid}`,
      shade_number_percentage: round1((shadeNumberOk / totalValid) * 100),
      shade_name_success: `${shadeNameOk}/${totalValid}`,
      shade_name_percentage: round1((shadeNameOk / totalValid) * 100),
      digits_success: checkDigits ? `${digitsOk}/${totalValid}` : 'N/A',
      digits_percentage: checkDigits ? round1((digitsOk / totalValid) * 100) : 'N/A',
    }
  }

  return {
    litho_code: lithoCode,
    type: 'Aucun produit',
    description: '',
    products_count: excelData.length,
    valid_products_count: 0,
    session_status: sessionStatus ? sessionStatus.status : 'pending',
    session_comment: sessionStatus ? sessionStatus.comment : '',
    session_date: sessionStatus ? sessionStatus.date : '',
    overall_success: '0/0',
    overall_percentage: 0,
    shade_number_success: '0/0',
    shade_number_percentage: 0,
    shade_name_success: '0/0',
    shade_name_percentage: 0,
    digits_success: '0/0',
    digits_percentage: 0,
  }
}

function createDetailRow(
  lithoCode: string,
  rowIndex: number,
  dataRow: LithoRecord,
  validationRow: EntryLike,
  sessionStatus: LithoValidation | null,
  checkDigits: boolean,
): DetailRow {
  const isFrameOrSaver = Boolean(validationRow.is_frame) || Boolean(validationRow.is_space_saver)
  return {
    litho_code: lithoCode,
    row_index: rowIndex + 1,
    upc: dataRow['UPC'] ?? '',
    product_description: dataRow['PRODUCT DESCRIPTION'] ?? '',
    shade_name: dataRow['SHADE NAME'] ?? '',
    shade_number: dataRow['SHADE NUMBER'] ?? '',
    product_facing: dataRow['PRODUCT FACING SL'] ?? '',
    digits_4: dataRow['4 DIGITS'] ?? '',
    is_frame: Boolean(validationRow.is_frame),
    is_space_saver: Boolean(validationRow.is_space_saver),
    shade_number_valid: !isFrameOrSaver ? Boolean(validationRow.shade_number) : 'N/A',
    shade_name_valid: !isFrameOrSaver ? Boolean(validationRow.shade_name) : 'N/A',
    digits_valid: !isFrameOrSaver && checkDigits ? Boolean(validationRow.digits) : 'N/A',
    overall_valid: !isFrameOrSaver ? Boolean(validationRow.overall) : 'N/A',
    session_status: sessionStatus ? sessionStatus.status : 'pending',
  }
}

function calculateGlobalStatistics(
  lithoSummaries: LithoSummary[],
  checkDigits: boolean,
): Record<string, string | number | boolean> {
  const totalLithos = lithoSummaries.length

  const approvedCount = lithoSummaries.filter((l) => l['session_status'] === 'approved').length
  const rejectedCount = lithoSummaries.filter((l) => l['session_status'] === 'rejected').length
  const pendingCount = totalLithos - approvedCount - rejectedCount

  const cubbyCount = lithoSummaries.filter((l) => l['type'] === 'CUBBY').length
  const mixedCount = lithoSummaries.filter((l) => String(l['type'] ?? '').includes('MIXED')).length
  const spaceSaverCount = lithoSummaries.filter((l) =>
    String(l['type'] ?? '').includes('SPACE_SAVER'),
  ).length
  const standardCount = lithoSummaries.filter((l) => l['type'] === 'Standard').length

  const nonCubby = lithoSummaries.filter((l) => l['type'] !== 'CUBBY')

  let avgOverall = 0
  let avgShadeNumber = 0
  let avgShadeName = 0
  let avgDigits = 0
  if (nonCubby.length) {
    const num = (l: LithoSummary, key: string): number =>
      typeof l[key] === 'number' ? (l[key] as number) : 0
    avgOverall = nonCubby.reduce((s, l) => s + num(l, 'overall_percentage'), 0) / nonCubby.length
    avgShadeNumber =
      nonCubby.reduce((s, l) => s + num(l, 'shade_number_percentage'), 0) / nonCubby.length
    avgShadeName =
      nonCubby.reduce((s, l) => s + num(l, 'shade_name_percentage'), 0) / nonCubby.length
    const digitsLithos = nonCubby.filter((l) => l['digits_percentage'] !== 'N/A')
    avgDigits = digitsLithos.length
      ? digitsLithos.reduce((s, l) => s + num(l, 'digits_percentage'), 0) / digitsLithos.length
      : 0
  }

  return {
    total_lithos: totalLithos,
    approved_lithos: approvedCount,
    rejected_lithos: rejectedCount,
    pending_lithos: pendingCount,
    cubby_lithos: cubbyCount,
    mixed_lithos: mixedCount,
    space_saver_lithos: spaceSaverCount,
    standard_lithos: standardCount,
    avg_overall_success: round1(avgOverall),
    avg_shade_number_success: round1(avgShadeNumber),
    avg_shade_name_success: round1(avgShadeName),
    avg_digits_success: avgDigits > 0 ? round1(avgDigits) : 'N/A',
    digits_validation_enabled: checkDigits,
  }
}

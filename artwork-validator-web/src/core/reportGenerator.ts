// Port of core/report_generator.py — builds a neutral ReportModel (list of
// sheets); the exceljs serialization lives in src/lib/excelIO.ts.
// Sheet names, French labels and helper logic are kept verbatim.
import type { CollectedData, LithoSummary } from './dataCollector'

export type ReportCell = string | number | boolean | null

export interface ReportSheet {
  name: string
  columns: string[]
  rows: ReportCell[][]
}

export interface ReportModel {
  sheets: ReportSheet[]
}

export interface ReportDeps {
  /** Returns the extracted PDF text for a litho code ('' when unavailable). */
  getTextForLitho(code: string): string
}

/** First 3 significant lines (len > 10) joined with ' | ', truncated at 200. */
export function extractPdfDescription(lithoCode: string, deps: ReportDeps): string {
  if (!lithoCode) return 'PDF non disponible'
  const pdfText = deps.getTextForLitho(lithoCode)
  if (!pdfText) return 'PDF vide ou illisible'

  const descriptionLines: string[] = []
  for (const rawLine of pdfText.split('\n')) {
    const line = rawLine.trim()
    if (line && line.length > 10) {
      descriptionLines.push(line)
      if (descriptionLines.length >= 3) break
    }
  }
  if (descriptionLines.length) {
    let description = descriptionLines.join(' | ')
    if (description.length > 200) description = description.slice(0, 197) + '...'
    return description
  }
  return 'Description non identifiable'
}

export function getPdfValidationStatus(pdfDescription: string): string {
  if (!pdfDescription || ['PDF non disponible', 'PDF vide ou illisible'].includes(pdfDescription)) {
    return '❌ PDF Invalide'
  }
  if (pdfDescription.includes('Erreur extraction')) return '⚠️ Erreur Lecture'
  if (pdfDescription.includes('Description non identifiable')) return '⚠️ Contenu Unclear'

  const lower = pdfDescription.toLowerCase()
  const positiveKeywords = ['loreal', "l'oreal", 'cosmetic', 'beauty', 'shade', 'color', 'teinte', 'produit']
  const negativeKeywords = ['error', 'erreur', 'invalid', 'corrupt']
  const hasPositive = positiveKeywords.some((k) => lower.includes(k))
  const hasNegative = negativeKeywords.some((k) => lower.includes(k))
  if (hasNegative) return '❌ Contenu Problématique'
  if (hasPositive) return '✅ PDF Valide'
  return '⚠️ À Vérifier'
}

export function mapSessionToValidationStatus(sessionStatus: string | null | undefined): string {
  const mapping: Record<string, string> = {
    approved: '✅ Approuvé',
    rejected: '❌ Rejeté',
    pending: '⏳ En Attente',
  }
  return mapping[sessionStatus ?? ''] ?? '❓ Indéterminé'
}

/** Word-count buckets used in the 'Analyse PDFs' sheet. */
export function categorizePdfSize(wordCount: number): string {
  if (wordCount === 0) return 'Vide'
  if (wordCount < 50) return 'Très petit'
  if (wordCount < 200) return 'Petit'
  if (wordCount < 500) return 'Moyen'
  if (wordCount < 1000) return 'Grand'
  return 'Très grand'
}

/** DataFrame-like: union of keys in first-seen order → columns; missing → null. */
function toSheet(name: string, records: Record<string, ReportCell>[], columnOrder?: string[]): ReportSheet {
  const columns: string[] = []
  for (const record of records) {
    for (const key of Object.keys(record)) {
      if (!columns.includes(key)) columns.push(key)
    }
  }
  const finalColumns = columnOrder ? columnOrder.filter((c) => columns.includes(c)) : columns
  return {
    name,
    columns: finalColumns,
    rows: records.map((r) => finalColumns.map((c) => (c in r ? r[c] : null))),
  }
}

function getPdfStatistics(collectedData: CollectedData, deps: ReportDeps) {
  const stats = { valid_pdfs: 0, invalid_pdfs: 0, to_verify_pdfs: 0, error_pdfs: 0 }
  for (const lithoData of collectedData.litho_summaries) {
    const lithoCode = String(lithoData['litho_code'] ?? '')
    if (!lithoCode) continue
    const status = getPdfValidationStatus(extractPdfDescription(lithoCode, deps))
    if (status.includes('✅')) stats.valid_pdfs += 1
    else if (status.includes('❌')) stats.invalid_pdfs += 1
    else if (status.includes('⚠️')) {
      if (status.includes('Erreur')) stats.error_pdfs += 1
      else stats.to_verify_pdfs += 1
    }
  }
  return stats
}

function createSessionSummary(collectedData: CollectedData, deps: ReportDeps): ReportSheet {
  const sessionInfo = collectedData.session_info
  const globalStats = collectedData.global_statistics
  const pdfStats = getPdfStatistics(collectedData, deps)

  const rows: ReportCell[][] = [
    ['Nom de la Session', sessionInfo.name || 'Non défini'],
    ['Date de Création', sessionInfo.created ? sessionInfo.created.slice(0, 19) : 'Non définie'],
    ['Dernière Modification', sessionInfo.updated ? sessionInfo.updated.slice(0, 19) : 'Non définie'],
    ['Date de Génération du Rapport', collectedData.generation_date.slice(0, 19)],
    ['', ''],
    ['Dossier PDFs', sessionInfo.pdf_folder || 'Non défini'],
    ['Fichier Excel', sessionInfo.excel_file || 'Non défini'],
    ['Fichier Session', sessionInfo.file_path ?? 'Non sauvegardé'],
    ['', ''],
    ['Total Lithos', (globalStats['total_lithos'] as number) ?? 0],
    ['Lithos Approuvées', (globalStats['approved_lithos'] as number) ?? 0],
    ['Lithos Rejetées', (globalStats['rejected_lithos'] as number) ?? 0],
    ['Lithos en Attente', (globalStats['pending_lithos'] as number) ?? 0],
    ['', ''],
    ['📄 STATISTIQUES PDF', ''],
    ['PDFs Valides', pdfStats.valid_pdfs],
    ['PDFs Invalides', pdfStats.invalid_pdfs],
    ['PDFs à Vérifier', pdfStats.to_verify_pdfs],
    ['PDFs avec Erreurs', pdfStats.error_pdfs],
    ['', ''],
    ['Vérification 4 DIGITS', collectedData.validator_settings.check_digits ? 'Activée' : 'Désactivée'],
    ['Lithos CUBBY', (globalStats['cubby_lithos'] as number) ?? 0],
    ['Lithos MIXED', (globalStats['mixed_lithos'] as number) ?? 0],
    ['Lithos SPACE SAVER', (globalStats['space_saver_lithos'] as number) ?? 0],
    ['Lithos Standard', (globalStats['standard_lithos'] as number) ?? 0],
  ]

  return { name: 'Résumé Session', columns: ['Paramètre', 'Valeur'], rows }
}

function createGlobalStats(collectedData: CollectedData, deps: ReportDeps): ReportSheet {
  const g = collectedData.global_statistics
  const pdfStats = getPdfStatistics(collectedData, deps)
  const rows: ReportCell[][] = [
    ['Total Lithos', (g['total_lithos'] as number) ?? 0, 'Nombre total de lithos dans la session'],
    ['', '', ''],
    ['STATUTS DE SESSION', '', ''],
    ['Approuvées', (g['approved_lithos'] as number) ?? 0, 'Lithos validées et approuvées'],
    ['Rejetées', (g['rejected_lithos'] as number) ?? 0, 'Lithos rejetées nécessitant une révision'],
    ['En Attente', (g['pending_lithos'] as number) ?? 0, 'Lithos non encore validées'],
    ['', '', ''],
    ['STATUTS PDF', '', ''],
    ['PDFs Valides', pdfStats.valid_pdfs, 'PDFs avec contenu valide et lisible'],
    ['PDFs Invalides', pdfStats.invalid_pdfs, 'PDFs non disponibles ou illisibles'],
    ['PDFs à Vérifier', pdfStats.to_verify_pdfs, 'PDFs nécessitant une vérification manuelle'],
    ['PDFs avec Erreurs', pdfStats.error_pdfs, 'PDFs avec erreurs de lecture'],
    ['', '', ''],
    ['TYPES DE LITHOS', '', ''],
    ['CUBBY', (g['cubby_lithos'] as number) ?? 0, 'Lithos de type CUBBY (pas de validation de produits)'],
    ['MIXED Facings', (g['mixed_lithos'] as number) ?? 0, 'Lithos avec facings mélangés'],
    ['SPACE SAVER', (g['space_saver_lithos'] as number) ?? 0, 'Lithos contenant des space savers'],
    ['Standard', (g['standard_lithos'] as number) ?? 0, 'Lithos de type standard'],
    ['', '', ''],
    ['MOYENNES DE VALIDATION', '', ''],
    ['Succès Global Moyen', `${g['avg_overall_success'] ?? 0}%`, 'Pourcentage moyen de réussite globale'],
    ['Succès Teintes Moyen', `${g['avg_shade_number_success'] ?? 0}%`, 'Pourcentage moyen de réussite des numéros de teinte'],
    ['Succès Noms Moyen', `${g['avg_shade_name_success'] ?? 0}%`, 'Pourcentage moyen de réussite des noms de teinte'],
    ['Succès 4 DIGITS Moyen', `${g['avg_digits_success'] ?? 'N/A'}`, 'Pourcentage moyen de réussite des 4 DIGITS (si activé)'],
  ]
  return { name: 'Statistiques Globales', columns: ['Métrique', 'Valeur', 'Description'], rows }
}

const LITHO_SUMMARY_COLUMN_ORDER = [
  'litho_code', 'type', 'session_status', 'validation_status',
  'pdf_description', 'pdf_validation_status', 'products_count',
  'valid_products_count', 'overall_success', 'overall_percentage',
  'shade_number_success', 'shade_number_percentage',
  'shade_name_success', 'shade_name_percentage',
  'digits_success', 'digits_percentage',
  'description', 'session_comment', 'session_date',
]

function enhanceSummaries(summaries: LithoSummary[], deps: ReportDeps): Record<string, ReportCell>[] {
  return summaries.map((row) => {
    const lithoCode = String(row['litho_code'] ?? '')
    const pdfDescription = extractPdfDescription(lithoCode, deps)
    return {
      ...(row as Record<string, ReportCell>),
      validation_status: mapSessionToValidationStatus(String(row['session_status'] ?? 'pending')),
      pdf_description: pdfDescription,
      pdf_validation_status: getPdfValidationStatus(pdfDescription),
    }
  })
}

function enhanceStatusLithos(lithos: LithoSummary[], deps: ReportDeps): Record<string, ReportCell>[] {
  return lithos.map((row) => {
    const lithoCode = String(row['litho_code'] ?? '')
    const pdfDescription = extractPdfDescription(lithoCode, deps)
    return {
      ...(row as Record<string, ReportCell>),
      pdf_description: pdfDescription,
      pdf_validation_status: getPdfValidationStatus(pdfDescription),
    }
  })
}

function createPdfAnalysis(collectedData: CollectedData, deps: ReportDeps): Record<string, ReportCell>[] {
  const rows: Record<string, ReportCell>[] = []
  for (const lithoData of collectedData.litho_summaries) {
    const lithoCode = String(lithoData['litho_code'] ?? '')
    if (!lithoCode) continue

    const pdfText = deps.getTextForLitho(lithoCode)
    const pdfDescription = extractPdfDescription(lithoCode, deps)
    const wordCount = pdfText ? pdfText.split(/\s+/).filter((w) => w.length > 0).length : 0
    const charCount = pdfText.length
    const lineCount = pdfText ? pdfText.split('\n').length : 0
    const containsProductInfo = pdfText
      ? ['shade', 'teinte', 'color', 'couleur'].some((k) => pdfText.toLowerCase().includes(k))
      : false
    const containsCodes = pdfText
      ? ['YCA', 'CUBBY', 'MIXED'].some((k) => pdfText.includes(k))
      : false

    rows.push({
      litho_code: lithoCode,
      pdf_description: pdfDescription,
      pdf_validation_status: getPdfValidationStatus(pdfDescription),
      word_count: wordCount,
      character_count: charCount,
      line_count: lineCount,
      contains_product_info: containsProductInfo ? '✅ Oui' : '❌ Non',
      contains_codes: containsCodes ? '✅ Oui' : '❌ Non',
      pdf_size_category: categorizePdfSize(wordCount),
      session_status: (lithoData['session_status'] as string) ?? 'pending',
    })
  }
  return rows
}

function createValidationSummary(collectedData: CollectedData, deps: ReportDeps): Record<string, ReportCell>[] {
  const summaries = collectedData.litho_summaries
  const statusCounts: Record<string, number> = { approved: 0, rejected: 0, pending: 0 }
  const pdfStatusCounts: Record<string, number> = {
    '✅ PDF Valide': 0,
    '❌ PDF Invalide': 0,
    '⚠️ À Vérifier': 0,
    '⚠️ Erreur Lecture': 0,
    '⚠️ Contenu Unclear': 0,
    '❌ Contenu Problématique': 0,
  }

  for (const lithoData of summaries) {
    const sessionStatus = String(lithoData['session_status'] ?? 'pending')
    if (sessionStatus in statusCounts) statusCounts[sessionStatus] += 1
    const lithoCode = String(lithoData['litho_code'] ?? '')
    const status = getPdfValidationStatus(extractPdfDescription(lithoCode, deps))
    if (status in pdfStatusCounts) pdfStatusCounts[status] += 1
  }

  const rows: Record<string, ReportCell>[] = []
  const pct = (count: number): string =>
    summaries.length ? `${((count / summaries.length) * 100).toFixed(1)}%` : '0%'

  for (const [status, count] of Object.entries(statusCounts)) {
    rows.push({
      Catégorie: 'Statut Session',
      Type: mapSessionToValidationStatus(status),
      Nombre: count,
      Pourcentage: pct(count),
      Description: `Lithos avec statut de session: ${status}`,
    })
  }
  for (const [pdfStatus, count] of Object.entries(pdfStatusCounts)) {
    if (count > 0) {
      rows.push({
        Catégorie: 'Statut PDF',
        Type: pdfStatus,
        Nombre: count,
        Pourcentage: pct(count),
        Description: `PDFs avec statut: ${pdfStatus}`,
      })
    }
  }
  return rows
}

/** Builds the full 8-sheet report model (conditional sheets included when non-empty). */
export function generateReportModel(collectedData: CollectedData, deps: ReportDeps): ReportModel {
  const sheets: ReportSheet[] = []

  sheets.push(createSessionSummary(collectedData, deps))
  sheets.push(createGlobalStats(collectedData, deps))
  sheets.push(
    toSheet('Résumé par Litho', enhanceSummaries(collectedData.litho_summaries, deps), LITHO_SUMMARY_COLUMN_ORDER),
  )

  if (collectedData.litho_details.length) {
    sheets.push(toSheet('Détails Complets', collectedData.litho_details as Record<string, ReportCell>[]))
  }

  const pending = collectedData.litho_summaries.filter((l) => l['session_status'] === 'pending')
  if (pending.length) {
    sheets.push(toSheet('Lithos en Attente', enhanceStatusLithos(pending, deps)))
  }

  const rejected = collectedData.litho_summaries.filter((l) => l['session_status'] === 'rejected')
  if (rejected.length) {
    sheets.push(toSheet('Lithos Rejetées', enhanceStatusLithos(rejected, deps)))
  }

  const pdfAnalysis = createPdfAnalysis(collectedData, deps)
  if (pdfAnalysis.length) {
    sheets.push(toSheet('Analyse PDFs', pdfAnalysis))
  }

  const validationSummary = createValidationSummary(collectedData, deps)
  if (validationSummary.length) {
    sheets.push(toSheet('Statuts Validation', validationSummary))
  }

  return { sheets }
}

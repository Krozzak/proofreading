// Port of core/error_templates.py — common-error database and pre-filled
// messages assisting validators (powers the quick-response buttons).
import type { LithoRecord } from './types'

export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical'

export type ErrorCategory = 'shade_validation' | 'layout' | 'walmart_specific' | 'content'

export interface ErrorTemplate {
  code: string
  title: string
  template: string
  suggestions: string[]
  quick_responses: string[]
  severity: ErrorSeverity
  category: ErrorCategory
  auto_reject: boolean
  requires_comment: boolean
}

export interface DetectedError {
  error_code: string
  template: ErrorTemplate
  context: Record<string, string | number>
  row_index: number
}

export interface ErrorSummary {
  total_errors: number
  critical_errors: number
  high_errors: number
  medium_errors: number
  low_errors: number
  auto_reject_recommended: boolean
  categories: Record<string, number>
}

export const ERROR_TEMPLATES: Record<string, ErrorTemplate> = {
  shade_name_mismatch: {
    code: 'shade_name_mismatch',
    title: 'Nom de teinte incorrect',
    template: 'Nom attendu: "{expected}", Trouvé: "{found}"',
    suggestions: [
      "Vérifier l'orthographe exacte du nom",
      'Vérifier les espaces et la casse',
      'Vérifier les équivalences WTP/WATERPROOF',
      'Comparer avec le PDF original',
    ],
    quick_responses: [
      '❌ Nom de teinte incorrect - Refaire le PDF',
      '❌ Erreur typographique dans nom de teinte',
      '⚠️ Nom de teinte absent du PDF',
      "✏️ Erreur mineure d'orthographe - À corriger",
    ],
    severity: 'high',
    category: 'shade_validation',
    auto_reject: false,
    requires_comment: true,
  },
  shade_name_missing: {
    code: 'shade_name_missing',
    title: 'Nom de teinte manquant',
    template: 'Nom de teinte "{expected}" non trouvé dans le PDF',
    suggestions: [
      'Vérifier que le nom est présent dans le PDF',
      "Vérifier l'extraction du texte PDF",
      "Si c'est un PDF scanné, vérifier la qualité OCR",
      'Contacter le fournisseur si le nom est réellement absent',
    ],
    quick_responses: [
      '❌ Nom de teinte manquant dans le PDF',
      '❌ Texte non extrait - PDF scanné de mauvaise qualité',
      '📞 Contacter fournisseur - Information manquante',
    ],
    severity: 'critical',
    category: 'shade_validation',
    auto_reject: true,
    requires_comment: true,
  },
  shade_number_mismatch: {
    code: 'shade_number_mismatch',
    title: 'Numéro de teinte incorrect',
    template: 'Numéro attendu: "{expected}", Trouvé: "{found}" ou absent',
    suggestions: [
      'Vérifier le numéro dans le PDF',
      "Vérifier la concordance avec l'Excel",
      "Vérifier s'il n'y a pas de confusion avec un autre code",
      'Contacter le fournisseur si incohérence persistante',
    ],
    quick_responses: [
      '❌ Numéro de teinte incorrect',
      '❌ Numéro de teinte manquant',
      '⚠️ Incohérence Excel/PDF - Vérifier la source',
      '📞 Contacter fournisseur pour clarification',
    ],
    severity: 'high',
    category: 'shade_validation',
    auto_reject: false,
    requires_comment: true,
  },
  shade_number_missing: {
    code: 'shade_number_missing',
    title: 'Numéro de teinte manquant',
    template: 'Numéro de teinte "{expected}" non trouvé dans le PDF',
    suggestions: [
      'Vérifier que le numéro est présent dans le PDF',
      "Vérifier s'il n'est pas dans un format différent",
      "Vérifier l'extraction du texte",
      'Rejeter si le numéro est obligatoire',
    ],
    quick_responses: [
      '❌ Numéro de teinte manquant - Refaire',
      '⚠️ Numéro présent mais format différent',
      '📞 Contacter fournisseur',
    ],
    severity: 'critical',
    category: 'shade_validation',
    auto_reject: true,
    requires_comment: true,
  },
  missing_4digits: {
    code: 'missing_4digits',
    title: '4 DIGITS manquant (Walmart)',
    template: 'Code 4 DIGITS "{expected}" non trouvé dans le PDF',
    suggestions: [
      '⚠️ Requis pour toutes les lithos Walmart',
      'Vérifier que le code est présent dans le PDF',
      'Le code doit être exactement 4 chiffres',
      'REJET OBLIGATOIRE si Walmart et code manquant',
    ],
    quick_responses: [
      '❌ 4 DIGITS manquant - REJET WALMART',
      '❌ Code Walmart absent - Non conforme',
      '📞 Urgence: Contacter fournisseur - Walmart requis',
    ],
    severity: 'critical',
    category: 'walmart_specific',
    auto_reject: true,
    requires_comment: true,
  },
  invalid_4digits: {
    code: 'invalid_4digits',
    title: '4 DIGITS incorrect',
    template: 'Code attendu: "{expected}", Trouvé: "{found}"',
    suggestions: [
      'Vérifier que le code correspond exactement',
      'Le format doit être exactement 4 chiffres',
      "Pas d'espaces ou caractères spéciaux",
      'Rejeter si le code ne correspond pas',
    ],
    quick_responses: [
      '❌ Code 4 DIGITS incorrect - REJET',
      '⚠️ Format 4 DIGITS invalide',
      '📞 Contacter fournisseur - Code erroné',
    ],
    severity: 'critical',
    category: 'walmart_specific',
    auto_reject: true,
    requires_comment: true,
  },
  facing_mismatch: {
    code: 'facing_mismatch',
    title: 'Facing incorrect',
    template: 'Facing attendu: {expected}, Trouvé: {found}',
    suggestions: [
      'Vérifier le planogramme',
      'Confirmer avec le retail',
      "Vérifier si c'est intentionnel",
      'Documenter la raison si approuvé',
    ],
    quick_responses: [
      '⚠️ Facing incorrect - Vérifier planogramme',
      '✅ Facing différent mais validé par retail',
      '❌ Facing incorrect - Refaire layout',
      '📞 Contacter planogramme pour confirmation',
    ],
    severity: 'medium',
    category: 'layout',
    auto_reject: false,
    requires_comment: true,
  },
  mixed_facings: {
    code: 'mixed_facings',
    title: 'Mixed Facings détecté',
    template: 'Mixed facings détecté: {facings}',
    suggestions: [
      "Vérifier si c'est intentionnel selon le planogramme",
      'Confirmer avec le département retail',
      'Documenter la raison si approuvé',
      'Rejeter si non conforme au plan',
    ],
    quick_responses: [
      '⚠️ Mixed facings - Validé par retail',
      '⚠️ Mixed facings - Conforme au planogramme',
      '❌ Mixed facings non autorisé - Refaire',
      '📞 Contacter retail pour validation',
    ],
    severity: 'medium',
    category: 'layout',
    auto_reject: false,
    requires_comment: true,
  },
  space_saver_issue: {
    code: 'space_saver_issue',
    title: 'Problème Space Saver',
    template: 'Space Saver: {issue}',
    suggestions: [
      "Vérifier l'emplacement du Space Saver",
      'Confirmer avec le planogramme',
      'Vérifier les dimensions',
      "S'assurer que c'est conforme",
    ],
    quick_responses: [
      '⚠️ Space Saver mal positionné',
      '✅ Space Saver conforme',
      '❌ Space Saver incorrect - Refaire',
      '📞 Contacter planogramme',
    ],
    severity: 'medium',
    category: 'layout',
    auto_reject: false,
    requires_comment: true,
  },
  wrong_product: {
    code: 'wrong_product',
    title: 'Mauvais produit',
    template: 'Produit incorrect: attendu "{expected}", trouvé "{found}"',
    suggestions: [
      'Vérifier que le PDF correspond au bon produit',
      'Vérifier le code produit',
      'REJET IMMÉDIAT si mauvais produit',
      'Contacter le fournisseur',
    ],
    quick_responses: [
      '❌ MAUVAIS PRODUIT - REJET IMMÉDIAT',
      '❌ PDF ne correspond pas à la commande',
      '📞 URGENCE: Mauvais fichier reçu',
    ],
    severity: 'critical',
    category: 'content',
    auto_reject: true,
    requires_comment: true,
  },
  missing_mandatory_info: {
    code: 'missing_mandatory_info',
    title: 'Information obligatoire manquante',
    template: 'Information manquante: {info}',
    suggestions: [
      'Vérifier les exigences du projet',
      'Rejeter si information obligatoire',
      "Documenter l'information manquante",
      'Contacter le fournisseur',
    ],
    quick_responses: [
      '❌ Information obligatoire manquante - REJET',
      '⚠️ Information recommandée manquante',
      "📞 Demander complément d'information",
    ],
    severity: 'high',
    category: 'content',
    auto_reject: true,
    requires_comment: true,
  },
}

interface ValidationLike {
  is_frame?: boolean
  is_space_saver?: boolean
  is_mixed?: boolean
  shade_name?: boolean
  shade_number?: boolean
  digits?: boolean
  facing?: string | number
}

/** Analyzes validation results and produces detailed errors (port of ErrorAnalyzer). */
export function analyzeValidationResults(
  validationResults: ValidationLike[],
  excelData: LithoRecord[],
  checkDigits = false,
): DetectedError[] {
  const errors: DetectedError[] = []
  const count = Math.min(validationResults.length, excelData.length)

  for (let idx = 0; idx < count; idx++) {
    const validation = validationResults[idx]
    const data = excelData[idx]

    if (validation.is_frame || validation.is_space_saver) continue

    // 1. Shade name errors
    if (validation.shade_name === false) {
      const shadeName = String(data['SHADE NAME'] ?? '')
      if (shadeName) {
        errors.push({
          error_code: 'shade_name_mismatch',
          template: ERROR_TEMPLATES['shade_name_mismatch'],
          context: { expected: shadeName, found: 'Non trouvé ou différent' },
          row_index: idx,
        })
      } else {
        errors.push({
          error_code: 'shade_name_missing',
          template: ERROR_TEMPLATES['shade_name_missing'],
          context: { expected: shadeName || 'Nom attendu' },
          row_index: idx,
        })
      }
    }

    // 2. Shade number errors
    if (validation.shade_number === false) {
      const shadeNumber = data['SHADE NUMBER'] ?? ''
      if (shadeNumber) {
        errors.push({
          error_code: 'shade_number_mismatch',
          template: ERROR_TEMPLATES['shade_number_mismatch'],
          context: { expected: shadeNumber as string | number, found: 'Non trouvé ou différent' },
          row_index: idx,
        })
      }
    }

    // 3. 4 DIGITS errors (when checkDigits is on)
    if (checkDigits && validation.digits === false) {
      const digits = data['4 DIGITS'] ?? ''
      if (digits) {
        errors.push({
          error_code: 'missing_4digits',
          template: ERROR_TEMPLATES['missing_4digits'],
          context: { expected: digits as string | number },
          row_index: idx,
        })
      }
    }

    // 4. Mixed facings
    if (validation.is_mixed) {
      errors.push({
        error_code: 'mixed_facings',
        template: ERROR_TEMPLATES['mixed_facings'],
        context: { facings: validation.facing ?? 'Multiple' },
        row_index: idx,
      })
    }
  }

  return errors
}

export function getErrorSummary(errors: DetectedError[]): ErrorSummary {
  const summary: ErrorSummary = {
    total_errors: errors.length,
    critical_errors: 0,
    high_errors: 0,
    medium_errors: 0,
    low_errors: 0,
    auto_reject_recommended: false,
    categories: {},
  }
  for (const error of errors) {
    const template = error.template
    if (template.severity === 'critical') {
      summary.critical_errors += 1
      if (template.auto_reject) summary.auto_reject_recommended = true
    } else if (template.severity === 'high') {
      summary.high_errors += 1
    } else if (template.severity === 'medium') {
      summary.medium_errors += 1
    } else {
      summary.low_errors += 1
    }
    summary.categories[template.category] = (summary.categories[template.category] ?? 0) + 1
  }
  return summary
}

export function formatErrorMessage(error: DetectedError): string {
  let message = error.template.template
  for (const [key, value] of Object.entries(error.context)) {
    message = message.replaceAll(`{${key}}`, String(value))
  }
  return `${error.template.title}: ${message}`
}

/** Quick responses of the up-to-3 most frequent error codes (first response each). */
export function getQuickResponseSuggestions(errors: DetectedError[]): string[] {
  if (!errors.length) return ['✅ Validation réussie - Aucune erreur détectée']

  const errorCounts = new Map<string, number>()
  for (const error of errors) {
    errorCounts.set(error.error_code, (errorCounts.get(error.error_code) ?? 0) + 1)
  }

  const suggestions = new Set<string>()
  const sorted = [...errorCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3)
  for (const [code] of sorted) {
    const template = ERROR_TEMPLATES[code]
    if (template && template.quick_responses.length) {
      suggestions.add(template.quick_responses[0])
    }
  }
  return [...suggestions]
}

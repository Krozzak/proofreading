// Multimodal AI validation: the model receives the litho page images + the
// brief rows + the brand rules and returns per-row verdicts in the same shape
// as the rule engines, plus a free-form check answer. This is the path that
// works on scanned/vectorized PDFs where text extraction fails.
import type { LithoRecord } from '../../core/types'
import { safeStr } from '../../core/textSafe'
import { renderPdfPageToJpeg } from '../pdfEngine'
import { chat, extractJson, type UserContentPart } from './client'
import { loadAiSettings } from './settings'

export interface AiRowVerdict {
  index: number
  shade_number: boolean
  shade_name: boolean
  digits: boolean
  overall: boolean
  notes: string
}

export interface AiValidationOutcome {
  rows: AiRowVerdict[]
  /** Answer to the user's free-form question, when one was asked. */
  custom_check_answer: string | null
  /** Model self-assessed confidence, 0-100. */
  confidence: number
  global_notes: string
  model: string
  date: string
}

export interface AiValidationInput {
  pdfData: ArrayBuffer
  pageCount: number
  excelData: LithoRecord[]
  brandDescription: string
  checkDigits: boolean
  /** Optional free-form check, e.g. "vérifie aussi que le logo Walmart est présent". */
  question?: string
  /** Pages sent to the model (first N). */
  maxPages?: number
}

const SYSTEM_PROMPT =
  "Tu es un contrôleur qualité expert en artwork d'imprimerie (lithos) chez L'Oréal. " +
  "On te fournit les images des pages d'une litho PDF et les lignes du brief Excel correspondant. " +
  'Pour CHAQUE ligne du brief, vérifie visuellement dans les images:\n' +
  "- shade_number: le numéro de teinte est visible tel quel\n" +
  "- shade_name: le nom de teinte est visible (les équivalences WTP ⇔ WATERPROOF sont acceptées)\n" +
  "- digits: le code 4 DIGITS est visible (seulement si demandé)\n" +
  'Règles:\n' +
  "- Lignes FRAME (PRODUCT FACING SL = FRAME) ou SPACE_SAVER: ne pas valider, overall = true, le noter dans notes.\n" +
  '- overall = true seulement si tous les critères vérifiés pour la ligne sont trouvés.\n' +
  '- En cas de doute sur une lecture, considère le critère comme NON trouvé et explique dans notes.\n' +
  'Réponds UNIQUEMENT avec un JSON strict de cette forme (dans un bloc ```json):\n' +
  '{"rows": [{"index": 0, "shade_number": true, "shade_name": true, "digits": true, "overall": true, "notes": ""}],\n' +
  ' "custom_check_answer": null, "confidence": 0-100, "global_notes": ""}'

function briefRowsForPrompt(excelData: LithoRecord[], checkDigits: boolean) {
  return excelData.map((row, index) => ({
    index,
    upc: safeStr(row['UPC']),
    product_description: safeStr(row['PRODUCT DESCRIPTION']),
    shade_name: safeStr(row['SHADE NAME']),
    shade_number: safeStr(row['SHADE NUMBER']),
    product_facing: safeStr(row['PRODUCT FACING SL']),
    ...(checkDigits ? { four_digits: safeStr(row['4 DIGITS']) } : {}),
  }))
}

export async function validateWithAi(input: AiValidationInput): Promise<AiValidationOutcome> {
  const settings = loadAiSettings()
  const maxPages = Math.min(input.maxPages ?? 3, input.pageCount)

  const parts: UserContentPart[] = []
  for (let page = 1; page <= maxPages; page++) {
    parts.push({ imageJpegBase64: await renderPdfPageToJpeg(input.pdfData, page) })
  }

  const rows = briefRowsForPrompt(input.excelData, input.checkDigits)
  parts.push({
    text:
      `Règles de la marque:\n${input.brandDescription}\n\n` +
      `Vérification 4 DIGITS demandée: ${input.checkDigits ? 'OUI' : 'NON (digits = true partout)'}\n\n` +
      `Lignes du brief (${rows.length}):\n${JSON.stringify(rows, null, 1)}\n\n` +
      (input.question
        ? `Vérification supplémentaire demandée par l'utilisateur (réponds dans custom_check_answer):\n"${input.question}"\n\n`
        : 'Aucune vérification supplémentaire (custom_check_answer = null).\n\n') +
      `Les ${maxPages} première(s) page(s) de la litho sont fournies en images ci-dessus.`,
  })

  const reply = await chat({ system: SYSTEM_PROMPT, parts, maxTokens: 4096 })
  const parsed = extractJson(reply) as {
    rows?: Partial<AiRowVerdict>[]
    custom_check_answer?: string | null
    confidence?: number
    global_notes?: string
  }

  const verdicts: AiRowVerdict[] = input.excelData.map((_, index) => {
    const r = parsed.rows?.find((x) => x.index === index) ?? parsed.rows?.[index]
    return {
      index,
      shade_number: r?.shade_number !== false,
      shade_name: r?.shade_name !== false,
      digits: r?.digits !== false,
      overall: r?.overall !== false,
      notes: typeof r?.notes === 'string' ? r.notes : '',
    }
  })

  return {
    rows: verdicts,
    custom_check_answer:
      typeof parsed.custom_check_answer === 'string' && parsed.custom_check_answer.trim()
        ? parsed.custom_check_answer
        : null,
    confidence:
      typeof parsed.confidence === 'number' ? Math.max(0, Math.min(100, parsed.confidence)) : 0,
    global_notes: typeof parsed.global_notes === 'string' ? parsed.global_notes : '',
    model: settings.model,
    date: new Date().toISOString(),
  }
}

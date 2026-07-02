// Declarative, JSON-serializable brand definitions — realizes the desktop
// roadmap's "Dynamic Brand Editor" + "Brand Import/Export" ideas so new brands
// (NYX, L'Oréal Paris, Garnier…) can be added without touching code.
import type { BrandConfig, ColumnType } from './baseConfig'

export const BRAND_SCHEMA_VERSION = 1

/** MNY-style: litho code = literal prefix + N digits, taken from the filename start. */
export interface PrefixFilenameRule {
  type: 'prefix'
  /** Literal the code starts with (e.g. 'YCA'). */
  literal: string
  /** Number of digits following the literal (e.g. 5 → code length = literal + 5). */
  digits: number
}

/** ESSIE-style: full regex control (all patterns are case-insensitive by default). */
export interface RegexFilenameRule {
  type: 'regex'
  /** Pattern a valid FILENAME must match (anchored at start by convention). */
  filenamePattern: string
  /** Pattern whose capture group 1 extracts the litho code from a filename. */
  extractPattern: string
  /** Pattern a bare litho CODE must fully match. */
  codePattern: string
  /** Regex flags (default 'i'). */
  flags?: string
}

export type FilenameRule = PrefixFilenameRule | RegexFilenameRule

export interface BrandColumn {
  name: string
  required: boolean
  type: ColumnType
}

export interface BrandDefinition {
  schema_version: number
  brand_code: string
  brand_name: string
  filename: FilenameRule
  columns: BrandColumn[]
  validation: {
    requires_upc: boolean
    requires_digits: boolean
  }
  /** Free-text rules description shown in Paramètres; auto-generated when absent. */
  description?: string
  examples?: {
    valid_filenames?: string[]
    invalid_filenames?: string[]
  }
  created_by?: 'builtin' | 'wizard' | 'ai' | 'import'
}

/**
 * Columns of the standard L'Oréal brief. New brands start from this template;
 * 'DECRIPTION' is intentionally misspelled (real brief files use it).
 */
export const STANDARD_COLUMNS: BrandColumn[] = [
  { name: 'LITHO', required: true, type: 'str' },
  { name: 'DECRIPTION', required: true, type: 'str' },
  { name: 'UPC SEQUENCE', required: true, type: 'str' },
  { name: 'UPC POSITION', required: true, type: 'str' },
  { name: 'UPC', required: true, type: 'str' },
  { name: 'PRODUCT DESCRIPTION', required: true, type: 'str' },
  { name: 'SHADE NAME', required: true, type: 'str' },
  { name: 'SHADE NUMBER', required: true, type: 'numeric' },
  { name: 'PRODUCT FACING SL', required: true, type: 'numeric' },
  { name: '4 DIGITS', required: true, type: 'numeric' },
  { name: 'NEW', required: false, type: 'str' },
  { name: 'STATUS', required: false, type: 'str' },
  { name: 'PRODUCT', required: false, type: 'str' },
  { name: 'TIER', required: false, type: 'str' },
  { name: 'SEASON', required: false, type: 'str' },
]

/** Validates a candidate definition (import, wizard, AI). Returns French error messages. */
export function validateBrandDefinition(value: unknown): { errors: string[]; definition: BrandDefinition | null } {
  const errors: string[] = []
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return { errors: ['Le JSON doit être un objet'], definition: null }
  }
  const d = value as Record<string, unknown>

  if (typeof d.brand_code !== 'string' || !/^[A-Z0-9_]{2,20}$/.test(d.brand_code)) {
    errors.push("brand_code : requis, 2-20 caractères A-Z/0-9/_ (ex: 'NYX', 'OAP')")
  }
  if (typeof d.brand_name !== 'string' || !d.brand_name.trim()) {
    errors.push('brand_name : requis (nom affiché de la marque)')
  }

  const fn = d.filename as Record<string, unknown> | undefined
  if (!fn || typeof fn !== 'object') {
    errors.push("filename : requis (règle de nommage, type 'prefix' ou 'regex')")
  } else if (fn.type === 'prefix') {
    if (typeof fn.literal !== 'string' || !fn.literal.length) {
      errors.push('filename.literal : requis (préfixe du code, ex: "YCA")')
    }
    if (typeof fn.digits !== 'number' || !Number.isInteger(fn.digits) || fn.digits < 1 || fn.digits > 20) {
      errors.push('filename.digits : entier entre 1 et 20')
    }
  } else if (fn.type === 'regex') {
    for (const key of ['filenamePattern', 'extractPattern', 'codePattern'] as const) {
      const pattern = fn[key]
      if (typeof pattern !== 'string' || !pattern.length) {
        errors.push(`filename.${key} : requis`)
        continue
      }
      try {
        new RegExp(pattern, typeof fn.flags === 'string' ? fn.flags : 'i')
      } catch (e) {
        errors.push(`filename.${key} : regex invalide (${e instanceof Error ? e.message : e})`)
      }
    }
  } else {
    errors.push("filename.type : doit être 'prefix' ou 'regex'")
  }

  const columns = d.columns as unknown
  if (!Array.isArray(columns) || columns.length === 0) {
    errors.push('columns : liste non vide requise')
  } else {
    const names = new Set<string>()
    columns.forEach((c, i) => {
      if (typeof c !== 'object' || c === null) {
        errors.push(`columns[${i}] : objet {name, required, type} attendu`)
        return
      }
      const col = c as Record<string, unknown>
      if (typeof col.name !== 'string' || !col.name.trim()) errors.push(`columns[${i}].name : requis`)
      else if (names.has(col.name)) errors.push(`columns[${i}] : colonne '${col.name}' en double`)
      else names.add(col.name as string)
      if (typeof col.required !== 'boolean') errors.push(`columns[${i}].required : booléen requis`)
      if (col.type !== 'str' && col.type !== 'numeric') errors.push(`columns[${i}].type : 'str' ou 'numeric'`)
    })
    if (!names.has('LITHO')) {
      errors.push("columns : la colonne 'LITHO' est obligatoire (elle relie les lignes Excel aux PDFs)")
    }
  }

  const validation = d.validation as Record<string, unknown> | undefined
  if (!validation || typeof validation !== 'object') {
    errors.push('validation : requis ({requires_upc, requires_digits})')
  } else {
    if (typeof validation.requires_upc !== 'boolean') errors.push('validation.requires_upc : booléen requis')
    if (typeof validation.requires_digits !== 'boolean') errors.push('validation.requires_digits : booléen requis')
    if (
      validation.requires_digits === true &&
      Array.isArray(columns) &&
      !columns.some((c) => (c as Record<string, unknown>)?.name === '4 DIGITS')
    ) {
      errors.push("validation.requires_digits=true mais la colonne '4 DIGITS' est absente de columns")
    }
  }

  if (errors.length) return { errors, definition: null }

  const definition: BrandDefinition = {
    schema_version: typeof d.schema_version === 'number' ? (d.schema_version as number) : BRAND_SCHEMA_VERSION,
    brand_code: d.brand_code as string,
    brand_name: (d.brand_name as string).trim(),
    filename: d.filename as FilenameRule,
    columns: (columns as BrandColumn[]).map((c) => ({ name: c.name.trim(), required: c.required, type: c.type })),
    validation: {
      requires_upc: (validation as { requires_upc: boolean }).requires_upc,
      requires_digits: (validation as { requires_digits: boolean }).requires_digits,
    },
    description: typeof d.description === 'string' ? d.description : undefined,
    examples:
      typeof d.examples === 'object' && d.examples !== null
        ? (d.examples as BrandDefinition['examples'])
        : undefined,
    created_by: ['builtin', 'wizard', 'ai', 'import'].includes(d.created_by as string)
      ? (d.created_by as BrandDefinition['created_by'])
      : 'import',
  }
  return { errors: [], definition }
}

/** Human-readable rules text (French) when the definition has no description. */
export function describeBrandDefinition(def: BrandDefinition): string {
  if (def.description) return def.description
  const filenameDesc =
    def.filename.type === 'prefix'
      ? `  • Pattern: ${def.filename.literal} + ${def.filename.digits} chiffres\n` +
        `  • Longueur code: ${def.filename.literal.length + def.filename.digits} caractères`
      : `  • Fichier valide: /${def.filename.filenamePattern}/${def.filename.flags ?? 'i'}\n` +
        `  • Extraction code: /${def.filename.extractPattern}/${def.filename.flags ?? 'i'}`
  const examples = def.examples?.valid_filenames?.length
    ? `\n  • Exemples: ${def.examples.valid_filenames.slice(0, 3).join(', ')}`
    : ''
  return (
    `Format ${def.brand_name} (${def.brand_code}):\n\n` +
    `📄 Fichiers PDF:\n${filenameDesc}${examples}\n\n` +
    `📊 Colonnes requises:\n  • ${def.columns.filter((c) => c.required).map((c) => c.name).join(', ')}\n\n` +
    `✅ Validations:\n` +
    `  • SHADE NUMBER / SHADE NAME: Validés dans le PDF\n` +
    `  • UPC: ${def.validation.requires_upc ? '✓ Activé' : '❌ Désactivé'}\n` +
    `  • 4 DIGITS: ${def.validation.requires_digits ? '✓ Activable (selon settings)' : '❌ Désactivé'}`
  )
}

function isDigits(s: string): boolean {
  return s.length > 0 && /^[0-9]+$/.test(s)
}

/** Builds a runtime BrandConfig (the 11-method interface) from a JSON definition. */
export function brandFromDefinition(def: BrandDefinition): BrandConfig {
  const columnTypes: Record<string, ColumnType> = {}
  for (const c of def.columns) columnTypes[c.name] = c.type
  const required = def.columns.filter((c) => c.required).map((c) => c.name)
  const optional = def.columns.filter((c) => !c.required).map((c) => c.name)

  let isValidFilename: (filename: string) => boolean
  let extractCode: (filename: string) => string | null
  let isValidCode: (code: string) => boolean

  if (def.filename.type === 'prefix') {
    const { literal, digits } = def.filename
    const codeLength = literal.length + digits
    isValidCode = (code) =>
      code.length === codeLength && code.startsWith(literal) && isDigits(code.slice(literal.length))
    isValidFilename = (filename) =>
      filename.length >= codeLength && isValidCode(filename.slice(0, codeLength))
    extractCode = (filename) => {
      if (filename.length < codeLength) return null
      const code = filename.slice(0, codeLength)
      return isValidCode(code) ? code : null
    }
  } else {
    const flags = def.filename.flags ?? 'i'
    const filenameRe = new RegExp(def.filename.filenamePattern, flags)
    const extractRe = new RegExp(def.filename.extractPattern, flags)
    const codeRe = new RegExp(def.filename.codePattern, flags)
    isValidFilename = (filename) => filenameRe.test(filename)
    isValidCode = (code) => codeRe.test(code)
    extractCode = (filename) => {
      const match = extractRe.exec(filename)
      if (match && match[1] !== undefined) {
        return isValidCode(match[1]) ? match[1] : null
      }
      return null
    }
  }

  return {
    getBrandCode: () => def.brand_code,
    getBrandDisplayName: () => def.brand_name,
    getRequiredColumns: () => [...required],
    getOptionalColumns: () => [...optional],
    getColumnTypes: () => ({ ...columnTypes }),
    isValidFilename,
    extractLithoCode: extractCode,
    isValidLithoCode: isValidCode,
    requiresUpcValidation: () => def.validation.requires_upc,
    requiresDigitsValidation: () => def.validation.requires_digits,
    getValidationDescription: () => describeBrandDefinition(def),
  }
}

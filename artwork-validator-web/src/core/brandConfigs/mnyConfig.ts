// Port of core/brand_configs/mny_config.py
import type { BrandConfig, ColumnType } from './baseConfig'

/** True when every character is an ASCII digit (Python str.isdigit on '0'-'9'). */
function isDigits(s: string): boolean {
  return s.length > 0 && /^[0-9]+$/.test(s)
}

/**
 * Maybelline New York: litho codes are `YCA` + 5 digits (8 chars),
 * '4 DIGITS' column exists and can be validated.
 */
export const mnyConfig: BrandConfig = {
  getBrandCode: () => 'MNY',
  getBrandDisplayName: () => 'Maybelline New York',

  getRequiredColumns: () => [
    'LITHO',
    // 'DECRIPTION' is intentionally misspelled — the real brief files use it.
    'DECRIPTION',
    'UPC SEQUENCE',
    'UPC POSITION',
    'UPC',
    'PRODUCT DESCRIPTION',
    'SHADE NAME',
    'SHADE NUMBER',
    'PRODUCT FACING SL',
    '4 DIGITS',
  ],

  getOptionalColumns: () => ['NEW', 'STATUS', 'PRODUCT', 'TIER', 'SEASON'],

  getColumnTypes: (): Record<string, ColumnType> => ({
    LITHO: 'str',
    DECRIPTION: 'str',
    'UPC SEQUENCE': 'str',
    'UPC POSITION': 'str',
    UPC: 'str',
    'PRODUCT DESCRIPTION': 'str',
    'SHADE NAME': 'str',
    'SHADE NUMBER': 'numeric',
    'PRODUCT FACING SL': 'numeric',
    '4 DIGITS': 'numeric',
    NEW: 'str',
    STATUS: 'str',
    PRODUCT: 'str',
    TIER: 'str',
    SEASON: 'str',
  }),

  isValidFilename(filename: string): boolean {
    if (filename.length < 8) return false
    const code = filename.slice(0, 8)
    return code.startsWith('YCA') && isDigits(code.slice(3))
  },

  extractLithoCode(filename: string): string | null {
    if (filename.length < 8) return null
    const code = filename.slice(0, 8)
    return this.isValidLithoCode(code) ? code : null
  },

  isValidLithoCode(code: string): boolean {
    if (code.length !== 8) return false
    return code.startsWith('YCA') && isDigits(code.slice(3))
  },

  requiresUpcValidation: () => false,
  requiresDigitsValidation: () => true,

  getValidationDescription: () =>
    'Format Maybelline New York (MNY):\n' +
    '\n' +
    '📄 Fichiers PDF:\n' +
    '  • Pattern: YCA + 5 chiffres\n' +
    '  • Exemples: YCA12345.pdf, YCA98765_v2.pdf\n' +
    '  • Longueur code: 8 caractères\n' +
    '\n' +
    '📊 Colonnes Excel spécifiques:\n' +
    '  • SHADE NUMBER: Numérique (ex: 110, 120)\n' +
    '  • 4 DIGITS: Numérique (4 derniers chiffres UPC)\n' +
    '\n' +
    '✅ Validations:\n' +
    '  • SHADE NUMBER: Validé dans PDF\n' +
    '  • SHADE NAME: Validé dans PDF\n' +
    '  • UPC: ❌ Désactivé (pas dans PDFs)\n' +
    '  • 4 DIGITS: ✓ Activable (selon settings)',
}

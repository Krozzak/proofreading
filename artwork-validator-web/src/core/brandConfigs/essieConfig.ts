// Port of core/brand_configs/essie_config.py
import type { BrandConfig, ColumnType } from './baseConfig'

export const SUPPORTED_GAMMES = ['CARE', 'GEL', 'NSTUDIO', 'ESSIE', 'EXPRESS'] as const

const GAMMES_PATTERN = SUPPORTED_GAMMES.join('|')
const FILENAME_RE = new RegExp(`^(${GAMMES_PATTERN})_S\\d+_\\d+_\\d+(_SHADESTRIPS)?`, 'i')
const EXTRACT_RE = new RegExp(`^((${GAMMES_PATTERN})_S\\d+_\\d+_\\d+)`, 'i')
const CODE_RE = new RegExp(`^(${GAMMES_PATTERN})_S\\d+_\\d+_\\d+$`, 'i')

/**
 * ESSIE: litho codes are `[GAMME]_S[SEASON]_[INDEX]_[TOTAL]` with an optional
 * `_SHADESTRIPS` suffix; SHADE NUMBER is text; no '4 DIGITS' column.
 */
export const essieConfig: BrandConfig = {
  getBrandCode: () => 'ESSIE',
  getBrandDisplayName: () => 'ESSIE',

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
  ],

  getOptionalColumns: () => ['NEW', 'STATUS', 'PRODUCT', 'TIER', 'SEASON', 'STRIP TYPE'],

  getColumnTypes: (): Record<string, ColumnType> => ({
    LITHO: 'str',
    DECRIPTION: 'str',
    'UPC SEQUENCE': 'str',
    'UPC POSITION': 'str',
    UPC: 'str',
    'PRODUCT DESCRIPTION': 'str',
    'SHADE NAME': 'str',
    'SHADE NUMBER': 'str', // string for ESSIE (e.g. '2-IN-1 BASE & TOP COAT')
    'PRODUCT FACING SL': 'numeric',
    NEW: 'str',
    STATUS: 'str',
    PRODUCT: 'str',
    TIER: 'str',
    SEASON: 'str',
    'STRIP TYPE': 'str',
  }),

  isValidFilename(filename: string): boolean {
    return FILENAME_RE.test(filename)
  },

  extractLithoCode(filename: string): string | null {
    const match = EXTRACT_RE.exec(filename)
    if (match) {
      const code = match[1]
      return this.isValidLithoCode(code) ? code : null
    }
    return null
  },

  isValidLithoCode(code: string): boolean {
    return CODE_RE.test(code)
  },

  requiresUpcValidation: () => false,
  requiresDigitsValidation: () => false,

  getValidationDescription: () =>
    'Format ESSIE:\n' +
    '\n' +
    '📄 Fichiers PDF:\n' +
    '  • Pattern: [GAMME]_S[SEASON]_[INDEX]_[TOTAL]\n' +
    '  • Exemples: CARE_S26_1_3.pdf, GEL_S26_2_6.pdf\n' +
    `  • Gammes supportées: ${SUPPORTED_GAMMES.join(', ')}\n` +
    '  • Suffix optionnel: _SHADESTRIPS\n' +
    '\n' +
    '📊 Colonnes Excel spécifiques:\n' +
    "  • SHADE NUMBER: Texte (ex: '2-IN-1 BASE & TOP COAT')\n" +
    '  • 4 DIGITS: ❌ N\'existe pas pour ESSIE\n' +
    '\n' +
    '✅ Validations:\n' +
    '  • SHADE NUMBER: Validé dans PDF\n' +
    '  • SHADE NAME: Validé dans PDF\n' +
    '  • UPC: ❌ Désactivé (pas dans PDFs)\n' +
    '  • 4 DIGITS: ❌ Désactivé (colonne absente)',
}

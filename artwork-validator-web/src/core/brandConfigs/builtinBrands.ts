// Built-in brand definitions (MNY, ESSIE) expressed in the JSON schema.
// Behavior is identical to the historical hardcoded configs — pinned by the
// brandConfigs tests and the Python parity suite.
import type { BrandDefinition } from './brandSchema'
import { STANDARD_COLUMNS } from './brandSchema'

export const SUPPORTED_GAMMES = ['CARE', 'GEL', 'NSTUDIO', 'ESSIE', 'EXPRESS'] as const

const GAMMES = SUPPORTED_GAMMES.join('|')

export const MNY_DEFINITION: BrandDefinition = {
  schema_version: 1,
  brand_code: 'MNY',
  brand_name: 'Maybelline New York',
  filename: { type: 'prefix', literal: 'YCA', digits: 5 },
  columns: STANDARD_COLUMNS,
  validation: { requires_upc: false, requires_digits: true },
  description:
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
  examples: {
    valid_filenames: ['YCA12345.pdf', 'YCA98765_v2.pdf'],
    invalid_filenames: ['CARE_S26_1_3.pdf', 'YCA123.pdf'],
  },
  created_by: 'builtin',
}

export const ESSIE_DEFINITION: BrandDefinition = {
  schema_version: 1,
  brand_code: 'ESSIE',
  brand_name: 'ESSIE',
  filename: {
    type: 'regex',
    filenamePattern: `^(${GAMMES})_S\\d+_\\d+_\\d+(_SHADESTRIPS)?`,
    extractPattern: `^((${GAMMES})_S\\d+_\\d+_\\d+)`,
    codePattern: `^(${GAMMES})_S\\d+_\\d+_\\d+$`,
    flags: 'i',
  },
  columns: [
    // Standard columns minus '4 DIGITS', SHADE NUMBER is text, + STRIP TYPE
    ...STANDARD_COLUMNS.filter((c) => c.name !== '4 DIGITS').map((c) =>
      c.name === 'SHADE NUMBER' ? { ...c, type: 'str' as const } : c,
    ),
    { name: 'STRIP TYPE', required: false, type: 'str' },
  ],
  validation: { requires_upc: false, requires_digits: false },
  description:
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
  examples: {
    valid_filenames: ['CARE_S26_1_3.pdf', 'GEL_S26_2_6_SHADESTRIPS.pdf'],
    invalid_filenames: ['YCA12345.pdf', 'INVALID_S26_1_3.pdf'],
  },
  created_by: 'builtin',
}

export const BUILTIN_DEFINITIONS: BrandDefinition[] = [MNY_DEFINITION, ESSIE_DEFINITION]

// AI-assisted brand definition generation: the user describes the brand
// (filename format with examples, brief columns) and the model returns a
// BrandDefinition JSON, validated by the same schema as the wizard/import.
import type { BrandDefinition } from '../../core/brandConfigs'
import { validateBrandDefinition } from '../../core/brandConfigs'
import { chat, extractJson } from './client'

export const BRAND_JSON_SPEC = `Le JSON de définition de marque a EXACTEMENT cette forme:
{
  "schema_version": 1,
  "brand_code": "CODE",            // 2-20 caractères A-Z/0-9/_, unique (ex: "NYX", "OAP")
  "brand_name": "Nom affiché",
  "filename": {
    // OPTION A — code = préfixe littéral + N chiffres au début du nom de fichier:
    "type": "prefix", "literal": "YCA", "digits": 5
    // OPTION B — regex (insensibles à la casse):
    // "type": "regex",
    // "filenamePattern": "^(CARE|GEL)_S\\\\d+_\\\\d+_\\\\d+(_SHADESTRIPS)?",  // nom de fichier valide
    // "extractPattern": "^((CARE|GEL)_S\\\\d+_\\\\d+_\\\\d+)",                // groupe 1 = code litho
    // "codePattern": "^(CARE|GEL)_S\\\\d+_\\\\d+_\\\\d+$"                     // code litho complet
  },
  "columns": [
    // Le brief standard L'Oréal — adapter si la marque diffère.
    // ⚠️ "DECRIPTION" est VOLONTAIREMENT mal orthographié (vrais briefs). Ne pas corriger.
    // ⚠️ "LITHO" est obligatoire (lie les lignes Excel aux PDFs).
    {"name": "LITHO", "required": true, "type": "str"},
    {"name": "DECRIPTION", "required": true, "type": "str"},
    {"name": "UPC SEQUENCE", "required": true, "type": "str"},
    {"name": "UPC POSITION", "required": true, "type": "str"},
    {"name": "UPC", "required": true, "type": "str"},
    {"name": "PRODUCT DESCRIPTION", "required": true, "type": "str"},
    {"name": "SHADE NAME", "required": true, "type": "str"},
    {"name": "SHADE NUMBER", "required": true, "type": "numeric"},  // "str" si teintes textuelles
    {"name": "PRODUCT FACING SL", "required": true, "type": "numeric"},
    {"name": "4 DIGITS", "required": true, "type": "numeric"},      // retirer si la marque n'a pas cette colonne
    {"name": "NEW", "required": false, "type": "str"},
    {"name": "STATUS", "required": false, "type": "str"},
    {"name": "PRODUCT", "required": false, "type": "str"},
    {"name": "TIER", "required": false, "type": "str"},
    {"name": "SEASON", "required": false, "type": "str"}
  ],
  "validation": {
    "requires_upc": false,        // false sauf indication contraire (UPC absents des lithos)
    "requires_digits": true       // true SEULEMENT si la colonne "4 DIGITS" existe
  },
  "examples": {
    "valid_filenames": ["EXEMPLE1.pdf"],
    "invalid_filenames": ["mauvais.pdf"]
  },
  "created_by": "ai"
}`

const SYSTEM_PROMPT =
  "Tu es un expert de l'application L'Oréal Litho Validator. Tu génères des définitions de marque " +
  'au format JSON strict pour son moteur de validation. ' +
  'Réponds UNIQUEMENT avec le JSON (dans un bloc ```json), sans texte autour.\n\n' +
  BRAND_JSON_SPEC

export async function generateBrandWithAi(description: string): Promise<BrandDefinition> {
  const ask = async (extra: string): Promise<{ def: BrandDefinition | null; errors: string[] }> => {
    const reply = await chat({
      system: SYSTEM_PROMPT,
      parts: [
        {
          text:
            `Description de la marque par l'utilisateur:\n"""${description}"""\n\n` +
            'Génère la définition JSON. Si la description ne précise pas les colonnes, pars du brief standard. ' +
            'Déduis le pattern de nom de fichier des exemples fournis (préfère "prefix" quand possible).' +
            extra,
        },
      ],
      maxTokens: 2048,
    })
    const parsed = extractJson(reply)
    const { definition, errors } = validateBrandDefinition(parsed)
    return { def: definition, errors }
  }

  const first = await ask('')
  if (first.def) return first.def

  // One retry with the validator's error messages as feedback
  const second = await ask(
    `\n\nATTENTION: ta réponse précédente était invalide:\n- ${first.errors.join('\n- ')}\nCorrige ces erreurs.`,
  )
  if (second.def) return second.def
  throw new Error(`Définition invalide après 2 tentatives: ${second.errors.join(' ; ')}`)
}

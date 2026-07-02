// ESSIE brand config, now derived from its JSON definition (see builtinBrands).
// The module keeps its historical exports so tests and callers are unchanged.
import { brandFromDefinition } from './brandSchema'
import { ESSIE_DEFINITION, SUPPORTED_GAMMES } from './builtinBrands'

export { SUPPORTED_GAMMES }
export const essieConfig = brandFromDefinition(ESSIE_DEFINITION)

// MNY brand config, now derived from its JSON definition (see builtinBrands).
// The module keeps its historical export so tests and callers are unchanged.
import { brandFromDefinition } from './brandSchema'
import { MNY_DEFINITION } from './builtinBrands'

export const mnyConfig = brandFromDefinition(MNY_DEFINITION)

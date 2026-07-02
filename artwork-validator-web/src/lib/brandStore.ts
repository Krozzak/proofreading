// Persistence of custom brand definitions (localStorage) + registry hydration.
// Built-ins live in src/core; this module only manages user-created brands.
import type { BrandDefinition } from '../core/brandConfigs'
import {
  isBuiltinBrand,
  registerDefinition,
  unregisterBrand,
  validateBrandDefinition,
} from '../core/brandConfigs'

export const BRANDS_STORAGE_KEY = 'avw:brands'

export function loadCustomBrands(): BrandDefinition[] {
  try {
    const raw = localStorage.getItem(BRANDS_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown[]
    if (!Array.isArray(parsed)) return []
    const out: BrandDefinition[] = []
    for (const item of parsed) {
      const { definition } = validateBrandDefinition(item)
      if (definition && !isBuiltinBrand(definition.brand_code)) out.push(definition)
    }
    return out
  } catch {
    return []
  }
}

function persist(brands: BrandDefinition[]): void {
  try {
    localStorage.setItem(BRANDS_STORAGE_KEY, JSON.stringify(brands))
  } catch {
    // quota/storage disabled — brands stay in memory for the session
  }
}

/** Registers all persisted custom brands into the runtime registry (app startup). */
export function hydrateCustomBrands(): BrandDefinition[] {
  const brands = loadCustomBrands()
  for (const def of brands) registerDefinition(def)
  return brands
}

/** Creates or updates a custom brand (built-ins cannot be overwritten). */
export function saveCustomBrand(def: BrandDefinition): { ok: boolean; error?: string } {
  if (isBuiltinBrand(def.brand_code)) {
    return { ok: false, error: `Le code '${def.brand_code}' est réservé à une marque intégrée` }
  }
  const brands = loadCustomBrands().filter((b) => b.brand_code !== def.brand_code)
  brands.push(def)
  persist(brands)
  registerDefinition(def)
  return { ok: true }
}

export function deleteCustomBrand(brandCode: string): boolean {
  if (isBuiltinBrand(brandCode)) return false
  const brands = loadCustomBrands().filter((b) => b.brand_code !== brandCode)
  persist(brands)
  return unregisterBrand(brandCode)
}

export function exportBrandJson(def: BrandDefinition): string {
  return JSON.stringify(def, null, 2)
}

/** Parses + validates a brand JSON string (import / AI output). */
export function parseBrandJson(json: string): { definition: BrandDefinition | null; errors: string[] } {
  let value: unknown
  try {
    value = JSON.parse(json)
  } catch (e) {
    return { definition: null, errors: [`JSON invalide: ${e instanceof Error ? e.message : e}`] }
  }
  return (({ definition, errors }) => ({ definition, errors }))(validateBrandDefinition(value))
}

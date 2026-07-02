// Dynamic brand registry: built-in JSON definitions (MNY, ESSIE) plus custom
// definitions registered at runtime (persisted by src/lib/brandStore.ts).
import type { BrandConfig } from './baseConfig'
import type { BrandDefinition } from './brandSchema'
import { brandFromDefinition } from './brandSchema'
import { BUILTIN_DEFINITIONS } from './builtinBrands'

const brands = new Map<string, BrandConfig>()
const definitions = new Map<string, BrandDefinition>()

export function registerBrand(config: BrandConfig): void {
  brands.set(config.getBrandCode(), config)
}

/** Registers a JSON definition (built-in or custom) and its runtime config. */
export function registerDefinition(def: BrandDefinition): BrandConfig {
  const config = brandFromDefinition(def)
  definitions.set(def.brand_code, def)
  brands.set(def.brand_code, config)
  return config
}

export function unregisterBrand(brandCode: string): boolean {
  definitions.delete(brandCode)
  return brands.delete(brandCode)
}

export function getBrand(brandCode: string): BrandConfig | null {
  return brands.get(brandCode) ?? null
}

export function getDefinition(brandCode: string): BrandDefinition | null {
  return definitions.get(brandCode) ?? null
}

export function getAllBrands(): BrandConfig[] {
  return [...brands.values()]
}

export function getAllDefinitions(): BrandDefinition[] {
  return [...definitions.values()]
}

export function getBrandCodes(): string[] {
  return [...brands.keys()]
}

export function isBuiltinBrand(brandCode: string): boolean {
  return BUILTIN_DEFINITIONS.some((d) => d.brand_code === brandCode)
}

for (const def of BUILTIN_DEFINITIONS) {
  registerDefinition(def)
}

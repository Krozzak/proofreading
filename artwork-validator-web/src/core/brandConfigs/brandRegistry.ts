// Port of core/brand_configs/brand_registry.py — brands are registered at module init.
import type { BrandConfig } from './baseConfig'
import { mnyConfig } from './mnyConfig'
import { essieConfig } from './essieConfig'

const brands = new Map<string, BrandConfig>()

export function registerBrand(config: BrandConfig): void {
  brands.set(config.getBrandCode(), config)
}

export function getBrand(brandCode: string): BrandConfig | null {
  return brands.get(brandCode) ?? null
}

export function getAllBrands(): BrandConfig[] {
  return [...brands.values()]
}

export function getBrandCodes(): string[] {
  return [...brands.keys()]
}

registerBrand(mnyConfig)
registerBrand(essieConfig)

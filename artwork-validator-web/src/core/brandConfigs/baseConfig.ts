// Port of core/brand_configs/base_config.py

/** Expected type of an Excel column: plain string or coerced number. */
export type ColumnType = 'str' | 'numeric'

export interface ValidationRules {
  brand_code: string
  brand_name: string
  filename_pattern: string
  required_columns: string[]
  optional_columns: string[]
  requires_upc: boolean
  requires_digits: boolean
}

/**
 * Contract every brand configuration must implement (MNY, ESSIE, ...).
 * Mirrors BaseBrandConfig's abstract methods 1:1.
 */
export interface BrandConfig {
  getBrandCode(): string
  getBrandDisplayName(): string
  getRequiredColumns(): string[]
  getOptionalColumns(): string[]
  getColumnTypes(): Record<string, ColumnType>
  isValidFilename(filename: string): boolean
  extractLithoCode(filename: string): string | null
  isValidLithoCode(code: string): boolean
  requiresUpcValidation(): boolean
  requiresDigitsValidation(): boolean
  getValidationDescription(): string
}

export function getValidationRules(config: BrandConfig): ValidationRules {
  return {
    brand_code: config.getBrandCode(),
    brand_name: config.getBrandDisplayName(),
    filename_pattern: config.getValidationDescription(),
    required_columns: config.getRequiredColumns(),
    optional_columns: config.getOptionalColumns(),
    requires_upc: config.requiresUpcValidation(),
    requires_digits: config.requiresDigitsValidation(),
  }
}

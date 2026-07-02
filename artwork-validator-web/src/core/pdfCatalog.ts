// Port of the non-Qt half of core/pdf_processor.py: filename validation per
// brand, valid/invalid partition, litho-code → file mapping. Rendering lives
// in src/lib/pdfEngine.ts; the OCR fallback is replaced by the
// `needsManualReview` flag + TextRecoveryProvider extension point.
import type { BrandConfig } from './brandConfigs'

/** Threshold below which the desktop app fell back to OCR (pdf_processor.py:248). */
export const MANUAL_REVIEW_TEXT_THRESHOLD = 50

/**
 * Extension point replacing the PaddleOCR fallback: a future AI/OCR API can
 * implement this to recover text from scanned PDFs (< 50 extractable chars).
 */
export interface TextRecoveryProvider {
  recover(file: ArrayBuffer, fileName: string): Promise<string>
}

export interface CatalogEntry {
  fileName: string
  lithoCode: string
  /** Concatenated text of all pages (normalized). */
  text: string
  pageCount: number
  /** True when extracted text < 50 chars — flagged "Revue manuelle requise". */
  needsManualReview: boolean
}

export interface PdfValidationReport {
  total_files: number
  valid_files: number
  invalid_files: number
  invalid_file_list: string[]
  valid_litho_codes: string[]
}

export class PdfCatalog {
  brandConfig: BrandConfig
  /** Valid files in load order (mirrors pdf_files). */
  entries: CatalogEntry[] = []
  invalidFiles: string[] = []

  constructor(brandConfig: BrandConfig) {
    this.brandConfig = brandConfig
  }

  /** Partitions filenames into valid/invalid per the brand's filename rules. */
  static partitionFiles(
    fileNames: string[],
    brandConfig: BrandConfig,
  ): { valid: string[]; invalid: string[] } {
    const pdfFiles = fileNames.filter((f) => f.endsWith('.pdf'))
    const valid: string[] = []
    const invalid: string[] = []
    for (const f of pdfFiles) {
      if (brandConfig.isValidFilename(f)) valid.push(f)
      else invalid.push(f)
    }
    return { valid, invalid }
  }

  addEntry(fileName: string, text: string, pageCount: number): CatalogEntry | null {
    const lithoCode = this.brandConfig.extractLithoCode(fileName)
    if (lithoCode === null) return null
    const entry: CatalogEntry = {
      fileName,
      lithoCode,
      text,
      pageCount,
      needsManualReview: text.trim().length < MANUAL_REVIEW_TEXT_THRESHOLD,
    }
    this.entries.push(entry)
    return entry
  }

  /** All litho codes, de-duplicated in file order (port of get_all_litho_codes). */
  getAllLithoCodes(): string[] {
    const codes: string[] = []
    for (const entry of this.entries) {
      if (!codes.includes(entry.lithoCode)) codes.push(entry.lithoCode)
    }
    return codes
  }

  /** First entry matching the litho code (port of get_text_for_litho lookup). */
  getEntryForLitho(lithoCode: string): CatalogEntry | null {
    return this.entries.find((e) => e.lithoCode === lithoCode) ?? null
  }

  getTextForLitho(lithoCode: string): string {
    return this.getEntryForLitho(lithoCode)?.text ?? ''
  }

  getValidationReport(): PdfValidationReport {
    return {
      total_files: this.entries.length + this.invalidFiles.length,
      valid_files: this.entries.length,
      invalid_files: this.invalidFiles.length,
      invalid_file_list: [...this.invalidFiles],
      valid_litho_codes: this.getAllLithoCodes(),
    }
  }
}

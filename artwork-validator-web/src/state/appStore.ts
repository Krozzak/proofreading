// Global app state (Zustand): brand, Excel data, PDF catalog, current litho,
// validation options, session — the web counterpart of MainWindow's state.
import { create } from 'zustand'
import type { BrandConfig } from '../core/brandConfigs'
import { getBrand, mnyConfig } from '../core/brandConfigs'
import {
  ExcelProcessor,
  validateExcelFormat,
  type DataQualityReport,
  type ExcelFormatReport,
} from '../core/excelProcessor'
import { LithoValidator, type ValidationResult } from '../core/validator'
import { PdfCatalog, MANUAL_REVIEW_TEXT_THRESHOLD } from '../core/pdfCatalog'
import type { RawSheet, SessionData, ValidationStatus } from '../core/types'
import {
  defaultSession,
  getLithoStatus,
  loadFromLocalStorage,
  saveToLocalStorage,
  updateLithoStatus,
} from '../lib/sessionStore'
import { extractPdfText } from '../lib/pdfEngine'

export type ViewName = 'overview' | 'validation' | 'settings' | 'files'

export interface PdfFileEntry {
  fileName: string
  lithoCode: string
  file: File
  text: string
  pageCount: number
  needsManualReview: boolean
}

export interface IngestProgress {
  total: number
  done: number
  currentFile: string
}

interface AppState {
  view: ViewName
  brandCode: string
  brandConfig: BrandConfig

  // Excel
  rawSheet: RawSheet | null
  excelFileName: string
  excelReport: ExcelFormatReport | null
  qualityReport: DataQualityReport | null

  // PDFs
  pdfEntries: PdfFileEntry[]
  invalidFiles: string[]
  pdfFolderLabel: string
  ingestProgress: IngestProgress | null

  // Options
  checkDigits: boolean
  validationMethod: 'legacy' | 'enhanced'

  // Navigation
  currentIndex: number

  // Session
  session: SessionData
  sessionRestored: boolean
  dirty: boolean

  // Quick responses (Paramètres editable defaults)
  customQuickResponses: string[]

  // Actions
  setView(view: ViewName): void
  setBrand(brandCode: string): void
  loadExcel(sheet: RawSheet, fileName: string): void
  ingestPdfFiles(files: File[], folderLabel?: string): Promise<void>
  setCheckDigits(value: boolean): void
  setValidationMethod(method: 'legacy' | 'enhanced'): void
  setCurrentIndex(index: number): void
  nextLitho(): boolean
  previousLitho(): boolean
  goToLitho(code: string): void
  validateCurrent(status: ValidationStatus, comment: string): void
  setSessionName(name: string): void
  restoreSession(session: SessionData): void
  resetSession(): void
  setCustomQuickResponses(responses: string[]): void
}

/** Builders shared by store consumers. */
export function buildExcelProcessor(state: Pick<AppState, 'brandConfig' | 'rawSheet'>): ExcelProcessor | null {
  if (!state.rawSheet) return null
  const processor = new ExcelProcessor(state.brandConfig)
  if (!processor.loadSheet(state.rawSheet)) return null
  return processor
}

export function buildValidator(
  state: Pick<AppState, 'brandConfig' | 'checkDigits' | 'validationMethod'>,
): LithoValidator {
  const validator = new LithoValidator(state.brandConfig)
  validator.checkDigits = state.checkDigits
  validator.useEnhancedValidation = state.validationMethod === 'enhanced'
  return validator
}

export function buildCatalog(state: Pick<AppState, 'brandConfig' | 'pdfEntries' | 'invalidFiles'>): PdfCatalog {
  const catalog = new PdfCatalog(state.brandConfig)
  for (const e of state.pdfEntries) {
    catalog.entries.push({
      fileName: e.fileName,
      lithoCode: e.lithoCode,
      text: e.text,
      pageCount: e.pageCount,
      needsManualReview: e.needsManualReview,
    })
  }
  catalog.invalidFiles = [...state.invalidFiles]
  return catalog
}

/** Litho codes de-duplicated in file order (one card per litho). */
export function lithoCodesOf(entries: PdfFileEntry[]): string[] {
  const codes: string[] = []
  for (const e of entries) if (!codes.includes(e.lithoCode)) codes.push(e.lithoCode)
  return codes
}

export function validateLitho(
  state: Pick<AppState, 'brandConfig' | 'checkDigits' | 'validationMethod' | 'rawSheet' | 'pdfEntries'>,
  lithoCode: string,
): { results: ValidationResult[]; excelData: ReturnType<ExcelProcessor['getDataForLitho']> } {
  const processor = buildExcelProcessor(state)
  const excelData = processor ? processor.getDataForLitho(lithoCode) : []
  const entry = state.pdfEntries.find((e) => e.lithoCode === lithoCode)
  const text = entry?.text ?? ''
  if (!excelData.length) return { results: [], excelData }
  const validator = buildValidator(state)
  return { results: validator.validate(text, excelData), excelData }
}

function persist(session: SessionData): void {
  saveToLocalStorage(session)
}

const initialSession = loadFromLocalStorage()

export const useAppStore = create<AppState>((set, get) => ({
  view: 'validation',
  brandCode: initialSession?.brand_code ?? 'MNY',
  brandConfig: getBrand(initialSession?.brand_code ?? 'MNY') ?? mnyConfig,

  rawSheet: null,
  excelFileName: '',
  excelReport: null,
  qualityReport: null,

  pdfEntries: [],
  invalidFiles: [],
  pdfFolderLabel: '',
  ingestProgress: null,

  checkDigits: initialSession?.check_digits ?? false,
  validationMethod: initialSession?.validation_method ?? 'legacy',

  currentIndex: initialSession?.last_litho_index ?? 0,

  session: initialSession ?? defaultSession(),
  sessionRestored: initialSession !== null && Object.keys(initialSession.validations).length > 0,
  dirty: false,

  customQuickResponses: [],

  setView: (view) => set({ view }),

  setBrand: (brandCode) => {
    const brandConfig = getBrand(brandCode)
    if (!brandConfig) return
    const state = get()
    // Re-partition already-loaded PDFs with the new brand rules
    const allFiles = [
      ...state.pdfEntries.map((e) => ({ file: e.file, text: e.text, pageCount: e.pageCount, fileName: e.fileName })),
    ]
    const stillValid: PdfFileEntry[] = []
    const nowInvalid: string[] = [...state.invalidFiles]
    // Previously-invalid files can't be revalidated without re-reading them;
    // the UI asks users to re-drop the folder after a brand switch when needed.
    for (const f of allFiles) {
      const code = brandConfig.extractLithoCode(f.fileName)
      if (code !== null) {
        stillValid.push({
          fileName: f.fileName,
          lithoCode: code,
          file: f.file,
          text: f.text,
          pageCount: f.pageCount,
          needsManualReview: f.text.trim().length < MANUAL_REVIEW_TEXT_THRESHOLD,
        })
      } else if (!nowInvalid.includes(f.fileName)) {
        nowInvalid.push(f.fileName)
      }
    }
    const excelReport = state.rawSheet ? validateExcelFormat(state.rawSheet, brandConfig) : null
    const session = { ...state.session, brand_code: brandCode }
    persist(session)
    set({
      brandCode,
      brandConfig,
      pdfEntries: stillValid,
      invalidFiles: nowInvalid,
      excelReport,
      currentIndex: 0,
      session,
    })
  },

  loadExcel: (sheet, fileName) => {
    const state = get()
    const excelReport = validateExcelFormat(sheet, state.brandConfig)
    let qualityReport: DataQualityReport | null = null
    if (excelReport.is_valid) {
      const processor = new ExcelProcessor(state.brandConfig)
      if (processor.loadSheet(sheet)) {
        qualityReport = processor.validateDataQuality()
      }
    }
    const session = { ...state.session, excel_file: fileName }
    persist(session)
    set({ rawSheet: sheet, excelFileName: fileName, excelReport, qualityReport, session })
  },

  ingestPdfFiles: async (files, folderLabel = '') => {
    const state = get()
    const brandConfig = state.brandConfig
    const pdfFiles = files.filter((f) => f.name.toLowerCase().endsWith('.pdf'))
    const valid: File[] = []
    const invalid: string[] = []
    for (const f of pdfFiles) {
      if (brandConfig.isValidFilename(f.name)) valid.push(f)
      else invalid.push(f.name)
    }

    set({
      invalidFiles: invalid,
      pdfFolderLabel: folderLabel,
      ingestProgress: { total: valid.length, done: 0, currentFile: '' },
    })

    const entries: PdfFileEntry[] = []
    for (let i = 0; i < valid.length; i++) {
      const file = valid[i]
      set({ ingestProgress: { total: valid.length, done: i, currentFile: file.name } })
      try {
        const buffer = await file.arrayBuffer()
        const info = await extractPdfText(buffer)
        const lithoCode = brandConfig.extractLithoCode(file.name)
        if (lithoCode !== null) {
          entries.push({
            fileName: file.name,
            lithoCode,
            file,
            text: info.text,
            pageCount: info.pageCount,
            needsManualReview: info.text.trim().length < MANUAL_REVIEW_TEXT_THRESHOLD,
          })
        }
      } catch {
        // Unreadable PDF: treat as invalid so the user sees it flagged
        invalid.push(file.name)
        set({ invalidFiles: [...invalid] })
      }
    }

    const session = { ...get().session, pdf_folder: folderLabel }
    persist(session)
    set({
      pdfEntries: entries,
      ingestProgress: null,
      currentIndex: 0,
      session,
    })
  },

  setCheckDigits: (value) => {
    const session = { ...get().session, check_digits: value }
    persist(session)
    set({ checkDigits: value, session })
  },

  setValidationMethod: (method) => {
    const session = { ...get().session, validation_method: method }
    persist(session)
    set({ validationMethod: method, session })
  },

  setCurrentIndex: (index) => {
    const state = get()
    const codes = lithoCodesOf(state.pdfEntries)
    if (index < 0 || index >= codes.length) return
    const session = { ...state.session, last_litho_index: index }
    persist(session)
    set({ currentIndex: index, session })
  },

  nextLitho: () => {
    const state = get()
    const codes = lithoCodesOf(state.pdfEntries)
    if (state.currentIndex < codes.length - 1) {
      state.setCurrentIndex(state.currentIndex + 1)
      return true
    }
    return false
  },

  previousLitho: () => {
    const state = get()
    if (state.currentIndex > 0) {
      state.setCurrentIndex(state.currentIndex - 1)
      return true
    }
    return false
  },

  goToLitho: (code) => {
    const state = get()
    const codes = lithoCodesOf(state.pdfEntries)
    const index = codes.indexOf(code)
    if (index >= 0) {
      state.setCurrentIndex(index)
      set({ view: 'validation' })
    }
  },

  validateCurrent: (status, comment) => {
    const state = get()
    const codes = lithoCodesOf(state.pdfEntries)
    const code = codes[state.currentIndex]
    if (!code) return
    const session = updateLithoStatus(state.session, code, status, comment)
    persist(session)
    set({ session, dirty: true })
    // Auto-advance to the next pending litho (next_requested behavior)
    const nextPending = codes.findIndex(
      (c, i) => i > state.currentIndex && getLithoStatus(session, c) === null,
    )
    if (nextPending >= 0) {
      state.setCurrentIndex(nextPending)
    } else if (state.currentIndex < codes.length - 1) {
      state.setCurrentIndex(state.currentIndex + 1)
    }
  },

  setSessionName: (name) => {
    const session = { ...get().session, session_name: name }
    persist(session)
    set({ session })
  },

  restoreSession: (session) => {
    persist(session)
    set({
      session,
      brandCode: session.brand_code,
      brandConfig: getBrand(session.brand_code) ?? mnyConfig,
      checkDigits: session.check_digits,
      validationMethod: session.validation_method,
      currentIndex: session.last_litho_index,
      sessionRestored: true,
      dirty: false,
    })
  },

  resetSession: () => {
    const state = get()
    const fresh = {
      ...defaultSession(),
      created_date: new Date().toISOString(),
      last_updated: new Date().toISOString(),
      brand_code: state.brandCode,
      check_digits: state.checkDigits,
      validation_method: state.validationMethod,
      pdf_folder: state.pdfFolderLabel,
      excel_file: state.excelFileName,
    }
    persist(fresh)
    set({ session: fresh, sessionRestored: false, dirty: false, currentIndex: 0 })
  },

  setCustomQuickResponses: (responses) => set({ customQuickResponses: responses }),
}))

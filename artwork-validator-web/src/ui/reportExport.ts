// M6 wiring: dataCollector → reportGenerator → excelIO → browser download.
import { collectAllValidationData } from '../core/dataCollector'
import { generateReportModel } from '../core/reportGenerator'
import { getLithoStatus } from '../lib/sessionStore'
import { downloadBlob, writeReport } from '../lib/excelIO'
import { buildCatalog, buildExcelProcessor, buildValidator, useAppStore } from '../state/appStore'
import { toast } from './toast'

export async function exportValidationReport(): Promise<void> {
  const state = useAppStore.getState()
  const processor = buildExcelProcessor(state)
  const catalog = buildCatalog(state)

  if (!processor || !catalog.entries.length) {
    toast('Chargez un fichier Excel et des PDFs avant d\'exporter un rapport', 'error')
    return
  }

  const validator = buildValidator(state)
  const session = state.session

  const collected = collectAllValidationData({
    getSessionInfo: () => ({
      name: session.session_name || 'Sans nom',
      created: session.created_date,
      updated: session.last_updated,
      pdf_folder: session.pdf_folder,
      excel_file: session.excel_file,
      validations_count: Object.keys(session.validations).length,
      file_path: null,
    }),
    getAllLithoCodes: () => catalog.getAllLithoCodes(),
    getDataForLitho: (code) => processor.getDataForLitho(code),
    getTextForLitho: (code) => catalog.getTextForLitho(code),
    validate: (pdfText, excelData) => validator.validate(pdfText, excelData),
    getLithoStatus: (code) => getLithoStatus(session, code),
    checkDigits: state.checkDigits,
  })

  const model = generateReportModel(collected, {
    getTextForLitho: (code) => catalog.getTextForLitho(code),
  })

  try {
    const buffer = await writeReport(model)
    const date = new Date().toISOString().slice(0, 10)
    downloadBlob(
      buffer,
      `Rapport_Validation_${date}.xlsx`,
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    toast('Rapport Excel exporté', 'success')
  } catch (e) {
    toast(`Erreur lors de l'export du rapport: ${e instanceof Error ? e.message : e}`, 'error')
  }
}

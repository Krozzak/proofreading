// Startup / ingestion screen: drop zones for the PDF folder and the Excel
// brief (drag-and-drop + folder picker + multi-file picker).
import { useRef, useState, type DragEvent } from 'react'
import { readBrief } from '../lib/excelIO'
import { useAppStore } from '../state/appStore'
import { toast } from './toast'

async function filesFromDataTransfer(dt: DataTransfer): Promise<File[]> {
  const items = [...dt.items]
  const out: File[] = []

  async function walkEntry(entry: FileSystemEntry): Promise<void> {
    if (entry.isFile) {
      const file = await new Promise<File>((resolve, reject) =>
        (entry as FileSystemFileEntry).file(resolve, reject),
      )
      out.push(file)
    } else if (entry.isDirectory) {
      const reader = (entry as FileSystemDirectoryEntry).createReader()
      // readEntries returns batches of max ~100; loop until empty
      for (;;) {
        const batch = await new Promise<FileSystemEntry[]>((resolve, reject) =>
          reader.readEntries(resolve, reject),
        )
        if (!batch.length) break
        for (const child of batch) await walkEntry(child)
      }
    }
  }

  const entries = items
    .map((item) => (item.kind === 'file' ? item.webkitGetAsEntry() : null))
    .filter((e): e is FileSystemEntry => e !== null)

  if (entries.length) {
    for (const entry of entries) await walkEntry(entry)
    return out
  }
  return [...dt.files]
}

export function FileDropZone() {
  const ingestPdfFiles = useAppStore((s) => s.ingestPdfFiles)
  const loadExcel = useAppStore((s) => s.loadExcel)
  const excelFileName = useAppStore((s) => s.excelFileName)
  const excelReport = useAppStore((s) => s.excelReport)
  const pdfCount = useAppStore((s) => s.pdfEntries.length)
  const invalidFiles = useAppStore((s) => s.invalidFiles)
  const progress = useAppStore((s) => s.ingestProgress)
  const session = useAppStore((s) => s.session)
  const sessionRestored = useAppStore((s) => s.sessionRestored)
  const setView = useAppStore((s) => s.setView)
  const bothReady = pdfCount > 0 && Boolean(excelReport?.is_valid)

  const folderInputRef = useRef<HTMLInputElement>(null)
  const filesInputRef = useRef<HTMLInputElement>(null)
  const excelInputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState<'pdf' | 'excel' | null>(null)

  async function handlePdfFiles(files: File[], folderLabel: string) {
    const pdfs = files.filter((f) => f.name.toLowerCase().endsWith('.pdf'))
    if (!pdfs.length) {
      toast('Aucun fichier PDF trouvé', 'error')
      return
    }
    await ingestPdfFiles(pdfs, folderLabel)
  }

  async function handleExcelFile(file: File) {
    try {
      const sheet = await readBrief(await file.arrayBuffer())
      loadExcel(sheet, file.name)
    } catch (e) {
      toast(`Impossible de lire le fichier Excel: ${e instanceof Error ? e.message : e}`, 'error')
    }
  }

  async function onDrop(zone: 'pdf' | 'excel', e: DragEvent) {
    e.preventDefault()
    setDragOver(null)
    const files = await filesFromDataTransfer(e.dataTransfer)
    if (zone === 'pdf') {
      await handlePdfFiles(files, 'Dossier déposé')
    } else {
      const excel = files.find((f) => f.name.toLowerCase().endsWith('.xlsx'))
      if (excel) await handleExcelFile(excel)
      else toast('Déposez un fichier .xlsx', 'error')
    }
  }

  const zoneClass = (zone: 'pdf' | 'excel', done: boolean) =>
    'flex flex-1 cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed p-8 text-center transition ' +
    (dragOver === zone
      ? 'border-red-500 bg-red-50'
      : done
        ? 'border-emerald-400 bg-emerald-50'
        : 'border-neutral-300 bg-white hover:border-neutral-400')

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 p-6">
      {sessionRestored && Object.keys(session.validations).length > 0 && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          ♻️ Session « {session.session_name || 'sans nom'} » restaurée (
          {Object.keys(session.validations).length} validation(s)). Re-déposez le dossier PDF
          {session.pdf_folder ? ` (« ${session.pdf_folder} »)` : ''} et le fichier Excel
          {session.excel_file ? ` (« ${session.excel_file} »)` : ''} pour continuer.
        </div>
      )}

      <div className="flex flex-col gap-4 md:flex-row">
        <div
          className={zoneClass('pdf', pdfCount > 0)}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver('pdf')
          }}
          onDragLeave={() => setDragOver(null)}
          onDrop={(e) => void onDrop('pdf', e)}
          onClick={() => folderInputRef.current?.click()}
        >
          <span className="text-4xl">📁</span>
          <span className="font-semibold">
            {pdfCount > 0 ? `${pdfCount} PDF(s) chargé(s)` : 'Dossier de lithos PDF'}
          </span>
          <span className="text-sm text-neutral-500">
            Glissez-déposez le dossier, ou cliquez pour le sélectionner
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              filesInputRef.current?.click()
            }}
            className="mt-1 rounded border border-neutral-300 px-2 py-1 text-xs text-neutral-600 hover:bg-neutral-100"
          >
            …ou sélectionner des fichiers PDF individuels
          </button>
        </div>

        <div
          className={zoneClass('excel', Boolean(excelReport?.is_valid))}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver('excel')
          }}
          onDragLeave={() => setDragOver(null)}
          onDrop={(e) => void onDrop('excel', e)}
          onClick={() => excelInputRef.current?.click()}
        >
          <span className="text-4xl">📊</span>
          <span className="font-semibold">{excelFileName || 'Brief Excel (.xlsx)'}</span>
          <span className="text-sm text-neutral-500">
            Glissez-déposez le fichier, ou cliquez pour le sélectionner
          </span>
        </div>
      </div>

      {progress && (
        <div className="rounded-xl border border-neutral-200 bg-white p-4">
          <div className="mb-1 flex justify-between text-sm">
            <span>Extraction du texte des PDFs…</span>
            <span>
              {progress.done}/{progress.total}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded bg-neutral-200">
            <div
              className="h-full bg-red-600 transition-all"
              style={{ width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%` }}
            />
          </div>
          <div className="mt-1 truncate text-xs text-neutral-500">{progress.currentFile}</div>
        </div>
      )}

      {excelReport && !excelReport.is_valid && (
        <div className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
          ❌ Fichier Excel invalide — colonnes obligatoires manquantes :{' '}
          <strong>{excelReport.missing_columns.join(', ')}</strong>
        </div>
      )}
      {excelReport?.is_valid && excelReport.missing_optional_columns.length > 0 && (
        <div className="rounded-xl border border-neutral-200 bg-white px-4 py-3 text-xs text-neutral-500">
          ℹ️ Colonnes optionnelles manquantes (non bloquant) :{' '}
          {excelReport.missing_optional_columns.join(', ')}
        </div>
      )}

      {bothReady && (
        <button
          onClick={() => setView('validation')}
          className="rounded-xl bg-red-600 py-3 text-lg font-bold text-white shadow hover:bg-red-500"
        >
          Commencer la validation ➜
        </button>
      )}

      {invalidFiles.length > 0 && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          ⚠️ {invalidFiles.length} fichier(s) au format de nom invalide (ignorés) :
          <ul className="mt-1 list-inside list-disc text-xs">
            {invalidFiles.slice(0, 8).map((f) => (
              <li key={f}>{f}</li>
            ))}
            {invalidFiles.length > 8 && <li>… et {invalidFiles.length - 8} autres</li>}
          </ul>
        </div>
      )}

      <input
        ref={folderInputRef}
        type="file"
        // @ts-expect-error non-standard attribute
        webkitdirectory=""
        multiple
        className="hidden"
        onChange={(e) => {
          const files = [...(e.target.files ?? [])]
          const folder = files[0]?.webkitRelativePath?.split('/')[0] ?? 'Dossier'
          if (files.length) void handlePdfFiles(files, folder)
          e.target.value = ''
        }}
      />
      <input
        ref={filesInputRef}
        type="file"
        accept=".pdf"
        multiple
        className="hidden"
        onChange={(e) => {
          const files = [...(e.target.files ?? [])]
          if (files.length) void handlePdfFiles(files, 'Sélection de fichiers')
          e.target.value = ''
        }}
      />
      <input
        ref={excelInputRef}
        type="file"
        accept=".xlsx"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) void handleExcelFile(file)
          e.target.value = ''
        }}
      />
    </div>
  )
}

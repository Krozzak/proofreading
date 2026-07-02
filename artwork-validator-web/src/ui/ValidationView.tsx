// Validation view: left panel (navigation, litho lists, comment, quick
// responses, approve/reject) + right litho viewer (stats, PDF canvas,
// results table / CUBBY matrix). Mirrors the desktop two-pane workflow.
import { useMemo, useState } from 'react'
import {
  analyzeValidationResults,
  getQuickResponseSuggestions,
} from '../core/errorTemplates'
import { getLithoStatus } from '../lib/sessionStore'
import type { LegacyEntryResult } from '../core/validator'
import { isCubbyResult } from '../core/validator'
import { lithoCodesOf, useAppStore, validateLitho } from '../state/appStore'
import { AiPanel } from './AiPanel'
import { CubbyMatrix } from './CubbyMatrix'
import { PdfCanvas } from './PdfCanvas'
import { ResultsTable } from './ResultsTable'
import { toast } from './toast'

type StatusTab = 'pending' | 'rejected' | 'approved'

const TAB_LABELS: Record<StatusTab, string> = {
  pending: '⏳ En attente',
  rejected: '❌ À revoir',
  approved: '✅ Validées',
}

export function ValidationView() {
  const pdfEntries = useAppStore((s) => s.pdfEntries)
  const rawSheet = useAppStore((s) => s.rawSheet)
  const brandConfig = useAppStore((s) => s.brandConfig)
  const checkDigits = useAppStore((s) => s.checkDigits)
  const setCheckDigits = useAppStore((s) => s.setCheckDigits)
  const validationMethod = useAppStore((s) => s.validationMethod)
  const setValidationMethod = useAppStore((s) => s.setValidationMethod)
  const currentIndex = useAppStore((s) => s.currentIndex)
  const session = useAppStore((s) => s.session)
  const validateCurrent = useAppStore((s) => s.validateCurrent)
  const nextLitho = useAppStore((s) => s.nextLitho)
  const previousLitho = useAppStore((s) => s.previousLitho)
  const goToLitho = useAppStore((s) => s.goToLitho)
  const customQuickResponses = useAppStore((s) => s.customQuickResponses)

  const [comment, setComment] = useState('')
  const [statusTab, setStatusTab] = useState<StatusTab>('pending')
  const [listFilter, setListFilter] = useState('')
  const [pageNumber, setPageNumber] = useState(1)

  const codes = useMemo(() => lithoCodesOf(pdfEntries), [pdfEntries])
  const currentCode = codes[currentIndex] ?? null
  const entry = useMemo(
    () => (currentCode ? pdfEntries.find((e) => e.lithoCode === currentCode) ?? null : null),
    [pdfEntries, currentCode],
  )

  const { results, excelData } = useMemo(() => {
    if (!currentCode) return { results: [], excelData: [] }
    return validateLitho({ brandConfig, checkDigits, validationMethod, rawSheet, pdfEntries }, currentCode)
  }, [brandConfig, checkDigits, validationMethod, rawSheet, pdfEntries, currentCode])

  const cubby = results.length === 1 && isCubbyResult(results[0]) ? results[0] : null
  const rowResults = cubby ? [] : (results as LegacyEntryResult[])

  const quickResponses = useMemo(() => {
    if (cubby || !rowResults.length) return customQuickResponses
    const errors = analyzeValidationResults(rowResults, excelData, checkDigits)
    return [...getQuickResponseSuggestions(errors), ...customQuickResponses]
  }, [cubby, rowResults, excelData, checkDigits, customQuickResponses])

  // Stats
  const statuses = codes.map((c) => getLithoStatus(session, c)?.status ?? 'pending')
  const approvedCount = statuses.filter((s) => s === 'approved').length
  const rejectedCount = statuses.filter((s) => s === 'rejected').length
  const pendingCount = codes.length - approvedCount - rejectedCount
  const processedPct = codes.length ? Math.round(((approvedCount + rejectedCount) / codes.length) * 100) : 0

  const currentStatus = currentCode ? getLithoStatus(session, currentCode) : null

  const listCodes = codes.filter((c) => {
    const st = getLithoStatus(session, c)?.status ?? 'pending'
    if (st !== statusTab) return false
    return !listFilter || c.toUpperCase().includes(listFilter.toUpperCase())
  })

  function onValidate(status: 'approved' | 'rejected') {
    if (!currentCode) return
    validateCurrent(status, comment)
    setComment('')
    setPageNumber(1)
    toast(
      status === 'approved' ? `✅ ${currentCode} approuvée` : `❌ ${currentCode} refusée`,
      status === 'approved' ? 'success' : 'info',
    )
  }

  function copyCode() {
    if (!currentCode) return
    navigator.clipboard
      .writeText(currentCode)
      .then(() => toast(`✓ Copié: ${currentCode}`, 'success'))
      .catch(() => toast('Copie impossible', 'error'))
  }

  if (!codes.length) {
    return (
      <div className="p-8 text-center text-neutral-500">
        Chargez un dossier de PDFs et un brief Excel pour commencer la validation.
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col gap-3 p-3 lg:flex-row">
      {/* ===== Left panel ===== */}
      <aside className="flex w-full shrink-0 flex-col gap-3 lg:w-80">
        {/* Navigation */}
        <div className="rounded-xl border border-neutral-200 bg-white p-3">
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={() => {
                previousLitho()
                setPageNumber(1)
              }}
              disabled={currentIndex === 0}
              className="rounded border border-neutral-300 px-3 py-1.5 text-sm disabled:opacity-40"
              title="Ctrl+←"
            >
              ◀ Précédent
            </button>
            <span className="text-sm font-semibold">
              {currentIndex + 1} / {codes.length}
            </span>
            <button
              onClick={() => {
                nextLitho()
                setPageNumber(1)
              }}
              disabled={currentIndex >= codes.length - 1}
              className="rounded border border-neutral-300 px-3 py-1.5 text-sm disabled:opacity-40"
              title="Ctrl+→"
            >
              Suivant ▶
            </button>
          </div>
          <div className="mt-2 h-1.5 overflow-hidden rounded bg-neutral-200">
            <div
              className="h-full bg-red-600 transition-all"
              style={{ width: `${((currentIndex + 1) / codes.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Litho lists */}
        <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-neutral-200 bg-white p-3">
          <div className="mb-2 flex gap-1">
            {(Object.keys(TAB_LABELS) as StatusTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setStatusTab(tab)}
                className={
                  'flex-1 rounded px-2 py-1 text-xs ' +
                  (statusTab === tab
                    ? 'bg-neutral-900 font-semibold text-white'
                    : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200')
                }
              >
                {TAB_LABELS[tab]} (
                {tab === 'pending' ? pendingCount : tab === 'rejected' ? rejectedCount : approvedCount})
              </button>
            ))}
          </div>
          <input
            value={listFilter}
            onChange={(e) => setListFilter(e.target.value)}
            placeholder="Filtrer les lithos…"
            className="mb-2 rounded border border-neutral-300 px-2 py-1 text-sm"
          />
          <div className="min-h-24 flex-1 overflow-y-auto">
            {listCodes.length === 0 && (
              <div className="py-4 text-center text-xs text-neutral-400">Aucune litho</div>
            )}
            {listCodes.map((code) => {
              const st = getLithoStatus(session, code)
              return (
                <button
                  key={code}
                  onClick={() => goToLitho(code)}
                  className={
                    'flex w-full items-center justify-between rounded px-2 py-1 text-left font-mono text-xs hover:bg-neutral-100 ' +
                    (code === currentCode ? 'bg-red-50 font-bold text-red-700' : '')
                  }
                  title={st?.comment || undefined}
                >
                  <span>{code}</span>
                  {st?.comment && <span title={st.comment}>💬</span>}
                </button>
              )
            })}
          </div>
        </div>

        {/* Comment + quick responses + validate */}
        <div className="rounded-xl border border-neutral-200 bg-white p-3">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Commentaire (optionnel)…"
            rows={3}
            className="w-full rounded border border-neutral-300 px-2 py-1.5 text-sm"
          />
          {quickResponses.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {quickResponses.map((qr) => (
                <button
                  key={qr}
                  onClick={() => setComment(qr)}
                  className="max-w-full truncate rounded-full border border-neutral-300 px-2 py-0.5 text-left text-[11px] text-neutral-600 hover:bg-neutral-100"
                  title={qr}
                >
                  {qr}
                </button>
              ))}
            </div>
          )}
          <div className="mt-3 flex gap-2">
            <button
              onClick={() => onValidate('approved')}
              className="flex-1 rounded-lg bg-emerald-600 py-2.5 font-semibold text-white hover:bg-emerald-500"
              title="Ctrl+Entrée"
            >
              ✅ Approuver
            </button>
            <button
              onClick={() => onValidate('rejected')}
              className="flex-1 rounded-lg bg-red-600 py-2.5 font-semibold text-white hover:bg-red-500"
              title="Ctrl+R"
            >
              ❌ Refuser
            </button>
          </div>
        </div>
      </aside>

      {/* ===== Right panel: litho viewer ===== */}
      <section className="flex min-w-0 flex-1 flex-col gap-3">
        {/* Stats strip */}
        <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
          {[
            ['Total PDFs', String(codes.length)],
            ['Courant', String(currentIndex + 1)],
            ['Traitement', `${processedPct}%`],
            ['Validés', String(approvedCount)],
            ['Rejetés', String(rejectedCount)],
            ['En attente', String(pendingCount)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-neutral-200 bg-white px-2 py-1.5 text-center">
              <div className="text-[10px] uppercase tracking-wide text-neutral-400">{label}</div>
              <div className="text-sm font-bold">{value}</div>
            </div>
          ))}
        </div>

        {/* Status + code + options */}
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-neutral-200 bg-white px-3 py-2">
          <button
            onClick={copyCode}
            className="rounded bg-neutral-900 px-2.5 py-1 font-mono text-sm font-bold text-white hover:bg-neutral-700"
            title="Cliquer pour copier le code"
          >
            {currentCode} 📋
          </button>

          <span className="text-sm">
            {currentStatus === null && '⏳ En attente'}
            {currentStatus?.status === 'approved' && (
              <span className="text-emerald-700">✅ Approuvé le {currentStatus.date.slice(0, 10)}</span>
            )}
            {currentStatus?.status === 'rejected' && (
              <span className="text-red-700">❌ Refusé le {currentStatus.date.slice(0, 10)}</span>
            )}
            {currentStatus?.comment && (
              <span className="ml-1 text-xs text-neutral-500" title={currentStatus.comment}>
                — {currentStatus.comment}
              </span>
            )}
          </span>

          <div className="ml-auto flex flex-wrap items-center gap-3 text-sm">
            <label className="flex items-center gap-1.5">
              Méthode
              <select
                value={validationMethod}
                onChange={(e) => setValidationMethod(e.target.value as 'legacy' | 'enhanced')}
                className="rounded border border-neutral-300 px-1.5 py-0.5 text-sm"
              >
                <option value="legacy">Legacy (classique)</option>
                <option value="enhanced">Enhanced (améliorée)</option>
              </select>
            </label>
            {brandConfig.requiresDigitsValidation() && (
              <label className="flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={checkDigits}
                  onChange={(e) => setCheckDigits(e.target.checked)}
                />
                4 DIGITS
              </label>
            )}
            {entry?.needsManualReview ? (
              <span
                className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800"
                title="Moins de 50 caractères de texte extraits — PDF probablement scanné ou vectorisé"
              >
                ⚠️ Revue manuelle requise
              </span>
            ) : (
              <span className="rounded-full bg-neutral-100 px-2.5 py-0.5 text-xs text-neutral-600">
                📄 Texte standard
              </span>
            )}
          </div>
        </div>

        {/* PDF + results */}
        <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 xl:grid-cols-2">
          <div className="flex flex-col rounded-xl border border-neutral-200 bg-white p-3">
            {entry && (
              <>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="truncate text-xs text-neutral-500" title={entry.fileName}>
                    {entry.fileName}
                  </span>
                  <span className="flex items-center gap-2">
                    <button
                      onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
                      disabled={pageNumber <= 1}
                      className="rounded border border-neutral-300 px-2 py-0.5 disabled:opacity-40"
                    >
                      ◀
                    </button>
                    Page {pageNumber} / {entry.pageCount}
                    <button
                      onClick={() => setPageNumber((p) => Math.min(entry.pageCount, p + 1))}
                      disabled={pageNumber >= entry.pageCount}
                      className="rounded border border-neutral-300 px-2 py-0.5 disabled:opacity-40"
                    >
                      ▶
                    </button>
                  </span>
                </div>
                <div className="flex-1 overflow-auto rounded border border-neutral-100 bg-neutral-50 p-2">
                  <PdfCanvas
                    file={entry.file}
                    pageNumber={pageNumber}
                    maxWidth={700}
                    className="mx-auto max-w-full shadow"
                  />
                </div>
              </>
            )}
          </div>

          <div className="flex flex-col gap-3 overflow-auto rounded-xl border border-neutral-200 bg-white p-3">
            {excelData.length === 0 ? (
              <div className="py-8 text-center text-sm text-neutral-400">
                Aucune donnée Excel pour <span className="font-mono">{currentCode}</span>
                {rawSheet ? '' : ' — chargez le brief Excel'}
              </div>
            ) : cubby ? (
              <CubbyMatrix result={cubby} />
            ) : (
              <ResultsTable excelData={excelData} results={rowResults} />
            )}
            {entry && excelData.length > 0 && !cubby && (
              <AiPanel entry={entry} excelData={excelData} />
            )}
          </div>
        </div>
      </section>
    </div>
  )
}

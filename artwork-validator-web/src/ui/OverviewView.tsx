// Overview: stats header, filters/search/sort, list/grid toggle, one card per
// litho with thumbnail + type badge + status, quick approve/reject.
import { useMemo, useState } from 'react'
import { getLithoStatus, updateLithoStatus } from '../lib/sessionStore'
import { saveToLocalStorage } from '../lib/sessionStore'
import { isCubbyResult } from '../core/validator'
import { lithoCodesOf, useAppStore, validateLitho } from '../state/appStore'
import { PdfCanvas } from './PdfCanvas'
import { toast } from './toast'

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected'
type SortMode = 'file' | 'code' | 'status'

export function OverviewView() {
  const pdfEntries = useAppStore((s) => s.pdfEntries)
  const rawSheet = useAppStore((s) => s.rawSheet)
  const brandConfig = useAppStore((s) => s.brandConfig)
  const checkDigits = useAppStore((s) => s.checkDigits)
  const validationMethod = useAppStore((s) => s.validationMethod)
  const session = useAppStore((s) => s.session)
  const goToLitho = useAppStore((s) => s.goToLitho)

  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [search, setSearch] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('file')
  const [gridMode, setGridMode] = useState(true)

  const codes = useMemo(() => lithoCodesOf(pdfEntries), [pdfEntries])

  const lithoTypes = useMemo(() => {
    const types = new Map<string, string>()
    if (!rawSheet) return types
    for (const code of codes) {
      const { results } = validateLitho(
        { brandConfig, checkDigits, validationMethod, rawSheet, pdfEntries },
        code,
      )
      if (!results.length) {
        types.set(code, 'Aucune donnée')
      } else if (isCubbyResult(results[0])) {
        types.set(code, 'CUBBY')
      } else {
        const first = results[0]
        const isMixed = 'is_mixed' in first && first.is_mixed
        const hasSaver = results.some((r) => 'is_space_saver' in r && r.is_space_saver)
        const parts: string[] = []
        if (isMixed) parts.push('MIXED')
        if (hasSaver) parts.push('SPACE_SAVER')
        types.set(code, parts.length ? parts.join(' + ') : 'Standard')
      }
    }
    return types
  }, [codes, rawSheet, brandConfig, checkDigits, validationMethod, pdfEntries])

  const statuses = codes.map((c) => getLithoStatus(session, c)?.status ?? 'pending')
  const approvedCount = statuses.filter((s) => s === 'approved').length
  const rejectedCount = statuses.filter((s) => s === 'rejected').length
  const pendingCount = codes.length - approvedCount - rejectedCount

  const visibleCodes = useMemo(() => {
    let list = codes.filter((code) => {
      const st = getLithoStatus(session, code)?.status ?? 'pending'
      if (statusFilter !== 'all' && st !== statusFilter) return false
      return !search || code.toUpperCase().includes(search.toUpperCase())
    })
    if (sortMode === 'code') list = [...list].sort()
    if (sortMode === 'status') {
      const order = { rejected: 0, pending: 1, approved: 2 }
      list = [...list].sort(
        (a, b) =>
          order[getLithoStatus(session, a)?.status ?? 'pending'] -
          order[getLithoStatus(session, b)?.status ?? 'pending'],
      )
    }
    return list
  }, [codes, session, statusFilter, search, sortMode])

  function quickValidate(code: string, status: 'approved' | 'rejected') {
    const next = updateLithoStatus(session, code, status, '')
    saveToLocalStorage(next)
    useAppStore.setState({ session: next, dirty: true })
    toast(status === 'approved' ? `✅ ${code} approuvée` : `❌ ${code} refusée`, 'success')
  }

  if (!codes.length) {
    return (
      <div className="p-8 text-center text-neutral-500">
        Chargez un dossier de PDFs pour voir la vue d'ensemble.
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col gap-3 p-3">
      {/* Stats header */}
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {[
          ['Total', String(codes.length), 'bg-neutral-900 text-white'],
          ['Approuvées', String(approvedCount), 'bg-emerald-600 text-white'],
          ['Rejetées', String(rejectedCount), 'bg-red-600 text-white'],
          ['En attente', String(pendingCount), 'bg-amber-500 text-white'],
        ].map(([label, value, cls]) => (
          <div key={label} className={`rounded-xl px-4 py-3 ${cls}`}>
            <div className="text-xs uppercase tracking-wide opacity-75">{label}</div>
            <div className="text-2xl font-bold">{value}</div>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-neutral-200 bg-white px-3 py-2 text-sm">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          className="rounded border border-neutral-300 px-2 py-1"
        >
          <option value="all">Tous les statuts</option>
          <option value="pending">⏳ En attente</option>
          <option value="approved">✅ Approuvées</option>
          <option value="rejected">❌ Rejetées</option>
        </select>
        <select
          value={sortMode}
          onChange={(e) => setSortMode(e.target.value as SortMode)}
          className="rounded border border-neutral-300 px-2 py-1"
        >
          <option value="file">Ordre des fichiers</option>
          <option value="code">Tri par code</option>
          <option value="status">Tri par statut</option>
        </select>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher une litho…"
          className="min-w-40 flex-1 rounded border border-neutral-300 px-2 py-1"
        />
        <button
          onClick={() => setGridMode(!gridMode)}
          className="rounded border border-neutral-300 px-2.5 py-1 hover:bg-neutral-100"
        >
          {gridMode ? '📋 Liste' : '🎴 Grille'}
        </button>
      </div>

      {/* Cards */}
      <div
        className={
          'min-h-0 flex-1 overflow-y-auto ' +
          (gridMode
            ? 'grid grid-cols-2 content-start gap-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
            : 'flex flex-col gap-2')
        }
      >
        {visibleCodes.map((code) => {
          const entry = pdfEntries.find((e) => e.lithoCode === code)!
          const st = getLithoStatus(session, code)
          const status = st?.status ?? 'pending'
          const type = lithoTypes.get(code) ?? '…'
          const statusColor =
            status === 'approved'
              ? 'border-emerald-400'
              : status === 'rejected'
                ? 'border-red-400'
                : 'border-neutral-200'
          return (
            <div
              key={code}
              className={`group relative flex cursor-pointer rounded-xl border-2 bg-white transition hover:shadow-md ${statusColor} ${
                gridMode ? 'flex-col p-2' : 'items-center gap-3 px-3 py-2'
              }`}
              onClick={() => goToLitho(code)}
            >
              <div className={gridMode ? 'h-32 overflow-hidden rounded bg-neutral-50' : 'h-14 w-10 overflow-hidden rounded bg-neutral-50'}>
                <PdfCanvas file={entry.file} pageNumber={1} maxWidth={gridMode ? 180 : 40} className="mx-auto max-h-full" />
              </div>
              <div className={gridMode ? 'mt-2 flex flex-col gap-1' : 'flex flex-1 items-center gap-3'}>
                <span className="font-mono text-xs font-bold">{code}</span>
                <span className="w-fit rounded-full bg-neutral-100 px-2 py-0.5 text-[10px] font-semibold text-neutral-600">
                  {type}
                </span>
                <span className="text-xs">
                  {status === 'approved' ? '✅' : status === 'rejected' ? '❌' : '⏳'}
                </span>
              </div>
              <div
                className="absolute right-2 top-2 hidden gap-1 group-hover:flex"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  onClick={() => quickValidate(code, 'approved')}
                  className="rounded bg-emerald-600 px-1.5 py-0.5 text-xs text-white"
                  title="Approuver"
                >
                  ✓
                </button>
                <button
                  onClick={() => quickValidate(code, 'rejected')}
                  className="rounded bg-red-600 px-1.5 py-0.5 text-xs text-white"
                  title="Refuser"
                >
                  ✗
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

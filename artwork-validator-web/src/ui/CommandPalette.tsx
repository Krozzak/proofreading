// Ctrl+K command palette: navigate views, jump to a litho, trigger actions.
import { useEffect, useMemo, useRef, useState } from 'react'
import { lithoCodesOf, useAppStore } from '../state/appStore'
import { exportSession } from './sessionActions'
import { exportValidationReport } from './reportExport'

interface Command {
  id: string
  label: string
  run(): void
}

interface Props {
  open: boolean
  onClose(): void
}

/** Simple fuzzy score: exact substring > word-prefix > character subsequence. */
function score(query: string, label: string): number {
  const q = query.toLowerCase()
  const l = label.toLowerCase()
  if (!q) return 1
  if (l.includes(q)) return 100 - l.indexOf(q)
  let qi = 0
  for (const ch of l) {
    if (ch === q[qi]) qi++
    if (qi === q.length) return 10
  }
  return qi === q.length ? 10 : 0
}

export function CommandPalette({ open, onClose }: Props) {
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const setView = useAppStore((s) => s.setView)
  const goToLitho = useAppStore((s) => s.goToLitho)
  const pdfEntries = useAppStore((s) => s.pdfEntries)

  const commands = useMemo<Command[]>(() => {
    const base: Command[] = [
      { id: 'view-overview', label: "Aller à : Vue d'ensemble", run: () => setView('overview') },
      { id: 'view-validation', label: 'Aller à : Validation', run: () => setView('validation') },
      { id: 'view-settings', label: 'Aller à : Paramètres', run: () => setView('settings') },
      { id: 'export-report', label: '📊 Exporter le rapport Excel', run: () => void exportValidationReport() },
      { id: 'export-session', label: '💾 Exporter la session JSON', run: exportSession },
    ]
    for (const code of lithoCodesOf(pdfEntries)) {
      base.push({ id: `litho-${code}`, label: `Ouvrir la litho ${code}`, run: () => goToLitho(code) })
    }
    return base
  }, [pdfEntries, setView, goToLitho])

  const results = useMemo(
    () =>
      commands
        .map((c) => ({ c, s: score(query, c.label) }))
        .filter(({ s }) => s > 0)
        .sort((a, b) => b.s - a.s)
        .slice(0, 12)
        .map(({ c }) => c),
    [commands, query],
  )

  useEffect(() => {
    if (open) {
      setQuery('')
      setSelected(0)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 pt-24" onClick={onClose}>
      <div
        className="w-full max-w-lg rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setSelected(0)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Escape') onClose()
            if (e.key === 'ArrowDown') setSelected((s) => Math.min(s + 1, results.length - 1))
            if (e.key === 'ArrowUp') setSelected((s) => Math.max(s - 1, 0))
            if (e.key === 'Enter' && results[selected]) {
              results[selected].run()
              onClose()
            }
          }}
          placeholder="Tapez une commande ou un code litho…"
          className="w-full border-b border-neutral-200 px-4 py-3 text-sm outline-none"
        />
        <div className="max-h-72 overflow-y-auto p-1">
          {results.map((c, i) => (
            <button
              key={c.id}
              onClick={() => {
                c.run()
                onClose()
              }}
              className={
                'block w-full rounded px-3 py-2 text-left text-sm ' +
                (i === selected ? 'bg-red-50 text-red-800' : 'hover:bg-neutral-100')
              }
            >
              {c.label}
            </button>
          ))}
          {!results.length && (
            <div className="px-3 py-4 text-center text-sm text-neutral-400">Aucun résultat</div>
          )}
        </div>
      </div>
    </div>
  )
}

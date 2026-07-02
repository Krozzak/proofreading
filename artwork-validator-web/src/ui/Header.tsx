// Global chrome: title, brand selector, view tabs, session actions.
import { useRef } from 'react'
import { getAllBrands } from '../core/brandConfigs'
import { useAppStore, type ViewName } from '../state/appStore'
import { exportSession, importSessionFromFile } from './sessionActions'
import { exportValidationReport } from './reportExport'

const TABS: { key: ViewName; label: string; shortcut: string }[] = [
  { key: 'files', label: '📁 Fichiers', shortcut: '' },
  { key: 'overview', label: "Vue d'ensemble", shortcut: 'Ctrl+1' },
  { key: 'validation', label: 'Validation', shortcut: 'Ctrl+2' },
  { key: 'settings', label: 'Paramètres', shortcut: 'Ctrl+3' },
]

export function Header() {
  const view = useAppStore((s) => s.view)
  const setView = useAppStore((s) => s.setView)
  const brandCode = useAppStore((s) => s.brandCode)
  const setBrand = useAppStore((s) => s.setBrand)
  useAppStore((s) => s.brandsVersion) // re-render the brand list after CRUD
  const sessionName = useAppStore((s) => s.session.session_name)
  const setSessionName = useAppStore((s) => s.setSessionName)
  const importInputRef = useRef<HTMLInputElement>(null)

  return (
    <header className="flex flex-wrap items-center gap-3 border-b border-neutral-800 bg-black px-4 py-2 text-white">
      <div className="flex items-center gap-2">
        <span className="text-lg font-bold tracking-tight">
          L'Oréal <span className="text-red-500">Litho Validator</span>
        </span>
        <span className="rounded bg-neutral-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-neutral-400">
          Web
        </span>
      </div>

      <nav className="flex items-center gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setView(tab.key)}
            title={tab.shortcut}
            className={
              'rounded px-3 py-1.5 text-sm transition ' +
              (view === tab.key
                ? 'bg-red-600 font-semibold text-white'
                : 'text-neutral-300 hover:bg-neutral-800')
            }
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="ml-auto flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-1.5 text-xs text-neutral-400">
          Marque
          <select
            value={brandCode}
            onChange={(e) => setBrand(e.target.value)}
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm text-white"
          >
            {getAllBrands().map((b) => (
              <option key={b.getBrandCode()} value={b.getBrandCode()}>
                {b.getBrandDisplayName()}
              </option>
            ))}
          </select>
        </label>

        <input
          value={sessionName}
          onChange={(e) => setSessionName(e.target.value)}
          placeholder="Nom de session…"
          className="w-36 rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm text-white placeholder:text-neutral-500"
        />

        <button
          onClick={exportSession}
          title="Exporter la session (Ctrl+S)"
          className="rounded border border-neutral-700 px-2.5 py-1 text-sm text-neutral-200 hover:bg-neutral-800"
        >
          💾 Session
        </button>
        <button
          onClick={() => importInputRef.current?.click()}
          title="Importer une session JSON"
          className="rounded border border-neutral-700 px-2.5 py-1 text-sm text-neutral-200 hover:bg-neutral-800"
        >
          📂 Importer
        </button>
        <input
          ref={importInputRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) importSessionFromFile(file)
            e.target.value = ''
          }}
        />
        <button
          onClick={() => void exportValidationReport()}
          title="Exporter le rapport Excel (Ctrl+E)"
          className="rounded bg-red-600 px-2.5 py-1 text-sm font-semibold text-white hover:bg-red-500"
        >
          📊 Rapport
        </button>
      </div>
    </header>
  )
}

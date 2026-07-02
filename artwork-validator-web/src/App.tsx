// App shell: header + active view + startup drop zones, global keyboard
// shortcuts, beforeunload guard, command palette and help modals.
import { useEffect, useState } from 'react'
import { useAppStore } from './state/appStore'
import { Header } from './ui/Header'
import { FileDropZone } from './ui/FileDropZone'
import { ValidationView } from './ui/ValidationView'
import { OverviewView } from './ui/OverviewView'
import { SettingsView } from './ui/SettingsView'
import { CommandPalette } from './ui/CommandPalette'
import { ShortcutsHelp } from './ui/ShortcutsHelp'
import { Toaster, toast } from './ui/toast'
import { exportSession } from './ui/sessionActions'
import { exportValidationReport } from './ui/reportExport'

export default function App() {
  const view = useAppStore((s) => s.view)
  const ready = useAppStore((s) => s.pdfEntries.length > 0 && s.rawSheet !== null)
  const dirty = useAppStore((s) => s.dirty)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (!(e.ctrlKey || e.metaKey)) return
      const state = useAppStore.getState()
      switch (e.key) {
        case 'k':
        case 'K':
          e.preventDefault()
          setPaletteOpen((o) => !o)
          break
        case '/':
          e.preventDefault()
          setHelpOpen((o) => !o)
          break
        case '1':
          e.preventDefault()
          state.setView('overview')
          break
        case '2':
          e.preventDefault()
          state.setView('validation')
          break
        case '3':
          e.preventDefault()
          state.setView('settings')
          break
        case 'ArrowLeft':
          e.preventDefault()
          state.previousLitho()
          break
        case 'ArrowRight':
          e.preventDefault()
          state.nextLitho()
          break
        case 'Enter':
          e.preventDefault()
          if (state.view === 'validation') {
            state.validateCurrent('approved', '')
            toast('✅ Litho approuvée', 'success')
          }
          break
        case 'r':
        case 'R':
          // Hijacks browser reload on purpose (internal tool, documented in help)
          e.preventDefault()
          if (state.view === 'validation') {
            state.validateCurrent('rejected', '')
            toast('❌ Litho refusée', 'info')
          }
          break
        case 's':
        case 'S':
          e.preventDefault()
          exportSession()
          break
        case 'e':
        case 'E':
          e.preventDefault()
          void exportValidationReport()
          break
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  useEffect(() => {
    function onBeforeUnload(e: BeforeUnloadEvent) {
      if (dirty) {
        e.preventDefault()
      }
    }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [dirty])

  return (
    <div className="flex h-full flex-col">
      <Header />
      <main className="min-h-0 flex-1 overflow-y-auto">
        {!ready || view === 'files' ? (
          <FileDropZone />
        ) : view === 'overview' ? (
          <OverviewView />
        ) : view === 'settings' ? (
          <SettingsView />
        ) : (
          <ValidationView />
        )}
      </main>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      <ShortcutsHelp open={helpOpen} onClose={() => setHelpOpen(false)} />
      <Toaster />
    </div>
  )
}

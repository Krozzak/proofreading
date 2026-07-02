// Session export/import wiring (replaces the desktop file dialogs).
import { exportSessionJson, importSessionJson, sanitizeSessionFilename } from '../lib/sessionStore'
import { downloadBlob } from '../lib/excelIO'
import { getDefinition, isBuiltinBrand } from '../core/brandConfigs'
import { useAppStore } from '../state/appStore'
import { toast } from './toast'

export function exportSession(): void {
  const state = useAppStore.getState()
  // Embed the brand definition when it's a custom one, so the session can be
  // imported on a machine that doesn't have that brand yet.
  const customBrand = !isBuiltinBrand(state.brandCode) ? getDefinition(state.brandCode) : null
  const json = exportSessionJson({
    ...state.session,
    ...(customBrand ? { custom_brand: customBrand } : {}),
  })
  const name = sanitizeSessionFilename(state.session.session_name || 'session')
  downloadBlob(json, `${name}.json`, 'application/json')
  useAppStore.setState({ dirty: false })
  toast('Session exportée en JSON', 'success')
}

export function importSessionFromFile(file: File): void {
  file
    .text()
    .then((text) => {
      const session = importSessionJson(text)
      useAppStore.getState().restoreSession(session)
      toast(`Session « ${session.session_name} » importée`, 'success')
    })
    .catch((e) => {
      toast(`Fichier de session invalide: ${e instanceof Error ? e.message : e}`, 'error')
    })
}

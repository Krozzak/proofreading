// Ctrl+/ shortcuts help modal.
interface Props {
  open: boolean
  onClose(): void
}

const SHORTCUTS: [string, string][] = [
  ['Ctrl+K', 'Palette de commandes'],
  ['Ctrl+/', "Afficher cette aide"],
  ['Ctrl+1', "Vue d'ensemble"],
  ['Ctrl+2', 'Vue Validation'],
  ['Ctrl+3', 'Paramètres'],
  ['Ctrl+←', 'PDF précédent'],
  ['Ctrl+→', 'PDF suivant'],
  ['Ctrl+Entrée', 'Approuver la litho courante'],
  ['Ctrl+R', 'Refuser la litho courante (remplace le rechargement navigateur)'],
  ['Ctrl+S', 'Exporter la session JSON'],
  ['Ctrl+E', 'Exporter le rapport Excel'],
]

export function ShortcutsHelp({ open, onClose }: Props) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-xl bg-white p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-3 font-bold">⌨️ Raccourcis clavier</h2>
        <table className="w-full text-sm">
          <tbody>
            {SHORTCUTS.map(([key, label]) => (
              <tr key={key} className="border-t border-neutral-100">
                <td className="py-1.5 pr-3">
                  <kbd className="rounded bg-neutral-100 px-1.5 py-0.5 font-mono text-xs">{key}</kbd>
                </td>
                <td className="py-1.5 text-neutral-600">{label}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <button
          onClick={onClose}
          className="mt-4 w-full rounded bg-neutral-900 py-2 text-sm text-white"
        >
          Fermer
        </button>
      </div>
    </div>
  )
}

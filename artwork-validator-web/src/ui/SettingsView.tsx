// Paramètres: brand rules read-out, quick-responses editor, session
// management, about box.
import { useState } from 'react'
import { useAppStore } from '../state/appStore'
import { clearLocalStorage } from '../lib/sessionStore'
import { exportSession, importSessionFromFile } from './sessionActions'
import { BrandManager } from './BrandManager'
import { AiSettingsSection } from './AiSettingsSection'
import { toast } from './toast'
import { useRef } from 'react'

function numOrNull(raw: string): number | null {
  const value = Number(raw.replace(',', '.'))
  return raw.trim() !== '' && Number.isFinite(value) && value > 0 ? value : null
}

export function SettingsView() {
  const brandConfig = useAppStore((s) => s.brandConfig)
  const customQuickResponses = useAppStore((s) => s.customQuickResponses)
  const setCustomQuickResponses = useAppStore((s) => s.setCustomQuickResponses)
  const resetSession = useAppStore((s) => s.resetSession)
  const session = useAppStore((s) => s.session)
  const expectedSize = useAppStore((s) => s.expectedSize)
  const setExpectedSize = useAppStore((s) => s.setExpectedSize)

  const [newResponse, setNewResponse] = useState('')
  const importRef = useRef<HTMLInputElement>(null)

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 p-4">
      <BrandManager />

      <section className="rounded-xl border border-neutral-200 bg-white p-4">
        <h2 className="mb-2 font-bold">Règles de validation — {brandConfig.getBrandDisplayName()}</h2>
        <pre className="whitespace-pre-wrap rounded bg-neutral-50 p-3 text-xs text-neutral-700">
          {brandConfig.getValidationDescription()}
        </pre>
      </section>

      <AiSettingsSection />

      <section className="rounded-xl border border-neutral-200 bg-white p-4">
        <h2 className="mb-2 font-bold">📐 Taille du visuel (bêta)</h2>
        <p className="mb-3 text-xs text-neutral-500">
          La taille affichée est lue dans les métadonnées du PDF : le <b>TrimBox</b> (format
          fini après coupe) quand il est présent, sinon le <b>CropBox</b> (taille de page,
          qui peut inclure fonds perdus et traits de coupe). La détection des lignes de
          coupe (dielines) dessinées dans le visuel est prévue dans une prochaine version —
          elle donnera les vraies dimensions même quand les métadonnées sont absentes.
          Renseignez une taille attendue pour faire vérifier chaque litho (comparaison
          indépendante de l'orientation).
        </p>
        <div className="flex flex-wrap items-end gap-3 text-sm">
          <label className="flex flex-col gap-1">
            <span className="text-xs text-neutral-500">Largeur attendue (mm)</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={expectedSize.widthMm ?? ''}
              onChange={(e) => setExpectedSize({ ...expectedSize, widthMm: numOrNull(e.target.value) })}
              placeholder="ex : 450"
              className="w-36 rounded border border-neutral-300 px-2 py-1"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-neutral-500">Hauteur attendue (mm)</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={expectedSize.heightMm ?? ''}
              onChange={(e) => setExpectedSize({ ...expectedSize, heightMm: numOrNull(e.target.value) })}
              placeholder="ex : 1200"
              className="w-36 rounded border border-neutral-300 px-2 py-1"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-neutral-500">Tolérance (± mm)</span>
            <input
              type="number"
              min="0"
              step="0.5"
              value={expectedSize.toleranceMm}
              onChange={(e) =>
                setExpectedSize({ ...expectedSize, toleranceMm: numOrNull(e.target.value) ?? 2 })
              }
              className="w-24 rounded border border-neutral-300 px-2 py-1"
            />
          </label>
          <button
            onClick={() => setExpectedSize({ widthMm: null, heightMm: null, toleranceMm: 2 })}
            className="rounded border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-100"
          >
            Effacer
          </button>
        </div>
      </section>

      <section className="rounded-xl border border-neutral-200 bg-white p-4">
        <h2 className="mb-2 font-bold">Réponses rapides personnalisées</h2>
        <p className="mb-2 text-xs text-neutral-500">
          Ces réponses s'ajoutent aux suggestions automatiques dans le panneau de validation.
        </p>
        <div className="flex flex-col gap-1">
          {customQuickResponses.map((qr, i) => (
            <div key={i} className="flex items-center gap-2 rounded border border-neutral-200 px-2 py-1 text-sm">
              <span className="flex-1">{qr}</span>
              <button
                onClick={() =>
                  setCustomQuickResponses(customQuickResponses.filter((_, j) => j !== i))
                }
                className="text-red-600 hover:text-red-500"
                title="Supprimer"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
        <div className="mt-2 flex gap-2">
          <input
            value={newResponse}
            onChange={(e) => setNewResponse(e.target.value)}
            placeholder="Nouvelle réponse rapide…"
            className="flex-1 rounded border border-neutral-300 px-2 py-1 text-sm"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && newResponse.trim()) {
                setCustomQuickResponses([...customQuickResponses, newResponse.trim()])
                setNewResponse('')
              }
            }}
          />
          <button
            onClick={() => {
              if (newResponse.trim()) {
                setCustomQuickResponses([...customQuickResponses, newResponse.trim()])
                setNewResponse('')
              }
            }}
            className="rounded bg-neutral-900 px-3 py-1 text-sm text-white"
          >
            Ajouter
          </button>
        </div>
      </section>

      <section className="rounded-xl border border-neutral-200 bg-white p-4">
        <h2 className="mb-2 font-bold">Session</h2>
        <p className="mb-3 text-xs text-neutral-500">
          Session courante : « {session.session_name || 'sans nom'} » —{' '}
          {Object.keys(session.validations).length} validation(s). La session est sauvegardée
          automatiquement dans le navigateur ; exportez-la en JSON pour l'archiver ou la partager
          (compatible avec les sessions de l'application bureau).
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={exportSession}
            className="rounded border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-100"
          >
            💾 Exporter la session (JSON)
          </button>
          <button
            onClick={() => importRef.current?.click()}
            className="rounded border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-100"
          >
            📂 Importer une session
          </button>
          <button
            onClick={() => {
              if (confirm('Réinitialiser la session ? Toutes les validations seront perdues.')) {
                clearLocalStorage()
                resetSession()
                toast('Session réinitialisée', 'info')
              }
            }}
            className="rounded border border-red-300 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
          >
            🗑️ Réinitialiser
          </button>
          <input
            ref={importRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) importSessionFromFile(f)
              e.target.value = ''
            }}
          />
        </div>
      </section>

      <section className="rounded-xl border border-neutral-200 bg-white p-4 text-xs text-neutral-500">
        <h2 className="mb-2 font-bold text-neutral-900">À propos</h2>
        <p>
          L'Oréal Artwork Validator — version web (v1.1.0). Application 100% navigateur : aucun
          fichier n'est envoyé sur un serveur, tout le traitement (extraction PDF, validation,
          rapport Excel) se fait localement. Les PDFs avec moins de 50 caractères de texte
          extractible sont marqués « Revue manuelle requise » (l'application bureau utilisait un
          fallback OCR ; une future intégration IA le remplacera).
        </p>
        <p className="mt-2">
          Raccourcis : Ctrl+K palette de commandes · Ctrl+/ aide · Ctrl+1/2/3 vues · Ctrl+←/→
          navigation · Ctrl+Entrée approuver · Ctrl+R refuser · Ctrl+S exporter session · Ctrl+E
          exporter rapport.
        </p>
      </section>
    </div>
  )
}

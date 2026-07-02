// Paramètres → Intelligence artificielle: provider-agnostic API settings
// (Anthropic / OpenAI-compatible), stored in the browser only.
import { useState } from 'react'
import {
  DEFAULT_BASE_URLS,
  DEFAULT_MODELS,
  loadAiSettings,
  saveAiSettings,
  testConnection,
  type AiProvider,
} from '../lib/ai'
import { toast } from './toast'

export function AiSettingsSection() {
  const [settings, setSettings] = useState(loadAiSettings)
  const [testing, setTesting] = useState(false)

  function update<K extends keyof typeof settings>(key: K, value: (typeof settings)[K]) {
    setSettings((s) => ({ ...s, [key]: value }))
  }

  function onProviderChange(provider: AiProvider) {
    setSettings((s) => ({
      ...s,
      provider,
      baseUrl: DEFAULT_BASE_URLS[provider],
      model: DEFAULT_MODELS[provider],
    }))
  }

  function save() {
    saveAiSettings(settings)
    toast('Réglages IA enregistrés', 'success')
  }

  async function test() {
    setTesting(true)
    try {
      saveAiSettings(settings)
      await testConnection(settings)
      toast('✅ Connexion IA fonctionnelle', 'success')
    } catch (e) {
      toast(`❌ Test échoué: ${e instanceof Error ? e.message : e}`, 'error')
    } finally {
      setTesting(false)
    }
  }

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <h2 className="mb-2 font-bold">Intelligence artificielle (optionnel)</h2>
      <p className="mb-3 text-xs text-neutral-500">
        Permet l'analyse visuelle des lithos par un modèle multimodal (utile pour les PDF scannés /
        vectorisés et les vérifications hors format) et la génération de marques dans le wizard. La
        clé API reste dans CE navigateur (localStorage) et n'est envoyée qu'au fournisseur configuré.
        ⚠️ Chaque analyse envoie les images de la litho à l'API — coût par appel et confidentialité à
        valider avec ton équipe.
      </p>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">
          Fournisseur (format d'API)
          <select
            value={settings.provider}
            onChange={(e) => onProviderChange(e.target.value as AiProvider)}
            className="rounded border border-neutral-300 px-2 py-1.5"
          >
            <option value="anthropic">Anthropic (Claude)</option>
            <option value="openai">OpenAI / compatible (Azure, proxy interne…)</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Modèle
          <input
            value={settings.model}
            onChange={(e) => update('model', e.target.value)}
            placeholder={DEFAULT_MODELS[settings.provider]}
            className="rounded border border-neutral-300 px-2 py-1.5 font-mono text-xs"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          URL de base
          <input
            value={settings.baseUrl}
            onChange={(e) => update('baseUrl', e.target.value)}
            placeholder={DEFAULT_BASE_URLS[settings.provider]}
            className="rounded border border-neutral-300 px-2 py-1.5 font-mono text-xs"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Clé API
          <input
            type="password"
            value={settings.apiKey}
            onChange={(e) => update('apiKey', e.target.value)}
            placeholder="sk-…"
            className="rounded border border-neutral-300 px-2 py-1.5 font-mono text-xs"
          />
        </label>
      </div>

      <div className="mt-3 flex gap-2">
        <button
          onClick={save}
          className="rounded bg-neutral-900 px-3 py-1.5 text-sm font-semibold text-white"
        >
          Enregistrer
        </button>
        <button
          onClick={() => void test()}
          disabled={!settings.apiKey || testing}
          className="rounded border border-neutral-300 px-3 py-1.5 text-sm disabled:opacity-40"
        >
          {testing ? 'Test en cours…' : '🔌 Tester la connexion'}
        </button>
      </div>
    </section>
  )
}

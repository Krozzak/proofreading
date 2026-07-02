// Multi-step brand creation/edition wizard: no code needed to add a brand
// (NYX, L'Oréal Paris, Garnier…). Produces a BrandDefinition JSON, tested
// live against sample filenames before saving.
import { useMemo, useState } from 'react'
import type { BrandColumn, BrandDefinition, FilenameRule } from '../core/brandConfigs'
import {
  BRAND_SCHEMA_VERSION,
  STANDARD_COLUMNS,
  brandFromDefinition,
  getBrandCodes,
  isBuiltinBrand,
  validateBrandDefinition,
} from '../core/brandConfigs'
import { saveCustomBrand } from '../lib/brandStore'
import { generateBrandWithAi, isAiConfigured } from '../lib/ai'
import { toast } from './toast'

interface Props {
  open: boolean
  /** When set, the wizard edits this definition instead of creating one. */
  initial?: BrandDefinition | null
  onClose(): void
  onSaved(def: BrandDefinition): void
}

const STEPS = ['Marque', 'Fichiers PDF', 'Colonnes', 'Options', 'Récapitulatif'] as const

function draftFrom(initial: BrandDefinition | null | undefined): {
  code: string
  name: string
  mode: 'prefix' | 'regex'
  literal: string
  digits: number
  filenamePattern: string
  extractPattern: string
  codePattern: string
  columns: BrandColumn[]
  requiresUpc: boolean
  requiresDigits: boolean
  testNames: string
} {
  if (initial) {
    return {
      code: initial.brand_code,
      name: initial.brand_name,
      mode: initial.filename.type,
      literal: initial.filename.type === 'prefix' ? initial.filename.literal : '',
      digits: initial.filename.type === 'prefix' ? initial.filename.digits : 5,
      filenamePattern: initial.filename.type === 'regex' ? initial.filename.filenamePattern : '',
      extractPattern: initial.filename.type === 'regex' ? initial.filename.extractPattern : '',
      codePattern: initial.filename.type === 'regex' ? initial.filename.codePattern : '',
      columns: initial.columns.map((c) => ({ ...c })),
      requiresUpc: initial.validation.requires_upc,
      requiresDigits: initial.validation.requires_digits,
      testNames: (initial.examples?.valid_filenames ?? []).join('\n'),
    }
  }
  return {
    code: '',
    name: '',
    mode: 'prefix',
    literal: '',
    digits: 5,
    filenamePattern: '',
    extractPattern: '',
    codePattern: '',
    columns: STANDARD_COLUMNS.map((c) => ({ ...c })),
    requiresUpc: false,
    requiresDigits: true,
    testNames: '',
  }
}

export function BrandWizard({ open, initial, onClose, onSaved }: Props) {
  const [step, setStep] = useState(0)
  const [draft, setDraft] = useState(() => draftFrom(initial))
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiBusy, setAiBusy] = useState(false)
  const [openedFor, setOpenedFor] = useState<BrandDefinition | null | undefined>(undefined)

  // Reset the draft when the wizard is (re)opened for a different brand
  if (open && openedFor !== initial) {
    setOpenedFor(initial)
    setDraft(draftFrom(initial))
    setStep(0)
    setAiPrompt('')
  }

  const definition: BrandDefinition = useMemo(() => {
    const filename: FilenameRule =
      draft.mode === 'prefix'
        ? { type: 'prefix', literal: draft.literal.toUpperCase(), digits: draft.digits }
        : {
            type: 'regex',
            filenamePattern: draft.filenamePattern,
            extractPattern: draft.extractPattern,
            codePattern: draft.codePattern,
            flags: 'i',
          }
    return {
      schema_version: BRAND_SCHEMA_VERSION,
      brand_code: draft.code.toUpperCase().trim(),
      brand_name: draft.name.trim(),
      filename,
      columns: draft.columns,
      validation: { requires_upc: draft.requiresUpc, requires_digits: draft.requiresDigits },
      examples: {
        valid_filenames: draft.testNames
          .split('\n')
          .map((s) => s.trim())
          .filter(Boolean)
          .slice(0, 5),
      },
      created_by: initial?.created_by === 'ai' ? 'ai' : 'wizard',
    }
  }, [draft, initial])

  const { errors } = useMemo(() => validateBrandDefinition(definition), [definition])

  const filenameTests = useMemo(() => {
    const names = draft.testNames
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    if (!names.length) return []
    const { definition: valid } = validateBrandDefinition(definition)
    if (!valid) return names.map((name) => ({ name, ok: false, code: null as string | null }))
    const config = brandFromDefinition(valid)
    return names.map((name) => ({
      name,
      ok: config.isValidFilename(name),
      code: config.extractLithoCode(name),
    }))
  }, [draft.testNames, definition])

  if (!open) return null

  const codeTaken =
    !initial && (getBrandCodes().includes(definition.brand_code) || isBuiltinBrand(definition.brand_code))

  function update<K extends keyof typeof draft>(key: K, value: (typeof draft)[K]) {
    setDraft((d) => ({ ...d, [key]: value }))
  }

  function save() {
    if (errors.length || codeTaken) return
    const result = saveCustomBrand(definition)
    if (!result.ok) {
      toast(result.error ?? 'Impossible de sauvegarder la marque', 'error')
      return
    }
    toast(`✅ Marque ${definition.brand_code} enregistrée`, 'success')
    onSaved(definition)
    onClose()
  }

  async function runAiGeneration() {
    if (!aiPrompt.trim()) return
    setAiBusy(true)
    try {
      const generated = await generateBrandWithAi(aiPrompt)
      setDraft({
        ...draftFrom(generated),
        testNames: (generated.examples?.valid_filenames ?? []).join('\n'),
      })
      toast('✨ Définition générée par l\'IA — vérifiez chaque étape avant d\'enregistrer', 'success')
      setStep(0)
    } catch (e) {
      toast(`Génération IA impossible: ${e instanceof Error ? e.message : e}`, 'error')
    } finally {
      setAiBusy(false)
    }
  }

  const stepValid =
    step === 0
      ? /^[A-Z0-9_]{2,20}$/.test(definition.brand_code) && definition.brand_name.length > 0 && !codeTaken
      : step === 1
        ? draft.mode === 'prefix'
          ? draft.literal.length > 0 && draft.digits >= 1
          : Boolean(draft.filenamePattern && draft.extractPattern && draft.codePattern)
        : step === 2
          ? draft.columns.length > 0 && draft.columns.some((c) => c.name === 'LITHO')
          : true

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header + steps */}
        <div className="border-b border-neutral-200 px-5 py-3">
          <div className="flex items-center justify-between">
            <h2 className="font-bold">
              {initial ? `Modifier la marque ${initial.brand_code}` : 'Nouvelle marque'}
            </h2>
            <button onClick={onClose} className="text-neutral-400 hover:text-neutral-700">✕</button>
          </div>
          <div className="mt-2 flex gap-1">
            {STEPS.map((label, i) => (
              <button
                key={label}
                onClick={() => i < step && setStep(i)}
                className={
                  'flex-1 rounded px-1 py-1 text-[11px] ' +
                  (i === step
                    ? 'bg-red-600 font-semibold text-white'
                    : i < step
                      ? 'bg-neutral-200 text-neutral-700'
                      : 'bg-neutral-100 text-neutral-400')
                }
              >
                {i + 1}. {label}
              </button>
            ))}
          </div>
        </div>

        {/* Body */}
        <div className="min-h-0 flex-1 overflow-y-auto p-5">
          {step === 0 && (
            <div className="flex flex-col gap-4">
              {!initial && (
                <div className="rounded-lg border border-violet-200 bg-violet-50 p-3 text-sm">
                  <div className="mb-1 font-semibold text-violet-900">✨ Créer avec l'IA (optionnel)</div>
                  <p className="mb-2 text-xs text-violet-800">
                    Décrivez la marque : format des noms de fichiers (avec des exemples), colonnes
                    particulières du brief… L'IA pré-remplit le wizard, vous validez ensuite chaque étape.
                    {!isAiConfigured() && (
                      <span className="font-semibold"> (Configurez d'abord l'API IA dans Paramètres, ou utilisez le Compagnon GPT.)</span>
                    )}
                  </p>
                  <textarea
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    rows={3}
                    placeholder="Ex: Marque NYX Professional Makeup. Les fichiers commencent par NYX suivi de 6 chiffres (NYX123456_v2.pdf). Brief standard sans colonne 4 DIGITS."
                    className="w-full rounded border border-violet-200 px-2 py-1.5 text-xs"
                  />
                  <button
                    onClick={() => void runAiGeneration()}
                    disabled={!isAiConfigured() || aiBusy || !aiPrompt.trim()}
                    className="mt-1 rounded bg-violet-600 px-3 py-1 text-xs font-semibold text-white disabled:opacity-40"
                  >
                    {aiBusy ? 'Génération…' : 'Générer la définition'}
                  </button>
                </div>
              )}
              <label className="flex flex-col gap-1 text-sm">
                Code de la marque (2-20 caractères, A-Z / 0-9 / _)
                <input
                  value={draft.code}
                  onChange={(e) => update('code', e.target.value.toUpperCase())}
                  disabled={Boolean(initial)}
                  placeholder="NYX, OAP, GARNIER…"
                  className="rounded border border-neutral-300 px-2 py-1.5 font-mono disabled:bg-neutral-100"
                />
                {codeTaken && <span className="text-xs text-red-600">Ce code est déjà utilisé.</span>}
              </label>
              <label className="flex flex-col gap-1 text-sm">
                Nom affiché
                <input
                  value={draft.name}
                  onChange={(e) => update('name', e.target.value)}
                  placeholder="NYX Professional Makeup"
                  className="rounded border border-neutral-300 px-2 py-1.5"
                />
              </label>
            </div>
          )}

          {step === 1 && (
            <div className="flex flex-col gap-4">
              <div className="flex gap-2">
                <button
                  onClick={() => update('mode', 'prefix')}
                  className={
                    'flex-1 rounded-lg border-2 p-3 text-left text-sm ' +
                    (draft.mode === 'prefix' ? 'border-red-500 bg-red-50' : 'border-neutral-200')
                  }
                >
                  <div className="font-semibold">Préfixe + chiffres</div>
                  <div className="text-xs text-neutral-500">Ex: YCA12345 (comme MNY)</div>
                </button>
                <button
                  onClick={() => update('mode', 'regex')}
                  className={
                    'flex-1 rounded-lg border-2 p-3 text-left text-sm ' +
                    (draft.mode === 'regex' ? 'border-red-500 bg-red-50' : 'border-neutral-200')
                  }
                >
                  <div className="font-semibold">Expression régulière (avancé)</div>
                  <div className="text-xs text-neutral-500">Ex: CARE_S26_1_3 (comme ESSIE)</div>
                </button>
              </div>

              {draft.mode === 'prefix' ? (
                <div className="flex gap-3">
                  <label className="flex flex-1 flex-col gap-1 text-sm">
                    Préfixe littéral
                    <input
                      value={draft.literal}
                      onChange={(e) => update('literal', e.target.value.toUpperCase())}
                      placeholder="YCA"
                      className="rounded border border-neutral-300 px-2 py-1.5 font-mono"
                    />
                  </label>
                  <label className="flex flex-1 flex-col gap-1 text-sm">
                    Nombre de chiffres après le préfixe
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={draft.digits}
                      onChange={(e) => update('digits', parseInt(e.target.value, 10) || 1)}
                      className="rounded border border-neutral-300 px-2 py-1.5"
                    />
                  </label>
                </div>
              ) : (
                <div className="flex flex-col gap-2 text-sm">
                  <label className="flex flex-col gap-1">
                    Pattern de nom de fichier valide (insensible à la casse)
                    <input
                      value={draft.filenamePattern}
                      onChange={(e) => update('filenamePattern', e.target.value)}
                      placeholder="^(CARE|GEL)_S\d+_\d+_\d+(_SHADESTRIPS)?"
                      className="rounded border border-neutral-300 px-2 py-1.5 font-mono text-xs"
                    />
                  </label>
                  <label className="flex flex-col gap-1">
                    Pattern d'extraction du code (groupe de capture 1)
                    <input
                      value={draft.extractPattern}
                      onChange={(e) => update('extractPattern', e.target.value)}
                      placeholder="^((CARE|GEL)_S\d+_\d+_\d+)"
                      className="rounded border border-neutral-300 px-2 py-1.5 font-mono text-xs"
                    />
                  </label>
                  <label className="flex flex-col gap-1">
                    Pattern de code litho valide (complet, avec $)
                    <input
                      value={draft.codePattern}
                      onChange={(e) => update('codePattern', e.target.value)}
                      placeholder="^(CARE|GEL)_S\d+_\d+_\d+$"
                      className="rounded border border-neutral-300 px-2 py-1.5 font-mono text-xs"
                    />
                  </label>
                </div>
              )}

              <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3">
                <div className="mb-1 text-sm font-semibold">🧪 Testez avec vos noms de fichiers réels</div>
                <textarea
                  value={draft.testNames}
                  onChange={(e) => update('testNames', e.target.value)}
                  rows={3}
                  placeholder={'Un nom de fichier par ligne, ex:\nNYX123456_v2.pdf\nmauvais_nom.pdf'}
                  className="w-full rounded border border-neutral-300 px-2 py-1.5 font-mono text-xs"
                />
                {filenameTests.length > 0 && (
                  <ul className="mt-2 flex flex-col gap-0.5 font-mono text-xs">
                    {filenameTests.map((t) => (
                      <li key={t.name}>
                        {t.ok ? '✅' : '❌'} {t.name}
                        {t.code && <span className="text-neutral-500"> → code {t.code}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="flex flex-col gap-2">
              <p className="text-xs text-neutral-500">
                Pré-rempli avec le brief standard L'Oréal. ⚠️ « DECRIPTION » est volontairement mal
                orthographié (les vrais briefs utilisent cet en-tête). La colonne LITHO est obligatoire.
              </p>
              <table className="w-full text-sm">
                <thead className="text-left text-xs uppercase text-neutral-500">
                  <tr>
                    <th className="py-1">Colonne</th>
                    <th>Obligatoire</th>
                    <th>Type</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {draft.columns.map((col, i) => (
                    <tr key={i} className="border-t border-neutral-100">
                      <td className="py-1">
                        <input
                          value={col.name}
                          onChange={(e) => {
                            const columns = [...draft.columns]
                            columns[i] = { ...col, name: e.target.value.toUpperCase() }
                            update('columns', columns)
                          }}
                          className="w-full rounded border border-neutral-200 px-2 py-0.5 font-mono text-xs"
                        />
                      </td>
                      <td>
                        <input
                          type="checkbox"
                          checked={col.required}
                          onChange={(e) => {
                            const columns = [...draft.columns]
                            columns[i] = { ...col, required: e.target.checked }
                            update('columns', columns)
                          }}
                        />
                      </td>
                      <td>
                        <select
                          value={col.type}
                          onChange={(e) => {
                            const columns = [...draft.columns]
                            columns[i] = { ...col, type: e.target.value as 'str' | 'numeric' }
                            update('columns', columns)
                          }}
                          className="rounded border border-neutral-200 px-1 py-0.5 text-xs"
                        >
                          <option value="str">texte</option>
                          <option value="numeric">numérique</option>
                        </select>
                      </td>
                      <td>
                        <button
                          onClick={() => update('columns', draft.columns.filter((_, j) => j !== i))}
                          disabled={col.name === 'LITHO'}
                          className="px-1 text-red-500 disabled:opacity-30"
                          title={col.name === 'LITHO' ? 'LITHO est obligatoire' : 'Supprimer'}
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button
                onClick={() =>
                  update('columns', [...draft.columns, { name: '', required: false, type: 'str' }])
                }
                className="self-start rounded border border-neutral-300 px-2 py-1 text-xs hover:bg-neutral-100"
              >
                + Ajouter une colonne
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col gap-4 text-sm">
              <label className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={draft.requiresDigits}
                  onChange={(e) => update('requiresDigits', e.target.checked)}
                  className="mt-0.5"
                />
                <span>
                  <span className="font-semibold">Validation 4 DIGITS (Walmart)</span>
                  <br />
                  <span className="text-xs text-neutral-500">
                    La colonne « 4 DIGITS » existe dans le brief et peut être vérifiée dans le PDF
                    (activable litho par litho ensuite). Nécessite la colonne dans l'étape Colonnes.
                  </span>
                </span>
              </label>
              <label className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={draft.requiresUpc}
                  onChange={(e) => update('requiresUpc', e.target.checked)}
                  className="mt-0.5"
                />
                <span>
                  <span className="font-semibold">Validation UPC</span>
                  <br />
                  <span className="text-xs text-neutral-500">
                    Généralement désactivée : les codes UPC n'apparaissent pas dans les lithos.
                  </span>
                </span>
              </label>
            </div>
          )}

          {step === 4 && (
            <div className="flex flex-col gap-3">
              {errors.length > 0 ? (
                <div className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">
                  <div className="font-semibold">Définition incomplète :</div>
                  <ul className="list-inside list-disc text-xs">
                    {errors.map((e) => (
                      <li key={e}>{e}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="rounded-lg border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-800">
                  ✅ Définition valide — prête à être enregistrée.
                </div>
              )}
              <pre className="max-h-64 overflow-auto rounded-lg bg-neutral-900 p-3 text-xs text-neutral-100">
                {JSON.stringify(definition, null, 2)}
              </pre>
              <p className="text-xs text-neutral-500">
                Ce JSON est le format d'échange des marques : exportable, importable sur un autre poste,
                et générable par le Compagnon GPT (voir Paramètres → Aide).
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-neutral-200 px-5 py-3">
          <button
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="rounded border border-neutral-300 px-3 py-1.5 text-sm disabled:opacity-40"
          >
            ← Précédent
          </button>
          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={!stepValid}
              className="rounded bg-neutral-900 px-4 py-1.5 text-sm font-semibold text-white disabled:opacity-40"
            >
              Suivant →
            </button>
          ) : (
            <button
              onClick={save}
              disabled={errors.length > 0 || codeTaken}
              className="rounded bg-red-600 px-4 py-1.5 text-sm font-semibold text-white disabled:opacity-40"
            >
              💾 Enregistrer la marque
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

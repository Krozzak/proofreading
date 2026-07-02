// Paramètres → Marques: list built-in and custom brands, create/edit via the
// wizard, duplicate, delete, JSON import/export, Excel template download.
import { useRef, useState } from 'react'
import type { BrandDefinition } from '../core/brandConfigs'
import { getAllDefinitions, isBuiltinBrand } from '../core/brandConfigs'
import { deleteCustomBrand, exportBrandJson, parseBrandJson, saveCustomBrand } from '../lib/brandStore'
import { downloadTemplate } from '../lib/templateGenerator'
import { downloadBlob } from '../lib/excelIO'
import { useAppStore } from '../state/appStore'
import { BrandWizard } from './BrandWizard'
import { toast } from './toast'

export function BrandManager() {
  const brandsVersion = useAppStore((s) => s.brandsVersion)
  const bumpBrands = useAppStore((s) => s.bumpBrands)
  const currentBrand = useAppStore((s) => s.brandCode)
  const setBrand = useAppStore((s) => s.setBrand)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [editing, setEditing] = useState<BrandDefinition | null>(null)
  const importRef = useRef<HTMLInputElement>(null)

  void brandsVersion // subscribe: re-render on brand CRUD
  const definitions = getAllDefinitions()

  function onImportFile(file: File) {
    file
      .text()
      .then((text) => {
        const { definition, errors } = parseBrandJson(text)
        if (!definition) {
          toast(`JSON de marque invalide:\n${errors.join('\n')}`, 'error')
          return
        }
        if (isBuiltinBrand(definition.brand_code)) {
          toast(`Le code ${definition.brand_code} est réservé à une marque intégrée`, 'error')
          return
        }
        const result = saveCustomBrand({ ...definition, created_by: 'import' })
        if (result.ok) {
          bumpBrands()
          toast(`✅ Marque ${definition.brand_code} importée`, 'success')
        } else {
          toast(result.error ?? 'Import impossible', 'error')
        }
      })
      .catch((e) => toast(`Lecture impossible: ${e instanceof Error ? e.message : e}`, 'error'))
  }

  function duplicate(def: BrandDefinition) {
    setEditing({
      ...def,
      brand_code: `${def.brand_code}_COPIE`.slice(0, 20),
      brand_name: `${def.brand_name} (copie)`,
      created_by: 'wizard',
    })
    setWizardOpen(true)
  }

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="font-bold">Marques</h2>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setEditing(null)
              setWizardOpen(true)
            }}
            className="rounded bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-500"
          >
            + Nouvelle marque
          </button>
          <button
            onClick={() => importRef.current?.click()}
            className="rounded border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-100"
          >
            📂 Importer JSON
          </button>
        </div>
      </div>
      <p className="mb-3 text-xs text-neutral-500">
        Les marques sont des définitions JSON : créez-en via le wizard (ou le Compagnon GPT),
        exportez-les pour les partager, importez celles de vos collègues. Chaque marque a son
        template Excel téléchargeable.
      </p>

      <div className="flex flex-col gap-2">
        {definitions.map((def) => {
          const builtin = isBuiltinBrand(def.brand_code)
          const active = def.brand_code === currentBrand
          return (
            <div
              key={def.brand_code}
              className={
                'flex flex-wrap items-center gap-2 rounded-lg border px-3 py-2 ' +
                (active ? 'border-red-300 bg-red-50' : 'border-neutral-200')
              }
            >
              <div className="min-w-40 flex-1">
                <span className="font-mono text-sm font-bold">{def.brand_code}</span>
                <span className="ml-2 text-sm text-neutral-600">{def.brand_name}</span>
                <span
                  className={
                    'ml-2 rounded-full px-2 py-0.5 text-[10px] font-semibold ' +
                    (builtin ? 'bg-neutral-200 text-neutral-600' : 'bg-violet-100 text-violet-700')
                  }
                >
                  {builtin ? 'intégrée' : def.created_by === 'ai' ? 'créée par IA' : 'personnalisée'}
                </span>
                {active && <span className="ml-2 text-[10px] font-semibold text-red-600">ACTIVE</span>}
              </div>
              <div className="flex flex-wrap gap-1.5 text-xs">
                {!active && (
                  <button
                    onClick={() => setBrand(def.brand_code)}
                    className="rounded border border-neutral-300 px-2 py-1 hover:bg-neutral-100"
                  >
                    Activer
                  </button>
                )}
                <button
                  onClick={() => void downloadTemplate(def).then(() => toast('Template téléchargé', 'success'))}
                  className="rounded border border-neutral-300 px-2 py-1 hover:bg-neutral-100"
                  title="Télécharger le template Excel du brief"
                >
                  📄 Template Excel
                </button>
                <button
                  onClick={() =>
                    downloadBlob(exportBrandJson(def), `brand_${def.brand_code}.json`, 'application/json')
                  }
                  className="rounded border border-neutral-300 px-2 py-1 hover:bg-neutral-100"
                >
                  ⬇ JSON
                </button>
                <button
                  onClick={() => duplicate(def)}
                  className="rounded border border-neutral-300 px-2 py-1 hover:bg-neutral-100"
                  title="Créer une nouvelle marque à partir de celle-ci"
                >
                  ⧉ Dupliquer
                </button>
                {!builtin && (
                  <>
                    <button
                      onClick={() => {
                        setEditing(def)
                        setWizardOpen(true)
                      }}
                      className="rounded border border-neutral-300 px-2 py-1 hover:bg-neutral-100"
                    >
                      ✏️ Modifier
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Supprimer la marque ${def.brand_code} ?`)) {
                          deleteCustomBrand(def.brand_code)
                          bumpBrands()
                          toast(`Marque ${def.brand_code} supprimée`, 'info')
                        }
                      }}
                      disabled={active}
                      className="rounded border border-red-300 px-2 py-1 text-red-700 hover:bg-red-50 disabled:opacity-40"
                      title={active ? "Impossible de supprimer la marque active" : 'Supprimer'}
                    >
                      🗑
                    </button>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <input
        ref={importRef}
        type="file"
        accept=".json"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onImportFile(f)
          e.target.value = ''
        }}
      />

      <BrandWizard
        open={wizardOpen}
        initial={editing}
        onClose={() => setWizardOpen(false)}
        onSaved={() => bumpBrands()}
      />
    </section>
  )
}

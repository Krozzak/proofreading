// AI analysis panel in the validation view: on-demand multimodal check of the
// current litho (brief rows judged on the page images + free-form question).
import { useState } from 'react'
import type { LithoRecord } from '../core/types'
import { safeStr } from '../core/textSafe'
import { isAiConfigured, validateWithAi } from '../lib/ai'
import { useAppStore, type PdfFileEntry } from '../state/appStore'
import { toast } from './toast'

interface Props {
  entry: PdfFileEntry
  excelData: LithoRecord[]
}

export function AiPanel({ entry, excelData }: Props) {
  const brandConfig = useAppStore((s) => s.brandConfig)
  const checkDigits = useAppStore((s) => s.checkDigits)
  const outcome = useAppStore((s) => s.aiResults[entry.lithoCode])
  const setAiResult = useAppStore((s) => s.setAiResult)
  const setView = useAppStore((s) => s.setView)
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [expanded, setExpanded] = useState(entry.needsManualReview)

  const configured = isAiConfigured()

  async function run() {
    if (!excelData.length) {
      toast('Aucune donnée Excel pour cette litho', 'error')
      return
    }
    setBusy(true)
    try {
      const result = await validateWithAi({
        pdfData: await entry.file.arrayBuffer(),
        pageCount: entry.pageCount,
        excelData,
        brandDescription: brandConfig.getValidationDescription(),
        checkDigits: checkDigits && brandConfig.requiresDigitsValidation(),
        question: question.trim() || undefined,
      })
      setAiResult(entry.lithoCode, result)
      toast(`🤖 Analyse IA terminée (confiance ${result.confidence}%)`, 'success')
    } catch (e) {
      toast(`Analyse IA échouée: ${e instanceof Error ? e.message : e}`, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="rounded-xl border border-violet-200 bg-violet-50/50 p-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between text-sm font-semibold text-violet-900"
      >
        <span>
          🤖 Analyse IA multimodale
          {entry.needsManualReview && (
            <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-800">
              recommandée — texte non extractible
            </span>
          )}
        </span>
        <span>{expanded ? '▾' : '▸'}</span>
      </button>

      {expanded && (
        <div className="mt-2 flex flex-col gap-2">
          {!configured ? (
            <p className="text-xs text-violet-800">
              L'IA lit directement l'image de la litho (fonctionne même quand le texte n'est pas
              extractible) et peut faire des vérifications hors format.{' '}
              <button onClick={() => setView('settings')} className="font-semibold underline">
                Configurer l'API IA dans Paramètres →
              </button>
            </p>
          ) : (
            <>
              <div className="flex gap-2">
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Vérification supplémentaire (optionnel) — ex: « le logo Walmart est-il présent ? »"
                  className="flex-1 rounded border border-violet-200 bg-white px-2 py-1.5 text-xs"
                />
                <button
                  onClick={() => void run()}
                  disabled={busy}
                  className="rounded bg-violet-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                >
                  {busy ? 'Analyse…' : outcome ? 'Relancer' : 'Analyser'}
                </button>
              </div>

              {outcome && (
                <div className="flex flex-col gap-2 rounded-lg border border-violet-200 bg-white p-2">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="font-semibold">
                      {outcome.rows.every((r) => r.overall) ? '✅ Tout est conforme' : '❌ Écarts détectés'}
                    </span>
                    <span className="rounded-full bg-violet-100 px-2 py-0.5 text-violet-700">
                      confiance {outcome.confidence}%
                    </span>
                    <span className="text-neutral-400">
                      {outcome.model} · {outcome.date.slice(0, 16).replace('T', ' ')}
                    </span>
                  </div>

                  <table className="w-full text-left text-xs">
                    <thead className="text-[10px] uppercase text-neutral-500">
                      <tr>
                        <th className="py-1">Ligne</th>
                        <th>Shade Name</th>
                        <th>Shade Number</th>
                        {checkDigits && <th>4 Digits</th>}
                        <th>Global</th>
                        <th>Notes IA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {outcome.rows.map((r) => (
                        <tr key={r.index} className={'border-t border-neutral-100 ' + (r.overall ? '' : 'bg-red-50')}>
                          <td className="py-1">
                            {safeStr(excelData[r.index]?.['SHADE NAME'])} {safeStr(excelData[r.index]?.['SHADE NUMBER'])}
                          </td>
                          <td>{r.shade_name ? '✓' : '✗'}</td>
                          <td>{r.shade_number ? '✓' : '✗'}</td>
                          {checkDigits && <td>{r.digits ? '✓' : '✗'}</td>}
                          <td>{r.overall ? '✅' : '❌'}</td>
                          <td className="max-w-56 truncate text-neutral-500" title={r.notes}>
                            {r.notes}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {outcome.custom_check_answer && (
                    <div className="rounded bg-violet-50 p-2 text-xs">
                      <span className="font-semibold">Vérification demandée :</span>{' '}
                      {outcome.custom_check_answer}
                    </div>
                  )}
                  {outcome.global_notes && (
                    <div className="text-xs text-neutral-500">{outcome.global_notes}</div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

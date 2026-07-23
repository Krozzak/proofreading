// Per-row validation results table (green/red rows, FRAME/SPACE_SAVER neutral).
import type { LithoRecord } from '../core/types'
import type { LegacyEntryResult } from '../core/validator'
import { safeStr } from '../core/textSafe'
import { useAppStore } from '../state/appStore'

interface Props {
  excelData: LithoRecord[]
  results: LegacyEntryResult[]
  /** When set, cell values become clickable to look them up in the extracted text. */
  onInspectValue?: (value: string) => void
}

function Check({ ok }: { ok: boolean }) {
  return ok ? <span className="text-emerald-600">✓</span> : <span className="font-bold text-red-600">✗</span>
}

function InspectableValue({
  value,
  onInspect,
}: {
  value: string
  onInspect?: (value: string) => void
}) {
  if (!onInspect || !value) return <>{value}</>
  return (
    <button
      onClick={() => onInspect(value)}
      className="cursor-pointer underline decoration-dotted decoration-neutral-400 underline-offset-2 hover:decoration-solid hover:decoration-neutral-700"
      title="Chercher cette valeur dans le texte extrait du PDF"
    >
      {value}
    </button>
  )
}

export function ResultsTable({ excelData, results, onInspectValue }: Props) {
  const checkDigits = useAppStore((s) => s.checkDigits)
  const requiresDigits = useAppStore((s) => s.brandConfig.requiresDigitsValidation())
  const showDigits = checkDigits && requiresDigits

  const count = Math.min(excelData.length, results.length)
  const isMixed = results.some((r) => r.is_mixed)
  const hasSpaceSaver = results.some((r) => r.is_space_saver)

  return (
    <div className="flex flex-col gap-2">
      {(isMixed || hasSpaceSaver) && (
        <div className="flex gap-2">
          {isMixed && (
            <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
              MIXED FACINGS
            </span>
          )}
          {hasSpaceSaver && (
            <span className="rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-semibold text-sky-800">
              SPACE SAVER
            </span>
          )}
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-neutral-100 text-xs uppercase text-neutral-600">
            <tr>
              <th className="px-3 py-2">UPC</th>
              <th className="px-3 py-2">Description produit</th>
              <th className="px-3 py-2">Shade Name</th>
              <th className="px-3 py-2">Shade Number</th>
              {showDigits && <th className="px-3 py-2">4 Digits</th>}
              <th className="px-3 py-2">Facing</th>
              <th className="px-3 py-2">Global</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: count }, (_, i) => {
              const row = excelData[i]
              const res = results[i]
              const neutral = res.is_frame || res.is_space_saver
              const rowClass = neutral
                ? 'bg-neutral-50 text-neutral-400'
                : res.overall
                  ? 'bg-emerald-50'
                  : 'bg-red-50'
              return (
                <tr key={i} className={`border-t border-neutral-200 ${rowClass}`}>
                  <td className="px-3 py-1.5 font-mono text-xs">{safeStr(row['UPC'])}</td>
                  <td className="max-w-56 truncate px-3 py-1.5" title={safeStr(row['PRODUCT DESCRIPTION'])}>
                    {safeStr(row['PRODUCT DESCRIPTION'])}
                  </td>
                  <td className="px-3 py-1.5">
                    <InspectableValue value={safeStr(row['SHADE NAME'])} onInspect={onInspectValue} />{' '}
                    {!neutral && <Check ok={res.shade_name} />}
                  </td>
                  <td className="px-3 py-1.5">
                    <InspectableValue value={safeStr(row['SHADE NUMBER'])} onInspect={onInspectValue} />{' '}
                    {!neutral && <Check ok={res.shade_number} />}
                  </td>
                  {showDigits && (
                    <td className="px-3 py-1.5">
                      <InspectableValue value={safeStr(row['4 DIGITS'])} onInspect={onInspectValue} />{' '}
                      {!neutral && <Check ok={res.digits} />}
                    </td>
                  )}
                  <td className="px-3 py-1.5">{safeStr(res.facing)}</td>
                  <td className="px-3 py-1.5">
                    {neutral ? (
                      <span className="text-xs">{res.is_frame ? 'FRAME' : 'SPACE SAVER'}</span>
                    ) : res.overall ? (
                      <span className="font-semibold text-emerald-700">✅ OK</span>
                    ) : (
                      <span className="font-semibold text-red-700">❌ Erreur</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Extracted-text inspector: shows the raw text the validation engine works
// on, with a search that reproduces the engine's matching exactly (uppercase,
// exact substring). When the exact search fails but the value exists once
// whitespace is ignored, the panel explains the mismatch — the most common
// cause of "false" errors (line breaks inside SHADE NAME, WATERPROOF…).
import { useMemo } from 'react'

interface Props {
  text: string
  pageCount: number
  needsManualReview: boolean
  query: string
  onQueryChange(query: string): void
}

interface Segment {
  str: string
  highlight: 'exact' | 'loose' | null
}

/** All [start, end) occurrences of the uppercased query in the uppercased text. */
function findExactRanges(upperText: string, upperQuery: string): [number, number][] {
  const ranges: [number, number][] = []
  let from = 0
  for (;;) {
    const idx = upperText.indexOf(upperQuery, from)
    if (idx < 0) break
    ranges.push([idx, idx + upperQuery.length])
    from = idx + Math.max(1, upperQuery.length)
  }
  return ranges
}

/**
 * Whitespace-insensitive fallback: squash all whitespace out of both sides,
 * search, and map the match back to a range in the original text.
 */
function findLooseRange(upperText: string, upperQuery: string): [number, number] | null {
  const squashedQuery = upperQuery.replace(/\s+/g, '')
  if (!squashedQuery) return null
  const map: number[] = []
  let squashed = ''
  for (let i = 0; i < upperText.length; i++) {
    if (!/\s/.test(upperText[i])) {
      squashed += upperText[i]
      map.push(i)
    }
  }
  const idx = squashed.indexOf(squashedQuery)
  if (idx < 0) return null
  return [map[idx], map[idx + squashedQuery.length - 1] + 1]
}

function toSegments(text: string, ranges: [number, number][], kind: 'exact' | 'loose'): Segment[] {
  const segments: Segment[] = []
  let cursor = 0
  for (const [start, end] of ranges) {
    if (start > cursor) segments.push({ str: text.slice(cursor, start), highlight: null })
    segments.push({ str: text.slice(start, end), highlight: kind })
    cursor = end
  }
  if (cursor < text.length) segments.push({ str: text.slice(cursor), highlight: null })
  return segments
}

export function ExtractedTextPanel({ text, pageCount, needsManualReview, query, onQueryChange }: Props) {
  const trimmedQuery = query.trim()

  const { segments, exactCount, looseFound } = useMemo(() => {
    if (!trimmedQuery) {
      return { segments: [{ str: text, highlight: null }] as Segment[], exactCount: 0, looseFound: false }
    }
    const upperText = text.toUpperCase()
    const upperQuery = trimmedQuery.toUpperCase()
    const exact = findExactRanges(upperText, upperQuery)
    if (exact.length) {
      return { segments: toSegments(text, exact, 'exact'), exactCount: exact.length, looseFound: false }
    }
    const loose = findLooseRange(upperText, upperQuery)
    return {
      segments: loose ? toSegments(text, [loose], 'loose') : ([{ str: text, highlight: null }] as Segment[]),
      exactCount: 0,
      looseFound: loose !== null,
    }
  }, [text, trimmedQuery])

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Chercher une valeur (ex : un shade name en erreur)…"
          className="min-w-48 flex-1 rounded border border-neutral-300 px-2 py-1.5 text-sm"
        />
        {trimmedQuery && (
          <span
            className={
              'rounded-full px-2.5 py-0.5 text-xs font-semibold ' +
              (exactCount > 0
                ? 'bg-emerald-100 text-emerald-800'
                : looseFound
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-red-100 text-red-800')
            }
          >
            {exactCount > 0
              ? `✓ ${exactCount} occurrence${exactCount > 1 ? 's' : ''}`
              : looseFound
                ? '⚠️ Trouvé, mais coupé par des espaces'
                : '✗ Introuvable dans le texte extrait'}
          </span>
        )}
      </div>

      {trimmedQuery && exactCount === 0 && looseFound && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
          La valeur existe dans le texte, mais avec des espaces ou retours à la ligne
          différents (surlignée en orange ci-dessous). Le moteur de validation cherche la
          chaîne exacte, c'est pourquoi il signale une erreur — vérifiez visuellement sur
          le PDF si la mise en page est correcte.
        </p>
      )}
      {trimmedQuery && exactCount === 0 && !looseFound && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
          Cette valeur n'apparaît nulle part dans le texte extrait du PDF, même en
          ignorant les espaces. Soit elle manque réellement sur le visuel, soit le texte
          est vectorisé/en image et n'est pas extractible (voir le badge « Revue manuelle »).
        </p>
      )}

      <div className="flex items-center gap-3 text-[11px] text-neutral-400">
        <span>
          {text.length.toLocaleString('fr-FR')} caractères extraits · {pageCount} page
          {pageCount > 1 ? 's' : ''}
        </span>
        {needsManualReview && (
          <span className="font-semibold text-amber-600">
            ⚠️ Très peu de texte extractible — PDF probablement scanné ou vectorisé
          </span>
        )}
        <span className="ml-auto">Recherche identique au moteur : majuscules, sous-chaîne exacte</span>
      </div>

      <pre className="min-h-0 flex-1 overflow-auto whitespace-pre-wrap rounded-lg border border-neutral-200 bg-neutral-50 p-3 font-mono text-xs leading-relaxed text-neutral-800">
        {text.trim().length === 0 ? (
          <span className="text-neutral-400">Aucun texte extractible dans ce PDF.</span>
        ) : (
          segments.map((seg, i) =>
            seg.highlight ? (
              <mark
                key={i}
                className={
                  seg.highlight === 'exact'
                    ? 'rounded bg-emerald-200 px-0.5 font-bold'
                    : 'rounded bg-amber-200 px-0.5 font-bold'
                }
              >
                {seg.str}
              </mark>
            ) : (
              seg.str
            ),
          )
        )}
      </pre>
    </div>
  )
}

// Litho layout computation for the visual overlay — the web counterpart of
// the desktop LayoutDebugOverlay: shows what the app understood of the litho
// (facing columns, tiers, slot occupancy). Display-only: it reads the brief
// rows and validation results but never feeds back into the engines, so the
// Python-parity core stays untouched.
import type { LithoRecord } from '../core/types'
import type { CubbyResult, LegacyEntryResult } from '../core/validator'
import { safeStr } from '../core/textSafe'

export type SlotState = 'ok' | 'error' | 'frame' | 'space_saver' | 'implicit_gap' | 'empty'

export interface LayoutSlot {
  label: string
  sublabel?: string
  state: SlotState
  title: string
}

export interface LayoutTier {
  name: string
  facing: number
  slots: LayoutSlot[]
}

export interface LithoLayout {
  /** Display order: top row first (highest physical tier on top). */
  tiers: LayoutTier[]
  mixedFacings: boolean
  /** Slots implied by the facing count but not declared in the brief. */
  implicitGaps: number
  source: 'brief' | 'cubby'
}

const INT_RE = /^[+-]?\d+$/

function isSpaceSaverRow(row: LithoRecord): boolean {
  return ['UPC', 'PRODUCT DESCRIPTION', 'SHADE NAME'].some(
    (field) => safeStr(row[field]) === 'SPACE_SAVER',
  )
}

function slotFromRow(row: LithoRecord, result: LegacyEntryResult | undefined): LayoutSlot {
  const facingValue = safeStr(row['PRODUCT FACING SL'])
  const shadeNumber = safeStr(row['SHADE NUMBER'])
  const shadeName = safeStr(row['SHADE NAME'])
  const upc = safeStr(row['UPC'])
  const title = [upc, shadeNumber, shadeName].filter(Boolean).join(' — ')

  if (facingValue === 'FRAME' || upc.toUpperCase() === 'FRAME') {
    return { label: 'FRAME', state: 'frame', title: title || 'FRAME' }
  }
  if (isSpaceSaverRow(row)) {
    return { label: 'SPACE SAVER', state: 'space_saver', title: 'SPACE SAVER déclaré au brief' }
  }
  const label = shadeNumber || shadeName.slice(0, 12) || upc.slice(-5) || '?'
  const state: SlotState = result && !result.overall ? 'error' : 'ok'
  return {
    label,
    sublabel: shadeNumber ? shadeName.slice(0, 16) : undefined,
    state,
    title:
      (title || 'Produit') +
      (state === 'error' ? ' — ✗ erreur de validation' : ' — ✓ validé'),
  }
}

/**
 * Builds the layout from the brief rows + per-row results. Rows are grouped
 * by the optional TIER column (single tier when absent); each tier's column
 * count comes from the facing values. Fewer declared rows than the facing →
 * trailing "SPACE SAVER ?" gap slots (undeclared empty positions).
 */
export function computeLithoLayout(
  excelData: LithoRecord[],
  results: LegacyEntryResult[],
): LithoLayout | null {
  if (!excelData.length) return null

  // Group rows (with their result) by TIER, preserving row order
  const groups = new Map<string, { row: LithoRecord; result: LegacyEntryResult | undefined }[]>()
  excelData.forEach((row, i) => {
    const tier = safeStr(row['TIER'])
    if (!groups.has(tier)) groups.set(tier, [])
    groups.get(tier)!.push({ row, result: results[i] })
  })

  // Mixed = more than one distinct integer facing across the whole litho
  // (same rule as the validator's MIXED badge)
  const allFacings = new Set<number>()
  for (const row of excelData) {
    const f = safeStr(row['PRODUCT FACING SL'])
    if (INT_RE.test(f)) allFacings.add(parseInt(f, 10))
  }
  const mixedFacings = allFacings.size > 1

  let implicitGaps = 0
  const tiers: LayoutTier[] = []
  for (const [tierValue, entries] of groups) {
    const facings = entries
      .map(({ row }) => safeStr(row['PRODUCT FACING SL']))
      .filter((f) => INT_RE.test(f))
      .map((f) => parseInt(f, 10))
    const facing = facings.length ? Math.max(...facings) : entries.length
    const slots = entries.map(({ row, result }) => slotFromRow(row, result))
    for (let i = slots.length; i < facing; i++) {
      implicitGaps++
      slots.push({
        label: 'SPACE SAVER ?',
        state: 'implicit_gap',
        title: `Facing ${facing} mais seulement ${entries.length} ligne(s) au brief — emplacement probablement SPACE SAVER non déclaré`,
      })
    }
    tiers.push({
      name: tierValue ? `TIER ${tierValue}` : groups.size > 1 ? 'TIER ?' : '',
      facing: Math.max(facing, slots.length),
      slots,
    })
  }

  // Top row = highest tier (like the desktop/CUBBY viewers); numeric when possible
  tiers.sort((a, b) => {
    const na = parseInt(a.name.replace(/\D+/g, ''), 10)
    const nb = parseInt(b.name.replace(/\D+/g, ''), 10)
    if (Number.isNaN(na) || Number.isNaN(nb)) return 0
    return nb - na
  })

  return { tiers, mixedFacings, implicitGaps, source: 'brief' }
}

/** Layout from a CUBBY result — matrix_data rows are already top-tier first. */
export function cubbyLayout(result: CubbyResult): LithoLayout {
  const [faces, tierCount] = result.cubby_dimensions
  const tiers: LayoutTier[] = result.matrix_data.map((tierRow, i) => ({
    name: `TIER ${tierCount - i}`,
    facing: faces,
    slots: tierRow.map((item): LayoutSlot => {
      if (item.upc === 'EMPTY') return { label: '—', state: 'empty', title: 'Emplacement vide' }
      if (item.is_frame) return { label: 'FRAME', state: 'frame', title: item.upc }
      return {
        label: item.shade_number || item.shade_name.slice(0, 12) || item.upc.slice(-5),
        sublabel: item.shade_number ? item.shade_name.slice(0, 16) : undefined,
        state: 'ok',
        title: [item.upc, item.shade_number, item.shade_name].filter(Boolean).join(' — '),
      }
    }),
  }))
  return { tiers, mixedFacings: false, implicitGaps: 0, source: 'cubby' }
}

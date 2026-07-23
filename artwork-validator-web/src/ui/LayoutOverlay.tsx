// Transparent overlay drawn over the litho canvas — web port of the desktop
// LayoutDebugOverlay: facing columns (dashed vertical lines + one cell per
// slot), tier bands, and the standard top zones (SHADE NUMBER 0-15%,
// SHADE NAME + 4 DIGITS 15-30%) when the litho has a single tier.
import type { LayoutSlot, LithoLayout } from '../lib/lithoLayout'

const CHIP_STYLES: Record<LayoutSlot['state'], string> = {
  ok: 'bg-emerald-600/90 text-white',
  error: 'bg-red-600/95 text-white',
  frame: 'bg-neutral-600/90 text-white',
  space_saver: 'bg-sky-600/90 text-white',
  implicit_gap: 'bg-amber-500/95 text-white',
  empty: 'bg-white/70 text-neutral-400',
}

const CELL_STYLES: Record<LayoutSlot['state'], string> = {
  ok: '',
  error: 'bg-red-500/10',
  frame: 'bg-neutral-500/10',
  space_saver: 'bg-sky-500/10',
  implicit_gap: 'bg-amber-400/25',
  empty: '',
}

export function LayoutOverlay({ layout }: { layout: LithoLayout }) {
  const showZones = layout.tiers.length === 1 && layout.source === 'brief'

  return (
    <div className="pointer-events-none absolute inset-0 z-10 overflow-hidden rounded">
      {/* Standard vertical zones (single-tier lithos), like the desktop debug overlay */}
      {showZones && (
        <>
          <div className="absolute inset-x-0 top-0 h-[15%] border-b-2 border-dashed border-emerald-600/50 bg-emerald-500/5">
            <span className="absolute bottom-0.5 right-1 rounded bg-white/80 px-1 text-[9px] font-bold text-emerald-700">
              SHADE NUMBER 0–15%
            </span>
          </div>
          <div className="absolute inset-x-0 top-[15%] h-[15%] border-b-2 border-dashed border-sky-600/50 bg-sky-500/5">
            <span className="absolute bottom-0.5 right-1 rounded bg-white/80 px-1 text-[9px] font-bold text-sky-700">
              SHADE NAME + 4 DIGITS 15–30%
            </span>
          </div>
        </>
      )}

      {/* Tier bands, each split into its facing columns */}
      <div className="absolute inset-0 flex flex-col">
        {layout.tiers.map((tier, ti) => (
          <div
            key={ti}
            className="relative flex min-h-0 flex-1 border-b-2 border-dashed border-violet-500/60 last:border-b-0"
          >
            {tier.name && (
              <span className="absolute left-1 top-1 z-20 rounded bg-violet-600/90 px-1.5 py-0.5 text-[10px] font-bold text-white">
                {tier.name}
              </span>
            )}
            {tier.slots.map((slot, si) => (
              <div
                key={si}
                className={
                  'flex min-w-0 flex-1 flex-col items-center border-l-2 border-dashed border-blue-500/50 pt-1 first:border-l-0 ' +
                  CELL_STYLES[slot.state]
                }
                title={slot.title}
              >
                <span
                  className={
                    'pointer-events-auto max-w-[95%] truncate rounded px-1.5 py-0.5 text-[10px] font-bold shadow ' +
                    CHIP_STYLES[slot.state]
                  }
                  title={slot.title}
                >
                  {slot.label}
                </span>
                {slot.sublabel && (
                  <span className="mt-0.5 max-w-[95%] truncate rounded bg-white/80 px-1 text-[9px] text-neutral-600">
                    {slot.sublabel}
                  </span>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>

      {layout.mixedFacings && (
        <span className="absolute bottom-1 left-1 z-20 rounded bg-amber-500/95 px-2 py-0.5 text-[10px] font-bold text-white shadow">
          ⚠️ FACINGS MIXTES
        </span>
      )}
    </div>
  )
}

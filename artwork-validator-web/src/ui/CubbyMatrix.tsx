// CUBBY matrix view: faces × tiers grid, displayed with tiers inverted
// (top row = highest physical tier), like the desktop viewer.
import type { CubbyResult } from '../core/validator'

export function CubbyMatrix({ result }: { result: CubbyResult }) {
  const [faces, tiers] = result.cubby_dimensions
  const matrix = result.matrix_data

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="rounded-full bg-violet-100 px-2.5 py-0.5 text-xs font-semibold text-violet-800">
          CUBBY {faces}F × {tiers}T
        </span>
        <span className="truncate text-xs text-neutral-500" title={result.description}>
          {result.description}
        </span>
      </div>
      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-center text-xs">
          <tbody>
            {matrix.map((tierRow, tierIndex) => (
              <tr key={tierIndex} className="border-t border-neutral-200 first:border-t-0">
                <td className="bg-neutral-100 px-2 py-1 font-semibold text-neutral-600">
                  TIER {tiers - tierIndex}
                </td>
                {tierRow.map((item, pos) => (
                  <td
                    key={pos}
                    className={
                      'border-l border-neutral-200 px-2 py-1.5 align-top ' +
                      (item.upc === 'EMPTY'
                        ? 'bg-neutral-50 text-neutral-300'
                        : item.is_frame
                          ? 'bg-amber-50'
                          : 'bg-white')
                    }
                  >
                    {item.upc === 'EMPTY' ? (
                      '—'
                    ) : (
                      <div className="flex flex-col gap-0.5">
                        <span className="font-mono text-[10px] text-neutral-500">{item.upc}</span>
                        <span className="font-semibold">{item.shade_number}</span>
                        <span className="truncate text-[10px]" title={item.shade_name}>
                          {item.shade_name}
                        </span>
                      </div>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

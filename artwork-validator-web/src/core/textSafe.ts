// Port of the `_safe_str` helpers scattered through the Python core.

/**
 * Converts any cell value to a trimmed string the way `_safe_str` does:
 * integral floats lose their decimal part (110.0 → '110'), null/NaN → ''.
 * (Python returns 'nan' for NaN, but records never contain NaN by then —
 * getDataForLitho already replaced NaN with ''.)
 */
export function safeStr(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'number') {
    if (Number.isNaN(value)) return ''
    return String(value)
  }
  return String(value).trim()
}

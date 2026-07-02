// Port of utils/session_manager.py, de-Qt'ed: localStorage autosave replaces
// the JSON session files; export/import stays compatible with desktop sessions.
import type { LithoValidation, SessionData, ValidationStatus } from '../core/types'

export const SESSION_STORAGE_KEY = 'avw:session:current'
export const SESSION_VERSION = '2.0-web'

export function defaultSession(): SessionData {
  return {
    session_name: '',
    pdf_folder: '',
    excel_file: '',
    last_litho_index: 0,
    validations: {},
    created_date: '',
    last_updated: '',
    session_type: '',
    check_digits: false,
    validation_method: 'legacy',
    brand_code: 'MNY',
    session_version: SESSION_VERSION,
  }
}

/**
 * Port of _validate_and_migrate_session. Unlike the desktop version (which
 * drops brand_code — a known bug), the web schema keeps brand_code and
 * validation_method so a re-imported session restores its full state.
 */
export function validateAndMigrateSession(sessionData: Record<string, unknown>): SessionData {
  const str = (key: string, fallback: string): string =>
    typeof sessionData[key] === 'string' ? (sessionData[key] as string) : fallback
  const nowIso = new Date().toISOString()

  const validationsRaw = sessionData['validations']
  const validations: Record<string, LithoValidation> = {}
  if (validationsRaw && typeof validationsRaw === 'object') {
    for (const [code, value] of Object.entries(validationsRaw as Record<string, unknown>)) {
      if (value && typeof value === 'object') {
        const v = value as Record<string, unknown>
        validations[code] = {
          status: (v['status'] as ValidationStatus) ?? 'pending',
          date: typeof v['date'] === 'string' ? v['date'] : '',
          comment: typeof v['comment'] === 'string' ? v['comment'] : '',
        }
      }
    }
  }

  const method = sessionData['validation_method']
  const customBrand =
    typeof sessionData['custom_brand'] === 'object' && sessionData['custom_brand'] !== null
      ? sessionData['custom_brand']
      : undefined
  return {
    ...(customBrand !== undefined ? { custom_brand: customBrand } : {}),
    session_name: str('session_name', 'Session sans nom'),
    pdf_folder: str('pdf_folder', ''),
    excel_file: str('excel_file', ''),
    last_litho_index:
      typeof sessionData['last_litho_index'] === 'number'
        ? (sessionData['last_litho_index'] as number)
        : 0,
    validations,
    created_date: str('created_date', nowIso),
    last_updated: str('last_updated', nowIso),
    session_type: str('session_type', ''),
    check_digits: Boolean(sessionData['check_digits']),
    validation_method: method === 'enhanced' ? 'enhanced' : 'legacy',
    brand_code: str('brand_code', 'MNY'),
    session_version: str('session_version', '1.0'),
  }
}

export function updateLithoStatus(
  session: SessionData,
  lithoCode: string,
  status: ValidationStatus,
  comment = '',
): SessionData {
  return {
    ...session,
    validations: {
      ...session.validations,
      [lithoCode]: { status, date: new Date().toISOString(), comment },
    },
    last_updated: new Date().toISOString(),
  }
}

export function getLithoStatus(session: SessionData, lithoCode: string): LithoValidation | null {
  return session.validations[lithoCode] ?? null
}

export function getRejectedLithos(session: SessionData): string[] {
  return Object.entries(session.validations)
    .filter(([, data]) => data.status === 'rejected')
    .map(([code]) => code)
}

export function getApprovedLithos(session: SessionData): string[] {
  return Object.entries(session.validations)
    .filter(([, data]) => data.status === 'approved')
    .map(([code]) => code)
}

/** Port of the save_session_as filename sanitizer. */
export function sanitizeSessionFilename(sessionName: string): string {
  const clean = [...sessionName]
    .filter((c) => /[\p{L}\p{N}]/u.test(c) || c === ' ' || c === '-' || c === '_')
    .join('')
    .trim()
  return clean || 'session_sans_nom'
}

export function saveToLocalStorage(session: SessionData): boolean {
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
    return true
  } catch {
    // QuotaExceededError or storage disabled — the UI offers JSON export instead
    return false
  }
}

export function loadFromLocalStorage(): SessionData | null {
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY)
    if (!raw) return null
    return validateAndMigrateSession(JSON.parse(raw) as Record<string, unknown>)
  } catch {
    return null
  }
}

export function clearLocalStorage(): void {
  try {
    localStorage.removeItem(SESSION_STORAGE_KEY)
  } catch {
    // ignore
  }
}

/** Serializes the session the way the desktop app writes its .json files. */
export function exportSessionJson(session: SessionData): string {
  return JSON.stringify({ ...session, last_updated: new Date().toISOString() }, null, 4)
}

export function importSessionJson(json: string): SessionData {
  return validateAndMigrateSession(JSON.parse(json) as Record<string, unknown>)
}

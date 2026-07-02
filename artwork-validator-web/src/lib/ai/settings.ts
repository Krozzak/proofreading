// AI provider settings — stored in the browser only (localStorage). The app
// is fully client-side: the key is sent to the configured API and nowhere else.
export type AiProvider = 'anthropic' | 'openai'

export interface AiSettings {
  provider: AiProvider
  baseUrl: string
  apiKey: string
  model: string
}

export const AI_SETTINGS_KEY = 'avw:ai:settings'

export const DEFAULT_BASE_URLS: Record<AiProvider, string> = {
  anthropic: 'https://api.anthropic.com',
  openai: 'https://api.openai.com/v1',
}

export const DEFAULT_MODELS: Record<AiProvider, string> = {
  anthropic: 'claude-sonnet-5',
  openai: 'gpt-4o',
}

export function defaultAiSettings(): AiSettings {
  return {
    provider: 'anthropic',
    baseUrl: DEFAULT_BASE_URLS.anthropic,
    apiKey: '',
    model: DEFAULT_MODELS.anthropic,
  }
}

export function loadAiSettings(): AiSettings {
  try {
    const raw = localStorage.getItem(AI_SETTINGS_KEY)
    if (!raw) return defaultAiSettings()
    const parsed = JSON.parse(raw) as Partial<AiSettings>
    const provider: AiProvider = parsed.provider === 'openai' ? 'openai' : 'anthropic'
    return {
      provider,
      baseUrl: typeof parsed.baseUrl === 'string' && parsed.baseUrl ? parsed.baseUrl : DEFAULT_BASE_URLS[provider],
      apiKey: typeof parsed.apiKey === 'string' ? parsed.apiKey : '',
      model: typeof parsed.model === 'string' && parsed.model ? parsed.model : DEFAULT_MODELS[provider],
    }
  } catch {
    return defaultAiSettings()
  }
}

export function saveAiSettings(settings: AiSettings): void {
  try {
    localStorage.setItem(AI_SETTINGS_KEY, JSON.stringify(settings))
  } catch {
    // storage disabled — settings stay in memory for the session
  }
}

export function isAiConfigured(settings: AiSettings = loadAiSettings()): boolean {
  return Boolean(settings.apiKey && settings.baseUrl && settings.model)
}

// Provider-agnostic multimodal chat client. Two wire formats are supported:
// - Anthropic Messages API (works from the browser with the
//   `anthropic-dangerous-direct-browser-access` header)
// - OpenAI-compatible chat/completions (OpenAI, Azure via full baseUrl, etc.)
import type { AiSettings } from './settings'
import { loadAiSettings } from './settings'

export interface UserContentPart {
  text?: string
  /** JPEG image, base64 without the data: prefix. */
  imageJpegBase64?: string
}

export interface ChatRequest {
  system: string
  parts: UserContentPart[]
  maxTokens?: number
  settings?: AiSettings
}

async function chatAnthropic(req: ChatRequest, settings: AiSettings): Promise<string> {
  const content: unknown[] = []
  for (const part of req.parts) {
    if (part.imageJpegBase64) {
      content.push({
        type: 'image',
        source: { type: 'base64', media_type: 'image/jpeg', data: part.imageJpegBase64 },
      })
    }
    if (part.text) {
      content.push({ type: 'text', text: part.text })
    }
  }

  const response = await fetch(`${settings.baseUrl.replace(/\/$/, '')}/v1/messages`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': settings.apiKey,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true',
    },
    body: JSON.stringify({
      model: settings.model,
      max_tokens: req.maxTokens ?? 4096,
      system: req.system,
      messages: [{ role: 'user', content }],
    }),
  })

  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new Error(`API ${response.status}: ${body.slice(0, 300)}`)
  }
  const json = (await response.json()) as { content?: { type: string; text?: string }[] }
  return (json.content ?? [])
    .filter((b) => b.type === 'text' && b.text)
    .map((b) => b.text)
    .join('\n')
}

async function chatOpenAi(req: ChatRequest, settings: AiSettings): Promise<string> {
  const content: unknown[] = []
  for (const part of req.parts) {
    if (part.imageJpegBase64) {
      content.push({
        type: 'image_url',
        image_url: { url: `data:image/jpeg;base64,${part.imageJpegBase64}` },
      })
    }
    if (part.text) {
      content.push({ type: 'text', text: part.text })
    }
  }

  const response = await fetch(`${settings.baseUrl.replace(/\/$/, '')}/chat/completions`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      authorization: `Bearer ${settings.apiKey}`,
    },
    body: JSON.stringify({
      model: settings.model,
      max_tokens: req.maxTokens ?? 4096,
      messages: [
        { role: 'system', content: req.system },
        { role: 'user', content },
      ],
    }),
  })

  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new Error(`API ${response.status}: ${body.slice(0, 300)}`)
  }
  const json = (await response.json()) as { choices?: { message?: { content?: string } }[] }
  return json.choices?.[0]?.message?.content ?? ''
}

/** Sends one multimodal turn and returns the assistant text. */
export async function chat(req: ChatRequest): Promise<string> {
  const settings = req.settings ?? loadAiSettings()
  if (!settings.apiKey) {
    throw new Error("Aucune clé API configurée (Paramètres → Intelligence artificielle)")
  }
  return settings.provider === 'openai' ? chatOpenAi(req, settings) : chatAnthropic(req, settings)
}

/**
 * Extracts a JSON object from a model reply (handles ```json fences and
 * surrounding prose).
 */
export function extractJson(text: string): unknown {
  const fenced = /```(?:json)?\s*([\s\S]*?)```/.exec(text)
  const candidate = fenced ? fenced[1] : text
  const start = candidate.indexOf('{')
  const end = candidate.lastIndexOf('}')
  if (start === -1 || end === -1 || end <= start) {
    throw new Error('La réponse du modèle ne contient pas de JSON')
  }
  return JSON.parse(candidate.slice(start, end + 1))
}

/** Cheap connectivity check for the settings screen. */
export async function testConnection(settings: AiSettings): Promise<void> {
  await chat({
    system: 'Réponds exactement: OK',
    parts: [{ text: 'ping' }],
    maxTokens: 8,
    settings,
  })
}

import type { NextApiRequest, NextApiResponse } from 'next';

/**
 * /api/generate — Server-side proxy to GCP self-hosted LLMs.
 *
 * Tries GCP Ollama first, then GCP LlamaCPP.
 * Runs server-side so there are zero CORS issues and
 * the GCP IPs are never exposed to the browser.
 */

const GCP_OLLAMA_URL = process.env.GCP_OLLAMA_URL || '';
const GCP_LLAMACPP_URL = process.env.GCP_LLAMACPP_URL || '';
const BACKEND_URL =
  process.env.GOBLIN_BACKEND_URL ||
  process.env.NEXT_PUBLIC_FASTAPI_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  'https://goblin-backend.fly.dev';

const DEFAULT_SYSTEM_PROMPT =
  process.env.GOBLIN_SYSTEM_PROMPT ||
  "You are Goblin Assistant. Respond as the assistant only. Do not include role labels like 'User:' or 'Assistant:'. " +
    "Do not claim you performed real-world actions (sending emails/messages, payments, etc.). " +
    "If asked to send a message/email, say you cannot send it directly and offer to draft it, asking for the needed details. " +
    'Be concise unless the user asks for more detail.';

// Map of model → provider hint ('ollama' | 'llamacpp')
const OLLAMA_MODELS = new Set([
  'gemma:2b',
  'mistral:7b',
  'phi3:3.8b',
  'deepseek-coder:1.3b',
  'llama3.2:1b',
  'qwen2.5:3b',
]);

type ChatRole = 'system' | 'user' | 'assistant';
type ChatMessage = { role: ChatRole; content: string };

interface GenerateRequest {
  prompt?: string;
  messages?: ChatMessage[];
  model?: string;
  max_tokens?: number;
  temperature?: number;
}

interface GenerateResponse {
  content: string;
  model: string;
  provider: string;
  usage?: {
    input_tokens?: number;
    output_tokens?: number;
    total_tokens?: number;
  };
  finish_reason?: string;
}

function getLastUserPrompt(messages: ChatMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i]?.role === 'user') return messages[i]?.content || '';
  }
  return '';
}

function normalizeMessages(prompt?: string, messages?: ChatMessage[]): ChatMessage[] {
  const cleaned: ChatMessage[] = Array.isArray(messages)
    ? messages
        .filter(m => m && typeof m.role === 'string' && typeof m.content === 'string')
        .map(m => ({ role: m.role as ChatRole, content: String(m.content) }))
    : [];

  if (cleaned.length > 0) {
    if (!cleaned.some(m => m.role === 'system')) {
      cleaned.unshift({ role: 'system', content: DEFAULT_SYSTEM_PROMPT });
    }
    return cleaned;
  }

  if (prompt && typeof prompt === 'string') {
    return [
      { role: 'system', content: DEFAULT_SYSTEM_PROMPT },
      { role: 'user', content: prompt },
    ];
  }

  return [];
}

function defaultMaxTokens(userText: string): number {
  const n = (userText || '').trim().length;
  if (n <= 32) return 64;
  if (n <= 200) return 128;
  return 256;
}

function clampInt(value: unknown, min: number, max: number): number | undefined {
  const n = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(n)) return undefined;
  const i = Math.floor(n);
  return Math.max(min, Math.min(max, i));
}

function clampFloat(value: unknown, min: number, max: number): number | undefined {
  const n = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(n)) return undefined;
  return Math.max(min, Math.min(max, n));
}

/**
 * Try GCP Ollama (/api/chat preferred, fallback to /api/generate)
 */
async function tryOllama(params: {
  prompt: string;
  messages: ChatMessage[];
  model: string;
  max_tokens: number;
  temperature: number;
}): Promise<GenerateResponse | null> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    // Prefer /api/chat when we have structured messages.
    if (params.messages.length > 0) {
      const chatRes = await fetch(`${GCP_OLLAMA_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: params.model,
          messages: params.messages,
          stream: false,
          options: {
            temperature: params.temperature,
            num_predict: params.max_tokens,
          },
        }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (chatRes.ok) {
        const data = await chatRes.json();
        return {
          content: data?.message?.content || '',
          model: data?.model || params.model,
          provider: 'gcp_ollama',
          usage: {
            input_tokens: data?.prompt_eval_count || 0,
            output_tokens: data?.eval_count || 0,
            total_tokens: (data?.prompt_eval_count || 0) + (data?.eval_count || 0),
          },
          finish_reason: data?.done ? 'stop' : 'stop',
        };
      }
    } else {
      clearTimeout(timeout);
    }

    // Fallback: /api/generate prompt-only.
    const controller2 = new AbortController();
    const timeout2 = setTimeout(() => controller2.abort(), 15000);
    const genRes = await fetch(`${GCP_OLLAMA_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: params.model, prompt: params.prompt, stream: false }),
      signal: controller2.signal,
    });
    clearTimeout(timeout2);

    if (!genRes.ok) return null;

    const data = await genRes.json();
    return {
      content: data.response || '',
      model: data.model || params.model,
      provider: 'gcp_ollama',
      usage: {
        input_tokens: data.prompt_eval_count || 0,
        output_tokens: data.eval_count || 0,
        total_tokens: (data.prompt_eval_count || 0) + (data.eval_count || 0),
      },
      finish_reason: 'stop',
    };
  } catch {
    return null;
  }
}

/**
 * Try GCP LlamaCPP (/v1/chat/completions — OpenAI-compatible)
 */
async function tryLlamaCpp(params: {
  messages: ChatMessage[];
  max_tokens: number;
  temperature: number;
}): Promise<GenerateResponse | null> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    const res = await fetch(`${GCP_LLAMACPP_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: params.messages,
        max_tokens: params.max_tokens,
        temperature: params.temperature,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!res.ok) return null;

    const data = await res.json();
    const choice = data.choices?.[0];
    return {
      content: choice?.message?.content || '',
      model: data.model || 'llamacpp',
      provider: 'gcp_llamacpp',
      usage: {
        input_tokens: data.usage?.prompt_tokens || 0,
        output_tokens: data.usage?.completion_tokens || 0,
        total_tokens: data.usage?.total_tokens || 0,
      },
      finish_reason: choice?.finish_reason || 'stop',
    };
  } catch {
    return null;
  }
}

/**
 * Fallback to the Fly backend /api/generate (multi-provider).
 */
async function tryBackend(params: {
  prompt: string;
  messages: ChatMessage[];
  model: string;
  max_tokens: number;
  temperature: number;
}): Promise<GenerateResponse | null> {
  if (!BACKEND_URL) return null;

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    const res = await fetch(`${BACKEND_URL.replace(/\/$/, '')}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: params.prompt,
        messages: params.messages,
        model: params.model,
        max_tokens: params.max_tokens,
        temperature: params.temperature,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!res.ok) return null;
    return (await res.json()) as GenerateResponse;
  } catch {
    return null;
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ detail: 'Method not allowed' });
  }

  const { prompt, messages, model, max_tokens, temperature } = req.body as GenerateRequest;

  const normalizedMessages = normalizeMessages(prompt, messages);
  const promptForLegacy =
    typeof prompt === 'string' && prompt.trim().length > 0 ? prompt : getLastUserPrompt(normalizedMessages);

  if (!promptForLegacy) {
    return res.status(400).json({ detail: 'Missing "prompt" or "messages"' });
  }

  const selectedModel = model || 'gemma:2b';
  const resolvedMaxTokens = clampInt(max_tokens, 1, 1024) ?? defaultMaxTokens(promptForLegacy);
  const resolvedTemp = clampFloat(temperature, 0.0, 2.0) ?? 0.2;

  // 1) Prefer the Fly backend first (fast, always-on local fallback). This avoids
  // long hangs when GCP endpoints are down/cold-starting.
  const backendResult = await tryBackend({
    prompt: promptForLegacy,
    messages: normalizedMessages,
    model: selectedModel,
    max_tokens: resolvedMaxTokens,
    temperature: resolvedTemp,
  });
  if (backendResult) return res.status(200).json(backendResult);

  // 2) If a known Ollama model is requested and Ollama is configured, try Ollama.
  if (GCP_OLLAMA_URL && OLLAMA_MODELS.has(selectedModel)) {
    const ollamaResult = await tryOllama({
      prompt: promptForLegacy,
      messages: normalizedMessages,
      model: selectedModel,
      max_tokens: resolvedMaxTokens,
      temperature: resolvedTemp,
    });
    if (ollamaResult) return res.status(200).json(ollamaResult);
  }

  // 3) Try LlamaCPP if configured (OpenAI-compatible chat endpoint).
  if (GCP_LLAMACPP_URL) {
    const llamaCppResult = await tryLlamaCpp({
      messages: normalizedMessages,
      max_tokens: resolvedMaxTokens,
      temperature: resolvedTemp,
    });
    if (llamaCppResult) return res.status(200).json(llamaCppResult);
  }

  // 4) Fallback: try Ollama with any model (it may have pulled others).
  if (GCP_OLLAMA_URL && !OLLAMA_MODELS.has(selectedModel)) {
    const ollamaFallback = await tryOllama({
      prompt: promptForLegacy,
      messages: normalizedMessages,
      model: selectedModel,
      max_tokens: resolvedMaxTokens,
      temperature: resolvedTemp,
    });
    if (ollamaFallback) return res.status(200).json(ollamaFallback);
  }

  // All providers failed
  return res.status(503).json({
    detail: 'All LLM providers are currently unavailable. Please try again later.',
    content: 'Sorry, all AI models are currently offline. Please try again in a moment.',
    model: selectedModel,
    provider: 'none',
  });
}

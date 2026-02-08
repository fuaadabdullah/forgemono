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

// Map of model → provider hint ('ollama' | 'llamacpp')
const OLLAMA_MODELS = new Set([
  'gemma:2b',
  'mistral:7b',
  'phi3:3.8b',
  'deepseek-coder:1.3b',
  'llama3.2:1b',
  'qwen2.5:3b',
]);

interface GenerateRequest {
  prompt: string;
  model?: string;
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

/**
 * Try GCP Ollama (/api/generate endpoint)
 */
async function tryOllama(prompt: string, model: string): Promise<GenerateResponse | null> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    const res = await fetch(`${GCP_OLLAMA_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, prompt, stream: false }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!res.ok) return null;

    const data = await res.json();
    return {
      content: data.response || '',
      model: data.model || model,
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
async function tryLlamaCpp(prompt: string): Promise<GenerateResponse | null> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    const res = await fetch(`${GCP_LLAMACPP_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 1024,
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

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ detail: 'Method not allowed' });
  }

  const { prompt, model } = req.body as GenerateRequest;

  if (!prompt || typeof prompt !== 'string') {
    return res.status(400).json({ detail: 'Missing or invalid "prompt"' });
  }

  const selectedModel = model || 'gemma:2b';

  // 1. If model is a known Ollama model and Ollama URL is configured, try Ollama first
  if (GCP_OLLAMA_URL && OLLAMA_MODELS.has(selectedModel)) {
    const ollamaResult = await tryOllama(prompt, selectedModel);
    if (ollamaResult) return res.status(200).json(ollamaResult);
  }

  // 2. Try LlamaCPP if configured
  if (GCP_LLAMACPP_URL) {
    const llamaCppResult = await tryLlamaCpp(prompt);
    if (llamaCppResult) return res.status(200).json(llamaCppResult);
  }

  // 3. Fallback: try Ollama with any model (it may have pulled others)
  if (GCP_OLLAMA_URL && !OLLAMA_MODELS.has(selectedModel)) {
    const ollamaFallback = await tryOllama(prompt, selectedModel);
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

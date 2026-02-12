import type { NextApiRequest, NextApiResponse } from 'next';

const GCP_OLLAMA_URL = process.env.GCP_OLLAMA_URL || '';

// Hard-coded fallback list in case Ollama /api/tags is unreachable
const FALLBACK_MODELS = [
  { name: 'gemma:2b', provider: 'ollama' },
  { name: 'mistral:7b', provider: 'ollama' },
  { name: 'phi3:3.8b', provider: 'ollama' },
  { name: 'deepseek-coder:1.3b', provider: 'ollama' },
  { name: 'llama3.2:1b', provider: 'ollama' },
  { name: 'qwen2.5:3b', provider: 'ollama' },
  { name: 'qwen2.5-3b-instruct', provider: 'llamacpp' },
];

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!GCP_OLLAMA_URL) {
    // No Ollama URL configured — return static fallback
    return res.status(200).json({ models: FALLBACK_MODELS, source: 'fallback' });
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const ollamaRes = await fetch(`${GCP_OLLAMA_URL}/api/tags`, {
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (!ollamaRes.ok) {
      throw new Error(`Ollama /api/tags returned ${ollamaRes.status}`);
    }

    const data = await ollamaRes.json();
    const models = (data.models || []).map((m: { name: string; size?: number }) => ({
      name: m.name,
      provider: 'ollama',
      size: m.size,
    }));

    // Append the LlamaCPP model
    models.push({ name: 'qwen2.5-3b-instruct', provider: 'llamacpp' });

    return res.status(200).json({ models, source: 'live' });
  } catch {
    // Fallback to static list
    return res.status(200).json({ models: FALLBACK_MODELS, source: 'fallback' });
  }
}

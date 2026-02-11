const encoder = new TextEncoder();

// ============================================================================
// Provider Configuration
// ============================================================================
const PROVIDERS = {
  groq: {
    baseUrl: 'https://api.groq.com/openai/v1',
    models: [
      'llama-3.1-70b-versatile',
      'llama-3.1-8b-instant',
      'llama-3.2-90b-text-preview',
      'mixtral-8x7b-32768',
    ],
    priority: 1, // Lower = higher priority for cloud fallback
  },
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    priority: 2,
  },
  anthropic: {
    baseUrl: 'https://api.anthropic.com/v1',
    models: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
    priority: 3,
    isAnthropic: true,
  },
  deepseek: {
    baseUrl: 'https://api.deepseek.com/v1',
    models: ['deepseek-chat', 'deepseek-coder'],
    priority: 4,
  },
};

// GPU Cloud Providers (RunPod, Vast.ai) - dynamic endpoints
const GPU_CLOUD_PROVIDERS = {
  runpod: {
    // RunPod uses serverless endpoints with OpenAI-compatible API
    models: ['llama-3.1-70b', 'llama-3.1-8b', 'mistral-7b', 'codellama-34b'],
    priority: 0, // Highest priority - cheapest GPU cloud
  },
  vastai: {
    // Vast.ai instances run OpenAI-compatible servers
    models: ['llama-3.1-70b', 'llama-3.1-8b', 'mixtral-8x7b'],
    priority: 0, // Same priority as RunPod
  },
};

// Self-hosted infrastructure (GCP, local)
const SELF_HOSTED = {
  gcp_ollama: { priority: -2 }, // Highest priority - self-hosted
  gcp_llamacpp: { priority: -1 }, // Second priority - self-hosted
  local_ollama: { priority: -2 }, // Same as GCP
  local_llamacpp: { priority: -1 },
};

// Model to provider mapping for auto-routing
const MODEL_PROVIDER_MAP = {};
for (const [provider, config] of Object.entries(PROVIDERS)) {
  for (const model of config.models) {
    MODEL_PROVIDER_MAP[model] = provider;
  }
}
for (const [provider, config] of Object.entries(GPU_CLOUD_PROVIDERS)) {
  for (const model of config.models) {
    if (!MODEL_PROVIDER_MAP[model]) {
      MODEL_PROVIDER_MAP[model] = provider;
    }
  }
}

// ============================================================================
// JWT Utilities
// ============================================================================
function base64UrlDecode(input) {
  let base64 = input.replace(/-/g, '+').replace(/_/g, '/');
  const pad = base64.length % 4;
  if (pad) {
    base64 += '='.repeat(4 - pad);
  }
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function verifyJwtHS256(token, secret, options) {
  const parts = token.split('.');
  if (parts.length !== 3) return null;

  const [headerB64, payloadB64, signatureB64] = parts;
  const headerJson = JSON.parse(new TextDecoder().decode(base64UrlDecode(headerB64)));
  if (headerJson.alg !== 'HS256') return null;

  const payloadBytes = base64UrlDecode(payloadB64);
  const payload = JSON.parse(new TextDecoder().decode(payloadBytes));

  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['verify']
  );

  const data = encoder.encode(`${headerB64}.${payloadB64}`);
  const signature = base64UrlDecode(signatureB64);
  const valid = await crypto.subtle.verify('HMAC', key, signature, data);
  if (!valid) return null;

  const now = Math.floor(Date.now() / 1000);
  const leeway = options?.leewaySeconds ?? 30;

  if (payload.exp && now > payload.exp + leeway) return null;
  if (payload.nbf && now + leeway < payload.nbf) return null;
  if (options?.issuer && payload.iss !== options.issuer) return null;
  if (options?.audience) {
    const aud = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
    if (!aud.includes(options.audience)) return null;
  }

  return payload;
}

function buildUpstreamRequest(originalRequest, upstreamUrl, jwtPayload) {
  const headers = new Headers(originalRequest.headers);
  headers.set('X-Forwarded-Host', new URL(originalRequest.url).host);
  if (jwtPayload?.sub) headers.set('X-LLM-User', String(jwtPayload.sub));
  if (jwtPayload?.scope) headers.set('X-LLM-Scope', String(jwtPayload.scope));

  // Remove internal auth header before forwarding
  headers.delete('Authorization');

  return new Request(upstreamUrl, {
    method: originalRequest.method,
    headers,
    body: originalRequest.body,
    redirect: 'manual',
  });
}

function pickUpstream(url, env) {
  const targetHeader = url.searchParams.get('target') || env.DEFAULT_TARGET || 'gateway';
  const path = url.pathname.toLowerCase();

  if (targetHeader === 'ollama' || path.startsWith('/ollama')) {
    return env.OLLAMA_INTERNAL_URL;
  }

  if (targetHeader === 'llamacpp' || path.startsWith('/llamacpp')) {
    return env.LLAMACPP_INTERNAL_URL;
  }

  return env.DEFAULT_INTERNAL_URL || env.GATEWAY_INTERNAL_URL;
}

async function enforceRateLimit(env, request) {
  if (!env.RATE_LIMITER) return null;

  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const key = `${ip}:${request.headers.get('Authorization') || 'anon'}`;
  const id = env.RATE_LIMITER.idFromName(key);
  const limiter = env.RATE_LIMITER.get(id);

  const limit = Number(env.RATE_LIMIT_PER_MINUTE || 60);
  const res = await limiter.fetch('https://rate-limit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ limit }),
  });

  if (res.status === 429) return res;
  return null;
}
// ============================================================================
// Chat Completions - Provider Routing
// ============================================================================

function getApiKey(env, provider) {
  const keyMap = {
    groq: env.GROQ_API_KEY,
    openai: env.OPENAI_API_KEY,
    anthropic: env.ANTHROPIC_API_KEY,
    deepseek: env.DEEPSEEK_API_KEY,
  };
  return keyMap[provider] || null;
}

function selectProvider(model, env) {
  // Check if model explicitly maps to a provider
  const explicitProvider = MODEL_PROVIDER_MAP[model];
  if (explicitProvider && getApiKey(env, explicitProvider)) {
    return explicitProvider;
  }

  // Fallback: find first available provider by priority
  const sortedProviders = Object.entries(PROVIDERS).sort((a, b) => a[1].priority - b[1].priority);

  for (const [provider] of sortedProviders) {
    if (getApiKey(env, provider)) {
      return provider;
    }
  }

  return null;
}

async function tryLocalProvider(env, body, timeout = 5000) {
  // Priority order: GCP Ollama → GCP llama.cpp → Local Ollama → Local llama.cpp → RunPod → Vast.ai

  // ========================================================================
  // 1. GCP-hosted Ollama (highest priority - your infrastructure)
  // ========================================================================
  if (env.GCP_OLLAMA_URL) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const headers = { 'Content-Type': 'application/json' };
      if (env.GCP_OLLAMA_API_KEY) {
        headers['Authorization'] = `Bearer ${env.GCP_OLLAMA_API_KEY}`;
      }

      const response = await fetch(`${env.GCP_OLLAMA_URL}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model: body.model || 'llama3.2',
          messages: body.messages,
          stream: false,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return {
          success: true,
          provider: 'gcp_ollama',
          data: formatOllamaResponse(data, body.model),
        };
      }
    } catch (e) {
      console.log('GCP Ollama failed:', e.message);
    }
  }

  // ========================================================================
  // 2. GCP-hosted llama.cpp
  // ========================================================================
  if (env.GCP_LLAMACPP_URL) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const headers = { 'Content-Type': 'application/json' };
      if (env.GCP_LLAMACPP_API_KEY) {
        headers['Authorization'] = `Bearer ${env.GCP_LLAMACPP_API_KEY}`;
      }

      const response = await fetch(`${env.GCP_LLAMACPP_URL}/v1/chat/completions`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return { success: true, provider: 'gcp_llamacpp', data };
      }
    } catch (e) {
      console.log('GCP llama.cpp failed:', e.message);
    }
  }

  // ========================================================================
  // 3. Local Ollama (dev environment)
  // ========================================================================
  if (env.OLLAMA_INTERNAL_URL) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(`${env.OLLAMA_INTERNAL_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: body.model || 'llama3.2',
          messages: body.messages,
          stream: false,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return {
          success: true,
          provider: 'ollama',
          data: formatOllamaResponse(data, body.model),
        };
      }
    } catch (e) {
      // Silent fail, try next
    }
  }

  // ========================================================================
  // 4. Local llama.cpp (dev environment)
  // ========================================================================
  if (env.LLAMACPP_INTERNAL_URL) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(`${env.LLAMACPP_INTERNAL_URL}/v1/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return { success: true, provider: 'llamacpp', data };
      }
    } catch (e) {
      // Silent fail, try GPU cloud
    }
  }

  // ========================================================================
  // 5. RunPod Serverless (GPU cloud - cheap)
  // ========================================================================
  if (env.RUNPOD_API_KEY && env.RUNPOD_ENDPOINT_ID) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout * 2); // RunPod may need cold start

      const runpodUrl = `https://api.runpod.ai/v2/${env.RUNPOD_ENDPOINT_ID}/openai/v1/chat/completions`;

      const response = await fetch(runpodUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${env.RUNPOD_API_KEY}`,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return { success: true, provider: 'runpod', data };
      }
    } catch (e) {
      console.log('RunPod failed:', e.message);
    }
  }

  // ========================================================================
  // 6. Vast.ai Instance (GPU cloud - flexible)
  // ========================================================================
  if (env.VASTAI_INSTANCE_URL) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout * 2);

      const headers = { 'Content-Type': 'application/json' };
      if (env.VASTAI_API_KEY) {
        headers['Authorization'] = `Bearer ${env.VASTAI_API_KEY}`;
      }

      // Vast.ai typically runs vLLM or other OpenAI-compatible servers
      const response = await fetch(`${env.VASTAI_INSTANCE_URL}/v1/chat/completions`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return { success: true, provider: 'vastai', data };
      }
    } catch (e) {
      console.log('Vast.ai failed:', e.message);
    }
  }

  return { success: false };
}

// Helper to format Ollama response to OpenAI format
function formatOllamaResponse(data, model) {
  return {
    id: `chatcmpl-ollama-${Date.now()}`,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: model || 'llama3.2',
    choices: [
      {
        index: 0,
        message: data.message,
        finish_reason: 'stop',
      },
    ],
    usage: {
      prompt_tokens: data.prompt_eval_count || 0,
      completion_tokens: data.eval_count || 0,
      total_tokens: (data.prompt_eval_count || 0) + (data.eval_count || 0),
    },
  };
}

async function callCloudProvider(provider, body, apiKey) {
  const config = PROVIDERS[provider];
  if (!config) throw new Error(`Unknown provider: ${provider}`);

  // Handle Anthropic's different API format
  if (config.isAnthropic) {
    return callAnthropicProvider(body, apiKey);
  }

  const response = await fetch(`${config.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`${provider} error (${response.status}): ${error}`);
  }

  return response.json();
}

async function callAnthropicProvider(body, apiKey) {
  // Convert OpenAI format to Anthropic format
  const systemMessage = body.messages.find((m) => m.role === 'system');
  const nonSystemMessages = body.messages.filter((m) => m.role !== 'system');

  const anthropicBody = {
    model: body.model,
    max_tokens: body.max_tokens || 4096,
    messages: nonSystemMessages.map((m) => ({
      role: m.role === 'assistant' ? 'assistant' : 'user',
      content: m.content,
    })),
  };

  if (systemMessage) {
    anthropicBody.system = systemMessage.content;
  }

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify(anthropicBody),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Anthropic error (${response.status}): ${error}`);
  }

  const data = await response.json();

  // Convert Anthropic response to OpenAI format
  return {
    id: data.id,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: data.model,
    choices: [
      {
        index: 0,
        message: {
          role: 'assistant',
          content: data.content[0]?.text || '',
        },
        finish_reason: data.stop_reason === 'end_turn' ? 'stop' : data.stop_reason,
      },
    ],
    usage: {
      prompt_tokens: data.usage?.input_tokens || 0,
      completion_tokens: data.usage?.output_tokens || 0,
      total_tokens: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0),
    },
  };
}

async function handleChatCompletions(request, env, jwtPayload) {
  const body = await request.json();
  const startTime = Date.now();

  // Validate request
  if (!body.messages || !Array.isArray(body.messages) || body.messages.length === 0) {
    return new Response(
      JSON.stringify({
        error: {
          message: 'messages is required and must be a non-empty array',
          type: 'invalid_request_error',
        },
      }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const requestedModel = body.model || 'llama-3.1-8b-instant';
  let result = null;
  let usedProvider = null;

  // Try local providers first (if configured)
  if (env.LOCAL_FIRST !== 'false') {
    const localResult = await tryLocalProvider(env, body, Number(env.LOCAL_TIMEOUT_MS || 5000));
    if (localResult.success) {
      result = localResult.data;
      usedProvider = localResult.provider;
    }
  }

  // Fallback to cloud providers
  if (!result) {
    const provider = selectProvider(requestedModel, env);
    if (!provider) {
      return new Response(
        JSON.stringify({
          error: { message: 'No available provider configured', type: 'service_unavailable' },
        }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const apiKey = getApiKey(env, provider);

    try {
      // If model doesn't match provider, use a default model for that provider
      const modelForProvider =
        MODEL_PROVIDER_MAP[requestedModel] === provider
          ? requestedModel
          : PROVIDERS[provider].models[0];

      result = await callCloudProvider(provider, { ...body, model: modelForProvider }, apiKey);
      usedProvider = provider;
    } catch (error) {
      // Try fallback providers
      const sortedProviders = Object.entries(PROVIDERS)
        .sort((a, b) => a[1].priority - b[1].priority)
        .filter(([p]) => p !== provider && getApiKey(env, p));

      for (const [fallbackProvider] of sortedProviders) {
        try {
          const fallbackKey = getApiKey(env, fallbackProvider);
          const fallbackModel = PROVIDERS[fallbackProvider].models[0];
          result = await callCloudProvider(
            fallbackProvider,
            { ...body, model: fallbackModel },
            fallbackKey
          );
          usedProvider = fallbackProvider;
          break;
        } catch (e) {
          continue;
        }
      }

      if (!result) {
        return new Response(
          JSON.stringify({
            error: {
              message: `All providers failed. Last error: ${error.message}`,
              type: 'service_unavailable',
            },
          }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }
  }

  const latencyMs = Date.now() - startTime;

  // Log to D1 if available
  if (env.DB) {
    try {
      await env.DB.prepare(
        `
        INSERT INTO inference_logs (user_id, provider, model, latency_ms, tokens_used, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
      `
      )
        .bind(
          jwtPayload?.sub || 'anonymous',
          usedProvider,
          result.model || requestedModel,
          latencyMs,
          result.usage?.total_tokens || 0
        )
        .run();
    } catch (e) {
      // Non-blocking log failure
    }
  }

  // Add edge metadata
  result._edge = {
    provider: usedProvider,
    latency_ms: latencyMs,
    cached: false,
    edge_location: request.cf?.colo || 'unknown',
  };

  return new Response(JSON.stringify(result), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'X-Edge-Provider': usedProvider,
      'X-Edge-Latency-Ms': String(latencyMs),
    },
  });
}

// ============================================================================
// Models Endpoint
// ============================================================================
async function handleModels(env) {
  const availableModels = [];

  // Cloud API providers
  for (const [provider, config] of Object.entries(PROVIDERS)) {
    if (getApiKey(env, provider)) {
      for (const model of config.models) {
        availableModels.push({
          id: model,
          object: 'model',
          created: 1700000000,
          owned_by: provider,
        });
      }
    }
  }

  // GCP-hosted models (highest priority)
  if (env.GCP_OLLAMA_URL) {
    availableModels.push(
      { id: 'llama3.2', object: 'model', created: 1700000000, owned_by: 'gcp_ollama' },
      { id: 'llama3.1', object: 'model', created: 1700000000, owned_by: 'gcp_ollama' },
      { id: 'qwen2.5', object: 'model', created: 1700000000, owned_by: 'gcp_ollama' },
      { id: 'mistral', object: 'model', created: 1700000000, owned_by: 'gcp_ollama' }
    );
  }
  if (env.GCP_LLAMACPP_URL) {
    availableModels.push({
      id: 'gcp-llm',
      object: 'model',
      created: 1700000000,
      owned_by: 'gcp_llamacpp',
    });
  }

  // Local development models
  if (env.OLLAMA_INTERNAL_URL) {
    availableModels.push(
      { id: 'llama3.2', object: 'model', created: 1700000000, owned_by: 'ollama' },
      { id: 'llama3.1', object: 'model', created: 1700000000, owned_by: 'ollama' }
    );
  }
  if (env.LLAMACPP_INTERNAL_URL) {
    availableModels.push({
      id: 'local-llm',
      object: 'model',
      created: 1700000000,
      owned_by: 'llamacpp',
    });
  }

  // GPU Cloud providers
  if (env.RUNPOD_API_KEY && env.RUNPOD_ENDPOINT_ID) {
    for (const model of GPU_CLOUD_PROVIDERS.runpod.models) {
      availableModels.push({
        id: model,
        object: 'model',
        created: 1700000000,
        owned_by: 'runpod',
      });
    }
  }
  if (env.VASTAI_INSTANCE_URL) {
    for (const model of GPU_CLOUD_PROVIDERS.vastai.models) {
      availableModels.push({
        id: model,
        object: 'model',
        created: 1700000000,
        owned_by: 'vastai',
      });
    }
  }

  return new Response(
    JSON.stringify({
      object: 'list',
      data: availableModels,
    }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

// ============================================================================
// Health & Status Endpoints
// ============================================================================
async function handleHealth(env) {
  const providers = {};

  // Cloud API providers
  for (const [provider] of Object.entries(PROVIDERS)) {
    providers[provider] = getApiKey(env, provider) ? 'configured' : 'not_configured';
  }

  return new Response(
    JSON.stringify({
      status: 'healthy',
      edge: true,
      providers,
      gcp: {
        ollama: env.GCP_OLLAMA_URL ? 'configured' : 'not_configured',
        llamacpp: env.GCP_LLAMACPP_URL ? 'configured' : 'not_configured',
      },
      local: {
        ollama: env.OLLAMA_INTERNAL_URL ? 'configured' : 'not_configured',
        llamacpp: env.LLAMACPP_INTERNAL_URL ? 'configured' : 'not_configured',
      },
      gpu_cloud: {
        runpod: env.RUNPOD_API_KEY && env.RUNPOD_ENDPOINT_ID ? 'configured' : 'not_configured',
        vastai: env.VASTAI_INSTANCE_URL ? 'configured' : 'not_configured',
      },
    }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

// ============================================================================
// Main Handler
// ============================================================================
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          'Access-Control-Max-Age': '86400',
        },
      });
    }

    // Public health endpoint (no auth required)
    if (path === '/health' || path === '/v1/health') {
      return handleHealth(env);
    }

    // Auth required for everything else
    const authHeader = request.headers.get('Authorization') || '';
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : '';
    if (!token) {
      return new Response(JSON.stringify({ error: 'Missing JWT' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const jwtPayload = await verifyJwtHS256(token, env.JWT_SECRET || '', {
      issuer: env.JWT_ISSUER,
      audience: env.JWT_AUDIENCE,
      leewaySeconds: Number(env.JWT_LEEWAY_SECONDS || 30),
    });

    if (!jwtPayload) {
      return new Response(JSON.stringify({ error: 'Invalid JWT' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const rateLimitResponse = await enforceRateLimit(env, request);
    if (rateLimitResponse) return rateLimitResponse;

    // ========================================================================
    // Chat Completions - Edge-handled
    // ========================================================================
    if (
      (path === '/v1/chat/completions' || path === '/chat/completions') &&
      request.method === 'POST'
    ) {
      return handleChatCompletions(request, env, jwtPayload);
    }

    // Models endpoint
    if (path === '/v1/models' || path === '/models') {
      return handleModels(env);
    }

    // ========================================================================
    // Proxy to Backend (other routes)
    // ========================================================================
    const upstreamBase = pickUpstream(url, env);
    if (!upstreamBase) {
      return new Response(JSON.stringify({ error: 'No upstream configured' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    let upstreamPath = url.pathname;
    if (upstreamPath.startsWith('/ollama')) upstreamPath = upstreamPath.replace('/ollama', '');
    if (upstreamPath.startsWith('/llamacpp')) upstreamPath = upstreamPath.replace('/llamacpp', '');

    const upstreamUrl = new URL(upstreamPath + url.search, upstreamBase).toString();
    const upstreamRequest = buildUpstreamRequest(request, upstreamUrl, jwtPayload);

    return fetch(upstreamRequest);
  },
};

export class RateLimiter {
  constructor(state) {
    this.state = state;
  }

  async fetch(request) {
    const body = await request.json();
    const limit = Number(body.limit || 60);

    const now = Date.now();
    const windowMs = 60 * 1000;
    const windowKey = Math.floor(now / windowMs).toString();

    const stored = await this.state.storage.get(windowKey);
    const count = stored ? Number(stored) : 0;

    if (count >= limit) {
      return new Response('Rate limit exceeded', { status: 429 });
    }

    await this.state.storage.put(windowKey, count + 1, {
      expirationTtl: 120,
    });

    return new Response('OK', { status: 200 });
  }
}

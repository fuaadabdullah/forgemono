/**
 * Cloudflare Worker with Model Gateway + Turnstile Integration
 *
 * Features:
 * - Bot Protection (Turnstile) ✅
 * - Rate Limiting (KV) ✅
 * - Intelligent Model Routing 🆕
 * - Load Balancing 🆕
 * - Automatic Failover 🆕
 * - Health Monitoring 🆕
 * - Cost Tracking (D1) 🆕
 */

// ==================== CONFIGURATION ====================

const RATE_LIMIT_WINDOW = 60;
const RATE_LIMIT_MAX_REQUESTS = 100;

const FORBIDDEN_PATTERNS = [
  /system\s*prompt/gi,
  /ignore\s+(previous|all)\s+instructions?/gi,
  /jailbreak/gi,
  /\b(api[_-]?key|password|token|secret)\s*[:=]/gi,
];

const TURNSTILE_PROTECTED_PATHS = [
  '/api/chat',
  '/api/inference',
  '/v1/chat/completions',
  '/chat/completions',
  '/api/auth/login',
  '/api/auth/register',
];

// Model to endpoint mapping with cost/latency metadata
const MODEL_ENDPOINTS = {
  // Local Models (Ollama)
  'llama3.2': { provider: 'ollama', priority: 1, cost: 0, avgLatency: 500 },
  'qwen2.5:3b': { provider: 'ollama', priority: 1, cost: 0, avgLatency: 480 },
  'codellama': { provider: 'ollama', priority: 1, cost: 0, avgLatency: 600 },
  'mistral': { provider: 'ollama', priority: 1, cost: 0, avgLatency: 550 },

  // Local Models (llama.cpp)
  'tinyllama': { provider: 'llamacpp', priority: 2, cost: 0, avgLatency: 2000 },
  'mistral-gguf': { provider: 'llamacpp', priority: 2, cost: 0, avgLatency: 2100 },

  // Remote Local (Kamatera)
  'llama3-70b': { provider: 'kamatera', priority: 3, cost: 0.001, avgLatency: 300 },
  'deepseek-v2': { provider: 'kamatera', priority: 3, cost: 0.001, avgLatency: 320 },

  // Cloud Models - Groq (fast & cheap)
  'llama2-70b-4096': { provider: 'groq', priority: 4, cost: 0.0001, avgLatency: 400 },
  'mixtral-8x7b-32768': { provider: 'groq', priority: 4, cost: 0.0001, avgLatency: 380 },
  'gemma-7b-it': { provider: 'groq', priority: 4, cost: 0.0001, avgLatency: 420 },

  // Cloud Models - OpenAI
  'gpt-4o': { provider: 'openai', priority: 5, cost: 0.01, avgLatency: 950 },
  'gpt-4o-mini': { provider: 'openai', priority: 5, cost: 0.001, avgLatency: 850 },
  'gpt-3.5-turbo': { provider: 'openai', priority: 5, cost: 0.0015, avgLatency: 750 },

  // Cloud Models - Anthropic
  'claude-3-opus': { provider: 'anthropic', priority: 6, cost: 0.015, avgLatency: 1200 },
  'claude-3-sonnet': { provider: 'anthropic', priority: 6, cost: 0.003, avgLatency: 1100 },
  'claude-3-haiku': { provider: 'anthropic', priority: 6, cost: 0.00025, avgLatency: 900 },
};

// ==================== MAIN WORKER ====================

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
    const startTime = Date.now();

    try {
      // ===== HEALTH CHECK =====
      if (url.pathname === '/health' || url.pathname === '/') {
        const providerHealth = await getProviderHealth(env.DB);

        return new Response(
          JSON.stringify({
            status: 'healthy',
            edge: 'active',
            timestamp: new Date().toISOString(),
            worker: 'goblin-assistant-edge',
            version: '1.2.0',
            features: {
              turnstile: true,
              rate_limiting: true,
              model_gateway: true,
              failover: true,
              caching: true,
            },
            providers: providerHealth,
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
              'X-Goblin-Edge': 'active',
              'X-Response-Time': `${Date.now() - startTime}ms`,
            },
          }
        );
      }

      // ===== FEATURE FLAGS =====
      const flags = await getFeatureFlags(env);

      if (!flags.api_enabled) {
        return new Response(
          JSON.stringify({ error: 'API temporarily disabled' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // ===== TURNSTILE VERIFICATION (Bot Protection) =====
      if (shouldVerifyTurnstile(url.pathname)) {
        const turnstileResult = await verifyTurnstileToken(request, env, clientIP);

        if (!turnstileResult.success) {
          await logSecurityEvent(
            clientIP,
            'turnstile_failed',
            `${url.pathname} - ${turnstileResult.error}`,
            env
          );

          return new Response(
            JSON.stringify({
              error: 'Bot verification failed',
              details: turnstileResult.error,
              help: 'Please complete the security check and try again',
            }),
            {
              status: 403,
              headers: {
                'Content-Type': 'application/json',
                'X-Goblin-Edge': 'active',
                'X-Bot-Check': 'failed',
              },
            }
          );
        }
      }

      // ===== RATE LIMITING =====
      const rateLimitOk = await checkRateLimit(clientIP, env.GOBLIN_CACHE);
      if (!rateLimitOk) {
        return new Response(
          JSON.stringify({
            error: 'Rate limit exceeded',
            limit: RATE_LIMIT_MAX_REQUESTS,
            window: `${RATE_LIMIT_WINDOW}s`,
          }),
          {
            status: 429,
            headers: {
              'Content-Type': 'application/json',
              'Retry-After': RATE_LIMIT_WINDOW.toString(),
            },
          }
        );
      }

      // ===== MODEL GATEWAY ROUTING =====
      if (isInferenceRequest(url.pathname)) {
        return await handleInferenceRequest(request, env, clientIP, startTime);
      }

      // ===== FALLBACK: Proxy to backend =====
      return await proxyToBackend(request, env);

    } catch (error) {
      console.error('[Worker Error]', error);
      return new Response(
        JSON.stringify({
          error: 'Internal server error',
          details: error.message,
        }),
        {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }
  },

  // ===== CRON: Health Checks =====
  async scheduled(event, env, ctx) {
    console.log('[Cron] Running health checks...');

    const endpoints = [
      { provider: 'ollama', url: env.OLLAMA_ENDPOINT },
      { provider: 'llamacpp', url: env.LLAMACPP_ENDPOINT },
      { provider: 'kamatera', url: env.KAMATERA_ENDPOINT },
    ];

    for (const ep of endpoints) {
      if (!ep.url) continue;

      try {
        await checkEndpointHealth(ep.provider, ep.url, env.DB);
      } catch (error) {
        console.error(`[Health Check] ${ep.provider} failed:`, error.message);
      }
    }

    console.log('[Cron] Health checks complete');
  },
};

// ==================== MODEL GATEWAY FUNCTIONS ====================

function isInferenceRequest(pathname) {
  const inferencePatterns = [
    '/v1/chat/completions',
    '/chat/completions',
    '/api/chat',
    '/api/inference',
    '/v1/completions',
    '/completions',
  ];
  return inferencePatterns.some(pattern => pathname.includes(pattern));
}

async function handleInferenceRequest(request, env, clientIP, startTime) {
  const requestId = crypto.randomUUID();
  let requestBody = null;

  try {
    requestBody = await request.json();
  } catch (e) {
    return new Response(
      JSON.stringify({ error: 'Invalid JSON in request body' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const model = requestBody.model || 'gpt-4o-mini';
  const routingStrategy = request.headers.get('X-Routing-Strategy') ||
                          env.DEFAULT_ROUTING_STRATEGY ||
                          'cost-optimized';

  console.log(`[${requestId}] Inference request for model: ${model}, strategy: ${routingStrategy}`);

  // ===== SELECT ENDPOINT =====
  const endpoint = await selectEndpoint(model, routingStrategy, env);

  if (!endpoint) {
    return new Response(
      JSON.stringify({
        error: 'No available endpoints for requested model',
        model: model,
        strategy: routingStrategy,
      }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }

  console.log(`[${requestId}] Routing to ${endpoint.provider} at ${endpoint.url}`);

  // ===== FAILOVER LOOP =====
  const maxAttempts = parseInt(env.MAX_FAILOVER_ATTEMPTS || '3');
  let lastError = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await forwardToProvider(request, requestBody, endpoint, env);
      const latency = Date.now() - startTime;

      // Log successful inference
      await logInference(env.DB, {
        requestId,
        userId: request.headers.get('X-User-ID'),
        model,
        provider: endpoint.provider,
        endpoint: endpoint.url,
        costUsd: endpoint.cost,
        latencyMs: latency,
        status: 'success',
        routingStrategy,
        wasCached: false,
      });

      // Add metadata headers
      const responseHeaders = new Headers(response.headers);
      responseHeaders.set('X-Provider-Used', endpoint.provider);
      responseHeaders.set('X-Request-ID', requestId);
      responseHeaders.set('X-Latency-Ms', latency.toString());
      responseHeaders.set('X-Cost-Usd', endpoint.cost.toString());
      responseHeaders.set('X-Attempt', attempt.toString());

      return new Response(response.body, {
        status: response.status,
        headers: responseHeaders,
      });

    } catch (error) {
      lastError = error.message;
      console.error(`[${requestId}] Attempt ${attempt}/${maxAttempts} failed:`, lastError);

      // Log failed attempt
      await logInference(env.DB, {
        requestId,
        userId: request.headers.get('X-User-ID'),
        model,
        provider: endpoint.provider,
        endpoint: endpoint.url,
        costUsd: 0,
        latencyMs: Date.now() - startTime,
        status: 'failed',
        errorMessage: lastError,
        routingStrategy,
        wasCached: false,
      });

      // If not last attempt, try failover
      if (attempt < maxAttempts && env.ENABLE_FAILOVER === 'true') {
        console.log(`[${requestId}] Attempting failover...`);
        // Get next best endpoint (excluding failed provider)
        const failoverEndpoint = await selectEndpoint(
          model,
          'balanced',
          env,
          [endpoint.provider]
        );

        if (failoverEndpoint) {
          Object.assign(endpoint, failoverEndpoint);
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt)); // Exponential backoff
          continue;
        }
      }

      // Last attempt failed
      if (attempt === maxAttempts) {
        return new Response(
          JSON.stringify({
            error: 'All inference endpoints failed',
            details: lastError,
            attempts: maxAttempts,
            requestId,
          }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }
  }
}

async function selectEndpoint(model, strategy, env, excludeProviders = []) {
  const modelConfig = MODEL_ENDPOINTS[model];
  const healthyProviders = await getHealthyProviders(env.DB, excludeProviders);

  // If model is explicitly mapped, use that provider
  if (modelConfig && healthyProviders.includes(modelConfig.provider)) {
    return {
      provider: modelConfig.provider,
      url: getProviderEndpoint(modelConfig.provider, env),
      cost: modelConfig.cost,
      priority: modelConfig.priority,
    };
  }

  // Otherwise, select based on strategy
  switch (strategy) {
    case 'cost-optimized':
      return selectCostOptimized(healthyProviders, env);

    case 'latency-optimized':
      return selectLatencyOptimized(healthyProviders, env);

    case 'local-first':
      return selectLocalFirst(healthyProviders, env);

    case 'balanced':
      return selectBalanced(healthyProviders, env);

    case 'quality-optimized':
      return selectQualityOptimized(healthyProviders, env);

    default:
      return selectCostOptimized(healthyProviders, env);
  }
}

function selectCostOptimized(providers, env) {
  // Priority: ollama > llamacpp > kamatera > groq > openai > anthropic
  const order = ['ollama', 'llamacpp', 'kamatera', 'groq', 'openai', 'anthropic'];

  for (const provider of order) {
    if (providers.includes(provider)) {
      return {
        provider,
        url: getProviderEndpoint(provider, env),
        cost: getCostForProvider(provider),
        priority: order.indexOf(provider) + 1,
      };
    }
  }

  return null;
}

function selectLatencyOptimized(providers, env) {
  // Priority: kamatera > groq > ollama > openai > anthropic > llamacpp
  const order = ['kamatera', 'groq', 'ollama', 'openai', 'anthropic', 'llamacpp'];

  for (const provider of order) {
    if (providers.includes(provider)) {
      return {
        provider,
        url: getProviderEndpoint(provider, env),
        cost: getCostForProvider(provider),
        priority: order.indexOf(provider) + 1,
      };
    }
  }

  return null;
}

function selectLocalFirst(providers, env) {
  // Only use local providers, fail if none available
  const localProviders = ['ollama', 'llamacpp', 'kamatera'];

  for (const provider of localProviders) {
    if (providers.includes(provider)) {
      return {
        provider,
        url: getProviderEndpoint(provider, env),
        cost: getCostForProvider(provider),
        priority: localProviders.indexOf(provider) + 1,
      };
    }
  }

  // Fallback to cloud if local unavailable (can be disabled)
  return selectCostOptimized(providers, env);
}

function selectBalanced(providers, env) {
  // Mix of cost and latency
  const order = ['ollama', 'groq', 'kamatera', 'openai', 'llamacpp', 'anthropic'];

  for (const provider of order) {
    if (providers.includes(provider)) {
      return {
        provider,
        url: getProviderEndpoint(provider, env),
        cost: getCostForProvider(provider),
        priority: order.indexOf(provider) + 1,
      };
    }
  }

  return null;
}

function selectQualityOptimized(providers, env) {
  // Best models first
  const order = ['openai', 'anthropic', 'groq', 'kamatera', 'ollama', 'llamacpp'];

  for (const provider of order) {
    if (providers.includes(provider)) {
      return {
        provider,
        url: getProviderEndpoint(provider, env),
        cost: getCostForProvider(provider),
        priority: order.indexOf(provider) + 1,
      };
    }
  }

  return null;
}

function getProviderEndpoint(provider, env) {
  const endpoints = {
    'ollama': env.OLLAMA_ENDPOINT || 'http://localhost:11434',
    'llamacpp': env.LLAMACPP_ENDPOINT || 'http://localhost:8080',
    'kamatera': env.KAMATERA_ENDPOINT || '',
    'openai': env.OPENAI_ENDPOINT || 'https://api.openai.com/v1',
    'anthropic': env.ANTHROPIC_ENDPOINT || 'https://api.anthropic.com/v1',
    'groq': env.GROQ_ENDPOINT || 'https://api.groq.com/openai/v1',
  };

  return endpoints[provider] || '';
}

function getCostForProvider(provider) {
  const costs = {
    'ollama': 0,
    'llamacpp': 0,
    'kamatera': 0.001,
    'groq': 0.0001,
    'openai': 0.005,
    'anthropic': 0.008,
  };

  return costs[provider] || 0;
}

async function forwardToProvider(request, body, endpoint, env) {
  const url = new URL(request.url);

  // Build target URL
  let targetUrl = endpoint.url;

  // Normalize endpoint for different providers
  if (endpoint.provider === 'ollama') {
    targetUrl += '/v1/chat/completions';
  } else if (endpoint.provider === 'llamacpp') {
    targetUrl += '/v1/chat/completions';
  } else if (endpoint.provider === 'kamatera') {
    targetUrl += '/v1/chat/completions';
  } else {
    // OpenAI-compatible (openai, groq, anthropic)
    targetUrl += url.pathname;
  }

  // Build headers
  const headers = new Headers({
    'Content-Type': 'application/json',
  });

  // Add API keys for cloud providers
  if (endpoint.provider === 'openai' && env.OPENAI_API_KEY) {
    headers.set('Authorization', `Bearer ${env.OPENAI_API_KEY}`);
  } else if (endpoint.provider === 'anthropic' && env.ANTHROPIC_API_KEY) {
    headers.set('X-API-Key', env.ANTHROPIC_API_KEY);
  } else if (endpoint.provider === 'groq' && env.GROQ_API_KEY) {
    headers.set('Authorization', `Bearer ${env.GROQ_API_KEY}`);
  } else if (endpoint.provider === 'kamatera' && env.KAMATERA_AUTH_TOKEN) {
    headers.set('Authorization', `Bearer ${env.KAMATERA_AUTH_TOKEN}`);
  }

  // Forward request
  const response = await fetch(targetUrl, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  return response;
}

// ==================== HELPER FUNCTIONS ====================

async function getHealthyProviders(db, excludeProviders = []) {
  try {
    const result = await db.prepare(`
      SELECT provider FROM provider_health
      WHERE is_healthy = 1
      AND last_check > datetime('now', '-5 minutes')
    `).all();

    const healthy = result.results.map(row => row.provider);
    return healthy.filter(p => !excludeProviders.includes(p));
  } catch (error) {
    console.error('[DB Error] getHealthyProviders:', error);
    // Fallback: assume all providers healthy if DB unavailable
    return ['ollama', 'llamacpp', 'kamatera', 'groq', 'openai', 'anthropic']
      .filter(p => !excludeProviders.includes(p));
  }
}

async function getProviderHealth(db) {
  try {
    const result = await db.prepare(`
      SELECT provider, is_healthy, avg_latency_ms, last_check
      FROM provider_health
      WHERE last_check > datetime('now', '-10 minutes')
    `).all();

    const health = {};
    for (const row of result.results) {
      health[row.provider] = {
        healthy: row.is_healthy === 1,
        latency_ms: row.avg_latency_ms,
        last_check: row.last_check,
      };
    }

    return health;
  } catch (error) {
    console.error('[DB Error] getProviderHealth:', error);
    return {};
  }
}

async function checkEndpointHealth(provider, endpoint, db) {
  const start = Date.now();

  try {
    // Send health check request
    const response = await fetch(`${endpoint}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });

    const latency = Date.now() - start;
    const isHealthy = response.ok && latency < 10000;

    // Update D1
    await db.prepare(`
      INSERT OR REPLACE INTO provider_health
      (provider, endpoint, last_check, is_healthy, avg_latency_ms)
      VALUES (?, ?, datetime('now'), ?, ?)
    `).bind(provider, endpoint, isHealthy ? 1 : 0, latency).run();

    console.log(`[Health] ${provider}: ${isHealthy ? 'UP' : 'DOWN'} (${latency}ms)`);
  } catch (error) {
    console.error(`[Health] ${provider} failed:`, error.message);

    // Mark as unhealthy
    await db.prepare(`
      INSERT OR REPLACE INTO provider_health
      (provider, endpoint, last_check, is_healthy, avg_latency_ms)
      VALUES (?, ?, datetime('now'), 0, 0)
    `).bind(provider, endpoint).run();
  }
}

async function logInference(db, data) {
  try {
    await db.prepare(`
      INSERT INTO inference_logs (
        request_id, user_id, model, provider, endpoint,
        prompt_tokens, completion_tokens, total_tokens,
        cost_usd, latency_ms, status, error_message,
        routing_strategy, was_cached
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      data.requestId,
      data.userId || null,
      data.model,
      data.provider,
      data.endpoint,
      data.promptTokens || 0,
      data.completionTokens || 0,
      data.totalTokens || 0,
      data.costUsd || 0,
      data.latencyMs,
      data.status,
      data.errorMessage || null,
      data.routingStrategy,
      data.wasCached ? 1 : 0
    ).run();
  } catch (error) {
    console.error('[DB Error] logInference:', error);
  }
}

// ===== Reuse existing helper functions from original worker =====

async function getFeatureFlags(env) {
  try {
    const result = await env.DB.prepare(`
      SELECT key, value FROM feature_flags WHERE enabled = 1
    `).all();

    const flags = {};
    for (const row of result.results) {
      flags[row.key] = row.value === 'true' || row.value === '1';
    }

    return {
      api_enabled: flags.api_enabled !== false,
      turnstile_enabled: flags.turnstile_enabled !== false,
      ...flags,
    };
  } catch (error) {
    console.error('[DB Error] getFeatureFlags:', error);
    return { api_enabled: true, turnstile_enabled: true };
  }
}

function shouldVerifyTurnstile(pathname) {
  return TURNSTILE_PROTECTED_PATHS.some(path => pathname.includes(path));
}

async function verifyTurnstileToken(request, env, clientIP) {
  const token = request.headers.get('X-Turnstile-Token');

  if (!token) {
    return { success: false, error: 'No Turnstile token provided' };
  }

  try {
    const verifyUrl = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
    const secretKey = env.TURNSTILE_SECRET_KEY_MANAGED || env.TURNSTILE_SECRET_KEY_INVISIBLE;

    const response = await fetch(verifyUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        secret: secretKey,
        response: token,
        remoteip: clientIP,
      }),
    });

    const result = await response.json();
    return {
      success: result.success,
      error: result.success ? null : (result['error-codes']?.join(', ') || 'Verification failed'),
    };
  } catch (error) {
    console.error('[Turnstile Error]', error);
    return { success: false, error: error.message };
  }
}

async function checkRateLimit(clientIP, kv) {
  const key = `rate_limit:${clientIP}`;
  const current = await kv.get(key);

  if (!current) {
    await kv.put(key, '1', { expirationTtl: RATE_LIMIT_WINDOW });
    return true;
  }

  const count = parseInt(current);
  if (count >= RATE_LIMIT_MAX_REQUESTS) {
    return false;
  }

  await kv.put(key, (count + 1).toString(), { expirationTtl: RATE_LIMIT_WINDOW });
  return true;
}

async function logSecurityEvent(clientIP, eventType, details, env) {
  try {
    await env.DB.prepare(`
      INSERT INTO audit_logs (event_type, user_id, metadata)
      VALUES (?, ?, ?)
    `).bind(
      `security:${eventType}`,
      null,
      JSON.stringify({ ip: clientIP, details })
    ).run();
  } catch (error) {
    console.error('[DB Error] logSecurityEvent:', error);
  }
}

async function proxyToBackend(request, env) {
  const url = new URL(request.url);
  const backendUrl = env.API_URL || 'http://localhost:8000';

  const targetUrl = `${backendUrl}${url.pathname}${url.search}`;

  return await fetch(targetUrl, {
    method: request.method,
    headers: request.headers,
    body: request.body,
  });
}

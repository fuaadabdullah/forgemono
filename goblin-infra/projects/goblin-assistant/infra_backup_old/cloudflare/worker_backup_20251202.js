/**
 * Cloudflare Worker with Turnstile Integration
 * This adds bot protection to prevent API abuse and reduce inference costs
 */

// Rate limiting configuration
const RATE_LIMIT_WINDOW = 60;
const RATE_LIMIT_MAX_REQUESTS = 100;

// Forbidden patterns for prompt sanitization
const FORBIDDEN_PATTERNS = [
  /system\s*prompt/gi,
  /ignore\s+(previous|all)\s+instructions?/gi,
  /jailbreak/gi,
  /\b(api[_-]?key|password|token|secret)\s*[:=]/gi,
];

// Protected endpoints that require Turnstile verification
const TURNSTILE_PROTECTED_PATHS = [
  '/api/chat',
  '/api/inference',
  '/api/auth/login',
  '/api/auth/signup',
  '/api/auth/reset-password',
];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
    const startTime = Date.now();

    try {
      // Health check endpoint - bypass all checks
      if (url.pathname === '/health' || url.pathname === '/') {
        return new Response(
          JSON.stringify({
            status: 'healthy',
            edge: 'active',
            timestamp: new Date().toISOString(),
            worker: 'goblin-assistant-edge',
            version: '1.1.0',
            features: {
              turnstile: true,
              rate_limiting: true,
              prompt_sanitization: true,
              caching: true,
            },
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

      // Feature flags check
      const flags = await getFeatureFlags(env);

      if (!flags.api_enabled) {
        return new Response(
          JSON.stringify({ error: 'API temporarily disabled' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // STEP 1: TURNSTILE VERIFICATION (Bot Protection)
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

      // STEP 2: RATE LIMITING
      if (flags.rate_limiting_enabled) {
        const rateLimitResult = await checkRateLimit(clientIP, env);
        if (!rateLimitResult.allowed) {
          return new Response(
            JSON.stringify({
              error: 'Rate limit exceeded',
              retry_after: rateLimitResult.retry_after,
            }),
            {
              status: 429,
              headers: {
                'Content-Type': 'application/json',
                'Retry-After': rateLimitResult.retry_after.toString(),
                'X-Goblin-Edge': 'active',
              },
            }
          );
        }
      }

      // STEP 3: PROMPT SANITIZATION
      let modifiedRequest = request;
      if (request.method === 'POST' && url.pathname.includes('/chat')) {
        const sanitizeResult = await sanitizePrompt(request);
        if (sanitizeResult.blocked) {
          await logSecurityEvent(clientIP, 'prompt_blocked', sanitizeResult.reason, env);
          return new Response(
            JSON.stringify({
              error: 'Request blocked',
              reason: 'Suspicious content detected',
            }),
            {
              status: 403,
              headers: {
                'Content-Type': 'application/json',
                'X-Goblin-Edge': 'active',
              },
            }
          );
        }
        if (sanitizeResult.modified) {
          modifiedRequest = sanitizeResult.request;
        }
      }

      // STEP 4: SESSION VALIDATION
      let userSession = null;
      const authHeader = request.headers.get('Authorization');
      if (authHeader?.startsWith('Bearer ')) {
        const token = authHeader.substring(7);
        userSession = await validateSession(token, env);
        if (!userSession) {
          return new Response(
            JSON.stringify({ error: 'Invalid or expired session' }),
            {
              status: 401,
              headers: {
                'Content-Type': 'application/json',
                'X-Goblin-Edge': 'active',
              },
            }
          );
        }
      }

      // STEP 5: CONVERSATION CONTEXT CACHING
      let conversationContext = null;
      if (userSession && url.pathname.includes('/chat')) {
        conversationContext = await getConversationContext(userSession.user_id, env);
      }

      // STEP 6: RESPONSE CACHING
      if (request.method === 'GET' && shouldCache(url)) {
        const cacheKey = `cache:${url.pathname}${url.search}`;
        const cached = env.GOBLIN_CACHE ? await env.GOBLIN_CACHE.get(cacheKey, 'json') : null;
        if (cached) {
          ctx.waitUntil(logAnalytics(request, clientIP, 'cache_hit', Date.now() - startTime, env));
          return new Response(JSON.stringify(cached), {
            headers: {
              'Content-Type': 'application/json',
              'X-Cache': 'HIT',
              'X-Goblin-Edge': 'active',
            },
          });
        }
      }

      // STEP 7: PROXY TO BACKEND
      const backendUrl = env.API_URL || 'http://localhost:8000';
      const backendRequest = new Request(
        `${backendUrl}${url.pathname}${url.search}`,
        modifiedRequest
      );

      if (conversationContext) {
        backendRequest.headers.set('X-Conversation-Context', JSON.stringify(conversationContext));
      }
      if (userSession) {
        backendRequest.headers.set('X-User-Id', userSession.user_id);
      }

      const response = await fetch(backendRequest);
      const responseData = await response.clone().text();

      // Cache successful GET responses
      if (request.method === 'GET' && response.ok && shouldCache(url) && env.GOBLIN_CACHE) {
        ctx.waitUntil(
          env.GOBLIN_CACHE.put(`cache:${url.pathname}${url.search}`, responseData, {
            expirationTtl: 300,
          })
        );
      }

      // Log analytics
      ctx.waitUntil(logAnalytics(request, clientIP, 'success', Date.now() - startTime, env));

      return new Response(responseData, {
        status: response.status,
        headers: {
          ...Object.fromEntries(response.headers),
          'X-Goblin-Edge': 'active',
          'X-Response-Time': `${Date.now() - startTime}ms`,
        },
      });
    } catch (error) {
      ctx.waitUntil(
        logSecurityEvent(clientIP, 'error', error.message, env)
      );

      return new Response(
        JSON.stringify({
          error: 'Internal server error',
          message: error.message,
        }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'X-Goblin-Edge': 'active',
          },
        }
      );
    }
  },
};

/**
 * Verify Turnstile token from request
 */
async function verifyTurnstileToken(request, env, clientIP) {
  let turnstileToken;

  // Check header (for API calls)
  turnstileToken = request.headers.get('X-Turnstile-Token');

  // Check body (for form submissions)
  if (!turnstileToken && request.method === 'POST') {
    try {
      const body = await request.clone().json();
      turnstileToken = body.turnstile_token;
    } catch (e) {
      // Not JSON body, skip
    }
  }

  if (!turnstileToken) {
    return {
      success: false,
      error: 'Turnstile token missing',
    };
  }

  // Determine which secret key to use
  const secretKey = env.TURNSTILE_SECRET_KEY_INVISIBLE || env.TURNSTILE_SECRET_KEY_MANAGED;

  if (!secretKey) {
    console.error('Turnstile secret key not configured');
    return { success: true }; // Fail open if not configured
  }

  // Verify with Cloudflare
  const formData = new FormData();
  formData.append('secret', secretKey);
  formData.append('response', turnstileToken);
  formData.append('remoteip', clientIP);

  try {
    const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();

    if (!result.success) {
      return {
        success: false,
        error: result['error-codes']?.join(', ') || 'Verification failed',
      };
    }

    return { success: true };
  } catch (error) {
    console.error('Turnstile verification error:', error);
    return { success: true }; // Fail open on error
  }
}

/**
 * Determine if path requires Turnstile verification
 */
function shouldVerifyTurnstile(pathname) {
  return TURNSTILE_PROTECTED_PATHS.some(path => pathname.startsWith(path));
}

// ... (keep all existing helper functions from original worker.js)

async function getFeatureFlags(env) {
  if (!env.GOBLIN_CACHE) return getDefaultFlags();

  const cached = await env.GOBLIN_CACHE.get('feature_flags', 'json');
  if (cached) return cached;

  if (!env.DB) return getDefaultFlags();

  try {
    const result = await env.DB.prepare('SELECT flag_name, enabled FROM feature_flags').all();
    const flags = {};
    result.results.forEach(row => {
      flags[row.flag_name] = row.enabled === 1;
    });

    await env.GOBLIN_CACHE.put('feature_flags', JSON.stringify(flags), {
      expirationTtl: 300,
    });

    return flags;
  } catch (error) {
    return getDefaultFlags();
  }
}

function getDefaultFlags() {
  return {
    api_enabled: true,
    rate_limiting_enabled: true,
    new_ui_enabled: false,
    experimental_features: false,
  };
}

async function checkRateLimit(clientIP, env) {
  if (!env.GOBLIN_CACHE) return { allowed: true };

  const key = `ratelimit:${clientIP}`;
  const current = await env.GOBLIN_CACHE.get(key);
  const count = current ? parseInt(current) : 0;

  if (count >= RATE_LIMIT_MAX_REQUESTS) {
    return {
      allowed: false,
      retry_after: RATE_LIMIT_WINDOW,
    };
  }

  await env.GOBLIN_CACHE.put(key, (count + 1).toString(), {
    expirationTtl: RATE_LIMIT_WINDOW,
  });

  return { allowed: true };
}

async function sanitizePrompt(request) {
  try {
    const body = await request.clone().json();
    const prompt = body.message || body.prompt || '';

    for (const pattern of FORBIDDEN_PATTERNS) {
      if (pattern.test(prompt)) {
        return {
          blocked: true,
          reason: `Pattern matched: ${pattern}`,
        };
      }
    }

    return { blocked: false, modified: false, request };
  } catch (error) {
    return { blocked: false, modified: false, request };
  }
}

async function validateSession(token, env) {
  if (!env.GOBLIN_CACHE) return null;

  const sessionKey = `session:${token}`;
  const session = await env.GOBLIN_CACHE.get(sessionKey, 'json');

  if (!session) return null;
  if (Date.now() > session.expires_at) {
    await env.GOBLIN_CACHE.delete(sessionKey);
    return null;
  }

  return session;
}

async function getConversationContext(userId, env) {
  if (!env.GOBLIN_CACHE) return null;

  const contextKey = `conversation:${userId}`;
  return await env.GOBLIN_CACHE.get(contextKey, 'json');
}

function shouldCache(url) {
  const cacheablePaths = ['/api/models', '/api/config', '/api/status'];
  return cacheablePaths.some(path => url.pathname.startsWith(path));
}

async function logAnalytics(request, clientIP, status, responseTime, env) {
  if (!env.GOBLIN_CACHE) return;

  const timestamp = Date.now();
  const url = new URL(request.url);
  const analyticsKey = `analytics:${timestamp}:${clientIP}`;

  const analytics = {
    timestamp,
    ip: clientIP,
    method: request.method,
    path: url.pathname,
    status,
    response_time: responseTime,
    user_agent: request.headers.get('User-Agent'),
  };

  await env.GOBLIN_CACHE.put(analyticsKey, JSON.stringify(analytics), {
    expirationTtl: 86400, // 24 hours
  });
}

async function logSecurityEvent(clientIP, event, reason, env) {
  if (!env.GOBLIN_CACHE) return;

  const timestamp = Date.now();
  const securityKey = `security:${timestamp}:${clientIP}`;

  const securityEvent = {
    timestamp,
    ip: clientIP,
    event,
    reason,
  };

  await env.GOBLIN_CACHE.put(securityKey, JSON.stringify(securityEvent), {
    expirationTtl: 604800, // 7 days
  });
}

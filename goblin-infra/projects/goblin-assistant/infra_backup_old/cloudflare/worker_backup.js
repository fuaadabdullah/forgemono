/**
 * Cloudflare Worker for Goblin Assistant - Edge Goblins
 * Memory Shards: KV for caching, sessions, feature flags, rate limits
 * Let your main backend focus on LLM inference. These edge goblins handle:
 * 1. Rate limiting user requests (KV-backed)
 * 2. Sanitizing prompts before they hit your main LLM
 * 3. Analytics event collection (KV storage)
 * 4. Simple CRUD caching (KV storage)
 * 5. User session state (KV storage)
 * 6. Conversation context caching (KV storage)
 * 7. Feature flags (KV storage)
 */

// Rate limiting configuration
const RATE_LIMIT_WINDOW = 60; // seconds
const RATE_LIMIT_MAX_REQUESTS = 100; // max requests per window per IP

// Forbidden patterns for prompt sanitization
const FORBIDDEN_PATTERNS = [
  /system\s*prompt/gi,
  /ignore\s+(previous|all)\s+instructions?/gi,
  /jailbreak/gi,
  /\b(api[_-]?key|password|token|secret)\s*[:=]/gi,
];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const clientIP = request.headers.get("CF-Connecting-IP") || "unknown";
    const startTime = Date.now();

    try {
      // Health check endpoint - responds directly without proxying
      if (url.pathname === "/health" || url.pathname === "/") {
        return new Response(
          JSON.stringify({
            status: "healthy",
            edge: "active",
            timestamp: new Date().toISOString(),
            worker: "goblin-assistant-edge",
            version: "1.0.0",
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              "X-Goblin-Edge": "active",
              "X-Response-Time": `${Date.now() - startTime}ms`,
            },
          }
        );
      }

      // 0. FEATURE FLAGS - Check if features are enabled
      const flags = await getFeatureFlags(env);

      if (!flags.api_enabled) {
        return new Response(
          JSON.stringify({ error: "API temporarily disabled" }),
          { status: 503, headers: { "Content-Type": "application/json" } }
        );
      }

      // 1. RATE LIMITING - Edge Goblin #1 (KV-backed)
      if (flags.rate_limiting_enabled) {
        const rateLimitResult = await checkRateLimit(clientIP, env);
        if (!rateLimitResult.allowed) {
          return new Response(
            JSON.stringify({
              error: "Rate limit exceeded",
              retry_after: rateLimitResult.retry_after,
            }),
            {
              status: 429,
              headers: {
                "Content-Type": "application/json",
                "X-RateLimit-Limit": RATE_LIMIT_MAX_REQUESTS.toString(),
                "X-RateLimit-Remaining": "0",
                "Retry-After": rateLimitResult.retry_after.toString(),
              },
            }
          );
        }
      }

      // 2. USER SESSION STATE - Check session validity
      const sessionToken = request.headers.get("Authorization")?.replace("Bearer ", "");
      let userSession = null;
      if (sessionToken) {
        userSession = await getUserSession(sessionToken, env);
        if (userSession && userSession.expired) {
          return new Response(
            JSON.stringify({ error: "Session expired" }),
            { status: 401, headers: { "Content-Type": "application/json" } }
          );
        }
      }

      // 3. CONVERSATION CONTEXT CACHING - Load recent context
      let conversationContext = null;
      if (userSession && url.pathname.includes("/chat")) {
        conversationContext = await getConversationContext(userSession.user_id, env);
      }

      // 4. PROMPT SANITIZATION - Edge Goblin #2
      let modifiedRequest = request;
      if (request.method === "POST" && (url.pathname.includes("/chat") || url.pathname.includes("/api"))) {
        const sanitizeResult = await sanitizePrompt(request);
        if (sanitizeResult.blocked) {
          ctx.waitUntil(logSecurityEvent(clientIP, "prompt_blocked", sanitizeResult.reason, env));
          return new Response(
            JSON.stringify({
              error: "Request blocked",
              reason: "Your request contains potentially harmful content",
            }),
            {
              status: 400,
              headers: { "Content-Type": "application/json" },
            }
          );
        }
        if (sanitizeResult.modified) {
          modifiedRequest = sanitizeResult.request;
        }
      }

      // 5. SIMPLE CRUD CACHING - Edge Goblin #3
      // Cache GET requests for non-user-specific data
      if (request.method === "GET" && shouldCache(url)) {
        const cacheKey = `cache:${url.pathname}${url.search}`;
        const cached = env.GOBLIN_CACHE ? await env.GOBLIN_CACHE.get(cacheKey, "json") : null;
        if (cached) {
          ctx.waitUntil(logAnalytics(request, clientIP, "cache_hit", Date.now() - startTime, env));
          return new Response(JSON.stringify(cached), {
            headers: {
              "Content-Type": "application/json",
              "X-Cache": "HIT",
              "X-Goblin-Edge": "active",
            },
          });
        }
      }

      // 6. PROXY TO BACKEND
      const backendUrl = env.API_URL || "http://localhost:8000";
      const backendRequest = new Request(
        `${backendUrl}${url.pathname}${url.search}`,
        modifiedRequest
      );

      // Add context headers for backend
      if (conversationContext) {
        backendRequest.headers.set("X-Conversation-Context", JSON.stringify(conversationContext));
      }
      if (userSession) {
        backendRequest.headers.set("X-User-Id", userSession.user_id);
      }

      const response = await fetch(backendRequest);
      const responseData = await response.clone().text();

      // Cache successful GET responses
      if (request.method === "GET" && response.ok && shouldCache(url) && env.GOBLIN_CACHE) {
        ctx.waitUntil(
          env.GOBLIN_CACHE.put(
            `cache:${url.pathname}${url.search}`,
            responseData,
            { expirationTtl: 300 } // 5 minutes
          )
        );
      }

      // Update conversation context if chat response
      if (userSession && url.pathname.includes("/chat") && response.ok) {
        ctx.waitUntil(updateConversationContext(userSession.user_id, responseData, env));
      }

      // 7. ANALYTICS - Edge Goblin #4 (Async, KV storage)
      const duration = Date.now() - startTime;
      ctx.waitUntil(logAnalytics(request, clientIP, "request_complete", duration, env));

      // Add edge headers
      const newResponse = new Response(responseData, response);
      newResponse.headers.set("X-Goblin-Edge", "active");
      newResponse.headers.set("X-Response-Time", `${duration}ms`);
      newResponse.headers.set("X-Cache", "MISS");

      return newResponse;

    } catch (error) {
      ctx.waitUntil(logAnalytics(request, clientIP, "error", Date.now() - startTime, env, error.message));
      return new Response(
        JSON.stringify({ error: "Internal server error" }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  },
};

// RATE LIMITING LOGIC
async function checkRateLimit(clientIP, env) {
  if (!env.GOBLIN_CACHE) {
    return { allowed: true }; // No cache, allow all requests
  }

  const key = `ratelimit:${clientIP}`;
  const current = await env.GOBLIN_CACHE.get(key);

  if (!current) {
    // First request in window
    await env.GOBLIN_CACHE.put(key, "1", { expirationTtl: RATE_LIMIT_WINDOW });
    return { allowed: true, remaining: RATE_LIMIT_MAX_REQUESTS - 1 };
  }

  const count = parseInt(current, 10);
  if (count >= RATE_LIMIT_MAX_REQUESTS) {
    return { allowed: false, retry_after: RATE_LIMIT_WINDOW };
  }

  // Increment counter
  await env.GOBLIN_CACHE.put(key, (count + 1).toString(), { expirationTtl: RATE_LIMIT_WINDOW });
  return { allowed: true, remaining: RATE_LIMIT_MAX_REQUESTS - count - 1 };
}

// PROMPT SANITIZATION LOGIC
async function sanitizePrompt(request) {
  try {
    const contentType = request.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      return { modified: false, request };
    }

    const body = await request.json();
    let blocked = false;
    let reason = "";

    // Check messages for forbidden patterns
    if (body.messages && Array.isArray(body.messages)) {
      for (const message of body.messages) {
        if (message.content) {
          for (const pattern of FORBIDDEN_PATTERNS) {
            if (pattern.test(message.content)) {
              blocked = true;
              reason = "Forbidden pattern detected in prompt";
              break;
            }
          }
        }
      }

      // Basic sanitization: trim whitespace, limit length
      body.messages = body.messages.map((msg) => ({
        ...msg,
        content: msg.content ? msg.content.trim().slice(0, 10000) : msg.content,
      }));
    }

    if (blocked) {
      return { blocked: true, reason };
    }

    // Create modified request with sanitized body
    const modifiedRequest = new Request(request.url, {
      method: request.method,
      headers: request.headers,
      body: JSON.stringify(body),
    });

    return { modified: true, request: modifiedRequest };
  } catch (e) {
    // If we can't parse, pass through original request
    return { modified: false, request };
  }
}

// CACHING LOGIC
function shouldCache(url) {
  // Cache non-sensitive GET endpoints
  const cachePaths = ["/health", "/models", "/providers", "/settings"];
  return cachePaths.some((path) => url.pathname.startsWith(path));
}

// ANALYTICS LOGGING
async function logAnalytics(request, clientIP, eventType, duration, env, errorMessage = null) {
  const event = {
    timestamp: new Date().toISOString(),
    ip: clientIP,
    method: request.method,
    path: new URL(request.url).pathname,
    event_type: eventType,
    duration_ms: duration,
    user_agent: request.headers.get("user-agent") || "unknown",
    error: errorMessage,
  };

  // Log to KV for simple analytics (or send to external service)
  if (env.GOBLIN_CACHE) {
    const analyticsKey = `analytics:${Date.now()}:${clientIP}`;
    await env.GOBLIN_CACHE.put(analyticsKey, JSON.stringify(event), {
      expirationTtl: 86400, // 24 hours
    });
  }

  // In production, you'd send to analytics service (e.g., Datadog, LogFlare)
  // await fetch("https://your-analytics-endpoint.com", {
  //   method: "POST",
  //   body: JSON.stringify(event),
  // });
}

// SECURITY EVENT LOGGING
async function logSecurityEvent(clientIP, eventType, reason, env) {
  const event = {
    timestamp: new Date().toISOString(),
    ip: clientIP,
    event_type: eventType,
    reason,
  };

  if (env.GOBLIN_CACHE) {
    const securityKey = `security:${Date.now()}:${clientIP}`;
    await env.GOBLIN_CACHE.put(securityKey, JSON.stringify(event), {
      expirationTtl: 86400 * 7, // 7 days
    });
  }
}

// FEATURE FLAGS - Memory Shard #1
async function getFeatureFlags(env) {
  if (!env.GOBLIN_CACHE) {
    return {
      api_enabled: true,
      rate_limiting_enabled: true,
      caching_enabled: true,
    };
  }

  const cached = await env.GOBLIN_CACHE.get("feature_flags", "json");
  if (cached) {
    return cached;
  }

  // Default flags
  const defaultFlags = {
    api_enabled: true,
    rate_limiting_enabled: true,
    caching_enabled: true,
    new_ui_enabled: false,
    experimental_features: false,
  };

  // Cache for 5 minutes
  await env.GOBLIN_CACHE.put("feature_flags", JSON.stringify(defaultFlags), {
    expirationTtl: 300,
  });

  return defaultFlags;
}

// USER SESSION STATE - Memory Shard #2
async function getUserSession(sessionToken, env) {
  if (!env.GOBLIN_CACHE || !sessionToken) {
    return null;
  }

  const sessionKey = `session:${sessionToken}`;
  const session = await env.GOBLIN_CACHE.get(sessionKey, "json");

  if (!session) {
    return null;
  }

  // Check if session is expired
  if (session.expires_at && new Date(session.expires_at) < new Date()) {
    await env.GOBLIN_CACHE.delete(sessionKey);
    return { ...session, expired: true };
  }

  return session;
}

// CONVERSATION CONTEXT CACHING - Memory Shard #3
async function getConversationContext(userId, env) {
  if (!env.GOBLIN_CACHE || !userId) {
    return null;
  }

  const contextKey = `conversation:${userId}`;
  const context = await env.GOBLIN_CACHE.get(contextKey, "json");

  return context || { messages: [], last_updated: null };
}

// UPDATE CONVERSATION CONTEXT - Memory Shard #3
async function updateConversationContext(userId, responseData, env) {
  if (!env.GOBLIN_CACHE || !userId) {
    return;
  }

  try {
    const response = JSON.parse(responseData);
    const contextKey = `conversation:${userId}`;

    // Get existing context
    const existing = await getConversationContext(userId, env);

    // Store last 10 messages only (non-sensitive summary)
    const newContext = {
      messages: [...(existing.messages || []), {
        timestamp: new Date().toISOString(),
        preview: response.message?.substring(0, 100) || "...",
      }].slice(-10),
      last_updated: new Date().toISOString(),
    };

    // Store for 1 hour
    await env.GOBLIN_CACHE.put(contextKey, JSON.stringify(newContext), {
      expirationTtl: 3600,
    });
  } catch (e) {
    // Ignore parsing errors
  }
}

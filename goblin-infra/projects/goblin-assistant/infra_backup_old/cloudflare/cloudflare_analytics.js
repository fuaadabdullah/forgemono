/**
 * Cloudflare Analytics Helper - Free Observability
 *
 * Provides comprehensive telemetry collection using Cloudflare Analytics Engine
 * as a free fallback/complement to Datadog.
 *
 * Features:
 * - Request latency tracking
 * - Error rates and status codes
 * - Geographic distribution
 * - Cache hit ratios
 * - LLM provider performance
 * - Endpoint usage patterns
 */

export class CloudflareAnalytics {
  constructor(env, request) {
    this.analytics = env.GOBLIN_ANALYTICS;
    this.request = request;
    this.startTime = Date.now();
  }

  /**
   * Track request completion with full telemetry
   * @param {Response} response - HTTP response object
   * @param {Object} metadata - Additional tracking data
   */
  async trackRequest(response, metadata = {}) {
    const latency = Date.now() - this.startTime;
    const cf = this.request.cf || {};

    const dataPoint = {
      // Timing
      blobs: [
        `${latency}`, // Request latency in ms
        cf.colo || 'unknown', // Cloudflare datacenter
        cf.country || 'unknown', // User country
        cf.city || 'unknown', // User city
        metadata.endpoint || this.getEndpoint(), // API endpoint
        metadata.provider || 'none', // LLM provider (groq, openai, etc)
        metadata.model || 'none', // LLM model
        metadata.cacheStatus || 'miss' // Cache hit/miss
      ],
      doubles: [
        latency, // p50, p95, p99 latency
        response.status, // Status code
        metadata.llmLatency || 0, // LLM-specific latency
        metadata.tokensUsed || 0, // Token usage
        metadata.cacheHit ? 1 : 0 // Cache hit (1) or miss (0)
      ],
      indexes: [
        response.status.toString(), // Group by status
        metadata.endpoint || 'unknown', // Group by endpoint
        metadata.provider || 'unknown', // Group by provider
        cf.country || 'unknown' // Group by country
      ]
    };

    try {
      await this.analytics.writeDataPoint(dataPoint);
    } catch (error) {
      // Fail silently - analytics shouldn't break the app
      console.error('Analytics write failed:', error);
    }
  }

  /**
   * Track error with context
   * @param {Error} error - Error object
   * @param {Object} context - Error context
   */
  async trackError(error, context = {}) {
    const latency = Date.now() - this.startTime;
    const cf = this.request.cf || {};

    const dataPoint = {
      blobs: [
        `${latency}`,
        cf.colo || 'unknown',
        cf.country || 'unknown',
        cf.city || 'unknown',
        context.endpoint || this.getEndpoint(),
        error.name || 'Error',
        error.message?.substring(0, 100) || 'Unknown error',
        context.provider || 'none'
      ],
      doubles: [
        latency,
        context.statusCode || 500,
        0, // No LLM latency on errors
        0, // No tokens used
        0  // Not a cache hit
      ],
      indexes: [
        'error',
        context.endpoint || 'unknown',
        error.name || 'Error',
        cf.country || 'unknown'
      ]
    };

    try {
      await this.analytics.writeDataPoint(dataPoint);
    } catch (err) {
      console.error('Analytics error tracking failed:', err);
    }
  }

  /**
   * Track cache performance
   * @param {string} key - Cache key
   * @param {boolean} hit - Whether cache was hit
   * @param {number} lookupTime - Cache lookup time in ms
   */
  async trackCache(key, hit, lookupTime = 0) {
    const cf = this.request.cf || {};

    const dataPoint = {
      blobs: [
        `${lookupTime}`,
        cf.colo || 'unknown',
        key.substring(0, 50), // Truncated cache key
        hit ? 'hit' : 'miss',
        this.getEndpoint(),
        'cache-lookup',
        'n/a',
        'n/a'
      ],
      doubles: [
        lookupTime,
        200, // Cache lookups are always 200 internally
        0,
        0,
        hit ? 1 : 0
      ],
      indexes: [
        'cache',
        hit ? 'hit' : 'miss',
        this.getEndpoint(),
        cf.colo || 'unknown'
      ]
    };

    try {
      await this.analytics.writeDataPoint(dataPoint);
    } catch (error) {
      console.error('Analytics cache tracking failed:', error);
    }
  }

  /**
   * Track LLM inference performance
   * @param {Object} inference - LLM inference details
   */
  async trackLLMInference(inference) {
    const cf = this.request.cf || {};

    const dataPoint = {
      blobs: [
        `${inference.latency || 0}`,
        cf.colo || 'unknown',
        cf.country || 'unknown',
        cf.city || 'unknown',
        '/api/inference',
        inference.provider || 'unknown',
        inference.model || 'unknown',
        inference.cached ? 'hit' : 'miss'
      ],
      doubles: [
        inference.totalLatency || 0, // Total request latency
        200, // Assume success (override if error)
        inference.latency || 0, // LLM-specific latency
        inference.tokensUsed || 0,
        inference.cached ? 1 : 0
      ],
      indexes: [
        'llm-inference',
        inference.provider || 'unknown',
        inference.model || 'unknown',
        cf.country || 'unknown'
      ]
    };

    try {
      await this.analytics.writeDataPoint(dataPoint);
    } catch (error) {
      console.error('Analytics LLM tracking failed:', error);
    }
  }

  /**
   * Get endpoint from request URL
   */
  getEndpoint() {
    try {
      const url = new URL(this.request.url);
      return url.pathname;
    } catch {
      return 'unknown';
    }
  }

  /**
   * Get geographic data from request
   */
  getGeoData() {
    const cf = this.request.cf || {};
    return {
      country: cf.country || 'unknown',
      city: cf.city || 'unknown',
      region: cf.region || 'unknown',
      continent: cf.continent || 'unknown',
      latitude: cf.latitude || 0,
      longitude: cf.longitude || 0,
      timezone: cf.timezone || 'UTC',
      colo: cf.colo || 'unknown' // Cloudflare datacenter
    };
  }
}

/**
 * Middleware to automatically track all requests
 *
 * Usage:
 * import { withAnalytics } from './cloudflare_analytics.js';
 *
 * export default {
 *   async fetch(request, env, ctx) {
 *     return withAnalytics(request, env, ctx, async (analytics) => {
 *       // Your handler code
 *       const response = new Response('OK');
 *
 *       // Track before returning
 *       await analytics.trackRequest(response, {
 *         endpoint: '/api/chat',
 *         provider: 'groq',
 *         model: 'llama-3.1-8b'
 *       });
 *
 *       return response;
 *     });
 *   }
 * }
 */
export async function withAnalytics(request, env, ctx, handler) {
  const analytics = new CloudflareAnalytics(env, request);

  try {
    const response = await handler(analytics);

    // Auto-track if handler didn't already track
    if (!response._analyticsTracked) {
      await analytics.trackRequest(response);
    }

    return response;
  } catch (error) {
    // Track error
    await analytics.trackError(error);
    throw error;
  }
}

/**
 * Query Analytics from Worker (for dashboards)
 *
 * Note: Analytics Engine is write-only from Workers.
 * Queries must be done via GraphQL API or Dashboard.
 *
 * See: https://developers.cloudflare.com/analytics/analytics-engine/sql-api/
 */
export const ANALYTICS_QUERIES = {
  // Average latency by endpoint (last 24h)
  latencyByEndpoint: `
    SELECT
      index1 as endpoint,
      AVG(double1) as avg_latency_ms,
      QUANTILE(double1, 0.95) as p95_latency_ms,
      QUANTILE(double1, 0.99) as p99_latency_ms,
      COUNT(*) as requests
    FROM GOBLIN_ANALYTICS
    WHERE timestamp > NOW() - INTERVAL '24' HOUR
    GROUP BY endpoint
    ORDER BY requests DESC
  `,

  // Error rate by endpoint
  errorRate: `
    SELECT
      index1 as endpoint,
      SUM(CASE WHEN double2 >= 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate,
      COUNT(*) as total_requests,
      SUM(CASE WHEN double2 >= 500 THEN 1 ELSE 0 END) as server_errors
    FROM GOBLIN_ANALYTICS
    WHERE timestamp > NOW() - INTERVAL '1' HOUR
    GROUP BY endpoint
  `,

  // Geographic distribution
  geoDistribution: `
    SELECT
      blob3 as country,
      COUNT(*) as requests,
      AVG(double1) as avg_latency_ms
    FROM GOBLIN_ANALYTICS
    WHERE timestamp > NOW() - INTERVAL '24' HOUR
    GROUP BY country
    ORDER BY requests DESC
    LIMIT 20
  `,

  // Cache hit ratio
  cacheHitRatio: `
    SELECT
      index1 as endpoint,
      SUM(double5) * 100.0 / COUNT(*) as cache_hit_rate,
      COUNT(*) as total_requests,
      SUM(double5) as cache_hits
    FROM GOBLIN_ANALYTICS
    WHERE timestamp > NOW() - INTERVAL '1' HOUR
      AND index1 != 'error'
    GROUP BY endpoint
  `,

  // LLM provider performance
  llmPerformance: `
    SELECT
      index2 as provider,
      index3 as model,
      AVG(double3) as avg_llm_latency_ms,
      QUANTILE(double3, 0.95) as p95_llm_latency_ms,
      SUM(double4) as total_tokens,
      COUNT(*) as requests
    FROM GOBLIN_ANALYTICS
    WHERE timestamp > NOW() - INTERVAL '24' HOUR
      AND index1 = 'llm-inference'
    GROUP BY provider, model
    ORDER BY requests DESC
  `
};

/**
 * Example integration in worker:
 *
 * import { CloudflareAnalytics } from './cloudflare_analytics.js';
 *
 * export default {
 *   async fetch(request, env, ctx) {
 *     const analytics = new CloudflareAnalytics(env, request);
 *
 *     try {
 *       // Your logic here
 *       const response = await handleRequest(request);
 *
 *       // Track success
 *       await analytics.trackRequest(response, {
 *         endpoint: '/api/chat',
 *         provider: 'groq',
 *         model: 'llama-3.1-8b',
 *         cacheStatus: 'hit',
 *         tokensUsed: 150
 *       });
 *
 *       return response;
 *     } catch (error) {
 *       // Track error
 *       await analytics.trackError(error, {
 *         endpoint: '/api/chat',
 *         statusCode: 500
 *       });
 *
 *       return new Response('Internal Server Error', { status: 500 });
 *     }
 *   }
 * }
 */

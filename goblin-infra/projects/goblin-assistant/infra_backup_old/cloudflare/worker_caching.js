/**
 * Cloudflare Worker - Enhanced Caching for Frontend Performance
 *
 * This worker adds aggressive caching rules for static assets,
 * UI bundles, and API responses to make the app feel instant.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cache = caches.default;

    // Define caching strategies by path pattern
    const cacheConfig = getCacheConfig(url.pathname);

    // Try to serve from cache first
    let response = await cache.match(request);

    if (response) {
      // Cache hit! Add header to indicate
      response = new Response(response.body, response);
      response.headers.set('X-Cache', 'HIT');
      response.headers.set('X-Cache-Age', getAge(response));
      return response;
    }

    // Cache miss - fetch from origin
    response = await fetch(request);

    // Clone response for caching (can only read body once)
    const responseToCache = response.clone();

    // Apply caching rules
    if (cacheConfig.shouldCache && response.ok) {
      const cachedResponse = new Response(responseToCache.body, responseToCache);

      // Set cache headers
      cachedResponse.headers.set('Cache-Control', cacheConfig.cacheControl);
      cachedResponse.headers.set('X-Cache', 'MISS');
      cachedResponse.headers.set('X-Cache-Rule', cacheConfig.rule);

      // Store in Cloudflare cache
      const cacheKey = new Request(url.toString(), request);
      await cache.put(cacheKey, cachedResponse.clone());

      return cachedResponse;
    }

    // Don't cache, return as-is
    response.headers.set('X-Cache', 'BYPASS');
    return response;
  }
};

/**
 * Get caching configuration based on URL path
 */
function getCacheConfig(pathname) {
  // Static assets - cache for 1 year (immutable)
  if (pathname.match(/\.(js|css|woff2?|ttf|eot|ico|svg|png|jpg|jpeg|webp|gif|mp4|webm)$/i)) {
    return {
      shouldCache: true,
      cacheControl: 'public, max-age=31536000, immutable',
      rule: 'static-assets-immutable'
    };
  }

  // Versioned bundles (with hash in filename)
  if (pathname.match(/\.[a-f0-9]{8,}\.(js|css)$/i)) {
    return {
      shouldCache: true,
      cacheControl: 'public, max-age=31536000, immutable',
      rule: 'versioned-bundles'
    };
  }

  // Vite/Webpack chunks
  if (pathname.includes('/assets/') || pathname.includes('/chunks/')) {
    return {
      shouldCache: true,
      cacheControl: 'public, max-age=31536000, immutable',
      rule: 'build-chunks'
    };
  }

  // HTML pages - short cache with revalidation
  if (pathname.endsWith('/') || pathname.endsWith('.html') || !pathname.includes('.')) {
    return {
      shouldCache: true,
      cacheControl: 'public, max-age=300, must-revalidate',
      rule: 'html-pages'
    };
  }

  // API responses - short cache for GET requests only
  if (pathname.startsWith('/api/')) {
    return {
      shouldCache: false, // Handle in API worker instead
      cacheControl: 'no-cache',
      rule: 'api-bypass'
    };
  }

  // Goblin typing effects / animations (precomputed)
  if (pathname.includes('/animations/') || pathname.includes('/effects/')) {
    return {
      shouldCache: true,
      cacheControl: 'public, max-age=86400, stale-while-revalidate=604800',
      rule: 'animations-effects'
    };
  }

  // Fonts - cache aggressively
  if (pathname.includes('/fonts/')) {
    return {
      shouldCache: true,
      cacheControl: 'public, max-age=31536000, immutable',
      rule: 'fonts'
    };
  }

  // Default - short cache
  return {
    shouldCache: true,
    cacheControl: 'public, max-age=3600',
    rule: 'default'
  };
}

/**
 * Get age of cached response
 */
function getAge(response) {
  const date = response.headers.get('Date');
  if (!date) return 'unknown';

  const age = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  return `${age}s`;
}

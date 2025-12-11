/**
 * Auth caching utilities for persistent storage and session management
 */

import { User, UserSession } from '../types/api';

const AUTH_CACHE_KEY = 'goblin-auth-cache';
const SESSIONS_CACHE_KEY = 'goblin-sessions-cache';
const CACHE_EXPIRY_KEY = 'goblin-cache-expiry';

interface AuthCacheData {
  user: User | null;
  sessions: UserSession[];
  lastRefresh: string | null;
  timestamp: number;
}

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxAge?: number; // Maximum age in milliseconds
}

/**
 * Auth cache utility for managing persistent auth state
 */
export class AuthCache {
  private static readonly DEFAULT_TTL = 24 * 60 * 60 * 1000; // 24 hours

  /**
   * Save auth data to cache
   */
  static save(data: Partial<AuthCacheData>, options: CacheOptions = {}): void {
    try {
      const cacheData: AuthCacheData = {
        user: data.user || null,
        sessions: data.sessions || [],
        lastRefresh: data.lastRefresh || null,
        timestamp: Date.now(),
      };

      const ttl = options.ttl || this.DEFAULT_TTL;
      const expiry = Date.now() + ttl;

      localStorage.setItem(AUTH_CACHE_KEY, JSON.stringify(cacheData));
      localStorage.setItem(CACHE_EXPIRY_KEY, expiry.toString());
    } catch (error) {
      console.warn('Failed to save auth cache:', error);
    }
  }

  /**
   * Load auth data from cache
   */
  static load(options: CacheOptions = {}): AuthCacheData | null {
    try {
      const cacheData = localStorage.getItem(AUTH_CACHE_KEY);
      const expiry = localStorage.getItem(CACHE_EXPIRY_KEY);

      if (!cacheData || !expiry) {
        return null;
      }

      const expiryTime = parseInt(expiry, 10);
      const maxAge = options.maxAge;

      // Check if cache has expired
      if (Date.now() > expiryTime) {
        this.clear();
        return null;
      }

      // Check maximum age if specified
      if (maxAge) {
        const parsed = JSON.parse(cacheData) as AuthCacheData;
        if (Date.now() - parsed.timestamp > maxAge) {
          this.clear();
          return null;
        }
      }

      return JSON.parse(cacheData) as AuthCacheData;
    } catch (error) {
      console.warn('Failed to load auth cache:', error);
      this.clear();
      return null;
    }
  }

  /**
   * Update specific fields in cache
   */
  static update(updates: Partial<AuthCacheData>): void {
    const current = this.load();
    if (current) {
      this.save({ ...current, ...updates });
    }
  }

  /**
   * Clear auth cache
   */
  static clear(): void {
    try {
      localStorage.removeItem(AUTH_CACHE_KEY);
      localStorage.removeItem(CACHE_EXPIRY_KEY);
      localStorage.removeItem(SESSIONS_CACHE_KEY);
    } catch (error) {
      console.warn('Failed to clear auth cache:', error);
    }
  }

  /**
   * Check if cache is valid
   */
  static isValid(options: CacheOptions = {}): boolean {
    return this.load(options) !== null;
  }
}

/**
 * Session-specific cache utilities
 */
export class SessionCache {
  private static readonly SESSIONS_TTL = 5 * 60 * 1000; // 5 minutes for sessions

  /**
   * Cache sessions data
   */
  static saveSessions(sessions: UserSession[]): void {
    try {
      const cacheData = {
        sessions,
        timestamp: Date.now(),
        expiry: Date.now() + this.SESSIONS_TTL,
      };

      localStorage.setItem(SESSIONS_CACHE_KEY, JSON.stringify(cacheData));
    } catch (error) {
      console.warn('Failed to save sessions cache:', error);
    }
  }

  /**
   * Load cached sessions
   */
  static loadSessions(): UserSession[] | null {
    try {
      const cacheData = localStorage.getItem(SESSIONS_CACHE_KEY);
      if (!cacheData) return null;

      const parsed = JSON.parse(cacheData);
      if (Date.now() > parsed.expiry) {
        localStorage.removeItem(SESSIONS_CACHE_KEY);
        return null;
      }

      return parsed.sessions;
    } catch (error) {
      console.warn('Failed to load sessions cache:', error);
      return null;
    }
  }

  /**
   * Clear sessions cache
   */
  static clearSessions(): void {
    try {
      localStorage.removeItem(SESSIONS_CACHE_KEY);
    } catch (error) {
      console.warn('Failed to clear sessions cache:', error);
    }
  }
}

/**
 * Cache invalidation utilities
 */
export class CacheInvalidation {
  /**
   * Invalidate all auth-related caches
   */
  static invalidateAll(): void {
    AuthCache.clear();
    SessionCache.clearSessions();
  }

  /**
   * Invalidate user-specific caches
   */
  static invalidateUser(): void {
    AuthCache.update({ user: null });
    SessionCache.clearSessions();
  }

  /**
   * Invalidate session-specific caches
   */
  static invalidateSessions(): void {
    AuthCache.update({ sessions: [] });
    SessionCache.clearSessions();
  }
}

/**
 * Cache statistics and monitoring
 */
export class CacheStats {
  static getStats(): {
    authCacheSize: number;
    sessionsCacheSize: number;
    authCacheExpiry: number | null;
    sessionsCacheExpiry: number | null;
  } {
    try {
      const authData = localStorage.getItem(AUTH_CACHE_KEY);
      const sessionsData = localStorage.getItem(SESSIONS_CACHE_KEY);
      const expiry = localStorage.getItem(CACHE_EXPIRY_KEY);

      return {
        authCacheSize: authData ? new Blob([authData]).size : 0,
        sessionsCacheSize: sessionsData ? new Blob([sessionsData]).size : 0,
        authCacheExpiry: expiry ? parseInt(expiry, 10) : null,
        sessionsCacheExpiry: sessionsData ? JSON.parse(sessionsData).expiry : null,
      };
    } catch (error) {
      return {
        authCacheSize: 0,
        sessionsCacheSize: 0,
        authCacheExpiry: null,
        sessionsCacheExpiry: null,
      };
    }
  }

  static isExpired(): boolean {
    const stats = this.getStats();
    const now = Date.now();
    return (
      (stats.authCacheExpiry !== null && now > stats.authCacheExpiry) ||
      (stats.sessionsCacheExpiry !== null && now > stats.sessionsCacheExpiry)
    );
  }
}

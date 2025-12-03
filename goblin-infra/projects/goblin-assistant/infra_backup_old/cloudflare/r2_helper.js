/**
 * R2 Storage Helper - Cheap storage for Goblin Assistant
 * 
 * Provides utilities for uploading/downloading files to Cloudflare R2
 * Saves 86% vs AWS S3 (free egress!)
 */

export class R2Storage {
  constructor(env) {
    this.audio = env.GOBLIN_AUDIO;
    this.logs = env.GOBLIN_LOGS;
    this.uploads = env.GOBLIN_UPLOADS;
    this.training = env.GOBLIN_TRAINING;
    this.cache = env.GOBLIN_CACHE_R2;
  }

  /**
   * Upload audio file (TTS output, voice recordings)
   * @param {string} key - File path (e.g., "tts/2024-12-02/response_abc123.mp3")
   * @param {ArrayBuffer|ReadableStream} data - Audio data
   * @param {Object} metadata - Optional metadata (contentType, userId, etc.)
   */
  async uploadAudio(key, data, metadata = {}) {
    return await this.audio.put(key, data, {
      httpMetadata: {
        contentType: metadata.contentType || 'audio/mpeg',
        contentDisposition: `inline; filename="${this.getFileName(key)}"`,
      },
      customMetadata: {
        uploadedAt: new Date().toISOString(),
        userId: metadata.userId || 'anonymous',
        source: metadata.source || 'tts',
        ...metadata
      }
    });
  }

  /**
   * Get audio file URL (for streaming/playback)
   * @param {string} key - File path
   * @returns {Promise<string>} - Public URL
   */
  async getAudioUrl(key) {
    const object = await this.audio.head(key);
    if (!object) return null;
    
    // R2 public bucket URL (configure in Cloudflare Dashboard)
    return `https://audio.goblin.fuaad.ai/${key}`;
  }

  /**
   * Upload log file (application logs, error traces)
   * @param {string} key - Log path (e.g., "error/2024-12-02/app_12345.log")
   * @param {string} logData - Log content
   */
  async uploadLog(key, logData) {
    return await this.logs.put(key, logData, {
      httpMetadata: {
        contentType: 'text/plain; charset=utf-8',
      },
      customMetadata: {
        timestamp: new Date().toISOString(),
        compressed: 'false'
      }
    });
  }

  /**
   * Upload user file (reference docs, images)
   * @param {string} userId - User ID
   * @param {string} fileName - Original filename
   * @param {ArrayBuffer|ReadableStream} data - File data
   * @param {Object} metadata - File metadata
   */
  async uploadUserFile(userId, fileName, data, metadata = {}) {
    const safeFileName = this.sanitizeFileName(fileName);
    const key = `users/${userId}/${Date.now()}_${safeFileName}`;
    
    return await this.uploads.put(key, data, {
      httpMetadata: {
        contentType: metadata.contentType || 'application/octet-stream',
        contentDisposition: `attachment; filename="${safeFileName}"`,
      },
      customMetadata: {
        uploadedAt: new Date().toISOString(),
        userId: userId,
        originalName: fileName,
        fileSize: metadata.fileSize || 0,
        ...metadata
      }
    });
  }

  /**
   * Get user file
   * @param {string} key - File key
   * @returns {Promise<R2Object>}
   */
  async getUserFile(key) {
    return await this.uploads.get(key);
  }

  /**
   * Delete user file
   * @param {string} key - File key
   */
  async deleteUserFile(key) {
    await this.uploads.delete(key);
  }

  /**
   * List user files
   * @param {string} userId - User ID
   * @returns {Promise<Array>}
   */
  async listUserFiles(userId) {
    const prefix = `users/${userId}/`;
    const list = await this.uploads.list({ prefix });
    return list.objects.map(obj => ({
      key: obj.key,
      size: obj.size,
      uploaded: obj.uploaded,
      fileName: this.getFileName(obj.key)
    }));
  }

  /**
   * Upload training artifact (model weights, embeddings)
   * @param {string} key - Artifact path (e.g., "fine-tuning/model_v1.safetensors")
   * @param {ArrayBuffer|ReadableStream} data - Artifact data
   * @param {Object} metadata - Training metadata
   */
  async uploadTrainingArtifact(key, data, metadata = {}) {
    return await this.training.put(key, data, {
      httpMetadata: {
        contentType: 'application/octet-stream',
      },
      customMetadata: {
        uploadedAt: new Date().toISOString(),
        modelVersion: metadata.modelVersion || 'unknown',
        trainingRun: metadata.trainingRun || 'manual',
        ...metadata
      }
    });
  }

  /**
   * Cache LLM response (overflow from KV)
   * @param {string} key - Cache key
   * @param {Object} response - LLM response data
   * @param {number} ttl - Time to live in seconds (default 7 days)
   */
  async cacheResponse(key, response, ttl = 604800) {
    const expiresAt = new Date(Date.now() + ttl * 1000).toISOString();
    
    return await this.cache.put(key, JSON.stringify(response), {
      httpMetadata: {
        contentType: 'application/json',
      },
      customMetadata: {
        cachedAt: new Date().toISOString(),
        expiresAt: expiresAt,
        ttl: ttl.toString()
      }
    });
  }

  /**
   * Get cached response
   * @param {string} key - Cache key
   * @returns {Promise<Object|null>}
   */
  async getCachedResponse(key) {
    const object = await this.cache.get(key);
    if (!object) return null;

    // Check expiration
    const metadata = object.customMetadata;
    if (metadata?.expiresAt && new Date(metadata.expiresAt) < new Date()) {
      await this.cache.delete(key); // Expired, delete
      return null;
    }

    return JSON.parse(await object.text());
  }

  /**
   * Get storage stats (for monitoring)
   */
  async getStats() {
    const buckets = [
      { name: 'audio', bucket: this.audio },
      { name: 'logs', bucket: this.logs },
      { name: 'uploads', bucket: this.uploads },
      { name: 'training', bucket: this.training },
      { name: 'cache', bucket: this.cache }
    ];

    const stats = await Promise.all(
      buckets.map(async ({ name, bucket }) => {
        const list = await bucket.list({ limit: 1000 });
        const totalSize = list.objects.reduce((sum, obj) => sum + obj.size, 0);
        return {
          bucket: name,
          objects: list.objects.length,
          size: this.formatBytes(totalSize),
          truncated: list.truncated
        };
      })
    );

    return stats;
  }

  // Utility functions
  sanitizeFileName(fileName) {
    return fileName.replace(/[^a-zA-Z0-9._-]/g, '_');
  }

  getFileName(key) {
    return key.split('/').pop();
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
}

/**
 * Example usage in Worker:
 * 
 * import { R2Storage } from './r2_helper.js';
 * 
 * export default {
 *   async fetch(request, env) {
 *     const storage = new R2Storage(env);
 *     
 *     // Upload TTS audio
 *     await storage.uploadAudio(
 *       'tts/2024-12-02/response_abc123.mp3',
 *       audioBuffer,
 *       { userId: 'user123', source: 'elevenlabs' }
 *     );
 *     
 *     // Get audio URL for playback
 *     const url = await storage.getAudioUrl('tts/2024-12-02/response_abc123.mp3');
 *     
 *     // Upload user file
 *     await storage.uploadUserFile(
 *       'user123',
 *       'reference.pdf',
 *       fileBuffer,
 *       { contentType: 'application/pdf', fileSize: 1024000 }
 *     );
 *     
 *     // Cache LLM response
 *     await storage.cacheResponse('prompt:abc123', {
 *       model: 'gpt-4',
 *       response: 'Hello!',
 *       tokens: 50
 *     });
 *     
 *     return new Response('OK');
 *   }
 * }
 */

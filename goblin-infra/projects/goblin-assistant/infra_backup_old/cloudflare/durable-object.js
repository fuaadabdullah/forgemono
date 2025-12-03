/**
 * Durable Object for Real-time Chat State
 * Use this for: WebSocket connections, real-time collaboration, stateful sessions
 *
 * Durable Objects are "single-threaded coordinators" - perfect for:
 * - Managing active chat rooms
 * - Coordinating multiple users in the same conversation
 * - Handling WebSocket connections
 * - Rate limiting with precise counts (more accurate than KV)
 */

export class ChatRoom {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.sessions = [];
    this.messageHistory = [];
  }

  async fetch(request) {
    const url = new URL(request.url);

    // Handle WebSocket upgrade
    if (request.headers.get("Upgrade") === "websocket") {
      return this.handleWebSocket(request);
    }

    // Handle HTTP requests
    if (url.pathname === "/history") {
      return new Response(JSON.stringify(this.messageHistory), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (url.pathname === "/stats") {
      return new Response(
        JSON.stringify({
          active_connections: this.sessions.length,
          total_messages: this.messageHistory.length,
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response("Not found", { status: 404 });
  }

  async handleWebSocket(request) {
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);

    await this.handleSession(server);

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }

  async handleSession(websocket) {
    websocket.accept();
    this.sessions.push(websocket);

    // Send history to new connection
    websocket.send(
      JSON.stringify({
        type: "history",
        messages: this.messageHistory,
      })
    );

    websocket.addEventListener("message", async (msg) => {
      try {
        const data = JSON.parse(msg.data);

        // Store message
        this.messageHistory.push({
          timestamp: new Date().toISOString(),
          content: data.content,
          user: data.user,
        });

        // Keep only last 100 messages
        if (this.messageHistory.length > 100) {
          this.messageHistory = this.messageHistory.slice(-100);
        }

        // Broadcast to all connected clients
        this.broadcast(
          JSON.stringify({
            type: "message",
            content: data.content,
            user: data.user,
            timestamp: new Date().toISOString(),
          })
        );
      } catch (err) {
        websocket.send(
          JSON.stringify({ type: "error", message: "Invalid message format" })
        );
      }
    });

    websocket.addEventListener("close", () => {
      this.sessions = this.sessions.filter((s) => s !== websocket);
    });
  }

  broadcast(message) {
    this.sessions.forEach((session) => {
      try {
        session.send(message);
      } catch (err) {
        // Remove dead connections
        this.sessions = this.sessions.filter((s) => s !== session);
      }
    });
  }
}

/**
 * Advanced Rate Limiter using Durable Objects
 * More accurate than KV-based rate limiting
 */
export class RateLimiter {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.requests = [];
  }

  async fetch(request) {
    const url = new URL(request.url);
    const now = Date.now();

    // Clean old requests (older than 1 minute)
    this.requests = this.requests.filter((ts) => now - ts < 60000);

    if (url.pathname === "/check") {
      const limit = 100; // 100 requests per minute
      const allowed = this.requests.length < limit;

      if (allowed) {
        this.requests.push(now);
      }

      return new Response(
        JSON.stringify({
          allowed,
          remaining: Math.max(0, limit - this.requests.length),
          reset_at: new Date(now + 60000).toISOString(),
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response("Not found", { status: 404 });
  }
}

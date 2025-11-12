import Database from 'better-sqlite3';
import { AuditEvent } from './types';
import crypto from 'crypto';

export class AuditLogger {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.initTable();
  }

  private initTable() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS audit_events (
        event_id TEXT PRIMARY KEY,
        request_id TEXT,
        caller_id TEXT,
        tool_id TEXT,
        function_name TEXT,
        args TEXT,
        result_code INTEGER,
        timestamp INTEGER,
        signature TEXT
      )
    `);
  }

  async log(event: Omit<AuditEvent, 'event_id' | 'signature'>) {
    const eventId = crypto.randomUUID();
    const eventData = JSON.stringify(event);
    const signature = crypto.createHmac('sha256', 'secret-key').update(eventData).digest('base64');

    const stmt = this.db.prepare(`
      INSERT INTO audit_events (event_id, request_id, caller_id, tool_id, function_name, args, result_code, timestamp, signature)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      eventId,
      event.request_id,
      event.caller_id,
      event.tool_id,
      event.function_name,
      JSON.stringify(event.args),
      event.result_code,
      event.timestamp,
      signature
    );
  }

  getEvents(requestId?: string) {
    let query = 'SELECT * FROM audit_events';
    if (requestId) {
      query += ' WHERE request_id = ?';
      return this.db.prepare(query).all(requestId);
    }
    return this.db.prepare(query).all();
  }
}
# API Quick Reference

## Current Endpoints

### `/api/raptor/start`

Start the Raptor service for local LLM management.

```bash
curl -X POST http://localhost:8001/api/raptor/start
```

### `/api/raptor/stop`

Stop the Raptor service.

```bash
curl -X POST http://localhost:8001/api/raptor/stop
```

### `/api/raptor/status`

Get current Raptor status.

```bash
curl http://localhost:8001/api/raptor/status
```

Response:

```json
{
  "running": true,
  "config_file": "/path/to/config"
}
```

### `/api/raptor/logs`

Get Raptor logs.

```bash
curl http://localhost:8001/api/raptor/logs
```

Response:

```json
{
  "log_tail": "Recent log entries..."
}
```

### `/api/raptor/demo/{mode}`

Run a Raptor demo in specified mode.

```bash
curl -X POST http://localhost:8001/api/raptor/demo/chat
```

## Frontend Usage

### Basic Raptor Management

```typescript
import { raptorStart, raptorStop, raptorStatus, raptorLogs } from './services/raptor';

// Start Raptor
await raptorStart();

// Check status
const status = await raptorStatus();
console.log('Raptor running:', status.running);

// Get logs
const logs = await raptorLogs();
console.log('Recent logs:', logs.log_tail);

// Stop Raptor
await raptorStop();
```

## Current Implementation Status

### What's Implemented ✅

- Raptor service management (start/stop/status)
- Basic logging functionality
- Demo mode execution

### What's Not Yet Implemented ❌

- Dashboard status endpoints
- Cost tracking and monitoring
- Vector database integration
- Multi-provider orchestration
- Advanced caching systems
- Health checks for multiple services
- Performance metrics and monitoring
- Complex API endpoints with authentication

## Files Changed

### Backend

- `backend/main.py` - FastAPI app with Raptor endpoints
- `backend/database.py` - Database configuration

### Frontend

- `src/services/raptor.ts` - Raptor service client
- `src/api/http-client.ts` - HTTP client configuration

## Status Codes

- `200` - Success
- `500` - Server error (check logs)

## Error Handling

Current endpoints return basic error responses. The system is designed for simplicity and local development use.

## Notes

- This is a basic implementation focused on local LLM management
- No authentication or authorization is currently implemented
- Database support is minimal (SQLite/PostgreSQL for basic data persistence)
- The system is designed for single-user or small team development use

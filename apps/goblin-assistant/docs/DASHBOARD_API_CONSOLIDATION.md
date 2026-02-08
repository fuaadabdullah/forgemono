# Dashboard API Consolidation

**Date**: 2025-01-XX
**Author**: AI Assistant
**Goal**: Basic API endpoints for local LLM assistant dashboard

---

## 📊 Overview

Created basic dashboard endpoints for the Goblin Assistant with simple status monitoring:

- `/api/raptor/status` - Raptor service status
- `/api/raptor/logs` - Raptor service logs
- `/api/raptor/start` - Start Raptor service
- `/api/raptor/stop` - Stop Raptor service

**Current Scope**:

- ✅ **Basic service monitoring** for Raptor local LLM service
- ✅ **Simple API endpoints** for service management
- ✅ **Frontend integration** for status display
- ✅ **Error handling** for service operations

---

## 🏗️ Backend Changes

### 1. Raptor Service Endpoints (`backend/main.py`)

**Purpose**: Basic endpoints for Raptor service management

**Endpoints**:

#### GET `/api/raptor/status`
- **Returns**: Raptor service status
- **Response**:
  ```json
  {
    "running": true,
    "config_file": "/path/to/config"
  }
  ```

#### GET `/api/raptor/logs`
- **Returns**: Recent log entries from Raptor service
- **Response**:
  ```json
  {
    "log_tail": "Recent log entries..."
  }
  ```

#### POST `/api/raptor/start`
- **Action**: Start the Raptor service
- **Response**: Success or error message

#### POST `/api/raptor/stop`
- **Action**: Stop the Raptor service
- **Response**: Success or error message

#### POST `/api/raptor/demo/{mode}`
- **Action**: Run Raptor demo in specified mode
- **Response**: Success or error message

### 2. Database Integration (`backend/database.py`)

**Purpose**: Basic database support for user data and configuration

**Features**:
- SQLite/PostgreSQL support
- Connection pooling for PostgreSQL
- Graceful fallback to SQLite for development
- Vault integration for production credentials

---

## 🎨 Frontend Changes

### 1. API Client Updates (`src/api/http-client.ts`)

**New Methods**:

```typescript
// Raptor service management
async raptorStart(): Promise<void>
async raptorStop(): Promise<void>
async raptorStatus(): Promise<RaptorStatus>
async raptorLogs(): Promise<RaptorLogsResponse>
async raptorDemo(mode: string): Promise<void>
```

### 2. Raptor Service (`src/services/raptor.ts`)

**Purpose**: Frontend service for Raptor management

**Features**:
- Service status monitoring
- Start/stop operations
- Log retrieval
- Demo execution

**Usage**:
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

---

## 📈 Current Implementation Status

### What's Implemented ✅

- Raptor service management endpoints
- Basic database configuration
- Frontend service client
- Error handling for service operations
- Simple status monitoring

### What's Not Yet Implemented ❌

- Multi-service dashboard (vector DB, MCP servers, RAG indexer, sandbox runner)
- Cost tracking and monitoring
- Advanced caching systems
- Performance metrics and monitoring
- Complex API endpoints with authentication
- WebSocket real-time updates
- Aggressive caching strategies

---

## 🧪 Testing

### Backend Testing

```bash
# Start backend
cd apps/goblin-assistant/backend
uvicorn main:app --reload

# Test Raptor endpoints
curl http://localhost:8001/api/raptor/status
curl http://localhost:8001/api/raptor/logs
curl -X POST http://localhost:8001/api/raptor/start
curl -X POST http://localhost:8001/api/raptor/stop
```

### Frontend Testing

```bash
# Start dev server
cd apps/goblin-assistant
pnpm dev

# Test in browser console
import { raptorStatus } from './services/raptor';
const status = await raptorStatus();
console.log('Raptor status:', status);
```

---

## 🚀 Future Enhancements

### 1. Dashboard Expansion

**Current**: Basic Raptor service monitoring
**Proposed**: Multi-service dashboard

```typescript
// Future dashboard structure
interface DashboardStatus {
  backend_api: ServiceStatus;
  raptor_service: ServiceStatus;
  // Future services:
  // vector_db?: ServiceStatus;
  // mcp_servers?: ServiceStatus;
  // rag_indexer?: ServiceStatus;
  // sandbox_runner?: ServiceStatus;
}
```

### 2. Enhanced Monitoring

**Current**: Basic service status
**Proposed**: Detailed metrics and health checks

```python
# Future service checks
async def check_backend_status() -> ServiceStatus
async def check_raptor_status() -> ServiceStatus
# Future checks:
# async def check_vector_db_status() -> ServiceStatus
# async def check_mcp_status() -> ServiceStatus
```

### 3. Caching Strategy

**Current**: No caching
**Proposed**: Simple in-memory caching for status endpoints

```python
class SimpleCache:
    """Thread-safe in-memory cache with TTL"""
    def __init__(self):
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._lock = asyncio.Lock()
```

### 4. Authentication & Security

**Current**: No authentication
**Proposed**: Basic authentication for service endpoints

```python
# Future authentication
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify API token
    pass
```

---

## 📚 Related Documentation

- [Local LLM Routing](./LOCAL_LLM_ROUTING.md) - Model selection and routing logic
- [UX Improvements](./UX_IMPROVEMENTS.md) - Status card enhancements
- [API Quick Reference](./API_QUICK_REF.md) - Current API endpoints

---

## ✅ Checklist

- [x] Create Raptor service endpoints in backend
- [x] Implement basic database configuration
- [x] Create frontend service client
- [x] Add error handling for service operations
- [x] Test basic functionality
- [ ] **TODO**: Add multi-service dashboard support
- [ ] **TODO**: Implement caching for status endpoints
- [ ] **TODO**: Add authentication and security
- [ ] **TODO**: Add performance metrics and monitoring
- [ ] **TODO**: Implement WebSocket real-time updates

---

**Status**: ✅ **BASIC IMPLEMENTATION COMPLETE** - Simple dashboard for Raptor service

**Current Focus**: Basic local LLM service management and monitoring. The system is designed for simplicity and can be extended with additional services and features as needed.

**Next Steps**:
1. Test basic Raptor service functionality
2. Monitor service stability and performance
3. Consider adding additional service monitoring as requirements evolve
4. Evaluate need for advanced features (caching, authentication, real-time updates)

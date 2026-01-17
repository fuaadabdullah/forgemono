# 🚀 Gradual Feature Re-enabling Guide

**Purpose:** Safely re-enable disabled features without breaking server stability  
**Approach:** One feature at a time, testing after each change

## 🎯 Re-enabling Priority Order

### Phase 1: Low Risk Features (Start Here)

#### 1. Database Features
**Why First:** Most stable, fewest dependencies  
**Files to modify:** `api/main.py`

**Step 1: Uncomment database import**
```python
# from api.storage.database import init_db  # Uncomment this line
```

**Step 2: Uncomment startup database initialization**
```python
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    try:
        print("🚀 Starting Goblin Assistant API...")
        
        # Initialize database tables (optional for now)
        print("🗄️  Checking database availability...")
        try:
            db_initialized = await init_db()
            if db_initialized:
                print("✅ Database initialized")
            else:
                print("⚠️  Database initialization skipped - running in limited mode")
        except Exception as e:
            print(f"⚠️  Database initialization failed: {e}")
            print("   Continuing without database - some features may be limited")

        print("🎉 Goblin Assistant API startup complete!")

    except Exception as e:
        print(f"❌ Critical startup error: {e}")
        raise
```

**Step 3: Test database functionality**
```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant
python -m uvicorn api.main:app --reload
curl http://localhost:8000/health
```

#### 2. Re-enable Chat Router (Requires Database)
**Step 1: Uncomment chat router**
```python
app.include_router(chat_router)  # Uncomment this line
```

**Step 2: Test chat functionality**
```bash
curl -X POST "http://localhost:8000/chat/conversations" -H "Content-Type: application/json" -d '{}'
```

---

### Phase 2: Medium Risk Features

#### 3. Redis Cache
**Why Second:** Has some dependencies but isolated  
**Files to modify:** `api/main.py`

**Step 1: Uncomment cache import and initialization**
```python
from api.storage.cache import cache  # Uncomment this line
```

**Step 2: Uncomment startup cache initialization**
```python
        # Initialize Redis cache
        print("📦 Initializing Redis cache...")
        try:
            await cache.init_redis()
            print("✅ Redis cache initialized")
        except Exception as e:
            print(f"⚠️  Redis initialization failed: {e}")
            print("   Continuing without Redis cache - performance may be reduced")
```

**Step 3: Test Redis functionality**
```bash
# Check if Redis is running
redis-cli ping

# Test server
python -m uvicorn api.main:app --reload
```

#### 4. Provider Monitoring
**Why Third:** Depends on providers configuration  
**Files to modify:** `api/main.py`, `api/monitoring.py`

**Step 1: Uncomment monitoring import**
```python
from api.monitoring import monitor  # Uncomment this line
```

**Step 2: Uncomment startup monitoring**
```python
        # Start provider monitoring
        print("📊 Starting provider monitoring...")
        try:
            await monitor.start()
            print("✅ Provider monitoring started")
        except Exception as e:
            print(f"⚠️  Provider monitoring failed to start: {e}")
            print("   Continuing without provider monitoring...")
```

**Step 3: Test monitoring functionality**
```bash
# Test if monitoring endpoints work
curl http://localhost:8000/health
```

---

### Phase 3: High Risk Features

#### 5. Middleware (Authentication & Error Handling)
**Why Last:** Can break everything if misconfigured  
**Files to modify:** `api/main.py`

**Step 1: Uncomment middleware imports**
```python
from api.middleware import ErrorHandlingMiddleware, AuthenticationMiddleware  # Uncomment
```

**Step 2: Uncomment middleware registration**
```python
# Add Error Handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add Authentication middleware
app.add_middleware(
    AuthenticationMiddleware,
    exclude_paths=[
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/auth/register",
        "/auth/login",
        "/auth/oauth/google",
        "/auth/oauth/google/callback",
        "/auth/passkey/register",
        "/auth/passkey/authenticate",
    ],
)
```

**Step 3: Test with authentication**
```bash
# Test without auth (should be blocked for protected endpoints)
curl http://localhost:8000/chat/conversations

# Test with auth header
curl -H "x-api-key: your-key" http://localhost:8000/chat/conversations
```

#### 6. Advanced Routers
**Why Last:** Most dependencies and complexity  
**Files to modify:** `api/main.py`

**Step 1: Uncomment one router at a time**
```python
# app.include_router(api_router)           # Uncomment first
# app.include_router(routing_router)       # Then this
# app.include_router(execute_router)       # Then this
# etc...
```

**Step 2: Test each router individually**
```bash
# Test API router
curl http://localhost:8000/api/goblins

# Test routing router
curl http://localhost:8000/routing/providers
```

---

## 🧪 Testing Protocol

### After Each Change:
1. **Server startup test:**
   ```bash
   python -m uvicorn api.main:app --reload
   ```

2. **Basic endpoint test:**
   ```bash
   curl http://localhost:8000/test
   ```

3. **Health check:**
   ```bash
   curl http://localhost:8000/health
   ```

### Success Criteria:
- ✅ Server starts without errors
- ✅ No crash on HTTP requests
- ✅ Expected endpoints respond correctly
- ✅ No import errors or circular dependency warnings

### Failure Handling:
- ❌ **If server crashes:** Revert the last change and check dependencies
- ❌ **If import errors:** Check for missing modules or circular imports
- ❌ **If endpoints fail:** Verify dependencies are properly initialized

---

## 🔄 Rollback Strategy

**If something breaks:**

1. **Immediate rollback:**
   ```bash
   # Re-comment the problematic import/feature
   # Restart server
   ```

2. **Check dependencies:**
   - Verify all required modules exist
   - Check environment variables
   - Test database/Redis connectivity

3. **Fix and retry:**
   - Address the specific error
   - Re-enable feature incrementally

---

## 📋 Feature Checklist

### Phase 1: Database & Chat
- [ ] Enable database initialization
- [ ] Enable chat router
- [ ] Test conversation creation
- [ ] Test message sending

### Phase 2: Cache & Monitoring  
- [ ] Enable Redis cache
- [ ] Enable provider monitoring
- [ ] Test cache functionality
- [ ] Test monitoring endpoints

### Phase 3: Middleware & Advanced
- [ ] Enable error handling middleware
- [ ] Enable authentication middleware
- [ ] Test API router
- [ ] Test routing router
- [ ] Test all other routers

---

## 💡 Pro Tips

1. **Start Small:** Enable one feature at a time
2. **Test Thoroughly:** Don't skip the testing protocol
3. **Monitor Logs:** Watch for warnings and errors
4. **Backup Working State:** Save working configurations
5. **Document Changes:** Keep track of what works and what doesn't

**Expected Timeline:** 2-4 hours for full re-enablement depending on issues encountered.

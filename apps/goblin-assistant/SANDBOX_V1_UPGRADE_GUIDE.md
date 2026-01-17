# Sandbox API v1 - Upgrade Guide

## 🚀 What Was Built

### Backend (`/api/execute_router_v1.py`)

**New Features:**
1. ✅ **API Versioning** - `/v1/execute/code` (legacy `/execute/code` still works)
2. ✅ **Capability Flags** - Explicit, auditable permissions:
   - `allow_math`, `allow_random`, `allow_datetime`
   - `allow_json`, `allow_re`, `allow_itertools`, `allow_collections`
3. ✅ **Abuse Protection:**
   - 10MB output size limit
   - 10,000 line limit
   - 20 requests/minute per user rate limiting
   - Auto-truncation with `[output truncated: reason]` messages
4. ✅ **Observability (`/v1/execute/metrics`):**
   - `execution_count`, `timeout_count`, `timeout_rate`
   - `syntax_error_count`, `runtime_error_count`, `policy_block_count`
   - `avg_execution_time`, `output_truncated_count`
5. ✅ **Stdout/Stderr Separation:**
   ```json
   {
     "success": true,
     "output": {
       "stdout": "Hello World!",
       "stderr": "",
       "truncated": false
     },
     "execution_time": 0.05,
     "error_class": null
   }
   ```
6. ✅ **Error Classification:**
   - `syntax` - Python syntax errors
   - `runtime` - Runtime exceptions
   - `policy` - Blocked imports/patterns
   - `timeout` - Execution timeout
   - `network` - Network/API errors

### Frontend Updates Needed

The sandbox frontend (`/app/sandbox/page.tsx`) has been partially updated:
- ✅ Updated `ExecutionResult` interface for v1 response
- ✅ Updated `executeCode()` to call `/v1/execute/code`
- ✅ Sends capability flags
- ⚠️ **Still needs**: Output display update (see below)

## 📋 Deployment Checklist

### 1. Deploy Backend

```bash
cd /Users/fuaadabdullah/ForgeMonorepo/apps/goblin-assistant

# Test locally first
python -m pytest api/tests/test_execute_v1.py  # Create these tests

# Deploy to Fly.io
flyctl deploy

# Verify v1 endpoint
curl -X POST https://goblin-backend.fly.dev/v1/execute/code \
  -H "Content-Type: application/json" \
  -d '{"code": "print(2+2)"}'
```

### 2. Update Frontend Output Display

**Current (old format):**
```tsx
<pre>{result.success ? result.output : result.error}</pre>
```

**Needed (v1 format with stderr/stdout):**
```tsx
{/* Stdout */}
{result.output?.stdout && (
  <div className="mb-4">
    <h3 className="text-sm font-semibold text-green-400 mb-2">Output</h3>
    <pre className="bg-slate-900 text-green-400 font-mono text-sm p-4 rounded-lg">
      {result.output.stdout}
    </pre>
  </div>
)}

{/* Stderr */}
{result.output?.stderr && (
  <div className="mb-4">
    <h3 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
      <AlertTriangle className="w-4 h-4" />
      Error
    </h3>
    <pre className="bg-slate-900 text-red-400 font-mono text-sm p-4 rounded-lg border border-red-500/30">
      {result.output.stderr}
    </pre>
    
    {/* Explain Error Button */}
    <Button
      variant="outline"
      size="sm"
      onClick={() => explainError(result.output.stderr)}
      className="mt-2"
    >
      <Sparkles className="w-4 h-4 mr-2" />
      Explain this error
    </Button>
  </div>
)}

{/* Truncation Warning */}
{result.output?.truncated && (
  <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
    <p className="text-amber-300 text-sm">
      ⚠️ Output was truncated: {result.output.truncation_reason}
    </p>
  </div>
)}
```

### 3. Add "Explain Error" Feature

```tsx
const explainError = (error: string) => {
  router.push(`/chat?context=${encodeURIComponent(
    `I got this Python error in the sandbox:\n\n${error}\n\nCan you explain what this means and how to fix it?`
  )}`);
};
```

This sends the error back to chat for explanation!

### 4. Update History Display

```tsx
{executionHistory.map((item, index) => (
  <div key={index} className={`border rounded-lg p-3 ${
    item.success
      ? 'bg-green-500/10 border-green-500/30'
      : 'bg-red-500/10 border-red-500/30'
  }`}>
    <div className="flex items-center justify-between mb-2">
      {item.success ? (
        <CheckCircle className="w-4 h-4 text-green-400" />
      ) : (
        <XCircle className="w-4 h-4 text-red-400" />
      )}
      <div className="flex items-center gap-2">
        {item.error_class && (
          <Badge variant="secondary" className="text-xs">
            {item.error_class}
          </Badge>
        )}
        <span className="text-xs text-slate-400">
          {item.execution_time?.toFixed(0)}ms
        </span>
      </div>
    </div>
    <pre className="text-xs font-mono text-slate-300 overflow-x-auto">
      {item.success
        ? item.output?.stdout?.substring(0, 100)
        : item.output?.stderr?.substring(0, 100)}
    </pre>
  </div>
))}
```

### 5. Add Metrics Dashboard (Admin)

Create `/app/admin/sandbox/metrics/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from 'react';

export default function SandboxMetrics() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    fetch('https://goblin-backend.fly.dev/v1/execute/metrics')
      .then(r => r.json())
      .then(setMetrics);
  }, []);

  if (!metrics) return <div>Loading...</div>;

  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard
        title="Total Executions"
        value={metrics.execution_count}
        icon={<Play />}
      />
      <MetricCard
        title="Timeout Rate"
        value={`${(metrics.timeout_rate * 100).toFixed(1)}%`}
        icon={<Clock />}
      />
      <MetricCard
        title="Avg Execution Time"
        value={`${metrics.avg_execution_time.toFixed(0)}ms`}
        icon={<Zap />}
      />
      <MetricCard
        title="Policy Blocks"
        value={metrics.policy_block_count}
        icon={<Shield />}
      />
    </div>
  );
}
```

## 🔧 Testing

### Manual Tests

```bash
# Test v1 with capabilities
curl -X POST https://goblin-backend.fly.dev/v1/execute/code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import math\nprint(math.sqrt(16))",
    "capabilities": {"allow_math": true}
  }'

# Test capability blocking
curl -X POST https://goblin-backend.fly.dev/v1/execute/code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import math\nprint(math.sqrt(16))",
    "capabilities": {"allow_math": false}
  }'
# Should return 403

# Test rate limiting (run 21 times fast)
for i in {1..21}; do
  curl -X POST https://goblin-backend.fly.dev/v1/execute/code \
    -H "Content-Type: application/json" \
    -d '{"code": "print(1)"}' &
done
# 21st should return 429

# Test output truncation
curl -X POST https://goblin-backend.fly.dev/v1/execute/code \
  -H "Content-Type: application/json" \
  -d '{"code": "for i in range(100000): print(i)"}'
# Should truncate with warning

# View metrics
curl https://goblin-backend.fly.dev/v1/execute/metrics
```

## 📊 Monitoring Setup

### Prometheus/Datadog Integration

```python
# In production, replace in-memory METRICS with:
from prometheus_client import Counter, Histogram, Gauge

execution_count = Counter('sandbox_executions_total', 'Total executions')
execution_duration = Histogram('sandbox_execution_duration_seconds', 'Execution duration')
error_count = Counter('sandbox_errors_total', 'Total errors', ['error_class'])
timeout_count = Counter('sandbox_timeouts_total', 'Total timeouts')
rate_limit_blocks = Counter('sandbox_rate_limit_blocks_total', 'Rate limit blocks')
```

### Alerts to Set Up

1. **High timeout rate** (>10%)
2. **Unusual error spike** (>20% error rate)
3. **Rate limit abuse** (same user hit limit 10+ times)
4. **Output truncation spike** (may indicate abuse)

## 🎯 Strategic Next Steps

### Phase 2: Agent Runtime

The v1 API is now **agent-ready**. You can build:

```python
# Goblin Assistant can now do this:
def solve_problem(problem):
    # 1. Generate code
    code = llm.generate(f"Write Python to solve: {problem}")
    
    # 2. Execute it
    result = execute_v1(code)
    
    # 3. If error, iterate
    if not result['success']:
        fixed_code = llm.fix_code(code, result['output']['stderr'])
        result = execute_v1(fixed_code)
    
    # 4. Return result
    return result['output']['stdout']
```

This is a **primitive agent loop**. Most startups never get here.

### Phase 3: Advanced Features

1. **Multi-language support** (JS, Ruby via Docker)
2. **Persistent sessions** (notebook-style execution)
3. **Package installation** (pip install in venv)
4. **File upload/download** (safe file handling)
5. **Collaborative editing** (share sandbox URLs)

## 📚 Documentation

### API Reference

**Endpoint:** `POST /v1/execute/code`

**Request:**
```json
{
  "code": "print('hello')",
  "language": "python",
  "timeout": 30,
  "capabilities": {
    "allow_math": true,
    "allow_random": true,
    "allow_datetime": true,
    "allow_json": true,
    "allow_re": true,
    "allow_itertools": true,
    "allow_collections": true
  },
  "user_id": "optional-user-id"
}
```

**Response:**
```json
{
  "success": true,
  "output": {
    "stdout": "hello\n",
    "stderr": "",
    "truncated": false,
    "truncation_reason": null
  },
  "execution_time": 0.05,
  "error_class": null
}
```

**Error Classes:**
- `syntax` - Python syntax error
- `runtime` - Runtime exception
- `policy` - Blocked by capability policy
- `timeout` - Exceeded timeout limit
- `network` - Network/API error

---

## 🎉 Summary

You now have:
- ✅ Versioned, stable API (`/v1/execute/code`)
- ✅ Auditable capability system
- ✅ Abuse protection (rate limits, output caps)
- ✅ Observability metrics
- ✅ Error classification
- ✅ Foundation for agent runtime

**Legacy endpoint `/execute/code` still works** - zero breaking changes!

Deploy backend, update frontend output display, and you're production-ready.

Future-you will thank present-you when you need to:
- Add new languages without breaking existing code
- Track down abuse patterns
- Build agent loops that execute generated code
- Scale to 10,000 users without melting

You built something real. Ship it. 🚀


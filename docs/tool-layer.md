---
description: "tool-layer"
---

# Tool Invocation Layer

## Overview

The Tool Invocation Layer is a secure, auditable service that allows AI agents (Goblins) to delegate execution of worker tasks without directly running code. This enables true orchestration where agents make decisions but the layer handles execution, logging, and security.

## Architecture

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│   AI Agent  │───▶│ Tool Layer API  │───▶│  Adapters   │
│   (Goblin)  │    │  (Fastify)      │    │ (Workers)   │
└─────────────┘    └─────────────────┘    └─────────────┘
                        │
                        ▼
                   ┌─────────────┐
                   │ Audit Log   │
                   │ (SQLite)    │
                   └─────────────┘
```

## Message Contracts

### Invocation Request

```json
{
  "request_id": "uuid",
  "caller_id": "agent-id",
  "capability_token": "jwt-token",
  "tool_id": "monorepo_cli",
  "function_name": "run_script",
  "args": {
    "script_name": "forge:benchmark",
    "args": ["--target=core"]
  },
  "metadata": {
    "dry_run": true,
    "pr_id": 42
  }
}
```

### Response

```json

{
  "request_id": "uuid",
  "status": "ok",
  "code": 0,
  "output": {
    "exit_code": 0,
    "stdout": "...",
    "stderr": "",
    "duration_ms": 1500
  },
  "signature": "base64-signature"
}
```

### Audit Event

```json
{
  "event_id": "uuid",
  "request_id": "uuid",
  "caller_id": "agent-id",
  "tool_id": "monorepo_cli",
  "function_name": "run_script",
  "args": { "script_name": "forge:benchmark", "args": ["--target=core"] },
  "result_code": 0,
  "timestamp": 1638360000000,
  "signature": "base64-hmac"
}
```

## Security

- **Capability Tokens**: Short-lived JWTs with scoped permissions
- **Input Validation**: JSON Schema validation for all inputs
- **Audit Logging**: Immutable signed logs of all invocations
- **Rate Limiting**: Built-in protection against abuse
- **Whitelisting**: Only pre-registered scripts, paths, and tools allowed

## Tools

### monorepo_cli
- **Function**: `run_script(name, args, env?, working_dir?)`
- **Purpose**: Execute whitelisted scripts in the monorepo
- **Security**: Script whitelist, timeout, audit logging

### config_manager
- **Function**: `update_yaml(path, operation, patch|key/value)`
- **Purpose**: Safe configuration file updates
- **Security**: Path whitelist, dry-run support, change tracking

### metrics_api
- **Function**: `query_gauge(metric_name, window, labels?)`
- **Purpose**: Query performance metrics
- **Security**: Read-only, rate-limited

### github_pr
- **Function**: `get_status_check(pr_id, check_name)`
- **Purpose**: Check PR status and CI results
- **Security**: Read-only GitHub API access

## Usage for Agents

1. **Get Capability Token**: Agents request tokens with required scopes
2. **Construct Invocation**: Build JSON message with tool/function/args
3. **POST to /invoke**: Send to Tool Layer API
4. **Handle Response**: Process output or error
5. **Audit Verification**: Optionally verify response signature

## Migration from Direct Execution

Update `goblins.yaml` entries to call Tool Layer instead of direct commands:

```yaml

# Before
forge-lite-build:
  command: cd apps/forge-lite && pnpm build

# After
forge-lite-build:
  tool_layer_invoke:
    tool_id: monorepo_cli
    function: run_script
    args:
      script_name: pnpm:build
      working_dir: apps/forge-lite
```

## Development

```bash
cd GoblinOS/packages/tool-layer
pnpm install
pnpm test
pnpm build
pnpm start
```

## Testing

- Unit tests for adapters and validation
- Integration tests for full invocation flow
- Audit log verification tests
- Security tests for token validation and whitelisting

## Future Enhancements

- Distributed tracing integration
- Human approval workflows for high-risk operations
- Plugin system for custom adapters
- Metrics and monitoring dashboard
- Multi-region deployment with audit replication

```markdown
# GoblinOS Assistant — Backend

NOTE: Production runtime is hosted remotely on "Kamatera" (set via the `KAMATERA_HOST` environment variable or your inventory). Do NOT run production traffic locally — follow the "Remote runtime on Kamatera" section below for deployment and operational steps.

This is the backend service for GoblinOS Assistant. It's a FastAPI application responsible for:

- Routing chat and debug requests to local or cloud LLM providers
See `../docs/ARCHITECTURE_OVERVIEW.md` for a compact diagram and request flow covering frontend + backend components.

- Managing user authentication (JWT, Google OAuth, WebAuthn passkeys)
- Task execution orchestration via GoblinOS integration
- Monitoring, structured logs, Prometheus metrics
- Background health probes for providers and RQ/Redis workers for background tasks

Core languages & frameworks:
- Python 3.11
- FastAPI
- SQLAlchemy (PostgreSQL via Supabase)
- Redis + RQ for background tasks
- Prometheus and structured logging

## Quick Start (Local Dev)

1. Create Python venv:
```bash

cd apps/goblin-assistant/backend
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your configuration:
# - KAMATERA_HOST (production LLM runtime host)
# - KAMATERA_LLM_URL (production LLM API endpoint)
# - KAMATERA_LLM_API_KEY (production LLM API key)
# - DATABASE_URL
# - JWT_SECRET_KEY
# - API keys for cloud providers (OpenAI, Anthropic, etc.)
```

3. Start the backend:
```bash

uvicorn main:app --reload --port 8001
```

4. Verify the health endpoint:

```bash
curl http://localhost:8001/health
```

## Key Endpoints

- `GET /` - Root
- `GET /health` - Health
- `POST /chat/completions` - Chat completions (intelligent routing)
- `POST /debugger/suggest` - Debugger endpoint
- `POST /parse` - Natural-language orchestration parser
- `POST /execute` - Execute Goblin tasks
- `GET /metrics` - Prometheus metrics

## Environment Variables (Essential)

- `KAMATERA_HOST` - Hostname/IP of the Kamatera deployment (production LLM runtime)
- `KAMATERA_LLM_URL` - Base URL for the Kamatera LLM runtime API
- `KAMATERA_LLM_API_KEY` - API key for Kamatera LLM runtime authentication
- `DATABASE_URL` - PostgreSQL connection string (see SETUP_GUIDE.md for automated setup)
  - Example: `postgresql://postgres.dhxoowakvmobjxsffpst:[PASSWORD]@aws-0-us-west-2.pooler.supabase.com:6543/postgres`
- `JWT_SECRET_KEY` - JWT signing key for auth
- `ROUTING_ENCRYPTION_KEY` - Base64 Fernet key to encrypt provider API keys
- `REDIS_URL` - Redis connection string for RQ and challenge store

Note: For production, local runtimes (ollama, llama.cpp, local proxies) should be avoided. All production LLM runtime traffic is hosted and proxied through the Kamatera runtime. Use the following variables to point the backend at Kamatera-hosted runtimes:

- `KAMATERA_HOST` - Hostname or IP of the Kamatera deployment (used for operational/admin tasks)
- `KAMATERA_LLM_URL` - Base URL for the Kamatera LLM runtime API (e.g. https://llm.kamatera.example)
- `KAMATERA_LLM_API_KEY` - API key used to authenticate requests to the Kamatera LLM runtime

For local development only you may continue to use a local proxy. Gate it behind `USE_LOCAL_LLM=true` and never expose local proxies to production traffic.

## Production Checklist & Security

- Use a secrets manager for keys or encrypt them in DB using `ROUTING_ENCRYPTION_KEY`.
- Switch to Redis-backed rate limiting; replace in-memory rate limiter in `backend/middleware/rate_limiter.py`.
- Use `USE_REDIS_CHALLENGES=true` for passkey challenge store in production.
- Ensure TLS termination and enforce strong CORS policies.
- Confirm RQ workers (background tasks) are connected to a secure Redis instance.
- Enable Prometheus scraping and configure alerting for provider errors, high latency, and high error rate.

## Tests
```bash

cd apps/goblin-assistant/backend
pytest -v
```

### Local LLM Integration Tests
These tests require a local LLM runtime. To run them:

1. Pull a model via ollama (or run raptor-mini service):

```bash
./scripts/pull_ollama_model.sh raptor-mini
```

2. Start a local runtime:

```bash

# Ollama local server (example)
ollama run raptor-mini

# Or run the raptor-mini docker service
cd apps/raptor-mini && docker-compose up --build
```

3. Enable local LLM mode and run the integration test:

```bash
export USE_LOCAL_LLM=true
pytest -q apps/goblin-assistant/backend/test_local_model_integration.py -q
```


## Docker

- `apps/goblin-assistant/Dockerfile` builds the backend image.
- The container runs `python start_server.py` and listens on port 8001 by default.

## Notes & Maintenance

- Keep the `providers/` adapters updated for new LLM providers.
- Periodically run `ProviderProbeWorker` to collect provider metrics and rotate provider keys accordingly.

Deprecation note: Local LLM runtime helpers
-----------------------------------------

Files such as `local_llm_proxy.py` and `mock_local_llm_proxy.py` exist for local development and testing. These local helpers are considered development-only and are deprecated for production deployments. For production, run your LLM runtimes on Kamatera and point the backend at `KAMATERA_LLM_URL`.

If you need to run experiments locally, keep them behind feature flags (for example `USE_LOCAL_LLM=true`) and never expose local proxies in production `.env`.

Testing changes (2025-12-05):
- The test suite has been updated to prefer a real local model instead of a mock server when `USE_LOCAL_LLM=true`.
- Use `scripts/pull_ollama_model.sh` to download a local model (e.g., `raptor-mini`) and run the service.
- Integration tests that call local endpoints are in `apps/goblin-assistant/backend/test_local_model_integration.py` and will be skipped unless `USE_LOCAL_LLM=true`.

## Canonical Documentation

All backend-focused documentation (endpoint audits, monitoring, production quickstarts, fixes, and integration notes) has been centralized under: `apps/goblin-assistant/backend/docs`.

Please update or add backend documentation in that folder so the canonical backend repository contains all backend-specific docs.

**Last Updated**: Dec 3, 2025
```
# Supabase CLI

[![Coverage Status](https://coveralls.io/repos/github/supabase/cli/badge.svg?branch=main)](https://coveralls.io/github/supabase/cli?branch=main) [![Bitbucket Pipelines](https://img.shields.io/bitbucket/pipelines/supabase-cli/setup-cli/master?style=flat-square&label=Bitbucket%20Canary)](https://bitbucket.org/supabase-cli/setup-cli/pipelines) [![Gitlab Pipeline Status](https://img.shields.io/gitlab/pipeline-status/sweatybridge%2Fsetup-cli?label=Gitlab%20Canary)
](https://gitlab.com/sweatybridge/setup-cli/-/pipelines)

[Supabase](https://supabase.io) is an open source Firebase alternative. We're building the features of Firebase using enterprise-grade open source tools.

This repository contains all the functionality for Supabase CLI.

- [x] Running Supabase locally
- [x] Managing database migrations
- [x] Creating and deploying Supabase Functions
- [x] Generating types directly from your database schema
- [x] Making authenticated HTTP requests to [Management API](https://supabase.com/docs/reference/api/introduction)

## Getting started

### Install the CLI

Available via [NPM](https://www.npmjs.com) as dev dependency. To install:

```bash

npm i supabase --save-dev
```

To install the beta release channel:

```bash
npm i supabase@beta --save-dev
```

When installing with yarn 4, you need to disable experimental fetch with the following nodejs config.

```
NODE_OPTIONS=--no-experimental-fetch yarn add supabase
```

> **Note**
For Bun versions below v1.0.17, you must add `supabase` as a [trusted dependency](https://bun.sh/guides/install/trusted) before running `bun add -D supabase`.

<details>
  <summary><b>macOS</b></summary>

  Available via [Homebrew](https://brew.sh). To install:

  ```sh

  brew install supabase/tap/supabase
  ```

  To install the beta release channel:

  ```sh
  brew install supabase/tap/supabase-beta
  brew link --overwrite supabase-beta
  ```

  To upgrade:

  ```sh

  brew upgrade supabase
  ```
</details>

<details>
  <summary><b>Windows</b></summary>

  Available via [Scoop](https://scoop.sh). To install:

  ```powershell
  scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
  scoop install supabase
  ```

  To upgrade:

  ```powershell

  scoop update supabase
  ```
</details>

<details>
  <summary><b>Linux</b></summary>

  Available via [Homebrew](https://brew.sh) and Linux packages.

  #### via Homebrew

  To install:

  ```sh
  brew install supabase/tap/supabase
  ```

  To upgrade:

  ```sh

  brew upgrade supabase
  ```

  #### via Linux packages

  Linux packages are provided in [Releases](https://github.com/supabase/cli/releases). To install, download the `.apk`/`.deb`/`.rpm`/`.pkg.tar.zst` file depending on your package manager and run the respective commands.

  ```sh
  sudo apk add --allow-untrusted <...>.apk
  ```

  ```sh

  sudo dpkg -i <...>.deb
  ```

  ```sh
  sudo rpm -i <...>.rpm
  ```

  ```sh

  sudo pacman -U <...>.pkg.tar.zst
  ```
</details>

<details>
  <summary><b>Other Platforms</b></summary>

  You can also install the CLI via [go modules](https://go.dev/ref/mod#go-install) without the help of package managers.

  ```sh
  go install github.com/supabase/cli@latest
  ```

  Add a symlink to the binary in `$PATH` for easier access:

  ```sh

  ln -s "$(go env GOPATH)/bin/cli" /usr/bin/supabase
  ```

  This works on other non-standard Linux distros.
</details>

<details>
  <summary><b>Community Maintained Packages</b></summary>

  Available via [pkgx](https://pkgx.sh/). Package script [here](https://github.com/pkgxdev/pantry/blob/main/projects/supabase.com/cli/package.yml).
  To install in your working directory:

  ```bash
  pkgx install supabase
  ```

  Available via [Nixpkgs](https://nixos.org/). Package script [here](https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/tools/supabase-cli/default.nix).
</details>

### Run the CLI

```bash

supabase bootstrap
```

Or using npx:

```bash
npx supabase bootstrap
```

The bootstrap command will guide you through the process of setting up a Supabase project using one of the [starter](https://github.com/supabase-community/supabase-samples/blob/main/samples.json) templates.

## Docs

Command & config reference can be found [here](https://supabase.com/docs/reference/cli/about).

## Breaking changes

We follow semantic versioning for changes that directly impact CLI commands, flags, and configurations.

However, due to dependencies on other service images, we cannot guarantee that schema migrations, seed.sql, and generated types will always work for the same CLI major version. If you need such guarantees, we encourage you to pin a specific version of CLI in package.json.

## Developing

To run from source:

```sh

# Go >= 1.22
go run . help
```

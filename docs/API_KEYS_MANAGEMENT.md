---
description: "API_KEYS_MANAGEMENT"
---

# API Keys & Secrets Management

- Do not commit secrets. Use local `.env` files or system keychains.
- For GoblinOS, copy `GoblinOS/.env.example` to `GoblinOS/.env` and fill values.
- For Python apps, use `.env` + `python-dotenv` or environment variables.
- Prefer Docker/compose secrets for services.

Rotations and shared secrets should be coordinated outside of the repo.


"""CI Bootstrap Server for handing out ephemeral secrets to VMs.

This server emulates a CI endpoint that VMs call during cloud-init bootstrap.
In production, this would be a secure CI service or Vault agent.

Usage:
  export CI_SECRETS_FILE=./bootstrap/test_secrets.json
  python ci_bootstrap_server.py

VMs call: curl http://ci-server:8080/secrets?instance=<id>
"""

import os
import json
from fastapi import FastAPI, HTTPException
from typing import Dict, Any

app = FastAPI(title="CI Bootstrap Server", version="1.0.0")

# Read secrets from file or environment
SECRETS_FILE = os.getenv("CI_SECRETS_FILE", "./test_secrets.json")


@app.get("/secrets")
async def get_secrets(instance: str) -> Dict[str, Any]:
    """Return secrets for a specific instance.

    In production, validate the instance token and return only authorized secrets.
    """
    if not os.path.exists(SECRETS_FILE):
        raise HTTPException(status_code=404, detail="Secrets file not found")

    with open(SECRETS_FILE, "r") as f:
        secrets = json.load(f)

    # For testing: return all secrets
    # In production: validate instance token and filter secrets
    return secrets


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ci-bootstrap"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)

#!/usr/bin/env python3
"""
Mock Vault Server for Goblin Assistant Migration Testing
Simulates HashiCorp Vault operations for testing migration scripts
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class MockVaultClient:
    """Mock Vault client for testing migration without actual Vault server"""

    def __init__(
        self, url: str = "http://localhost:8200", token: str = "goblin-vault-root-token"
    ):
        self.url = url
        self.token = token
        self.store: Dict[str, Any] = {}
        self.policies: Dict[str, Any] = {}
        self.auth_methods: Dict[str, Any] = {}
        print(f"🔧 Mock Vault initialized at {url}")

    def is_initialized(self) -> bool:
        return True

    def is_sealed(self) -> bool:
        return False

    def write_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Write secret to KV store"""
        full_path = f"secret/data/{path}"
        self.store[full_path] = {
            "data": data,
            "metadata": {
                "created_time": datetime.utcnow().isoformat(),
                "deletion_time": "",
                "destroyed": False,
                "version": 1,
            },
        }
        print(f"✅ Secret written to {path}")
        return True

    def read_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """Read secret from KV store"""
        full_path = f"secret/data/{path}"
        if full_path in self.store:
            return self.store[full_path]["data"]
        return None

    def list_secrets(self, path: str) -> list:
        """List secrets under path"""
        prefix = f"secret/data/{path}"
        secrets = []
        for key in self.store.keys():
            if key.startswith(prefix):
                secrets.append(key.replace(f"secret/data/{path}/", "").split("/")[0])
        return list(set(secrets))

    def delete_secret(self, path: str) -> bool:
        """Delete secret"""
        full_path = f"secret/data/{path}"
        if full_path in self.store:
            del self.store[full_path]
            print(f"🗑️ Secret deleted from {path}")
            return True
        return False

    def enable_auth_method(self, method: str, config: Dict[str, Any]) -> bool:
        """Enable authentication method"""
        self.auth_methods[method] = config
        print(f"🔐 Auth method {method} enabled")
        return True

    def create_policy(self, name: str, policy: str) -> bool:
        """Create Vault policy"""
        self.policies[name] = policy
        print(f"📋 Policy {name} created")
        return True

    def setup_database_engine(self, config: Dict[str, Any]) -> bool:
        """Setup database secrets engine"""
        print("🗄️ Database engine configured")
        return True

    def create_database_role(self, name: str, config: Dict[str, Any]) -> bool:
        """Create database role"""
        print(f"👤 Database role {name} created")
        return True

    def generate_database_credentials(self, role: str) -> Dict[str, Any]:
        """Generate dynamic database credentials"""
        return {
            "username": f"vault_{role}_{int(datetime.utcnow().timestamp())}",
            "password": f"temp_pass_{os.urandom(8).hex()}",
            "ttl": "1h",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get Vault status"""
        return {
            "initialized": True,
            "sealed": False,
            "standby": False,
            "version": "1.15.0",
            "cluster_name": "goblin-vault",
            "server_time_utc": int(datetime.utcnow().timestamp()),
        }

    def save_state(self, filename: str = "mock_vault_state.json"):
        """Save mock vault state to file"""
        state = {
            "store": self.store,
            "policies": self.policies,
            "auth_methods": self.auth_methods,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with open(filename, "w") as f:
            json.dump(state, f, indent=2)
        print(f"💾 Mock Vault state saved to {filename}")

    def load_state(self, filename: str = "mock_vault_state.json"):
        """Load mock vault state from file"""
        if os.path.exists(filename):
            with open(filename, "r") as f:
                state = json.load(f)
            self.store = state.get("store", {})
            self.policies = state.get("policies", {})
            self.auth_methods = state.get("auth_methods", {})
            print(f"📂 Mock Vault state loaded from {filename}")
            return True
        return False


# Global mock vault instance
mock_vault = MockVaultClient()

if __name__ == "__main__":
    # Test the mock vault
    print("🧪 Testing Mock Vault...")

    # Write a test secret
    mock_vault.write_secret(
        "test/api_keys", {"openai": "sk-test123", "anthropic": "sk-ant-test456"}
    )

    # Read it back
    secret = mock_vault.read_secret("test/api_keys")
    print(f"📖 Read secret: {secret}")

    # List secrets
    secrets = mock_vault.list_secrets("test")
    print(f"📋 Listed secrets: {secrets}")

    # Save state
    mock_vault.save_state()

    print("✅ Mock Vault test completed!")
